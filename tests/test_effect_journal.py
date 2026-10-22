import sqlite3,tempfile,unittest
from pathlib import Path
from src.effect_journal import EffectJournal

class EffectTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.file=Path(self.temp.name)/"effects.db"
  self.db=sqlite3.connect(self.file,isolation_level=None)
  self.j=EffectJournal(self.db)
 def tearDown(self):
  self.db.close();self.temp.cleanup()
 def test_crash_reopen_cannot_replay(self):
  e=self.j.prepare("task1","github:fixture","create_issue","fixed-key")
  self.j.dispatch(e)
  self.db.close()
  self.db=sqlite3.connect(self.file,isolation_level=None)
  self.j=EffectJournal(self.db)
  self.assertEqual(self.j.recover(e)["action"],"RECONCILE_REMOTE_READ_ONLY")
  with self.assertRaises(PermissionError): self.j.dispatch(e)
  self.j.uncertain(e)
  self.assertEqual(self.j.recover(e)["action"],"RECONCILE_REMOTE_READ_ONLY")
  self.assertEqual(self.j.resolve(e,True,{"source":"fixture","proof":"synthetic-confirmation"}),"CONFIRMED")
  self.assertEqual(self.j.recover(e)["state"],"CONFIRMED")
 def test_duplicate_key_same_operation(self):
  a=self.j.prepare("t","scope","action","key")
  self.assertEqual(a,self.j.prepare("t","scope","action","key"))
  with self.assertRaises(ValueError):self.j.prepare("t","different","action","key")
 def test_no_unverified_receipt(self):
  e=self.j.prepare("task1","target","operation","k")
  self.j.dispatch(e)
  with self.assertRaises(ValueError): self.j.resolve(e,True,{"source":"fixture"})
if __name__=="__main__":unittest.main()
