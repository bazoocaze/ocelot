from rich.console import Console

from src.constants import APP_REFERER, APP_DISPLAY_NAME
from src.openai_compatible_backend import OpenAiCompatibleApiBackend

console = Console()


class OpenRouterBackend(OpenAiCompatibleApiBackend):
    def __init__(self, api_key: str, model_name: str, debug: bool = False, show_reasoning: bool = True,
                 base_url: str = "https://openrouter.ai/api/v1", **kwargs):
        extra_headers = {
            "HTTP-Referer": APP_REFERER,
            "X-Title": APP_DISPLAY_NAME
        }
        super().__init__(api_key=api_key, base_url=base_url, model_name=model_name, debug=debug,
                         show_reasoning=show_reasoning, extra_headers=extra_headers)
