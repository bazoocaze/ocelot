import argparse
import json
import re
import sys

import requests
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

console = Console()


def run_prompt_on_ollama(model_name, prompt, debug=False, hide_think=False):
    api_url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": True  # Enable streaming support
    }
    response = requests.post(api_url, json=payload, stream=True)
    if response.status_code != 200:
        console.print(f"Error: {response.status_code}", style="red")
        if debug:
            console.print(f"DEBUG: Response body:", style="red")
            console.print(f"DEBUG: {response.text}", style="red")
        return 1

    if debug:
        console.print(f"DEBUG: Stream started", style="red")
    output_text = ""
    with Live(Markdown(output_text), console=console, refresh_per_second=10) as live:
        for line in response.iter_lines(decode_unicode=True):
            if line:
                if debug:
                    console.print(f"DEBUG: {line}", style="red")
                result = json.loads(line)  # Assuming the response is a valid Python dictionary
                output_text += result["response"]
                if hide_think:
                    to_output = re.sub('<' + 'think' + '>.*</' + 'think' + r'>\s+', '', output_text, flags=re.DOTALL)
                else:
                    to_output = re.sub(r"<think>", "\\<think\\>", output_text)
                    to_output = re.sub(r"</think>", "\\</think\\>", to_output)
                live.update(Markdown(to_output, style="bright_blue"))

    return 0


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

    return run_prompt_on_ollama(model_name, prompt, debug, hide_think)


if __name__ == "__main__":
    sys.exit(main())
