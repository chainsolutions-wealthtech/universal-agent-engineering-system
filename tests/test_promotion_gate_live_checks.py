"""Non-regression tests for GitHub's actual job-level Checks API names."""
import unittest
from scripts.promotion_gate import assess, REQUIRED_CHECK_JOBS

SHA = "c2936e09152f249bc49e405908e567ff6d4a33e3"
OLD_SHA = "8cd0932b4ef8b2704c582e509753a01717fe7d45"


def live_case():
    return {
        "main_protected": True,
        "independent_approval": True,
        "draft": False,
        "permissions_attested": True,
        "isolated_deployment_ready": True,
        "pr_head_sha": SHA,
        "check_runs": [
            {"id": i, "name": job, "head_sha": SHA, "status": "completed",
             "conclusion": "success", "app": {"slug": "github-actions"}}
            for i, job in enumerate(REQUIRED_CHECK_JOBS.values(), 1)
        ],
    }


class LiveGitHubPromotionGateTests(unittest.TestCase):
    def test_exact_current_sha_job_checks_are_accepted_with_other_gates(self):
        self.assertEqual(assess(live_case()), {"admissible": True, "failures": []})

    def test_stale_green_checks_cannot_authorize_a_new_commit(self):
        case = live_case()
        for run in case["check_runs"]:
            run["head_sha"] = OLD_SHA
        self.assertFalse(assess(case)["admissible"])
        self.assertEqual(sum("CHECK_NOT_SUCCESS:" in x for x in assess(case)["failures"]), 4)

    def test_unknown_actor_is_not_treated_as_github_actions(self):
        case = live_case()
        case["check_runs"][0]["app"] = {"slug": "unknown"}
        self.assertFalse(assess(case)["admissible"])

    def test_new_failed_rerun_supersedes_old_green_check(self):
        case = live_case()
        failed = dict(case["check_runs"][0], id=1000, conclusion="failure")
        case["check_runs"].append(failed)
        self.assertIn("CHECK_NOT_SUCCESS:UAES Core Tests", assess(case)["failures"])

    def test_sha_and_check_records_must_be_present(self):
        case = live_case()
        case["pr_head_sha"] = "main"
        self.assertIn("PR_HEAD_SHA_UNVERIFIED", assess(case)["failures"])
        case = live_case()
        case["check_runs"] = []
        self.assertFalse(assess(case)["admissible"])

    def test_old_successful_checks_cannot_overwrite_failed_live_checks(self):
        case = live_case()
        case["check_runs"][0]["conclusion"] = "failure"
        case["checks"] = {name: "success" for name in REQUIRED_CHECK_JOBS}
        self.assertFalse(assess(case)["admissible"])

    def test_policy_gates_still_apply_to_live_github_checks(self):
        case = live_case()
        case["main_protected"] = False
        self.assertIn("MAIN_UNPROTECTED", assess(case)["failures"])
        case = live_case()
        case["independent_approval"] = False
        self.assertIn("INDEPENDENT_APPROVAL_MISSING", assess(case)["failures"])


if __name__ == "__main__":
    unittest.main()
