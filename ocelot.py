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
from src.chat_session import ChatSession  # New import

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

def interactive_chat(args):
    model_name = args.model_name
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

    chat_session = ChatSession(backend)

    console.print("Interactive chat started. Type 'exit' to quit.", style="bold green")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        chat_session.add_user(user_input)
        response = chat_session.ask(user_input, stream=False)

        console.print(f"Assistant: {response}", style="bright_blue")

    return 0

def main():
    parser = argparse.ArgumentParser(description="Run a prompt on an LLM model.")
    subparsers = parser.add_subparsers(dest='command', help='Subcommands')

    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate text from a prompt')
    generate_parser.add_argument("model_name",
                                 help="Name of the model to use. Format: [backend/]model_name. Supported backends: ollama, openrouter")
    generate_parser.add_argument("prompt", help="The text prompt to send to the model.")
    generate_parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    generate_parser.add_argument("--no-show-reasoning", action="store_true", help="Hide reasoning process.")

    # Interactive chat command
    chat_parser = subparsers.add_parser('chat', help='Interactive chat with the model')
    chat_parser.add_argument("model_name",
                             help="Name of the model to use. Format: [backend/]model_name. Supported backends: ollama, openrouter")
    chat_parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    chat_parser.add_argument("--no-show-reasoning", action="store_true", help="Hide reasoning process.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'generate':
        return run_command(args)
    elif args.command == 'chat':
        return interactive_chat(args)

if __name__ == "__main__":
    sys.exit(main())
