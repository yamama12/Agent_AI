# CONTROLLEUR PRICINPAL DU CHATBOT
from api.conversation import Conversation
from api.message import Message
from database.db import get_db
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from database.eleve_repository import (
    get_student_main_subject_grades,
    get_student_schedule_for_day,
)
from services.rag_service import retrieve_eleve_context
from services.pdf_service import (
    generate_attestationInscri_pdf,
    generate_attestationPresence_pdf
)
from services.graph_service import (
    generate_graph_bundle,
)
from services.docx_service import generate_CertificatScolarite_docx
from ai.agent_ai import ask_agent, interpret_graph_summary
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

DAY_ALIASES = {
    "lundi": "lundi",
    "lun": "lundi",
    "monday": "lundi",
    "mardi": "mardi",
    "mar": "mardi",
    "tuesday": "mardi",
    "mercredi": "mercredi",
    "mer": "mercredi",
    "wednesday": "mercredi",
    "jeudi": "jeudi",
    "jeu": "jeudi",
    "thursday": "jeudi",
    "vendredi": "vendredi",
    "ven": "vendredi",
    "friday": "vendredi",
    "samedi": "samedi",
    "sam": "samedi",
    "saturday": "samedi",
    "dimanche": "dimanche",
    "dim": "dimanche",
    "sunday": "dimanche",
}

MAIN_SUBJECT_IDS = {63, 64, 67}

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
            "pending_consultation": None,
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


def _is_role_or_capabilities_question(message: str) -> bool:
    msg = _normalize_text(message)
    if not msg:
        return False

    signals = (
        "quel est ton role",
        "quel est votre role",
        "c est quoi ton role",
        "c est quoi votre role",
        "qu est ce que ton role",
        "qu est ce que votre role",
        "c est quoi ton travail",
        "c est quoi votre travail",
        "que fais tu",
        "que faites vous",
        "quel est ton objectif",
        "quel est votre objectif",
        "a quoi sers tu",
        "a quoi servez vous",
        "que peux tu faire",
        "que pouvez vous faire",
        "quelles sont tes fonctionnalites",
        "quelles sont vos fonctionnalites",
        "quelles sont tes missions",
        "quelles sont vos missions",
    )
    return any(signal in msg for signal in signals)


def _ask_role_capabilities_reply() -> dict:
    return ask_agent(
        user_message=(
            "L'utilisateur demande ton role, tes missions ou ce que tu peux faire. "
            "Reponds avec intent='chat' dans un ton professionnel, naturel et concis. "
            "Explique clairement que la generation des documents administratifs est dediee au personnel administrateur, "
            "et que la generation des graphes, des statistiques et des analyses est reservee a l'Administrateur. "
        ),
    )


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
        "moyenne",
        "moyennes",
        "note",
        "notes",
        "trimestre",
        "matiere",
        "matieres",
        "meilleur",
        "meilleurs",
        "eleve",
        "eleves",
        "classe",
        "classes",
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
    if any(token in msg for token in ("meilleur", "meilleurs", "top")):
        return "top_students_by_class"
    
    if "moyenne" in msg and "matiere" in msg:
        return "average_grades_by_subject"
    
    if "moyenne" in msg and "classe" in msg:
        return "average_grades_by_class"
    
    if any(token in msg for token in ("distribution", "trimestre")) and "note" in msg:
        return "grades_distribution"
    if "classe" in msg or "classes" in msg:
        return "students_by_class"
    return None


def _has_admin_consultation_access(roles: list[str]) -> bool:
    return "ROLE_ADMIN" in roles or "ROLE_SUPER_ADMIN" in roles


def _detect_student_consultation_type(message: str) -> str | None:
    msg = _normalize_text(message)
    if not msg:
        return None

    if any(token in msg for token in ("emploi du temps", "horaire", "horaires")):
        return "schedule"

    graph_terms = (
        "graphe",
        "graphique",
        "statistique",
        "statistiques",
        "distribution",
        "repartition",
        "moyenne",
        "moyennes",
        "top",
        "meilleur",
        "meilleurs",
    )
    if any(token in msg for token in ("dc1", "ds", "matiere principale", "matieres principales")):
        return "grades"
    if ("note" in msg or "notes" in msg) and not any(term in msg for term in graph_terms):
        return "grades"

    return None


def _extract_requested_day(message: str) -> str | None:
    msg = _normalize_text(message)
    if not msg:
        return None

    for alias in sorted(DAY_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", msg):
            return DAY_ALIASES[alias]
    return None


def _is_day_only_follow_up(message: str) -> bool:
    msg = _normalize_text(message)
    if not msg:
        return False

    requested_day = _extract_requested_day(message)
    if not requested_day:
        return False

    filler_words = {
        "le",
        "la",
        "les",
        "de",
        "du",
        "des",
        "pour",
        "stp",
        "svp",
        "s",
        "il",
        "te",
        "vous",
        "plait",
        "merci",
        "jour",
        "ce",
        "cette",
    }
    tokens = [token for token in msg.split() if token]
    meaningful_tokens = [token for token in tokens if token not in filler_words and token not in DAY_ALIASES]
    return len(meaningful_tokens) == 0


def _student_full_name(eleve_data: dict | None) -> str:
    eleve_data = eleve_data or {}
    return f"{eleve_data.get('PrenomFr', '')} {eleve_data.get('NomFr', '')}".strip()


def _missing_student_consultation_reply(
    session: dict,
    consultation_type: str,
    requested_identity: str | None = None,
):
    subject = "l'emploi du temps" if consultation_type == "schedule" else "les notes"
    if requested_identity:
        response = (
            f"Je n'ai pas pu identifier l'eleve demande ({requested_identity}) "
            f"pour consulter {subject}. Merci de preciser son nom complet ou son matricule."
        )
    else:
        response = (
            f"Je n'ai pas pu identifier l'eleve demande pour consulter {subject}. "
            "Merci de preciser son nom complet ou son matricule."
        )
    return _respond(session, response)


def _not_inscrit_consultation_reply(session: dict, eleve_data: dict, consultation_type: str):
    subject = "l'emploi du temps" if consultation_type == "schedule" else "les notes"
    full_name = _student_full_name(eleve_data)
    response = (
        f"L'eleve {full_name} n'est pas inscrit pour l'annee scolaire active. "
        f"La consultation de {subject} n'est donc pas possible."
    )
    return _respond(session, response)


def _ask_for_schedule_day_reply(session: dict, eleve_data: dict | None = None):
    full_name = _student_full_name(eleve_data)
    target = f" de {full_name}" if full_name else ""
    return _respond(
        session,
        f"Merci de preciser le jour souhaite pour consulter l'emploi du temps{target}.",
    )


def _no_school_day_reply(session: dict, requested_day: str):
    return _respond(
        session,
        f"Il n'y a pas de cours le {requested_day.capitalize()} dans l'etablissement.",
    )


def _format_schedule_fallback(eleve_data: dict, requested_day: str, schedule_rows: list[dict]) -> str:
    full_name = _student_full_name(eleve_data)
    day_label = requested_day.capitalize()
    if not schedule_rows:
        return f"Aucun cours n'est programme pour {full_name} le {day_label}."

    lines = [f"Emploi du temps de {full_name} pour {day_label} :"]
    for row in schedule_rows:
        slot_parts = [part for part in (row.get("heure_debut"), row.get("heure_fin")) if part]
        slot = " - ".join(slot_parts) if slot_parts else (row.get("seance") or "Seance non precisee")
        details = f"{slot} : {row.get('matiere') or 'Matiere non precisee'}"
        if row.get("salle"):
            salle_value = str(row["salle"]).strip()
            if salle_value.lower().startswith("salle"):
                details += f" | {salle_value}"
            else:
                details += f" | Salle {salle_value}"
        if row.get("enseignant_id"):
            details += f" | Enseignant ID {row['enseignant_id']}"
        if row.get("remarque"):
            details += f" | {row['remarque']}"
        lines.append(details)
    return "\n".join(lines)


def _schedule_consultation_reply(
    session: dict,
    eleve_data: dict,
    requested_day: str,
    schedule_rows: list[dict],
    rag_context: str = "",
):
    return _respond(session, _format_schedule_fallback(eleve_data, requested_day, schedule_rows))


def _format_grade_value(value: str | None) -> str:
    cleaned = str(value).strip() if value is not None else ""
    return cleaned if cleaned else "Non renseignee"


def _format_grades_fallback(eleve_data: dict, grade_rows: list[dict]) -> str:
    full_name = _student_full_name(eleve_data)
    if not grade_rows:
        return (
            f"Aucune note du trimestre 1 n'est disponible pour {full_name} "
            "dans les matieres principales."
        )

    lines = [f"Notes du trimestre 1 de {full_name} dans les matieres principales :"]
    for row in grade_rows:
        matiere = row.get("matiere") or f"Matiere {row.get('id_matiere')}"
        lines.append(
            f"{matiere} : DC1 = {_format_grade_value(row.get('DC1'))}, "
            f"DS = {_format_grade_value(row.get('DS'))}"
        )
    return "\n".join(lines)


def _grades_consultation_reply(
    session: dict,
    eleve_data: dict,
    grade_rows: list[dict],
    rag_context: str = "",
):
    filtered_rows = [
        row for row in grade_rows
        if row.get("id_matiere") in MAIN_SUBJECT_IDS
    ]
    return _respond(session, _format_grades_fallback(eleve_data, filtered_rows))


def _handle_admin_student_consultation(
    session: dict,
    roles: list[str],
    consultation_type: str,
    rag_result: dict | None,
    rag_context: str,
    requested_day: str | None = None,
    lookup_identity: str | None = None,
):
    if not _has_admin_consultation_access(roles):
        session["pending_consultation"] = None
        return _respond(
            session,
            "Cette fonctionnalite de consultation des informations eleve est reservee au personnel administrateur.",
        )

    if not rag_result or not rag_result.get("data"):
        session["pending_consultation"] = None
        return _missing_student_consultation_reply(session, consultation_type, lookup_identity)

    eleve_data = rag_result["data"]
    if eleve_data.get("StatutInscription") != "inscrit":
        session["pending_consultation"] = None
        return _not_inscrit_consultation_reply(session, eleve_data, consultation_type)

    session["last_student"] = rag_result
    session["last_context"] = rag_context

    if consultation_type == "schedule":
        if not requested_day:
            session["pending_consultation"] = {
                "type": "schedule",
                "rag_result": rag_result,
                "rag_context": rag_context,
            }
            return _ask_for_schedule_day_reply(session, eleve_data)

        if requested_day == "dimanche":
            session["pending_consultation"] = None
            return _no_school_day_reply(session, requested_day)

        error, schedule_rows = get_student_schedule_for_day(
            str(eleve_data.get("Matricule")),
            requested_day,
        )
        session["pending_consultation"] = None
        
        if error:
            return _respond(session, f"Erreur lors de la récupération de l'emploi du temps : {error.get('error', 'Erreur inconnue')}")
        
        return _schedule_consultation_reply(
            session,
            eleve_data,
            requested_day,
            schedule_rows,
            rag_context=rag_context,
        )

    error, grade_rows = get_student_main_subject_grades(str(eleve_data.get("Matricule")))
    session["pending_consultation"] = None
    
    return _grades_consultation_reply(
        session,
        eleve_data,
        grade_rows,
        rag_context=rag_context,
    )


def _ask_if_student_needed(session: dict, message: str) -> dict:
    """
    Demande à l'IA si une recherche d'élève est nécessaire pour ce message
    """
    forced_graph_type = _detect_graph_type_from_message(message)
    if forced_graph_type:
        return {"needs_student": False}
    if _detect_student_consultation_type(message):
        return {"needs_student": True}

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


def _is_document_request(message: str) -> bool:
    msg = _normalize_text(message)
    return "attestation" in msg or "certificat" in msg


def _get_lookup_error_code(error) -> str | None:
    if isinstance(error, dict):
        return error.get("code")
    return None


def _get_lookup_identity(error) -> str | None:
    if not isinstance(error, dict):
        return None

    person = error.get("person") or {}
    prenom = (person.get("PrenomFr") or "").strip()
    nom = (person.get("NomFr") or "").strip()
    full_name = f"{prenom} {nom}".strip()
    if full_name:
        return full_name

    identity = error.get("requested_identity")
    return identity.strip() if isinstance(identity, str) and identity.strip() else None


def _not_student_document_reply(session: dict, requested_identity: str | None = None):
    target = f" pour {requested_identity}" if requested_identity else ""
    llm_reply = _ask_agent_with_memory(
        session,
        user_message=(
            "Le personnel administratif demande un document administratif"
            f"{target}, mais cette personne n'est pas enregistree comme eleve "
            "dans notre etablissement. Explique clairement et professionnellement "
            "que cette personne n'est pas un eleve de l'etablissement et que le "
            "document demande ne peut donc pas etre genere."
        ),
    )
    fallback = (
        "La personne demandee n'est pas enregistree comme eleve dans notre "
        "etablissement. Le document demande ne peut donc pas etre genere."
    )
    return _respond(session, llm_reply.get("response", fallback))

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
    if _is_role_or_capabilities_question(message):
        llm_reply = _ask_role_capabilities_reply()
        return _respond(session, llm_reply.get("response", ""))
    forced_graph_type = _detect_graph_type_from_message(message)
    consultation_type = _detect_student_consultation_type(message)
    requested_day = _extract_requested_day(message)
    document_request = _is_document_request(message)

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

    pending_consultation = session.get("pending_consultation") or {}
    if (
        pending_consultation.get("type") == "schedule"
        and not forced_graph_type
        and not document_request
        and (consultation_type is None or _is_day_only_follow_up(message))
    ):
        pending = pending_consultation
        pending_rag = pending.get("rag_result") or session.get("last_student")
        pending_context = pending.get("rag_context") or session.get("last_context", "")

        if not requested_day:
            return _ask_for_schedule_day_reply(
                session,
                (pending_rag or {}).get("data") if isinstance(pending_rag, dict) else None,
            )

        return _handle_admin_student_consultation(
            session,
            roles,
            consultation_type="schedule",
            rag_result=pending_rag,
            rag_context=pending_context,
            requested_day=requested_day,
        )
    elif pending_consultation:
        session["pending_consultation"] = None

    # Étape 1: Demander à l'IA si ce message nécessite une recherche d'élève
    needs_student_check = _ask_if_student_needed(session, message)
    needs_student = needs_student_check.get("needs_student", True)
    
    print(f"DEBUG: Needs student check = {needs_student}")

    # Initialiser les variables RAG
    rag_result = None
    error = None
    rag_context = ""
    lookup_error_code = None
    lookup_identity = None

    # Étape 2: Ne faire la recherche RAG que si nécessaire
    if needs_student:
        rag_result, error = retrieve_eleve_context(message)
        lookup_error_code = _get_lookup_error_code(error)
        lookup_identity = _get_lookup_identity(error)
        
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

        if not rag_result and lookup_error_code == "missing_student_identity":
            if session.get("last_student"):
                rag_result = session.get("last_student")
                rag_context = session.get("last_context", "")

        # Vérifications spécifiques aux documents
        if "certificat" in message_lower:
            if not rag_result or not rag_result.get("data"):
                if lookup_error_code in {"not_student", "student_not_found"}:
                    return _not_student_document_reply(session, lookup_identity)
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
            
        if document_request and not rag_result and lookup_error_code in {"not_student", "student_not_found"}:
            return _not_student_document_reply(session, lookup_identity)

    if consultation_type:
        return _handle_admin_student_consultation(
            session,
            roles,
            consultation_type=consultation_type,
            rag_result=rag_result,
            rag_context=rag_context,
            requested_day=requested_day,
            lookup_identity=lookup_identity,
        )

    # Étape 3: APPEL LLM 
    decision = _ask_agent_with_memory(session, message, rag_context)

    if forced_graph_type and decision.get("intent") != "show_graph":
        decision = {
            "intent": "show_graph",
            "graph_type": forced_graph_type,
            "response": decision.get("response", ""),
        }

    if not decision or "intent" not in decision:
        return _respond(session, "Je n'ai pas compris votre demande.")

    # 📊 CAS GRAPHE
    if decision.get("intent") == "show_graph":

        if "ROLE_SUPER_ADMIN" not in roles:
            return _respond(session, "Vous n'avez pas l'autorisation de générer des graphiques. Cette fonctionnalité est réservée a l'Administrateur.")

        graph_type = decision.get("graph_type")
        graph_bundle = generate_graph_bundle(graph_type)

        if not graph_bundle:
            return _respond(session, "Type de graphe non supporte.")

        graphic_name = graph_bundle["graphic_name"]
        image_url = f"http://127.0.0.1:8000/statistics/{graphic_name}"
        graph_response = interpret_graph_summary(
            graph_type=graph_type,
            graph_summary=graph_bundle.get("summary", {}),
            user_message=message,
        )
        response_text = graph_response or decision.get("response", "")

        return _respond(
            session,
            response_text,
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
            if lookup_error_code in {"not_student", "student_not_found"}:
                return _not_student_document_reply(session, lookup_identity)
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
    session["pending_consultation"] = None
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


