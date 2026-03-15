import os
import mysql.connector
from services.rag_service import phonetic_code

connection = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=int(os.getenv("DB_PORT", 3306)),
)

cursor = connection.cursor(dictionary=True)

cursor.execute("SELECT id, PrenomFr, NomFr FROM personne")

rows = cursor.fetchall()

for row in rows:
    prenom_ph = phonetic_code(row["PrenomFr"])
    nom_ph = phonetic_code(row["NomFr"])

    cursor.execute(
        """
        UPDATE personne 
        SET prenom_phonetic=%s, nom_phonetic=%s 
        WHERE id=%s
        """,
        (prenom_ph, nom_ph, row["id"]),
    )

connection.commit()

cursor.close()
connection.close()

print("Phonetic columns updated successfully.")