import unittest
from io import StringIO
from unittest.mock import patch

# Import the main function from ocelot_cli.py
from ocelot_cli import run_application, ConfigLoader
from src.ollama_backend import OllamaBackend
from src.provider_factory import ProviderFactory


class TestOllamaIntegrationFlow(unittest.TestCase):

    def setUp(self):
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load_config()
        self.provider_factory = ProviderFactory(config=self.config)
        self.ollama_backend: OllamaBackend = self.provider_factory.resolve_backend('ollama', debug=True)

    @patch('sys.stdout', new_callable=StringIO)
    def test_list_models_command_ollama(self, mock_stdout):
        # Run the list-models command
        run_application(self.config_loader, ['list-models'])

        # Capture the output and check if it contains expected models
        output = mock_stdout.getvalue()
        self.assertIn("Available models:", output)
        self.assertIn("ollama/", output)  # Check for at least one model from ollama

    @patch('sys.stdout', new_callable=StringIO)
    def test_generate_command_ollama(self, mock_stdout):
        # Run a real model name to use
        model_name = self._get_ollama_model_to_use()

        # Run the generate command with a real model name
        run_application(self.config_loader, ['--plain', 'generate', '-m', model_name, 'How much is 75 + 75?'])

        # Capture the output and check if it contains expected content
        output = mock_stdout.getvalue()
        self.assertIn("150", output)  # Check for assistant response

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stdin', new_callable=StringIO)
    def test_chat_command_ollama(self, mock_stdin, mock_stdout):
        # Run a real model name to use
        model_name = self._get_ollama_model_to_use()

        # Mock the input for the chat command
        mock_stdin.write("What is 75 + 75?\nexit\n")
        mock_stdin.seek(0)

        # Run the chat command with a real model name
        run_application(self.config_loader, ['--plain', 'chat', '-m', model_name])

        # Capture the output and check if it contains expected content
        output = mock_stdout.getvalue()
        self.assertIn("Assistant: 150", output)  # Check for assistant response

    def _get_ollama_model_to_use(self):
        running = self.ollama_backend.get_running_models()
        if running:
            return running[0]

        available_models = self.ollama_backend.list_models()
        if available_models:
            return available_models[0]

        self.fail("No running or available Ollama models found")

    @staticmethod
    def _reset_stream(mock_stdout):
        mock_stdout: StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        return mock_stdout


if __name__ == '__main__':
    unittest.main()
