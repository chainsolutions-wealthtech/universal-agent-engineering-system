# Read-only reconciliation service — checkpoint

> **Historical checkpoint.** Reviewer-related requirements in this original snapshot are superseded for UAES by D007 (2026-11-06): automated current-head security/regression checks, **no mandatory human PR approval**, and no bypass of actual external GitHub rules. Historical observations below remain unchanged.

A bounded reconciliation pass enumerates IN_FLIGHT/UNKNOWN effects from durable SQLite state, invokes a supplied readback adapter, and retains UNKNOWN on missing, invalid or failed observations. A terminal observation is recorded with source/proof fields and is not replayed on restart.

The included adapter is **synthetic and unauthenticated**. Neither typed data nor source/proof strings prove authenticity. No live GitHub readback, live GitHub mutation, credential broker or external authorization was enabled. Production integration must verify the adapter's identity, authenticated readback, immutable provider evidence and claim/mandate binding before transition to CONFIRMED.

Do not merge before independent review, enforced protection of main and current-head CI.
