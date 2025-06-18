from typing import List, Dict, Union, Generator
import json
import requests
from rich.console import Console

console = Console()
from src.base_llm_backend import BaseLLMBackend  # Updated import path

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

class OpenRouterBackend(BaseLLMBackend):
    def __init__(self, api_key: str, model: str, debug: bool = False, show_reasoning: bool = True):
        self._api_key = api_key
        self._model = model
        self._base_url = "https://openrouter.ai/api/v1"
        self._debug = debug
        self._show_reasoning = show_reasoning

    def generate(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": "https://github.com/bazoocaze/ocelot",
            "X-Title": "Ocelot CLI"
        }

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": stream
        }

        response = requests.post(url, headers=headers, json=payload, stream=stream)
        if not response.ok:
            if self._debug:
                debug_text = response.text.splitlines()[0]
                console.print(f"DEBUG: status={response.status_code}, text={debug_text}", style="bold")
            raise RuntimeError(f"Request error: {response.status_code} - {response.text}")

        if stream:
            return self._stream_response(response)
        else:
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> Union[str, Generator[str, None, None]]:
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": "https://github.com/yourusername/ocelot",  # Replace with your actual repo
            "X-Title": "Ocelot CLI"
        }

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": stream
        }

        response = requests.post(url, headers=headers, json=payload, stream=stream)
        if not response.ok:
            if self._debug:
                debug_text = response.text.splitlines()[0]
                console.print(f"DEBUG: status={response.status_code}, text={debug_text}", style="bold")
            raise RuntimeError(f"Request error: {response.status_code} - {response.text}")

        if stream:
            return self._stream_response(response)
        else:
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def _stream_response(self, response: requests.Response) -> Generator[str, None, None]:
        reasoning = False
        for line in response.iter_lines():
            if not line:
                continue
            response = OpenRouterResponse(line, self._debug)
            if response.is_done:
                break
            if response.is_content:
                if reasoning:
                    reasoning = False
                    yield "</think>\n\n"
                yield response.content
                continue
            if response.is_reasoning and self._show_reasoning:
                if not reasoning:
                    reasoning = True
                    yield "<think>"
                yield response.reasoning
                continue
            if self._debug:
                console.print(f"DEBUG: Unknown response: {response.line}", style="bold red")
