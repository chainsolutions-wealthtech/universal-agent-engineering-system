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
 def test_missing_source_does_not_create_fake_backup(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/"never-created.sqlite"
   target=Path(tmp)/"snapshot.sqlite"
   with self.assertRaises(FileNotFoundError):backup(source,target)
   self.assertFalse(source.exists())
   self.assertFalse(target.exists())

 def test_existing_backup_and_restore_targets_are_never_overwritten(self):
  with tempfile.TemporaryDirectory() as tmp:
   src=Path(tmp)/"source.db";Engine(src).db.close()
   original=Path(tmp)/"reserved.db";original.write_bytes(b"original")
   with self.assertRaises(FileExistsError):backup(src,original)
   self.assertEqual(original.read_bytes(),b"original")
   snap=Path(tmp)/"backup.db";receipt=backup(src,snap)
   with self.assertRaises(FileExistsError):restore(snap,original,receipt["sha256"])
   self.assertEqual(original.read_bytes(),b"original")

 def test_dangling_destination_symlinks_are_never_followed(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);src=root/"source.db";Engine(src).db.close()
   backup_link=root/"backup-link.db";target=root/"not-yet-existing.db"
   try:backup_link.symlink_to(target)
   except (OSError,NotImplementedError):self.skipTest("symlink unsupported")
   with self.assertRaises((FileExistsError,ValueError)):backup(src,backup_link)
   self.assertFalse(target.exists())
   snap=root/"backup.db";receipt=backup(src,snap)
   restore_link=root/"restore-link.db";restore_link.symlink_to(target)
   with self.assertRaises((FileExistsError,ValueError)):restore(snap,restore_link,receipt["sha256"])
   self.assertFalse(target.exists())

 def test_symlink_source_is_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);src=root/"real.db";Engine(src).db.close()
   ref=root/"linked.db"
   try:ref.symlink_to(src)
   except (OSError,NotImplementedError):self.skipTest("symlink unsupported")
   with self.assertRaises(ValueError):backup(ref,root/"copy.db")

if __name__=="__main__":unittest.main()
