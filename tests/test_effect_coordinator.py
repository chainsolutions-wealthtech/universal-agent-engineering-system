import tempfile,unittest
from pathlib import Path
from src.uaes_core import Engine
from src.effect_coordinator import EffectCoordinator

class CoordinatorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.e=Engine(Path(self.tmp.name)/"db.sqlite")
  self.a=self.e.agent("a")
  self.m=self.e.mandate(self.a,"fixture","analyze")
  self.t=self.e.submit("fixture","analyze",{})
  self.f=self.e.claim(self.t,self.a,self.m)
  self.c=EffectCoordinator(self.e)
 def tearDown(self):
  self.e.db.close();self.tmp.cleanup()
 def test_uncertain_effect_is_not_completion_ready(self):
  eid=self.c.prepare(self.t,self.a,self.m,self.f,"sandbox","create","k1")
  self.assertEqual(self.c.completion_gate(self.t)["reason"],"UNRESOLVED_EFFECT")
  self.c.journal.dispatch(eid)
  self.c.journal.uncertain(eid)
  self.assertEqual(self.c.journal.recover(eid)["action"],"RECONCILE_REMOTE_READ_ONLY")
  self.assertFalse(self.c.completion_gate(self.t)["admissible"])
 def test_revoked_or_stale_claim_cannot_create_effect(self):
  self.e.revoke(self.m)
  with self.assertRaises(PermissionError):
   self.c.prepare(self.t,self.a,self.m,self.f,"sandbox","create","k2")
 def test_replay_key_cannot_switch_claim(self):
  eid=self.c.prepare(self.t,self.a,self.m,self.f,"sandbox","create","same-key")
  self.assertEqual(eid,self.c.prepare(self.t,self.a,self.m,self.f,"sandbox","create","same-key"))
  self.e.db.execute("UPDATE tasks SET claim_expiry=0 WHERE id=?",(self.t,))
  a2=self.e.agent("b")
  m2=self.e.mandate(a2,"fixture","analyze")
  f2=self.e.claim(self.t,a2,m2)
  with self.assertRaises(PermissionError):
   self.c.prepare(self.t,a2,m2,f2,"sandbox","create","same-key")
if __name__=="__main__":unittest.main()
