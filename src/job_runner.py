"""Durable local job runner: one bounded work item per invocation, no remote writes."""
import json,time
from src.uaes_core import Engine
from src.continuity_link import ContinuityEngine, ROOT_SOURCE
from src.uaes_worker import Worker

class JobRunner:
    def __init__(self,db_path,continuity_id=None,continuity_source=None):
        self.engine=(ContinuityEngine(db_path,continuity_id,continuity_source or ROOT_SOURCE)
                     if continuity_id else Engine(db_path))
        self.continuity_id=continuity_id
    def run_once(self,agent_id,mandate_id):
        now=time.time()
        # Recover only local deterministic actions; no unknown external effect replay.
        rows=self.engine.db.execute("""SELECT id,action FROM tasks WHERE state='READY'
          OR (state='CLAIMED' AND claim_expiry<=?) ORDER BY rowid LIMIT 50""",(now,)).fetchall()
        for tid,action in rows:
            if self.continuity_id:
                bound=self.engine.db.execute(
                    "SELECT 1 FROM continuity_links WHERE continuity_id=? AND kind='task' AND object_id=?",
                    (self.continuity_id,tid)).fetchone()
                if not bound:
                    continue
            if action not in ("analyze","validate"): continue
            has_effect=self.engine.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='effects'").fetchone()
            if has_effect and self.engine.db.execute(
                "SELECT 1 FROM effects WHERE task_id=? LIMIT 1",(tid,)).fetchone():
                continue  # External/uncertain effects always need independent reconciliation.
            try:
                return Worker(self.engine,agent_id,mandate_id).execute(tid)
            except (PermissionError, ValueError):
                continue
        return None
    def close(self):
        self.engine.db.close()
