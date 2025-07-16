from typing import List

from rich.console import Console

from src.base_llm_backend import BaseLLMBackend
from src.gemini_backend import GeminiBackend
from src.ollama_backend import OllamaBackend
from src.openai_compatible_backend import OpenAiCompatibleApiBackend
from src.openrouter_backend import OpenRouterBackend

console = Console()

BACKEND_CLASSES = {
    "ollama": OllamaBackend,
    "openrouter": OpenRouterBackend,
    "openai": OpenAiCompatibleApiBackend,
    "gemini": GeminiBackend,
}


class ProviderFactory:
    def __init__(self, config: dict):
        self._providers = config["providers"]

    def parse_model_name(self, model_name: str):
        if "/" not in model_name:
            if len(self.all_providers()) == 1:
                return self.all_providers()[0], model_name
            else:
                return "ollama", model_name
        return model_name.split("/", 1)

    def resolve_backend(self, provider_name: str = None, model_name: str = None, debug: bool = False,
                        show_reasoning: bool = True) -> BaseLLMBackend:
        kwargs = {
            "debug": debug,
            "show_reasoning": show_reasoning,
            "model_name": model_name or "none",
        }

        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' not found or not configured.")

        provider_cfg = self._providers[provider_name]
        provider_type = provider_cfg["type"]

        if provider_type not in BACKEND_CLASSES:
            raise ValueError(
                f"Provider type '{provider_type}' not supported. Available: {list(BACKEND_CLASSES.keys())}")

        cls = BACKEND_CLASSES[provider_type]

        kwargs.update(provider_cfg)
        kwargs["type"] = None

        # Remove None
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        return cls(**kwargs)

    def all_providers(self) -> List[str]:
        return list(self._providers.keys())
