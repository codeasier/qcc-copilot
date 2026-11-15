import unittest

from tests.qcc_testutil import call, fixture, init_topic, new_base


class TestSummary(unittest.TestCase):
    def test_export_preserves_gaps_e11(self):
        base = new_base()
        init_topic(base)
        ws = __import__("qcc_copilot.workspace", fromlist=["Workspace"]).Workspace.route(base, "t1")
        t, r, h = ws.snapshot()
        t["tasks"] = [{"task_id": "x", "description": "缺基线", "closed": False, "fact_key": "baseline"}]
        t["next"] = "采集基线"
        ws.save(t, r, h)
        s = call("summary.export", base, "t1")["summary"]
        self.assertIn("缺基线", s["gaps"])
        self.assertIn("source_scope_note", s)
        self.assertIn("content_hash", s)

    def test_import_invalid(self):
        bad = fixture("e11_summaries.json")["summaries"][4]  # 未知版本
        r = call("summary.import", summary=bad)
        self.assertFalse(r["ok"])
        noid = fixture("e11_summaries.json")["summaries"][5]  # 缺标识
        r2 = call("summary.import", summary=noid)
        self.assertFalse(r2["ok"])

    def test_export_time_not_semantic(self):
        from qcc_copilot import summary as S

        a = {"schema_version": "1.0", "format_version": "1.0", "topic_id": "t",
             "revision": 1, "stage": "effect", "next": "n", "gaps": []}
        b = dict(a, exported_at="2026-01-01T00:00:00Z")
        c = dict(a, exported_at="2026-02-02T00:00:00Z")
        self.assertEqual(S.compute_summary_hash(b), S.compute_summary_hash(c))

    def test_aggregate_e11(self):
        data = fixture("e11_summaries.json")["summaries"]
        agg = call("summary.aggregate", summaries=data)["aggregate"]
        self.assertEqual(agg["topics"]["topic-A"]["revision"], 4)
        self.assertEqual(agg["counts"]["conflicts"], 1)
        self.assertEqual(agg["counts"]["invalid"], 2)
        self.assertTrue(any(a["action"] == "older_skip_no_rollback" for a in agg["audit"]))

    def test_duplicate_not_double_counted(self):
        s = {"schema_version": "1.0", "format_version": "1.0", "topic_id": "t",
             "revision": 3, "exported_at": "2026-01-01T00:00:00Z", "next": "n",
             "gaps": [], "stage": "effect"}
        s2 = dict(s, exported_at="2026-02-02T00:00:00Z")
        agg = call("summary.aggregate", summaries=[s, s2])["aggregate"]
        self.assertEqual(agg["counts"]["topics"], 1)
        self.assertEqual(agg["counts"]["duplicates"], 1)
        self.assertEqual(agg["counts"]["conflicts"], 0)

    def test_same_revision_diff_content_conflict(self):
        a = {"schema_version": "1.0", "format_version": "1.0", "topic_id": "t",
             "revision": 3, "exported_at": "x", "next": "n", "gaps": [], "stage": "effect"}
        b = dict(a, next="不同内容")
        agg = call("summary.aggregate", summaries=[a, b])["aggregate"]
        self.assertEqual(agg["counts"]["conflicts"], 1)
        self.assertEqual(agg["counts"]["duplicates"], 0)

    def test_views_show_snapshot_and_conflicts(self):
        agg = call("summary.aggregate",
                   summaries=fixture("e11_summaries.json")["summaries"])["aggregate"]
        v = call("summary.views", aggregate=agg)["views"]
        self.assertIn("快照", v["markdown"])
        self.assertIn("进展未知", v["markdown"])
        self.assertTrue(v["conflicts_visible"])
        self.assertTrue(v["csv"].startswith("topic_id,"))

    def test_feedback_suggestion_only_e11(self):
        base = new_base()
        init_topic(base)
        fb = call("feedback.export", base, topic_id="t1", target_revision=0,
                  author="负责人", content="补充基线测量")["feedback"]
        r = call("feedback.import", base, "t1", feedback=fb)
        self.assertTrue(r["imported"])
        self.assertEqual(r["role"], "suggestion_or_todo")
        self.assertFalse(r["facts_changed"])
        self.assertFalse(r["benefit_changed"])
        self.assertFalse(r["version_diff"])

    def test_feedback_old_revision_flagged(self):
        base = new_base()
        init_topic(base)
        ws = __import__("qcc_copilot.workspace", fromlist=["Workspace"]).Workspace.route(base, "t1")
        t, r, h = ws.snapshot()
        ws.save(t, r, h)  # 推进到修订 1
        fb = call("feedback.export", base, topic_id="t1", target_revision=0,
                  author="负责人", content="针对旧修订")["feedback"]
        res = call("feedback.import", base, "t1", feedback=fb)
        self.assertTrue(res["version_diff"])


if __name__ == "__main__":
    unittest.main()
