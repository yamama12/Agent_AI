import os
from dotenv import load_dotenv
try:
    from mistralai import Mistral
except ImportError:
    from mistralai.client import Mistral

# Charger la clé depuis .env
load_dotenv()
client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

# Récupérer la liste des modèles
models = client.models.list()

print("=== Liste des modèles accessibles avec votre clé ===")
for model in getattr(models, "data", models):
    model_id = getattr(model, "id", None) or getattr(model, "name", "inconnu")
    created = getattr(model, "created", None)
    if created is not None:
        print(f"Nom interne: {model_id} | created: {created}")
    else:
        print(f"Nom interne: {model_id}")
