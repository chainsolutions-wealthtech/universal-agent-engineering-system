"""SQLite online backup and verified restore for isolated UAES state.

Fail closed on missing input databases, symlinked input paths, occupied output
paths, and invalid SQLite backups. Never create a fabricated empty source DB
or overwrite state that belongs to another operation.
"""
import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import quote


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_only_connection(path):
    # SQLite's default connect() creates absent databases: never use it for
    # a backup input. URI mode=ro refuses to fabricate a source.
    uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _require_input(path):
    if path.is_symlink():
        raise ValueError("symlink backup/source paths are not trusted")
    if not path.is_file():
        raise FileNotFoundError("SQLite source database does not exist")


def _check_integrity(path):
    with closing(_read_only_connection(path)) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite integrity verification failed")


def backup(db_path, destination):
    source = Path(db_path)
    target = Path(destination)
    if source.resolve() == target.resolve():
        raise ValueError("backup destination must differ")
    _require_input(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also rejects dangling destination symlinks and
    # competing operations; never open an existing file for SQLite output.
    with target.open("xb"):
        pass
    try:
        with closing(_read_only_connection(source)) as db, closing(
                sqlite3.connect(target)) as copy:
            db.backup(copy)
        _check_integrity(target)
        return {"backup": str(target), "sha256": sha256(target),
                "integrity": "ok"}
    except Exception:
        target.unlink(missing_ok=True)
        raise


def restore(backup_path, destination, expected_sha256):
    source = Path(backup_path)
    dest = Path(destination)
    _require_input(source)
    if dest.exists() or dest.is_symlink():
        raise FileExistsError("never overwrite live state")
    if sha256(source) != expected_sha256:
        raise ValueError("backup hash mismatch")
    _check_integrity(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("xb"):
        pass
    try:
        with closing(_read_only_connection(source)) as db, closing(
                sqlite3.connect(dest)) as output:
            db.backup(output)
        _check_integrity(dest)
        return {"restored": str(dest), "sha256": sha256(dest)}
    except Exception:
        dest.unlink(missing_ok=True)
        raise
