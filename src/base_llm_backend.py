from abc import abstractmethod, ABC
from typing import List, Dict, Union, Generator


class BaseLLMBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str, stream: bool = False) -> Union[str, Generator[str, None, None]]:
        raise NotImplementedError

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> Union[str, Generator[str, None, None]]:
        raise NotImplementedError

    def list_models(self) -> List[str]:
        """
        Returns a list of available models.
        This method should be implemented by concrete backend classes.

        Returns:
            List[str]: A list of model names.
        """
        raise NotImplementedError
