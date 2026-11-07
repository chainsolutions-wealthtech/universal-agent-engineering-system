"""Additive continuity index over the existing UAES SQLite authorities.

A continuity ID is a documentary correlation key, never an authorization,
mandate, task queue, or substitute for provider readback.
"""
import json
import sqlite3
import time
from src.uaes_core import Engine

ROOT_ID = "UAES-CONV-CONT-20261107-ROOT-01"
ROOT_SOURCE = "https://github.com/chainsolutions-wealthtech/universal-agent-engineering-system/issues/6"

SCHEMA = """
CREATE TABLE IF NOT EXISTS continuity_roots (
  id TEXT PRIMARY KEY, source TEXT NOT NULL, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS continuity_links (
  continuity_id TEXT NOT NULL REFERENCES continuity_roots(id),
  kind TEXT NOT NULL CHECK(kind IN
    ('agent','mandate','task','event','effect','checkpoint','decision','artifact')),
  object_id TEXT NOT NULL, created REAL NOT NULL,
  PRIMARY KEY(continuity_id,kind,object_id));
CREATE INDEX IF NOT EXISTS continuity_links_lookup
  ON continuity_links(kind,object_id);
CREATE TABLE IF NOT EXISTS continuity_checkpoints (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  continuity_id TEXT NOT NULL REFERENCES continuity_roots(id),
  event_watermark INTEGER NOT NULL,
  snapshot TEXT NOT NULL,
  recorded REAL NOT NULL);
CREATE INDEX IF NOT EXISTS continuity_checkpoint_latest
  ON continuity_checkpoints(continuity_id,id DESC);
"""

class ContinuityEngine(Engine):
    """Preserve Engine's existing schema and behavior; add correlated operations."""

    def __init__(self, path, continuity_id=ROOT_ID, source=ROOT_SOURCE):
        super().__init__(path)
        if not continuity_id or not source:
            raise ValueError("continuity ID and source required")
        self.db.executescript(SCHEMA)
        self.continuity_id = continuity_id
        self.db.execute(
            "INSERT OR IGNORE INTO continuity_roots VALUES(?,?,?)",
            (continuity_id, source, time.time()))
        actual = self.db.execute(
            "SELECT source FROM continuity_roots WHERE id=?",
            (continuity_id,)).fetchone()[0]
        if actual != source:
            raise ValueError("continuity ID cannot be rebound to another source")

    def link(self, kind, object_id):
        if kind not in ("agent","mandate","task","event","effect",
                        "checkpoint","decision","artifact"):
            raise ValueError("unsupported continuity object kind")
        if object_id is None or str(object_id) == "":
            raise ValueError("object ID required")
        # Reject links to nonexistent local authority records. External
        # decisions/artifacts must carry their own immutable source reference.
        table = {"agent":"agents","mandate":"mandates","task":"tasks",
                 "event":"events","effect":"effects"}.get(kind)
        if table:
            col = "seq" if kind == "event" else "id"
            try:
                found = self.db.execute(
                    f"SELECT 1 FROM {table} WHERE {col}=?", (object_id,)).fetchone()
            except sqlite3.OperationalError as exc:
                raise ValueError("local authority table unavailable") from exc
            if not found:
                raise ValueError("cannot link missing local authority")
        self.db.execute(
            "INSERT OR IGNORE INTO continuity_links VALUES(?,?,?,?)",
            (self.continuity_id,kind,str(object_id),time.time()))

    def event(self, kind, subject, data):
        # Preserve the existing event authority and sequence; correlate the
        # exact inserted row, not an independently generated event.
        super().event(kind, subject, data)
        seq = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
        self.link("event",seq)

    def _write_with_link(self, kind, operation):
        """Commit authority row, original event and correlation as one unit."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            object_id = operation()
            self.link(kind, object_id)
            self.db.execute("COMMIT")
            return object_id
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def agent(self, label, agent_id=None):
        return self._write_with_link(
            "agent", lambda: super(ContinuityEngine, self).agent(label, agent_id))

    def mandate(self, agent_id, project_id, scope, ttl=3600):
        return self._write_with_link(
            "mandate", lambda: super(ContinuityEngine, self).mandate(
                agent_id, project_id, scope, ttl))

    def submit(self, project_id, action, payload):
        return self._write_with_link(
            "task", lambda: super(ContinuityEngine, self).submit(
                project_id, action, payload))

    def bind_existing(self, kind, object_id):
        """Opt-in migration of legacy rows; never silently claim their history."""
        self.link(kind,object_id)

    def checkpoint(self):
        """Atomically persist a snapshot and its correlation."""
        self.db.execute("BEGIN IMMEDIATE")
        try:
            current = super().checkpoint()
            watermark = self.db.execute(
                "SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0]
            snapshot = {"core":current,"event_watermark":watermark,
                        "continuity_id":self.continuity_id}
            cur = self.db.execute(
                "INSERT INTO continuity_checkpoints(continuity_id,event_watermark,snapshot,recorded) VALUES(?,?,?,?)",
                (self.continuity_id,watermark,json.dumps(snapshot,sort_keys=True),time.time()))
            self.link("checkpoint",cur.lastrowid)
            self.db.execute("COMMIT")
            return {"checkpoint_id":cur.lastrowid,**snapshot}
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def resume(self):
        """Read-only continuity projection; does not claim work or replay effects."""
        root = self.db.execute(
            "SELECT source FROM continuity_roots WHERE id=?",
            (self.continuity_id,)).fetchone()
        if not root:
            raise ValueError("unknown continuity")
        links = self.db.execute(
            "SELECT kind,object_id FROM continuity_links WHERE continuity_id=? ORDER BY created,kind,object_id",
            (self.continuity_id,)).fetchall()
        last = self.db.execute(
            "SELECT id,event_watermark,snapshot FROM continuity_checkpoints WHERE continuity_id=? ORDER BY id DESC LIMIT 1",
            (self.continuity_id,)).fetchone()
        # Report live local states; never infer successful remote side effects.
        tasks = []
        for kind, object_id in links:
            if kind == "task":
                row = self.db.execute(
                    "SELECT state,claim_owner,fencing FROM tasks WHERE id=?",
                    (object_id,)).fetchone()
                tasks.append({"id":object_id,"state":row[0] if row else "MISSING",
                              "claim_owner":row[1] if row else None,
                              "fencing":row[2] if row else None})
        effects = []
        try:
            for kind, object_id in links:
                if kind == "effect":
                    row = self.db.execute("SELECT state FROM effects WHERE id=?",
                                          (object_id,)).fetchone()
                    effects.append({"id":object_id,"state":row[0] if row else "MISSING"})
        except sqlite3.OperationalError:
            effects.append({"state":"UNAVAILABLE"})
        return {"continuity_id":self.continuity_id,"source":root[0],
                "links":[{"kind":k,"object_id":o} for k,o in links],
                "tasks":tasks,"effects":effects,
                "checkpoint":None if not last else
                    {"id":last[0],"event_watermark":last[1],
                     "snapshot":json.loads(last[2])},
                "next_action":"RECONCILE_PROVIDER_AND_AUTHORIZATION_BEFORE_EXECUTION"}
