"""Static admission controls for S1 resource-capped UAES staging overlay."""
import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "compose.yaml"
OVERLAY = ROOT / "compose.s1-staging.yaml"


class S1ResourceBoundedStagingTests(unittest.TestCase):
    def test_overlay_limits_are_explicit_and_host_isolation_preserved(self):
        candidate = OVERLAY.read_text(encoding="utf-8")
        baseline = BASE.read_text(encoding="utf-8")
        for expected in (
            '    cpus: "0.35"',
            "    mem_limit: 256m",
            "    memswap_limit: 256m",
            "    pids_limit: 64",
            "    cap_drop:",
            "      - ALL",
            "    logging:",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, candidate)
        for forbidden in (
            "privileged:", "network_mode:", "ports:", "docker.sock",
            "container_name:", "volumes:", "UAES_AGENT_ID:", "UAES_MANDATE_ID:",
            "build:", "image:", "secrets:", "user: root",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, candidate)
        # Preserve mandatory existing effective identity, storage and safety.
        self.assertIn("UAES_AGENT_ID: ${UAES_AGENT_ID:?existing agent identity required}", baseline)
        self.assertIn("UAES_MANDATE_ID: ${UAES_MANDATE_ID:?approved mandate required}", baseline)
        self.assertIn("uaes_data:/data", baseline)
        self.assertIn("    read_only: true", baseline)
        self.assertIn("no-new-privileges:true", baseline)
        self.assertNotIn("ports:", baseline)

    def test_compose_overlay_configuration_parses_if_compose_available(self):
        if not shutil.which("docker"):
            self.skipTest("Docker CLI absent, no host deployment assumed")
        check = subprocess.run(
            ["docker", "compose", "version"], capture_output=True,
            text=True, timeout=15, check=False)
        if check.returncode != 0:
            self.skipTest("Docker Compose CLI absent")
        # Placeholder IDs are used only to parse the composed configuration;
        # never run 'up' or write a runtime/authorization record.
        env = dict(os.environ)
        env["UAES_AGENT_ID"] = "config-schema-only-not-an-agent"
        env["UAES_MANDATE_ID"] = "config-schema-only-not-a-mandate"
        check = subprocess.run(
            ["docker", "compose", "-p", "uaes-staging",
             "-f", str(BASE), "-f", str(OVERLAY),
             "config", "--quiet"],
            env=env, capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(check.returncode, 0, check.stderr)


if __name__ == "__main__":
    unittest.main()
