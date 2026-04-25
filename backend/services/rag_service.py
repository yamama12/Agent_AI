"""
RAG Service – Student identification
Fault-tolerant matching
"""
import re
from difflib import SequenceMatcher

from Levenshtein import distance as levenshtein_distance

from database.eleve_repository import (
    get_eleve_data,
    get_eleve_data_by_name,
    get_person_status_by_id,
    get_person_status_by_name,
    search_eleve_candidates,
    search_by_phonetic,
)

# WORDS TO IGNORE
STOP_WORDS = {
    "donner","donne", "moi", "je", "l", "la", "le", "les", "de", "des", "d", "pour", "veux", "veut", "Génèrer", "générer", "generer", "generate", "génère",
    "attestation", "atestation","certificat", "inscription", "presence", "présence",
    "scolarite", "scolarité",
    "un", "une", "mon", "ma", "mes", "élève", "eleve", "du",
    "certificate", "certification", "for", "please", "i", "want", "a",
    "emploi", "temps", "horaire", "horaires", "jour", "jours", "cours", "seance", "seances",
    "note", "notes", "matiere", "matieres", "principal", "principaux", "principale", "principales",
    "dc1", "ds", "trimestre",
    "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
}

SURNAME_JOINERS = {
    "ben", "ibn", "bint",
    "el", "al",
    "bou", "bel", "bin",
    "abd", "abdel", "abdelkader", "abdelrahman",
    "hadj", "hadji", "haj", "hajj", "haji"
}


def _display_name(first_name: str | None = None, last_name: str | None = None) -> str:
    parts = [part.strip().title() for part in (first_name, last_name) if part and part.strip()]
    return " ".join(parts)


def _build_student_not_found_error(requested_identity: str | None = None):
    message = "Aucun eleve n'a ete retrouve dans notre etablissement."
    if requested_identity:
        message = (
            f"Aucun eleve n'a ete retrouve dans notre etablissement pour "
            f"'{requested_identity}'."
        )

    return {
        "code": "student_not_found",
        "message": (
            f"{message} Veuillez verifier l'orthographe ou utiliser le matricule "
            "de l'eleve."
        ),
        "requested_identity": requested_identity,
    }


def _build_not_student_error(person: dict | None = None, requested_identity: str | None = None):
    person = person or {}
    full_name = _display_name(person.get("PrenomFr"), person.get("NomFr"))
    identity = full_name or requested_identity

    message = "La personne demandee n'est pas enregistree comme eleve dans notre etablissement."
    if identity:
        message = (
            f"{identity} n'est pas enregistre(e) comme eleve dans notre etablissement."
        )

    return {
        "code": "not_student",
        "message": message,
        "requested_identity": identity,
        "person": person or None,
    }


def _build_missing_identity_error():
    return {
        "code": "missing_student_identity",
        "message": "Could not detect first and last name.",
    }

def normalize_name(s: str) -> str:
    if not s:
        return ""

    s = s.lower().strip()

    s = re.sub(r"[éèêë]", "e", s)
    s = re.sub(r"[àâä]", "a", s)
    s = re.sub(r"[îï]", "i", s)
    s = re.sub(r"[ôö]", "o", s)
    s = re.sub(r"[ûüù]", "u", s)
    s = re.sub(r"[ç]", "c", s)

    # Common transliteration variants
    s = re.sub(r"(?<=[^aeiou])y(?=[aeiou])", "i", s)
    s = re.sub(r"(?<=[aeiou])y(?=[^aeiou])", "i", s)
    s = re.sub(r"ey", "i", s)
    s = re.sub(r"ei", "i", s)
    s = re.sub(r"ai", "i", s)
    s = re.sub(r"ay", "i", s)

    # Interchangeable consonants
    s = re.sub(r"ph", "f", s)
    s = re.sub(r"ck", "k", s)
    s = re.sub(r"q", "k", s)
    s = re.sub(r"gh", "g", s)
    s = re.sub(r"dj", "j", s)
    s = re.sub(r"tj", "j", s)

    # Reduce double consonants
    s = re.sub(r"bb", "b", s)
    s = re.sub(r"dd", "d", s)
    s = re.sub(r"ff", "f", s)
    s = re.sub(r"gg", "g", s)
    s = re.sub(r"ll", "l", s)
    s = re.sub(r"mm", "m", s)
    s = re.sub(r"nn", "n", s)
    s = re.sub(r"pp", "p", s)
    s = re.sub(r"rr", "r", s)
    s = re.sub(r"ss", "s", s)
    s = re.sub(r"tt", "t", s)
    s = re.sub(r"zz", "z", s)

    # Remove silent h
    s = re.sub(r"h(?=[^aeiou])", "", s)
    s = re.sub(r"(?<=[^aeiou])h", "", s)
    s = re.sub(r"h$", "", s)

    # Keep only letters
    s = re.sub(r"[^a-z]", "", s)

    return s


def phonetic_code(s: str) -> str:
    s = normalize_name(s)
    if not s:
        return ""

    first_char = s[0]

    s = re.sub(r"[sz]", "s", s)
    s = re.sub(r"[cgqk]", "k", s)
    s = re.sub(r"[dt]", "t", s)
    s = re.sub(r"[bp]", "p", s)
    s = re.sub(r"[fv]", "f", s)
    s = re.sub(r"[jw]", "j", s)
    s = re.sub(r"[lr]", "l", s)
    s = re.sub(r"[mn]", "n", s)

    # check vowels in lowercase
    vowels = "aeiou"

    # Remove vowels except first char
    result = first_char
    for char in s[1:]:
        if char not in vowels:
            result += char

    # Remove duplicates and fix length
    result = re.sub(r"(.)\1+", r"\1", result)
    result = (result + "0000")[:6]

    return result


def similarity(a: str, b: str) -> float:
    a_n = normalize_name(a)
    b_n = normalize_name(b)

    if not a_n or not b_n:
        return 0.0

    length_weight = min(len(a_n), len(b_n)) / max(len(a_n), len(b_n), 1)

    lev = 1 - levenshtein_distance(a_n, b_n) / max(len(a_n), len(b_n), 1)
    seq = SequenceMatcher(None, a_n, b_n).ratio()

    prefix_len = min(3, len(a_n), len(b_n))
    prefix_a = a_n[:prefix_len]
    prefix_b = b_n[:prefix_len]
    prefix_score = 1 - levenshtein_distance(prefix_a, prefix_b) / prefix_len

    suffix_len = min(3, len(a_n), len(b_n))
    suffix_a = a_n[-suffix_len:] if len(a_n) >= suffix_len else a_n
    suffix_b = b_n[-suffix_len:] if len(b_n) >= suffix_len else b_n
    suffix_score = 1 - levenshtein_distance(suffix_a, suffix_b) / max(len(suffix_a), len(suffix_b), 1)

    weights = {
        "lev": 0.35 * length_weight,
        "seq": 0.25,
        "prefix": 0.25,
        "suffix": 0.15,
    }

    total_score = (
        lev * weights["lev"]
        + seq * weights["seq"]
        + prefix_score * weights["prefix"]
        + suffix_score * weights["suffix"]
    )

    weight_sum = sum(weights.values())
    return total_score / weight_sum if weight_sum > 0 else 0.0


def global_score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0

    ortho = similarity(a, b)

    phono_a = phonetic_code(a)
    phono_b = phonetic_code(b)

    if not phono_a or not phono_b:
        phono_score = 0.0
    else:
        phono_score = 1 - levenshtein_distance(phono_a, phono_b) / max(len(phono_a), len(phono_b), 1)

    avg_len = (len(a) + len(b)) / 2
    if avg_len <= 4:
        ortho_weight, phono_weight = 0.8, 0.2
    elif avg_len <= 6:
        ortho_weight, phono_weight = 0.7, 0.3
    else:
        ortho_weight, phono_weight = 0.6, 0.4

    return (ortho * ortho_weight) + (phono_score * phono_weight)


def full_name_score(target_first: str, target_last: str, c_first: str, c_last: str) -> float:
    full_target = f"{target_first} {target_last}"
    full_candidate = f"{c_first} {c_last}"
    return global_score(full_target, full_candidate)


def smart_match(target, candidates):
    scored = []
    target_norm = {
        "first": normalize_name(target["first"]),
        "last": normalize_name(target["last"]),
    }

    # Precompute these once
    first_len = len(target_norm["first"])
    last_len = len(target_norm["last"])
    min_first_score = 0.62 + (0.08 * (first_len / 10))
    min_last_score = 0.62 + (0.08 * (last_len / 10))

    for c in candidates:
        cand_first = c.get("PrenomFr") or ""
        cand_last = c.get("NomFr") or ""

        cand_first_parts = [p for p in re.findall(r"[A-Za-zÀ-ÿ]+", cand_first) if p]

        # Always score against the FULL first name 
        first_score_full = global_score(target["first"], cand_first)

        if len(cand_first_parts) > 1:
            first_score_parts = max(global_score(target["first"], part) for part in cand_first_parts)
            first_score = max(first_score_full, first_score_parts)
            full_first_exact_bonus = (normalize_name(target["first"]) == normalize_name(cand_first))
        else:
            first_score = first_score_full
            full_first_exact_bonus = (target_norm["first"] == normalize_name(cand_first))


        last_score = global_score(target["last"], cand_last)

        last_norm = target_norm["last"]
        if len(last_norm) <= 4:
            min_last_gate = 0.72
        elif len(last_norm) <= 6:
            min_last_gate = 0.76
        else:
            min_last_gate = 0.80

        # rescue if phonetics match
        last_phon_match = (phonetic_code(target["last"]) == phonetic_code(cand_last))

        if last_score < min_last_gate and not last_phon_match:
            continue

        full_score = full_name_score(target["first"], target["last"], cand_first, cand_last)

        if first_score >= min_first_score and last_score >= min_last_score:
            total = (
                first_score * 0.35
                + last_score  * 0.30
                + full_score  * 0.35
            )

            if full_first_exact_bonus:
                total += 0.20
            elif target_norm["first"][:3] == normalize_name(cand_first)[:3]:
                total += 0.10

            if target_norm["last"] == normalize_name(cand_last):
                total += 0.20
            elif target_norm["last"][:3] == normalize_name(cand_last)[:3]:
                total += 0.10

            if phonetic_code(target["first"]) == phonetic_code(cand_first):
                total += 0.12
            if phonetic_code(target["last"]) == phonetic_code(cand_last):
                total += 0.12
            if c.get("Actif") == 1:
                total += 0.05

            scored.append((c, min(total, 1.0)))

    if not scored:
        return "NOT_FOUND", None

    scored.sort(key=lambda x: x[1], reverse=True)
    print("TOP 5:")
    for c, s in scored[:5]:
        print(c["Matricule"], c.get("PrenomFr"), c.get("NomFr"), round(s, 3))
    best_score = scored[0][1]

    if best_score < 0.37:
        return "NOT_FOUND", None

    if len(scored) > 1:
        best_c, best_score = scored[0]
        second_c, second_score = scored[1]

        # If top results are extremely close, ask for clarification
        ambiguity_threshold = 0.05
        min_score_for_ambiguity = 0.85

        if best_score >= min_score_for_ambiguity and abs(best_score - second_score) <= ambiguity_threshold:
            return "AMBIGUOUS", [s[0] for s in scored[: min(3, len(scored))]]


    return "FOUND", scored[0][0]



def extract_name_from_message(message: str):
    message_clean = re.sub(
        r"\b(?:attestation|certificat|inscription|presence|présence|scolarite|scolarité|donner|donne|moi|je|pour|de|d['’]?|l[ea]?|du|un|une|emploi|temps|horaire|horaires|jour|jours|cours|seance|seances|note|notes|matiere|matieres|principal|principaux|principale|principales|dc1|ds|trimestre|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b",
        " ",
        message,
        flags=re.IGNORECASE,
    )

    words = [w.lower() for w in re.findall(r"[a-zA-ZÀ-ÿ]{2,}", message_clean)]
    valid = [w for w in words if w not in STOP_WORDS]

    if len(valid) < 2:
        return None, None, []

    last_parts = [valid[-1]]
    i = len(valid) - 2
    while i >= 0 and valid[i] in SURNAME_JOINERS:
        last_parts.insert(0, valid[i])
        i -= 1

    last = " ".join(last_parts).strip()

    # everything before last_parts => first (+ middle)
    remaining = valid[: i + 1]
    if not remaining:
        return None, None, []

    first = remaining[0]
    middle = remaining[1:]
    return last, first, middle


# Chercher les candidats dans la base
def retrieve_eleve_context(message: str):
    print(f"Received message: {message}")

    # 1) Student ID 
    m = re.search(r"\b\d{3,}\b", message)
    id_lookup_error = None
    if m:
        student_id = m.group()
        print(f"Search by ID: {student_id}")
        try:
            student = get_eleve_data(student_id)
            if student:
                return _build_context(student), None
        except Exception as e:
            print(f"Error with ID {student_id}: {e}")
            person_status = get_person_status_by_id(student_id)
            if person_status and not person_status.get("IsEleve"):
                return None, _build_not_student_error(
                    person=person_status,
                    requested_identity=f"ID {student_id}",
                )
            if not person_status:
                id_lookup_error = _build_student_not_found_error(
                    requested_identity=f"ID {student_id}"
                )

    # 2) First/last name
    last, first, middle = extract_name_from_message(message)

    if not last or not first:
        words = [w.lower() for w in re.findall(r"[a-zA-ZÀ-ÿ]{3,}", message)]
        valid = [w for w in words if w not in STOP_WORDS]
        if len(valid) >= 2:
            last, first = valid[-1], valid[-2]
            middle = [] 
            print(f"Fallback extraction: {first} {last}")
        else:
            return None, id_lookup_error or _build_missing_identity_error()

    # Build full first name only after we have first
    target_first_full = first
    requested_identity = _display_name(target_first_full, last)

    print(f"Searching student: {target_first_full} {last}")

    try:
        student = get_eleve_data_by_name(last, first)
        if student:
            print(f"Exact match: {student['PrenomFr']} {student['NomFr']}")
            return _build_context(student), None
    except Exception as e:
        print(f"Exact search failed: {e}")

    person_status = get_person_status_by_name(last, first)
    if person_status and not person_status.get("IsEleve"):
        return None, _build_not_student_error(
            person=person_status,
            requested_identity=requested_identity,
        )

    # try last name with middle parts joined (ex: 'bel hadj kacem')
    alt_last = None
    if middle:
        alt_last = " ".join(middle + [last]).strip()
        if alt_last and alt_last != last:
            print(f"Retry exact match with compound last name: {alt_last} {first}")
            try:
                student = get_eleve_data_by_name(alt_last, first)
                if student:
                    print(f"Exact match: {student['PrenomFr']} {student['NomFr']}")
                    return _build_context(student), None
            except Exception as e:
                print(f"Exact search failed (compound last): {e}")

            person_status = get_person_status_by_name(alt_last, first)
            if person_status and not person_status.get("IsEleve"):
                return None, _build_not_student_error(
                    person=person_status,
                    requested_identity=_display_name(first, alt_last),
                )

    last_variants = [last]
    if alt_last and alt_last != last:
        last_variants.append(alt_last)

    first_key = phonetic_code(first)

    candidates = []
    for last_variant in last_variants:
        last_key = phonetic_code(last_variant)
        candidates = search_by_phonetic(first_key, last_key)
        if candidates:
            break

    if not candidates:
        candidates = search_eleve_candidates(limit=5000, active_only=True)

    if not candidates:
        candidates = search_eleve_candidates(limit=15000, active_only=False)


    if not candidates:
        return None, _build_student_not_found_error(requested_identity=requested_identity)

    print(f"{len(candidates)} candidates to analyze")

    status, result = smart_match({"first": target_first_full, "last": last}, candidates)
    print(f"Match result #1: {status}")

    if status == "NOT_FOUND" and len(last_variants) > 1:
        status, result = smart_match({"first": target_first_full, "last": last_variants[1]}, candidates)
        print(f"Match result #1b (compound last): {status}")

    # swap
    if status == "NOT_FOUND" and last and target_first_full:
        status, result = smart_match({"first": last, "last": target_first_full}, candidates)
        print(f"Match result #2 (swapped): {status}")
        
    if status == "FOUND":
        try:
            student = get_eleve_data(result["Matricule"])
            print(f"Approx match: {student['PrenomFr']} {student['NomFr']}")
            return _build_context(student), None
        except Exception as e:
            print(f" Error loading student: {e}")

    if status == "AMBIGUOUS":
        candidates = [
            {
                "matricule": s.get("Matricule"),
                "prenom": s.get("PrenomFr"),
                "nom": s.get("NomFr"),
            }
            for s in result[:3]
        ]
        names = ", ".join(
            f"{c['prenom']} {c['nom']} ({c['matricule']})" for c in candidates
        )
        return None, {
            "code": "ambiguous",
            "message": (
                "Plusieurs élèves correspondent à votre demande :\n"
                f"{names}\n\n"
                "Merci d'indiquer le matricule ou la date de naissance."
            ),
            "candidates": candidates,
        }

    if not last:
        scored_firstnames = []
        for c in candidates:
            score = global_score(first, c["PrenomFr"])
            if score >= 0.75:
                scored_firstnames.append((c, score))

        if scored_firstnames:
            scored_firstnames.sort(key=lambda x: x[1], reverse=True)
            best = scored_firstnames[0]
            if best[1] >= 0.8:
                student = get_eleve_data(best[0]["Matricule"])
                print(f"Recherche par prénom uniquement: {student['PrenomFr']} {student['NomFr']}")
                return _build_context(student), (
                    f"Remarque: correspondance trouvée uniquement par prénom '{first}'. "
                    f"Veuillez vérifier le nom complet: {student['PrenomFr']} {student['NomFr']}"
                )

    return None, _build_student_not_found_error(requested_identity=requested_identity)



def _build_context(student_data: dict):
    context = f"""
Official student information:
Student: {student_data.get('PrenomFr')} {student_data.get('NomFr')}
Student ID: {student_data.get('Matricule')}
Date of birth: {student_data.get('DateNaissance')}
Place of birth: {student_data.get('LieuNaissance')}
Address: {student_data.get('AdresseFr')}
Phone: {student_data.get('Tel1')}
Nationality: {student_data.get('Nationalite')}
Current class: {student_data.get('Classe')}
School year: {student_data.get('AnneeScolaire')}
Registration date: {student_data.get('DateInscription')}
Registration status: {student_data.get('StatutInscription')}
Current year active: {'Yes' if student_data.get('AnneeActuelle') else 'No'}
"""
    print(
        f" Elève trouvé: {student_data.get('PrenomFr')} {student_data.get('NomFr')} "
        f"(ID: {student_data.get('Matricule')})"
    )

    return {
        "matricule": student_data.get("Matricule"),
        "context": context,
        "data": student_data,
    }
