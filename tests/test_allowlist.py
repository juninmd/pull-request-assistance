import unittest
import os
import json
import tempfile
from pathlib import Path
from src.config import RepositoryAllowlist

class TestRepositoryAllowlist(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.allowlist_path = os.path.join(self.temp_dir.name, "repositories.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_empty(self):
        # File doesn't exist
        allowlist = RepositoryAllowlist(self.allowlist_path)
        self.assertEqual(len(allowlist.list_repositories()), 0)

    def test_add_and_save(self):
        allowlist = RepositoryAllowlist(self.allowlist_path)
        allowlist.add_repository("owner/repo")
        self.assertTrue(allowlist.is_allowed("owner/repo"))
        self.assertTrue(os.path.exists(self.allowlist_path))

        # Verify file content
        with open(self.allowlist_path, 'r') as f:
            data = json.load(f)
            self.assertIn("owner/repo", data["repositories"])

    def test_remove(self):
        allowlist = RepositoryAllowlist(self.allowlist_path)
        allowlist.add_repository("owner/repo")
        self.assertTrue(allowlist.remove_repository("owner/repo"))
        self.assertFalse(allowlist.is_allowed("owner/repo"))
        self.assertFalse(allowlist.remove_repository("owner/repo"))

    def test_clear(self):
        allowlist = RepositoryAllowlist(self.allowlist_path)
        allowlist.add_repository("a/b")
        allowlist.clear()
        self.assertEqual(len(allowlist.list_repositories()), 0)

    def test_load_existing(self):
        data = {"repositories": ["owner/repo1", "owner/repo2"]}
        with open(self.allowlist_path, 'w') as f:
            json.dump(data, f)

        allowlist = RepositoryAllowlist(self.allowlist_path)
        self.assertTrue(allowlist.is_allowed("owner/repo1"))
        self.assertTrue(allowlist.is_allowed("owner/repo2"))

    def test_create_default(self):
        # Just coverage for the class method
        allowlist = RepositoryAllowlist.create_default_allowlist("testuser")
        self.assertIsInstance(allowlist, RepositoryAllowlist)
