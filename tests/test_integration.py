import unittest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO

# Import the main function from ocelot_cli.py
from ocelot_cli import run_app, ConfigLoader

class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load_config()

    @patch('sys.argv', ['ocelot_cli.py', 'list-models'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_list_models_command(self, mock_stdout):
        # Run the list-models command
        run_app(self.config_loader)

        # Capture the output and check if it contains expected models
        output = mock_stdout.getvalue()
        self.assertIn("Available models:", output)
        self.assertIn("ollama/", output)  # Check for at least one model from ollama

    @patch('sys.argv', ['ocelot_cli.py', 'list-models'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_generate_command(self, mock_stdout):
        # Run the list-models command to get available models
        run_app(self.config_loader)

        # Capture the output and extract a real model name
        output = mock_stdout.getvalue()
        self.assertIn("Available models:", output)

        # Extract the first available model from ollama
        lines = output.split('\n')
        for line in lines:
            if "ollama/" in line:
                model_name = line.strip()
                break

        # Run the generate command with a real model name
        sys.argv = ['ocelot_cli.py', 'generate', '-m', model_name, 'Hello, world!']
        run_app(self.config_loader)

        # Capture the output and check if it contains expected content
        output = mock_stdout.getvalue()
        self.assertIn("Assistant:", output)  # Check for assistant response

if __name__ == '__main__':
    unittest.main()
