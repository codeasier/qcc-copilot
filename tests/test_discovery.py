import unittest

from tests.qcc_testutil import call, fixture, fixture_path, init_topic, new_base


class TestDiscovery(unittest.TestCase):
    def test_refine_supplied_improvement_e01(self):
        data = fixture("e01_improvement.json")
        r = call("discovery.refine", supplied=data["supplied"])["refined"]
        self.assertTrue(r["implementation"]["feature_implemented"])
        self.assertFalse(r["benefit"]["benefit_proven"])
        self.assertEqual(r["benefit"]["claim"]["support"], "unverified")
        self.assertFalse(r["adoption"]["adopted_proven"])
        self.assertTrue(r["unknowns"])

    def test_zero_candidates_when_insufficient(self):
        r = call("discovery.candidates", candidate_cards_submitted_by_host=[],
                 scope_note="资料不足")
        self.assertTrue(r["insufficient"])
        self.assertEqual(r["candidates"], [])
        self.assertIn("不强行", r["note"])

    def test_candidate_cards_e02(self):
        data = fixture("e02_materials/discovery_request.json")
        r = call("discovery.candidates", **data)
        self.assertFalse(r["insufficient"])
        self.assertEqual(len(r["candidates"]), 4)
        self.assertTrue(all(c["sources"] for c in r["candidates"]))

    def test_reconcile_dedup_preserves_sources(self):
        data = fixture("e02_materials/discovery_request.json")
        cards = call("discovery.candidates", **data)["candidates"]
        rec = call("discovery.reconcile", candidates=cards)
        keys = [m["dedup_key"] for m in rec["merges"]]
        self.assertIn("build-flaky", keys)
        merged = [m for m in rec["merges"] if m["dedup_key"] == "build-flaky"][0]
        self.assertGreaterEqual(len(merged["sources_preserved"]), 2)
        self.assertTrue(rec["duplicate_sources_preserved"])
        self.assertLess(len(rec["candidates"]), len(cards))

    def test_select_scope_only(self):
        base = new_base()
        data = fixture("e02_materials/discovery_request.json")
        card = call("discovery.candidates", **data)["candidates"][1]
        out = call("discovery.select", base, candidate=card)
        self.assertTrue(out["selected_scope_only"])
        topic = call("workspace.status", base, topic_id=out["topic_id"])
        self.assertEqual(topic["topic_id"], out["topic_id"])

    def test_sources_coverage_e03(self):
        data = fixture("e03_sources.json")
        r = call("sources.index", base_dir=str(fixture_path("e02_materials")),
                 sources=data["sources"], max_bytes=data["max_bytes"])["index"]
        counts = r["coverage"]["counts"]
        for status in ("read", "unread", "failed", "truncated"):
            self.assertGreater(counts.get(status, 0), 0, f"缺少 {status} 覆盖记录")
        self.assertFalse(r["coverage"]["full_coverage"])
        self.assertTrue(r["coverage"]["unread_or_failed"])

    def test_remote_boundary(self):
        b = call("sources.boundary")
        self.assertIn("统一", b["boundary"])
        self.assertIn("when_absent", b)


if __name__ == "__main__":
    unittest.main()
