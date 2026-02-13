import unittest
from unittest.mock import MagicMock, patch
import os
import time
from src.jules import JulesClient

class TestJulesClient(unittest.TestCase):
    def setUp(self):
        self.api_key = "fake_key"
        self.client = JulesClient(api_key=self.api_key)

    def test_init_env(self):
        with patch.dict(os.environ, {"JULES_API_KEY": "env_key"}, clear=True):
            client = JulesClient()
            self.assertEqual(client.api_key, "env_key")

    def test_init_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                JulesClient()

    @patch("src.jules.client.requests.get")
    def test_list_sources(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"sources": [{"name": "s1"}], "nextPageToken": None}
        mock_get.return_value = mock_response

        sources = self.client.list_sources()
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["name"], "s1")
        # Check URL
        args, kwargs = mock_get.call_args
        self.assertTrue(args[0].endswith("/v1alpha/sources"))

    @patch("src.jules.client.requests.post")
    def test_create_session(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "sessions/123"}
        mock_post.return_value = mock_response

        session = self.client.create_session("source", "prompt")
        self.assertEqual(session["name"], "sessions/123")

        # Check payload
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['prompt'], "prompt")
        self.assertEqual(kwargs['json']['sourceContext']['source'], "source")

    @patch("src.jules.client.requests.get")
    def test_get_session(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "sessions/123"}
        mock_get.return_value = mock_response

        session = self.client.get_session("sessions/123")
        self.assertEqual(session["name"], "sessions/123")

    @patch("src.jules.client.requests.get")
    def test_list_sessions(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"sessions": [{"name": "s1"}]}
        mock_get.return_value = mock_response

        sessions = self.client.list_sessions()
        self.assertEqual(len(sessions), 1)

    @patch("src.jules.client.requests.post")
    def test_approve_plan(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        self.client.approve_plan("sessions/123")
        mock_post.assert_called_once()

    @patch("src.jules.client.requests.post")
    def test_send_message(self, mock_post):
        mock_response = MagicMock()
        mock_response.text = "{}"
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        self.client.send_message("sessions/123", "msg")
        mock_post.assert_called_once()

    @patch("src.jules.client.requests.get")
    def test_list_activities(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"activities": []}
        mock_get.return_value = mock_response

        self.client.list_activities("sessions/123")
        mock_get.assert_called_once()

    @patch("src.jules.client.requests.get")
    def test_wait_for_session_success(self, mock_get):
        # First call: running, Second call: completed
        mock_response1 = MagicMock()
        mock_response1.json.return_value = {"status": "RUNNING"}

        mock_response2 = MagicMock()
        mock_response2.json.return_value = {"status": "COMPLETED", "outputs": ["pr"]}

        mock_get.side_effect = [mock_response1, mock_response2]

        with patch("time.sleep"): # Don't actually sleep
            session = self.client.wait_for_session("sessions/123")
            self.assertEqual(session["status"], "COMPLETED")

    @patch("src.jules.client.requests.get")
    def test_wait_for_session_timeout(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "RUNNING"}
        mock_get.return_value = mock_response

        with patch("time.sleep"):
            # Set time.time to simulate timeout
            # We need to mock time.time so it increments
            with patch("time.time", side_effect=[0, 10, 20, 30, 40]):
                # Wait for 5 seconds max
                with self.assertRaises(TimeoutError):
                    self.client.wait_for_session("sessions/123", max_wait_seconds=5)

    @patch("src.jules.client.requests.post")
    def test_create_pull_request_session(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "s1"}
        mock_post.return_value = mock_response

        self.client.create_pull_request_session("owner/repo", "prompt")

        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['automationMode'], "AUTO_CREATE_PR")
        self.assertEqual(kwargs['json']['sourceContext']['source'], "sources/github/owner/repo")

if __name__ == '__main__':
    unittest.main()
