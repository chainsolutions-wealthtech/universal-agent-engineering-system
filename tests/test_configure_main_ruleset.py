"""Offline tests for provider-enforced UAES main ruleset, no API or token needed."""
import unittest
from scripts.configure_main_ruleset import (
    GITHUB_ACTIONS_APP_ID, REQUIRED_JOBS, RulesetGateError,
    proposed_ruleset, validate_current_head_checks, verify_effective_rules, verify_effective_bypass,
)

SHA = "a" * 40
ACTORS = [
    {"actor_type": "User", "actor_id": 94637590, "bypass_mode": "always"},
    {"actor_type": "User", "actor_id": 270385782, "bypass_mode": "always"},
    {"actor_type": "Integration", "actor_id": 1234567, "bypass_mode": "always"},
]


def valid_pull():
    return {"state": "open", "base": {"ref": "main"}, "head": {"sha": SHA}}


def valid_checks():
    return [
        {"id": n + 1, "name": name, "head_sha": SHA, "status": "completed",
         "conclusion": "success", "app": {"id": GITHUB_ACTIONS_APP_ID}}
        for n, name in enumerate(REQUIRED_JOBS)
    ]


def applied_rules():
    return [{"ruleset_id": 9, **item} for item in proposed_ruleset(ACTORS)["rules"]]


class RulesetTests(unittest.TestCase):
    def test_main_ruleset_preserves_three_bypass_actors_and_automated_checks(self):
        config = proposed_ruleset(ACTORS)
        self.assertEqual(config["enforcement"], "active")
        self.assertEqual(config["conditions"]["ref_name"]["include"], ["refs/heads/main"])
        self.assertEqual(config["bypass_actors"], ACTORS)
        checks = next(r for r in config["rules"] if r["type"] == "required_status_checks")
        self.assertEqual([x["context"] for x in checks["parameters"]["required_status_checks"]], list(REQUIRED_JOBS))
        self.assertTrue(checks["parameters"]["strict_required_status_checks_policy"])
        reviews = next(r for r in config["rules"] if r["type"] == "pull_request")
        self.assertEqual(reviews["parameters"]["required_approving_review_count"], 0)
        self.assertFalse(reviews["parameters"]["require_code_owner_review"])

    def test_provider_must_attest_exact_bypass_actor_count_and_identity(self):
        details = {"enforcement": "active", "bypass_actors": [dict(x) for x in ACTORS]}
        self.assertTrue(verify_effective_bypass(details, ACTORS))
        details["bypass_actors"].pop()
        with self.assertRaisesRegex(RulesetGateError, "EXACT_THREE_ACCOUNT_BYPASS"):
            verify_effective_bypass(details, ACTORS)
        details = {"enforcement": "active", "bypass_actors": [dict(x) for x in ACTORS]}
        details["bypass_actors"][0]["bypass_mode"] = "pull_request"
        with self.assertRaisesRegex(RulesetGateError, "EXACT_THREE_ACCOUNT_BYPASS"):
            verify_effective_bypass(details, ACTORS)

    def test_current_exact_pr_head_is_required(self):
        self.assertEqual(validate_current_head_checks(valid_pull(), valid_checks()), SHA)
        stale = valid_checks()
        stale[0]["head_sha"] = "b" * 40
        with self.assertRaisesRegex(RulesetGateError, "CURRENT_HEAD_CHECK_MISSING"):
            validate_current_head_checks(valid_pull(), stale)

    def test_failed_latest_rerun_overrides_old_success(self):
        checks = valid_checks()
        checks.append({**checks[0], "id": 1000, "conclusion": "failure"})
        with self.assertRaisesRegex(RulesetGateError, "CURRENT_HEAD_CHECK_NOT_GREEN"):
            validate_current_head_checks(valid_pull(), checks)

    def test_untrusted_ci_source_cannot_pass(self):
        checks = valid_checks()
        checks[0]["app"] = {"id": -1}
        with self.assertRaisesRegex(RulesetGateError, "CURRENT_HEAD_CHECK_MISSING"):
            validate_current_head_checks(valid_pull(), checks)

    def test_effective_enforcement_requires_provider_rules(self):
        self.assertTrue(verify_effective_rules({"protected": True}, applied_rules(), 9))
        with self.assertRaisesRegex(RulesetGateError, "MAIN_UNPROTECTED"):
            verify_effective_rules({"protected": False}, applied_rules(), 9)
        with self.assertRaisesRegex(RulesetGateError, "UAES_RULESET_NOT_ENFORCED"):
            verify_effective_rules({"protected": True}, applied_rules()[:2], 9)

    def test_external_approval_requirement_is_not_bypassed(self):
        rules = applied_rules()
        rules.append({"type": "pull_request", "ruleset_id": 7,
                      "parameters": {"required_approving_review_count": 1}})
        with self.assertRaisesRegex(RulesetGateError, "EXTERNALLY_REQUIRED_APPROVAL"):
            verify_effective_rules({"protected": True}, rules, 9)

    def test_missing_check_context_or_app_cannot_certify_ruleset(self):
        rules = applied_rules()
        x = next(r for r in rules if r["type"] == "required_status_checks")
        x["parameters"]["required_status_checks"] = [{"context": "core-tests", "integration_id": 99}]
        with self.assertRaisesRegex(RulesetGateError, "REQUIRED_GITHUB_ACTIONS_CHECKS"):
            verify_effective_rules({"protected": True}, rules, 9)


if __name__ == "__main__":
    unittest.main()
