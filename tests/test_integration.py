import unittest
from io import StringIO
from unittest.mock import patch

# Import the main function from ocelot_cli.py
from ocelot_cli import run_app, ConfigLoader
from src.ollama_backend import OllamaBackend
from src.provider_factory import ProviderFactory


class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load_config()
        self.provider_factory = ProviderFactory(config=self.config)
        self.ollama_backend: OllamaBackend = self.provider_factory.resolve_backend('ollama', debug=True)

    @patch('sys.stdout', new_callable=StringIO)
    def test_list_models_command_ollama(self, mock_stdout):
        # Run the list-models command
        run_app(self.config_loader, ['list-models'])

        # Capture the output and check if it contains expected models
        output = mock_stdout.getvalue()
        self.assertIn("Available models:", output)
        self.assertIn("ollama/", output)  # Check for at least one model from ollama

    @patch('sys.stdout', new_callable=StringIO)
    def test_generate_command_ollama(self, mock_stdout):
        # Run the list-models command to get available models
        run_app(self.config_loader, ['--plain', 'list-models'])

        # Capture the output and extract a real model name
        output = mock_stdout.getvalue()
        self.assertIn("ollama/", output)

        available_models = [line.strip() for line in output.split('\n') if "ollama/" in line]

        model_name = self._get_running_ollama_model()
        if not model_name:
            model_name = available_models[0]

        mock_stdout = self._reset_stream(mock_stdout)

        # Run the generate command with a real model name
        run_app(self.config_loader, ['--plain', 'generate', '-m', model_name, 'How much is 75 + 75?'])

        # Capture the output and check if it contains expected content
        output = mock_stdout.getvalue()
        self.assertIn("150", output)  # Check for assistant response

    def _get_running_ollama_model(self):
        running = self.ollama_backend.get_running_models()
        if running:
            return running[0]
        else:
            return None

    @staticmethod
    def _reset_stream(mock_stdout):
        mock_stdout: StringIO
        mock_stdout.truncate(0)
        mock_stdout.seek(0)
        return mock_stdout


if __name__ == '__main__':
    unittest.main()
