import unittest
from scripts.promotion_gate import assess,REQUIRED_CHECKS

class PromotionGateTests(unittest.TestCase):
 def setUp(self):
  self.valid={"main_protected":True,"independent_approval":True,"draft":False,
      "permissions_attested":True,"isolated_deployment_ready":True,
      "checks":{k:"success" for k in REQUIRED_CHECKS}}
 def test_all_evidence_required(self):
  self.assertTrue(assess(self.valid)["admissible"])
  for field in ("main_protected","independent_approval","permissions_attested","isolated_deployment_ready"):
   case=dict(self.valid,**{field:False})
   self.assertFalse(assess(case)["admissible"])
  self.assertFalse(assess(dict(self.valid,draft=True))["admissible"])
 def test_missing_checks_fail_closed(self):
  self.assertFalse(assess(dict(self.valid,checks={}))["admissible"])
 def test_failed_check_not_accepted(self):
  checks=dict(self.valid["checks"]);checks["UAES Container Smoke"]="failure"
  self.assertIn("CHECK_NOT_SUCCESS:UAES Container Smoke",
      assess(dict(self.valid,checks=checks))["failures"])
if __name__=="__main__":unittest.main()
