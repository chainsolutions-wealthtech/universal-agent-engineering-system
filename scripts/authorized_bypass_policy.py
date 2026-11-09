"""Exact-identity, non-expanding GitHub ruleset bypass policy.

A GitHub App installation *account* is not itself an authorized GitHub
ruleset actor. Users can be targeted individually, whereas an organization
needs a precisely authorized Integration actor (a GitHub App installed on that
organization's target repository). OrganizationAdmin is deliberately refused
because it could authorize more people than the three requested principals.
No bypass is created before all three mappings are provider-attested.
"""
import json
import re
from pathlib import Path

EXPECTED = {
    "Wealthtechinnovations": ("User", 94637590),
    "Patricked-code": ("User", 270385782),
    "chainsolutions-wealthtech": ("Organization", 299685687),
}
APP_SLUG = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]{1,98}$")


class BypassPolicyError(ValueError):
    """Fail closed: the requested actor set is not exactly attested."""


def load_bypass_configuration(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BypassPolicyError("BYPASS_CONFIGURATION_UNREADABLE") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise BypassPolicyError("BYPASS_SCHEMA_INVALID")
    if data.get("scope") != "chainsolutions-wealthtech/universal-agent-engineering-system":
        raise BypassPolicyError("BYPASS_SCOPE_INVALID")
    if data.get("required_bypass_mode") != "always":
        raise BypassPolicyError("BYPASS_MODE_UNEXPECTED")
    accounts = data.get("accounts")
    if not isinstance(accounts, list) or len(accounts) != 3:
        raise BypassPolicyError("EXACTLY_THREE_ACCOUNTS_REQUIRED")
    by_login = {a.get("account_login"): a for a in accounts if isinstance(a, dict)}
    if set(by_login) != set(EXPECTED) or len(by_login) != 3:
        raise BypassPolicyError("AUTHORIZED_ACCOUNT_SET_MISMATCH")
    actors = []
    for login, (kind, numeric_id) in EXPECTED.items():
        actor = by_login[login]
        if actor.get("account_type") != kind or type(actor.get("account_id")) is not int or actor["account_id"] != numeric_id:
            raise BypassPolicyError("AUTHORIZED_ACCOUNT_ID_MISMATCH:" + login)
        if actor.get("bypass_mode") != "always":
            raise BypassPolicyError("AUTHORIZED_BYPASS_MODE_UNEXPECTED:" + login)
        if kind == "User":
            if actor.get("bypass_actor_type") != "User" or actor.get("bypass_actor_id") != numeric_id:
                raise BypassPolicyError("AUTHORIZED_USER_ACTOR_MISMATCH:" + login)
        else:
            if actor.get("bypass_actor_type") != "Integration":
                raise BypassPolicyError("ORGANIZATION_IS_NOT_USER_OR_UNSCOPED_ADMIN")
            if type(actor.get("bypass_actor_id")) is not int or actor["bypass_actor_id"] < 1:
                raise BypassPolicyError("TARGET_ORGANIZATION_APP_ID_NOT_ATTESTED")
            if not isinstance(actor.get("app_slug"), str) or not APP_SLUG.fullmatch(actor["app_slug"]):
                raise BypassPolicyError("TARGET_ORGANIZATION_APP_SLUG_NOT_ATTESTED")
        actors.append({
            "actor_type": actor["bypass_actor_type"],
            "actor_id": actor["bypass_actor_id"],
            "bypass_mode": "always",
        })
    if len({(x["actor_type"], x["actor_id"]) for x in actors}) != 3:
        raise BypassPolicyError("DUPLICATE_BYPASS_PRINCIPAL")
    return data, actors


def verify_bypass_principals(client, config):
    """Use an authenticated GitHub API source before enabling bypass rights."""
    for actor in config["accounts"]:
        login = actor["account_login"]
        kind, expected_id = EXPECTED[login]
        if kind == "User":
            current = client.request("GET", "/users/" + login)
        else:
            current = client.request("GET", "/orgs/" + login)
        if (not isinstance(current, dict) or current.get("id") != expected_id
                or current.get("login", "").lower() != login.lower()):
            raise BypassPolicyError("GITHUB_PRINCIPAL_READBACK_MISMATCH:" + login)
        if kind == "User":
            permission = client.request(
                "GET", "/repos/chainsolutions-wealthtech/universal-agent-engineering-system"
                "/collaborators/" + login + "/permission")
            if (not isinstance(permission, dict) or permission.get("permission")
                    not in ("write", "maintain", "admin")):
                raise BypassPolicyError("NO_EFFECTIVE_REPO_WRITE_ACCESS:" + login)
        else:
            slug, app_id = actor["app_slug"], actor["bypass_actor_id"]
            app = client.request("GET", "/apps/" + slug)
            if (not isinstance(app, dict) or app.get("id") != app_id
                    or app.get("slug", "").lower() != slug.lower()):
                raise BypassPolicyError("GITHUB_APP_IDENTITY_UNVERIFIED")
            # A valid App alone is not proof it can act on this repo. Read
            # user-accessible app installations and their repo selections.
            installs = client.request("GET", "/user/installations?per_page=100")
            if not isinstance(installs, dict):
                raise BypassPolicyError("APP_INSTALLATIONS_UNVERIFIED")
            if installs.get("total_count", 101) > len(installs.get("installations", [])):
                raise BypassPolicyError("APP_INSTALLATIONS_PAGINATION_UNVERIFIED")
            eligible = [
                item for item in installs.get("installations", [])
                if item.get("app_id") == app_id
                and item.get("account", {}).get("login", "").lower() == login.lower()
                and item.get("account", {}).get("id") == expected_id
            ]
            if len(eligible) != 1:
                raise BypassPolicyError("TARGET_ORGANIZATION_INSTALLATION_UNVERIFIED")
            # Verify live installation permissions, not just account membership.
            # Bypass rules do not confer write access; the App must already
            # have provider-granted Contents and Pull requests write rights.
            granted = eligible[0].get("permissions")
            if not isinstance(granted, dict):
                raise BypassPolicyError("APP_GRANTED_PERMISSIONS_UNVERIFIED")
            if granted.get("contents") != "write" or granted.get("pull_requests") != "write":
                raise BypassPolicyError("APP_REQUIRED_WRITE_GRANTS_MISSING")
            installation_id = eligible[0].get("id")
            if type(installation_id) is not int:
                raise BypassPolicyError("INSTALLATION_ID_UNVERIFIED")
            repositories = client.request(
                "GET", "/user/installations/" + str(installation_id)
                + "/repositories?per_page=100")
            if not isinstance(repositories, dict):
                raise BypassPolicyError("APP_REPO_ACCESS_UNVERIFIED")
            items = repositories.get("repositories", [])
            if repositories.get("total_count", 101) > len(items):
                raise BypassPolicyError("APP_REPOSITORIES_PAGINATION_UNVERIFIED")
            if not any(
                item.get("full_name", "").lower()
                == "chainsolutions-wealthtech/universal-agent-engineering-system"
                for item in items
            ):
                raise BypassPolicyError("APP_NOT_INSTALLED_ON_UAES_REPOSITORY")
    return True
