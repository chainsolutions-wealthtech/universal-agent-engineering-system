# Worker service and readback gate

The first bounded worker loop handles pre-authorized synthetic/local actions with a persistent SQLite database and a configurable poll count. The readback verifier adds a typed observation contract and rejects mismatched identity/provenance fields. A synthetic adapter is supplied exclusively for tests.

This is **not** authenticated GitHub readback: trusted adapters must be separately reviewed, authenticated and pinned. Typed Python objects alone do not make evidence authentic. A dedicated operational secret broker and externally hosted service are required for unattended production execution.

Safety gate: no external mutation until main ruleset and independent review, verified GitHub App installation permissions, mandate-bound effect journal, authenticated readback, idempotency and tested rollback are all attested.
