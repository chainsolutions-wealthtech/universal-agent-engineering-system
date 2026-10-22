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
