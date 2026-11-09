# U02 — S1 admission and governed isolated staging deployment

> STATUS: **READ-ONLY HOST PREFLIGHT, NO DEPLOYMENT** (2026-11-09).
> This document is an additive U02 operational plan. It does **not** grant
> deployment authority, certify a host, or supersede
> `docs/UNIFIED_DELIVERY_SEQUENCE.md`, `docs/DEPLOYMENT_RUNBOOK.md`,
> `state/CURRENT_STATE.json` or existing UAES mandates/claims/effects.
> No changes to Patricked-code/MCP, GRT, UAP V5 or other repositories.

## 1. Scoped evidence, not general host certification

The preflight was performed via **read-only** registered S1 SSH-bridge
diagnostics. Do not publish private infrastructure addresses, usernames,
service configuration, credentials, domains, SSH paths or unredacted command
output in this repository.

| Item | Verified host observation | Remaining admission condition |
| --- | --- | --- |
| Server | Existing shared S1 host | Owner has chosen S1 for *candidate* deployment, not an execution grant |
| Disk | Root filesystem size 77G; 56G used; 18G available; 76% usage | Verify inodes, filesystem quotas and staging/backup reserve before installing |
| Docker | Runtime present; pre-existing MCP container reports healthy | Check Docker Compose version, daemon health, project namespace and Docker access scope |
| PM2/Plesk | Existing services and virtual hosts found | Do not touch their filesystem, reload services, change firewall/DNS or reuse runtime credentials |
| Existing backups | Plesk/MySQL backup files observed | They do not certify an isolated UAES backup or off-host restoration |
| CPU/RAM/swap | **NOT VERIFIED** by the bounded diagnostics | Read `nproc`, `/proc/meminfo`, memory headroom and swap; reject if insufficient |
| Ports/firewall | Existing MCP is bound to loopback; UAES does not currently publish an application port | Verify other ports, firewall, TLS/ingress and whether a separate endpoint is actually needed |
| System security | Host project context is known, but general sudo/ACL/user and Docker group permissions not checked | Verify dedicated non-root UAES service identity, immutable image and no Docker socket mount |
| Write tool | The current bridge reports `free_shell=false` and `run_command_s1=false` | Use separately authorized UAES-only executor; never repurpose MCP deployment tools |
| Runtime | No UAES deployment observed | Do not set `runtime_operational=true` without fresh host receipts |

Run the checked-in `scripts/preflight_s1_readonly.sh` **from an already
authorized, reviewed execution context**. The script invokes read-only
queries only; it does not install, stop, launch, write or delete anything.
Do not send its unredacted output to public GitHub or an assistant.

## 2. Isolation boundary for the eventual deployment

1. **Identity:** create a dedicated service account/UID and per-project
   Linux filesystem permissions through the authorized host administrator.
   Do not put the UAES process in the `docker` group or mount
   `/var/run/docker.sock` into the worker. Never reuse credentials
   from the MCP bridge, Plesk subscriptions or existing applications.
2. **Filesystem:** use a new dedicated application root (candidate
   `/opt/uaes`, only after confirming it is unused and not a symlink);
   keep release code, persistent SQLite state and backups in separately
   owned directories and volumes. Never create directories inside the
   MCP application root or another project's Plesk vhost.
3. **Container namespace:** the future Compose project name is
   `uaes-staging`, **not** any existing Compose project; use a dedicated
   named persistent volume, healthchecks, restart policy and resource
   limits sized *after* CPU/RAM observations. Prefer read-only container
   root filesystem, `no-new-privileges`, drop Linux capabilities,
   dedicated UID and no privileged mode or host networking.
4. **Network:** existing `compose.yaml` exposes no host port. Keep
   `/healthz` and `/readyz` internal while validating staging. Do not
   add a public proxy, host port, domain, DNS or firewall rule without
   a separate explicit network admission.
5. **Credentials:** GitHub App private key, installation tokens and
   deployment credentials remain in an approved secret broker, outside
   GitHub, chat, logs and Compose files. U02 local-only worker gets no
   credentials for other repos. Do not synthesize an agent/mandate from
   a conversation assertion: real rights must be verified in the
   canonical UAES database.
6. **Autonomy boundary:** the present Docker image can run *only local
   deterministic allowlisted actions*. GitHub code-writing agent,
   continuous background coding, GitHub App permissions and external
   target project admission are U03–U09, not U02.

## 3. Governed execution sequence: no execution until preflight is complete

| Stage | Change after authorization | Required actual receipt |
| --- | --- | --- |
| A / Admission | Confirm CPU, available RAM/swap, disk/inodes, shell/Compose and dedicated write scope | Redacted host capability & signed owner/admin admission |
| B / Source | Obtain exact reviewed UAES `main` SHA; verify CI and ruleset; keep release immutable | GitHub SHA, five latest check runs and image provenance |
| C / Build | Build isolated image without changing existing services | Immutable image ID/digest, runtime version and resource limits |
| D / Identity | Create isolated host account, volume and **already-authorized** UAES agent/mandate | UID, volume owner, project/mandate expiry and scope, no copied secrets |
| E / Staging | Start **only** `uaes-staging`, no external repo write credentials | Container ID, actual `/healthz`, authenticated `/readyz`, logs and process state |
| F / Recovery | Stop/restart only UAES worker, test crash and duplicate-event fencing | Restart timestamps, zero foreign-service restarts, task/event invariants |
| G / Backup | Make SQLite online backup to independent destination; test digest and restore to fresh location | SHA-256, SQLite integrity check and fresh restore evidence |
| H / Rollback | Return UAES to previously pinned image/state using governed rollback | Image SHA/digest and restored state proof, no MCP/Plesk impact |
| I / U02 acceptance | Reconcile all receipts and record in GitHub checkpoint | `U02_VERIFIED_STAGING` only when every required receipt exists |

Never run `docker system prune`, broad `docker compose down`,
`docker stop` by wildcard, global service restart, host-level
`chown -R`, `chmod -R`, or `apt upgrade` as part of UAES admission.

## 4. Stop/rollback gates

- Stop if available RAM/swap or disk/inodes are inadequate after live
  measurement; size resource limits from observed headroom, not guesses.
- Stop if `/opt/uaes` already exists without a verified UAES owner,
  or if a symlink/volume might resolve into another service.
- Stop if a deployment actor has only MCP-targeted permissions;
  sharing a host does **not** share authorization.
- Stop if the image SHA, actual agent/mandate, healthcheck, backup,
  restore or rollback evidence cannot be verified.
- Stop if any intended operation could alter existing MCP/Plesk/PM2
  services, change host-wide DNS/network/firewall, or reach other repos.

## 5. NEXT_ACTION

1. Obtain the missing S1 CPU, RAM, swap, inodes, OS, Docker Compose,
   access control and port/firewall readings from a trusted independent
   host administrative session. Keep raw output private.
2. Establish a dedicated UAES host deployment connection with
   **explicitly scoped** write permission; the existing MCP SSH bridge
   does not supply a generic S1/UAES deployment action.
3. Agree on a resource budget and backup destination based on
   actual headroom. Only then perform the authorized U02 staging
   actions and read back their receipts.

Until completed, `state/CURRENT_STATE.json` remains
`active_gate=U02` and `runtime_operational=false`.
