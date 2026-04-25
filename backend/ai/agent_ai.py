import json
import os
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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


def _call_llm_text(prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model="gemma-3-4b-it",
            contents=prompt
        )
        return (response.text or "").strip()
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


def _format_percent(value) -> str:
    return f"{float(value):.1f}".replace(".", ",")


def _format_score(value) -> str:
    return f"{float(value):.2f}".replace(".", ",")


def _fallback_graph_interpretation(graph_type: str, graph_summary: dict) -> str:
    items = graph_summary.get("items") or []
    total = int(graph_summary.get("total") or 0)
    category_count = int(graph_summary.get("category_count") or len(items))

    if not items or total <= 0:
        return (
            "Le graphique a ete genere, mais aucune donnee exploitable n'est "
            "disponible pour proposer une interpretation fiable."
        )

    leader = items[0]
    leader_pct = _format_percent(leader.get("share") or 0)

    if graph_type == "students_by_gender" and len(items) >= 2:
        runner_up = items[1]
        diff = abs(int(leader.get("value") or 0) - int(runner_up.get("value") or 0))
        return (
            f"Le graphique presente {total} eleves au total. "
            f"La categorie la plus representee est {leader['label']} avec "
            f"{leader['value']} eleves ({leader_pct} %), contre "
            f"{runner_up['value']} pour {runner_up['label']}. "
            f"L'ecart entre les deux categories est de {diff} eleves."
        )

    if graph_type == "top_students_by_class":
        student_name = leader.get("student") or "Non precise"
        average_value = graph_summary.get("average_value")
        response = (
            f"Le graphique compare le meilleur eleve de {category_count} classes. "
            f"La meilleure performance est en {leader['label']} avec {student_name}, "
            f"qui obtient {_format_score(leader['value'])}/20."
        )
        if average_value:
            response += (
                f" La moyenne des meilleurs eleves est de "
                f"{_format_score(average_value)}/20."
            )
        return response

    scope = {
        "students_by_class": "classes",
        "students_by_locality": "localites",
        "inscriptions_breakdown": "types d'inscription",
        "average_grades_by_class": "classes",
        "average_grades_by_subject": "matieres",
        "grades_distribution": "trimestres",
        "top_students_by_class": "classes",
    }.get(graph_type, "categories")

    response = (
        f"Le graphique presente {total} eleves repartis sur {category_count} {scope}. "
        f"La categorie dominante est {leader['label']} avec {leader['value']} eleves "
        f"({leader_pct} % du total)."
    )

    if len(items) >= 2:
        runner_up = items[1]
        runner_up_pct = _format_percent(runner_up.get("share") or 0)
        response += (
            f" Elle est suivie de {runner_up['label']} avec "
            f"{runner_up['value']} eleves ({runner_up_pct} %)."
        )

    note = graph_summary.get("note")
    if note:
        response += f" {note}."

    return response


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
    text = _extract_llm_text(raw)
    if text:
        return _clean_professional_response(text, "show_graph")

    return _fallback_graph_interpretation(graph_type, graph_summary)

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
        response = client.models.generate_content(
            model="gemma-3-4b-it",
            contents=prompt
        )
        raw = (response.text or "").strip()
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


