# Program for end-to-end autonomous delivery

All milestones are **PLANNED** unless separately verified by runtime receipts.

| Milestone | Required outcome | Blocking gate |
|---|---|---|
| A00 | Canonical requirements and permissions inventory | Official GitHub permission evidence |
| A01 | Policy and identity domain models | Security/authority invariants reviewed |
| A02 | Hosted service, encrypted secret broker, persistent DB | Infrastructure and access configured |
| A03 | GitHub App auth and permission probes | Actual installation-scoped rights attested |
| A04 | Repository provisioning and protected initialization | Create/readback and no-duplicate tests |
| A05 | Project memory/event ledger and replay | Replay + tamper tests |
| A06 | Agent registration, mandates, task DAG, claims | Concurrency and revoke tests |
| A07 | Bus, retries, dead letters, resume | Crash/unknown outcome tests |
| A08 | Provider and skill adapters | Provider switch continuity test |
| A09 | Autonomous code-to-PR loop | Sandbox, CI, independent review |
| A10 | Controlled merge, release, deploy and rollback | Enforced branch/environment gates |
| A11 | Monitoring, recovery and operator cockpit | Incident and disaster drills |
| A12 | Security review and full autonomous pilot | External sign-off where mandatory |

## Automated-operation target
The default route is unattended execution **within pre-approved mandates and policy bounds**. Escalate only when external consent or exceptional risk requires it; never falsify approval or substitute a chat statement for external entitlements.
