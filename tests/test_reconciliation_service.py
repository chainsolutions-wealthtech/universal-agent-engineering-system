import sqlite3,tempfile,unittest
from pathlib import Path
from src.effect_journal import EffectJournal
from src.receipt_verifier import SyntheticReadbackAdapter
from src.reconciliation_service import ReconciliationService

class ReconciliationTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory()
  self.db=sqlite3.connect(Path(self.t.name)/"effects.sqlite",isolation_level=None)
  self.j=EffectJournal(self.db)
 def tearDown(self):
  self.db.close();self.t.cleanup()
 def test_confirmed_synthetic_readback_and_idempotent_resume(self):
  eid=self.j.prepare("task","fixture","create","key")
  self.j.dispatch(eid)
  adapter=SyntheticReadbackAdapter({("fixture","create","key"):"CONFIRMED"})
  service=ReconciliationService(self.db,adapter)
  self.assertEqual(service.reconcile_once(),{"checked":1,"resolved":1,"unknown":0})
  self.assertEqual(service.reconcile_once(),{"checked":0,"resolved":0,"unknown":0})
  self.assertEqual(self.j.recover(eid)["state"],"CONFIRMED")
 def test_unknown_stays_blocked(self):
  eid=self.j.prepare("task","fixture","create","key")
  self.j.dispatch(eid)
  report=ReconciliationService(self.db,SyntheticReadbackAdapter({})).reconcile_once()
  self.assertEqual(report["unknown"],1)
  self.assertEqual(self.j.recover(eid)["action"],"RECONCILE_REMOTE_READ_ONLY")
 def test_batch_is_bounded(self):
  with self.assertRaises(ValueError):
   ReconciliationService(self.db,SyntheticReadbackAdapter({})).reconcile_once(0)
if __name__=="__main__":unittest.main()
