import json

from rich.console import Console

from src.openai_compatible_backend import OpenAiCompatibleApiBackend

console = Console()


class OpenRouterResponse:
    def __init__(self, line, debug=False):
        self.valid = True
        self.done = False
        self.content = ""
        self.reasoning = ""
        self.line = line.decode('utf-8')
        self._debug = debug
        self._process_line(self.line)

    def _process_line(self, line):
        if not line.startswith('data: '):
            self.valid = False
            return
        if line == 'data: [DONE]':
            self.done = True
            return
        try:
            data = json.loads(line[6:])  # Skip 'data: ' prefix
            self.content = data["choices"][0]["delta"].get("content", "")
            self.reasoning = data["choices"][0]["delta"].get("reasoning", "")
        except json.JSONDecodeError:
            if self._debug:
                console.print(f"DEBUG: Failed to parse line: {line}", style="bold red")

    @property
    def is_done(self):
        return self.done

    @property
    def is_valid(self) -> bool:
        return self.valid

    @property
    def is_reasoning(self) -> bool:
        return bool(self.reasoning)

    @property
    def is_content(self) -> bool:
        return bool(self.content)


class OpenRouterBackend(OpenAiCompatibleApiBackend):
    def __init__(self, api_key: str, model_name: str, debug: bool = False, show_reasoning: bool = True,
                 base_url: str = "https://openrouter.ai/api/v1", **kwargs):
        extra_headers = {
            # "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/bazoocaze/ocelot",
            "X-Title": "Ocelot CLI"
        }
        super().__init__(api_key=api_key, base_url=base_url, model_name=model_name, debug=debug,
                         show_reasoning=show_reasoning, extra_headers=extra_headers)
