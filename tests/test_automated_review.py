"""Automated review tests: real static checks with no human gate."""
import tempfile
import unittest
from pathlib import Path
from scripts.automated_review import review_repository


class AutomatedReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / ".github" / "workflows").mkdir(parents=True)
        (self.root / "src").mkdir()
        self.workflow = self.root / ".github/workflows/checks.yml"
        self.workflow.write_text("name: Checks\non: push\npermissions:\n  contents: read\njobs:\n  test:\n    runs-on: ubuntu-latest\n")

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_read_only_workflow_passes(self):
        self.assertEqual(review_repository(self.root), [])

    def test_missing_workflow_permissions_blocked(self):
        self.workflow.write_text("name: Checks\non: push\njobs: {}\n")
        self.assertTrue(any("PERMISSIONS_MISSING" in f for f in review_repository(self.root)))

    def test_unsafe_privileged_pr_trigger_blocked(self):
        self.workflow.write_text("name: Checks\non:\n  pull_request_target:\npermissions:\n  contents: read\n")
        self.assertTrue(any("PRIVILEGED_TRIGGER" in f for f in review_repository(self.root)))

    def test_private_key_pattern_blocked(self):
        (self.root / "src" / "private.py").write_text("KEY = '-----BEGIN PRIVATE KEY-----'\n")
        self.assertTrue(any("CREDENTIAL_PATTERN_DETECTED" in f for f in review_repository(self.root)))


if __name__ == "__main__":
    unittest.main()
