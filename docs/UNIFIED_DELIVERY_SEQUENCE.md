# UAES — canonical unified delivery sequence (2026-11-06)

> **Status: governed plan, NOT an execution grant or production attestation.**
> This document unifies the two owner-approved implementation orders without replacing
> `docs/BUILD_PLAN.md`, `docs/AUTONOMY_IMPLEMENTATION_ROADMAP.md`, the existing
> `src/uaes_core.py` task authority, the event ledger or GitHub review rules.
> Project: `chainsolutions-wealthtech/universal-agent-engineering-system`.
> Bootstrap source: PR #1, `bootstrap/independent-foundation`.

## Immutable operating rules

- GitHub `main`, PR reviews and required checks are **provider-enforced** boundaries;
  passing a local `promotion_gate.py` is not equivalent to an enforced ruleset.
- No merging PR #1 before independently verified main protection, current-head CI,
  independent approval and the additional promotion prerequisites specified in
  `docs/P0_PROMOTION_BLOCKERS.md` / `scripts/promotion_gate.py`.
- Every external operation uses an actual scoped permission, current-head readback,
  idempotency key and confirmed receipt; unknown outcomes are reconciled, not replayed.
- Existing identity, mandate, tasks, claims/fencing, effect journal and recovery in
  `src/` remain the only UAES local authorities. Discovery or projections MUST NOT
  create another work queue or confer execution permission.
- UAES is independent of MCP, UAP V5 and GRT. MCP interop is **opt-in** with explicit
  ownership and one governing task authority per target. No inherited credentials,
  mandates, secrets or runtime directories. No Codex or Copilot dependency.
- Changes are incremental on reviewable branches with baseline tests, RED/GREEN,
  adjacent regressions, current-HEAD CI and durable checkpoint receipts.
- When a preauthorized operation completes, recompute readiness and proceed to the
  next admissible task; no routine user prompt is required. Stop at real authorization,
  independent-review, safety or unknown-effect gates, or when no work is admissible.
- A ChatGPT chat, a GitHub workflow emitting next actions, a local Docker smoke test,
  and a hosted continuously executing code agent are four distinct things. Only
  separately observed runtime evidence can establish the final one.

## Ordered dependency chain

| Step | Owner-approved objective | Reuse and implementation boundary | Acceptance / evidence | Blocking authority |
|---|---|---|---|---|
| U00 | **Secure `main` and PR #1** | Issues #2/#3; current-head Checks API, `promotion_gate.py` | Enforced ruleset requires PR, independent approval, correct checks, no bypass/force-push; independent review on exact head | Repository administrator and reviewer |
| U01 | **Integrate UAES bootstrap** | PR #1, existing `src/`, tests, `Dockerfile`, `compose.yaml`; do not rewrite history | P0 gates evidenced, green checks and authorized merge SHA re-read on `main` | U00 and remaining promotion gates |
| U02 | **Bring up isolated durable worker staging** | `src/daemon.py`, `src/job_runner.py`, SQLite, `docs/DEPLOYMENT_RUNBOOK.md` | Independently hosted `/readyz`, persistent volume, service restart, backup/restore, rollback, digest and current SHA evidence | U01, isolated host, authorized secret/config path |
| U03 | **Verify GitHub App and token broker** | `src/github_app_auth.py`, `docs/GITHUB_APP_CAPABILITY_MATRIX.md`, issue #4 | App/installation identity, scope and exact grants read back; expiring scoped installation tokens, secret-store isolation | U00–U02, approved App installation and broker |
| U04 | **Add project inventory and cartography** | Extend `src/github_readback.py` and read-only reconciliation; maintain per-project provenance | Discovery of main, relevant branches, PRs, issues, commits, architecture, workflows, dependencies and SHA; repeatable diff | U03 read permissions; source quality |
| U05 | **Implement mandate, program and task factory** | Extend the existing UAES task DAG only; Project → Mandate/Mission → Program → WorkItem/Wave → TaskBlueprint → Task → UTL | Parent/child traceability, dependency readiness, deduplication, collision tests, no fabricated authorization | U04, authority and state migration checks |
| U06 | **Admit and recover authorized code agents** | Existing agents/mandates/sessions/claims/leases/fencing, checkpoints and journal | `Je suis agent codeur` triggers identity and effective-rights verification, context reconciliation, checkpoint rebind and admissible claim | U02/U03/U05; no permission derived from chat phrase |
| U07 | **Connect real sandboxed coding execution** | Extend `src/uaes_worker.py`, `src/job_runner.py`, `src/daemon.py`; no second scheduler | Scoped task/UTL produces isolated code diff, RED/GREEN, adjacent regression tests and branch commit | U06, verified executor identity, sandbox and safety |
| U08 | **Govern GitHub PR → CI → review → merge → deploy** | Existing GitHub Actions, checks/receipt verifier/effect coordinator; project-specific deploy adapter | Exact SHA, independent review, required checks, allowed merge, release/deployment and runtime readback when applicable | U00/U03/U07, target repo/environment policy |
| U09 | **Certify AUTO_CONTINUE and restart resilience** | Existing daemon, effect journal, leases/fencing and next-action projection; historical MCP `PROGRAM_AUTO_CONTINUE` only as non-authoritative reference | Two independent eligible tasks advance sequentially without another chat turn; crash/restart/duplicate-event recovery and no bypass | U05–U08 |
| U10 | **Optional MCP interoperability** | Explicit adapter to an approved MCP governed admission/target mapping; NO second task or runtime authority | Same target task has one owning authority; stand-alone mode works without MCP; integration contract and isolation tests | U09 and separately approved MCP boundary |
| U11 | **Pilot on Openfunds and another isolated repository** | Install App + per-project configuration, not a cloned UAES engine | Two repositories cartographed, eligible tasks produced/tested, independently governed delivery and continuation evidence | U09, repo-specific permissions; U10 not required |

The steps above describe acceptance dependencies, **not a claim that each predecessor is
implemented**. Technical documentation, synthetic tests and isolated read-only features
may be prepared in parallel with blocked gates, without performing prohibited effects.

## Existing roadmap crosswalk

| Existing work | Unified location |
|---|---|
| `P00–P03`, `A00–A01` | U00–U01 and D005 architecture decision |
| `P04`, `A03–A04` | U03; protected initialization depends on U00 |
| `P05–P09`, `A05–A07` | U05–U06 (reuse current UAES core, event journal, BUS proposals) |
| `P10`, `A08–A09` | U06–U07 |
| `P11`, `A09–A10` | U07–U08 |
| `P12`, `A02/A11` | U02 and U08–U09 |
| `P13`, `A12` | U09–U11 |
| Missing explicit cartography/task factory | U04–U05 |
| Optional MCP, non-MCP portability | U10–U11 |

## Live evidence baseline and continuation

Observed 2026-11-06 after the worker-readiness patch:
- PR #1 `OPEN`, `Draft`, head `bf6cbd2f75f83c186cdb3972170c41a2aaef2aed`;
  all seven returned head check-runs `SUCCESS` at that observation.
- `main` SHA `8cd0932b4ef8b2704c582e509753a01717fe7d45`,
  `protected=false`; ruleset list empty; PR review list empty.
- `runtime_operational=false`; isolated UAES runtime, App grants and token broker
  not attested; no production deployment, main merge or external repo write.

**NEXT_ACTION**: execute U00 by a truly authorized branch-rule administrator and
independent reviewer. Meanwhile prepare safe additive work for U02–U05 on separate
reviewable changes and re-check each GitHub SHA before writing. Once U00 gates are
attested, promote U01 and continue through the ordered dependencies. Record exact
commit/check/approval/merge/deploy/runtime receipts. Never substitute a GitHub
checkpoint comment for a verified runtime state.

Related anchors: PR #1; issues #2 (ruleset), #3 (review), #4 (App), #5 (worker).
