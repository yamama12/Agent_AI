# CONTROLLEUR PRICINPAL DU CHATBOT
from api.conversation import Conversation
from api.message import Message
from database.db import get_db
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from services.rag_service import retrieve_eleve_context
from services.pdf_service import (
    generate_attestationInscri_pdf,
    generate_attestationPresence_pdf
)
from services.graph_service import (
    generate_students_by_class_chart_file,
    generate_students_by_gender_chart_file,
    generate_students_by_locality_chart_file,
)
from services.docx_service import generate_CertificatScolarite_docx
from ai.agent_ai import ask_agent
import json
import os
import re
import time
import unicodedata

router = APIRouter()

# Mémoire multi-tours (RAM)
SESSION_MEMORY = {}
MEMORY_TTL_SECONDS = 30 * 60
MEMORY_MAX_HISTORY = 6

# Request schema
class ChatRequest(BaseModel):
    message: str

class DeleteFilesRequest(BaseModel):
    files: List[str]

os.makedirs("files", exist_ok=True)

# Utils
def extract_attestation_type(text: str):
    text = text.lower()
    if "présence" in text or "presence" in text:
        return "attestation_presence"
    if "inscription" in text:
        return "attestation_inscription"
    return None


def _get_session_id(http_request: Request) -> str:
    header_id = (
        http_request.headers.get("x-session-id")
        or http_request.headers.get("x-sessionid")
        or http_request.headers.get("x-session")
    )
    if header_id:
        return header_id.strip()
    return http_request.client.host


def _cleanup_sessions(now: float):
    expired = [
        sid for sid, s in SESSION_MEMORY.items()
        if now - s.get("last_seen", now) > MEMORY_TTL_SECONDS
    ]
    for sid in expired:
        SESSION_MEMORY.pop(sid, None)


def _get_session(session_id: str):
    now = time.time()
    _cleanup_sessions(now)
    session = SESSION_MEMORY.get(session_id)
    if not session:
        session = {
            "history": [],
            "last_student": None,
            "last_context": "",
            "pending_document": None,
            "rag_result": None,
            "last_seen": now,
        }
        SESSION_MEMORY[session_id] = session
    session["last_seen"] = now
    return session


def _record_history(session: dict, role: str, text: str):
    if not text:
        return
    session["history"].append({"role": role, "text": text})
    if len(session["history"]) > MEMORY_MAX_HISTORY:
        session["history"] = session["history"][-MEMORY_MAX_HISTORY:]


def _build_history_text(session: dict) -> str:
    if not session.get("history"):
        return ""
    lines = []
    for item in session["history"]:
        role = "Utilisateur" if item["role"] == "user" else "Assistant"
        lines.append(f"{role}: {item['text']}")
    return "\n".join(lines)


def _ask_agent_with_memory(session: dict, user_message: str, rag_context: str = "") -> dict:
    history = _build_history_text(session)
    if history:
        user_message = (
            "HISTORIQUE (resume des derniers messages):\n"
            f"{history}\n\n"
            "DEMANDE ACTUELLE:\n"
            f"{user_message}"
        )
    return ask_agent(user_message=user_message, rag_context=rag_context)


def _respond(session: dict, text: str, extra: dict | None = None):
    _record_history(session, "agent_ai", text)
    payload = {"response": text}
    if extra:
        payload.update(extra)
    return payload


def _normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _detect_graph_type_from_message(message: str) -> str | None:
    msg = _normalize_text(message)
    if not msg:
        return None

    graph_signals = (
        "graphe",
        "graphique",
        "statistique",
        "statistiques",
        "repartition",
        "repartiton",
        "inscription",
        "reinscription",
        "nouvelle",
        "localite",
        "localites",
        "ville",
    )
    has_graph_signal = any(token in msg for token in graph_signals)
    if not has_graph_signal:
        return None

    if any(token in msg for token in ("sexe", "genre", "garcon", "garcons", "fille", "filles")):
        return "students_by_gender"
    if any(token in msg for token in ("localite", "localites", "ville", "villes")):
        return "students_by_locality"
    if "inscription" in msg and (
        "reinscription" in msg
        or "nouvelle inscription" in msg
        or "nouvelle" in msg
        or "totalite" in msg
        or "total" in msg
    ):
        return "inscriptions_breakdown"
    if "classe" in msg or "classes" in msg:
        return "students_by_class"
    return None

def _ask_if_student_needed(session: dict, message: str) -> dict:
    """
    Demande à l'IA si une recherche d'élève est nécessaire pour ce message
    """
    forced_graph_type = _detect_graph_type_from_message(message)
    if forced_graph_type:
        return {"needs_student": False}

    prompt = f"""
Tu es un agent ai qui analyse si une demande utilisateur nécessite de rechercher un élève dans la base de données.

Ta tâche : Déterminer si le message de l'utilisateur fait référence à un élève spécifique ou nécessite des informations personnelles d'un élève.

Règles :
- Si l'utilisateur mentionne un NOM, PRÉNOM, MATRICULE, ou demande un DOCUMENT ADMINISTRATIF (attestation, certificat) → NEEDS_STUDENT = true
- Si c'est une conversation générale (salutations, questions sur le système, météo, etc.) → NEEDS_STUDENT = false
- Si l'utilisateur demande de l'aide ou des explications sur les documents → NEEDS_STUDENT = false
- Si le message est ambigu mais pourrait concerner un élève → NEEDS_STUDENT = true

Message: "{message}"

Réponds UNIQUEMENT avec un JSON valide :
{{"needs_student": true}} ou {{"needs_student": false}}
"""
    try:
        response = ask_agent(user_message=prompt, rag_context="")
        if isinstance(response, dict) and "needs_student" in response:
            return response
        # Fallback: si la réponse n'est pas au bon format, extraire du texte
        response_text = response.get("response", "")
        if "true" in response_text.lower():
            return {"needs_student": True}
        return {"needs_student": False}
    except:
        # En cas d'erreur, par précaution, on suppose que l'élève est nécessaire
        return {"needs_student": True}

# Gestion cas des anciens élèves non inscrits
def _not_inscrit_reply(session: dict, eleve_data: dict):
    full_name = f"{eleve_data.get('PrenomFr','')} {eleve_data.get('NomFr','')}".strip()
    message = (
        f"L'eleve {full_name} n'est pas inscrit pour cette annee scolaire au le Collège & Lycée ISE. "
        "c'est un ancien eleve."
        "Par consequent, je ne peux pas generer le document demande. "
        "Veuillez verifier les informations et reessayer. "
        "Redige une reponse professionnelle."
    )
    llm_reply = _ask_agent_with_memory(session, user_message=message)
    return _respond(session, llm_reply.get("response", ""))


# Endpoint principal
@router.post("/chat/")
def chat(request: ChatRequest, http_request: Request):
    message = request.message.strip()
    message_lower = message.lower()
    session_id = _get_session_id(http_request)
    session = _get_session(session_id)

    roles_header = http_request.headers.get("x-user-roles", "[]")
    try:
        roles = json.loads(roles_header)
        if isinstance(roles, str):
            roles = [roles]
        elif not isinstance(roles, list):
            roles = []
    except Exception:
        roles = [r.strip() for r in roles_header.split(",") if r.strip()]

    print(f"DEBUG: Message='{message}'")
    print(f"DEBUG: Session ID={session_id}")
    print(f"DEBUG: User Roles={roles}")

    _record_history(session, "user", message)
    forced_graph_type = _detect_graph_type_from_message(message)

    # Gestion memoire pour attestation sans type
    if session.get("pending_document") == "attestation":
        doc_type = extract_attestation_type(message)

        if not doc_type:
            llm_reply = _ask_agent_with_memory(
                session,
                user_message=(
                    "L'utilisateur souhaite une attestation mais "
                    "n'a pas encore precise le type. "
                    "Pose une question claire et professionnelle "
                    "pour savoir s'il s'agit d'une attestation "
                    "d'inscription ou de presence."
                ),
            )
            return _respond(session, llm_reply.get("response", ""))

        rag_result = session.get("rag_result")
        eleve_data = rag_result["data"] if rag_result else None

        if not eleve_data:
            session["pending_document"] = None
        else:
            if eleve_data.get("StatutInscription") != "inscrit":
                session["pending_document"] = None
                return _not_inscrit_reply(session, eleve_data)

            pdf_file = (
                generate_attestationInscri_pdf(eleve_data)
                if doc_type == "attestation_inscription"
                else generate_attestationPresence_pdf(eleve_data)
            )

            file_url = f"http://127.0.0.1:8000/files/{pdf_file}"
            session["pending_document"] = None

            llm_reply = _ask_agent_with_memory(
                session,
                user_message="Le document a ete genere avec succes. Redige une reponse professionnelle.",
            )

            session["last_student"] = rag_result
            session["last_context"] = rag_result.get("context", "")
            return _respond(session, f"{llm_reply.get('response', '')}\n\n{file_url}")

    # Étape 1: Demander à l'IA si ce message nécessite une recherche d'élève
    needs_student_check = _ask_if_student_needed(session, message)
    needs_student = needs_student_check.get("needs_student", True)
    
    print(f"DEBUG: Needs student check = {needs_student}")

    # Initialiser les variables RAG
    rag_result = None
    error = None
    rag_context = ""

    # Étape 2: Ne faire la recherche RAG que si nécessaire
    if needs_student:
        rag_result, error = retrieve_eleve_context(message)
        
        if isinstance(error, dict) and error.get("code") == "ambiguous":
            candidates = error.get("candidates") or []
            formatted = "; ".join(
                f"{c.get('prenom')} {c.get('nom')} (ID {c.get('matricule')})" for c in candidates
            )
            llm_reply = _ask_agent_with_memory(
                session,
                user_message=(
                    "L'eleve demande est ambigu. Propose une question claire et professionnelle "
                    "pour demander de preciser l'eleve. Voici les candidats possibles : "
                    f"{formatted}."
                ),
            )
            return _respond(
                session,
                llm_reply.get("response", error.get("message")),
                {
                    "candidates": candidates,
                    "selection_request": message,
                },
            )

        rag_context = rag_result["context"] if rag_result else ""

        if not rag_result and error == "Could not detect first and last name.":
            if session.get("last_student"):
                rag_result = session.get("last_student")
                rag_context = session.get("last_context", "")

        # Vérifications spécifiques aux documents
        if "certificat" in message_lower:
            if not rag_result or not rag_result.get("data"):
                llm_reply = _ask_agent_with_memory(
                    session,
                    user_message=(
                        "L'utilisateur demande un certificat de scolarite "
                        "mais l'eleve n'a pas pu etre identifie. "
                        "Demande de preciser le nom complet."
                    ),
                )
                return _respond(session, llm_reply.get("response", ""))

            eleve_data = rag_result["data"]

            if eleve_data.get("StatutInscription") != "inscrit":
                return _not_inscrit_reply(session, eleve_data)

            docx_file = generate_CertificatScolarite_docx(eleve_data)
            file_url = f"http://127.0.0.1:8000/files/{docx_file}"

            llm_reply = _ask_agent_with_memory(
                session,
                user_message="Le certificat de scolarite a ete genere avec succes. Redige une reponse professionnelle.",
            )

            session["last_student"] = rag_result
            session["last_context"] = rag_context
            return _respond(session, f"{llm_reply.get('response', '')}\n\n{file_url}")

        # Attestation sans type -> Memoire pour demander le type
        if "attestation" in message_lower:
            doc_type = extract_attestation_type(message)

            if not doc_type and rag_result and rag_result.get("data"):
                session["pending_document"] = "attestation"
                session["rag_result"] = rag_result

                llm_reply = _ask_agent_with_memory(
                    session,
                    user_message=(
                        "L'utilisateur demande une attestation sans preciser le type. "
                        "Pose une question claire et professionnelle."
                    ),
                    rag_context=rag_context,
                )
                return _respond(session, llm_reply.get("response", ""))
            
        # Élève non trouvé
        if not rag_result and isinstance(error, str) and error.startswith("No student found"):
            llm_reply = _ask_agent_with_memory(
                session,
                user_message=(
                    "L'élève demandé n'est pas inscrit dans notre établissement. "
                    "le document demandé ne peut pas être généré. "
                    "Rédige une réponse professionnelle et claire pour informer l'utilisateur "
                ),
            )
            return _respond(session, llm_reply.get("response", ""))

    # Étape 3: APPEL LLM 
    decision = _ask_agent_with_memory(session, message, rag_context)

    if forced_graph_type and decision.get("intent") != "show_graph":
        decision = {
            "intent": "show_graph",
            "graph_type": forced_graph_type,
            "response": (
                "Voici le graphique demande. "
                "Il presente une vue claire de la repartition."
            ),
        }

    if not decision or "intent" not in decision:
        return _respond(session, "Je n'ai pas compris votre demande.")

    # 📊 CAS GRAPHE
    if decision.get("intent") == "show_graph":

        if "ROLE_SUPER_ADMIN" not in roles:
            return _respond(session, "Vous n'avez pas l'autorisation de générer des graphiques. Cette fonctionnalité est réservée a l'Administrateur.")

        graph_type = decision.get("graph_type")

        if graph_type == "students_by_class":
            Graphicname = generate_students_by_class_chart_file()

        elif graph_type == "students_by_gender":
            Graphicname = generate_students_by_gender_chart_file()

        elif graph_type == "students_by_locality":
            Graphicname = generate_students_by_locality_chart_file()

        else:
            return _respond(session, "Type de graphe non supporte.")

        image_url = f"http://127.0.0.1:8000/statistics/{Graphicname}"

        return _respond(
            session,
            decision.get("response", ""),
            extra={
                "graph": {
                    "type": graph_type,
                    "url": image_url
                }
            }
        )

    # CAS DOCUMENT
    response_text = decision.get("response", "")
    
    if decision.get("intent") == "generate_document":
        if "ROLE_ADMIN" not in roles:
            return _respond(session, "Cette fonctionnalité est réservée aux personnel administratifs.")
        if not rag_result or not rag_result.get("data"):
            llm_reply = _ask_agent_with_memory(
                session,
                user_message=(
                    "L'utilisateur demande un document administratif "
                    "mais l'eleve n'a pas pu etre identifie. "
                    "Demande de preciser le nom complet."
                ),
            )
            return _respond(session, llm_reply.get("response", ""))

        eleve_data = rag_result["data"]

        if eleve_data.get("StatutInscription") != "inscrit":
            return _not_inscrit_reply(session, eleve_data)

        doc_type = decision.get("document_type")
        file_url = None

        if doc_type == "attestation_inscription":
            pdf_file = generate_attestationInscri_pdf(eleve_data)
            file_url = f"http://127.0.0.1:8000/files/{pdf_file}"

        elif doc_type == "attestation_presence":
            pdf_file = generate_attestationPresence_pdf(eleve_data)
            file_url = f"http://127.0.0.1:8000/files/{pdf_file}"

        if file_url:
            response_text = f"{response_text}\n\n{file_url}"

    if rag_result and rag_result.get("data"):
        session["last_student"] = rag_result
        session["last_context"] = rag_context
        
    session["pending_document"] = None
    session["rag_result"] = None
    
    return _respond(session, response_text)

# Endpoint pour supprimer les fichiers générés (optionnel, peut être utilisé pour le nettoyage)
@router.post("/chat/delete-files")
def delete_files(payload: DeleteFilesRequest):
    deleted = []
    skipped = []

    for item in payload.files:
        raw = str(item).replace("\\", "/")
        if not raw:
            skipped.append(str(item))
            continue

        base_dir = "files"
        relative = raw
        if raw.startswith("statistics/"):
            base_dir = "statistics"
            relative = raw[len("statistics/"):]
        elif raw.startswith("files/"):
            base_dir = "files"
            relative = raw[len("files/"):]

        filename = os.path.basename(relative)
        if not filename:
            skipped.append(raw)
            continue

        file_path = os.path.join(base_dir, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                deleted.append(f"{base_dir}/{filename}")
            except Exception:
                skipped.append(f"{base_dir}/{filename}")
        else:
            skipped.append(f"{base_dir}/{filename}")

    return {"deleted": deleted, "skipped": skipped}

# Créer une conversation
@router.post("/conversations")
def create_conversation(db: Session = Depends(get_db)):
    conv = Conversation(title="Nouvelle Conversation")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

# Lister les conversations
@router.get("/conversations")
def get_conversations(db: Session = Depends(get_db)):
    return db.query(Conversation).order_by(Conversation.created_at.desc()).all()

# Messages d'une conversation
@router.get("/conversations/{conv_id}/messages")
def get_messages(conv_id: str, db: Session = Depends(get_db)):
    return db.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.created_at).all()

@router.post("/conversations/{conv_id}/messages")
def send_message(conv_id: str, payload: dict, db: Session = Depends(get_db)):
    user_msg = Message(
        conversation_id=conv_id,
        sender="user",
        text=payload["text"]
    )
    db.add(user_msg)
    db.commit()

    # Appel IA
    ai_response = ask_agent(payload["text"])

    bot_msg = Message(
        conversation_id=conv_id,
        sender="bot",
        text=ai_response
    )
    db.add(bot_msg)
    db.commit()

    return {
        "user": user_msg,
        "bot": bot_msg
    }


