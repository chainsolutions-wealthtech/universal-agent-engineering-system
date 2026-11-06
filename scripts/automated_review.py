#!/usr/bin/env python3
"""Automated review: deterministic, read-only security invariants.

This is an automated CI static-policy check, not a human or independent
approval. It cannot grant repository permissions, prove production safety,
or replace external provider-enforced requirements.
"""
import json
import re
import sys
from pathlib import Path

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
)
_PROTECTED_EXTENSIONS = (".py", ".yml", ".yaml", ".json", ".toml", ".sh")


def review_repository(root):
    """Produce reproducible findings without reading secrets outside source tree."""
    root = Path(root)
    findings = []
    workflows = root / ".github" / "workflows"
    if not workflows.is_dir():
        findings.append("WORKFLOWS_NOT_FOUND")
    else:
        for path in sorted((*workflows.glob("*.yml"), *workflows.glob("*.yaml"))):
            body = path.read_text(encoding="utf-8")
            if re.search(r"^\s*pull_request_target\s*:", body, re.MULTILINE):
                findings.append("UNTRUSTED_PRIVILEGED_TRIGGER:" + path.name)
            if not re.search(r"^permissions\s*:", body, re.MULTILINE):
                findings.append("EXPLICIT_WORKFLOW_PERMISSIONS_MISSING:" + path.name)
    paths = [*root.glob("src/**/*.py"), *root.glob("scripts/**/*.py"),
             *root.glob(".github/workflows/*.yml"),
             *root.glob(".github/workflows/*.yaml"),
             *root.glob("state/*.json")]
    for path in sorted(set(paths)):
        if not path.is_file() or path.suffix not in _PROTECTED_EXTENSIONS:
            continue
        body = path.read_text(encoding="utf-8")
        if any(pattern.search(body) for pattern in _SECRET_PATTERNS):
            findings.append("CREDENTIAL_PATTERN_DETECTED:" + str(path.relative_to(root)))
    return findings


def main():
    root = Path(__file__).resolve().parents[1]
    findings = review_repository(root)
    print(json.dumps({
        "gate": "automated-review",
        "mode": "static-policy-check",
        "status": "FAIL" if findings else "PASS",
        "findings": findings,
        "claim": "no independent human approval; CI-only static checks",
    }, sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
