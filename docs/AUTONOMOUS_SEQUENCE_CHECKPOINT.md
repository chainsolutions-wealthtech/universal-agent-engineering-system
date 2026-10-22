# Continuous sequence — next runnable milestone

At this point UAES includes: CI-tested local agents and mandates; SQLite task leases and fencing; read-only continuity workflow; durable effect journal; atomic effect preparation; a guarded completion method that requires confirmed bound effects; and a one-shot local runner that resumes deterministic allowlisted jobs across process restarts. These are prototypes, not a hosted autonomous service.

## Explicit limitations
A caller-supplied source/proof receipt is **not** an independently verified provider attestation. Do not wire this directly to live GitHub write operations. The existing local worker's simple complete() path is only for allowlisted synthetic actions; external effect completion must use complete_with_effects() after trusted provider readback. This runner is not an infinite daemon or a scheduler.

## Next work
Implement authenticated target readback and verified receipts, a persistent daemon with structured shutdown and safe retries, permission policy enforcement, independent CI review gates, then sandbox end-to-end integration. main remains unprotected and PR #1 must not be merged before verified protections and independent review.
