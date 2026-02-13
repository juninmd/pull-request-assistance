import unittest
import subprocess
import os
from unittest.mock import MagicMock, patch, call, ANY
from src.agents.pr_assistant.agent import PRAssistantAgent

class TestAgent(unittest.TestCase):
    def setUp(self):
        self.mock_github = MagicMock()
        self.mock_jules = MagicMock()
        self.mock_allowlist = MagicMock()
        self.mock_allowlist.is_allowed.return_value = True
        self.mock_ai_client = MagicMock()

        self.agent = PRAssistantAgent(
            self.mock_jules,
            self.mock_github,
            self.mock_allowlist,
            target_owner="juninmd",
            allowed_authors=["juninmd"],
            ai_client=self.mock_ai_client
        )

    def test_init_default_ai(self):
        # Test that it defaults to GeminiClient if no ai_client provided
        with patch("src.agents.pr_assistant.agent.GeminiClient") as mock_gemini:
             agent = PRAssistantAgent(
                self.mock_jules,
                self.mock_github,
                self.mock_allowlist,
                target_owner="juninmd"
             )
             mock_gemini.assert_called_once()
             self.assertEqual(agent.ai_client, mock_gemini.return_value)

    def test_run_flow(self):
        # Mock search result
        mock_issue = MagicMock()
        mock_issue.number = 1
        mock_issue.repository.full_name = "juninmd/test-repo"
        mock_issue.title = "Test PR"

        mock_pr = MagicMock()
        mock_pr.number = 1
        mock_pr.draft = False
        mock_pr.user.login = "juninmd"
        mock_pr.title = "Test PR"
        mock_pr.html_url = "https://github.com/repo/pull/1"

        # Mock issues object with totalCount
        mock_issues = MagicMock()
        mock_issues.totalCount = 1
        mock_issues.__iter__.return_value = iter([mock_issue])
        self.mock_github.search_prs.return_value = mock_issues
        self.mock_github.get_pr_from_issue.return_value = mock_pr

        # Mock process_pr calls
        with patch.object(self.agent, 'process_pr', return_value={"action": "skipped", "pr": 1}) as mock_process:
            self.agent.run()

            self.mock_github.search_prs.assert_called()
            self.mock_github.get_pr_from_issue.assert_called()
            mock_process.assert_called()

            # Verify final summary call
            self.mock_github.send_telegram_msg.assert_called()
            summary_call = self.mock_github.send_telegram_msg.call_args[0][0]
            self.assertIn("PR Assistant Summary", summary_call)
            self.assertIn("*Total Analisados:* 1", summary_call)

    def test_process_pr_clean_merge(self):
        pr = MagicMock()
        pr.number = 1
        pr.mergeable = True
        pr.user.login = "juninmd"
        pr.base.repo.full_name = "juninmd/test-repo"

        # Mock commits and status
        commit = MagicMock()
        combined_status = MagicMock()
        combined_status.state = "success"
        commit.get_combined_status.return_value = combined_status
        commit.get_check_runs.return_value = []
        pr.get_commits.return_value.reversed = [commit]
        pr.get_commits.return_value.totalCount = 1

        self.mock_github.merge_pr.return_value = (True, "Merged")
        self.agent.process_pr(pr)

        self.mock_github.merge_pr.assert_called_with(pr)
        self.mock_github.send_telegram_notification.assert_called_with(pr)

    def test_process_pr_pipeline_failure(self):
        pr = MagicMock()
        pr.number = 2
        pr.mergeable = True
        pr.user.login = "juninmd"
        pr.base.repo.full_name = "juninmd/test-repo"

        commit = MagicMock()
        combined_status = MagicMock()
        combined_status.state = "failure"

        # Mock failed status
        status_fail = MagicMock()
        status_fail.state = "failure"
        status_fail.context = "ci/build"
        status_fail.description = "Build failed"

        combined_status.statuses = [status_fail]
        combined_status.total_count = 1

        commit.get_combined_status.return_value = combined_status
        commit.get_check_runs.return_value = []
        pr.get_commits.return_value.reversed = [commit]
        pr.get_commits.return_value.totalCount = 1

        # Mock AI generation
        self.mock_ai_client.generate_pr_comment.return_value = "AI generated comment"

        self.agent.process_pr(pr)

        # Verify that a comment was created
        pr.create_issue_comment.assert_called_once_with("AI generated comment")
        self.mock_github.merge_pr.assert_not_called()

    def test_process_pr_pipeline_failure_ai_error(self):
        # Fallback test
        pr = MagicMock()
        pr.number = 2
        pr.mergeable = True
        pr.user.login = "juninmd"
        pr.base.repo.full_name = "juninmd/test-repo"

        commit = MagicMock()
        combined_status = MagicMock()
        combined_status.state = "failure"
        status_fail = MagicMock()
        status_fail.state = "failure"
        status_fail.context = "ci/build"
        status_fail.description = "Build failed"
        combined_status.statuses = [status_fail]
        combined_status.total_count = 1
        commit.get_combined_status.return_value = combined_status
        commit.get_check_runs.return_value = []
        pr.get_commits.return_value.reversed = [commit]
        pr.get_commits.return_value.totalCount = 1

        # Mock AI generation failure
        self.mock_ai_client.generate_pr_comment.side_effect = Exception("AI Error")

        self.agent.process_pr(pr)

        # Verify fallback comment
        pr.create_issue_comment.assert_called_once()
        args = pr.create_issue_comment.call_args[0][0]
        self.assertIn("Pipeline Failure Detected", args)


    @patch("src.agents.pr_assistant.agent.subprocess")
    @patch("src.agents.pr_assistant.agent.tempfile.TemporaryDirectory")
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> feature\n")
    def test_resolve_conflicts_autonomously_flow(self, mock_file, mock_tempdir, mock_subprocess):
        mock_subprocess.CalledProcessError = subprocess.CalledProcessError
        # Verify complete autonomous flow
        pr = MagicMock()
        pr.number = 3
        pr.mergeable = False
        pr.user.login = "juninmd"
        pr.base.repo.full_name = "juninmd/repo"
        pr.head.repo.full_name = "fork-user/repo"
        pr.base.repo.clone_url = "https://github.com/juninmd/repo.git"
        pr.head.repo.clone_url = "https://github.com/fork-user/repo.git"
        pr.head.ref = "feature"
        pr.base.ref = "main"
        pr.head.repo.id = 1
        pr.base.repo.id = 2 # Different ID = fork

        self.agent.github_client.token = "TOKEN"

        # Setup temp dir
        mock_tempdir.return_value.__enter__.return_value = "/tmp/repo"

        # Setup subprocess responses
        def side_effect(cmd, **kwargs):
            if cmd[0] == "git" and cmd[1] == "merge":
                raise subprocess.CalledProcessError(1, cmd)
            return MagicMock(returncode=0)

        mock_subprocess.run.side_effect = side_effect
        mock_subprocess.check_output.return_value = b"file1.py\n"


        self.mock_ai_client.resolve_conflict.return_value = "resolved\n"

        self.agent.process_pr(pr)

        self.mock_ai_client.resolve_conflict.assert_called()

    def test_process_pr_mergeable_none(self):
        pr = MagicMock()
        pr.number = 99
        pr.user.login = "juninmd"
        pr.mergeable = None
        pr.base.repo.full_name = "juninmd/repo"

        # Instead of mocking print, we mock self.log which calls print or logger
        # The agent uses self.log
        # BaseAgent.log calls print.

        with patch("builtins.print") as mock_print:
            self.agent.process_pr(pr)
            # We just want to ensure it didn't crash and logged
            # Check arguments of print calls
            found = False
            for call_obj in mock_print.call_args_list:
                args = call_obj[0]
                if args and "mergeability unknown" in str(args[0]):
                    found = True
                    break
            self.assertTrue(found)

    def test_run_with_draft_prs(self):
        """Test that draft PRs are tracked and included in summary"""
        mock_issue_draft = MagicMock()
        mock_issue_draft.number = 1
        mock_issue_draft.repository.full_name = "juninmd/test-repo"
        mock_issue_draft.title = "Draft PR"

        mock_issue_ready = MagicMock()
        mock_issue_ready.number = 2
        mock_issue_ready.repository.full_name = "juninmd/test-repo"
        mock_issue_ready.title = "Ready PR"

        mock_pr_draft = MagicMock()
        mock_pr_draft.number = 1
        mock_pr_draft.draft = True
        mock_pr_draft.user.login = "juninmd"
        mock_pr_draft.title = "Draft PR"
        mock_pr_draft.html_url = "https://github.com/juninmd/test-repo/pull/1"

        mock_pr_ready = MagicMock()
        mock_pr_ready.number = 2
        mock_pr_ready.draft = False
        mock_pr_ready.user.login = "juninmd"
        mock_pr_ready.title = "Ready PR"
        mock_pr_ready.mergeable = True

        # Setup mock ready PR commit status
        commit = MagicMock()
        commit.get_combined_status.return_value.state = "success"
        commit.get_check_runs.return_value = []
        mock_pr_ready.get_commits.return_value.reversed = [commit]
        mock_pr_ready.get_commits.return_value.totalCount = 1

        mock_issues = MagicMock()
        mock_issues.totalCount = 2
        mock_issues.__iter__.return_value = iter([mock_issue_draft, mock_issue_ready])

        self.mock_github.search_prs.return_value = mock_issues
        self.mock_github.get_pr_from_issue.side_effect = [mock_pr_draft, mock_pr_ready]
        self.mock_github.merge_pr.return_value = (True, "Merged")

        result = self.agent.run()

        # Verify draft PR is tracked
        self.assertEqual(len(result['draft_prs']), 1)

        # Verify telegram summary
        summary_call = self.mock_github.send_telegram_msg.call_args[0][0]
        self.assertIn("Draft:", summary_call)
        self.assertIn("*PRs em Draft:*", summary_call)
        self.assertIn("test\-repo\#1", summary_call) # Escaped

    def test_escape_telegram(self):
        text = "Hello_world*"
        escaped = self.agent._escape_telegram(text)
        self.assertEqual(escaped, "Hello\\_world\\*")

    def test_check_pipeline_status_pending_legacy(self):
        pr = MagicMock()
        commit = MagicMock()
        combined = MagicMock()
        combined.state = "pending"
        combined.total_count = 1
        commit.get_combined_status.return_value = combined
        pr.get_commits.return_value.reversed = [commit]
        pr.get_commits.return_value.totalCount = 1

        status = self.agent.check_pipeline_status(pr)
        self.assertFalse(status["success"])
        self.assertEqual(status["reason"], "pending")

    def test_check_pipeline_status_pending_checks(self):
        pr = MagicMock()
        commit = MagicMock()
        combined = MagicMock()
        combined.total_count = 0
        commit.get_combined_status.return_value = combined

        run = MagicMock()
        run.status = "in_progress"
        run.name = "build"
        commit.get_check_runs.return_value = [run]

        pr.get_commits.return_value.reversed = [commit]
        pr.get_commits.return_value.totalCount = 1

        status = self.agent.check_pipeline_status(pr)
        self.assertFalse(status["success"])
        self.assertEqual(status["reason"], "pending")
        self.assertIn("build", status["details"])

if __name__ == '__main__':
    unittest.main()
