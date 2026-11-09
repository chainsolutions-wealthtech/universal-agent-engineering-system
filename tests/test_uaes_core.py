import tempfile, unittest
from pathlib import Path
from src.uaes_core import Engine

class CoreTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.path=Path(self.tmp.name)/"core.sqlite"
  self.e=Engine(self.path)
  self.a=self.e.agent("synthetic")
  self.m=self.e.mandate(self.a,"fixture","analyze")
 def tearDown(self): self.e.db.close();self.tmp.cleanup()
 def test_claim_complete_reopen(self):
  t=self.e.submit("fixture","analyze",{"ref":"synthetic"})
  token=self.e.claim(t,self.a,self.m)
  with self.assertRaises(ValueError): self.e.claim(t,self.a,self.m)
  with self.assertRaises(PermissionError): self.e.complete(t,self.a,token+1,{"ok":True})
  self.e.complete(t,self.a,token,{"ok":True})
  self.assertEqual(Engine(self.path).checkpoint()["tasks"],[("DONE",1)])
 def test_denied_without_mandate(self):
  t=self.e.submit("fixture","analyze",{})
  with self.assertRaises(PermissionError): self.e.claim(t,self.a,"missing")
  self.e.revoke(self.m)
  with self.assertRaises(PermissionError): self.e.claim(t,self.a,self.m)
 def test_revoked_after_claim_cannot_complete(self):
  t=self.e.submit("fixture","analyze",{})
  token=self.e.claim(t,self.a,self.m)
  self.e.revoke(self.m)
  with self.assertRaises(PermissionError): self.e.complete(t,self.a,token,{"ok":True})
  self.assertEqual(self.e.db.execute("SELECT state FROM tasks WHERE id=?",(t,)).fetchone()[0],"CLAIMED")
 def test_expired_after_claim_cannot_complete(self):
  t=self.e.submit("fixture","analyze",{})
  token=self.e.claim(t,self.a,self.m)
  self.e.db.execute("UPDATE mandates SET expires=0 WHERE id=?",(self.m,))
  with self.assertRaises(PermissionError): self.e.complete(t,self.a,token,{"ok":True})
 def test_reclaim_expired_lease_fences_old_worker(self):
  other=self.e.agent("second")
  other_mandate=self.e.mandate(other,"fixture","analyze")
  t=self.e.submit("fixture","analyze",{})
  first=self.e.claim(t,self.a,self.m)
  self.e.db.execute("UPDATE tasks SET claim_expiry=0 WHERE id=?",(t,))
  second=self.e.claim(t,other,other_mandate)
  self.assertGreater(second,first)
  with self.assertRaises(PermissionError): self.e.complete(t,self.a,first,{"bad":True})
  self.e.complete(t,other,second,{"ok":True})
  self.assertEqual(self.e.db.execute("SELECT count(*) FROM events WHERE kind='task.completed'").fetchone()[0],1)
 def test_renew_requires_current_lease_and_mandate(self):
  t=self.e.submit("fixture","analyze",{})
  token=self.e.claim(t,self.a,self.m)
  self.e.renew(t,self.a,self.m,token)
  self.e.revoke(self.m)
  with self.assertRaises(PermissionError): self.e.renew(t,self.a,self.m,token)
 def test_dedupe(self):
  self.e.submit("fixture","analyze",{})
  with self.assertRaises(Exception): self.e.submit("fixture","analyze",{})
if __name__=="__main__":unittest.main()
