"""Three-account policy: never silently narrow rights or expand to all admins."""
import json
import tempfile
import unittest
from pathlib import Path
from scripts.authorized_bypass_policy import (
    BypassPolicyError, load_bypass_configuration, verify_bypass_principals,
)

SOURCE = Path(__file__).resolve().parents[1] / "state/AUTHORIZED_BYPASS_ACCOUNTS.json"


class BypassActorPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "actors.json"
        self.data = json.loads(SOURCE.read_text(encoding="utf-8"))

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        self.path.write_text(json.dumps(self.data), encoding="utf-8")
        return self.path

    def complete_app(self):
        app = self.data["accounts"][2]
        app["app_slug"] = "uaes-test-app"
        app["bypass_actor_id"] = 123456

    def test_missing_app_identity_still_blocks_ruleset(self):
        self.data["accounts"][2]["app_slug"] = None
        self.data["accounts"][2]["bypass_actor_id"] = None
        with self.assertRaisesRegex(BypassPolicyError, "TARGET_ORGANIZATION_APP_ID_NOT_ATTESTED"):
            load_bypass_configuration(self.save())

    def test_owner_declared_candidate_is_not_live_attestation(self):
        self.assertEqual(self.data["accounts"][2]["bypass_actor_id"], 5417646)
        self.assertEqual(self.data["accounts"][2]["app_slug"], "chainsolutions-universal-gateway")
        self.assertIn("CANDIDATE", self.data["verification"])
        _, actors = load_bypass_configuration(self.save())
        self.assertEqual(actors[2]["actor_id"], 5417646)
        # Only verify_bypass_principals() performs actual GitHub readback before any write.

    def test_three_exact_actors_can_be_constructed_when_app_mapped(self):
        self.complete_app()
        data, actors = load_bypass_configuration(self.save())
        self.assertEqual(len(data["accounts"]), 3)
        self.assertEqual([x["actor_type"] for x in actors], ["User", "User", "Integration"])
        self.assertEqual([x["bypass_mode"] for x in actors], ["always"] * 3)

    def test_never_grant_organization_wide_administrator_bypass_implicitly(self):
        self.complete_app()
        self.data["accounts"][2]["bypass_actor_type"] = "OrganizationAdmin"
        with self.assertRaisesRegex(BypassPolicyError, "ORGANIZATION_IS_NOT_USER"):
            load_bypass_configuration(self.save())

    def test_no_actor_dropped_or_added_silently(self):
        self.complete_app()
        self.data["accounts"].pop()
        with self.assertRaisesRegex(BypassPolicyError, "EXACTLY_THREE_ACCOUNTS_REQUIRED"):
            load_bypass_configuration(self.save())
        self.data["accounts"].append({"account_login": "unexpected"})
        self.data["accounts"].append({"account_login": "fourth"})
        with self.assertRaisesRegex(BypassPolicyError, "EXACTLY_THREE_ACCOUNTS_REQUIRED"):
            load_bypass_configuration(self.save())

    def test_wrong_identity_or_partial_privilege_is_rejected(self):
        self.complete_app()
        self.data["accounts"][0]["account_id"] = 1
        with self.assertRaisesRegex(BypassPolicyError, "AUTHORIZED_ACCOUNT_ID_MISMATCH"):
            load_bypass_configuration(self.save())
        self.data["accounts"][0]["account_id"] = 94637590
        self.data["accounts"][1]["bypass_mode"] = "pull_request"
        with self.assertRaisesRegex(BypassPolicyError, "AUTHORIZED_BYPASS_MODE_UNEXPECTED"):
            load_bypass_configuration(self.save())

    def test_repository_and_scope_must_match(self):
        self.complete_app()
        self.data["scope"] = "someone-else/repo"
        with self.assertRaisesRegex(BypassPolicyError, "BYPASS_SCOPE_INVALID"):
            load_bypass_configuration(self.save())

    def test_live_principal_readback_requires_correct_app_and_repo(self):
        self.complete_app()
        class Client:
            def __init__(self):
                self.responses = {
                    "/users/Wealthtechinnovations": {"login": "Wealthtechinnovations", "id": 94637590},
                    "/users/Patricked-code": {"login": "Patricked-code", "id": 270385782},
                    "/orgs/chainsolutions-wealthtech": {"login": "chainsolutions-wealthtech", "id": 299685687},
                    "/repos/chainsolutions-wealthtech/universal-agent-engineering-system/collaborators/Wealthtechinnovations/permission": {"permission": "admin"},
                    "/repos/chainsolutions-wealthtech/universal-agent-engineering-system/collaborators/Patricked-code/permission": {"permission": "admin"},
                    "/apps/uaes-test-app": {"id": 123456, "slug": "uaes-test-app"},
                    "/user/installations?per_page=100": {"total_count": 1, "installations": [
                        {"id": 9988, "app_id": 123456, "account": {
                            "login": "chainsolutions-wealthtech", "id": 299685687}}]},
                    "/user/installations/9988/repositories?per_page=100": {
                        "total_count": 1, "repositories": [{"full_name":
                            "chainsolutions-wealthtech/universal-agent-engineering-system"}]},
                }
            def request(self, method, path):
                return self.responses[path]
        client = Client()
        self.assertTrue(verify_bypass_principals(client, self.data))
        client.responses["/apps/uaes-test-app"] = {"id": 123457, "slug": "uaes-test-app"}
        with self.assertRaisesRegex(BypassPolicyError, "GITHUB_APP_IDENTITY_UNVERIFIED"):
            verify_bypass_principals(client, self.data)
        client.responses["/apps/uaes-test-app"] = {"id": 123456, "slug": "uaes-test-app"}
        client.responses["/user/installations/9988/repositories?per_page=100"] = {
            "total_count": 0, "repositories": []}
        with self.assertRaisesRegex(BypassPolicyError, "APP_NOT_INSTALLED_ON_UAES"):
            verify_bypass_principals(client, self.data)


if __name__ == "__main__":
    unittest.main()
