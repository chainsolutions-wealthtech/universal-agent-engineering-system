"""Regression tests for additive UAES continuity correlation."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from src.continuity_link import ContinuityEngine, ROOT_ID, ROOT_SOURCE

class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "uaes.sqlite"
        self.engine = ContinuityEngine(self.path)

    def tearDown(self):
        self.engine.db.close()
        self.tmp.cleanup()

    def test_end_to_end_restart_and_existing_authority(self):
        e = self.engine
        agent = e.agent("coding-agent")
        mandate = e.mandate(agent,"project-a","analyze")
        task = e.submit("project-a","analyze",{"value":1})
        fencing = e.claim(task,agent,mandate)
        e.complete(task,agent,fencing,{"ok":True})
        checkpoint = e.checkpoint()
        self.assertEqual(checkpoint["continuity_id"],ROOT_ID)
        self.assertGreater(checkpoint["event_watermark"],0)
        e.db.close()
        resumed = ContinuityEngine(self.path)
        self.engine = resumed
        result = resumed.resume()
        self.assertEqual(result["source"],ROOT_SOURCE)
        self.assertEqual(result["tasks"][0]["state"],"DONE")
        self.assertEqual(result["checkpoint"]["id"],checkpoint["checkpoint_id"])
        kinds = {item["kind"] for item in result["links"]}
        self.assertTrue({"agent","mandate","task","event","checkpoint"} <= kinds)
        self.assertEqual(resumed.db.execute(
            "SELECT COUNT(*) FROM tasks WHERE id=?",(task,)).fetchone()[0],1)

    def test_runner_resumes_only_bound_tasks_after_restart(self):
        from src.job_runner import JobRunner
        e = self.engine
        agent = e.agent("authorized-agent")
        mandate = e.mandate(agent,"project-x","analyze")
        bound = e.submit("project-x","analyze",{"bound":True})
        from src.uaes_core import Engine
        legacy = Engine(self.path)
        unbound = legacy.submit("project-y","analyze",{"unbound":True})
        legacy.db.close()
        e.db.close()
        runner = JobRunner(self.path,ROOT_ID,ROOT_SOURCE)
        try:
            item = runner.run_once(agent,mandate)
            self.assertEqual(item["task_id"],bound)
            self.assertIsNone(runner.run_once(agent,mandate))
            self.assertEqual(runner.engine.db.execute(
                "SELECT state FROM tasks WHERE id=?",(unbound,)).fetchone()[0],"READY")
            self.assertEqual(runner.engine.resume()["tasks"][0]["state"],"DONE")
            runner.engine.checkpoint()
        finally:
            runner.close()
        self.engine = ContinuityEngine(self.path)
        self.assertIsNotNone(self.engine.resume()["checkpoint"])

    def test_daemon_restart_preserves_continuity_and_no_replay(self):
        from src.daemon import Daemon
        e=self.engine
        agent=e.agent("daemon-agent")
        mandate=e.mandate(agent,"daemon-project","validate")
        task=e.submit("daemon-project","validate",{"value":1})
        e.db.close()
        first=Daemon(self.path,agent,mandate,interval=0,continuity_id=ROOT_ID,
                     continuity_source=ROOT_SOURCE)
        self.assertIsNotNone(first.once())
        first_checkpoint=first.stats["checkpoint_id"]
        self.assertTrue(first.stats["continuity_recovered"])
        self.assertIsNotNone(first_checkpoint)
        restarted=Daemon(self.path,agent,mandate,interval=0,continuity_id=ROOT_ID,
                         continuity_source=ROOT_SOURCE)
        self.assertIsNone(restarted.once())
        self.assertTrue(restarted.stats["continuity_recovered"])
        self.assertGreater(restarted.stats["checkpoint_id"],first_checkpoint)
        self.engine=ContinuityEngine(self.path)
        self.assertEqual(self.engine.resume()["tasks"][0]["state"],"DONE")
        self.assertEqual(self.engine.db.execute(
            "SELECT COUNT(*) FROM tasks WHERE id=?",(task,)).fetchone()[0],1)

    def test_link_failure_rolls_back_task_and_event(self):
        e=self.engine
        before=e.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        original=e.link
        def fail(kind, object_id):
            if kind == "task":
                raise RuntimeError("simulated correlation failure")
            return original(kind,object_id)
        e.link=fail
        with self.assertRaises(RuntimeError):
            e.submit("project-rollback","analyze",{})
        e.link=original
        self.assertEqual(e.db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],0)
        self.assertEqual(e.db.execute("SELECT COUNT(*) FROM events").fetchone()[0],before)

    def test_checkpoint_failure_rolls_back_snapshot(self):
        e=self.engine
        original=e.link
        def fail(kind, object_id):
            if kind == "checkpoint":
                raise RuntimeError("simulated checkpoint failure")
            return original(kind,object_id)
        e.link=fail
        with self.assertRaises(RuntimeError):
            e.checkpoint()
        e.link=original
        self.assertEqual(e.db.execute(
            "SELECT COUNT(*) FROM continuity_checkpoints").fetchone()[0],0)

    def test_idempotent_link_and_no_parallel_task(self):
        e=self.engine
        task=e.submit("project-b","validate",{})
        e.bind_existing("task",task)
        e.bind_existing("task",task)
        self.assertEqual(e.db.execute(
            "SELECT COUNT(*) FROM continuity_links WHERE kind='task' AND object_id=?",
            (task,)).fetchone()[0],1)
        self.assertEqual(e.db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],1)

    def test_missing_local_authority_fails_closed(self):
        with self.assertRaises(ValueError):
            self.engine.bind_existing("task","invented-task")
        with self.assertRaises(ValueError):
            self.engine.bind_existing("agent","invented-agent")

    def test_checkpoint_link_rejects_missing_or_foreign_root(self):
        e = self.engine
        with self.assertRaises(ValueError):
            e.bind_existing("checkpoint", 987654321)
        another = ContinuityEngine(self.path, "independent-root",
                                   "https://github.com/chainsolutions-wealthtech/universal-agent-engineering-system/issues/6#independent")
        try:
            foreign_checkpoint = another.checkpoint()["checkpoint_id"]
        finally:
            another.db.close()
        with self.assertRaises(ValueError):
            e.bind_existing("checkpoint", foreign_checkpoint)
        self.assertEqual(e.db.execute(
            "SELECT COUNT(*) FROM continuity_links WHERE kind='checkpoint'").fetchone()[0], 0)

    def test_revoke_event_link_failure_rolls_back_revocation(self):
        e = self.engine
        agent = e.agent("revocation-test-agent")
        mandate = e.mandate(agent, "revocation-project", "analyze")
        before = e.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        original = e.link
        def fail(kind, object_id):
            if kind == "event":
                raise RuntimeError("simulated event-link failure")
            return original(kind, object_id)
        e.link = fail
        try:
            with self.assertRaises(RuntimeError):
                e.revoke(mandate)
        finally:
            e.link = original
        self.assertEqual(e.db.execute(
            "SELECT revoked FROM mandates WHERE id=?", (mandate,)).fetchone()[0], 0)
        self.assertEqual(e.db.execute("SELECT COUNT(*) FROM events").fetchone()[0], before)
        e.revoke(mandate)
        self.assertEqual(e.db.execute(
            "SELECT revoked FROM mandates WHERE id=?", (mandate,)).fetchone()[0], 1)
        self.assertEqual(e.db.execute(
            """SELECT COUNT(*) FROM continuity_links l JOIN events v ON v.seq=l.object_id
               WHERE l.kind='event' AND v.kind='mandate.revoked' AND v.subject=?""",
            (mandate,)).fetchone()[0], 1)

    def test_reject_rebinding_source(self):
        with self.assertRaises(ValueError):
            ContinuityEngine(self.path,ROOT_ID,"https://example.org/other")

    def test_original_engine_can_read_additive_schema(self):
        from src.uaes_core import Engine
        old=Engine(self.path)
        try:
            self.assertIn("tasks",old.checkpoint())
        finally:
            old.db.close()

if __name__ == "__main__":
    unittest.main()
