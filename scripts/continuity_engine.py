#!/usr/bin/env python3
"""Read-only, deterministic orchestration: choose one next admissible UAES action.
No GitHub credentials or write permissions required. Emits auditable JSON.
"""
import json, os
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
def main():
    state=json.loads((ROOT/"state/CURRENT_STATE.json").read_text())
    evidence_file=os.environ.get("UAES_EVIDENCE_FILE")
    evidence=json.loads(Path(evidence_file).read_text()) if evidence_file else {}
    gates=[
        ("P0_MAIN_PROTECTION",bool(evidence.get("main_protected",False)),"Observe GitHub ruleset/branch protection on main; administrative action requires separately verified rights."),
        ("P0_INDEPENDENT_REVIEW",bool(evidence.get("independent_review_approved",False)),"Request independent review of PR #1; never self-approve."),
        ("P0_CI",bool(evidence.get("ci_success_current_head",False)),"Verify required CI on current PR head SHA."),
        ("P1_PERMISSION_AUDIT",bool(evidence.get("permissions_attested",False)),"Inventory effective GitHub App permissions and installation."),
        ("P1_RUNTIME",bool(evidence.get("runtime_verified",False)),"Build and validate persistent authorized workers and audit storage.")
    ]
    outstanding=next(((name,description) for name,passed,description in gates if not passed),None)
    result={
      "project":state["project"],"status":"BLOCKED_ON_EVIDENCE" if outstanding else "GATES_ATTESTED",
      "next_action":outstanding[0] if outstanding else "PROCEED_WITH_AUTHORIZED_IMPLEMENTATION",
      "reason":outstanding[1] if outstanding else "All supplied gate proofs indicate pass; live provider readback still required.",
      "gates":{name:passed for name,passed,_ in gates},
      "note":"This is a candidate computed from supplied evidence, not a runtime approval or a GitHub mutation."
    }
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__":main()
