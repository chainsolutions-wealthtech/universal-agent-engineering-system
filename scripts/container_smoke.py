"""Prepare and verify a synthetic SQLite task for the container smoke test."""
import argparse,json,sqlite3
from pathlib import Path
from src.uaes_core import Engine
p=argparse.ArgumentParser()
p.add_argument("mode",choices=("seed","verify"))
p.add_argument("database")
a=p.parse_args()
if a.mode=="seed":
    engine=Engine(a.database)
    agent=engine.agent("ci-only")
    mandate=engine.mandate(agent,"ci-fixture","analyze")
    task=engine.submit("ci-fixture","analyze",{"synthetic":True})
    Path(str(a.database)+".ids").write_text(json.dumps({"agent":agent,"mandate":mandate,"task":task}))
    engine.db.close()
else:
    ids=json.loads(Path(str(a.database)+".ids").read_text())
    db=sqlite3.connect(a.database)
    status=db.execute("SELECT state FROM tasks WHERE id=?",(ids["task"],)).fetchone()
    completed=db.execute("SELECT COUNT(*) FROM events WHERE kind='task.completed' AND subject=?",(ids["task"],)).fetchone()[0]
    assert status==("DONE",) and completed==1,(status,completed)
    db.close()
    print("Container smoke: task completed exactly once after durable restart")
