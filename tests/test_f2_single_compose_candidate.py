"""Static non-regression checks for U02 F.2 candidate; no deployment effects."""
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "compose.f2-candidate.yaml"
BASE = ROOT / "compose.yaml"


class F2SingleComposeCandidateTests(unittest.TestCase):
    def test_base_is_not_replaced(self):
        self.assertTrue(BASE.is_file())
        self.assertTrue(CANDIDATE.is_file())
        self.assertNotEqual(BASE.resolve(), CANDIDATE.resolve())

    def test_preserves_canonical_identity_storage_and_security(self):
        base = BASE.read_text(encoding="utf-8")
        candidate = CANDIDATE.read_text(encoding="utf-8")
        for marker in (
            "UAES_DB: /data/uaes.sqlite",
            "UAES_AGENT_ID: ${UAES_AGENT_ID:?existing agent identity required}",
            "UAES_MANDATE_ID: ${UAES_MANDATE_ID:?approved mandate required}",
            "- uaes_data:/data",
            "http://127.0.0.1:8080/readyz",
            "no-new-privileges:true",
            "read_only: true",
            "- /tmp",
        ):
            self.assertIn(marker, base)
            self.assertIn(marker, candidate)
        self.assertNotIn("ports:", candidate)
        self.assertNotIn("/var/run/docker.sock", candidate)

    def test_resource_envelope_and_single_file(self):
        candidate = CANDIDATE.read_text(encoding="utf-8")
        for marker in (
            'cpus: "0.35"',
            "mem_limit: 256m",
            "memswap_limit: 256m",
            "pids_limit: 64",
            "cap_drop:",
            "- ALL",
            'max-size: "5m"',
            'max-file: "3"',
        ):
            self.assertIn(marker, candidate)

    def test_compose_config_when_available(self):
        if not shutil.which("docker"):
            self.skipTest("Docker Compose unavailable; static assertions still run")
        version = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
        if version.returncode:
            self.skipTest("Docker Compose plugin unavailable")
        env = dict(os.environ, UAES_AGENT_ID="synthetic-test-agent", UAES_MANDATE_ID="synthetic-test-mandate")
        result = subprocess.run(
            ["docker", "compose", "-f", str(CANDIDATE), "config", "--quiet"],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
