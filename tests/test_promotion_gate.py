import unittest
from scripts.promotion_gate import assess,REQUIRED_CHECKS

class PromotionGateTests(unittest.TestCase):
 def setUp(self):
  self.valid={"main_protected":True,"required_approving_reviews":0,"draft":False,
      "permissions_attested":True,"isolated_deployment_ready":True,
      "checks":{k:"success" for k in REQUIRED_CHECKS}}
 def test_all_evidence_required(self):
  self.assertTrue(assess(self.valid)["admissible"])
  for field in ("main_protected","permissions_attested","isolated_deployment_ready"):
   case=dict(self.valid,**{field:False})
   self.assertFalse(assess(case)["admissible"])
  self.assertFalse(assess(dict(self.valid,draft=True))["admissible"])
 def test_review_policy_provenance_required_but_no_human_approval(self):
  self.assertTrue(assess(dict(self.valid,independent_approval=False))["admissible"])
  for requirement in (None, 1, 2, -1, True):
   case=dict(self.valid)
   case["required_approving_reviews"]=requirement
   self.assertFalse(assess(case)["admissible"])
  case=dict(self.valid)
  del case["required_approving_reviews"]
  self.assertIn("REVIEW_POLICY_UNVERIFIED",assess(case)["failures"])
 def test_missing_checks_fail_closed(self):
  self.assertFalse(assess(dict(self.valid,checks={}))["admissible"])
 def test_failed_check_not_accepted(self):
  checks=dict(self.valid["checks"]);checks["UAES Container Smoke"]="failure"
  self.assertIn("CHECK_NOT_SUCCESS:UAES Container Smoke",
      assess(dict(self.valid,checks=checks))["failures"])
if __name__=="__main__":unittest.main()
