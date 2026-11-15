import json
import subprocess
import sys
import unittest
from pathlib import Path

from qcc_copilot import workspace as W
from tests.qcc_testutil import call, fixture, init_topic, new_base

ROOT = Path(__file__).resolve().parent.parent


class TestFreshSessionChainE12(unittest.TestCase):
    """E12 / 10.2：成员与负责人两种角色、新会话不依赖旧聊天状态，文件/引用/数字/版本一致。"""

    def test_full_chain_two_sessions(self):
        base = new_base()

        # —— 会话一（成员）——
        init_topic(base, topic_id="topic-A", title="多平台构建失败定位", owner="成员甲")
        m = fixture("e05_benefit.json")["metric"]
        calc = call("benefit.compute", base, "topic-A", metric=m, persist=True)["calculation"]
        call("claim.add", base, "topic-A", text="实测净收益 8 小时", origin="record",
             category="benefit", evidence=[{"source_id": "timesheet-2026-09", "proves": ["measurement"]}],
             verification=[{"kind": "measurement", "supports": True}])
        did = call("delivery.snapshot", base, "topic-A")["snapshot"]["delivery_id"]
        call("deliverable.compile", base, "topic-A", delivery_id=did)
        ver = call("deliverable.verify", base, "topic-A", delivery_id=did, run_render=False)
        summary = call("summary.export", base, "topic-A")["summary"]

        # —— 切换会话：只重新用文件路径定位 Workspace，不携带任何内存状态 ——
        ws2 = W.Workspace.route(base, "topic-A")
        resumed = W.Workspace.resume(base, "topic-A")
        self.assertTrue(resumed["resumed_from_persisted_state"])
        self.assertEqual(ws2.load()["revision"], summary["revision"])

        # 负责人：聚合 + 反馈导出 + 成员导入回流
        agg = call("summary.aggregate", summaries=[summary, summary])["aggregate"]
        self.assertEqual(agg["counts"]["topics"], 1)
        self.assertEqual(agg["counts"]["duplicates"], 1)
        fb = call("feedback.export", base, topic_id="topic-A",
                  target_revision=resumed["revision"], author="负责人乙",
                  content="补充效果验证记录")["feedback"]
        call("feedback.import", base, "topic-A", feedback=fb)

        # —— 新会话恢复：反馈进入待办，数字与快照一致 ——
        resumed2 = W.Workspace.resume(base, "topic-A")
        self.assertTrue(any("负责人反馈" in t.get("description", "")
                            for t in resumed2["unresolved_tasks"]))
        snap = call("delivery.get", base, "topic-A", delivery_id=did)["snapshot"]
        self.assertEqual(snap["calculations"][0]["result"]["net_hours"], 8.0)
        self.assertEqual(snap["content_hash"], snap["content_hash"])
        self.assertEqual(calc["result"]["net_person_days"], 1.0)

    def test_cli_structured_io(self):
        env = dict(__import__("os").environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        out = subprocess.run(
            [sys.executable, "-m", "qcc_copilot", "version"],
            capture_output=True, text=True, env=env, cwd=str(ROOT),
        )
        body = json.loads(out.stdout)
        self.assertTrue(body["ok"])
        self.assertEqual(body["data"]["version"], "0.1.0")

        inp = Path(base := new_base()) / "req.json"
        inp.write_text(json.dumps({"workspace": base, "topic_id": "cli-t",
                                   "title": "CLI", "owner": "甲"}), encoding="utf-8")
        out2 = subprocess.run(
            [sys.executable, "-m", "qcc_copilot", "workspace.init", "--input", str(inp)],
            capture_output=True, text=True, env=env, cwd=str(ROOT),
        )
        body2 = json.loads(out2.stdout)
        self.assertTrue(body2["ok"])
        self.assertEqual(body2["data"]["topic_id"], "cli-t")

    def test_cli_error_is_structured(self):
        env = dict(__import__("os").environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        inp = Path(new_base()) / "req.json"
        inp.write_text(json.dumps({"workspace": str(inp.parent)}), encoding="utf-8")
        out = subprocess.run(
            [sys.executable, "-m", "qcc_copilot", "workspace.resume", "--input", str(inp)],
            capture_output=True, text=True, env=env, cwd=str(ROOT),
        )
        body = json.loads(out.stdout)
        self.assertFalse(body["ok"])
        self.assertIn("code", body["error"])


if __name__ == "__main__":
    unittest.main()
