"""Fail-closed UAES promotion gate. Never grants permissions or merges PRs."""
import argparse,json,sys

REQUIRED_CHECKS={"UAES Core Tests","Documentation validation","UAES Continuity Dispatch","UAES Container Smoke"}

def assess(snapshot):
    failures=[]
    if not snapshot.get("main_protected"):failures.append("MAIN_UNPROTECTED")
    if not snapshot.get("independent_approval"):failures.append("INDEPENDENT_APPROVAL_MISSING")
    if snapshot.get("draft",True):failures.append("PR_STILL_DRAFT")
    if not snapshot.get("permissions_attested"):failures.append("INSTALLATION_PERMISSIONS_UNATTESTED")
    if not snapshot.get("isolated_deployment_ready"):failures.append("ISOLATED_RUNTIME_UNVERIFIED")
    checks=snapshot.get("checks",{})
    for check in sorted(REQUIRED_CHECKS):
        if checks.get(check)!="success":failures.append("CHECK_NOT_SUCCESS:"+check)
    return {"admissible":not failures,"failures":failures}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("snapshot",help="JSON attestations gathered from authenticated GitHub and host APIs")
    a=p.parse_args()
    with open(a.snapshot,encoding="utf-8") as file:snapshot=json.load(file)
    report=assess(snapshot)
    print(json.dumps(report,sort_keys=True))
    return 0 if report["admissible"] else 1

if __name__=="__main__":sys.exit(main())
