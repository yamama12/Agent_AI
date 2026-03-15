import os
import mysql.connector

#--------------------------------------------------------------------
# Extraction des données pour la génération des documents : 
#--------------------------------------------------------------------
def get_eleve_data(matricule: str):
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
                            TRIM(p.NomFr) AS NomFr,
                            TRIM(p.PrenomFr) AS PrenomFr,
                            TRIM(p.AdresseFr) AS AdresseFr,
                            TRIM(p.Tel1) AS Tel1,
                            e.DateNaissance,
                            TRIM(l.LIBELLELOCALITEFR) AS LieuNaissance,
                            TRIM(c.NOMCLASSEFR) AS Classe,
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
            "DateNaissance": row["DateNaissance"],
            "LieuNaissance": row["LieuNaissance"],
            "Classe": row["Classe"],
            "AdresseFr": row["AdresseFr"],
            "Nationalite": row["Nationalite"],
            "Tel1": row["Tel1"],
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
                        TRIM(p.AdresseFr) AS AdresseFr,
                        TRIM(p.Tel1) AS Tel1,
                        e.DateNaissance,
                        TRIM(l.LIBELLELOCALITEFR) AS LieuNaissance,
                        TRIM(c.NOMCLASSEFR) AS Classe,
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
            "DateNaissance": row["DateNaissance"],
            "LieuNaissance": row["LieuNaissance"],
            "Classe": row["Classe"],
            "AdresseFr": row["AdresseFr"],
            "Nationalite": row["Nationalite"],
            "Tel1": row["Tel1"],
            "AnneeScolaire": row["AnneeScolaire"],
            "DateInscription": row["DateInscription"],
            "StatutInscription": row["statut_inscription"],
            "AnneeActuelle": row["AnneeActuelle"],
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