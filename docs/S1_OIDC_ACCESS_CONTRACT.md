# S1 OIDC access contract — preflight only

UAES may deploy to S1 only through a dedicated broker which verifies GitHub Actions OIDC tokens using GitHub's published signing keys, checks issuer, exact audience, expiry, repository ID, immutable workflow identity, ref and protected environment, and issues a short-lived project-isolated capability for **UAES only**.

## Strict prerequisites
1. Provision an independently managed S1 OIDC trust gateway or equivalent audited federation endpoint. No generic SSH access, borrowed MCP credentials, or shared deployments.
2. Configure a dedicated `uaes-s1-staging` GitHub environment with restrictive reviewers and branch policy, and its non-secret variable `UAES_S1_OIDC_AUDIENCE` equal to the broker's exact expected audience.
3. Give the broker only a dedicated UAES deployment identity scoped to its own directory, network/ports, volumes and container resources; prohibit access to MCP/GRT/UAP V5.
4. Require protected-main promotion and independent review, provenance of the exact built artifact, image digest pinning, backup and rollback checks.
5. Record sanitized admission logs and attest remote service readiness/health before declaring deployment success.

The `UAES S1 OIDC Preflight` workflow is manual and checks prerequisites without requesting, recording or exchanging an OIDC token. It **does not access S1**. Do not confuse an OIDC token from GitHub with an SSH credential: an explicit trust broker is required to bridge that boundary.

Next: implement and independently verify the broker in a segregated S1 deployment context, authorize a first sandbox exchange, and only then enable deployment operations.
