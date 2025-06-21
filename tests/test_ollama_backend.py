import unittest
from unittest.mock import patch, MagicMock
from src.ollama_backend import OllamaBackend

class TestOllamaBackend(unittest.TestCase):

    def setUp(self):
        self.backend = OllamaBackend(model_name="test_model", base_url="http://localhost:11434")

    @patch('requests.post')
    def test_generate_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = [b'{"response": "Hello, world!"}']
        mock_post.return_value = mock_response

        result = list(self.backend.generate("Test prompt", stream=True))
        self.assertEqual(result, ["Hello, world!"])

    @patch('requests.post')
    def test_generate_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with self.assertRaises(RuntimeError) as context:
            list(self.backend.generate("Test prompt", stream=True))
        self.assertIn("Request error: 500 - Internal Server Error", str(context.exception))

    @patch('requests.post')
    def test_chat_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = [b'{"message": {"content": "Hello, world!"}}']
        mock_post.return_value = mock_response

        result = list(self.backend.chat([{"role": "user", "content": "Test prompt"}], stream=True))
        self.assertEqual(result, ["Hello, world!"])

    @patch('requests.post')
    def test_chat_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with self.assertRaises(RuntimeError) as context:
            list(self.backend.chat([{"role": "user", "content": "Test prompt"}], stream=True))
        self.assertIn("Request error: 500 - Internal Server Error", str(context.exception))

    @patch('requests.get')
    def test_list_models_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"models": [{"name": "test_model"}]}
        mock_get.return_value = mock_response

        result = self.backend.list_models()
        self.assertEqual(result, ["test_model"])

    @patch('requests.get')
    def test_list_models_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        result = self.backend.list_models()
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()
