import unittest
from unittest.mock import patch, MagicMock
from src.main import main
import sys

class TestMain(unittest.TestCase):
    @patch("src.main.PRAssistantAgent")
    @patch("src.main.GithubClient")
    @patch("src.main.JulesClient")
    @patch("src.main.RepositoryAllowlist")
    @patch("src.main.Settings")
    @patch("src.main.get_ai_client")
    def test_main(self, mock_get_ai, mock_settings, mock_allowlist, mock_jules, mock_github, mock_agent):
        mock_settings_instance = MagicMock()
        mock_settings_instance.jules_api_key = "key"
        mock_settings_instance.repository_allowlist_path = "path"
        mock_settings_instance.github_owner = "owner"
        mock_settings.from_env.return_value = mock_settings_instance

        main()

        mock_settings.from_env.assert_called_once()
        mock_get_ai.assert_called_once_with(mock_settings_instance)
        mock_agent.assert_called_once()
        mock_agent.return_value.run.assert_called_once()

    @patch("src.main.Settings")
    def test_main_error(self, mock_settings):
        mock_settings.from_env.side_effect = Exception("Config error")
        with self.assertRaises(SystemExit):
            main()

if __name__ == '__main__':
    unittest.main()
