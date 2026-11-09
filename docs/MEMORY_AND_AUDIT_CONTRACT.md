# Canonical memory, documentation and audit

## Ownership
One canonical owner per durable fact. Current state, chronological events and source archives are different artifacts; never equate a summary with a full transcript.

## What gets recorded
Project/program ID, requested change, source/provenance, requirements, priorities, alternative designs, rejected options, approved decisions, policy/machine version, assigned agent, mandate, claim, session binding, effect/idempotency key, artifact SHAs, tests, CI, release, deployment, incident, evidence receipts, failure, retry and next action.

## Recommended stores
- Public Git repo: reviewed charter, non-sensitive ADRs, specifications, roadmap, schemas and release notes.
- Protected append-only event/evidence store: private content, full authorized transcripts, audit receipts and hashes, redacted logs.
- Database: effective state projections, locks, tasks and indexes; rebuildable from events when possible.
- Object storage: immutable exports, verification bundles and snapshots with retention policy.

## Resumption contract
Given a project and an authorized agent, resolve the existing canonical project/identity, compare last recorded checkpoint with fresh source-of-truth observations, reconcile uncertain effects, renew authorization, and then select only the next eligible action. Refuse to manufacture identities, successes or credentials.

## Security/privacy
Sensitive sources only with informed authorized collection; retention and deletion rules, encryption at rest/in transit, least-privileged queries, log redaction, access audits and export integrity controls.
