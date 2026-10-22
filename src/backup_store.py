"""SQLite online backup and verified restore for isolated UAES state."""
import hashlib, sqlite3
from pathlib import Path

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(65536),b""):h.update(chunk)
    return h.hexdigest()

def backup(db_path,destination):
    source=Path(db_path); target=Path(destination)
    if source.resolve()==target.resolve():raise ValueError("backup destination must differ")
    if target.exists():raise FileExistsError("refuse to overwrite existing backup")
    target.parent.mkdir(parents=True,exist_ok=True)
    try:
        with sqlite3.connect(source) as db, sqlite3.connect(target) as copy:
            db.backup(copy)
        with sqlite3.connect(target) as verify:
            result=verify.execute("PRAGMA integrity_check").fetchone()[0]
        if result!="ok":raise RuntimeError("backup integrity failed")
        return {"backup":str(target),"sha256":sha256(target),"integrity":"ok"}
    except Exception:
        target.unlink(missing_ok=True)
        raise

def restore(backup_path,destination,expected_sha256):
    source=Path(backup_path); dest=Path(destination)
    if dest.exists():raise FileExistsError("never overwrite live state")
    if sha256(source)!=expected_sha256:raise ValueError("backup hash mismatch")
    dest.parent.mkdir(parents=True,exist_ok=True)
    try:
        with sqlite3.connect(source) as db:
            if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                raise ValueError("source integrity failure")
            with sqlite3.connect(dest) as output:db.backup(output)
        return {"restored":str(dest),"sha256":sha256(dest)}
    except Exception:
        dest.unlink(missing_ok=True)
        raise
