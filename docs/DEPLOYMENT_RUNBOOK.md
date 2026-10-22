# Autonomous worker deployment runbook (NOT DEPLOYED)

This repository supplies a Docker image and Compose service capable of polling **local deterministic allowlisted** tasks from a persistent SQLite volume. It cannot perform GitHub writes or provision its own permission grants. A runtime agent and mandate must already exist in the mounted database; missing values stop startup instead of fabricating authority.

## Preconditions
- Independent authorized host and container runtime; no MCP/GRT/UAP V5 infrastructure use by default.
- Verified PR, main ruleset, independent review and pinned deployment revision.
- Persistent backed-up volume with authorized existing agent/mandate and appropriate filesystem ownership.
- Scoped secret vault and token broker required before adding any GitHub API worker.
- Restore/rollback plan and health/observability checks.

## Staging only, after prerequisites are met
Build with `docker compose build`. Set `UAES_AGENT_ID` and `UAES_MANDATE_ID` to valid pre-existing authorized records; run `docker compose up -d`. Read `/healthz` internally and inspect health state. The service uses a bounded local task vocabulary; do not attach external repositories or credentials.

## Limitations
The daemon is single-node and exposes no public network port in Compose. It is not a proven multi-node scheduler. Health readiness checks configuration, not effective permission validity; production readiness requires DB and authorization checks. Docker deployment, persistent storage configuration, remote backups, TLS ingress and hosted uptime **have not been performed or verified**.

## Next checkpoint
Deploy to an isolated, explicitly authorized environment, validate restart/rollback and backup recovery, then complete independent security review before any external writes.
