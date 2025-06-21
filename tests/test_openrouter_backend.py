import unittest
from unittest.mock import patch
from src.openrouter_backend import OpenRouterBackend

class TestOpenRouterBackend(unittest.TestCase):

    def setUp(self):
        self.api_key = "test_api_key"
        self.model_name = "test_model"
        self.backend = OpenRouterBackend(api_key=self.api_key, model_name=self.model_name)

    @patch('requests.post')
    def test_generate_success(self, mock_post):
        mock_response = unittest.mock.Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "test content"}}
            ]
        }
        mock_post.return_value = mock_response

        result = self.backend.generate("test prompt")
        self.assertEqual(result, "test content")

    @patch('requests.post')
    def test_generate_failure(self, mock_post):
        mock_response = unittest.mock.Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        with self.assertRaises(RuntimeError) as context:
            self.backend.generate("test prompt")
        self.assertIn("Request error: 400 - Bad Request", str(context.exception))

    @patch('requests.post')
    def test_chat_success(self, mock_post):
        mock_response = unittest.mock.Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "test content"}}
            ]
        }
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "test message"}]
        result = self.backend.chat(messages)
        self.assertEqual(result, "test content")

    @patch('requests.post')
    def test_chat_failure(self, mock_post):
        mock_response = unittest.mock.Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "test message"}]
        with self.assertRaises(RuntimeError) as context:
            self.backend.chat(messages)
        self.assertIn("Request error: 400 - Bad Request", str(context.exception))

    @patch('requests.get')
    def test_list_models_success(self, mock_get):
        mock_response = unittest.mock.Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": [
                {"id": "model1"},
                {"id": "model2"}
            ]
        }
        mock_get.return_value = mock_response

        result = self.backend.list_models()
        self.assertEqual(result, ["model1", "model2"])

    @patch('requests.get')
    def test_list_models_failure(self, mock_get):
        mock_response = unittest.mock.Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_get.return_value = mock_response

        with self.assertRaises(RuntimeError) as context:
            self.backend.list_models()
        self.assertIn("Request error: 400 - Bad Request", str(context.exception))

    @patch('requests.post')
    def test_generate_headers(self, mock_post):
        mock_response = unittest.mock.Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "test content"}}
            ]
        }
        mock_post.return_value = mock_response

        self.backend.generate("test prompt")
        args, kwargs = mock_post.call_args
        headers = kwargs.get('headers', {})
        self.assertIn("HTTP-Referer", headers)
        self.assertEqual(headers["HTTP-Referer"], "https://github.com/bazoocaze/ocelot")
        self.assertIn("X-Title", headers)
        self.assertEqual(headers["X-Title"], "Ocelot CLI")

    @patch('requests.post')
    def test_chat_headers(self, mock_post):
        mock_response = unittest.mock.Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "test content"}}
            ]
        }
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "test message"}]
        self.backend.chat(messages)
        args, kwargs = mock_post.call_args
        headers = kwargs.get('headers', {})
        self.assertIn("HTTP-Referer", headers)
        self.assertEqual(headers["HTTP-Referer"], "https://github.com/bazoocaze/ocelot")
        self.assertIn("X-Title", headers)
        self.assertEqual(headers["X-Title"], "Ocelot CLI")

if __name__ == '__main__':
    unittest.main()
