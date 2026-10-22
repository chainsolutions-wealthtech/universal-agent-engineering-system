import tempfile,unittest
from pathlib import Path
from src.uaes_core import Engine
from src.effect_coordinator import EffectCoordinator

class AtomicCompletionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.e=Engine(Path(self.tmp.name)/"db.sqlite")
  self.agent=self.e.agent("a")
  self.m=self.e.mandate(self.agent,"fixture","analyze")
  self.t=self.e.submit("fixture","analyze",{})
  self.f=self.e.claim(self.t,self.agent,self.m)
  self.c=EffectCoordinator(self.e)
 def tearDown(self):
  self.e.db.close();self.tmp.cleanup()
 def test_unconfirmed_effect_blocks_task(self):
  eid=self.c.prepare(self.t,self.agent,self.m,self.f,"sandbox","write","unique")
  with self.assertRaises(PermissionError):
   self.e.complete_with_effects(self.t,self.agent,self.f,{"ok":True})
  self.assertEqual(self.e.db.execute("SELECT state FROM tasks WHERE id=?",(self.t,)).fetchone()[0],"CLAIMED")
 def test_confirmed_effect_can_complete_atomically_in_fixture(self):
  eid=self.c.prepare(self.t,self.agent,self.m,self.f,"fixture","write","unique")
  self.c.journal.dispatch(eid)
  self.c.journal.resolve(eid,True,{"source":"synthetic-test-only","proof":"fixture-not-provider-attestation"})
  self.e.complete_with_effects(self.t,self.agent,self.f,{"ok":True})
  self.assertEqual(self.e.db.execute("SELECT state FROM tasks WHERE id=?",(self.t,)).fetchone()[0],"DONE")
if __name__=="__main__":unittest.main()
