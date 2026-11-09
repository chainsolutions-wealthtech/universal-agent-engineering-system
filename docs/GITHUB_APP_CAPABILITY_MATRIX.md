# GitHub App permissions and maximum-capability audit

**Status: NOT YET VERIFIED against the target GitHub App.** Permission selection and admin approvals must follow GitHub's current official API documentation. The owner requested maximum usable reach, not an implicit bypass of GitHub security boundaries.

## Inventory requirements
Exhaustively enumerate Repository, Organization, Account and Enterprise permission categories and their actual supported levels (read/write/admin where available), REST/GraphQL endpoints, webhook events, installation scope, user-vs-installation token support, rate limits, restrictions and additional approvals. Keep dated evidence and a source URL for every entry. Recheck official documentation on permission or API changes.

## Mandatory capability clusters
- Repository provisioning, visibility, metadata, templates and ownership
- Code/contents, commits, branches, tags and Git data
- Issues, discussions, projects and pull requests/reviews
- Actions, workflows, checks, statuses, environments, deployments and releases
- Rulesets, branch protection and code security settings
- Webhooks, audit events, memberships, teams, organization administration and enterprise operations where supported
- Packages, secrets and variables through approved interfaces
- Installation lifecycle and temporary tokens
- Credential-safe external providers and infrastructure deployments

## Credential and authorization design
A broker holds encrypted GitHub App private keys outside git, mints short-lived installation tokens and records only fingerprints. For an operation, compute intersection of installation capabilities, org/repo rules, agent mandate, policy, environment and approvals. Default deny on missing evidence.

## Bootstrap gates
1. Verify App identity, owner and installations without revealing credentials.
2. Inspect currently granted permission levels; do not infer them from installation existence.
3. Verify repository_creation capability and policy; request permission change through approved GitHub process if missing.
4. Verify tool surface and audited authenticated execution of required endpoints.
5. Record creation and every subsequent action with effect reconciliation.
