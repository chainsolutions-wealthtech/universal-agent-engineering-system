# P0 promotion policy revision — 2026-11-06

**Current owner-approved policy supersedes the historical reviewer requirement below.**
UAES no longer requires an independent *human* PR reviewer. Configure an effective protected-main ruleset requiring PRs and current-head CI checks (`core-tests`, `documentary-contracts`, `container-smoke`, `determine-next`, `automated-review`), with **zero required approving reviews** and, under owner decision D008, exactly three audited, identity-scoped `always` bypass actors for the authorized accounts. For all other actors, force-push and deletion remain prohibited; verify the effective rules with GitHub. The automated-review job performs deterministic security checks and full regressions; it is not an independent human approval.

Until main protection, exact check names, effective review-count policy, app permissions, and isolated runtime prerequisites are observed, promotion remains blocked. If an existing organization/provider policy requires approval, do not bypass it: obtain a legitimate policy change from the authorized GitHub administrator or stop that merge. The below 2026-10-22 assessment remains historical evidence, **not current instructions**.

### Rights-preservation amendment (2026-11-06, D008)

The owner has now explicitly required that the three authorized installation accounts retain maximal capabilities. **Do not execute the older empty-bypass configuration.** The updated installer `scripts/configure_main_ruleset.py` requires exactly three scoped, auditable `always` bypass actors and provider-side identity/installation verification: Wealthtechinnovations and Patricked-code as Users, plus an actual GitHub App Integration installed on UAES for chainsolutions-wealthtech. The third App principal is not yet attested, and the connected GitHub tool still cannot create rulesets. No ruleset has been applied. See `state/AUTHORIZED_BYPASS_ACCOUNTS.json` and `docs/U00_MAIN_RULESET_RUNBOOK.md`.

---

# P0 promotion blockers — checked 2026-10-22

Repository: `chainsolutions-wealthtech/universal-agent-engineering-system`, PR #1, branch `bootstrap/independent-foundation`.

## Live evidence at assessment
- Main branch `protected=false` via GitHub branches API.
- PR #1 is draft; no independently submitted reviews were returned from the connected GitHub review API.
- The four workflow families passed on the previously observed PR head.
- The ChatGPT GitHub connector exposes repository mutations but **no administration mutation endpoint for rulesets or branch protection**. Do not impersonate admin access or claim the main branch is protected.
- Connected GitHub App installation listings are not an attestation of the UAES dedicated App's exact effective grants.

## Required administrative operations
Apply a ruleset to `main` requiring pull requests, an independent approving review, no bypass, dismissal of stale reviews and required checks from the actual checks inventory. Then verify the ruleset in GitHub and obtain an independent review of PR #1. Provision an isolated runner host and dedicated GitHub App installations only through the authenticated administrative channel, and gather evidence of their scope and permissions.

The promotion gate in `scripts/promotion_gate.py` refuses promotion if evidence is missing. It is **not** itself an enforced GitHub branch-protection setting. Keep PR #1 draft and unmerged until these prerequisites are independently attested.
