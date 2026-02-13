import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from src.agents.base_agent import BaseAgent

class TestBaseAgent(unittest.TestCase):
    def setUp(self):
        self.mock_jules = MagicMock()
        self.mock_github = MagicMock()
        self.mock_allowlist = MagicMock()

        # Create concrete implementation
        class ConcreteAgent(BaseAgent):
            @property
            def persona(self): return "persona"
            @property
            def mission(self): return "mission"
            def run(self): return {}

        self.agent = ConcreteAgent(self.mock_jules, self.mock_github, self.mock_allowlist, name="test_agent")

    def test_init(self):
        self.assertEqual(self.agent.name, "test_agent")
        self.assertEqual(self.agent.jules_client, self.mock_jules)

    def test_log(self):
        with patch("builtins.print") as mock_print:
            self.agent.log("test")
            mock_print.assert_called_with("[test_agent] [INFO] test")

    def test_get_allowed_repositories(self):
        self.mock_allowlist.list_repositories.return_value = ["repo"]
        self.assertEqual(self.agent.get_allowed_repositories(), ["repo"])

    def test_can_work_on_repository(self):
        self.mock_allowlist.is_allowed.return_value = True
        self.assertTrue(self.agent.can_work_on_repository("repo"))

    def test_get_repository_info_success(self):
        self.mock_github.get_repo.return_value = "repo_obj"
        self.assertEqual(self.agent.get_repository_info("repo"), "repo_obj")

    def test_get_repository_info_error(self):
        self.mock_github.get_repo.side_effect = Exception("error")
        self.assertIsNone(self.agent.get_repository_info("repo"))

    @patch("src.agents.base_agent.Path.exists")
    def test_load_instructions_exists(self, mock_exists):
        mock_exists.return_value = True
        with patch("builtins.open", mock_open(read_data="instructions")):
            content = self.agent.load_instructions()
            self.assertEqual(content, "instructions")
            # Cache check
            self.assertEqual(self.agent._instructions_cache, "instructions")

    @patch("src.agents.base_agent.Path.exists")
    def test_load_instructions_missing(self, mock_exists):
        mock_exists.return_value = False
        content = self.agent.load_instructions()
        self.assertEqual(content, "")

    @patch("src.agents.base_agent.Path.exists")
    def test_load_instructions_error(self, mock_exists):
        mock_exists.return_value = True
        with patch("builtins.open", side_effect=Exception("err")):
            content = self.agent.load_instructions()
            self.assertEqual(content, "")

    @patch.object(BaseAgent, 'load_instructions')
    def test_get_instructions_section(self, mock_load):
        mock_load.return_value = """
## Header 1
Content 1
## Header 2
Content 2
## Header 3
Content 3
"""
        section = self.agent.get_instructions_section("## Header 2")
        self.assertEqual(section.strip(), "Content 2")

    @patch("src.agents.base_agent.Path.exists")
    def test_load_jules_instructions(self, mock_exists):
        mock_exists.return_value = True
        with patch("builtins.open", mock_open(read_data="Prompt with {{var}}")):
            content = self.agent.load_jules_instructions(variables={"var": "val"})
            self.assertEqual(content, "Prompt with val")

    @patch("src.agents.base_agent.Path.exists")
    def test_load_jules_instructions_missing(self, mock_exists):
        mock_exists.return_value = False
        content = self.agent.load_jules_instructions()
        self.assertEqual(content, "")

    def test_create_jules_session_success(self):
        self.mock_allowlist.is_allowed.return_value = True
        self.mock_jules.create_pull_request_session.return_value = {"id": "123"}
        self.mock_jules.wait_for_session.return_value = {"status": "done"}

        res = self.agent.create_jules_session("repo", "instr", "title", wait_for_completion=True)
        self.assertEqual(res["status"], "done")

        self.mock_jules.wait_for_session.assert_called_with("123")

    def test_create_jules_session_not_allowed(self):
        self.mock_allowlist.is_allowed.return_value = False
        with self.assertRaises(ValueError):
            self.agent.create_jules_session("repo", "instr", "title")

if __name__ == '__main__':
    unittest.main()
