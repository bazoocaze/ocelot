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
from src.chat_session import ChatSession


def output_tokens(tokens, show_reasoning: bool, debug: bool = False, plain: bool = False):
    output = ModelOutput(show_reasoning=show_reasoning)
    if debug:
        for token in tokens:
            output.add_token(token)
            print(f"[{token}]", end="", flush=True)
        print("\n--- CONTENT ---")
        print(output.content())
        print("---")
    if plain:
        for token in tokens:
            output.add_token(token)
            print(f"{token}", end="", flush=True)
    else:
        with Live(Markdown(output.content()), console=console, refresh_per_second=10) as live:
            for token in tokens:
                output.add_token(token)
                live.update(Markdown(output.content(), style="bright_blue"))


def command_generate(config, args):
    provider_factory = ProviderFactory(config)
    provider_name, model_name = provider_factory.parse_model_name(args.model_name)
    backend = provider_factory.resolve_backend(provider_name, model_name, debug=args.debug,
                                               show_reasoning=not args.no_show_reasoning)
    tokens = backend.generate(args.prompt, stream=True)
    output_tokens(tokens, show_reasoning=not args.no_show_reasoning, debug=args.debug, plain=args.plain)
    return 0


def command_chat(config, args):
    show_reasoning = not args.no_show_reasoning

    provider_factory = ProviderFactory(config)
    provider_name, model_name = provider_factory.parse_model_name(args.model_name)
    backend = provider_factory.resolve_backend(provider_name, model_name, debug=args.debug,
                                               show_reasoning=show_reasoning)
    chat_session = ChatSession(backend)

    console.print("Interactive chat started. Type 'exit' to quit.", style="bold green")

    command_history = []
    history_index = 0
    readline.set_startup_hook(lambda: readline.insert_text(command_history[history_index]))  # Initialize readline

    initial_prompt = args.initial_prompt

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
            output_tokens(response, show_reasoning, debug=args.debug, plain=args.plain)
    except (EOFError, KeyboardInterrupt):
        console.print("")

    return 0


def command_list_models(config, args):
    provider_factory = ProviderFactory(config)
    providers = provider_factory.all_providers() if args.provider_name == "all" else [args.provider_name]

    models = []
    for provider in providers:
        backend = provider_factory.resolve_backend(provider_name=provider, debug=args.debug)
        models.extend([f"{provider}/{model}" for model in backend.list_models()])

    if args.plain:
        for model in models:
            print(model)
    else:
        console.print("Available models:", style="bold green")
        for model in models:
            console.print(f"- {model}")
    return 0


def parse_args(input_args):
    parser = argparse.ArgumentParser(description="Jaguatirica Command Line Interface for LLM Models.")
    subparsers = parser.add_subparsers(dest='command', help='Subcommands')

    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate text from a prompt',
                                            description="Generate text from a prompt using the specified model.")
    generate_parser.add_argument("-m", "--model_name", required=True,
                                 help="Name of the model to use. Format: [provider/]model_name.")
    generate_parser.add_argument("--no-show-reasoning", action="store_true", help="Hide reasoning process.")
    generate_parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")
    generate_parser.add_argument("--plain", action="store_true", help="Show output without formatting.")
    generate_parser.add_argument("prompt", help="The text prompt to send to the model.")

    # Interactive chat command
    chat_parser = subparsers.add_parser('chat', help='Interactive chat with the model',
                                        description="Start an interactive chat session with the specified model.")
    chat_parser.add_argument("-m", "--model_name", required=True,
                             help="Name of the model to use. Format: [provider/]model_name.")
    chat_parser.add_argument("--no-show-reasoning", action="store_true", help="Hide reasoning process.")
    chat_parser.add_argument("--initial-prompt", type=str, help="Initial prompt to send to the model.")
    chat_parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")
    chat_parser.add_argument("--plain", action="store_true", help="Show output without formatting.")

    # List models command
    list_models_parser = subparsers.add_parser('list-models', help='List available models',
                                               description="List all available models from the specified provider(s).")
    list_models_parser.add_argument("-p", "--provider_name", default='all',
                                    help="Name of the provider to use. Supported providers: all, ollama, openrouter, others(via config).")
    list_models_parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")
    list_models_parser.add_argument("--plain", action="store_true", help="Show output without formatting.")

    args = parser.parse_args(input_args)

    if not args.command:
        parser.print_help()

    return args


def run_application(config_loader: ConfigLoader, input_args):
    args = parse_args(input_args)
    debug = "-d" in input_args or "--debug" in input_args

    config = config_loader.load_config()

    try:
        if args.command == "generate":
            return command_generate(config, args)
        elif args.command == "chat":
            return command_chat(config, args)
        elif args.command == "list-models":
            return command_list_models(config, args)
        else:
            console.print("Invalid or missing command.", style="bold red")
            return 1
    except KeyboardInterrupt:
        console.print("Keyboard interrupt detected. Exiting...", style="bold red")
        return 1
    except Exception as e:
        console.print(f"ERROR: {e}", style="bold red")
        if debug:
            print_exc()

    return 1


def main():
    config_loader = ConfigLoader()
    exit_code = run_application(config_loader, sys.argv[1:] if len(sys.argv) > 1 else [])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
