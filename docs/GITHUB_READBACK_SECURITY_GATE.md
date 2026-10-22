# Read-only GitHub commit readback — reviewable prototype

The new GitHubCommitReadback adapter performs **GET-only** inspection of a specific commit SHA in an explicitly identified `owner/repository`. The caller supplies an installation-scoped token at runtime. It does not mint or persist tokens or trigger any GitHub write.

## Security guarantees and limits

- Reject malformed targets, unsupported operations and missing authentication before any network call.
- Bind accepted observations to a GitHub REST response with matching 40-character commit SHA.
- Treat HTTP failures, 404 and mismatched responses as **UNKNOWN**; never infer that an external mutation did not happen.
- Tests use fake HTTP transport and **no real credential**.
- This is only a commit-identity readback, not general proof that an intended PR, file change, deployment or remote side effect was authorized or correct.
- Trust requires a configured authenticated token broker, pinned runtime dependencies, explicit repo policies, validated network identity/TLS, and independent review.
- `EffectJournal.resolve` still permits caller-supplied receipts, so **the external-write path must remain disabled** until resolution is restricted to verified observations and permission checks.
- The service is not deployed, and `main` remains unprotected. The PR is still draft.

## Next acceptance gate

Make provider attestation unforgeable at the effect-completion boundary, add scoped permission-policy tests, verify protection of `main` and obtain independent PR review before promoting anything to production.
