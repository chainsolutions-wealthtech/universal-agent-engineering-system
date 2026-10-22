# Durable effects and unknown-outcome recovery — prototype

An effect transitions PREPARED -> IN_FLIGHT -> (UNKNOWN) -> CONFIRMED / REJECTED. The intent is written to SQLite before any external action. IN_FLIGHT and UNKNOWN are never replayed blindly; recovery returns a read-only reconciliation requirement. Every effect has a unique, scoped idempotency key.

## Safety and limits
The code records **caller-provided** receipts and does not yet cryptographically authenticate a remote provider, perform its readback, or authorize a remote action. A receipt with source/proof fields is not itself trustworthy: the external reconciler must verify its provenance before invoking resolve. Do not use this prototype to authorize production writes.

## Next milestones
- Bind effects to the authorized mandate, task fencing and signed target observation.
- Implement target-specific readback with verified identity and evidence.
- Ensure task completion atomically references confirmed effects.
- Persist inbox/outbox and recovery policy; test crash points, duplicate callbacks and concurrency.
- Promote only with independent review, main protection, and runtime-permission attestation.
