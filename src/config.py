import os
from pathlib import Path

import requests
import yaml

from src.constants import APP_NAME, CONFIG_FILENAME, OLLAMA_DEFAULT_ENDPOINT


class ConfigLoader:
    def _get_config_path(self, app_name, filename) -> Path:
        config_home = Path(os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config")
        return config_home / app_name / filename

    def _ollama_is_running(self, base_url) -> bool:
        try:
            r = requests.get(f"{base_url}/api/tags", timeout=1)
            return r.ok
        except requests.RequestException:
            return False

    def _get_default_providers(self) -> dict:
        providers = {}

        endpoint = OLLAMA_DEFAULT_ENDPOINT
        if self._ollama_is_running(endpoint):
            providers["ollama"] = {
                "type": "ollama",
                "base_url": endpoint
            }

        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            providers["openrouter"] = {
                "type": "openrouter",
                "api_key": openrouter_key
            }

        return providers

    def load_config(self) -> dict:
        path = self._get_config_path(APP_NAME, CONFIG_FILENAME)
        if path.exists():
            with path.open() as f:
                return yaml.safe_load(f)
        else:
            return {"providers": self._get_default_providers()}
