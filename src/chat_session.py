from typing import List, Dict, Optional, Union, Generator

from src.base_llm_backend import BaseLLMBackend  # Updated import path


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
