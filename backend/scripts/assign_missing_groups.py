#!/usr/bin/env python3
"""
Script utilitaire pour assigner les groupes manquants à tous les élèves.
Cela évite le problème "Aucun cours n'est programmé" dû à un groupe non assigné.
"""

import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

def assign_missing_groups():
    """
    Assigne un groupe à chaque élève qui n'en a pas.
    Pour chaque classe, on assigne le premier groupe disponible avec des cours.
    """
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306)),
            charset="utf8mb4",
        )
        cursor = conn.cursor(dictionary=True)
        
        print("ASSIGNATION DES GROUPES MANQUANTS")
        print("=" * 80)
        
        # Find students without groups
        query_students_no_group = """
        SELECT DISTINCT
            i.id as inscription_id,
            i.Classe,
            c.NOMCLASSEFR as classe_name,
            p.NomFr,
            p.PrenomFr
        FROM inscriptioneleve i
        INNER JOIN classe c ON i.Classe = c.id
        INNER JOIN eleve e ON i.Eleve = e.id
        INNER JOIN personne p ON e.IdPersonne = p.id
        WHERE (i.groupe IS NULL OR i.groupe = '')
        AND i.Annuler = 0
        ORDER BY i.Classe
        """
        
        cursor.execute(query_students_no_group)
        students = cursor.fetchall()
        
        print(f"Élèves sans groupe: {len(students)}")
        
        if not students:
            print("✓ Tous les élèves ont un groupe assigné")
            return
        
        # Group by class
        by_class = {}
        for student in students:
            classe_id = student['Classe']
            if classe_id not in by_class:
                by_class[classe_id] = {
                    'name': student['classe_name'],
                    'students': []
                }
            by_class[classe_id]['students'].append(student)
        
        # Assign groups
        total_updated = 0
        
        for classe_id, data in by_class.items():
            print(f"\nClasse: {data['name']} (ID: {classe_id})")
            
            # Find available groups for this class
            query_groups = """
            SELECT DISTINCT e.Groupe
            FROM emploidutemps e
            WHERE e.Classe = %s
            AND e.Groupe IS NOT NULL
            AND e.Groupe != ''
            ORDER BY e.Groupe
            """
            
            cursor.execute(query_groups, (classe_id,))
            groups = cursor.fetchall()
            
            if not groups:
                print(f"  ✗ Aucun groupe trouvé pour cette classe")
                continue
            
            group_to_assign = groups[0]['Groupe']
            print(f"  Groupe à assigner: '{group_to_assign}'")
            print(f"  Nombre d'élèves: {len(data['students'])}")
            
            # Assign the group to all students in this class
            for student in data['students']:
                update_query = """
                UPDATE inscriptioneleve
                SET groupe = %s
                WHERE id = %s
                """
                
                cursor.execute(update_query, (group_to_assign, student['inscription_id']))
                total_updated += cursor.rowcount
                print(f"    ✓ {student['PrenomFr']} {student['NomFr']}")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"✓ Total: {total_updated} élève(s) mis à jour")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    assign_missing_groups()
