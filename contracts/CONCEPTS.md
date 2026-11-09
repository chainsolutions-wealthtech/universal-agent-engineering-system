# Core domain concepts — draft

- **Agent identity:** durable identifier for an admitted actor; does not confer permission.
- **Mandate:** bounded delegation with scope, issuer, lifetime and approvals.
- **Session:** ephemeral execution context bound to an authorized identity.
- **Mission:** durable objective owned by a project and associated with mandates.
- **Task:** actionable unit within a governed dependency DAG.
- **Claim:** temporary exclusive reservation, not an authority grant.
- **Permission:** effective capability evaluated for the specific operation and target.
- **Evidence:** externally verifiable observation or execution receipt.
- **Checkpoint:** durable verified recovery point, never an invented success signal.

Invariants: no duplicate active claim; no write based only on identity; do not treat documentation as runtime permission; fail closed on ambiguity; do not claim work completed without verifying the authoritative target.
