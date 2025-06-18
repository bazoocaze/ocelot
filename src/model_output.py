from typing import Optional

class ModelOutput:
    def __init__(self, show_reasoning: bool = True):
        self._buffer = ""
        self._reasoning = False
        self._show_reasoning = show_reasoning
        self._content = ""

    def add_token(self, token: str):
        self._buffer += token
        if not self._show_reasoning:
            if "<think>" in self._buffer:
                if "</think>" in self._buffer:
                    # Remove think tags and their content
                    start = self._buffer.find("<think>")
                    end = self._buffer.find("</think>") + len("</think>")
                    self._buffer = self._buffer[:start] + self._buffer[end:]
                    self._reasoning = False
                else:
                    self._reasoning = True
            self._content = self._buffer
        else:
            # Escape think tags if not hiding
            self._content = self._buffer.replace(
                "<think>", "\\<think\\>").replace(
                "</think>", "\\</think\\>")

    def content(self):
        if self._reasoning and not self._show_reasoning:
            return ""
        return self._content
