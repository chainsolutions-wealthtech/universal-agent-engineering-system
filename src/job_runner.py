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
    def recover(self):
        """Read local continuity after restart; never auto-authorize/replay."""
        if not self.continuity_id:
            return None
        return self.engine.resume()

    def checkpoint(self):
        """Persist an atomic local continuity checkpoint if enabled."""
        if not self.continuity_id:
            return None
        return self.engine.checkpoint()

    def run_once(self,agent_id,mandate_id):
        now=time.time()
        # Exclude effect-bound candidates before LIMIT, without requiring a
        # journal table in legacy databases that have never used effects.
        has_effect=self.engine.db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='effects'").fetchone()
        effect_filter=(" AND NOT EXISTS (SELECT 1 FROM effects AS e WHERE e.task_id=t.id)"
                       if has_effect else "")
        # Recover only local deterministic actions; no unknown external effect replay.
        if self.continuity_id:
            # Apply continuity eligibility before LIMIT; otherwise 50 unrelated
            # READY tasks can starve a later bound task indefinitely. Also apply\n            # the effective mandate before LIMIT so unrelated bound tasks cannot\n            # starve the eligible project; claim() still enforces authority.
            rows=self.engine.db.execute("""SELECT t.id,t.action FROM tasks AS t
              WHERE (t.state='READY' OR (t.state='CLAIMED' AND t.claim_expiry<=?))
              AND EXISTS (SELECT 1 FROM continuity_links AS l
                WHERE l.continuity_id=? AND l.kind='task' AND l.object_id=t.id)
              AND EXISTS (SELECT 1 FROM mandates AS m
                WHERE m.id=? AND m.agent_id=? AND m.project_id=t.project_id
                AND m.scope=t.action AND m.revoked=0 AND m.expires>?)
              AND t.action IN ('analyze','validate')
              """ + effect_filter + """ ORDER BY t.rowid LIMIT 50""",
              (now,self.continuity_id,mandate_id,agent_id,now)).fetchall()
        else:
            # Preserve unscoped operation, but prefilter the current mandate
            # before LIMIT; Engine.claim() remains the final authorization gate.
            rows=self.engine.db.execute("""SELECT t.id,t.action FROM tasks AS t WHERE (t.state='READY'
              OR (t.state='CLAIMED' AND t.claim_expiry<=?))
              AND EXISTS (SELECT 1 FROM mandates AS m
                WHERE m.id=? AND m.agent_id=? AND m.project_id=t.project_id
                AND m.scope=t.action AND m.revoked=0 AND m.expires>?)
              AND t.action IN ('analyze','validate')
              """ + effect_filter + """ ORDER BY t.rowid LIMIT 50""",
              (now,mandate_id,agent_id,now)).fetchall()
        for tid,action in rows:
            if action not in ("analyze","validate"): continue
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
