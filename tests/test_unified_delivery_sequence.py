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

    def test_bootstrap_state_never_pretends_hosted_runtime_exists(self):
        state = json.loads((ROOT / "state/CURRENT_STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(state["execution_sequence_ref"], "docs/UNIFIED_DELIVERY_SEQUENCE.md")
        self.assertFalse(state["runtime_operational"])
        self.assertEqual(state["active_gate"], "U00")
        self.assertIn("MAIN_RULESET_UNENFORCED", state["blocked_gates"])
        self.assertNotIn("INDEPENDENT_REVIEW_MISSING", state["blocked_gates"])
        self.assertEqual(state["owner_pr_review_policy"], "NO_MANDATORY_HUMAN_REVIEW")
        self.assertIn("PROVIDER_REVIEW_POLICY_UNVERIFIED", state["blocked_gates"])


if __name__ == "__main__":
    unittest.main()
