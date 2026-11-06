#!/usr/bin/env python3
"""GitHub-native UAES main ruleset: apply only with an authenticated admin token.

Default execution is offline plan inspection. --apply is idempotent and requires a
scoped token with repository Administration:write. Never prints token material.
Does not merge pull requests, mark PRs ready, or bypass organization policies.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

REPOSITORY = "chainsolutions-wealthtech/universal-agent-engineering-system"
RULESET_NAME = "UAES main governed automation D007"
REQUIRED_JOBS = (
    "core-tests",
    "documentary-contracts",
    "container-smoke",
    "automated-review",
    "determine-next",
)
GITHUB_ACTIONS_APP_ID = 15368  # Observed in GitHub Checks API on 2026-11-06.
API_ROOT = "https://api.github.com"
API_VERSION = "2026-03-10"


class RulesetGateError(RuntimeError):
    """A provider-authenticated prerequisite is missing or ambiguous."""


def proposed_ruleset():
    """Declarative provider-enforced policy, not a local substitute for GitHub."""
    return {
        "name": RULESET_NAME,
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {"type": "pull_request", "parameters": {
                "dismiss_stale_reviews_on_push": True,
                "require_code_owner_review": False,
                "require_last_push_approval": False,
                "required_approving_review_count": 0,
                "required_review_thread_resolution": True,
                "allowed_merge_methods": ["merge", "squash", "rebase"],
                "required_reviewers": [],
            }},
            {"type": "required_status_checks", "parameters": {
                "strict_required_status_checks_policy": True,
                "required_status_checks": [
                    {"context": name, "integration_id": GITHUB_ACTIONS_APP_ID}
                    for name in REQUIRED_JOBS
                ],
            }},
        ],
    }


def validate_current_head_checks(pull, check_runs):
    """Prevent a stale green run or an unrelated app from admitting bootstrap."""
    if not isinstance(pull, dict) or pull.get("state") != "open":
        raise RulesetGateError("PR_1_NOT_OPEN")
    if pull.get("base", {}).get("ref") != "main":
        raise RulesetGateError("PR_1_BASE_CHANGED")
    sha = (pull.get("head") or {}).get("sha")
    if not isinstance(sha, str) or len(sha) != 40:
        raise RulesetGateError("PR_1_HEAD_UNVERIFIED")
    if not isinstance(check_runs, list):
        raise RulesetGateError("CHECK_RUNS_NOT_OBSERVED")
    for name in REQUIRED_JOBS:
        candidates = [
            record for record in check_runs
            if isinstance(record, dict)
            and record.get("name") == name
            and record.get("head_sha") == sha
            and (record.get("app") or {}).get("id") == GITHUB_ACTIONS_APP_ID
            and isinstance(record.get("id"), int)
        ]
        if not candidates:
            raise RulesetGateError("CURRENT_HEAD_CHECK_MISSING:" + name)
        latest = max(candidates, key=lambda r: r["id"])
        if latest.get("status") != "completed" or latest.get("conclusion") != "success":
            raise RulesetGateError("CURRENT_HEAD_CHECK_NOT_GREEN:" + name)
    return sha


def verify_effective_rules(branch, effective, ruleset_id):
    """Require actual GitHub-applied rules, including checks and zero reviewers."""
    if not isinstance(branch, dict) or branch.get("protected") is not True:
        raise RulesetGateError("MAIN_UNPROTECTED")
    if not isinstance(effective, list) or not effective:
        raise RulesetGateError("MAIN_APPLIED_RULES_MISSING")
    own = [rule for rule in effective if rule.get("ruleset_id") == ruleset_id]
    by_type = {rule.get("type"): rule for rule in own}
    if not {"deletion", "non_fast_forward", "pull_request", "required_status_checks"}.issubset(by_type):
        raise RulesetGateError("UAES_RULESET_NOT_ENFORCED")
    for rule in effective:
        if rule.get("type") != "pull_request":
            continue
        params = rule.get("parameters") or {}
        count = params.get("required_approving_review_count")
        if type(count) is not int or count != 0:
            raise RulesetGateError("EXTERNALLY_REQUIRED_APPROVAL_OR_UNVERIFIED_POLICY")
        if params.get("require_code_owner_review") or params.get("require_last_push_approval"):
            raise RulesetGateError("EXTERNALLY_REQUIRED_HUMAN_REVIEW")
        if any((x.get("minimum_approvals") or 0) > 0 for x in params.get("required_reviewers", [])):
            raise RulesetGateError("EXTERNALLY_REQUIRED_TEAM_REVIEW")
    status_params = by_type["required_status_checks"].get("parameters") or {}
    if status_params.get("strict_required_status_checks_policy") is not True:
        raise RulesetGateError("CURRENT_BASE_SHA_CHECK_POLICY_MISSING")
    observed = {item.get("context"): item.get("integration_id")
                for item in status_params.get("required_status_checks", [])}
    if any(observed.get(name) != GITHUB_ACTIONS_APP_ID for name in REQUIRED_JOBS):
        raise RulesetGateError("REQUIRED_GITHUB_ACTIONS_CHECKS_NOT_ENFORCED")
    return True


class GitHubAdminClient:
    def __init__(self, token, http_open=None):
        if not token:
            raise RulesetGateError("ADMINISTRATION_TOKEN_NOT_AVAILABLE")
        self.token = token
        self.open = http_open or urllib.request.urlopen

    def request(self, method, path, data=None):
        payload = None if data is None else json.dumps(data).encode("utf-8")
        request = urllib.request.Request(
            API_ROOT + path, data=payload, method=method,
            headers={
                "Authorization": "Bearer " + self.token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": API_VERSION,
                "Content-Type": "application/json",
            },
        )
        try:
            with self.open(request, timeout=20) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            # Never print token, raw request, body or proprietary response.
            raise RulesetGateError("GITHUB_HTTP_%s_%s" % (exc.code, method)) from None
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            raise RulesetGateError("GITHUB_PROVIDER_UNVERIFIED_%s" % type(exc).__name__) from None


def ensure_ruleset(client):
    base = "/repos/" + REPOSITORY
    branch = client.request("GET", base + "/branches/main")
    if not isinstance(branch, dict) or not branch.get("commit", {}).get("sha"):
        raise RulesetGateError("MAIN_HEAD_UNVERIFIED")
    pull = client.request("GET", base + "/pulls/1")
    head = (pull.get("head") or {}).get("sha")
    checks = client.request("GET", base + "/commits/" + str(head) + "/check-runs?per_page=100")
    sha = validate_current_head_checks(pull, (checks or {}).get("check_runs"))

    existing = client.request("GET", base + "/rulesets?includes_parents=true&per_page=100")
    if not isinstance(existing, list):
        raise RulesetGateError("EXISTING_RULESETS_UNVERIFIED")
    named = [r for r in existing if r.get("name") == RULESET_NAME]
    if len(named) > 1:
        raise RulesetGateError("DUPLICATE_NAMED_RULESETS")
    effective_before = client.request("GET", base + "/rules/branches/main?per_page=100")
    if not isinstance(effective_before, list):
        raise RulesetGateError("CURRENT_APPLIED_RULES_UNVERIFIED")
    for rule in effective_before:
        if rule.get("type") == "pull_request":
            params = rule.get("parameters") or {}
            if type(params.get("required_approving_review_count")) is not int:
                raise RulesetGateError("EXISTING_REVIEW_POLICY_UNKNOWN")
            if params["required_approving_review_count"] > 0 or params.get("require_code_owner_review") or params.get("require_last_push_approval"):
                raise RulesetGateError("EXISTING_HUMAN_REVIEW_POLICY_CONFLICT")
    if named:
        item = named[0]
        if item.get("source_type") not in ("Repository", None):
            raise RulesetGateError("UNMANAGED_INHERITED_RULESET_CONFLICT")
        ruleset_id = item["id"]
        current = client.request("GET", base + "/rulesets/" + str(ruleset_id))
        desired = proposed_ruleset()
        for field in ("name", "target", "enforcement", "conditions", "bypass_actors", "rules"):
            if current.get(field) != desired[field]:
                raise RulesetGateError("NAMED_RULESET_DIFFERS_MANUAL_RECONCILIATION_REQUIRED:" + field)
        operation = "ALREADY_PRESENT"
    else:
        created = client.request("POST", base + "/rulesets", proposed_ruleset())
        ruleset_id = created.get("id") if isinstance(created, dict) else None
        if not isinstance(ruleset_id, int):
            raise RulesetGateError("RULESET_CREATE_UNVERIFIED")
        operation = "CREATED"

    # Re-read live GitHub authority; successful HTTP POST does not equal enforcement.
    verified_branch = client.request("GET", base + "/branches/main")
    effective = client.request("GET", base + "/rules/branches/main?per_page=100")
    verify_effective_rules(verified_branch, effective, ruleset_id)
    return {"status": "VERIFIED_ENFORCED", "operation": operation,
            "repository": REPOSITORY, "ruleset_id": ruleset_id,
            "pr_head_sha_at_preflight": sha, "required_checks": list(REQUIRED_JOBS),
            "required_human_approvals": 0, "branch": "main"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Admin-only: create and verify active ruleset")
    args = parser.parse_args(argv)
    if not args.apply:
        print(json.dumps({"status": "DRY_RUN_ONLY", "ruleset": proposed_ruleset()}, indent=2, sort_keys=True))
        return 0
    try:
        token = os.getenv("UAES_ADMIN_GITHUB_TOKEN", "")
        result = ensure_ruleset(GitHubAdminClient(token))
    except RulesetGateError as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
