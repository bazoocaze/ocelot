import sys
import argparse
import requests
import re
from rich.console import Console
from rich.markdown import Markdown

console = Console()

def run_prompt_on_ollama(model_name, prompt, debug=False, hide_think=False):
    api_url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False  # Disable streaming support
    }
    response = requests.post(api_url, json=payload)
    if response.status_code == 200:
        if debug:
            console.print(f"DEBUG: {response.text}", style="red")
        result = response.json()
        if hide_think:
            # Remove think...eol tags from the response
            # Use re.DOTALL to match across newlines
            processed_response = re.sub('<' + 'think' + '>.*</' + 'think' + r'>\s+', '', result["response"], flags=re.DOTALL)
            console.print(Markdown(processed_response), style="green")
        else:
            console.print(Markdown(result["response"]), style="green")
    else:
        console.print(f"Error: {response.status_code}", style="red")
        if debug:
            console.print(f"DEBUG: Response body:", style="red")
            console.print(f"DEBUG: {response.text}", style="red")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Run a prompt on an Ollama model.")
    parser.add_argument("model_name", help="Name of the Ollama model to use.")
    parser.add_argument("prompt", help="The text prompt to send to the model.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (for future use).")
    parser.add_argument("--hide-think", action="store_true", help="Hide thinking process (for future use).")

    args = parser.parse_args()

    model_name = args.model_name
    prompt = args.prompt
    debug = args.debug
    hide_think = args.hide_think

    run_prompt_on_ollama(model_name, prompt, debug, hide_think)

if __name__ == "__main__":
    main()
