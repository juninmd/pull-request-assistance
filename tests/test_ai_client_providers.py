import unittest
import os
from unittest.mock import MagicMock, patch
import requests

from src.ai_client import get_ai_client, GeminiClient, OllamaClient, OpenAIClient

class TestAIClientProviders(unittest.TestCase):
    def test_get_ai_client_gemini(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test"}):
            client = get_ai_client("gemini")
            self.assertIsInstance(client, GeminiClient)

    def test_get_ai_client_ollama(self):
        client = get_ai_client("ollama")
        self.assertIsInstance(client, OllamaClient)

    def test_get_ai_client_openai(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}):
            client = get_ai_client("openai")
            self.assertIsInstance(client, OpenAIClient)

    def test_get_ai_client_unknown(self):
        with self.assertRaises(ValueError):
            get_ai_client("unknown")

    @patch("src.ai_client.genai.Client")
    def test_gemini_client(self, mock_client_class):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "test response"
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test"}):
            client = GeminiClient()
            self.assertEqual(client.generate("test prompt"), "test response")
            self.assertEqual(client.resolve_conflict("test content", "test block"), "test response\n")
            self.assertEqual(client.generate_pr_comment("test error"), "test response")

    def test_gemini_client_missing_key(self):
        with patch.dict(os.environ, clear=True):
            client = GeminiClient()
            with self.assertRaisesRegex(ValueError, "GEMINI_API_KEY is required"):
                client.generate("test prompt")
            with self.assertRaisesRegex(ValueError, "GEMINI_API_KEY is required"):
                client.resolve_conflict("test content", "test block")
            with self.assertRaisesRegex(ValueError, "GEMINI_API_KEY is required"):
                client.generate_pr_comment("test error")

    @patch("src.ai_client.ollama.Client")
    def test_ollama_client(self, mock_client_class):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.response = "test response"
        mock_client.generate.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = OllamaClient()
        self.assertEqual(client.generate("test prompt"), "test response")
        self.assertEqual(client.resolve_conflict("test content", "test block"), "test response\n")
        self.assertEqual(client.generate_pr_comment("test error"), "test response")

    @patch("src.ai_client.requests.post")
    def test_openai_client(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "test response"}}]
        }
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}):
            client = OpenAIClient()
            self.assertEqual(client.generate("test prompt"), "test response")
            self.assertEqual(client.resolve_conflict("test content", "test block"), "test response\n")
            self.assertEqual(client.generate_pr_comment("test error"), "test response")

    @patch("src.ai_client.requests.post")
    def test_openai_client_empty_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}):
            client = OpenAIClient()
            self.assertEqual(client.generate("test prompt"), "")

    def test_openai_client_missing_key(self):
        with patch.dict(os.environ, clear=True):
            client = OpenAIClient()
            with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY is required"):
                client.generate("test prompt")
