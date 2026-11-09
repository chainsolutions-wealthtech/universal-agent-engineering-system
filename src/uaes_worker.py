"""Bounded worker for explicitly allowed, local-only UAES actions."""
import json
from src.uaes_core import Engine

class Worker:
    def __init__(self, engine: Engine, agent_id: str, mandate_id: str):
        self.engine, self.agent_id, self.mandate_id = engine, agent_id, mandate_id

    def execute(self, task_id: str):
        task=self.engine.db.execute(
            "SELECT action,payload FROM tasks WHERE id=?", (task_id,)).fetchone()
        if task is None:
            raise KeyError("unknown task")
        action,payload=task
        # Whitelist is an explicit boundary: no filesystem, shell or remote operations.
        if action not in ("analyze","validate"):
            raise PermissionError("worker action not allowlisted")
        token=self.engine.claim(task_id,self.agent_id,self.mandate_id)
        if action == "analyze":
            result={"kind":"analysis","payload_keys":sorted(json.loads(payload).keys())}
        else:
            obj=json.loads(payload)
            result={"kind":"validation","valid":isinstance(obj,dict),"field_count":len(obj)}
        self.engine.complete(task_id,self.agent_id,token,result)
        return {"task_id":task_id,"fencing":token,"result":result}

def resume_completed(engine: Engine, task_id: str):
    row=engine.db.execute("SELECT state,result FROM tasks WHERE id=?",(task_id,)).fetchone()
    if row is None: raise KeyError("unknown task")
    if row[0]!="DONE": return {"status":row[0],"reconciled":False}
    return {"status":"DONE","reconciled":True,"result":json.loads(row[1])}
