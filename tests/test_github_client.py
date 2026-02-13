import unittest
from unittest.mock import MagicMock, patch
import os
from src.github_client import GithubClient
from github import GithubException

class TestGithubClient(unittest.TestCase):
    def setUp(self):
        self.token = "fake_token"
        with patch.dict(os.environ, {"GITHUB_TOKEN": self.token}, clear=True):
            self.client = GithubClient()

    def test_init_missing_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                GithubClient()

    def test_search_prs(self):
        with patch.object(self.client.g, 'search_issues') as mock_search:
            self.client.search_prs("query")
            mock_search.assert_called_with("query")

    def test_get_pr_from_issue(self):
        mock_issue = MagicMock()
        self.client.get_pr_from_issue(mock_issue)
        mock_issue.as_pull_request.assert_called_once()

    def test_get_repo(self):
        with patch.object(self.client.g, 'get_repo') as mock_get:
            self.client.get_repo("owner/repo")
            mock_get.assert_called_with("owner/repo")

    def test_merge_pr_success(self):
        mock_pr = MagicMock()
        success, msg = self.client.merge_pr(mock_pr)
        self.assertTrue(success)
        self.assertEqual(msg, "Merged successfully")
        mock_pr.merge.assert_called_once()

    def test_merge_pr_failure(self):
        mock_pr = MagicMock()
        mock_pr.merge.side_effect = GithubException(409, "Conflict")
        success, msg = self.client.merge_pr(mock_pr)
        self.assertFalse(success)
        self.assertIn("Conflict", str(msg))

    def test_comment_on_pr(self):
        mock_pr = MagicMock()
        self.client.comment_on_pr(mock_pr, "body")
        mock_pr.create_issue_comment.assert_called_with("body")

    def test_get_issue_comments(self):
        mock_pr = MagicMock()
        self.client.get_issue_comments(mock_pr)
        mock_pr.get_issue_comments.assert_called_once()

    def test_commit_file_success(self):
        mock_pr = MagicMock()
        mock_repo = MagicMock()
        mock_pr.base.repo = mock_repo
        mock_repo.get_contents.return_value.sha = "sha"
        mock_repo.get_contents.return_value.path = "path"

        result = self.client.commit_file(mock_pr, "path", "content", "msg")
        self.assertTrue(result)
        mock_repo.update_file.assert_called_once()

    def test_commit_file_failure(self):
        mock_pr = MagicMock()
        mock_pr.base.repo.get_contents.side_effect = GithubException(404, "Not Found")

        result = self.client.commit_file(mock_pr, "path", "content", "msg")
        self.assertFalse(result)

    @patch("src.github_client.requests.post")
    def test_send_telegram_msg_success(self, mock_post):
        self.client.telegram_bot_token = "bot"
        self.client.telegram_chat_id = "chat"

        mock_response = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.send_telegram_msg("text")
        self.assertTrue(result)
        mock_post.assert_called_once()

    def test_send_telegram_msg_missing_creds(self):
        self.client.telegram_bot_token = None
        result = self.client.send_telegram_msg("text")
        self.assertIsNone(result)

    @patch("src.github_client.requests.post")
    def test_send_telegram_msg_failure(self, mock_post):
        self.client.telegram_bot_token = "bot"
        self.client.telegram_chat_id = "chat"
        mock_post.side_effect = Exception("Network")

        result = self.client.send_telegram_msg("text")
        self.assertFalse(result)

    def test_send_telegram_notification(self):
        mock_pr = MagicMock()
        mock_pr.title = "Title"
        mock_pr.user.login = "User"
        mock_pr.base.repo.full_name = "Repo"
        mock_pr.body = "Body"

        with patch.object(self.client, 'send_telegram_msg') as mock_send:
            mock_send.return_value = True
            self.client.send_telegram_notification(mock_pr)
            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            self.assertIn("Merged", args[0])

if __name__ == '__main__':
    unittest.main()
