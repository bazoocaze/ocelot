from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from src.model_output import ModelOutput

console = Console()

class TokenOutput:
    def __init__(self, show_reasoning: bool, debug: bool = False, plain: bool = False):
        self.show_reasoning = show_reasoning
        self.debug = debug
        self.plain = plain
        self.output = ModelOutput(show_reasoning=show_reasoning)

    def _debug_output(self, tokens):
        for token in tokens:
            self.output.add_token(token)
            print(f"[{token}]", end="", flush=True)
        print("\n--- CONTENT ---")
        print(self.output.content())
        print("---")

    def _plain_output(self, tokens):
        for token in tokens:
            self.output.add_token(token)
            print(f"{token}", end="", flush=True)

    def _rich_output(self, tokens):
        with Live(Markdown(self.output.content()), console=console, refresh_per_second=10,
                   vertical_overflow="visible") as live:
            for token in tokens:
                self.output.add_token(token)
                live.update(Markdown(self.output.content(), style="bright_blue"))

    def output_tokens(self, tokens):
        if self.debug:
            self._debug_output(tokens)
        elif self.plain:
            self._plain_output(tokens)
        else:
            self._rich_output(tokens)
