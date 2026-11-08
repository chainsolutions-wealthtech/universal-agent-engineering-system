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
 def test_restart_preserves_uncertain_effect_and_runs_later_safe_task(self):
  """A restarted worker must not replay an uncertain effect or starve safe work."""
  with tempfile.TemporaryDirectory() as folder:
   file=Path(folder)/"db.sqlite"
   runner=JobRunner(file)
   agent=runner.engine.agent("restart-effect-agent")
   blocked=runner.engine.submit("blocked-project","analyze",{"unsafe":True})
   journal=EffectJournal(runner.engine.db)
   effect=journal.prepare(blocked,"remote","mutation","restart-effect-key")
   journal.dispatch(effect)
   runner.close()
   runner=JobRunner(file)
   mandate=runner.engine.mandate(agent,"safe-project","analyze")
   safe=runner.engine.submit("safe-project","analyze",{"safe":True})
   result=runner.run_once(agent,mandate)
   self.assertIsNotNone(result)
   self.assertEqual(result["task_id"],safe)
   self.assertEqual(runner.engine.db.execute(
       "SELECT state FROM tasks WHERE id=?",(blocked,)).fetchone()[0],"READY")
   self.assertEqual(runner.engine.db.execute(
       "SELECT COUNT(*) FROM effects WHERE task_id=?",(blocked,)).fetchone()[0],1)
   self.assertEqual(runner.engine.db.execute(
       "SELECT COUNT(*) FROM events WHERE kind='task.completed'").fetchone()[0],1)
   runner.close()
 def test_continuity_filter_precedes_bounded_candidate_limit(self):
  """A bound 51st task must not starve behind 50 unrelated READY tasks."""
  from src.uaes_core import Engine
  from src.continuity_link import ROOT_ID
  with tempfile.TemporaryDirectory() as folder:
   file=Path(folder)/"db.sqlite"
   legacy=Engine(file)
   for index in range(50):
    legacy.submit(f"unrelated-{index}","analyze",{"index":index})
   legacy.db.close()
   runner=JobRunner(file,continuity_id=ROOT_ID)
   agent=runner.engine.agent("continuity-agent")
   mandate=runner.engine.mandate(agent,"eligible-project","analyze")
   eligible=runner.engine.submit("eligible-project","analyze",{"expected":"bound"})
   self.assertEqual(runner.engine.db.execute(
       "SELECT COUNT(*) FROM tasks WHERE state='READY'").fetchone()[0],51)
   result=runner.run_once(agent,mandate)
   self.assertIsNotNone(result)
   self.assertEqual(result["task_id"],eligible)
   self.assertEqual(runner.engine.db.execute(
       "SELECT state FROM tasks WHERE id=?",(eligible,)).fetchone()[0],"DONE")
   self.assertEqual(runner.engine.db.execute(
       "SELECT COUNT(*) FROM tasks WHERE state='READY'").fetchone()[0],50)
   runner.close()
 def test_continuity_mandate_filter_precedes_candidate_limit(self):
  """Fifty bound tasks with the wrong project must not starve an authorized task."""
  from src.continuity_link import ROOT_ID
  with tempfile.TemporaryDirectory() as folder:
   runner=JobRunner(Path(folder)/"db.sqlite",continuity_id=ROOT_ID)
   agent=runner.engine.agent("scoped-agent")
   mandate=runner.engine.mandate(agent,"authorized-project","analyze")
   for index in range(50):
    runner.engine.submit(f"wrong-project-{index}","analyze",{"index":index})
   eligible=runner.engine.submit("authorized-project","analyze",{"expected":"authorized"})
   result=runner.run_once(agent,mandate)
   self.assertIsNotNone(result)
   self.assertEqual(result["task_id"],eligible)
   self.assertEqual(runner.engine.db.execute(
       "SELECT COUNT(*) FROM tasks WHERE state='READY'").fetchone()[0],50)
   runner.close()
 def test_legacy_mandate_filter_precedes_candidate_limit(self):
  """Fifty unrelated READY tasks cannot hide the first mandated legacy task."""
  with tempfile.TemporaryDirectory() as folder:
   runner=JobRunner(Path(folder)/"db.sqlite")
   agent=runner.engine.agent("legacy-scoped-agent")
   mandate=runner.engine.mandate(agent,"permitted","analyze")
   for index in range(50):
    runner.engine.submit(f"unpermitted-{index}","analyze",{"index":index})
   eligible=runner.engine.submit("permitted","analyze",{"safe":True})
   result=runner.run_once(agent,mandate)
   self.assertIsNotNone(result)
   self.assertEqual(result["task_id"],eligible)
   self.assertEqual(runner.engine.db.execute("SELECT COUNT(*) FROM tasks WHERE state='READY'").fetchone()[0],50)
   runner.close()
 def test_effect_blocked_tasks_do_not_starve_eligible_legacy_task(self):
  """Fifty effect-blocked READY tasks cannot hide a later safe task."""
  with tempfile.TemporaryDirectory() as folder:
   runner=JobRunner(Path(folder)/"db.sqlite")
   agent=runner.engine.agent("effect-safe-agent")
   journal=EffectJournal(runner.engine.db)
   for index in range(50):
    tid=runner.engine.submit(f"blocked-project-{index}","analyze",{"index":index})
    eid=journal.prepare(tid,"remote","mutation",f"blocked-key-{index}")
    journal.dispatch(eid)
   eligible=runner.engine.submit("eligible-project","analyze",{"safe":True})
   eligible_mandate=runner.engine.mandate(agent,"eligible-project","analyze")
   result=runner.run_once(agent,eligible_mandate)
   self.assertIsNotNone(result)
   self.assertEqual(result["task_id"],eligible)
   self.assertEqual(runner.engine.db.execute("SELECT COUNT(*) FROM tasks WHERE state='READY'").fetchone()[0],50)
   runner.close()

 def test_effect_blocked_tasks_do_not_starve_eligible_continuity_task(self):
  """Fifty distinct effect-bound projects do not block a later mandated linked task."""
  from src.continuity_link import ROOT_ID
  with tempfile.TemporaryDirectory() as folder:
   runner=JobRunner(Path(folder)/"db.sqlite",continuity_id=ROOT_ID)
   agent=runner.engine.agent("continuity-effect-agent")
   mandate=runner.engine.mandate(agent,"shared-project","analyze")
   journal=EffectJournal(runner.engine.db)
   for index in range(50):
    tid=runner.engine.submit(f"blocked-project-{index}","analyze",{"index":index})
    eid=journal.prepare(tid,"remote","mutation",f"continuity-blocked-{index}")
    journal.dispatch(eid)
   eligible=runner.engine.submit("shared-project","analyze",{"safe":True})
   result=runner.run_once(agent,mandate)
   self.assertIsNotNone(result)
   self.assertEqual(result["task_id"],eligible)
   self.assertEqual(runner.engine.db.execute(
       "SELECT COUNT(*) FROM tasks WHERE state='READY'").fetchone()[0],50)
   runner.close()

 def test_restart_preserves_revoked_mandate_and_does_not_claim_task(self):
  """A restarted worker must not revive authorization revoked before shutdown."""
  with tempfile.TemporaryDirectory() as folder:
   file=Path(folder)/"db.sqlite"
   runner=JobRunner(file)
   agent=runner.engine.agent("revoked-restart-agent")
   mandate=runner.engine.mandate(agent,"revoked-project","analyze")
   task=runner.engine.submit("revoked-project","analyze",{"safe":True})
   runner.engine.revoke(mandate)
   runner.close()
   runner=JobRunner(file)
   self.assertIsNone(runner.run_once(agent,mandate))
   self.assertEqual(runner.engine.db.execute(
       "SELECT state FROM tasks WHERE id=?",(task,)).fetchone()[0],"READY")
   self.assertEqual(runner.engine.db.execute(
       "SELECT COUNT(*) FROM events WHERE kind='task.claimed' AND subject=?",
       (task,)).fetchone()[0],0)
   self.assertEqual(runner.engine.db.execute(
       "SELECT COUNT(*) FROM events WHERE kind='task.completed' AND subject=?",
       (task,)).fetchone()[0],0)
   runner.close()

if __name__=="__main__":unittest.main()
