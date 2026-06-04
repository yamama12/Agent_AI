import os
import mysql.connector

PRIMARY_SUBJECT_IDS = (63, 64, 67)
TRIMESTRE_1_ID = 31


def _get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
    )

#--------------------------------------------------------------------
# Extraction des données pour la génération des documents : 
#--------------------------------------------------------------------
def get_eleve_data(matricule: str):
    connection = _get_connection()

    cursor = connection.cursor(dictionary=True)

    try:
        query = """
                        SELECT 
                            TRIM(p.NomFr) AS NomFr,
                            TRIM(p.PrenomFr) AS PrenomFr,
                            TRIM(p.AdresseFr) AS AdresseFr,
                            TRIM(p.Tel1) AS Tel1,
                            e.id AS EleveId,
                            e.DateNaissance,
                            TRIM(l.LIBELLELOCALITEFR) AS LieuNaissance,
                            i.id AS InscriptionId,
                            i.Classe AS ClasseId,
                            i.groupe AS GroupeId,
                            TRIM(c.NOMCLASSEFR) AS Classe,
                            a.id AS AnneeScolaireId,
                            TRIM(n.NationaliteFr) AS Nationalite,
                            TRIM(a.AnneeScolaire) AS AnneeScolaire,
                            i.Date AS DateInscription,
                            a.Actif AS AnneeActuelle, 
                            CASE 
                                WHEN a.Actif = 1 THEN 'inscrit'
                                WHEN a.Actif = 0 THEN 'non_inscrit'
                                ELSE 'non_inscrit'
                            END AS statut_inscription
                        FROM personne p  
                        INNER JOIN eleve e ON p.id = e.IdPersonne
                        LEFT JOIN localite l ON p.Localite = l.IDLOCALITE
                        LEFT JOIN inscriptioneleve i ON e.id = i.Eleve AND i.Annuler = 0
                        LEFT JOIN classe c ON i.Classe = c.id
                        LEFT JOIN nationalite n ON p.Nationalite = n.id
                        LEFT JOIN anneescolaire a ON c.ID_ANNEE_SCO = a.id
                        WHERE p.id = %s
                        ORDER BY i.Date DESC
                        LIMIT 1
                """


        cursor.execute(query, (matricule,))
        row = cursor.fetchone()

        if not row:
            raise Exception("Élève non trouvé dans la base de données")

        result = {
            "Matricule": matricule,
            "NomFr": row["NomFr"],
            "PrenomFr": row["PrenomFr"],
            "EleveId": row.get("EleveId"),
            "InscriptionId": row.get("InscriptionId"),
            "ClasseId": row.get("ClasseId"),
            "GroupeId": row.get("GroupeId"),
            "DateNaissance": row["DateNaissance"],
            "LieuNaissance": row["LieuNaissance"],
            "Classe": row["Classe"],
            "AdresseFr": row["AdresseFr"],
            "Nationalite": row["Nationalite"],
            "Tel1": row["Tel1"],
            "AnneeScolaireId": row.get("AnneeScolaireId"),
            "AnneeScolaire": row["AnneeScolaire"],
            "DateInscription": row["DateInscription"],
            "StatutInscription": row["statut_inscription"],
            "AnneeActuelle": row["AnneeActuelle"],
        }

        if not row.get("AnneeActuelle"):
            result["StatutInscription"] = "non_inscrit"

        return result

    finally:
        cursor.close()
        connection.close()


def get_eleve_data_by_name(nom: str, prenom: str):
    connection = _get_connection()

    cursor = connection.cursor(dictionary=True)

    try:
        query = """
                    SELECT 
                        p.id AS Matricule,
                        TRIM(p.NomFr) AS NomFr,
                        TRIM(p.PrenomFr) AS PrenomFr,
                        TRIM(p.AdresseFr) AS AdresseFr,
                        TRIM(p.Tel1) AS Tel1,
                        e.id AS EleveId,
                        e.DateNaissance,
                        TRIM(l.LIBELLELOCALITEFR) AS LieuNaissance,
                        i.id AS InscriptionId,
                        i.Classe AS ClasseId,
                        i.groupe AS GroupeId,
                        TRIM(c.NOMCLASSEFR) AS Classe,
                        a.id AS AnneeScolaireId,
                        TRIM(n.NationaliteFr) AS Nationalite,
                        TRIM(a.AnneeScolaire) AS AnneeScolaire,
                        i.Date AS DateInscription,
                        a.Actif AS AnneeActuelle,
                        CASE 
                            WHEN a.Actif = 1 THEN 'inscrit'
                            ELSE 'non_inscrit'
                        END AS statut_inscription
                    FROM personne p
                    INNER JOIN eleve e ON p.id = e.IdPersonne
                    LEFT JOIN localite l ON p.Localite = l.IDLOCALITE
                    LEFT JOIN inscriptioneleve i ON e.id = i.Eleve AND i.Annuler = 0
                    LEFT JOIN classe c ON i.Classe = c.id
                    LEFT JOIN nationalite n ON p.Nationalite = n.id
                    LEFT JOIN anneescolaire a ON c.ID_ANNEE_SCO = a.id
                    WHERE LOWER(TRIM(p.NomFr)) = LOWER(TRIM(%s))
                    AND LOWER(TRIM(p.PrenomFr)) = LOWER(TRIM(%s))
                    ORDER BY i.Date DESC
                    LIMIT 1
                """


        cursor.execute(query, (nom, prenom))
        row = cursor.fetchone()

        if not row:
            raise Exception("Élève non trouvé")

        return {
            "Matricule": row["Matricule"],
            "NomFr": row["NomFr"],
            "PrenomFr": row["PrenomFr"],
            "EleveId": row.get("EleveId"),
            "InscriptionId": row.get("InscriptionId"),
            "ClasseId": row.get("ClasseId"),
            "GroupeId": row.get("GroupeId"),
            "DateNaissance": row["DateNaissance"],
            "LieuNaissance": row["LieuNaissance"],
            "Classe": row["Classe"],
            "AdresseFr": row["AdresseFr"],
            "Nationalite": row["Nationalite"],
            "Tel1": row["Tel1"],
            "AnneeScolaireId": row.get("AnneeScolaireId"),
            "AnneeScolaire": row["AnneeScolaire"],
            "DateInscription": row["DateInscription"],
            "StatutInscription": row["statut_inscription"],
            "AnneeActuelle": row["AnneeActuelle"],
        }

    finally:
        cursor.close()
        connection.close()


def get_student_parents_info(matricule: str):
    """
    Recupere les informations des parents d'un eleve:
    - Nom complet
    - Lien de parente
    - Numeros de telephone (Tel1, Tel2)
    - Etablissement

    Le matricule attendu correspond a l'id de la table personne de l'eleve.
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT
                TRIM(CONCAT_WS(' ', NULLIF(TRIM(pp.PrenomFr), ''), NULLIF(TRIM(pp.NomFr), ''))) AS NomComplet,
                TRIM(pp.Tel1) AS Tel1,
                TRIM(pp.Tel2) AS Tel2,
                TRIM(pa.Etablissement) AS Etablissement,
                TRIM(pe.Type) AS TypeParente
            FROM personne p_eleve
            INNER JOIN eleve e
                ON e.IdPersonne = p_eleve.id
            INNER JOIN parenteleve pe
                ON pe.Eleve = e.id
            INNER JOIN parent pa
                ON pa.id = pe.Parent
            LEFT JOIN personne pp
                ON pp.id = pa.Personne
            WHERE p_eleve.id = %s
            ORDER BY pe.id, pa.id
        """

        cursor.execute(query, (matricule,))
        rows = cursor.fetchall() or []

        formatted_rows = []
        for row in rows:
            formatted_rows.append(
                {
                    "NomComplet": (row.get("NomComplet") or "").strip(),
                    "Tel1": (row.get("Tel1") or "").strip(),
                    "Tel2": (row.get("Tel2") or "").strip(),
                    "Etablissement": (row.get("Etablissement") or "").strip(),
                    "TypeParente": (row.get("TypeParente") or "").strip(),
                }
            )

        return None, formatted_rows

    except Exception as e:
        return {"error": str(e)}, []

    finally:
        cursor.close()
        connection.close()


def get_person_status_by_id(person_id: str):
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
    )

    cursor = connection.cursor(dictionary=True)

    try:
        query = """
                    SELECT
                        p.id AS Matricule,
                        TRIM(p.NomFr) AS NomFr,
                        TRIM(p.PrenomFr) AS PrenomFr,
                        e.id AS EleveId
                    FROM personne p
                    LEFT JOIN eleve e ON p.id = e.IdPersonne
                    WHERE p.id = %s
                    LIMIT 1
                """

        cursor.execute(query, (person_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return {
            "Matricule": row["Matricule"],
            "NomFr": row["NomFr"],
            "PrenomFr": row["PrenomFr"],
            "IsEleve": row["EleveId"] is not None,
        }

    finally:
        cursor.close()
        connection.close()


def get_person_status_by_name(nom: str, prenom: str):
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
    )

    cursor = connection.cursor(dictionary=True)

    try:
        query = """
                    SELECT
                        p.id AS Matricule,
                        TRIM(p.NomFr) AS NomFr,
                        TRIM(p.PrenomFr) AS PrenomFr,
                        e.id AS EleveId
                    FROM personne p
                    LEFT JOIN eleve e ON p.id = e.IdPersonne
                    WHERE LOWER(TRIM(p.NomFr)) = LOWER(TRIM(%s))
                      AND LOWER(TRIM(p.PrenomFr)) = LOWER(TRIM(%s))
                    LIMIT 1
                """

        cursor.execute(query, (nom, prenom))
        row = cursor.fetchone()

        if not row:
            return None

        return {
            "Matricule": row["Matricule"],
            "NomFr": row["NomFr"],
            "PrenomFr": row["PrenomFr"],
            "IsEleve": row["EleveId"] is not None,
        }

    finally:
        cursor.close()
        connection.close()


def search_eleve_candidates(limit=500, active_only=True):
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
    )

    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                p.id AS Matricule,
                TRIM(p.NomFr) AS NomFr,
                TRIM(p.PrenomFr) AS PrenomFr,
                COALESCE(a.Actif, 0) AS Actif
            FROM personne p
            INNER JOIN eleve e ON p.id = e.IdPersonne
            LEFT JOIN inscriptioneleve i ON e.id = i.Eleve AND i.Annuler = 0
            LEFT JOIN classe c ON i.Classe = c.id
            LEFT JOIN anneescolaire a ON c.ID_ANNEE_SCO = a.id
        """

        if active_only:
            query += " WHERE a.Actif = 1 "

        query += """
            ORDER BY p.NomFr, p.PrenomFr
            LIMIT %s
        """

        cursor.execute(query, (limit,))
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()



def search_by_phonetic(prenom_key: str, nom_key: str, limit: int = 2000):
    if not prenom_key or not nom_key:
        return []

    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
    )
    cursor = connection.cursor(dictionary=True)

    try:
        query_a = """
            SELECT 
                p.id AS Matricule,
                TRIM(p.NomFr) AS NomFr,
                TRIM(p.PrenomFr) AS PrenomFr,
                c.NOMCLASSEFR AS Classe
            FROM personne p
            INNER JOIN eleve e ON p.id = e.IdPersonne
            LEFT JOIN inscriptioneleve i ON e.id = i.Eleve AND i.Annuler = 0
            LEFT JOIN classe c ON i.Classe = c.id
            LEFT JOIN anneescolaire a ON c.ID_ANNEE_SCO = a.id
            WHERE a.Actif = 1
              AND (p.nom_phonetic = %s OR LEFT(p.nom_phonetic, 4) = LEFT(%s, 4))
              AND (p.prenom_phonetic = %s OR LEFT(p.prenom_phonetic, 4) = LEFT(%s, 4))
            LIMIT %s
        """
        cursor.execute(query_a, (nom_key, nom_key, prenom_key, prenom_key, limit))
        rows = cursor.fetchall()
        if rows:
            return rows

        query_b = """
            SELECT 
                p.id AS Matricule,
                TRIM(p.NomFr) AS NomFr,
                TRIM(p.PrenomFr) AS PrenomFr,
                c.NOMCLASSEFR AS Classe
            FROM personne p
            INNER JOIN eleve e ON p.id = e.IdPersonne
            LEFT JOIN inscriptioneleve i ON e.id = i.Eleve AND i.Annuler = 0
            LEFT JOIN classe c ON i.Classe = c.id
            LEFT JOIN anneescolaire a ON c.ID_ANNEE_SCO = a.id
            WHERE a.Actif = 1
              AND (
                    p.nom_phonetic = %s OR LEFT(p.nom_phonetic, 4) = LEFT(%s, 4)
                 OR p.prenom_phonetic = %s OR LEFT(p.prenom_phonetic, 4) = LEFT(%s, 4)
              )
            LIMIT %s
        """
        cursor.execute(query_b, (nom_key, nom_key, prenom_key, prenom_key, limit))
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()



#--------------------------------------------------------------------
# Extraction des données pour la génération des graphes : 
#--------------------------------------------------------------------

# Obtenir le nombre d'élèves par classe pour l'année scolaire en cours. 
def get_student_active_enrollment(matricule: str):
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT
                p.id AS Matricule,
                e.id AS EleveId,
                i.id AS InscriptionId,
                i.Classe AS ClasseId,
                TRIM(c.NOMCLASSEFR) AS Classe,
                i.groupe AS GroupeId,
                a.id AS AnneeScolaireId,
                TRIM(a.AnneeScolaire) AS AnneeScolaire
            FROM personne p
            INNER JOIN eleve e
                ON p.id = e.IdPersonne
            INNER JOIN inscriptioneleve i
                ON e.id = i.Eleve
               AND i.Annuler = 0
            INNER JOIN anneescolaire a
                ON i.AnneeScolaire = a.id
            LEFT JOIN classe c
                ON i.Classe = c.id
            WHERE p.id = %s
              AND a.Actif = 1
            ORDER BY i.Date DESC, i.id DESC
            LIMIT 1
        """

        cursor.execute(query, (matricule,))
        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

#---------------------------------------------------------------
# Obtenir les notes de matières principales de l'élève.
#---------------------------------------------------------------
def get_student_main_subject_grades(
    matricule: str,
    trimestre_id: int | None = None,
):
    enrollment = get_student_active_enrollment(matricule)
    if not enrollment:
        return None, []

    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        subject_ids_sql = ", ".join(str(subject_id) for subject_id in PRIMARY_SUBJECT_IDS)
        inscription_id = enrollment.get("InscriptionId")
        classe_id = enrollment.get("ClasseId")

        def _has_any_grade(rows: list[dict]) -> bool:
            for row in rows:
                dc1 = str(row.get("DC1")).strip() if row.get("DC1") is not None else ""
                ds = str(row.get("DS")).strip() if row.get("DS") is not None else ""
                if dc1 or ds:
                    return True
            return False

        def _compact_name(value: str) -> str:
            cleaned = (value or "").strip().lower()
            return cleaned.replace(" ", "").replace("-", "").replace("'", "")

        def _get_student_name_variants() -> list[str]:
            cursor.execute(
                """
                SELECT TRIM(NomFr) AS NomFr, TRIM(PrenomFr) AS PrenomFr
                FROM personne
                WHERE id = %s
                LIMIT 1
                """,
                (matricule,),
            )
            person = cursor.fetchone() or {}
            nom = (person.get("NomFr") or "").strip()
            prenom = (person.get("PrenomFr") or "").strip()
            variants = {
                _compact_name(f"{prenom} {nom}"),
                _compact_name(f"{nom} {prenom}"),
                _compact_name(f"{prenom}{nom}"),
                _compact_name(f"{nom}{prenom}"),
            }
            return [v for v in variants if v]

        def _query_by_inscription(current_trimestre_id: int) -> list[dict]:
            if not inscription_id or not classe_id:
                return []

            query = f"""
                SELECT
                    m.id AS id_matiere,
                    COALESCE(
                        NULLIF(TRIM(m.NomMatiereFr), ''),
                        CONCAT('Matiere ', m.id)
                    ) AS matiere,
                    MAX(NULLIF(TRIM(n.DC1), '')) AS DC1,
                    MAX(NULLIF(TRIM(n.DS), '')) AS DS
                FROM matiere m
                LEFT JOIN noteeleveparmatiere n
                    ON n.id_matiere = m.id
                   AND n.id_inscription = %s
                   AND n.id_classe = %s
                   AND n.id_trimestre = %s
                   AND (n.Etat IN ('0', '1') OR n.Etat IS NULL)
                WHERE m.id IN ({subject_ids_sql})
                GROUP BY m.id, m.NomMatiereFr
                ORDER BY FIELD(m.id, {subject_ids_sql})
            """
            cursor.execute(query, (inscription_id, classe_id, current_trimestre_id))
            return cursor.fetchall()

        def _query_by_name(current_trimestre_id: int, name_variants: list[str]) -> list[dict]:
            if not name_variants:
                return []

            placeholders = ", ".join(["%s"] * len(name_variants))
            query = f"""
                SELECT
                    m.id AS id_matiere,
                    COALESCE(
                        NULLIF(TRIM(m.NomMatiereFr), ''),
                        CONCAT('Matiere ', m.id)
                    ) AS matiere,
                    MAX(NULLIF(TRIM(n.DC1), '')) AS DC1,
                    MAX(NULLIF(TRIM(n.DS), '')) AS DS
                FROM matiere m
                LEFT JOIN noteeleveparmatiere n
                    ON n.id_matiere = m.id
                   AND n.id_trimestre = %s
                   AND (n.Etat IN ('0', '1') OR n.Etat IS NULL)
                   AND REPLACE(REPLACE(REPLACE(LOWER(TRIM(n.nomprenom)), ' ', ''), '-', ''), "'", '') IN ({placeholders})
                WHERE m.id IN ({subject_ids_sql})
                GROUP BY m.id, m.NomMatiereFr
                ORDER BY FIELD(m.id, {subject_ids_sql})
            """
            params = [current_trimestre_id] + name_variants
            cursor.execute(query, tuple(params))
            return cursor.fetchall()

        if trimestre_id is None:
            cursor.execute(
                """
                SELECT id
                FROM trimestre
                WHERE actif = '1'
                ORDER BY id DESC
                LIMIT 1
                """
            )
            active_t = cursor.fetchone()
            preferred_trimestre = int(active_t["id"]) if active_t and active_t.get("id") is not None else TRIMESTRE_1_ID
        else:
            preferred_trimestre = int(trimestre_id)

        # 1) Chemin principal: inscription active
        rows = _query_by_inscription(preferred_trimestre)
        if _has_any_grade(rows):
            return enrollment, rows

        # 2) Fallback sur les trimestres de la meme inscription
        if inscription_id and classe_id:
            cursor.execute(
                f"""
                SELECT DISTINCT n.id_trimestre AS id_trimestre
                FROM noteeleveparmatiere n
                WHERE n.id_inscription = %s
                  AND n.id_classe = %s
                  AND n.id_matiere IN ({subject_ids_sql})
                  AND (n.Etat IN ('0', '1') OR n.Etat IS NULL)
                  AND (
                        NULLIF(TRIM(n.DC1), '') IS NOT NULL
                     OR NULLIF(TRIM(n.DS), '') IS NOT NULL
                  )
                ORDER BY n.id_trimestre DESC
                """,
                (inscription_id, classe_id),
            )
            for item in cursor.fetchall():
                candidate = int(item["id_trimestre"])
                if candidate == preferred_trimestre:
                    continue
                candidate_rows = _query_by_inscription(candidate)
                if _has_any_grade(candidate_rows):
                    return enrollment, candidate_rows

        # 3) Fallback orphan rows: match par nomprenom (quand anciennes inscriptions supprimees)
        name_variants = _get_student_name_variants()
        rows_by_name = _query_by_name(preferred_trimestre, name_variants)
        if _has_any_grade(rows_by_name):
            return enrollment, rows_by_name

        if name_variants:
            placeholders = ", ".join(["%s"] * len(name_variants))
            cursor.execute(
                f"""
                SELECT DISTINCT n.id_trimestre AS id_trimestre
                FROM noteeleveparmatiere n
                WHERE n.id_matiere IN ({subject_ids_sql})
                  AND (n.Etat IN ('0', '1') OR n.Etat IS NULL)
                  AND (
                        NULLIF(TRIM(n.DC1), '') IS NOT NULL
                     OR NULLIF(TRIM(n.DS), '') IS NOT NULL
                  )
                  AND REPLACE(REPLACE(REPLACE(LOWER(TRIM(n.nomprenom)), ' ', ''), '-', ''), "'", '') IN ({placeholders})
                ORDER BY n.id_trimestre DESC
                """,
                tuple(name_variants),
            )
            for item in cursor.fetchall():
                candidate = int(item["id_trimestre"])
                if candidate == preferred_trimestre:
                    continue
                candidate_rows = _query_by_name(candidate, name_variants)
                if _has_any_grade(candidate_rows):
                    return enrollment, candidate_rows

        return enrollment, rows_by_name if rows_by_name else rows

    finally:
        cursor.close()
        connection.close()


def get_students_count_by_classe():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
    )
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                c.NOMCLASSEFR AS classe,
                COUNT(e.id) AS NombreEleves
            FROM eleve e
            INNER JOIN inscriptioneleve i 
                ON e.id = i.Eleve AND i.Annuler = 0
            INNER JOIN classe c 
                ON i.Classe = c.id
            INNER JOIN anneescolaire a 
                ON c.ID_ANNEE_SCO = a.id
            WHERE a.Actif = 1
            GROUP BY c.NOMCLASSEFR
            ORDER BY NombreEleves DESC
        """
        cursor.execute(query)
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

# Obtenir le nombre d'élèves par sexe pour l'année scolaire en cours.
def get_students_count_by_gender():

    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
    )

    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                civ.libelleCiviliteFr AS sexe,
                COUNT(e.id) AS NombreEleves
            FROM eleve e
            INNER JOIN personne p
                ON e.IdPersonne = p.id
            INNER JOIN civilite civ
                ON p.Civilite = civ.idCivilite
            INNER JOIN inscriptioneleve i
                ON e.id = i.Eleve AND i.Annuler = 0
            INNER JOIN classe c
                ON i.Classe = c.id
            INNER JOIN anneescolaire a
                ON c.ID_ANNEE_SCO = a.id
            WHERE a.Actif = 1
            GROUP BY civ.libelleCiviliteFr
            ORDER BY NombreEleves DESC
        """

        cursor.execute(query)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


# Obtenir le nombre d'élèves par localité pour l'année scolaire en cours
def get_students_count_by_locality():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
    )
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                COALESCE(TRIM(l.LIBELLELOCALITEFR), 'Non spécifiée') AS localite,
                COUNT(DISTINCT e.id) AS NombreEleves
            FROM eleve e
            INNER JOIN personne p 
                ON e.IdPersonne = p.id
            INNER JOIN inscriptioneleve i 
                ON e.id = i.Eleve AND i.Annuler = 0
            INNER JOIN classe c 
                ON i.Classe = c.id
            INNER JOIN anneescolaire a 
                ON c.ID_ANNEE_SCO = a.id
            LEFT JOIN localite l 
                ON p.Localite = l.IDLOCALITE
            WHERE a.Actif = 1
            GROUP BY l.LIBELLELOCALITEFR
            HAVING COUNT(DISTINCT e.id) >= 5  -- Ne montre que les localités avec au moins 5 élèves
            ORDER BY NombreEleves DESC, localite
            LIMIT 15  -- Top 15 localités
        """
        cursor.execute(query)
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

#--------------------------------------------------------------------
# Extraction des données pour les graphiques de notes
#--------------------------------------------------------------------

def _safe_cast_to_decimal(value):
    """
    Convertit une valeur en nombre décimal de façon sécurisée
    Gère les virgules et les points comme séparateurs décimaux
    """
    if value is None or str(value).strip() == '':
        return 0
    try:
        # Remplacer la virgule par un point
        cleaned = str(value).replace(',', '.').strip()
        return float(cleaned)
    except:
        return None


def _get_notes_from_row(row):
    notes = []
    
    for col in ['orale', 'DS', 'DC1']:
        note = _safe_cast_to_decimal(row.get(col))
        if note is not None:
            notes.append(note)
    
    # IMPORTANT : en dehors de la boucle
    if not notes:
        notes.append(0)
    
    return notes


def get_average_grades_by_class(annee_scolaire: str = None, trimestre_id: str = None):
    """
    Récupère la moyenne des notes par classe
    Note: Par défaut, utilise le trimestre 1 (id=31)
    Prend en compte orale, DS et DC1
    """
    if trimestre_id is None:
        trimestre_id = "31"
    
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
    )
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                c.NOMCLASSEFR AS classe,
                n.id_inscription,
                COALESCE(NULLIF(TRIM(n.orale), ''), 0) AS orale,
                COALESCE(NULLIF(TRIM(n.DS), ''), 0) AS DS,
                COALESCE(NULLIF(TRIM(n.DC1), ''), 0) AS DC1,
                n.id_matiere
            FROM noteeleveparmatiere n
            INNER JOIN classe c ON n.id_classe = c.id
            INNER JOIN anneescolaire a ON c.ID_ANNEE_SCO = a.id
            WHERE n.id_trimestre = %s
            AND a.AnneeScolaire = '2024/2025'
            AND (n.Etat = '1' OR n.Etat IS NULL)
        """
        
        cursor.execute(query, (trimestre_id,))
        rows = cursor.fetchall()
        
        print(f"Nombre de lignes récupérées pour classes: {len(rows)}")
        
        # Traitement des données - regroupement par classe, élève, matière
        # Pour calculer la moyenne par matière d'abord
        eleve_matiere_notes = {}
        
        for row in rows:
            classe = row['classe']
            if not classe:
                continue
            
            eleve_id = row['id_inscription']
            matiere_id = row['id_matiere']
            
            key = f"{classe}_{eleve_id}_{matiere_id}"
            
            if key not in eleve_matiere_notes:
                eleve_matiere_notes[key] = {
                    'classe': classe,
                    'eleve_id': eleve_id,
                    'matiere_id': matiere_id,
                    'notes': []
                }
            
            # Ajouter les notes de cette ligne
            notes = _get_notes_from_row(row)
            eleve_matiere_notes[key]['notes'].extend(notes)
        
        # Calculer la moyenne par matière pour chaque élève
        class_data = {}
        
        for key, data in eleve_matiere_notes.items():
            if data['notes']:
                classe = data['classe']
                
                if classe not in class_data:
                    class_data[classe] = {
                        'sum_moyennes_matieres': 0,
                        'count_matieres': 0,
                        'eleves': set(),
                        'matieres': set()
                    }
                
                # Moyenne de l'élève pour cette matière
                moyenne_matiere = sum(data['notes']) / len(data['notes'])
                
                class_data[classe]['sum_moyennes_matieres'] += moyenne_matiere
                class_data[classe]['count_matieres'] += 1
                class_data[classe]['eleves'].add(data['eleve_id'])
                class_data[classe]['matieres'].add(data['matiere_id'])
        
        # Formater les résultats
        result = []
        for classe, data in class_data.items():
            if data['count_matieres'] > 0:
                moyenne = data['sum_moyennes_matieres'] / data['count_matieres']
                result.append({
                    'classe': classe,
                    'MoyenneGenerale': round(moyenne, 2),
                    'NombreEleves': len(data['eleves']),
                    'NombreMatieres': len(data['matieres'])
                })
        
        result.sort(key=lambda x: x['MoyenneGenerale'], reverse=True)
        
        print(f"Résultat classes: {len(result)} classes traitées")
        if result:
            print(f"Première classe: {result[0]}")
        
        return result

    finally:
        cursor.close()
        connection.close()


def get_average_grades_by_subject(trimestre_id: str = None):
    """
    Récupère la moyenne des notes par matière
    Prend en compte orale, DS et DC1
    """
    if trimestre_id is None:
        trimestre_id = "31"
    
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
    )
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                m.NomMatiereFr AS matiere,
                n.id_inscription,
                COALESCE(NULLIF(TRIM(n.orale), ''), 0) AS orale,
                COALESCE(NULLIF(TRIM(n.DS), ''), 0) AS DS,
                COALESCE(NULLIF(TRIM(n.DC1), ''), 0) AS DC1
            FROM noteeleveparmatiere n
            INNER JOIN matiere m ON n.id_matiere = m.id
            INNER JOIN classe c ON n.id_classe = c.id
            INNER JOIN anneescolaire a ON c.ID_ANNEE_SCO = a.id
            WHERE n.id_trimestre = %s
            AND a.AnneeScolaire = '2024/2025'
            AND (n.Etat = '1' OR n.Etat IS NULL)
        """
        
        cursor.execute(query, (trimestre_id,))
        rows = cursor.fetchall()
        
        print(f"Nombre de lignes récupérées pour matières: {len(rows)}")
        
        # Regroupement par matière, élève
        eleve_matiere_notes = {}
        
        for row in rows:
            matiere = row['matiere']
            if not matiere:
                continue
            
            eleve_id = row['id_inscription']
            
            key = f"{matiere}_{eleve_id}"
            
            if key not in eleve_matiere_notes:
                eleve_matiere_notes[key] = {
                    'matiere': matiere,
                    'eleve_id': eleve_id,
                    'notes': []
                }
            
            notes = _get_notes_from_row(row)
            eleve_matiere_notes[key]['notes'].extend(notes)
        
        # Calculer la moyenne par élève puis par matière
        subject_data = {}
        
        for key, data in eleve_matiere_notes.items():
            if data['notes']:
                matiere = data['matiere']
                
                if matiere not in subject_data:
                    subject_data[matiere] = {
                        'sum_moyennes_eleves': 0,
                        'count_eleves': 0,
                        'eleves': set()
                    }
                
                # Moyenne de l'élève pour cette matière
                moyenne_eleve = sum(data['notes']) / len(data['notes'])
                
                subject_data[matiere]['sum_moyennes_eleves'] += moyenne_eleve
                subject_data[matiere]['count_eleves'] += 1
                subject_data[matiere]['eleves'].add(data['eleve_id'])
        
        # Formater les résultats
        result = []
        for matiere, data in subject_data.items():
            if data['count_eleves'] >= 5:  # Au moins 5 élèves
                moyenne = data['sum_moyennes_eleves'] / data['count_eleves']
                result.append({
                    'matiere': matiere,
                    'Moyenne': round(moyenne, 2),
                    'NombreEleves': len(data['eleves'])
                })
        
        result.sort(key=lambda x: x['Moyenne'], reverse=True)
        
        print(f"Résultat matières: {len(result)} matières traitées")
        
        return result

    finally:
        cursor.close()
        connection.close()


def get_grades_distribution_by_trimestre():
    """
    Récupère la distribution des notes pour le trimestre 1
    Prend en compte orale, DS et DC1
    """
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
    )
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
                        SELECT 
            t.nom_trimestre AS trimestre,
            n.id_inscription,
            COALESCE(NULLIF(TRIM(n.orale), ''), 0) AS orale,
            COALESCE(NULLIF(TRIM(n.DS), ''), 0) AS DS,
            COALESCE(NULLIF(TRIM(n.DC1), ''), 0) AS DC1
        FROM noteeleveparmatiere n
        INNER JOIN trimestre t ON n.id_trimestre = t.id
        LEFT JOIN classe c ON n.id_classe = c.id
        LEFT JOIN anneescolaire a ON c.ID_ANNEE_SCO = a.id
        WHERE n.id_trimestre = '31'
        AND (n.Etat = '1' OR n.Etat IS NULL)
        AND (
            a.AnneeScolaire = '2024/2025'
            OR a.id IS NULL
        )
                        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"Nombre de lignes récupérées pour distribution: {len(rows)}")
        
        # Regroupement par élève pour calculer sa moyenne générale
        eleve_notes = {}
        
        for row in rows:
            trimestre = row['trimestre']
            if not trimestre:
                trimestre = "Trimestre 1"
            
            eleve_id = row['id_inscription']
            
            key = f"{trimestre}_{eleve_id}"
            
            if key not in eleve_notes:
                eleve_notes[key] = {
                    'trimestre': trimestre,
                    'eleve_id': eleve_id,
                    'notes': []
                }
            
            notes = _get_notes_from_row(row)
            eleve_notes[key]['notes'].extend(notes)
        
        # Calculer la moyenne par élève
        trimestre_data = {}
        
        for key, data in eleve_notes.items():
            if data['notes']:
                trimestre = data['trimestre']
                
                if trimestre not in trimestre_data:
                    trimestre_data[trimestre] = {
                        'moyennes_eleves': [],
                        'eleves': set()
                    }
                
                # Moyenne générale de l'élève
                moyenne_eleve = sum(data['notes']) / len(data['notes'])
                
                trimestre_data[trimestre]['moyennes_eleves'].append(moyenne_eleve)
                trimestre_data[trimestre]['eleves'].add(data['eleve_id'])
        
        # Formater les résultats
        result = []
        for trimestre, data in trimestre_data.items():
            if data['moyennes_eleves']:
                result.append({
                    'trimestre': trimestre,
                    'MoyenneGenerale': round(sum(data['moyennes_eleves']) / len(data['moyennes_eleves']), 2),
                    'NoteMin': round(min(data['moyennes_eleves']), 2),
                    'NoteMax': round(max(data['moyennes_eleves']), 2),
                    'NombreEleves': len(data['eleves'])
                })
        
        print(f"Résultat distribution: {len(result)} trimestres traités")
        
        return result

    finally:
        cursor.close()
        connection.close()


def get_top_students_by_class(limit_per_class: int = 3):
    """
    Récupère les meilleurs élèves par classe
    Prend en compte orale, DS et DC1
    """
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
    )
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                c.NOMCLASSEFR AS classe,
                n.id_inscription,
                n.nomprenom AS nom_eleve,
                COALESCE(NULLIF(TRIM(n.orale), ''), 0) AS orale,
                COALESCE(NULLIF(TRIM(n.DS), ''), 0) AS DS,
                COALESCE(NULLIF(TRIM(n.DC1), ''), 0) AS DC1,
                n.id_matiere
            FROM noteeleveparmatiere n
            INNER JOIN classe c ON n.id_classe = c.id
            INNER JOIN anneescolaire a ON c.ID_ANNEE_SCO = a.id
            WHERE n.id_trimestre = '31'
            AND a.AnneeScolaire = '2024/2025'
            AND (n.Etat = '1' OR n.Etat IS NULL)
        """

        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"Nombre de lignes récupérées pour top students: {len(rows)}")
        
        # Regroupement par élève et matière
        eleve_matiere_notes = {}
        
        for row in rows:
            classe = row['classe']
            if not classe:
                continue
            
            eleve_id = row['id_inscription']
            matiere_id = row['id_matiere']
            
            key = f"{classe}_{eleve_id}_{matiere_id}"
            
            if key not in eleve_matiere_notes:
                eleve_matiere_notes[key] = {
                    'classe': classe,
                    'eleve_id': eleve_id,
                    'nom_eleve': row['nom_eleve'],
                    'matiere_id': matiere_id,
                    'notes': []
                }
            
            notes = _get_notes_from_row(row)
            eleve_matiere_notes[key]['notes'].extend(notes)
        
        # Calculer la moyenne par matière puis la moyenne générale par élève
        eleve_moyennes = {}
        
        for key, data in eleve_matiere_notes.items():
            if data['notes']:
                eleve_id = data['eleve_id']
                classe = data['classe']
                
                matiere_key = f"{classe}_{eleve_id}"
                
                if matiere_key not in eleve_moyennes:
                    eleve_moyennes[matiere_key] = {
                        'classe': classe,
                        'nom_eleve': data['nom_eleve'],
                        'sum_moyennes_matieres': 0,
                        'count_matieres': 0
                    }
                
                # Moyenne pour cette matière
                moyenne_matiere = sum(data['notes']) / len(data['notes'])
                
                eleve_moyennes[matiere_key]['sum_moyennes_matieres'] += moyenne_matiere
                eleve_moyennes[matiere_key]['count_matieres'] += 1
        
        # Calculer la moyenne générale
        students = []
        for key, data in eleve_moyennes.items():
            if data['count_matieres'] >= 2:  # Au moins 2 matières
                moyenne = data['sum_moyennes_matieres'] / data['count_matieres']
                students.append({
                    'classe': data['classe'],
                    'nom_eleve': data['nom_eleve'],
                    'moyenne': round(moyenne, 2)
                })
        
        print(f"Nombre d'élèves avec moyenne: {len(students)}")
        
        # Grouper par classe et prendre les top N
        students_by_class = {}
        for student in students:
            classe = student['classe']
            if classe not in students_by_class:
                students_by_class[classe] = []
            students_by_class[classe].append(student)
        
        # Trier et limiter
        result = []
        for classe, class_students in students_by_class.items():
            class_students.sort(key=lambda x: x['moyenne'], reverse=True)
            for i, student in enumerate(class_students[:limit_per_class]):
                result.append({
                    'classe': classe,
                    'nom_eleve': student['nom_eleve'],
                    'moyenne': student['moyenne'],
                    'rang': i + 1
                })
        
        result.sort(key=lambda x: (x['classe'], x['rang']))
        
        print(f"Résultat top students: {len(result)} élèves sélectionnés")
        
        return result

    finally:
        cursor.close()
        connection.close()


def get_inscriptions_breakdown():
    """
    Récupère la répartition des inscriptions (Nouvelle vs Réinscription)
    pour l'année scolaire en cours
    """
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        charset="utf8mb4",
    )
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                CASE 
                    WHEN i.TypeInscri = 'N' OR i.TypeInscri = 'Nouvelle' THEN 'Nouvelle Inscription'
                    WHEN i.TypeInscri = 'R' OR i.TypeInscri = 'Réinscription' THEN 'Réinscription'
                    ELSE 'Autre'
                END AS type_inscription,
                COUNT(DISTINCT i.Eleve) AS NombreEleves
            FROM inscriptioneleve i
            INNER JOIN classe c ON i.Classe = c.id
            INNER JOIN anneescolaire a ON c.ID_ANNEE_SCO = a.id
            WHERE i.Annuler = 0
              AND a.AnneeScolaire = '2024/2025'
            GROUP BY 
                CASE 
                    WHEN i.TypeInscri = 'N' OR i.TypeInscri = 'Nouvelle' THEN 'Nouvelle Inscription'
                    WHEN i.TypeInscri = 'R' OR i.TypeInscri = 'Réinscription' THEN 'Réinscription'
                    ELSE 'Autre'
                END
            ORDER BY NombreEleves DESC
        """
        
        cursor.execute(query)
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


#--------------------------------------------------------------------
# Extraction des données pour la consultation de l'emploi du temps
#--------------------------------------------------------------------

def get_student_schedule_for_day(matricule: str, requested_day: str):
    """
    Récupère l'emploi du temps d'un élève pour un jour spécifique.
    
    Args:
        matricule: Identifiant de la personne (élève)
        requested_day: Jour demandé en français (lundi, mardi, etc.)
    
    Returns:
        Tuple (error_or_none, schedule_rows)
    """
    connection = _get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Mapping des jours en français vers les IDs de la base de données
        day_mapping = {
            'lundi': 1,
            'mardi': 2,
            'mercredi': 3,
            'jeudi': 4,
            'vendredi': 5,
            'samedi': 6,
        }
        
        day_id = day_mapping.get(requested_day.lower())
        if not day_id:
            return {"error": f"Jour invalide : {requested_day}"}, []
        
        # Récupérer les informations de l'élève d'abord
        eleve_data = get_eleve_data(matricule)
        if not eleve_data:
            return {"error": "Élève non trouvé"}, []
        
        classe_id = eleve_data.get("ClasseId")
        groupe_id = eleve_data.get("GroupeId")
        annee_scolaire_id = eleve_data.get("AnneeScolaireId")
        
        if not classe_id:
            return {"error": "Classe non trouvée pour cet élève"}, []
        
        print(f"DEBUG get_student_schedule_for_day:")
        print(f"  Matricule: {matricule}")
        print(f"  Jour demandé: {requested_day} (ID: {day_id})")
        print(f"  Classe ID: {classe_id}")
        print(f"  Groupe ID: {groupe_id}")
        print(f"  Année scolaire ID: {annee_scolaire_id}")
        
        # Récupérer l'emploi du temps
        query = """
                SELECT 
                    e.id,
                    e.Jour,
                    j.libelleJourFr AS jour_label,
                    e.Matiere,
                    m.NomMatiereFr AS matiere,
                    e.Salle,
                    s.nomSalleFr AS salle,
                    e.Enseignant,

                    -- depuis personne maintenant
                    per.PrenomFr AS enseignant_prenom,
                    per.NomFr AS enseignant_nom,

                    COALESCE(sc_debut.debut, CAST(CONCAT(e.SeanceDebut, ':00') AS CHAR)) COLLATE utf8mb4_0900_ai_ci AS heure_debut,
                    COALESCE(sc_fin.fin, CAST(CONCAT(e.SeanceFin, ':00') AS CHAR)) COLLATE utf8mb4_0900_ai_ci AS heure_fin,
                    COALESCE(sc_debut.nomSeance, CAST(CONCAT('Seance ', e.SeanceDebut, '-', e.SeanceFin) AS CHAR)) COLLATE utf8mb4_0900_ai_ci AS seance,
                    
                    e.Remarque,
                    e.Groupe

                FROM emploidutemps e

                LEFT JOIN jour j ON e.Jour = j.id
                LEFT JOIN matiere m ON e.Matiere = m.id
                LEFT JOIN salle s ON e.Salle = s.id

                LEFT JOIN enseingant en ON e.Enseignant = en.id
                LEFT JOIN personne per ON en.idPersonne = per.id

                LEFT JOIN seance sc_debut ON e.SeanceDebut = sc_debut.id
                LEFT JOIN seance sc_fin ON e.SeanceFin = sc_fin.id

                WHERE e.Classe = %s
                AND e.Jour = %s
                AND e.AnneeScolaire = %s

                ORDER BY e.SeanceDebut, e.SeanceFin;
        """
        
        cursor.execute(query, (classe_id, day_id, annee_scolaire_id))
        rows = cursor.fetchall()
        
        print(f"  Query returned {len(rows) if rows else 0} rows")
        if not rows:
            print(f"  ⚠️  NO SCHEDULE FOUND for classe_id={classe_id}, day_id={day_id}, annee_scolaire_id={annee_scolaire_id}, groupe_id={groupe_id}")
        
        # Formater les résultats
        schedule_rows = []
        for row in rows:
            enseignant_name = ""
            if row.get("enseignant_prenom") and row.get("enseignant_nom"):
                enseignant_name = f"{row['enseignant_prenom']} {row['enseignant_nom']}".strip()
            
            schedule_row = {
                "id": row.get("id"),
                "jour": row.get("jour_label") or requested_day.capitalize(),
                "matiere": row.get("matiere") or "Matière non spécifiée",
                "salle": row.get("salle") or "Salle non spécifiée",
                "enseignant": enseignant_name or "Enseignant non spécifié",
                "heure_debut": row.get("heure_debut") or "Non spécifié",
                "heure_fin": row.get("heure_fin") or "Non spécifié",
                "seance": row.get("seance") or "Séance non spécifiée",
                "remarque": row.get("remarque") or "",
            }
            schedule_rows.append(schedule_row)
        
        return None, schedule_rows

    except Exception as e:
        print(f"ERROR in get_student_schedule_for_day: {str(e)}")
        return {"error": str(e)}, []

    finally:
        cursor.close()
        connection.close()
