import unittest

from tests.qcc_testutil import call, fixture


class TestMethods(unittest.TestCase):
    def test_profile_no_official_scoring(self):
        p = call("methods.profile")
        self.assertFalse(p["official_scoring_configured"])
        self.assertFalse(p["has_official_weights"])
        self.assertEqual(len(p["dimensions"]), 3)
        self.assertIn("统一标准", p["universality_warning"])

    def test_stage_existing_implementation(self):
        facts = {
            "problem_statement": True, "beneficiaries": True,
            "baseline": False, "target": False, "unit": True,
            "cause_hypothesis": True, "factor_verification": False,
            "countermeasure": True, "implementation": {"filled": True, "verified": False},
            "improved_metric": False, "comparable": False,
        }
        r = call("methods.stage", topic={"facts": facts}, facts=facts)
        self.assertNotEqual(r["current_stage"], "complete")
        self.assertTrue(r["structure_and_evidence_separate"])
        self.assertTrue(r["can_continue_with_existing_implementation"])
        self.assertTrue(r["allows_backtrack"])
        self.assertFalse(r["evidence_sufficient"])
        self.assertTrue(r["gaps"])

    def test_reasoning_e06(self):
        data = fixture("e06_reasoning.json")
        r = call("methods.check", topic=data["topic"])
        self.assertTrue(r["causal_gaps"])
        self.assertTrue(r["link_gaps"])
        self.assertFalse(r["evidence_sufficient"])
        self.assertIn("相关性", r["causal_gaps"][0]["reason"])

    def test_recommend_is_actionable(self):
        gaps = [{"stage": "baseline", "missing": ["baseline"], "stage_name": "基线与目标"}]
        r = call("methods.recommend", topic={}, gaps=gaps)
        rec = r["recommendations"][0]
        for k in ("question", "recommended_method", "reason", "required_inputs", "expected_output"):
            self.assertIn(k, rec)

    def test_update_gaps_closes_with_basis(self):
        topic = {"tasks": [
            {"task_id": "t1", "fact_key": "baseline", "closed": False},
            {"task_id": "t2", "fact_key": "factor_verification", "closed": False},
        ]}
        r = call("methods.update_gaps", topic=topic,
                 new_evidence=[{"fact_key": "baseline", "supports": True, "verification_id": "v1"}])
        self.assertIn("t1", r["closed"])
        self.assertIn("t2", r["still_open"])
        self.assertEqual(topic["tasks"][0]["closure_basis"], "v1")
        self.assertTrue(r["closure_requires_basis"])

    def test_not_applicable_supported(self):
        # 不适用与回溯是规则能力，不因模板存在强制照搬
        r = call("methods.stage", topic={"facts": {}}, facts={})
        self.assertTrue(r["not_applicable_supported"])
        self.assertTrue(r["allows_backtrack"])


if __name__ == "__main__":
    unittest.main()
