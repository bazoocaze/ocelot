from typing import List, Dict, Union, Generator

import requests
from rich.console import Console

from src.base_llm_backend import BaseLLMBackend

console = Console()


class GeminiBackend(BaseLLMBackend):
    def __init__(self, api_key: str, model_name: str, base_url: str = "http://localhost:11434", debug: bool = False,
                 show_reasoning: bool = False):
        self._api_key = api_key
        self._model_name = model_name
        self._base_url = base_url
        self._debug = debug
        self._show_reasoning = show_reasoning

    def _get_headers(self):
        if not self._api_key:
            print("Error: GEMINI_API_KEY environment variable is not set.")
            return None

        headers = {
            "X-Goog-Api-Key": self._api_key,
            "Content-Type": "application/json"
        }
        return headers

    def _generate_content(self, parts):
        headers = self._get_headers()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model_name}:generateContent"
        data = {
            "contents": [{
                "parts": parts
            }]
        }

        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(f"Request error: {response.status_code} - {response.text}")
        if self._debug:
            console.print(f"DEBUG: status={response.status_code}, text={response.json()}", style="bold")

        response_json = response.json()
        content = response_json.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        yield content

    def generate(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        parts = [{"text": prompt}]
        yield from self._generate_content(parts)

    def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> Union[str, Generator[str, None, None]]:
        parts = [{"text": message["content"]} for message in messages]
        yield from self._generate_content(parts)

    def list_models(self) -> List[str]:
        headers = self._get_headers()
        url = "https://generativelanguage.googleapis.com/v1beta/models"

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(f"Request error: {response.status_code} - {response.text}")

        response_json = response.json()
        models = response_json.get('models', [])

        return [model.get('name', '').replace('models/', '') for model in models]
