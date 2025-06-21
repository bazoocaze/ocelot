import unittest
from unittest.mock import patch

from src.provider_factory import ProviderFactory

class TestProviderFactory(unittest.TestCase):
    def setUp(self):
        self.config = {
            "providers": {
                "ollama": {"type": "ollama"},
                "openrouter": {"type": "openrouter"},
                "openai": {"type": "openai"}
            }
        }
        self.provider_factory = ProviderFactory(config=self.config)

    def test_parse_model_name_single_provider(self):
        model_name = "test-model"
        provider, name = self.provider_factory.parse_model_name(model_name)
        self.assertEqual(provider, "ollama")
        self.assertEqual(name, model_name)

    def test_parse_model_name_multiple_providers(self):
        config_with_multiple_providers = {
            "providers": {
                "provider1": {"type": "ollama"},
                "provider2": {"type": "openrouter"}
            }
        }
        provider_factory = ProviderFactory(config=config_with_multiple_providers)
        model_name = "test-model"
        provider, name = provider_factory.parse_model_name(model_name)
        self.assertEqual(provider, "ollama")
        self.assertEqual(name, model_name)

    def test_parse_model_name_with_provider_prefix(self):
        model_name = "provider1/test-model"
        provider, name = self.provider_factory.parse_model_name(model_name)
        self.assertEqual(provider, "provider1")
        self.assertEqual(name, "test-model")

    def test_resolve_backend_success(self):
        backend = self.provider_factory.resolve_backend(provider_name="ollama", model_name="test-model")
        self.assertIsNotNone(backend)

    def test_resolve_backend_provider_not_found(self):
        with self.assertRaises(ValueError) as context:
            self.provider_factory.resolve_backend(provider_name="unknown-provider", model_name="test-model")
        self.assertTrue("Provider 'unknown-provider' not found or not configured." in str(context.exception))

    def test_resolve_backend_type_not_supported(self):
        config_with_unsupported_provider = {
            "providers": {
                "ollama": {"type": "unsupported-type"}
            }
        }
        provider_factory = ProviderFactory(config=config_with_unsupported_provider)
        with self.assertRaises(ValueError) as context:
            provider_factory.resolve_backend(provider_name="ollama", model_name="test-model")
        self.assertTrue("Provider type 'unsupported-type' not supported." in str(context.exception))

    def test_all_providers(self):
        providers = self.provider_factory.all_providers()
        self.assertEqual(set(providers), set(["ollama", "openrouter", "openai"]))
