import argparse
import json
import sys
from typing import List, Dict, Optional, Union, Generator

import requests
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

console = Console()


class BaseLLMBackend:
    def generate(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        raise NotImplementedError

    def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> Union[str, Generator[str, None, None]]:
        raise NotImplementedError


class OllamaBackend(BaseLLMBackend):
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream
        }
        response = requests.post(url, json=payload, stream=stream)
        if not response.ok:
            raise RuntimeError(f"Request error: {response.status_code} - {response.text}")
        return self._stream_generate_response(response)

    def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> Union[str, Generator[str, None, None]]:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }
        response = requests.post(url, json=payload, stream=stream)
        if not response.ok:
            raise RuntimeError(f"Request error: {response.status_code} - {response.text}")
        return self._stream_chat_response(response)

    def _stream_generate_response(self, response: requests.Response) -> Generator[str, None, None]:
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                yield data.get("response", "")

    def _stream_chat_response(self, response: requests.Response) -> Generator[str, None, None]:
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                yield data.get("message", {}).get("content", "")


class ChatSession:
    def __init__(self, backend: BaseLLMBackend, system_prompt: Optional[str] = None):
        self.backend = backend
        self.messages: List[Dict[str, str]] = []
        if system_prompt:
            self.add_system(system_prompt)

    def add_system(self, content: str):
        self.messages.append({"role": "system", "content": content})

    def add_user(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def ask(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        self.add_user(prompt)
        response = self.backend.chat(self.messages, stream=stream)
        if not stream:
            self.add_assistant(response)
            return response

        def streaming_response():
            full = ""
            for token in response:
                yield token
                full += token
            self.add_assistant(full)

        return streaming_response()


class ModelOutput:
    def __init__(self, show_think: bool = True):
        self._buffer = ""
        self._thinking = False
        self._show_think = show_think
        self._content = ""

    def add_token(self, token: str):
        self._buffer += token
        if not self._show_think:
            if "<think>" in self._buffer:
                if "</think>" in self._buffer:
                    # Remove think tags and their content
                    start = self._buffer.find("<think>")
                    end = self._buffer.find("</think>") + len("</think>")
                    self._buffer = self._buffer[:start] + self._buffer[end:]
                    self._thinking = False
                else:
                    self._thinking = True
            self._content = self._buffer
        else:
            # Escape think tags if not hiding
            self._content = self._buffer.replace(
                "<think>", "\\<think\\>").replace(
                "</think>", "\\</think\\>")

    def content(self):
        if self._thinking and not self._show_think:
            return ""
        return self._content


def generate_on_backend(ollama, prompt, debug, show_think):
    output = ModelOutput(show_think=show_think)
    with Live(Markdown(output.content()), console=console, refresh_per_second=10) as live:
        for token in ollama.generate(prompt, stream=True):
            output.add_token(token)
            live.update(Markdown(output.content(), style="bright_blue"))
    return 0


def main():
    parser = argparse.ArgumentParser(description="Run a prompt on an Ollama model.")
    parser.add_argument("model_name", help="Name of the Ollama model to use.")
    parser.add_argument("prompt", help="The text prompt to send to the model.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    parser.add_argument("--no-show-think", action="store_true", help="Hide thinking process.")

    args = parser.parse_args()

    model_name = args.model_name
    prompt = args.prompt
    debug = args.debug
    no_show_think = args.no_show_think

    ollama = OllamaBackend(model_name)

    return generate_on_backend(ollama, prompt, debug, not no_show_think)


if __name__ == "__main__":
    sys.exit(main())
