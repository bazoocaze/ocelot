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
from src.model_output import ModelOutput  # Updated import path

class BaseLLMBackend:
    def generate(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        raise NotImplementedError

    def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> Union[str, Generator[str, None, None]]:
        raise NotImplementedError

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

def generate_on_backend(ollama, prompt, show_reasoning, debug=False):
    output = ModelOutput(show_reasoning=show_reasoning)
    if debug:
        for token in ollama.generate(prompt, stream=True):
            output.add_token(token)
            print(f"[{token}]", end="", flush=True)
        print("\n--- CONTENT ---")
        print(output.content())
        print("---")
    else:
        with Live(Markdown(output.content()), console=console, refresh_per_second=10) as live:
            for token in ollama.generate(prompt, stream=True):
                output.add_token(token)
                live.update(Markdown(output.content(), style="bright_blue"))
    return 0

def run_command(args):
    model_name = args.model_name
    prompt = args.prompt
    debug = args.debug
    show_reasoning = not args.no_show_reasoning

    if model_name.startswith("openrouter/"):
        model_name = model_name[len("openrouter/"):]
        openrouter_api_key = environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            console.print("ERROR: OPENROUTER_API_KEY environment variable is not set", style="bold red")
            return 1
        backend = OpenRouterBackend(openrouter_api_key, model=model_name, debug=debug, show_reasoning=show_reasoning)
    else:
        # Default to Ollama backend
        if model_name.startswith("ollama/"):
            model_name = model_name[len("ollama/"):]
        backend = OllamaBackend(model_name, debug=debug)

    try:
        return generate_on_backend(backend, prompt, show_reasoning, debug=debug)
    except KeyboardInterrupt:
        console.print("Keyboard interrupt detected. Exiting...", style="bold red")
        return 1
    except Exception as e:
        console.print(f"ERROR: {e}", style="bold red")
        if debug:
            print_exc()
        return 1

def main():
    parser = argparse.ArgumentParser(description="Run a prompt on an LLM model.")
    subparsers = parser.add_subparsers(dest='command', help='Subcommands')

    # Run command
    run_parser = subparsers.add_parser('run', help='Run a prompt')
    run_parser.add_argument("model_name",
                            help="Name of the model to use. Format: [backend/]model_name. Supported backends: ollama, openrouter")
    run_parser.add_argument("prompt", help="The text prompt to send to the model.")
    run_parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    run_parser.add_argument("--no-show-reasoning", action="store_true", help="Hide reasoning process.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'run':
        return run_command(args)

if __name__ == "__main__":
    sys.exit(main())
