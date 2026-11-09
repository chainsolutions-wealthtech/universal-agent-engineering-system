# Project charter — UAES

## Purpose
Build a durable provider-neutral multi-agent engineering platform for project discovery, requirements, architectural decisions, planning, authorized execution, evidence, checkpoints and recovery.

## Independent authority
This repository is distinct from UAP V5, MCP and GRT. Their identities, policies, tasks and history are never silently copied, superseded or combined.

## Design requirements
- Stable agent identity distinct from a session, mandate, task, claim and permission.
- Canonical memory with provenance and explicitly identified owner.
- Guarded planning, task DAG and auditable state transitions.
- Event coordination with deduplication and resumable operations.
- ChatGPT, Claude and other providers usable without Codex/Copilot requirements.
- No external repository writes until its own authorization has been verified.

## Constraints
Initial bootstrap is documentary only; no production authority, agent admission or delegated GitHub App rights are implied.
