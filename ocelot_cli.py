import argparse
import os
import readline
import sys
from traceback import print_exc

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from src.config import ConfigLoader
from src.prompt_preprocessor import PromptPreprocessor
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
        with Live(Markdown(output.content()), console=console, refresh_per_second=10,
                  vertical_overflow="visible") as live:
            for token in tokens:
                output.add_token(token)
                live.update(Markdown(output.content(), style="bright_blue"))


def command_generate(config, args):
    provider_factory = ProviderFactory(config)
    provider_name, model_name = provider_factory.parse_model_name(args.model_name)
    backend = provider_factory.resolve_backend(provider_name, model_name, debug=args.debug,
                                               show_reasoning=not args.no_show_reasoning)

    # If prompt is not provided, read from standard input
    if not args.prompt:
        args.prompt = sys.stdin.read().strip()

    # Pre-process the prompt
    preprocessor = PromptPreprocessor()
    processed_prompt = preprocessor.process_prompt(args.prompt)

    tokens = backend.generate(processed_prompt, stream=True)
    output_tokens(tokens, show_reasoning=not args.no_show_reasoning, debug=args.debug, plain=args.plain)
    return 0


def custom_file_reference_completer(text: str, state: int, safe: bool = True):
    if not text.startswith('@@'):
        return None

    path = text[2:]

    # Protection against absolute or unsafe paths
    if safe and (path.startswith('/') or '..' in path or path.startswith('~') or '//' in path):
        return None

    dirname = os.path.dirname(path)
    prefix = os.path.basename(path)

    base_dir = os.getcwd()
    dir_to_list = os.path.join(base_dir, dirname)
    dir_to_list = os.path.realpath(dir_to_list)  # resolve symlinks

    # Security: disallow access outside the base directory
    if safe and not dir_to_list.startswith(os.path.realpath(base_dir)):
        return None

    if not os.path.isdir(dir_to_list):
        return None

    try:
        entries = os.listdir(dir_to_list)
    except Exception:
        return None

    matches = []
    for entry in entries:
        if entry.startswith(prefix):
            full_path = os.path.join(dirname, entry) if dirname else entry
            entry_path = os.path.join(dir_to_list, entry)

            # Prevent matches that escape the base directory
            if safe and not os.path.realpath(entry_path).startswith(os.path.realpath(base_dir)):
                continue

            if os.path.isdir(entry_path):
                full_path += '/'
            matches.append('@@' + full_path)

    matches.sort()
    if state < len(matches):
        return matches[state]
    return None


def command_chat(config, args):
    show_reasoning = not args.no_show_reasoning
    debug = args.debug

    provider_factory = ProviderFactory(config)
    provider_name, model_name = provider_factory.parse_model_name(args.model_name)
    backend = provider_factory.resolve_backend(provider_name, model_name, debug=debug,
                                               show_reasoning=show_reasoning)
    chat_session = ChatSession(backend)

    console.print("Interactive chat started. Type 'exit' to exit or '/help' for available commands.",
                  style="bold green")

    command_history = []
    history_index = 0
    readline.set_startup_hook(lambda: readline.insert_text(command_history[history_index]))  # Initialize readline

    # Define internal commands for autocomplete
    internal_commands = ['plain', 'reasoning', 'debug', 'clear', 'help']

    # Create a custom completer function
    def custom_completer(text, state):
        if text.startswith('/'):
            options = [cmd for cmd in internal_commands if cmd.startswith(text[1:])]
            if state < len(options):
                return '/' + options[state]
        elif text.startswith('@@'):
            return custom_file_reference_completer(text, state)
        return None

    # Set the custom completer for readline
    readline.set_completer(custom_completer)
    readline.set_completer_delims(' ')
    readline.parse_and_bind("tab: complete")  # Bind the tab key to the completer

    initial_prompt = args.initial_prompt

    # Initialize the prompt preprocessor
    preprocessor = PromptPreprocessor()

    # Initialize plain flag
    plain = args.plain

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

            if not user_input:
                continue

            # Check for commands
            if user_input.startswith('/'):
                command = user_input[1:].lower()
                if command == "plain":
                    plain = not plain
                    console.print(f"Plain mode {'enabled' if plain else 'disabled'}", style="bold green")
                elif command == "reasoning":
                    show_reasoning = not show_reasoning
                    console.print(f"Reasoning mode {'enabled' if show_reasoning else 'disabled'}", style="bold green")
                elif command == "debug":
                    debug = not debug
                    console.print(f"Debug mode {'enabled' if debug else 'disabled'}", style="bold green")
                elif command == "clear":
                    chat_session.clear_history()
                    console.print("Chat history cleared.", style="bold green")
                elif command == "help":
                    console.print("Available commands:", style="bold green")
                    console.print("/plain - Toggle plain mode on/off")
                    console.print("/reasoning - Toggle reasoning mode on/off")
                    console.print("/debug - Toggle debug mode on/off")
                    console.print("/clear - Clear chat history")
                    console.print("/help - Show this help message")
                else:
                    console.print(f"Unknown command: {user_input}", style="bold red")
                continue

            # Add the current input to the history
            command_history.append(user_input)
            history_index = len(command_history)

            # Pre-process the user input
            processed_input = preprocessor.process_prompt(user_input)

            try:
                response = chat_session.ask(processed_input, stream=True)

                console.print(f"Assistant: ", style="bright_blue", end="")
                output_tokens(response, show_reasoning, debug=debug, plain=plain)
            except KeyboardInterrupt:
                console.print("\nKeyboard interrupt detected", style="bold red")

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
    generate_parser.add_argument("prompt", nargs='?',
                                 help="The text prompt to send to the model. If not provided, read from standard input.")

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
