from typing import List, Dict, Union, Generator


class BaseLLMBackend:
    def generate(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        raise NotImplementedError

    def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> Union[str, Generator[str, None, None]]:
        raise NotImplementedError
