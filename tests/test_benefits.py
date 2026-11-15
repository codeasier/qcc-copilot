import unittest

from tests.qcc_testutil import call, fixture


class TestBenefitAccounting(unittest.TestCase):
    # 独立参考值：用普通算术字面量核算，不复用产品计算函数自证。
    def test_e05_positive(self):
        ev = fixture("expected_values.json")["person_day"]["reference"]
        m = fixture("e05_benefit.json")["metric"]
        r = call("benefit.compute", metric=m, persist=False)["calculation"]["result"]
        self.assertEqual(r["gross_hours"], 40 * (0.5 - 0.25))  # 10 独立算得
        self.assertEqual(r["net_hours"], 40 * (0.5 - 0.25) - 2)  # 8
        self.assertEqual(r["net_person_days"], 8 / 8)  # 1
        self.assertEqual(r["net_hours"], ev["net_hours"])
        self.assertEqual(r["net_person_days"], ev["net_person_days"])

    def test_e05_negative_preserved(self):
        ev = fixture("expected_values.json")["person_day_negative"]["reference"]
        m = dict(fixture("e05_benefit.json")["metric"])
        m["attributable_cost_hours"] = 12
        r = call("benefit.compute", metric=m, persist=False)["calculation"]["result"]
        self.assertEqual(r["net_hours"], 10 - 12)  # -2
        self.assertEqual(r["net_person_days"], -2 / 8)  # -0.25
        self.assertTrue(r["negative_net_preserved"])
        self.assertEqual(r["net_person_days"], ev["net_person_days"])

    def test_e04_missing_baseline(self):
        r = call("benefit.compute", metric={"improved": 0.25, "unit": "hours",
                                            "event_count": 10}, persist=False)["calculation"]
        self.assertFalse(r["result"]["computable"])
        self.assertTrue(any("baseline" in g for g in r["result"]["gaps"]))
        self.assertIn("fillable_model", r["result"])

    def test_incomparable_population(self):
        r = call("benefit.compute", metric={"baseline": 0.5, "improved": 0.25, "unit": "hours",
                                            "event_count": 10, "baseline_population": "A",
                                            "improved_population": "B"}, persist=False)["calculation"]
        self.assertTrue(any("compar" in g for g in r["result"]["gaps"]))

    def test_unit_mismatch(self):
        r = call("benefit.compute", metric={"baseline": 30, "baseline_unit": "minutes",
                                            "improved": 0.25, "improved_unit": "hours",
                                            "event_count": 10}, persist=False)["calculation"]
        self.assertTrue(any("unit" in g for g in r["result"]["gaps"]))

    def test_waiting_time_not_labor(self):
        r = call("benefit.compute", metric={"baseline": 60, "improved": 20, "unit": "minutes",
                                            "event_count": 10, "time_kind": "waiting",
                                            "human_work_changed": False}, persist=False)["calculation"]
        self.assertFalse(r["result"]["labor_benefit_computable"])
        self.assertEqual(r["result"]["present_as"], "等待/交付周期改善")

    def test_zero_denominator(self):
        r = call("benefit.ratio", numerator=5, denominator=0)["ratio"]
        self.assertFalse(r["computable"])
        self.assertIn("denominator", r["reason"])

    def test_coverage_ratio_independent(self):
        ev = fixture("expected_values.json")["coverage_ratio"]["reference"]
        r = call("benefit.ratio", numerator=85, denominator=100)["ratio"]
        self.assertEqual(r["value"], 0.85)
        self.assertEqual(r["percent"], ev["percent"])

    def test_non_labor_no_person_day(self):
        r = call("benefit.nonlabor", metric={"name": "验证覆盖率", "numerator": 85,
                                             "denominator": 100, "unit": "percent"})["metric"]
        self.assertIsNone(r["person_day_conversion"])
        self.assertTrue(r["ratio"]["computable"])

    def test_separate_extrapolation(self):
        m = fixture("e05_benefit.json")["metric"]
        calc = call("benefit.compute", metric=m, persist=False)["calculation"]
        r = call("benefit.separate", measured=calc,
                 extrapolation={"assumed_teams": 3, "assumed_events_per_team": 40})
        self.assertTrue(r["forward_looking_not_merged"])
        self.assertFalse(r["extrapolation"]["merged_into_measured"])
        self.assertEqual(r["measured_total_hours"], 8.0)

    def test_duplicate_events_dedup(self):
        m = dict(fixture("e05_benefit.json")["metric"])
        m["event_ids"] = ["a", "b", "b", "c"]
        m.pop("event_count")
        r = call("benefit.compute", metric=m, persist=False)["calculation"]["result"]
        self.assertEqual(r["event_count_used"], 3)
        self.assertEqual(r["dedup"]["duplicates_removed"], 1)


if __name__ == "__main__":
    unittest.main()
