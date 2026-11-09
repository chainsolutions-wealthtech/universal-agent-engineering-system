# UAES continuity correlation — additive U05/U06/U09 slice

Documentary root: `UAES-CONV-CONT-20261107-ROOT-01`
Source: https://github.com/chainsolutions-wealthtech/universal-agent-engineering-system/issues/6

## Ownership and non-regression
The existing `src/uaes_core.py` SQLite `agents`, `mandates`, `tasks` and `events` remain the **only** local task/identity/event authorities. `src/continuity_link.py` subclasses `Engine` and adds a correlation index (`continuity_roots`, `continuity_links`) and checkpoint snapshots (`continuity_checkpoints`) in **the same database**. No new task queue, agent identity, authorization or effect executor is created.

The root is documentary and must not authorize any task. The default ID points to issue #6; another ID must be registered with a stable source. Local objects can be linked by exact ID; missing local records are rejected. Legacy rows are not silently claimed as part of this conversation.

## Integration
Use `ContinuityEngine(db_path)` in place of `Engine(db_path)` only for authorized new work associated with this root. Calls to `agent`, `mandate`, `submit` and `event` add persistent correlations while preserving existing method semantics. Existing `claim`, `renew` and `complete` operate on the original tasks and emit correlated original events. `checkpoint()` records a durable snapshot with the original task-state projection and the latest event sequence. `resume()` reads the latest checkpoint and **current** linked task/effect states, returning a mandatory reconciliation action rather than claiming work or replaying external effects.

For existing tasks/agents/mandates/effects, use `bind_existing(kind, id)` after checking their provenance. An effect can only be bound if the existing effect-journal table and record are present. External decision/artifact IDs must include a stable, traceable source reference.

## Boundaries
- Checkpoint is a local SQLite snapshot, **not** an independently attested remote runtime checkpoint.
- The journal of effects, trusted readback, fencing and idempotency remain in their existing modules.
- No full private conversation transcript is stored in this public repository.
- No automatic GitHub writes, remote deployments, agent admission, provider credential validation or merge are authorized by this slice.
- Existing runtime wiring still requires an additive integration step and verified provider receipts before claiming U06/U09 acceptance.
- Baseline is PR #1 branch; proposed PR must target `bootstrap/independent-foundation`, **not** unprotected `main`.

## Verification
`python -m unittest tests.test_continuity_link`
`python -m unittest discover -s tests`

Acceptance requires passing tests at the exact proposed HEAD and independently verified runtime receipts for the eventual production rollout. U00/U01 remain blocked by existing GitHub policy requirements.
