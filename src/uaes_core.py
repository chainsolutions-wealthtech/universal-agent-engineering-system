"""Durable SQLite core for UAES. Synthetic/local project scope only."""
import json, sqlite3, time, uuid
from pathlib import Path

DDL = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS agents(id TEXT PRIMARY KEY, label TEXT NOT NULL, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS mandates(id TEXT PRIMARY KEY, agent_id TEXT NOT NULL REFERENCES agents(id),
 project_id TEXT NOT NULL, scope TEXT NOT NULL, expires REAL NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, project_id TEXT NOT NULL, action TEXT NOT NULL,
 payload TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'READY', claim_owner TEXT,
 claim_expiry REAL, claim_mandate TEXT, fencing INTEGER NOT NULL DEFAULT 0, result TEXT, UNIQUE(project_id,action));
CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
 subject TEXT NOT NULL, data TEXT NOT NULL, recorded REAL NOT NULL);
"""
class Engine:
    def __init__(self, path):
        self.db=sqlite3.connect(str(path), isolation_level=None, timeout=10)
        self.db.executescript(DDL)
    def event(self,kind,subject,data):
        self.db.execute("INSERT INTO events(kind,subject,data,recorded) VALUES(?,?,?,?)",
                        (kind,subject,json.dumps(data,sort_keys=True),time.time()))
    def agent(self,label,agent_id=None):
        aid=agent_id or str(uuid.uuid4())
        self.db.execute("INSERT INTO agents VALUES(?,?,?)",(aid,label,time.time()))
        self.event("agent.created",aid,{"label":label})
        return aid
    def mandate(self,agent_id,project_id,scope,ttl=3600):
        mid=str(uuid.uuid4())
        self.db.execute("INSERT INTO mandates VALUES(?,?,?,?,?,0)",
                        (mid,agent_id,project_id,scope,time.time()+ttl))
        self.event("mandate.created",mid,{"agent_id":agent_id,"project_id":project_id,"scope":scope})
        return mid
    def revoke(self,mid):
        self.db.execute("UPDATE mandates SET revoked=1 WHERE id=?",(mid,))
        self.event("mandate.revoked",mid,{})
    def submit(self,project_id,action,payload):
        tid=str(uuid.uuid4())
        self.db.execute("INSERT INTO tasks(id,project_id,action,payload) VALUES(?,?,?,?)",
                        (tid,project_id,action,json.dumps(payload,sort_keys=True)))
        self.event("task.submitted",tid,{"project_id":project_id,"action":action})
        return tid
    def claim(self,task_id,agent_id,mandate_id,lease=90):
        now=time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            mandate=self.db.execute("SELECT project_id,scope,expires,revoked FROM mandates WHERE id=? AND agent_id=?",
                                    (mandate_id,agent_id)).fetchone()
            task=self.db.execute("SELECT project_id,action,state,claim_expiry,fencing FROM tasks WHERE id=?",
                                 (task_id,)).fetchone()
            if not mandate or not task or mandate[3] or mandate[2]<=now or mandate[0]!=task[0] or mandate[1]!=task[1]:
                raise PermissionError("effective mandate absent, revoked or expired")
            if task[2] not in ("READY","CLAIMED") or (task[2]=="CLAIMED" and task[3]>now):
                raise ValueError("task not claimable")
            token=task[4]+1
            self.db.execute("UPDATE tasks SET state='CLAIMED',claim_owner=?,claim_expiry=?,claim_mandate=?,fencing=? WHERE id=?",
                            (agent_id,now+lease,mandate_id,token,task_id))
            self.event("task.claimed",task_id,{"agent":agent_id,"fencing":token})
            self.db.execute("COMMIT")
            return token
        except Exception:
            self.db.execute("ROLLBACK")
            raise
    def complete(self,task_id,agent_id,fencing,result):
        now=time.time()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            authorization=self.db.execute("""SELECT 1 FROM tasks t JOIN mandates m ON t.claim_mandate=m.id
              WHERE t.id=? AND t.claim_owner=? AND t.fencing=? AND m.agent_id=?
              AND m.project_id=t.project_id AND m.scope=t.action
              AND m.revoked=0 AND m.expires>?""",
              (task_id,agent_id,fencing,agent_id,now)).fetchone()
            if not authorization: raise PermissionError("mandate revoked, expired or mismatched")
            updated=self.db.execute("""UPDATE tasks SET state='DONE',result=? WHERE id=? AND state='CLAIMED'
            AND claim_owner=? AND fencing=? AND claim_expiry>?""",
            (json.dumps(result,sort_keys=True),task_id,agent_id,fencing,now)).rowcount
            if not updated: raise PermissionError("stale claim / expired lease")
            self.event("task.completed",task_id,{"fencing":fencing,"result":result})
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise
    def checkpoint(self):
        return {"events":self.db.execute("SELECT count(*) FROM events").fetchone()[0],
                "tasks":self.db.execute("SELECT state,count(*) FROM tasks GROUP BY state").fetchall()}
