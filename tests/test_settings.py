import unittest
import os
from unittest.mock import patch
from src.config import Settings

class TestSettings(unittest.TestCase):
    def test_defaults(self):
        # Mock env vars
        with patch.dict(os.environ, {
            "GITHUB_TOKEN": "token",
            "JULES_API_KEY": "key"
        }, clear=True):
            settings = Settings.from_env()
            self.assertEqual(settings.ai_provider, "gemini")
            self.assertEqual(settings.ollama_base_url, "http://localhost:11434")
            self.assertEqual(settings.ollama_model, "llama3")
            self.assertIsNone(settings.ai_model)

    def test_custom_values(self):
         with patch.dict(os.environ, {
            "GITHUB_TOKEN": "token",
            "JULES_API_KEY": "key",
            "AI_PROVIDER": "ollama",
            "AI_MODEL": "custom-model",
            "OLLAMA_BASE_URL": "http://custom:1234",
            "OLLAMA_MODEL": "custom-llama"
        }, clear=True):
            settings = Settings.from_env()
            self.assertEqual(settings.ai_provider, "ollama")
            self.assertEqual(settings.ai_model, "custom-model")
            self.assertEqual(settings.ollama_base_url, "http://custom:1234")
            self.assertEqual(settings.ollama_model, "custom-llama")

    def test_missing_required(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                Settings.from_env()

if __name__ == '__main__':
    unittest.main()
