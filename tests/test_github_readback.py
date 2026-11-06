import io
import json
import unittest
import urllib.error

from src.github_readback import GitHubCommitReadback, classify_repository_snapshot
from src.receipt_verifier import ReadbackVerifier

SHA="a"*40

class _Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self,*args): self.close()

class GitHubReadbackTests(unittest.TestCase):
    def test_authenticated_commit_readback_matches_target(self):
        opened=[]
        def fake_open(req, timeout):
            opened.append(req)
            return _Response(json.dumps({"sha":SHA}).encode())
        adapter=GitHubCommitReadback(lambda:"test-only-token",fake_open)
        result=ReadbackVerifier(adapter).inspect({
            "target":"example/fixture","operation":"commit_exists","idempotency_key":SHA
        })
        self.assertEqual(result["status"],"CONFIRMED")
        self.assertEqual(result["proof"],"example/fixture@"+SHA)
        self.assertEqual(opened[0].get_method(),"GET")
    def test_remote_absence_must_remain_unknown(self):
        def missing(req,timeout):
            raise urllib.error.HTTPError(req.full_url,404,"not found",{},None)
        adapter=GitHubCommitReadback(lambda:"test-only-token",missing)
        result=ReadbackVerifier(adapter).inspect({
            "target":"example/fixture","operation":"commit_exists","idempotency_key":SHA
        })
        self.assertEqual(result["status"],"UNKNOWN")
    def test_unsupported_or_tokenless_is_denied(self):
        adapter=GitHubCommitReadback(lambda:None,lambda *args:None)
        with self.assertRaises(PermissionError):
            adapter.readback("example/fixture","commit_exists",SHA)
        with self.assertRaises(PermissionError):
            adapter.readback("example/fixture","create_issue",SHA)
        with self.assertRaises(PermissionError):
            adapter.readback("https://other.invalid/x","commit_exists",SHA)
    def test_wrong_commit_sha_never_confirmed(self):
        adapter=GitHubCommitReadback(lambda:"test",lambda req,timeout:_Response(json.dumps({"sha":"b"*40}).encode()))
        self.assertEqual(ReadbackVerifier(adapter).inspect({
            "target":"example/fixture","operation":"commit_exists","idempotency_key":SHA
        })["status"],"UNKNOWN")

class RepositorySnapshotTests(unittest.TestCase):
    def fixture(self):
        return (
            {"full_name": "example/fixture"},
            {"commit": {"sha": SHA}, "protected": False},
            {"head": {"sha": "b"*40}, "state": "open", "draft": True},
            [{"id": 3, "name": "core-tests", "head_sha": "b"*40,
              "status": "completed", "conclusion": "success"},
             {"id": 4, "name": "core-tests", "head_sha": "b"*40,
              "status": "completed", "conclusion": "failure"},
             {"id": 5, "name": "core-tests", "head_sha": "c"*40,
              "status": "completed", "conclusion": "success"}],
            [],
        )

    def test_read_only_projection_preserves_provenance_and_latest_check(self):
        result = classify_repository_snapshot(*self.fixture())
        self.assertEqual(result["status"], "OBSERVED")
        self.assertFalse(result["main_protected"])
        self.assertEqual(result["ruleset_count"], 0)
        self.assertEqual(result["pull"]["head_sha"], "b"*40)
        self.assertEqual(result["check_runs_latest"]["core-tests"]["id"], 4)
        self.assertEqual(result["check_runs_latest"]["core-tests"]["conclusion"], "failure")
        self.assertEqual(result["authorization"], "NOT_DERIVED_FROM_READBACK")
        self.assertEqual(result["runtime"], "NOT_ATTESTED_BY_READBACK")

    def test_missing_evidence_never_becomes_false_or_zero(self):
        repo, branch, pull, checks, rules = self.fixture()
        self.assertEqual(classify_repository_snapshot(repo, {}, pull, checks, rules)["status"], "UNKNOWN")
        self.assertEqual(classify_repository_snapshot(repo, branch, pull, None, rules)["reason"], "PR_CHECKS_UNVERIFIED")
        self.assertEqual(classify_repository_snapshot(repo, branch, pull, checks, None)["reason"], "RULESETS_UNVERIFIED")
        branch["protected"] = None
        self.assertEqual(classify_repository_snapshot(repo, branch, pull, checks, rules)["reason"], "BRANCH_PROTECTION_UNVERIFIED")

    def test_unrequested_pull_does_not_fabricate_checks(self):
        repo, branch, pull, checks, rules = self.fixture()
        result = classify_repository_snapshot(repo, branch, None, None, rules)
        self.assertEqual(result["pull"], "NOT_REQUESTED")
        self.assertNotIn("check_runs_latest", result)

    def test_malformed_or_wrong_head_checks_are_not_success(self):
        repo, branch, pull, checks, rules = self.fixture()
        pull["head"]["sha"] = "c"*40
        result = classify_repository_snapshot(repo, branch, pull, checks, rules)
        self.assertEqual(result["check_runs_latest"]["core-tests"]["id"], 5)
        pull["head"]["sha"] = "invalid"
        self.assertEqual(classify_repository_snapshot(repo, branch, pull, checks, rules)["reason"], "PR_HEAD_SHA_UNVERIFIED")

if __name__=="__main__": unittest.main()
