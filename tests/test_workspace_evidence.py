import json
import unittest
from pathlib import Path

from qcc_copilot import deliveries, evidence, workspace as W
from qcc_copilot.errors import AmbiguousWorkspace, DamagedWorkspace, RevisionConflict
from tests.qcc_testutil import call, init_topic, new_base


class TestWorkspace(unittest.TestCase):
    def test_init_and_resume(self):
        base = new_base()
        self.assertTrue(init_topic(base)["created"])
        r = call("workspace.resume", base)
        self.assertTrue(r["resumed_from_persisted_state"])
        self.assertEqual(r["revision"], 0)
        self.assertIn("描述", r["next"])

    def test_ambiguous_routing_preserves_all(self):
        base = new_base()
        init_topic(base, topic_id="A", title="甲")
        init_topic(base, topic_id="B", title="乙")
        with self.assertRaises(AmbiguousWorkspace) as ctx:
            call("workspace.route", base)
        self.assertCountEqual(ctx.exception.details, ["A", "B"])
        self.assertEqual(call("workspace.route", base, topic_id="B")["topic_id"], "B")

    def test_damaged_workspace_preserved(self):
        base = new_base()
        init_topic(base)
        p = Path(base) / ".qcc" / "t1" / "topic.json"
        p.write_text("{ not json", encoding="utf-8")
        with self.assertRaises(DamagedWorkspace):
            call("workspace.resume", base, topic_id="t1")
        self.assertEqual(p.read_text(encoding="utf-8"), "{ not json")

    def test_unknown_version_not_reinitialized(self):
        base = new_base()
        init_topic(base)
        p = Path(base) / ".qcc" / "t1" / "topic.json"
        obj = json.loads(p.read_text(encoding="utf-8"))
        obj["schema_version"] = "0.0"
        p.write_text(json.dumps(obj), encoding="utf-8")
        with self.assertRaises(DamagedWorkspace):
            call("workspace.resume", base, topic_id="t1")

    def test_revision_conflict_on_human_edit(self):
        base = new_base()
        init_topic(base)
        ws = W.Workspace.route(base, "t1")
        topic, rev, h = ws.snapshot()
        p = ws.topic_path
        obj = json.loads(p.read_text(encoding="utf-8"))
        obj["next"] = "人工修改后的下一步"
        p.write_text(json.dumps(obj), encoding="utf-8")
        with self.assertRaises(RevisionConflict):
            ws.save(topic, rev, h)
        self.assertEqual(json.loads(p.read_text(encoding="utf-8"))["next"], "人工修改后的下一步")

    def test_concurrent_write_conflict(self):
        base = new_base()
        init_topic(base)
        ws = W.Workspace.route(base, "t1")
        t1, r1, h1 = ws.snapshot()
        t2, r2, h2 = ws.snapshot()  # 两个工具基于同一修订读取
        ws.save(t1, r1, h1)
        with self.assertRaises(RevisionConflict):
            ws.save(t2, r2, h2)

    def test_backup_written(self):
        base = new_base()
        init_topic(base)
        ws = W.Workspace.route(base, "t1")
        t, r, h = ws.snapshot()
        ws.save(t, r, h)
        self.assertTrue(any(ws.revisions_dir.glob("rev-*.json")))


class TestEvidence(unittest.TestCase):
    def test_member_statement_not_measured(self):
        c = evidence.make_claim(text="省了人天", origin="member_statement", category="benefit",
                                requested_support="supported")
        self.assertEqual(c["support"], "unverified")
        self.assertEqual(c["downgraded_from"], "supported")

    def test_launch_link_not_benefit_evidence(self):
        c = evidence.make_claim(text="上线后有收益", origin="record", category="benefit",
                                evidence=[{"source_id": "s1", "proves": ["deployment"]}])
        self.assertEqual(c["support"], "insufficient")

    def test_verified_claim_supported(self):
        c = evidence.make_claim(text="实测节省", origin="record", category="benefit",
                                evidence=[{"source_id": "s", "proves": ["measurement"]}],
                                verification=[{"kind": "measurement", "supports": True}])
        self.assertEqual(c["support"], "supported")

    def test_conflict_preserved(self):
        base = new_base()
        init_topic(base)
        call("claim.add", base, "t1", text="收益 10 小时", origin="record", category="benefit",
             verification=[{"kind": "measurement", "supports": True}],
             evidence=[{"source_id": "a", "proves": ["measurement"]}])
        ws = W.Workspace.route(base, "t1")
        cid = ws.load()["claims"][0]["claim_id"]
        out = call("claim.conflict", base, "t1", claim_id=cid,
                   source={"source_id": "b", "note": "另一记录给出不同数值"})
        self.assertEqual(out["claim"]["support"], "conflicting")
        self.assertEqual(len(out["claim"]["conflicts"]), 1)

    def test_targeted_invalidation(self):
        topic = {
            "claims": [
                {"claim_id": "c-benefit", "depends_on": ["calc-1"], "needs_review": False},
                {"claim_id": "c-unrelated", "depends_on": ["src-x"], "needs_review": False},
            ],
            "calculations": [{"calculation_id": "calc-1", "depends_on": ["src-1"], "needs_review": False}],
            "dependencies": [{"derived_id": "del-1", "kind": "delivery", "depends_on": ["c-benefit"]}],
            "deliveries": [{"delivery_id": "del-1"}],
        }
        r = evidence.compute_invalidation(topic, ["src-1"])
        self.assertIn("calc-1", r["affected_derived_calculations"])
        self.assertIn("c-benefit", r["affected_derived_claims"])
        self.assertNotIn("c-unrelated", r["affected_derived_claims"])
        self.assertTrue(topic["claims"][0]["needs_review"])
        self.assertFalse(topic["claims"][1]["needs_review"])
        self.assertFalse(r["unrelated_reset"])

    def test_idempotent_repeat(self):
        topic = {"events": []}
        e = {"type": "source_change"}
        created1, _ = evidence.idempotent_event(topic, "k1", e)
        created2, _ = evidence.idempotent_event(topic, "k1", e)
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(len(topic["events"]), 1)

    def test_delivery_snapshot_is_historical(self):
        base = new_base()
        init_topic(base)
        snap = call("delivery.snapshot", base, "t1")["snapshot"]
        did = snap["delivery_id"]
        # 修改当前课题
        ws = W.Workspace.route(base, "t1")
        t, r, h = ws.snapshot()
        t["next"] = "变化后的下一步"
        ws.save(t, r, h)
        again = deliveries.get_snapshot(ws, did)
        self.assertEqual(again["topic_revision"], snap["topic_revision"])
        self.assertEqual(again["content_hash"], snap["content_hash"])


if __name__ == "__main__":
    unittest.main()
