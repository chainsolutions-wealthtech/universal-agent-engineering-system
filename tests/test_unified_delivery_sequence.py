"""Continuity-contract checks: one delivery order, no invented runtime."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class UnifiedDeliverySequenceTests(unittest.TestCase):
    def test_unified_steps_are_unique_and_ordered(self):
        content = (ROOT / "docs/UNIFIED_DELIVERY_SEQUENCE.md").read_text(encoding="utf-8")
        steps = re.findall(r"^\| (U\d{2}) \|", content, flags=re.MULTILINE)
        self.assertEqual(steps, [f"U{i:02d}" for i in range(12)])
        self.assertIn("U00_MAIN_RULESET_RUNBOOK.md", content)

    def test_historical_roadmaps_remain_and_link_unified_order(self):
        for path, first, last in (
            ("docs/BUILD_PLAN.md", "P00", "P13"),
            ("docs/AUTONOMY_IMPLEMENTATION_ROADMAP.md", "A00", "A12"),
        ):
            body = (ROOT / path).read_text(encoding="utf-8")
            for name in ("UNIFIED_DELIVERY_SEQUENCE.md", first, last):
                self.assertIn(name, body)

    def test_integrated_state_attests_native_ruleset_without_inventing_runtime(self):
        state = json.loads((ROOT / "state/CURRENT_STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(state["execution_sequence_ref"], "docs/UNIFIED_DELIVERY_SEQUENCE.md")
        self.assertFalse(state["runtime_operational"])
        self.assertEqual(state["active_gate"], "U02")
        self.assertNotIn("MAIN_RULESET_UNENFORCED", state["blocked_gates"])
        self.assertNotIn("PROVIDER_REVIEW_POLICY_UNVERIFIED", state["blocked_gates"])
        self.assertIn("UAES_RUNTIME_UNATTESTED", state["blocked_gates"])
        self.assertIn("UAES_APP_PERMISSIONS_UNATTESTED", state["blocked_gates"])
        self.assertEqual(state["owner_pr_review_policy"], "NO_MANDATORY_HUMAN_REVIEW")
        self.assertEqual(state["authorized_account_mapping_ref"],
                         "state/AUTHORIZED_BYPASS_ACCOUNTS.json")
        receipt = state["u00_provider_receipt"]
        self.assertEqual(receipt["ruleset_id"], 26883048)
        self.assertTrue(receipt["branch_protected"])
        self.assertEqual(receipt["enforcement"], "active")
        self.assertEqual(receipt["target_branch"], "main")
        self.assertEqual(receipt["required_human_approvals"], 0)
        self.assertEqual(receipt["required_check_integration_id"], 15368)
        self.assertEqual(receipt["required_checks"],
                         ["core-tests", "documentary-contracts", "container-smoke",
                          "automated-review", "determine-next"])
        self.assertEqual(
            {(a["actor_type"], a["actor_id"], a["bypass_mode"])
             for a in receipt["bypass_actors"]},
            {("User", 94637590, "always"), ("User", 270385782, "always"),
             ("Integration", 5417646, "always")})
        self.assertEqual(state["u01_integrations"]["bootstrap"]["pr"], 1)
        self.assertEqual(state["u01_integrations"]["continuity"]["pr"], 7)
        self.assertEqual(
            state["u01_integrations"]["merge_sequence"], ["PR#1", "PR#7"])
        self.assertEqual(
            state["u01_integrations"]["latest_main_sha_at_attestation"],
            "91b6e5fb674c30a29ca07b7dc024db7671db9ade")
        self.assertNotIn("runtime", state["status"].lower())


if __name__ == "__main__":
    unittest.main()
