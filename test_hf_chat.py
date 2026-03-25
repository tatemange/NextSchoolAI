import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
key = os.getenv("HUGGINGFACE_API_KEY")

if not key:
    print("Erreur : HUGGINGFACE_API_KEY non trouvée dans le fichier .env")
    exit(1)

model = "meta-llama/Llama-3.1-8B-Instruct"
client = InferenceClient(api_key=key)

print(f"Testing Chat Completions via InferenceClient pour {model}...")

try:
    messages = [{"role": "user", "content": "Dis bonjour et donne un exemple de code python court de base."}]
    res = client.chat_completion(
        model=model,
        messages=messages,
        max_tokens=60
    )
    print("\n[RÉPONSE DU MODÈLE]")
    print(res.choices[0].message.content)
except Exception as e:
    print(f"Erreur lors du test de chat: {e}")
