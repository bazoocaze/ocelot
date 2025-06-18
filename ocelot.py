import argparse
import json
import sys
from os import environ
from traceback import print_exc
from typing import List, Dict, Optional, Union, Generator

import requests
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

console = Console()
from src.model_output import ModelOutput  # Updated import path
from src.base_llm_backend import BaseLLMBackend  # Updated import path
from src.openrouter_backend import OpenRouterBackend  # Updated import path
from src.ollama_backend import OllamaBackend  # Updated import path

class ChatSession:
    def __init__(self, backend: BaseLLMBackend, system_prompt: Optional[str] = None):
        self.backend = backend
        self.messages: List[Dict[str, str]] = []
        if system_prompt:
            self.add_system(system_prompt)

    def add_system(self, content: str):
        self.messages.append({"role": "system", "content": content})

    def add_user(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def ask(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        self.add_user(prompt)
        response = self.backend.chat(self.messages, stream=stream)
        if not stream:
            self.add_assistant(response)
            return response

        def streaming_response():
            full = ""
            for token in response:
                yield token
                full += token
            self.add_assistant(full)

        return streaming_response()

def generate_on_backend(ollama, prompt, show_reasoning, debug=False):
    output = ModelOutput(show_reasoning=show_reasoning)
    if debug:
        for token in ollama.generate(prompt, stream=True):
            output.add_token(token)
            print(f"[{token}]", end="", flush=True)
        print("\n--- CONTENT ---")
        print(output.content())
        print("---")
    else:
        with Live(Markdown(output.content()), console=console, refresh_per_second=10) as live:
            for token in ollama.generate(prompt, stream=True):
                output.add_token(token)
                live.update(Markdown(output.content(), style="bright_blue"))
    return 0

def run_command(args):
    model_name = args.model_name
    prompt = args.prompt
    debug = args.debug
    show_reasoning = not args.no_show_reasoning

    if model_name.startswith("openrouter/"):
        model_name = model_name[len("openrouter/"):]
        openrouter_api_key = environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            console.print("ERROR: OPENROUTER_API_KEY environment variable is not set", style="bold red")
            return 1
        backend = OpenRouterBackend(openrouter_api_key, model=model_name, debug=debug, show_reasoning=show_reasoning)
    else:
        # Default to Ollama backend
        if model_name.startswith("ollama/"):
            model_name = model_name[len("ollama/"):]
        backend = OllamaBackend(model_name, debug=debug)

    try:
        return generate_on_backend(backend, prompt, show_reasoning, debug=debug)
    except KeyboardInterrupt:
        console.print("Keyboard interrupt detected. Exiting...", style="bold red")
        return 1
    except Exception as e:
        console.print(f"ERROR: {e}", style="bold red")
        if debug:
            print_exc()
        return 1

def main():
    parser = argparse.ArgumentParser(description="Run a prompt on an LLM model.")
    subparsers = parser.add_subparsers(dest='command', help='Subcommands')

    # Run command
    run_parser = subparsers.add_parser('run', help='Run a prompt')
    run_parser.add_argument("model_name",
                            help="Name of the model to use. Format: [backend/]model_name. Supported backends: ollama, openrouter")
    run_parser.add_argument("prompt", help="The text prompt to send to the model.")
    run_parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    run_parser.add_argument("--no-show-reasoning", action="store_true", help="Hide reasoning process.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'run':
        return run_command(args)

if __name__ == "__main__":
    sys.exit(main())
