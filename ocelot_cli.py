import argparse
import readline
import sys
from traceback import print_exc

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from src.config import ConfigLoader
from src.provider_factory import ProviderFactory

console = Console()
from src.model_output import ModelOutput
from src.base_llm_backend import BaseLLMBackend
from src.chat_session import ChatSession

def output_tokens(tokens, show_reasoning: bool, debug: bool = False, plain_output: bool = False):
    output = ModelOutput(show_reasoning=show_reasoning)
    if debug or plain_output:
        for token in tokens:
            output.add_token(token)
            print(f"[{token}]", end="", flush=True)
        print("\n--- CONTENT ---")
        print(output.content())
        print("---")
    else:
        with Live(Markdown(output.content()), console=console, refresh_per_second=10) as live:
            for token in tokens:
                output.add_token(token)
                live.update(Markdown(output.content(), style="bright_blue"))

def generate_on_backend(backend: BaseLLMBackend, prompt: str, show_reasoning: bool, debug: bool = False, plain_output: bool = False) -> int:
    tokens = backend.generate(prompt, stream=True)
    output_tokens(tokens, show_reasoning, debug=debug, plain_output=plain_output)
    return 0

def run_generate(config, args):
    provider_factory = ProviderFactory(config)
    provider_name, model_name = provider_factory.resolve_provider_for_model_name(args.model_name)
    prompt = args.prompt
    debug = args.debug
    show_reasoning = not args.no_show_reasoning
    plain_output = args.plain_output

    try:
        backend = provider_factory.resolve_backend(provider_name, model_name, debug=debug,
                                                   show_reasoning=show_reasoning)
        return generate_on_backend(backend, prompt, show_reasoning, debug=debug, plain_output=plain_output)
    except KeyboardInterrupt:
        console.print("Keyboard interrupt detected. Exiting...", style="bold red")
        return 1
    except Exception as e:
        console.print(f"ERROR: {e}", style="bold red")
        if debug:
            print_exc()
        return 1

def interactive_chat(config, args):
    provider_factory = ProviderFactory(config)
    provider_name, model_name = provider_factory.resolve_provider_for_model_name(args.model_name)
    debug = args.debug
    show_reasoning = not args.no_show_reasoning
    plain_output = args.plain_output
    initial_prompt = args.initial_prompt

    try:
        backend = provider_factory.resolve_backend(provider_name, model_name, debug=debug,
                                                   show_reasoning=show_reasoning)
    except ValueError as e:
        console.print(str(e), style="bold red")
        return 1

    chat_session = ChatSession(backend)

    console.print("Interactive chat started. Type 'exit' to quit.", style="bold green")

    command_history = []
    history_index = 0
    readline.set_startup_hook(lambda: readline.insert_text(command_history[history_index]))  # Initialize readline

    try:
        while True:
            if initial_prompt:
                console.print(f"You: {initial_prompt}\n", end="")
                user_input = initial_prompt
                readline.add_history(initial_prompt)
                initial_prompt = None
            else:
                user_input = input("You: ")
                if user_input.lower() == "exit":
                    break

            # Add the current input to the history
            command_history.append(user_input)
            history_index = len(command_history)

            response = chat_session.ask(user_input, stream=True)

            console.print(f"Assistant: ", style="bright_blue", end="")
            output_tokens(response, show_reasoning, debug=debug, plain_output=plain_output)

    except EOFError:
        console.print("")
        pass
    except KeyboardInterrupt | EOFError:
        console.print("\nKeyboard interrupt detected. Exiting...", style="bold red")
        return 1
    except Exception as e:
        console.print(f"ERROR: {e}", style="bold red")
        if debug:
            print_exc()
        return 1

    return 0

def list_models(config, args):
    provider_factory = ProviderFactory(config)
    provider_name = args.provider_name or 'all'
    debug = args.debug
    plain = args.plain

    try:
        models = []
        providers = provider_factory.all_providers() if provider_name == 'all' else [provider_name]
        for provider in providers:
            backend = provider_factory.resolve_backend(provider_name=provider, debug=debug)
            provider_models = backend.list_models()
            models.extend([f"{provider}/{model}" for model in provider_models])

        if plain:
            for model in models:
                print(model)
        else:
            console.print("Available models:", style="bold green")
            for model in models:
                console.print(f"- {model}")
    except Exception as e:
        console.print(f"ERROR: {e}", style="bold red")
        if debug:
            print_exc()
        return 1

    return 0

def parse_args(input_args):
    parser = argparse.ArgumentParser(description="Run a prompt on an LLM model.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    parser.add_argument("--plain-output", action="store_true", help="Show output without formatting, similar to debug mode.")
    subparsers = parser.add_subparsers(dest='command', help='Subcommands')
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate text from a prompt')
    generate_parser.add_argument("-m", "--model_name",
                                 required=True,
                                 help="Name of the model to use. Format: [backend/]model_name.")
    generate_parser.add_argument("prompt", help="The text prompt to send to the model.")
    generate_parser.add_argument("--no-show-reasoning", action="store_true", help="Hide reasoning process.")
    # Interactive chat command
    chat_parser = subparsers.add_parser('chat', help='Interactive chat with the model')
    chat_parser.add_argument("-m", "--model_name",
                             required=True,
                             help="Name of the model to use. Format: [backend/]model_name. Supported backends: ollama, openrouter.")
    chat_parser.add_argument("--no-show-reasoning", action="store_true", help="Hide reasoning process.")
    chat_parser.add_argument("--initial-prompt", type=str, help="Initial prompt to send to the model.")
    # List models command
    list_models_parser = subparsers.add_parser('list-models', help='List available models')
    list_models_parser.add_argument("-p", "--provider_name",
                                    default='all',
                                    help="Name of the backend to use. Supported backends: ollama, openrouter, all, others(config).")
    list_models_parser.add_argument("--plain", action="store_true",
                                    help="List models in plain text without formatting.")
    args = parser.parse_args(input_args)

    if not args.command:
        parser.print_help()

    return args

def run_app(config_loader: ConfigLoader, input_args):
    args = parse_args(input_args)

    if not args.command:
        return 1

    config = config_loader.load_config()

    if args.command == 'generate':
        return run_generate(config, args)
    elif args.command == 'chat':
        return interactive_chat(config, args)
    elif args.command == 'list-models':
        return list_models(config, args)

    console.print("Invalid command.", style="bold red")

    return 1

def main():
    config_loader = ConfigLoader()
    return run_app(config_loader, sys.argv[1:] if len(sys.argv) > 1 else None)

if __name__ == "__main__":
    sys.exit(main())
