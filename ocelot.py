import argparse
import json
import sys
from os import environ
from traceback import print_exc
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


class OpenRouterBackend(BaseLLMBackend):
    def __init__(self, api_key: str, model: str, debug: bool = False):
        self._api_key = api_key
        self._model = model
        self._base_url = "https://openrouter.ai/api/v1"
        self._debug = debug

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
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    if line == 'data: [DONE]':
                        break
                    try:
                        data = json.loads(line[6:])  # Skip 'data: ' prefix
                        content = data["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        if self._debug:
                            console.print(f"DEBUG: Failed to parse line: {line}", style="bold red")
                        continue


class OllamaBackend(BaseLLMBackend):
    def __init__(self, model: str, base_url: str = "http://localhost:11434", debug: bool = False):
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._debug = debug

    def generate(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        url = f"{self._base_url}/api/generate"
        payload = {
            "model": self._model,
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
            "model": self._model,
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


def generate_on_backend(ollama, prompt, show_think):
    output = ModelOutput(show_think=show_think)
    with Live(Markdown(output.content()), console=console, refresh_per_second=10) as live:
        for token in ollama.generate(prompt, stream=True):
            output.add_token(token)
            live.update(Markdown(output.content(), style="bright_blue"))
    return 0


def main():
    parser = argparse.ArgumentParser(description="Run a prompt on an LLM model.")
    parser.add_argument("model_name", help="Name of the model to use. Format: [backend/]model_name. Supported backends: ollama, openrouter")
    parser.add_argument("prompt", help="The text prompt to send to the model.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    parser.add_argument("--no-show-think", action="store_true", help="Hide thinking process.")

    args = parser.parse_args()

    model_name: str = args.model_name
    prompt = args.prompt
    debug = args.debug
    no_show_think = args.no_show_think

    if model_name.startswith("openrouter/"):
        model_name = model_name[len("openrouter/"):]
        openrouter_api_key = environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            console.print("ERROR: OPENROUTER_API_KEY environment variable is not set", style="bold red")
            return 1
        backend = OpenRouterBackend(openrouter_api_key, model=model_name, debug=debug)
    else:
        # Default to Ollama backend
        if model_name.startswith("ollama/"):
            model_name = model_name[len("ollama/"):]
        backend = OllamaBackend(model_name, debug=debug)

    try:
        return generate_on_backend(backend, prompt, not no_show_think)
    except KeyboardInterrupt:
        console.print("Keyboard interrupt detected. Exiting...", style="bold red")
        return 1
    except Exception as e:
        console.print(f"ERROR: {e}", style="bold red")
        if debug:
            print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
