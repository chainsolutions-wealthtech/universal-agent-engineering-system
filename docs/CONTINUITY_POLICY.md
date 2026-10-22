# Continuous chaining — execution policy

## Purpose
Drive each admissible stage automatically, rather than requiring a new chat instruction after every task. The authoritative engine will eventually run in a durable externally hosted service. The GitHub Actions workflow is an initial read-only orchestrator and receipt producer.

## Events and scheduler
GitHub issues, pull requests and CI completions trigger reconciliation; an hourly schedule catches lost events and interruptions. Events may be duplicated or delayed: use unique event IDs, idempotency keys and bounded retries. Concurrency must not create concurrent task claims.

## Gate semantics
1. Observe current HEAD and effective ruleset/branch protection; absence or inaccessible evidence is **unverified**, never PASS.
2. Required current-head CI must pass.
3. Independent review is not the same as CI and cannot be self-certified.
4. GitHub App permissions and scopes must be attested separately from identity and mandate.
5. No automatic write or merge may bypass GitHub protections or organizational policies.
6. On permission, authorization, security or ambiguous effect: STOP and emit a durable blocked receipt.

## Current scope
The CI continuity workflow only emits next-action recommendations plus evidence artifacts. It does **not** claim the full autonomous engine is already operational, and it makes no GitHub repository mutations. Later phases can add authorized workers with narrow operations, durable store, error handling and audit receipts.

## Definition of eventual autonomy
Unattended flow for routine pre-authorized operations, with external approval only where legitimately required. A chat session is never a substitute for a persistent scheduler, key vault or third-party security policy.
