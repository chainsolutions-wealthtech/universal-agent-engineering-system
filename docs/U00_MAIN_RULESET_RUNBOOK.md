# U00 — apply and attest protected main (owner policy D007)

This document specifies the **native GitHub administration** required before
integrating bootstrap PR #1. It is not an authorization to bypass GitHub
branch protections, organizational rules or applicable terms.

## Current provider result — verified 2026-11-09

**U00 COMPLETE.** This runbook's original installation instructions and
2026-11-06 blocker are historical. The owner created ruleset
[`26883048`](https://github.com/chainsolutions-wealthtech/universal-agent-engineering-system/settings/rules/26883048)
through GitHub's native administrative UI. A fresh GitHub REST readback
confirmed repository-level `enforcement=active`, `main.protected=true`,
`refs/heads/main` target, `required_approving_review_count=0`, five required
GitHub Actions checks bound to App ID `15368`, and the exact three
`always` bypass records `User/94637590`, `User/270385782`,
`Integration/5417646`. GitHub also confirmed PR #1 merge
`c5172a7e85eed43732687bd63c2e5a290d4c97be` and PR #7 merge
`91b6e5fb674c30a29ca07b7dc024db7671db9ade`. Do **not** rerun the
bootstrap installer `--apply` as a means of checking an already merged PR
#1: its historical bootstrap preflight intentionally requires that PR to
remain open. For ongoing verification read the **native** GitHub ruleset,
branch and Check Runs endpoints instead.

**Important scope distinction:** the GitHub ruleset confirms the App's
numeric Integration bypass principal; it is **not** evidence of the
dedicated App's full installation permission matrix, token broker,
hosted UAES worker, staging, backups or production autonomy. U02 is next.

## Required state

- Repository: `chainsolutions-wealthtech/universal-agent-engineering-system`.
- Protected ref: `refs/heads/main`; ruleset name: `UAES main governed automation D007`.
- Merge path: pull requests only. **Zero required human approvals** under UAES policy D007. No required code-owner review or last-push reviewer.
- Required checks on the current PR HEAD from the **GitHub Actions application ID 15368** (observed on 2026-11-06): `core-tests`, `documentary-contracts`, `container-smoke`, `automated-review`, `determine-next`.
- Required checks use strict up-to-date base policy. For ordinary actors: no deletion or force-push. The three explicitly authorized identities retain an auditable `always` bypass on **this** ruleset; no blanket RepositoryRole or OrganizationAdmin bypass is granted.
- GitHub identities verified from current API access: `Wealthtechinnovations` (User ID 94637590), `Patricked-code` (User ID 270385782), and `chainsolutions-wealthtech` (Organization ID 299685687). This is three **installation accounts**, not three user logins. The organization's authorized executing principal must be mapped to the exact GitHub App `Integration` installed on UAES; an organization cannot be used as a `User` bypass actor.
- The discoverable mapping is `state/AUTHORIZED_BYPASS_ACCOUNTS.json`. The owner-declared candidate GitHub App is `ChainSolutions Universal Gateway`, App ID `5417646`, public URL slug `chainsolutions-universal-gateway`. These values are **candidates only**, not live GitHub App/installation attestations. The installer must verify App ID, slug, organization installation and actual UAES repository access before any write, otherwise stop without altering rights.
- Organization-level rules cannot be overridden; if there is a real external approval requirement, stop and report that requirement.

## Safe preparatory execution

From the reviewed UAES branch in a trusted working environment:

```bash
python -m unittest discover -s tests -v
python scripts/configure_main_ruleset.py
```

The second command is a **network-free dry-run**. A complete syntactic candidate produces `DRY_RUN_ONLY`, **not** a claim of authorized actor identity. With a missing or invalid mapping, it emits `BLOCKED_NO_RIGHTS_CHANGE` rather than applying an incomplete policy. This is deliberate and does not require routine owner approval.

## Authorized administration and readback

GitHub's `POST /repos/{owner}/{repo}/rulesets` requires an authenticated
credential with **Repository Administration: write**. A GitHub profile reporting
`admin=true` does not itself provide that credential to a particular tool.

The mapping includes only the previously owner-declared App ID and slug as candidates. The installer validates all three identities and the App's organization installation/repository access through the provider API **before creating any rule**, failing closed if evidence is inaccessible or mismatched. Do not substitute the ChatGPT GitHub connector's installation IDs for the ChainSolutions Universal Gateway App's identity.

Once an authorized GitHub administration executor exists, supply its **short-lived**
token from a protected secret broker as the runtime-only
`UAES_ADMIN_GITHUB_TOKEN` variable and run:

```bash
python scripts/configure_main_ruleset.py --apply
```

Never place the token in the Git repository, CI logs, issues, prompts, command
arguments, or public documentation. Do not run the privileged installer from
`pull_request` workflows or untrusted branch code.

The installer reads the three-actor mapping, verifies the two users and the organization's App installation, PR #1, exact current-HEAD GitHub Actions results, current
branch and effective rules, checks for an existing named ruleset, refuses
conflicting external review requirements, applies **one** named ruleset if
absent, and re-reads the effective GitHub policy. It must emit
`VERIFIED_ENFORCED` with a provider-native ruleset ID before the gate is
considered completed. A GitHub API failure or ambiguous state is a blocker.

If the ruleset exists but differs, including any of the three bypass identities or bypass modes, the installer refuses to overwrite it and
requires deliberate reconciliation. The installer **never merges PR #1**. Do not apply the historical `bypass_actors: []` variant: it would conflict with the current owner-approved rights-preservation policy.

## Post-U00 continuation

1. Re-read GitHub's main protection, applied rules, review count and required
   checks at the PR's current exact head SHA; record links and ruleset ID.
2. Run `promotion_gate.py` with `promotion_stage=bootstrap`, obtained from
   authenticated live evidence. Its local result is advisory, not a GitHub
   permission grant.
3. When provider-enforced gates are satisfied, promote PR #1 from Draft and
   merge via the authorized GitHub pull request route (not direct push).
4. Re-read merge SHA, `main` and CI. Only then begin U02 isolated worker
   deployment and subsequent GitHub App provisioning.

**Observed blocker as of the 2026-11-06 investigation:** the connected
GitHub identity has repository `admin` status, but the installed
ChatGPT GitHub tools expose **no ruleset/branch-protection mutation** and the
available execution environment has **no authorized admin token**. No
ruleset creation or protected merge has been performed. Running this
script later under a separately authenticated administrator is an actual
external prerequisite, not something an hourly chat automation can assume.

Canonical continuation: `docs/UNIFIED_DELIVERY_SEQUENCE.md`, issues #2–#5
and PR #1.
