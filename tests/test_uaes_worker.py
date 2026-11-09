import tempfile,unittest
from pathlib import Path
from src.uaes_core import Engine
from src.uaes_worker import Worker,resume_completed

class WorkerTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.path=Path(self.temp.name)/"tasks.sqlite"
  self.e=Engine(self.path)
  self.agent=self.e.agent("fixture-agent")
  self.mandate=self.e.mandate(self.agent,"fixture","analyze")
 def tearDown(self):
  self.e.db.close(); self.temp.cleanup()
 def test_end_to_end_resume_without_duplicate_effect(self):
  tid=self.e.submit("fixture","analyze",{"source":"synthetic"})
  r=Worker(self.e,self.agent,self.mandate).execute(tid)
  self.assertEqual(r["result"]["payload_keys"],["source"])
  self.e.db.close()
  self.e=Engine(self.path)
  state=resume_completed(self.e,tid)
  self.assertEqual(state["status"],"DONE")
  self.assertTrue(state["reconciled"])
  with self.assertRaises(ValueError): Worker(self.e,self.agent,self.mandate).execute(tid)
  self.assertEqual(self.e.db.execute("SELECT count(*) FROM events WHERE kind='task.completed'").fetchone()[0],1)
 def test_worker_cannot_run_unapproved_action(self):
  tid=self.e.submit("fixture","shell",{"command":"echo test"})
  with self.assertRaises(PermissionError): Worker(self.e,self.agent,self.mandate).execute(tid)
  self.assertEqual(resume_completed(self.e,tid)["status"],"READY")
 def test_cross_scope_mandate_denied(self):
  tid=self.e.submit("other","analyze",{})
  with self.assertRaises(PermissionError): Worker(self.e,self.agent,self.mandate).execute(tid)
if __name__=="__main__":unittest.main()
