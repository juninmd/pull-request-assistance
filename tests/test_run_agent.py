import unittest
import sys
from unittest.mock import patch, MagicMock
from src.run_agent import main, save_results

class TestRunAgent(unittest.TestCase):
    def test_no_args(self):
        with patch.object(sys, 'argv', ["run-agent"]):
            with self.assertRaises(SystemExit):
                main()

    def test_unknown_agent(self):
        with patch.object(sys, 'argv', ["run-agent", "unknown"]):
            with self.assertRaises(SystemExit):
                main()

    @patch("src.run_agent.Settings")
    @patch("src.run_agent.PRAssistantAgent")
    @patch("src.run_agent.get_ai_client")
    @patch("src.run_agent.GithubClient")
    @patch("src.run_agent.JulesClient")
    @patch("src.run_agent.RepositoryAllowlist")
    @patch("src.run_agent.save_results")
    def test_run_pr_assistant(self, mock_save, mock_allowlist, mock_jules, mock_github, mock_get_ai, mock_agent_cls, mock_settings):
        with patch.object(sys, 'argv', ["run-agent", "pr-assistant"]):
            mock_agent = mock_agent_cls.return_value
            mock_agent.run.return_value = {"status": "ok"}

            main()

            mock_agent_cls.assert_called_once()
            mock_get_ai.assert_called_once()
            mock_save.assert_called_once()

    @patch("src.run_agent.Settings")
    @patch("src.run_agent.ProductManagerAgent")
    @patch("src.run_agent.save_results")
    @patch("src.run_agent.GithubClient")
    @patch("src.run_agent.JulesClient")
    @patch("src.run_agent.RepositoryAllowlist")
    def test_run_product_manager(self, mock_allowlist, mock_jules, mock_github, mock_save, mock_agent_cls, mock_settings):
        with patch.object(sys, 'argv', ["run-agent", "product-manager"]):
            main()
            mock_agent_cls.assert_called_once()

    @patch("src.run_agent.Settings")
    @patch("src.run_agent.InterfaceDeveloperAgent")
    @patch("src.run_agent.save_results")
    @patch("src.run_agent.GithubClient")
    @patch("src.run_agent.JulesClient")
    @patch("src.run_agent.RepositoryAllowlist")
    def test_run_interface_developer(self, mock_allowlist, mock_jules, mock_github, mock_save, mock_agent_cls, mock_settings):
        with patch.object(sys, 'argv', ["run-agent", "interface-developer"]):
            main()
            mock_agent_cls.assert_called_once()

    @patch("src.run_agent.Settings")
    @patch("src.run_agent.SeniorDeveloperAgent")
    @patch("src.run_agent.save_results")
    @patch("src.run_agent.GithubClient")
    @patch("src.run_agent.JulesClient")
    @patch("src.run_agent.RepositoryAllowlist")
    def test_run_senior_developer(self, mock_allowlist, mock_jules, mock_github, mock_save, mock_agent_cls, mock_settings):
        with patch.object(sys, 'argv', ["run-agent", "senior-developer"]):
            main()
            mock_agent_cls.assert_called_once()

    @patch("src.run_agent.Settings")
    @patch("src.run_agent.PRAssistantAgent")
    @patch("src.run_agent.get_ai_client")
    @patch("src.run_agent.GithubClient")
    @patch("src.run_agent.JulesClient")
    @patch("src.run_agent.RepositoryAllowlist")
    @patch("src.run_agent.save_results")
    def test_run_all(self, mock_save, mock_allowlist, mock_jules, mock_github, mock_get_ai, mock_pr, mock_settings):
        # We need to mock other agents too if 'all' calls them
        with patch("src.run_agent.ProductManagerAgent") as mock_pm, \
             patch("src.run_agent.InterfaceDeveloperAgent") as mock_ui, \
             patch("src.run_agent.SeniorDeveloperAgent") as mock_dev:

            with patch.object(sys, 'argv', ["run-agent", "all"]):
                main()

                mock_pm.assert_called()
                mock_ui.assert_called()
                mock_dev.assert_called()
                mock_pr.assert_called()
                # Each agent runs and saves its own results (4 agents) + 'all' saves aggregated results (1)
                assert mock_save.call_count == 5

    def test_save_results(self):
        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            with patch("src.run_agent.Path.mkdir"):
                save_results("test", {"a": 1})
                mock_file.assert_called()

if __name__ == '__main__':
    unittest.main()
