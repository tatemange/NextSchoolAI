from huggingface_hub import InferenceClient

key = "VOTRE_TOKEN_HUGGINGFACE_ICI"
client = InferenceClient(api_key=key)

models = [
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "HuggingFaceH4/zephyr-7b-beta"
]

for model in models:
    try:
        res = client.chat_completion(
            model=model,
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=10
        )
        print(f"[{model}] SUCCESS: {res.choices[0].message.content}")
        break # Stop on first success just to know which to pick
    except Exception as e:
        print(f"[{model}] ERROR: {e}")
