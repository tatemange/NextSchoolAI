import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
key = os.getenv("HUGGINGFACE_API_KEY")

if not key:
    print("Erreur : HUGGINGFACE_API_KEY non trouvée dans le fichier .env")
    exit(1)

models_to_test = [
    "meta-llama/Llama-3.1-8B-Instruct",
    "deepseek-ai/DeepSeek-R1",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "HuggingFaceH4/zephyr-7b-beta"
]

client = InferenceClient(api_key=key)

for model in models_to_test:
    try:
        messages = [{"role": "user", "content": "Dis bonjour courtement."}]
        res = client.chat_completion(
            model=model,
            messages=messages,
            max_tokens=20
        )
        print(f"[{model}] -> SUCCÈS")
    except Exception as e:
        print(f"[{model}] -> ERREUR: {e}")
