# Container deployment readiness gate

> **Historical checkpoint.** Reviewer-related requirements in this original snapshot are superseded for UAES by D007 (2026-11-06): automated current-head security/regression checks, **no mandatory human PR approval**, and no bypass of actual external GitHub rules. Historical observations below remain unchanged.

CI now builds the Docker image and starts a **bounded local-only worker** with an explicitly seeded synthetic agent, mandate and task on a persistent mounted SQLite database. It verifies one task completion, restarts the image and proves no duplicate completion. Network access is disabled during the container smoke test, so no GitHub mutations occur.

This validates image startup and a local restart scenario only. It does NOT attest production security, externally hosted uptime, user permissions, signed provider receipts, backups, deployment, or independent PR approval.

## Next gating tasks
1. Ensure the new container CI succeeds on the current PR head.
2. Verify/enforce the required main branch ruleset and independent review.
3. Validate secure runtime secrets and effective GitHub App permissions.
4. Deploy to an isolated explicitly authorized host, test backups and rollback, collect provider-native evidence.
5. Enable scoped external operations only after verified attestation and production review.
