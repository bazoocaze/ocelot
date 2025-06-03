import sys
import requests

def run_prompt_on_ollama(model_name, prompt):
    api_url = f"https://api.ollama.com/v1/models/{model_name}/generate"
    payload = {
        "prompt": prompt,
    }
    response = requests.post(api_url, json=payload)
    if response.status_code == 200:
        result = response.json()
        print("Result from Ollama API:")
        print(result)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 main.py <model name> <text prompt>")
        sys.exit(1)
    
    model_name = sys.argv[1]
    prompt = sys.argv[2]
    run_prompt_on_ollama(model_name, prompt)

if __name__ == "__main__":
    main()
