# Worker MVP checkpoint

## Implemented on bootstrap branch
A bounded, synchronous worker runs allowlisted, deterministic, **local-only** actions (analyze/validate) against SQLite-backed tasks. It requires an agent and scoped mandate, obtains transactional claim fencing, writes completion + audit event, and supports read-only resume after process reopening. CI exercises an interrupted/reopened state and asserts no duplicate completion.

## Not implemented
No long-running worker daemon, network APIs, external GitHub effects, queue transport, secret vault, independent process scheduler, hosted deployment, encryption-at-rest, deadline-aware cancellation, production authorization, external evidence attestation or recovery for unknown side effects.

## Following gates
Main branch protection and independent review; a separate permission-audited GitHub App broker; durable workers with secure leases and crash recovery; full integration tests using sandbox repositories before any autonomous external write.
