# Effect coordination milestone — prototype

Implemented a local coordinator tying an effect intent to the task, claiming agent, effective mandate and fencing token. All effects for a task must be confirmed before the coordinator's completion-readiness check can pass. Unknown or in-flight effects remain blocked and require remote readback. Tests cover claim validity, revoked mandates, key reuse and uncertain result state.

**Not a production authority or an external executor.** Readiness is a check only: the existing core completion method does not yet enforce this gate atomically. Effect prepare and binding are currently in separate SQLite transactions; implement atomic binding and authenticated remote receipts before enabling actual GitHub writes. Never infer success from unverified caller-provided receipts.

Next: unify task completion and verified effect binding in one guarded transaction; implement a persistent inbox/outbox and safe bounded recovery loop with synthetic targets. Protect main and obtain an independent review before merging the bootstrap PR.
