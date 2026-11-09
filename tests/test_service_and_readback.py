import tempfile,unittest
from pathlib import Path
from src.receipt_verifier import ReadbackVerifier,SyntheticReadbackAdapter
from src.worker_service import WorkerService
from src.uaes_core import Engine

class ReadbackTests(unittest.TestCase):
 def test_known_synthetic_effect(self):
  intent={"target":"fixture","operation":"create","idempotency_key":"k"}
  check=ReadbackVerifier(SyntheticReadbackAdapter({("fixture","create","k"):"CONFIRMED"}))
  self.assertEqual(check.inspect(intent)["status"],"CONFIRMED")
 def test_unknown_cannot_confirm(self):
  result=ReadbackVerifier(SyntheticReadbackAdapter({})).inspect(
      {"target":"fixture","operation":"create","idempotency_key":"k"})
  self.assertEqual(result["status"],"UNKNOWN")
  self.assertTrue(result["requires_reconciliation"])
 def test_mismatched_proof_rejected(self):
  class Forged:
   def readback(self,*args):
    from src.receipt_verifier import VerifiedObservation
    return VerifiedObservation("fixture","other","create","k","CONFIRMED","fake")
  with self.assertRaises(PermissionError):
   ReadbackVerifier(Forged()).inspect(
       {"target":"fixture","operation":"create","idempotency_key":"k"})

class WorkerServiceTests(unittest.TestCase):
 def test_bounded_restartable_worker(self):
  with tempfile.TemporaryDirectory() as p:
   db=Path(p)/"jobs.sqlite"
   engine=Engine(db)
   agent=engine.agent("fixture")
   mandate=engine.mandate(agent,"fixture","validate")
   task=engine.submit("fixture","validate",{"ok":1})
   engine.db.close()
   first=WorkerService(db,agent,mandate,poll_seconds=.001,max_iterations=1).run()
   self.assertEqual(first["completed"],[task])
   second=WorkerService(db,agent,mandate,poll_seconds=.001,max_iterations=1).run()
   self.assertEqual(second["completed"],[])
if __name__=="__main__":unittest.main()
