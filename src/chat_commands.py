import os
import readline

from rich.console import Console

console = Console()


class ChatCommands:
    def __init__(self, plain: bool = False, show_reasoning: bool = True, debug: bool = False, base_dir: str = None,
                 chat_session=None):
        self.base_dir = base_dir or os.getcwd()
        self.plain = plain
        self.show_reasoning = show_reasoning
        self.debug = debug
        self._chat_session = chat_session

        self.command_history = []
        self.history_index = 0
        self.internal_commands = ['plain', 'reasoning', 'debug', 'clear', 'help']

    def custom_file_reference_completer(self, text: str, state: int, safe: bool = True):
        if not text.startswith('@@'):
            return None

        path = text[2:]

        # Protection against absolute or unsafe paths
        if safe and (path.startswith('/') or '..' in path or path.startswith('~') or '//' in path):
            return None

        dirname = os.path.dirname(path)
        prefix = os.path.basename(path)

        dir_to_list = os.path.join(self.base_dir, dirname)
        dir_to_list = os.path.realpath(dir_to_list)  # resolve symlinks

        # Security: disallow access outside the base directory
        if safe and not dir_to_list.startswith(os.path.realpath(self.base_dir)):
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
                if safe and not os.path.realpath(entry_path).startswith(os.path.realpath(self.base_dir)):
                    continue

                if os.path.isdir(entry_path):
                    full_path += '/'
                matches.append('@@' + full_path)

        matches.sort()
        if state < len(matches):
            return matches[state]
        return None

    def custom_completer(self, text, state):
        if text.startswith('/'):
            options = [cmd for cmd in self.internal_commands if cmd.startswith(text[1:])]
            if state < len(options):
                return '/' + options[state]
        elif text.startswith('@@'):
            return self.custom_file_reference_completer(text, state)
        return None

    def setup_readline(self):
        readline.set_completer(self.custom_completer)
        readline.set_completer_delims(' ')
        readline.parse_and_bind("tab: complete")  # Bind the tab key to the completer
        readline.set_startup_hook(lambda: readline.insert_text(self.command_history[self.history_index]))

    def add_command_to_history(self, command):
        self.command_history.append(command)
        self.history_index = len(self.command_history)

    def clear_history(self):
        self.command_history = []
        self.history_index = 0
        self._chat_session.clear_history()

    def process_command(self, user_input: str):
        if not user_input.startswith('/'):
            return False
        command = user_input[1:].lower()
        if command == "plain":
            self.plain = not self.plain
            console.print(f"Plain mode {'enabled' if self.plain else 'disabled'}", style="bold green")
        elif command == "reasoning":
            self.show_reasoning = not self.show_reasoning
            console.print(f"Reasoning mode {'enabled' if self.show_reasoning else 'disabled'}", style="bold green")
        elif command == "debug":
            self.debug = not self.debug
            console.print(f"Debug mode {'enabled' if self.debug else 'disabled'}", style="bold green")
        elif command == "clear":
            self.clear_history()
            console.print("Chat history cleared.", style="bold green")
        elif command in ["help", "?", "h"]:
            console.print("Available commands:", style="bold green")
            console.print("/plain - Toggle plain mode on/off")
            console.print("/reasoning - Toggle reasoning mode on/off")
            console.print("/debug - Toggle debug mode on/off")
            console.print("/clear - Clear chat history")
            console.print("/help - Show this help message")
        else:
            console.print(f"Unknown command: {user_input}", style="bold red")

        return True
