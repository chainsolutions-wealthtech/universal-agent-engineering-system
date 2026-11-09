# Expired-lease recovery checkpoint

## Implemented
The SQLite task engine allows a new authorized agent to reclaim a task only when the prior lease has expired. Every claim increments a fencing token; an old worker cannot finalize a task after a new worker has reclaimed it. Added `renew` with atomic lease extension, scope/mandate validity verification and an audit event. Tests cover stale-worker rejection, one completion receipt and revoked-mandate renewal refusal.

## Limits and next action
This is a local SQLite prototype, not a continuously running distributed scheduler. Reclamation does not verify whether an old worker caused an external side effect; future external actions must use durable idempotency keys and reconciliation receipts before replay. **Never replay an unknown remote write merely because its lease expired.**

Next: implement an effect journal/outbox and crash-reconciliation semantics, then integrate with a sandbox worker and independently verify behavior. Maintain PR #1 as draft until `main` protection and independent review are verified.
