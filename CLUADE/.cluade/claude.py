import argparse
import json
import os
import time
from openai import OpenAI, APIStatusError, APIConnectionError

def load_config():
    config_paths = ["setting.local.json", "../setting.local.json", "../../setting.local.json"]
    for path in config_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    return None

def main():
    parser = argparse.ArgumentParser(description="Run OpenRouter models via Claude wrapper.")
    parser.add_argument("--model", required=True, help="The model identifier to use.")
    args = parser.parse_args()

    config = load_config()
    
    if not config or "env" not in config:
        api_key = os.getenv("ANTHROPIC_AUTH_TOKEN")
    else:
        api_key = config["env"].get("ANTHROPIC_AUTH_TOKEN")

    if not api_key:
        print("Error: No API token found in setting.local.json or environment variables.")
        return

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=10.0  # Prevents hanging on bad connections
    )

    primary_model = args.model
    fallbacks = [
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemini-2.5-flash:free",
        "mistralai/mistral-7b-instruct:free"
    ]
    
    models_to_try = [primary_model] + [m for m in fallbacks if m != primary_model]

    user_prompt = input("Type your prompt here: ")
    print()

    for model in models_to_try:
        try:
            print(f"Trying model: {model}...")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": user_prompt}],
                extra_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Interview Practice App"
                }
            )
            print("\n--- Response ---")
            print(response.choices[0].message.content)
            return
            
        except (APIStatusError, APIConnectionError) as e:
            print(f"  -> Connection/API failure with this model.")
            if model == models_to_try[-1]:
                print(f"\nAll fallback models failed. Final Error: {e}")
            else:
                print("  -> Attempting next available fallback model...\n")
                time.sleep(1)
                
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return

if __name__ == "__main__":
    main()