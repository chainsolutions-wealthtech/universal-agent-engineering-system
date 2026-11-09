import tempfile,unittest
from pathlib import Path
from src.job_runner import JobRunner
from src.effect_journal import EffectJournal

class RunnerTests(unittest.TestCase):
 def test_restart_persists_and_does_not_rerun_completed(self):
  with tempfile.TemporaryDirectory() as folder:
   file=Path(folder)/"db.sqlite"
   runner=JobRunner(file)
   a=runner.engine.agent("synthetic")
   m=runner.engine.mandate(a,"fixture","analyze")
   tid=runner.engine.submit("fixture","analyze",{"hello":"world"})
   runner.close()
   runner=JobRunner(file)
   self.assertEqual(runner.run_once(a,m)["task_id"],tid)
   runner.close()
   runner=JobRunner(file)
   self.assertIsNone(runner.run_once(a,m))
   self.assertEqual(runner.engine.db.execute(
       "SELECT count(*) FROM events WHERE kind='task.completed'").fetchone()[0],1)
   runner.close()
 def test_unknown_effect_blocks_replay(self):
  with tempfile.TemporaryDirectory() as folder:
   runner=JobRunner(Path(folder)/"db.sqlite")
   a=runner.engine.agent("a")
   m=runner.engine.mandate(a,"fixture","analyze")
   tid=runner.engine.submit("fixture","analyze",{})
   journal=EffectJournal(runner.engine.db)
   eid=journal.prepare(tid,"remote","mutation","test-key")
   journal.dispatch(eid)
   self.assertIsNone(runner.run_once(a,m))
   runner.close()
if __name__=="__main__":unittest.main()
