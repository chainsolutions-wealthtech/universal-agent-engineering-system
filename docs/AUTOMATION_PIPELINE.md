# Governed autonomous engineering pipeline — design contract

| Stage | Input | Automatic verification evidence |
|---|---|---|
| 01 INTAKE | Request + source + constraints | Immutable correlation ID |
| 02 DISCOVER | Repositories/projects/docs | Source refs, version/SHA |
| 03 RECONCILE | Conflicting claims | Provenance report + decision status |
| 04 SPECIFY | Approved outcomes | Testable requirements |
| 05 ARCHITECT | Constraints | ADR and architecture review |
| 06 PLAN | Requirements | DAG, dependencies, effort, risk |
| 07 AUTHORIZE | Mandate + actual permissions | Policy decision receipt |
| 08 CLAIM | Ready task | Atomic lease/fencing token |
| 09 EXECUTE | Scoped plan | Idempotency key + effect report |
| 10 VERIFY | Execution result | Fresh tests + target readback |
| 11 REVIEW | Diff + specification | Independent review results |
| 12 INTEGRATE | Passing gates | PR/merge receipt under ruleset |
| 13 DEPLOY | Approved release | Deploy health, rollback proof |
| 14 OBSERVE | Service state | Metrics, alerts, incident events |
| 15 PERSIST | New verified truth | Checkpoint + source owner update |
| 16 RESUME | Checkpoint + live state | NEXT_ACTION, bounded reconciliation |

## Automation mechanics
Queue + durable outbox/inbox, idempotent commands, atomic task leases, exponential backoff with caps, dead-letter quarantine, explicit STOP states, manual break-glass access, audit-chain integrity and periodic disaster-recovery drills.

## Quality gates
Unit / integration / contract / security / dependency / e2e tests; source + specification review; environment isolation; canary rollout and rollback. Persist all outcomes. No unreviewed production change merely because an AI judged it safe.

## Metrics
Cycle completion, duplicate actions, unauthorized attempts, recovery time, task age, SLA breaches, release failure rate, missing receipts, memory divergence, external authority conflicts, token failures.

## Continuous operation
An independently hosted scheduler/worker and secure secrets are required. Chat sessions do not independently run perpetual background workers. Automation service deployment is a separate, verifiable milestone.
