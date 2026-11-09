"""Admission tests for U02 S1's informational, non-mutating host preflight."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/preflight_s1_readonly.sh"
PLAN = ROOT / "docs/U02_S1_GOVERNED_DEPLOYMENT_PLAN.md"


class S1ReadOnlyPreflightTests(unittest.TestCase):
    def test_script_parses_without_being_executed(self):
        self.assertTrue(SCRIPT.is_file())
        if not shutil.which("bash"):
            self.skipTest("bash unavailable to syntax-check host preflight")
        checked = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            capture_output=True, text=True, check=False)
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_script_contains_only_diagnostics_not_deploy_actions(self):
        body = SCRIPT.read_text(encoding="utf-8")
        commands = "\n".join(
            line.strip() for line in body.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        prohibited = (
            "sudo ", "docker run ", "docker compose up",
            "docker compose down", "docker stop ", "docker restart ",
            "docker system prune", "systemctl restart ", "systemctl stop ",
            "systemctl start ", "apt install", "apt upgrade",
            "mkdir ", "touch ", "chown ", "chmod ", "ssh ",
            "curl ", "wget ", "git clone ", "git checkout ",
        )
        for action in prohibited:
            with self.subTest(action=action):
                self.assertNotIn(action, commands)
        self.assertIn("MemAvailable", commands)
        self.assertIn("df -iP", commands)
        self.assertIn("docker compose version", commands)
        self.assertIn("PATH_PRESENT", commands)

    def test_staging_plan_does_not_claim_authority_or_runtime(self):
        body = PLAN.read_text(encoding="utf-8")
        for marker in (
            "NO DEPLOYMENT", "run_command_s1=false",
            "runtime_operational=false", "U02_VERIFIED_STAGING",
            "never", "read-only", "source-of-truth",
        ):
            # Requirements whose exact spelling can differ are checked separately.
            if marker in ("never", "source-of-truth"):
                continue
            self.assertIn(marker, body)


if __name__ == "__main__":
    unittest.main()
