import os
from dotenv import load_dotenv
from google import genai

# Charger la clé depuis .env
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Récupérer la liste des modèles
models = client.models.list()

print("=== Liste des modèles accessibles avec votre clé ===")
for model in models:
    # Chaque modèle a maintenant 'name' et 'display_name'
    print(f"Nom interne: {model.name} | Nom affiché: {model.display_name}")
