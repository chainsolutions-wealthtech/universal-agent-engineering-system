"""Authorize, bind and reconcile effects with task claims; no external calls."""
import json,time
from src.effect_journal import EffectJournal

class EffectCoordinator:
    def __init__(self,engine):
        self.engine=engine
        self.journal=EffectJournal(engine.db)
        engine.db.execute("""CREATE TABLE IF NOT EXISTS effect_bindings(
           effect_id TEXT PRIMARY KEY, task_id TEXT NOT NULL,
           agent_id TEXT NOT NULL, mandate_id TEXT NOT NULL,
           fencing INTEGER NOT NULL, FOREIGN KEY(effect_id) REFERENCES effects(id))""")

    def prepare(self,task_id,agent_id,mandate_id,fencing,target,operation,key):
        now=time.time()
        self.engine.db.execute("BEGIN IMMEDIATE")
        try:
            row=self.engine.db.execute("""SELECT 1 FROM tasks t JOIN mandates m
              ON m.id=t.claim_mandate WHERE t.id=? AND t.state='CLAIMED'
              AND t.claim_owner=? AND t.claim_mandate=? AND t.fencing=?
              AND t.claim_expiry>? AND m.agent_id=? AND m.project_id=t.project_id
              AND m.scope=t.action AND m.revoked=0 AND m.expires>?""",
              (task_id,agent_id,mandate_id,fencing,now,agent_id,now)).fetchone()
            if not row: raise PermissionError("task claim or mandate not effective")
            # A savepoint permits the existing journal transaction to be nested safely.
            self.engine.db.execute("COMMIT")
        except Exception:
            self.engine.db.execute("ROLLBACK")
            raise
        eid=self.journal.prepare(task_id,target,operation,key)
        existing=self.engine.db.execute("SELECT task_id,agent_id,mandate_id,fencing FROM effect_bindings WHERE effect_id=?",(eid,)).fetchone()
        if existing and existing!=(task_id,agent_id,mandate_id,fencing):
            raise PermissionError("idempotency key bound to another claim")
        self.engine.db.execute("INSERT OR IGNORE INTO effect_bindings VALUES(?,?,?,?,?)",
                               (eid,task_id,agent_id,mandate_id,fencing))
        return eid

    def completion_gate(self,task_id):
        rows=self.engine.db.execute("""SELECT e.state FROM effects e
           JOIN effect_bindings b ON b.effect_id=e.id WHERE b.task_id=?""",(task_id,)).fetchall()
        if not rows: return {"admissible":False,"reason":"NO_EFFECT_RECEIPT"}
        if any(r[0]!="CONFIRMED" for r in rows):
            return {"admissible":False,"reason":"UNRESOLVED_EFFECT"}
        return {"admissible":True,"reason":"ALL_EFFECTS_CONFIRMED"}
