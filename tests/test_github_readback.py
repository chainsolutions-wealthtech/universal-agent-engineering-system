import io
import json
import unittest
import urllib.error

from src.github_readback import GitHubCommitReadback
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
if __name__=="__main__": unittest.main()
