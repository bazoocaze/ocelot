import sys
import argparse
import requests

def run_prompt_on_ollama(model_name, prompt, debug=False):
    api_url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
    }
    response = requests.post(api_url, json=payload)
    if response.status_code == 200:
        print(response.text)
        result = response.json()
        print("Result from Ollama API:")
        print(result)
    else:
        print(f"Error: {response.status_code}")
        if debug:
            print("Response body:")
            print(response.text)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Run a prompt on an Ollama model.")
    parser.add_argument("model_name", help="Name of the Ollama model to use.")
    parser.add_argument("prompt", help="The text prompt to send to the model.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (for future use).")

    args = parser.parse_args()

    model_name = args.model_name
    prompt = args.prompt
    debug = args.debug

    run_prompt_on_ollama(model_name, prompt, debug)

if __name__ == "__main__":
    main()
