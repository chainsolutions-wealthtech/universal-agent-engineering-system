import tempfile,unittest
from pathlib import Path
from src.uaes_core import Engine
from src.backup_store import backup,restore

class BackupTests(unittest.TestCase):
 def test_backup_and_restore_with_no_overwrite(self):
  with tempfile.TemporaryDirectory() as tmp:
   src=Path(tmp)/"live.db"; snapshot=Path(tmp)/"copy.db"; recovered=Path(tmp)/"restore.db"
   e=Engine(src);a=e.agent("synthetic");e.mandate(a,"fixture","analyze")
   info=backup(src,snapshot)
   self.assertEqual(info["integrity"],"ok")
   e.db.close()
   restore(snapshot,recovered,info["sha256"])
   other=Engine(recovered)
   self.assertEqual(other.db.execute("SELECT count(*) FROM agents").fetchone()[0],1)
   other.db.close()
   with self.assertRaises(FileExistsError):restore(snapshot,recovered,info["sha256"])
 def test_wrong_digest_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   src=Path(tmp)/"source.db";e=Engine(src);e.db.close()
   snap=Path(tmp)/"backup.db";backup(src,snap)
   with self.assertRaises(ValueError):restore(snap,Path(tmp)/"restore.db","0"*64)
if __name__=="__main__":unittest.main()
