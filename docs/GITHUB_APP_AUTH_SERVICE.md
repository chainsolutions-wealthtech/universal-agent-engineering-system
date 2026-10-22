# GitHub App authentication service — implementation gate

`src/github_app_auth.py` implements GitHub App JWT signing (RS256) and read-only discovery of installation-granted permissions. This module runs **only** where the `cryptography` package and authorized secret material are provided. Never commit, echo or place the private key in public workflows.

Required environment: `UAES_GITHUB_APP_ID`, `UAES_GITHUB_INSTALLATION_ID`, `UAES_GITHUB_APP_PRIVATE_KEY_PEM`. App JWT lifetime is limited; use short-lived installation access tokens for actual repository actions in a separate execution broker. GitHub endpoint rights, organization policies, installations and provider approval must all be verified before use.

Current state: code committed for review, **no key provisioned, no installation permissions attested with this module, no live GitHub App token minted, and no repository creation grant assumed**.

Dependency for authorized deployment: `cryptography`, version pinned by a reviewed lockfile; runtime secret store, credential rotation and scoped outbound controls are still required.
