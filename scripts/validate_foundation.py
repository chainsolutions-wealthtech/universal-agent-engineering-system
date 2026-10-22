#!/usr/bin/env python3
"""Validate UAES documentary contracts without external dependencies."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
REQUIRED=[
"README.md","00_START_HERE.md","docs/PROJECT_CHARTER.md","docs/DECISIONS.md",
"docs/BUILD_PLAN.md","contracts/CONCEPTS.md","state/CURRENT_STATE.json",
"docs/AUTONOMY_CHARTER.md","docs/GITHUB_APP_CAPABILITY_MATRIX.md",
"docs/AUTOMATION_PIPELINE.md","docs/MEMORY_AND_AUDIT_CONTRACT.md",
"docs/AUTONOMY_IMPLEMENTATION_ROADMAP.md"
]
for rel in REQUIRED:
    path=ROOT/rel
    assert path.is_file() and path.stat().st_size>30, f"missing/empty: {rel}"
state=json.loads((ROOT/"state/CURRENT_STATE.json").read_text(encoding="utf-8"))
assert state["project"]=="universal-agent-engineering-system"
assert state["runtime_operational"] is False
for rel in ("docs/AUTONOMY_CHARTER.md","docs/GITHUB_APP_CAPABILITY_MATRIX.md"):
    s=(ROOT/rel).read_text(encoding="utf-8")
    assert "permission" in s.lower(), f"missing permissions rule: {rel}"
print("UAES documentary foundation validated:",len(REQUIRED),"files")
