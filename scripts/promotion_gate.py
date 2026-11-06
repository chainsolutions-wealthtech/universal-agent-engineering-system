"""Fail-closed UAES promotion gate. Never grants permissions or merges PRs.

Legacy named check snapshots remain supported for compatibility. The optional
``check_runs`` input accepts GitHub Checks API job records and binds each
required check to the exact PR head SHA. A supplied snapshot is not, by itself,
proof of authenticated origin: the caller must fetch it from the trusted API.
"""
import argparse
import json
import re
import sys

REQUIRED_CHECKS = {
    "UAES Core Tests",
    "Documentation validation",
    "UAES Continuity Dispatch",
    "UAES Container Smoke",
    "UAES Automated Review",
}

# GitHub Checks API exposes job names, not their parent workflow titles.
REQUIRED_CHECK_JOBS = {
    "UAES Core Tests": "core-tests",
    "Documentation validation": "documentary-contracts",
    "UAES Continuity Dispatch": "determine-next",
    "UAES Container Smoke": "container-smoke",
    "UAES Automated Review": "automated-review",
}
_SHA = re.compile(r"^[a-fA-F0-9]{40}$")


def _validate_github_check_runs(snapshot, failures):
    head = snapshot.get("pr_head_sha")
    if not isinstance(head, str) or not _SHA.fullmatch(head):
        failures.append("PR_HEAD_SHA_UNVERIFIED")
        return
    records = snapshot.get("check_runs")
    if not isinstance(records, list):
        failures.append("CHECK_RUNS_UNAVAILABLE")
        return
    for workflow_title, job_name in sorted(REQUIRED_CHECK_JOBS.items()):
        matching = [
            rec for rec in records
            if isinstance(rec, dict)
            and rec.get("name") == job_name
            and rec.get("head_sha", "").lower() == head.lower()
            and isinstance(rec.get("id"), int)
            and isinstance(rec.get("app"), dict)
            and rec["app"].get("slug") == "github-actions"
        ]
        if not matching:
            failures.append("CHECK_NOT_SUCCESS:" + workflow_title)
            continue
        # An older successful run cannot override a newer failed rerun.
        latest = max(matching, key=lambda rec: rec["id"])
        if latest.get("status") != "completed" or latest.get("conclusion") != "success":
            failures.append("CHECK_NOT_SUCCESS:" + workflow_title)


def assess(snapshot):
    failures = []
    if not snapshot.get("main_protected"):
        failures.append("MAIN_UNPROTECTED")
    # Owner policy: no mandatory human/independent PR review. The effective
    # provider-side policy must be observed; never override an existing rule.
    approvals = snapshot.get("required_approving_reviews")
    if not isinstance(approvals, int) or isinstance(approvals, bool) or approvals < 0:
        failures.append("REVIEW_POLICY_UNVERIFIED")
    elif approvals > 0:
        failures.append("PROVIDER_REVIEW_REQUIRED")
    if snapshot.get("draft", True):
        failures.append("PR_STILL_DRAFT")
    # The bootstrap PR introduces only inert, local-only prototypes. It
    # must be integrated before an isolated hosted runtime can be deployed.
    # Never apply this exemption to external GitHub writes or deployment.
    stage = snapshot.get("promotion_stage", "production")
    if stage not in ("bootstrap", "production"):
        failures.append("PROMOTION_STAGE_UNVERIFIED")
    if stage != "bootstrap":
        if not snapshot.get("permissions_attested"):
            failures.append("INSTALLATION_PERMISSIONS_UNATTESTED")
        if not snapshot.get("isolated_deployment_ready"):
            failures.append("ISOLATED_RUNTIME_UNVERIFIED")

    # Prefer immutable-SHA-bound live checks when supplied. Legacy snapshots
    # are retained for existing callers and synthetic tests only.
    if "check_runs" in snapshot:
        _validate_github_check_runs(snapshot, failures)
    else:
        checks = snapshot.get("checks", {})
        for check in sorted(REQUIRED_CHECKS):
            if checks.get(check) != "success":
                failures.append("CHECK_NOT_SUCCESS:" + check)
    return {"admissible": not failures, "failures": failures}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", help="JSON attestations gathered from authenticated GitHub and host APIs")
    args = parser.parse_args()
    with open(args.snapshot, encoding="utf-8") as file:
        snapshot = json.load(file)
    report = assess(snapshot)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["admissible"] else 1


if __name__ == "__main__":
    sys.exit(main())
