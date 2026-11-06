"""Worker readiness uses effective local mandate state, not environment strings."""
import tempfile
import unittest
from pathlib import Path
from src.uaes_core import Engine
from src.daemon import Daemon


class DaemonReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "state.sqlite"
        self.engine = Engine(self.db)
        self.agent = self.engine.agent("authorized-test")
        self.mandate = self.engine.mandate(self.agent, "fixture", "analyze")
        self.daemon = Daemon(self.db, self.agent, self.mandate)

    def tearDown(self):
        self.engine.db.close()
        self.temp.cleanup()

    def test_active_mandate_is_ready(self):
        self.assertTrue(self.daemon.readiness())

    def test_revocation_immediately_removes_readiness(self):
        self.engine.revoke(self.mandate)
        self.assertFalse(self.daemon.readiness())

    def test_expired_mandate_is_not_ready(self):
        self.engine.db.execute("UPDATE mandates SET expires=0 WHERE id=?", (self.mandate,))
        self.assertFalse(self.daemon.readiness())

    def test_unknown_agent_and_mandate_are_not_ready(self):
        self.assertFalse(Daemon(self.db, "unknown-agent", self.mandate).readiness())
        self.assertFalse(Daemon(self.db, self.agent, "unknown-mandate").readiness())

    def test_missing_database_does_not_fabricate_readiness(self):
        self.assertFalse(Daemon(self.db.parent / "not-created.sqlite", self.agent, self.mandate).readiness())

    def test_shutdown_removes_readiness(self):
        self.daemon.stop_event.set()
        self.assertFalse(self.daemon.readiness())


if __name__ == "__main__":
    unittest.main()
