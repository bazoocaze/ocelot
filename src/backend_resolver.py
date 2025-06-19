from os import environ

from rich.console import Console

from src.base_llm_backend import BaseLLMBackend
from src.ollama_backend import OllamaBackend
from src.openrouter_backend import OpenRouterBackend

console = Console()

def resolve_backend(model_name: str = None, provider: str = None, debug: bool = False, show_reasoning: bool = True) -> BaseLLMBackend:
    if provider == "openrouter":
        openrouter_api_key = environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            console.print("ERROR: OPENROUTER_API_KEY environment variable is not set", style="bold red")
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")
        return OpenRouterBackend(openrouter_api_key, model=model_name, debug=debug, show_reasoning=show_reasoning)
    elif provider == "ollama":
        if model_name.startswith("ollama/"):
            model_name = model_name[len("ollama/"):]
        return OllamaBackend(model_name, debug=debug)
    else:
        # Default to resolving using the model name
        if model_name and model_name.startswith("openrouter/"):
            model_name = model_name[len("openrouter/"):]
            openrouter_api_key = environ.get("OPENROUTER_API_KEY")
            if not openrouter_api_key:
                console.print("ERROR: OPENROUTER_API_KEY environment variable is not set", style="bold red")
                raise ValueError("OPENROUTER_API_KEY environment variable is not set")
            return OpenRouterBackend(openrouter_api_key, model=model_name, debug=debug, show_reasoning=show_reasoning)
        else:
            # Default to Ollama backend
            if model_name and model_name.startswith("ollama/"):
                model_name = model_name[len("ollama/"):]
            return OllamaBackend(model_name, debug=debug)

