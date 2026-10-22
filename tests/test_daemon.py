import tempfile,unittest
from pathlib import Path
from src.uaes_core import Engine
from src.daemon import Daemon

class DaemonTests(unittest.TestCase):
 def test_existing_mandate_and_restart(self):
  with tempfile.TemporaryDirectory() as root:
   db=Path(root)/"db.sqlite"
   e=Engine(db)
   a=e.agent("fixture")
   m=e.mandate(a,"fixture","analyze")
   t=e.submit("fixture","analyze",{"test":1})
   e.db.close()
   first=Daemon(db,a,m,0).serve(max_iterations=1)
   second=Daemon(db,a,m,0).serve(max_iterations=1)
   self.assertEqual(first["completed"],1)
   self.assertEqual(second["completed"],0)
 def test_no_fabricated_mandate(self):
  with tempfile.TemporaryDirectory() as root:
   db=Path(root)/"db.sqlite"
   e=Engine(db)
   a=e.agent("fixture")
   e.submit("fixture","analyze",{})
   e.db.close()
   out=Daemon(db,a,"absent",0).serve(max_iterations=1)
   self.assertEqual(out["completed"],0)
if __name__=="__main__":unittest.main()
