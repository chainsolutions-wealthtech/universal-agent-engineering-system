"""Durable effect intent journal. Never automatically replay unknown external effects."""
import json, sqlite3, time, uuid

class EffectJournal:
    def __init__(self, db):
        self.db=db
        self.db.execute("""CREATE TABLE IF NOT EXISTS effects(
          id TEXT PRIMARY KEY, idempotency_key TEXT NOT NULL UNIQUE,
          task_id TEXT NOT NULL, target TEXT NOT NULL, operation TEXT NOT NULL,
          state TEXT NOT NULL CHECK(state IN ('PREPARED','IN_FLIGHT','UNKNOWN','CONFIRMED','REJECTED')),
          receipt TEXT, created_at REAL NOT NULL, updated_at REAL NOT NULL)""")
    def prepare(self, task_id, target, operation, key):
        now=time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row=self.db.execute("SELECT id,task_id,target,operation FROM effects WHERE idempotency_key=?",(key,)).fetchone()
            if row:
                if row[1:]!=(task_id,target,operation): raise ValueError("idempotency key reused for different effect")
                eid=row[0]
            else:
                eid=str(uuid.uuid4())
                self.db.execute("INSERT INTO effects VALUES(?,?,?,?,?,'PREPARED',?,?,?)",
                                (eid,key,task_id,target,operation,None,now,now))
            self.db.execute("COMMIT")
            return eid
        except Exception:
            self.db.execute("ROLLBACK")
            raise
    def dispatch(self,eid):
        """Mark uncertain BEFORE any external call; safe after crash."""
        now=time.time()
        changed=self.db.execute("UPDATE effects SET state='IN_FLIGHT',updated_at=? WHERE id=? AND state='PREPARED'",(now,eid)).rowcount
        if changed!=1: raise PermissionError("effect cannot be dispatched again")
    def uncertain(self,eid):
        changed=self.db.execute("UPDATE effects SET state='UNKNOWN',updated_at=? WHERE id=? AND state='IN_FLIGHT'",(time.time(),eid)).rowcount
        if changed!=1: raise ValueError("effect is not in flight")
    def recover(self,eid):
        row=self.db.execute("SELECT state,target,operation,idempotency_key FROM effects WHERE id=?",(eid,)).fetchone()
        if not row: raise KeyError("unknown effect")
        if row[0] in ("IN_FLIGHT","UNKNOWN"):
            return {"action":"RECONCILE_REMOTE_READ_ONLY","target":row[1],"operation":row[2],"idempotency_key":row[3]}
        if row[0]=="PREPARED": return {"action":"AWAIT_AUTHORIZED_DISPATCH"}
        return {"action":"NONE","state":row[0]}
    def resolve(self,eid,confirmed,receipt):
        """Only trusted reconciler may call this; a caller must validate provenance first."""
        if not isinstance(receipt,dict) or not receipt.get("source") or not receipt.get("proof"):
            raise ValueError("verified source and proof required")
        state="CONFIRMED" if confirmed else "REJECTED"
        changed=self.db.execute(
          "UPDATE effects SET state=?,receipt=?,updated_at=? WHERE id=? AND state IN ('IN_FLIGHT','UNKNOWN')",
          (state,json.dumps(receipt,sort_keys=True),time.time(),eid)).rowcount
        if changed!=1: raise ValueError("effect already resolved or never dispatched")
        return state
