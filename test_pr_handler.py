import unittest
from pr_handler import PRHandler

class TestPRHandler(unittest.TestCase):
    def setUp(self):
        self.handler = PRHandler()

    def test_ignore_other_authors(self):
        pr = {'author': 'Other User', 'has_conflicts': False, 'pipeline_status': 'success'}
        self.assertEqual(self.handler.decide_action(pr), "IGNORE")

    def test_resolve_conflicts(self):
        # Conflicts take precedence over pipeline status
        pr = {'author': 'Jules da Google', 'has_conflicts': True, 'pipeline_status': 'failure'}
        self.assertEqual(self.handler.decide_action(pr), "RESOLVE_CONFLICTS")

    def test_request_corrections_on_failure(self):
        pr = {'author': 'Jules da Google', 'has_conflicts': False, 'pipeline_status': 'failure'}
        self.assertEqual(self.handler.decide_action(pr), "REQUEST_CORRECTIONS")

    def test_auto_merge_on_success(self):
        pr = {'author': 'Jules da Google', 'has_conflicts': False, 'pipeline_status': 'success'}
        self.assertEqual(self.handler.decide_action(pr), "AUTO_MERGE")

if __name__ == '__main__':
    unittest.main()
