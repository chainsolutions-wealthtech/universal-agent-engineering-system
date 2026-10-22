# Autonomous end-to-end operating charter (proposal)

## Objective
Run the complete software lifecycle without repeated human operation: intake, discovery, design, planning, coding, testing, review, integration, deployment, monitoring, recovery and durable reporting.

## Non-negotiable boundaries
- User intent is a mandate request, not a GitHub permission grant. Effective GitHub permissions are determined by the installation, organization policies and target repository.
- Request the **maximum officially supported GitHub App permissions only where explicitly needed**, then enforce a narrower per-operation policy (least privilege at execution). No invented or bypassed approval.
- Human action is an exception only when GitHub or another service requires one (installation, permission approval, billing, secret setup, legally or operationally high-impact authorization).
- No secret in git, logs, prompts, issues or public documentation. Private transcripts remain in a protected evidence store.
- Persist verified source, intent, approval, plan revision, action request, result and receipt for each transition.
- No claim of completed work unless the target system has been re-read and independently checked.
- No automatic merge of unreviewed high-impact or policy changes; automated independent review may be used only when explicitly accepted by policy and supported by enforced gates.
- External repositories have their own authorities; their roles/identities/tasks must not be imported as UAES permissions.

## End-to-end state flow
INTAKE -> DISCOVER -> RECONCILE -> SPECIFY -> ARCHITECT -> PLAN -> AUTHORIZE -> CLAIM -> EXECUTE -> VERIFY -> REVIEW -> INTEGRATE -> DEPLOY -> OBSERVE -> PERSIST -> RESUME.

Every stage has an input contract, an evidence receipt, a bounded retry policy and a recovery action. Unknown result => reconcile, not repeat blindly.
