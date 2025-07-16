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

    def _populate_openrouter(self, config):
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            config["providers"]["openrouter"] = {
                "type": "openrouter",
                "api_key": openrouter_key
            }
        else:
            config.setdefault("not-found", {})[
                "openrouter"] = "OpenRouter API key not set (env var OPENROUTER_API_KEY)."

    def _populate_ollama(self, config):
        endpoint = OLLAMA_DEFAULT_ENDPOINT
        if self._ollama_is_running(endpoint):
            config["providers"]["ollama"] = {
                "type": "ollama",
                "base_url": endpoint
            }
        else:
            config.setdefault("not-found", {})[
                "ollama"] = f"Ollama not running/detected on {OLLAMA_DEFAULT_ENDPOINT}."

    def load_config(self) -> dict:
        path = self._get_config_path(APP_NAME, CONFIG_FILENAME)
        if path.exists():
            with path.open() as f:
                return yaml.safe_load(f)
        else:
            config = {"providers": {}}
            self._populate_config(config)
            return config

    def _populate_gemini(self, config):
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            config["providers"]["gemini"] = {
                "type": "gemini",
                "api_key": gemini_key
            }
        else:
            config.setdefault("not-found", {})[
                "gemini"] = "Gemini API key not set (env var GEMINI_API_KEY)."

    def _populate_config(self, config):
        self._populate_ollama(config)
        self._populate_openrouter(config)
        self._populate_gemini(config)
