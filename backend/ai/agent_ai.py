import json
import os
import re
from dotenv import load_dotenv
try:
    from mistralai import Mistral
except ImportError:
    from mistralai.client import Mistral

load_dotenv()

MODEL_NAME = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

GRAPH_TYPE_LABELS = {
    "students_by_class": "repartition des eleves par classe",
    "students_by_gender": "repartition des eleves par sexe",
    "students_by_locality": "repartition des eleves par localite",
    "inscriptions_breakdown": "repartition des inscriptions",
    "average_grades_by_class": "moyennes des notes par classe",
    "average_grades_by_subject": "moyennes des notes par matiere",
    "grades_distribution": "distribution des notes par trimestre",
    "top_students_by_class": "meilleurs eleves par classe",
}

DOCUMENT_TYPE_LABELS = {
    "attestation_inscription": "attestation d'inscription",
    "attestation_presence": "attestation de presence",
    "certificat_scolarite": "certificat de scolarite",
}


def _is_student_need_classification_prompt(user_message: str) -> bool:
    text = (user_message or "").lower()
    return (
        "needs_student" in text
        and "message:" in text
        and "analyse" in text
        and "recherche" in text
    )


def _clean_professional_response(text: str, intent: str) -> str:
    raw = (text or "").strip()
    if not raw:
        if intent == "show_graph":
            return (
                "Voici le graphique de repartition des eleves par classe. "
                "Il presente clairement la distribution actuelle des effectifs."
            )
        return "Je reste a votre disposition pour toute precision complementaire."

    blocked_patterns = [
        r"\[.*?ins[ée]rer.*?\]",
        r"je ne peux pas g[ée]n[ée]rer d[' ]image",
        r"comme je ne peux pas g[ée]n[ée]rer d[' ]image",
        r"description textuelle",
    ]
    for pattern in blocked_patterns:
        raw = re.sub(pattern, "", raw, flags=re.IGNORECASE | re.DOTALL).strip()

    raw = re.sub(r"\n{3,}", "\n\n", raw)
    raw = re.sub(r"\s{2,}", " ", raw).strip()
    raw = re.sub(r"\bassistant(e)?\b", "agent", raw, flags=re.IGNORECASE)
    raw = re.sub(r"https?://\S+|www\.\S+", "", raw, flags=re.IGNORECASE).strip()

    if not raw:
        if intent == "show_graph":
            return (
                "Voici le graphique de repartition des eleves par classe. "
                "Il permet d'identifier rapidement les classes les plus chargees."
            )
        return "Je reste disponible pour vous accompagner sur votre demande."
    return raw


def _normalize_payload(data: dict) -> dict:
    if not isinstance(data, dict):
        return {
            "intent": "chat",
            "response": "Je n'ai pas compris votre demande. Pouvez-vous reformuler ?",
        }

    intent = data.get("intent", "chat")
    if intent not in {"chat", "generate_document", "show_graph"}:
        intent = "chat"

    if intent == "show_graph":
        graph_type = data.get("graph_type")
        if graph_type == "students":
            graph_type = "students_by_class"
        if graph_type not in {
            "students_by_class", 
            "students_by_gender", 
            "inscriptions_breakdown", 
            "students_by_locality",
            "average_grades_by_class",
            "average_grades_by_subject",
            "grades_distribution",
            "top_students_by_class"
        }:
            graph_type = "students_by_class"
        data["graph_type"] = graph_type

    data["intent"] = intent
    data["response"] = _clean_professional_response(data.get("response", ""), intent)
    return data


def _extract_mistral_content(response) -> str:
    try:
        content = response.choices[0].message.content
    except Exception:
        return ""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        chunks = []
        for item in content:
            text = ""
            if isinstance(item, dict):
                text = item.get("text") or ""
            else:
                text = getattr(item, "text", "") or ""
            if text:
                chunks.append(text)
        return "\n".join(chunks).strip()

    return ""


def _call_llm_text(prompt: str) -> str:
    try:
        response = client.chat.complete(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_mistral_content(response)
    except Exception as e:
        print("ERROR:", str(e))
        return ""


def _extract_llm_text(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""

    text = re.sub(r"^```(?:json|text)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text).strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            return text

        if isinstance(data, dict):
            response = data.get("response") or data.get("text")
            if isinstance(response, str):
                return response.strip()

    return text


def _clean_llm_text_no_fallback(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return ""

    blocked_patterns = [
        r"\[.*?ins[Ã©e]rer.*?\]",
        r"je ne peux pas g[Ã©e]n[Ã©e]rer d[' ]image",
        r"comme je ne peux pas g[Ã©e]n[Ã©e]rer d[' ]image",
        r"description textuelle",
    ]
    for pattern in blocked_patterns:
        raw = re.sub(pattern, "", raw, flags=re.IGNORECASE | re.DOTALL).strip()

    raw = re.sub(r"\n{3,}", "\n\n", raw)
    raw = re.sub(r"\s{2,}", " ", raw).strip()
    raw = re.sub(r"\bassistant(e)?\b", "agent", raw, flags=re.IGNORECASE)
    raw = re.sub(r"https?://\S+|www\.\S+", "", raw, flags=re.IGNORECASE).strip()
    return raw


def interpret_graph_summary(graph_type: str, graph_summary: dict, user_message: str = "") -> str:
    if graph_type == "top_students_by_class":
        prompt = f"""
Tu es un agent administratif scolaire.
Tu dois interpreter un classement des meilleurs eleves par classe a partir des donnees structurees ci-dessous.

Contraintes strictes :
- Reponds en francais naturel et professionnel.
- Redige 2 ou 3 phrases maximum.
- Base-toi uniquement sur les chiffres fournis.
- Mentionne le nombre de classes representees.
- Cite l'eleve et la classe en tete du classement avec sa moyenne sur 20.
- Si pertinent, ajoute une observation sur la moyenne des meilleurs eleves.
- N'utilise ni puces, ni markdown, ni JSON.
- Ne dis pas "voici le graphique demande".

Type de graphique : {GRAPH_TYPE_LABELS.get(graph_type, graph_type)}
Question utilisateur : {user_message or "Non precise"}
Donnees du graphique (JSON) : {json.dumps(graph_summary, ensure_ascii=False)}

Texte final :
"""
    else:
        prompt = f"""
Tu es un agent administratif scolaire.
Tu dois interpreter un graphique a partir des donnees structurees ci-dessous.

Contraintes strictes :
- Reponds en francais naturel et professionnel.
- Redige 2 ou 3 phrases maximum.
- Base-toi uniquement sur les chiffres fournis.
- Mentionne le total.
- Cite la categorie dominante avec sa valeur et son pourcentage.
- Si pertinent, ajoute une deuxieme observation utile.
- N'utilise ni puces, ni markdown, ni JSON.
- Ne dis pas "voici le graphique demande".

Type de graphique : {GRAPH_TYPE_LABELS.get(graph_type, graph_type)}
Question utilisateur : {user_message or "Non precise"}
Donnees du graphique (JSON) : {json.dumps(graph_summary, ensure_ascii=False)}

Texte final :
"""

    raw = _call_llm_text(prompt)
    text = _clean_llm_text_no_fallback(_extract_llm_text(raw))
    if text:
        return text

    retry_prompt = f"""
Tu es un agent administratif scolaire.
Ecris UNIQUEMENT une interpretation professionnelle en francais (2 phrases maximum) du graphique suivant.
Base-toi uniquement sur ces donnees JSON :
{json.dumps(graph_summary, ensure_ascii=False)}
"""
    retry_raw = _call_llm_text(retry_prompt)
    return _clean_llm_text_no_fallback(_extract_llm_text(retry_raw))


def generate_document_success_response(document_type: str, student_data: dict, user_message: str = "") -> str:
    full_name = (
        f"{(student_data or {}).get('PrenomFr', '')} {(student_data or {}).get('NomFr', '')}"
    ).strip() or "l'eleve demande"
    classe = (student_data or {}).get("Classe") or "non precisee"
    annee = (student_data or {}).get("AnneeScolaire") or "non precisee"
    doc_label = DOCUMENT_TYPE_LABELS.get(document_type, "document administratif")

    prompt = f"""
Tu es un agent administratif scolaire.
Un document vient d'etre genere avec succes.

Contraintes strictes :
- Reponds en francais naturel et professionnel.
- Redige 1 ou 2 phrases maximum.
- Mentionne le type de document et le nom de l'eleve.
- N'utilise ni puces, ni markdown, ni JSON, ni URL.

Type de document : {doc_label}
Eleve : {full_name}
Classe : {classe}
Annee scolaire : {annee}
Message utilisateur initial : {user_message or "Non precise"}

Texte final :
"""
    raw = _call_llm_text(prompt)
    text = _clean_llm_text_no_fallback(_extract_llm_text(raw))
    if text:
        return text

    retry_prompt = (
        "Redige une phrase professionnelle en francais confirmant la generation reussie "
        f"du {doc_label} pour {full_name} (classe {classe}, annee scolaire {annee})."
    )
    retry_raw = _call_llm_text(retry_prompt)
    return _clean_llm_text_no_fallback(_extract_llm_text(retry_raw))

def ask_agent(user_message: str, rag_context: str = "") -> dict:
    """
    Interroge le LLM pour obtenir une réponse ou générer un document.
    Retourne toujours un dict JSON avec 'intent' et 'response', et éventuellement 'document_type'.
    """
    
    # Si c'est une requête spéciale pour vérifier si un élève est nécessaire
    if _is_student_need_classification_prompt(user_message):
        # C'est une requête de classification, pas une conversation normale
        return _classify_student_need(user_message)
    
    prompt = f"""
Si l'utilisateur demande ton role, tes missions, tes fonctionnalites ou ce que tu peux faire, tu dois repondre avec intent="chat" et expliquer clairement que la generation des documents administratifs est dediee au personnel administrateur, tandis que la generation des graphes, des statistiques et des analyses est reservee a l'Administrateur.
Tu es un agent IA administratif scolaire compétent et professionnel.
IMPORTANT : tu es un agent, jamais un assistant.
IMPORTANT : n'utilise jamais le mot "assistant" pour te designer.
IMPORTANT : n'inclus jamais de lien URL dans tes reponses.

OBJECTIFS :
- Pour les salutations : répondre de manière chaleureuse et professionnelle, en invitant l'utilisateur à formuler sa demande et en expliquant que tu peux générer des documents administratifs.
- Comprendre la demande de l'utilisateur.
- Fournir une réponse naturelle et polie à l'utilisateur.
- Générer un document uniquement si l'élève est identifié et que le type de document est clair.
- Générer un document UNIQUEMENT si le type est explicitement mentionné.
- Si "attestation" est demandée sans type → intent="chat" obligatoire.
- Tu n’as JAMAIS le droit de deviner le type d’attestation.
- Ne jamais promettre un document si l'élève n'est pas identifié.
- Ne jamais mentionner l'envoi par email.
- Toujours utiliser un ton professionnel et clair, même en cas d'erreur.

RÈGLES MÉTIER STRICTES (À RESPECTER OBLIGATOIREMENT) :
1. ATTESTATION DE PRÉSENCE
   - Elle est TOUJOURS STANDARD
   - Elle ne dépend d’AUCUNE période
   - Elle ne dépend d’AUCUN événement
   - Tu n’as JAMAIS le droit de demander une précision supplémentaire
   - Si l'utilisateur demande une attestation de présence et que l’élève est identifié,
     tu DOIS utiliser intent="generate_document" avec document_type="attestation_presence"
2. "présence" et "presence" sont équivalents.
3. ATTESTATION D’INSCRIPTION
- Elle est TOUJOURS STANDARD
- Il n’existe AUCUN autre type d’attestation d’inscription
- Tu n’as JAMAIS le droit de demander une précision supplémentaire
- Tu n’as JAMAIS le droit de demander une précision de type d’attestation d’inscription
- Si l'utilisateur demande une attestation d'inscription et que l’élève est identifié :
  → intent="generate_document"
  → document_type="attestation_inscription"
4. Certificat de scolarité : générer uniquement si élève identifié.
5. Si type de document inconnu ou élève non identifié, fournir une réponse claire et professionnelle, intent="chat".

INTERDICTION ABSOLUE :
- Si l'utilisateur demande une attestation sans préciser "inscription" ou "présence",
  tu DOIS répondre avec intent="chat" et demander explicitement le type.
- Tu n’as JAMAIS le droit de choisir le type à la place de l’utilisateur.

6. STATISTIQUES ET GRAPHIQUES
- Si l'utilisateur demande une répartition, statistique, graphique ou analyse des élèves
- Exemples : 
    • "Combien d'élèves sont inscrits par classe ?" 
    • "Fais-moi un graphique de la répartition des élèves par classe"
    • "répartition des élèves par classe"
    • "statistiques des élèves"
    • "nombre d'élèves par classe"
    • "répartition garçons filles"
    • "totalite d'inscription : reinscription et nouvelle inscription"
    • "repartition des eleves par localite"
- Si la demande concerne la repartition des eleves par classe : graph_type="students_by_class"
- Si la demande concerne la repartition des eleves par sexe (garcons/filles) : graph_type="students_by_gender"
- Si la demande concerne la totalite des inscriptions (reinscription vs nouvelle inscription) : graph_type="inscriptions_breakdown"
- Si la demande concerne la repartition des eleves par localite : graph_type="students_by_locality"
- Si la demande concerne les moyennes des notes par classe : graph_type="average_grades_by_class"
- Si la demande concerne les moyennes par matière : graph_type="average_grades_by_subject"
- Si la demande concerne la distribution des notes par trimestre : graph_type="grades_distribution"
- Si la demande concerne les meilleurs élèves par classe : graph_type="top_students_by_class"
- Tu DOIS fournir une introduction claire et professionnelle dans le champ "response" avant le graphique
- Ne jamais demamnder un élève

FORMAT STRICT JSON OBLIGATOIRE :

- CHAT :
{{
  "intent": "chat",
  "response": "texte naturel et professionnel pour l'utilisateur"
}}

- DOCUMENT :
{{
  "intent": "generate_document",
  "document_type": "attestation_inscription | attestation_presence | certificat_scolarite",
  "response": "message clair et professionnel pour l'utilisateur"
}}

- GRAPH :
{{
  "intent": "show_graph",
  "graph_type": "students_by_class | students_by_gender | inscriptions_breakdown | students_by_locality | average_grades_by_class | average_grades_by_subject | grades_distribution | top_students_by_class",
  "response": "texte professionnel d’introduction au graphique"
}}

CONTEXTE ELEVE :
{rag_context}

QUESTION UTILISATEUR :
{user_message}
"""

    return _normalize_payload(_call_llm_with_json(prompt))


def _classify_student_need(user_message: str) -> dict:
    """
    Fonction interne pour classifier si un message nécessite une recherche d'élève
    """
    # Extraire le message réel de la requête de classification
    match = re.search(r'Message: "([^"]+)"', user_message)
    if not match:
        return {"needs_student": True}
    
    actual_message = match.group(1)
    
    prompt = f"""
Analyse ce message et réponds UNIQUEMENT avec un JSON contenant un booléen "needs_student".

Règles :
- needs_student = true si l'utilisateur mentionne un NOM, PRÉNOM, MATRICULE, ou demande un DOCUMENT ADMINISTRATIF
- needs_student = false si c'est une conversation générale (salutations, questions sur le système, blagues, etc.)
- needs_student = false si l'utilisateur demande de l'aide ou des explications générales
- needs_student = false si la demande concerne des statistiques, des répartitions ou des graphes globaux 

Message: "{actual_message}"

JSON:
"""
    
    result = _call_llm_with_json(prompt)
    # S'assurer que le résultat a la bonne structure
    if isinstance(result, dict):
        if "needs_student" in result:
            return result
        elif "intent" in result:
            # Si le LLM a retourné un intent, le convertir
            return {"needs_student": result.get("intent") == "generate_document"}
    
    return {"needs_student": True}


def _call_llm_with_json(prompt: str) -> dict:
    """
    Fonction interne pour appeler le LLM, envoyer un prompt et récupérer une réponse JSON structurée.
    """
    try:
        response = client.chat.complete(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = _extract_mistral_content(response)
        print("RAW:", raw)

        # Recherche du JSON
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            # Fallback : texte brut converti en chat
            return {"intent": "chat", "response": raw or "Je n’ai pas compris votre demande."}

        # Conversion en dict
        data = json.loads(match.group())
        return data

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "intent": "chat",
            "response": "Une erreur est survenue lors de l'interprétation de votre demande. Veuillez reformuler."
        }


