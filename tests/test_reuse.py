import unittest

from tests.qcc_testutil import call, fixture


class TestReuse(unittest.TestCase):
    def test_common_value_separates_tool_usability_e07(self):
        d = fixture("e07_reuse.json")
        r = call("reuse.evaluate", **d)["evaluation"]
        self.assertTrue(r["tool_usability"]["separate_metric"])
        self.assertTrue(r["potential_only"])
        self.assertEqual(r["tool_usability"]["given"]["metric"], "member_tool_time_saved_hours")

    def test_reuse_package_flags_personal_infra(self):
        d = fixture("e07_reuse.json")
        r = call("reuse.package", **{
            "conditions": ["统一构建镜像"], "steps": ["接入流水线"],
            "depends_on_personal_infra": d["depends_on_personal_infra"],
        })["package"]
        self.assertTrue(r["fields"]["personal_infra_flagged"])
        self.assertTrue(r["fields"]["decoupling_needed"])
        self.assertTrue(r["missing"])  # 资产/验证/维护/成本缺失可见

    def test_adoption_installed_not_adopted_e07(self):
        d = fixture("e07_reuse.json")
        r = call("reuse.adoption", adoption_records=d["adoption_records"])["adoption"]
        self.assertTrue(r["installed_not_adopted"])
        self.assertTrue(r["potential_vs_adopted_separate"])
        adopted = [c for c in r["classified"] if c["adoption_state"] == "adopted"]
        self.assertEqual(len(adopted), 1)
        self.assertTrue(adopted[0]["benefit_verified"])

    def test_count_dedup_same_team(self):
        records = [
            {"team": "团队B", "status": "adopted", "source_id": "log1", "dedup_key": "k"},
            {"team": "团队B", "status": "adopted", "source_id": "log2", "dedup_key": "k"},
            {"team": "团队A", "status": "installed", "dedup_key": "k"},
        ]
        r = call("reuse.count", records=records)["count"]
        self.assertEqual(r["distinct_adopted_teams"], 1)
        self.assertTrue(r["duplicate_sources_not_double_counted"])

    def test_failure_feedback_narrows(self):
        pkg = call("reuse.package", conditions=["c"], assets=["a"], steps=["s"],
                   validation=["v"], maintenance=["m"], cost=2)["package"]
        r = call("reuse.feedback", package=pkg,
                 feedback=[{"team": "团队C", "feedback": "缺少所需权限，无法适用"}])
        self.assertTrue(r["applicability_narrowed"])
        self.assertTrue(r["validation_tasks"])


if __name__ == "__main__":
    unittest.main()
