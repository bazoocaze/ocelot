import unittest
from src.model_output import ModelOutput

class TestModelOutput(unittest.TestCase):
    def setUp(self):
        self.output = ModelOutput(show_reasoning=False)

    def test_add_token_single(self):
        self.output.add_token("Hello")
        self.assertEqual(self.output.content(), "Hello")

    def test_add_token_multiple(self):
        self.output.add_token("Hello ")
        self.output.add_token("World!")
        self.assertEqual(self.output.content(), "Hello World!")

    def test_add_token_with_reasoning_tags_hidden(self):
        self.output.add_token("<think>This is a thought</think>")
        self.assertEqual(self.output.content(), "")

    def test_add_token_with_reasoning_tags_shown(self):
        output = ModelOutput(show_reasoning=True)
        output.add_token("<think>This is a thought</think>")
        self.assertEqual(output.content(), "\\<think\\>This is a thought\\</think\\>")

    def test_add_token_partial_reasoning_tag(self):
        self.output.add_token("<think>This is a ")
        self.output.add_token("thought</think>")
        self.assertEqual(self.output.content(), "")

    def test_add_token_nested_reasoning_tags(self):
        self.output.add_token("<think>This is <nested> thought</nested></think>")
        self.assertEqual(self.output.content(), "")

if __name__ == '__main__':
    unittest.main()
