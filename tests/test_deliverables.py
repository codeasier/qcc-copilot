import json
import platform
import shutil
import unittest
from pathlib import Path

from qcc_copilot import workspace as W
from tests.qcc_testutil import call, fixture, init_topic, new_base


def setup(base, core_supported=True, run_render=False):
    init_topic(base, title="多平台构建", owner="甲")
    m = fixture("e05_benefit.json")["metric"]
    call("benefit.compute", base, "t1", metric=m, persist=True)
    if core_supported:
        call("claim.add", base, "t1", text="实测净收益 8 小时", origin="record",
             category="benefit", evidence=[{"source_id": "s", "proves": ["measurement"]}],
             verification=[{"kind": "measurement", "supports": True}])
    did = call("delivery.snapshot", base, "t1")["snapshot"]["delivery_id"]
    comp = call("deliverable.compile", base, "t1", delivery_id=did)
    ver = call("deliverable.verify", base, "t1", delivery_id=did, run_render=run_render)
    return did, comp, ver


def ddir(base, did):
    return W.Workspace.route(base, "t1").deliveries_dir / did


class TestDeliverables(unittest.TestCase):
    def test_compile_full_bundle_e10(self):
        base = new_base()
        did, comp, _ = setup(base)
        required = {"report.md", "benefit.md", "reuse.md", "chart_data.json", "chart.svg",
                    "data_worksheet.md", "review_questions.md", "review.json",
                    "slides.json", "deck.pptx", "manifest.json"}
        self.assertTrue(required.issubset(set(comp["files"])))
        self.assertTrue(comp["pptx_real"])
        from qcc_copilot import pptx

        vr = pptx.verify_pptx(str(ddir(base, did) / "deck.pptx"))
        self.assertTrue(vr["structure_ok"])
        self.assertEqual(vr["slides"], 5)
        mani = json.loads((ddir(base, did) / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn("content_hash", mani["snapshot"])

    def test_numbers_consistent_with_snapshot(self):
        base = new_base()
        did, _, _ = setup(base)
        benefit = (ddir(base, did) / "benefit.md").read_text(encoding="utf-8")
        self.assertIn("8.0", benefit)  # 净收益小时
        self.assertIn("1.0", benefit)  # 净人天
        report = (ddir(base, did) / "report.md").read_text(encoding="utf-8")
        self.assertIn(did, report)

    def test_only_slide_text_is_not_ppt_completion(self):
        base = new_base()
        did, _, _ = setup(base)
        (ddir(base, did) / "deck.pptx").unlink()
        ver = call("deliverable.verify", base, "t1", delivery_id=did, run_render=False)
        self.assertEqual(ver["checks"]["coverage"]["status"], "failed")
        self.assertFalse(ver["checks"]["overflow_and_chart"]["pptx_structure"]["ok"])
        self.assertEqual(ver["overall"], "failed")

    def test_review_no_fabricated_scores(self):
        base = new_base()
        did, _, _ = setup(base)
        r = call("deliverable.review", base, "t1", delivery_id=did)["review"]
        self.assertFalse(r["official_scores_generated"])
        self.assertFalse(r["official_scoring_configured"])
        self.assertFalse(r["award_probability_generated"])
        for f in r["findings"]:
            for k in ("依据", "问题", "影响", "建议", "待补证"):
                self.assertIn(k, f)

    def test_placeholder_and_overflow_detected_e10(self):
        base = new_base()
        did, _, _ = setup(base)
        rp = ddir(base, did) / "report.md"
        rp.write_text(rp.read_text(encoding="utf-8") + "\n{{UNFILLED_PLACEHOLDER}}\nTODO 待填\n",
                      encoding="utf-8")
        # 缺图/缺数据
        (ddir(base, did) / "chart_data.json").write_text(
            json.dumps({"data_points": []}), encoding="utf-8")
        ver = call("deliverable.verify", base, "t1", delivery_id=did, run_render=False)
        self.assertEqual(ver["checks"]["placeholders"]["status"], "failed")
        self.assertEqual(ver["checks"]["overflow_and_chart"]["status"], "failed")
        self.assertTrue(ver["checks"]["overflow_and_chart"]["chart_data_missing"])
        self.assertEqual(ver["overall"], "failed")

    def test_render_not_passed_when_unavailable(self):
        base = new_base()
        _, _, ver = setup(base, run_render=False)
        self.assertEqual(ver["checks"]["render"]["status"], "not_run")
        self.assertNotEqual(ver["overall"], "passed")

    @unittest.skipUnless(platform.system() == "Darwin" and shutil.which("qlmanage"),
                         "需要 macOS Quick Look 独立渲染器")
    def test_real_independent_render_e10(self):
        base = new_base()
        _, _, ver = setup(base, run_render=True)
        self.assertEqual(ver["checks"]["render"]["status"], "passed")

    def test_draft_when_core_unverified_e09(self):
        base = new_base()
        did, _, ver = setup(base, core_supported=False)
        st = call("deliverable.status", base, "t1", delivery_id=did, verification=ver)
        self.assertEqual(st["status"], "draft")
        self.assertTrue(st["premature_formal_export_blocked"])

    def test_snapshot_not_rewritten_by_current_changes(self):
        base = new_base()
        did, _, _ = setup(base)
        snap_before = (ddir(base, did) / "snapshot.json").read_bytes()
        ws = W.Workspace.route(base, "t1")
        t, r, h = ws.snapshot()
        t["next"] = "当前又变了"
        ws.save(t, r, h)
        self.assertEqual((ddir(base, did) / "snapshot.json").read_bytes(), snap_before)


if __name__ == "__main__":
    unittest.main()
