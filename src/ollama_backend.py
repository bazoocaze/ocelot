import json
from typing import List, Dict, Union, Generator

import requests
from rich.console import Console

console = Console()
from src.base_llm_backend import BaseLLMBackend  # Updated import path


class OllamaResponse:
    def __init__(self, line, debug=False):
        self.valid = True
        self.content = ""
        self.line = line.decode('utf-8')
        self._debug = debug
        self._process_line(self.line)

    def _process_line(self, line):
        if not line:
            self.valid = False
            return

        data = json.loads(line)
        content = data.get("response", "")
        if content:
            self.content = content
            return

    @property
    def is_valid(self) -> bool:
        return self.valid

    @property
    def is_content(self) -> bool:
        return bool(self.content)


class OllamaBackend(BaseLLMBackend):
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434", debug: bool = False,
                 show_reasoning: bool = False):
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._debug = debug
        self._show_reasoning = show_reasoning  # unused

    def generate(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        url = f"{self._base_url}/api/generate"
        payload = {
            "model": self._model_name,
            "prompt": prompt,
            "stream": stream
        }
        response = requests.post(url, json=payload, stream=stream)
        if not response.ok:
            if self._debug:
                debug_text = response.text.splitlines()[0]
                console.print(f"DEBUG: status={response.status_code}, text={debug_text}", style="bold")
            raise RuntimeError(f"Request error: {response.status_code} - {response.text}")
        return self._stream_generate_response(response)

    def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> Union[str, Generator[str, None, None]]:
        url = f"{self._base_url}/api/chat"
        payload = {
            "model": self._model_name,
            "messages": messages,
            "stream": stream
        }
        response = requests.post(url, json=payload, stream=stream)
        if not response.ok:
            raise RuntimeError(f"Request error: {response.status_code} - {response.text}")
        return self._stream_chat_response(response)

    def list_models(self) -> List[str]:
        url = f"{self._base_url}/api/tags"
        try:
            response = requests.get(url)
            if not response.ok:
                raise RuntimeError(f"Request error: {response.status_code} - {response.text}")
            data = response.json()
            return [m.get("name") for m in data.get("models", [])]
        except Exception as e:
            console.print(f"ERROR: Failed to fetch models: {e}", style="bold red")
            return []

    def get_running_models(self) -> List[str]:
        url = f"{self._base_url}/api/ps"
        try:
            response = requests.get(url)
            if not response.ok:
                raise RuntimeError(f"Request error: {response.status_code} - {response.text}")
            data = response.json()
            return ["ollama/" + m.get("name") for m in data.get("models", [])]
        except Exception as e:
            console.print(f"ERROR: Failed to fetch running models: {e}", style="bold red")
            return []

    def _stream_generate_response(self, response: requests.Response) -> Generator[str, None, None]:
        for line in response.iter_lines():
            response = OllamaResponse(line, self._debug)
            if response.is_content:
                yield response.content
                continue
            if self._debug:
                console.print(f"DEBUG: Unknown response: {response.line}", style="bold red")

    def _stream_chat_response(self, response: requests.Response) -> Generator[str, None, None]:
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                yield data.get("message", {}).get("content", "")
