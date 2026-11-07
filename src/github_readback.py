"""Read-only GitHub provider observation; never dispatches a mutation.

Supports immutable commit-by-SHA verification only. Caller supplies a scoped installation
token at runtime through a secure broker. A 404 or failed authentication is UNKNOWN:
absence does not prove a timed-out remote mutation never happened.
"""
import json
import re
import urllib.error
import urllib.request

from src.receipt_verifier import VerifiedObservation

_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


class GitHubCommitReadback:
    def __init__(self, token_provider, http_open=None):
        self._token_provider = token_provider
        self._open = http_open or urllib.request.urlopen

    def readback(self, target, operation, key):
        if operation != "commit_exists" or not _REPO.fullmatch(target) or not _SHA.fullmatch(key):
            raise PermissionError("unsupported GitHub readback contract")
        token = self._token_provider()
        if not token or not isinstance(token, str):
            raise PermissionError("installation token unavailable")
        url = "https://api.github.com/repos/" + target + "/commits/" + key
        request = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }, method="GET")
        try:
            with self._open(request, timeout=15) as response:
                payload = json.load(response)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
            return None
        if not isinstance(payload, dict) or payload.get("sha", "").lower() != key.lower():
            return None
        # Reference is bound to the provider response and verified commit identity.
        return VerifiedObservation(
            source="github-rest-commit",
            target=target,
            operation=operation,
            idempotency_key=key,
            outcome="CONFIRMED",
            immutable_reference=target + "@" + payload["sha"].lower(),
        )


# U04: provider-observation classifier. This is a read-only projection over
# already fetched responses; it never claims a task, creates a backlog or
# grants a GitHub permission. Missing evidence is UNKNOWN, not an empty repo.
def classify_repository_snapshot(repository, branch, pull, check_runs, rulesets):
    """Classify supplied GitHub API responses without deriving execution rights.

    The caller is responsible for obtaining these values from the provider
    under its own read-only credential. No credential, network, or scheduler
    is introduced by this projection.
    """
    if not isinstance(repository, dict) or not isinstance(branch, dict):
        return {"status": "UNKNOWN", "reason": "REPOSITORY_OR_BRANCH_UNVERIFIED"}
    name = repository.get("full_name")
    if not isinstance(name, str) or not _REPO.fullmatch(name):
        return {"status": "UNKNOWN", "reason": "REPOSITORY_IDENTITY_UNVERIFIED"}
    branch_sha = (branch.get("commit") or {}).get("sha")
    if not isinstance(branch_sha, str) or not _SHA.fullmatch(branch_sha):
        return {"status": "UNKNOWN", "reason": "BRANCH_SHA_UNVERIFIED", "repository": name}
    if type(branch.get("protected")) is not bool:
        return {"status": "UNKNOWN", "reason": "BRANCH_PROTECTION_UNVERIFIED", "repository": name}
    if not isinstance(rulesets, list):
        return {"status": "UNKNOWN", "reason": "RULESETS_UNVERIFIED", "repository": name}
    if pull is None:
        return {"status": "OBSERVED", "repository": name,
                "main_sha": branch_sha.lower(), "main_protected": branch["protected"],
                "ruleset_count": len(rulesets), "pull": "NOT_REQUESTED"}
    if not isinstance(pull, dict):
        return {"status": "UNKNOWN", "reason": "PR_UNVERIFIED", "repository": name}
    head_sha = (pull.get("head") or {}).get("sha")
    if not isinstance(head_sha, str) or not _SHA.fullmatch(head_sha):
        return {"status": "UNKNOWN", "reason": "PR_HEAD_SHA_UNVERIFIED", "repository": name}
    if not isinstance(check_runs, list):
        return {"status": "UNKNOWN", "reason": "PR_CHECKS_UNVERIFIED",
                "repository": name, "head_sha": head_sha.lower()}
    checks = {}
    for run in check_runs:
        if not isinstance(run, dict) or not isinstance(run.get("head_sha"), str) or run["head_sha"].lower() != head_sha.lower():
            continue
        name_check = run.get("name")
        run_id = run.get("id")
        if not isinstance(name_check, str) or type(run_id) is not int:
            continue
        previous = checks.get(name_check)
        if previous is None or run_id > previous["id"]:
            checks[name_check] = {
                "id": run_id, "status": run.get("status"),
                "conclusion": run.get("conclusion"),
            }
    return {
        "status": "OBSERVED", "repository": name, "main_sha": branch_sha.lower(),
        "main_protected": branch["protected"], "ruleset_count": len(rulesets),
        "pull": {"head_sha": head_sha.lower(), "state": pull.get("state"),
                 "draft": pull.get("draft")},
        "check_runs_latest": checks,
        "authorization": "NOT_DERIVED_FROM_READBACK",
        "runtime": "NOT_ATTESTED_BY_READBACK",
    }
