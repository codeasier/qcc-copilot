import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestDistribution(unittest.TestCase):
    def test_all_versioned_resources_load(self):
        from qcc_copilot import methods, util

        mani = util.load_json_resource("manifest.json")
        for rel in mani["resources"]["schemas"]:
            util.load_json_resource(rel)
        for rel in mani["resources"]["methods"]:
            util.load_json_resource(rel)
        for rel in mani["resources"]["templates"]:
            util.load_text_resource(rel)
        self.assertEqual(methods.profile_summary()["id"], "qcc-three-dimensions")
        self.assertFalse(methods.profile_summary()["official_scoring_configured"])

    def test_install_from_new_directory(self):
        """从新目录安装后资源齐全：复制包到临时位置，换工作目录仍能加载契约/方法/模板。"""
        src = ROOT / "src" / "qcc_copilot"
        tmp = Path(tempfile.mkdtemp(prefix="qcc-dist-"))
        dest = tmp / "pkg" / "qcc_copilot"
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        env = dict(os.environ)
        env["PYTHONPATH"] = str(dest.parent)

        def run(cmd, payload=None):
            args = [sys.executable, "-m", "qcc_copilot", cmd]
            if payload is not None:
                args += ["--input", "-"]
            p = subprocess.run(args, input=(json.dumps(payload) if payload is not None else None),
                               capture_output=True, text=True, env=env, cwd=str(tmp))
            return json.loads(p.stdout)

        caps = run("capabilities")
        self.assertTrue(caps["ok"])
        self.assertTrue(caps["data"]["core"]["stdlib_ooxml_pptx"])

        types = run("contract.types")
        self.assertTrue(types["ok"])
        self.assertIn("topic", types["data"]["types"])

        profile = run("methods.profile")
        self.assertTrue(profile["ok"])
        self.assertEqual(profile["data"]["id"], "qcc-three-dimensions")


    def test_cli_input_modes(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        base = tempfile.mkdtemp(prefix="qcc-cli-")

        def run(args, stdin_text=None):
            p = subprocess.run(
                [sys.executable, "-m", "qcc_copilot", *args],
                input=stdin_text, capture_output=True, text=True, env=env,
            )
            return json.loads(p.stdout)

        inline = run(["workspace.init", "--input",
                      json.dumps({"workspace": base, "topic_id": "t1"})])
        self.assertTrue(inline["ok"])
        piped = run(["workspace.init"],
                    json.dumps({"workspace": base, "topic_id": "t2"}))
        self.assertTrue(piped["ok"])
        dash = run(["workspace.init", "--input", "-"],
                   json.dumps({"workspace": base, "topic_id": "t3"}))
        self.assertTrue(dash["ok"])
        missing = run(["workspace.init", "--input", "/nonexistent/req.json"])
        self.assertFalse(missing["ok"])
        self.assertEqual(missing["error"]["code"], "qcc_error")

    def test_skill_ships_with_package(self):
        from importlib import resources

        root = resources.files("qcc_copilot").joinpath("skill")
        self.assertTrue(root.joinpath("SKILL.md").is_file())
        self.assertTrue(root.joinpath("references", "commands.md").is_file())
        self.assertIn("name: qcc-copilot", root.joinpath("SKILL.md").read_text(encoding="utf-8"))

    def test_skill_export(self):
        from qcc_copilot import skillpack
        from qcc_copilot.errors import QccError

        dest = Path(tempfile.mkdtemp(prefix="qcc-skill-")) / "qcc-copilot"
        out = skillpack.export(str(dest))
        self.assertEqual(out["dest"], str(dest.resolve()))
        self.assertEqual(out["skill"], "qcc-copilot")
        self.assertTrue((dest / "SKILL.md").is_file())
        self.assertTrue((dest / "references" / "support-matrix.md").is_file())
        self.assertGreaterEqual(len(out["files"]), 15)
        with self.assertRaises(QccError):
            skillpack.export(str(dest))
        forced = skillpack.export(str(dest), force=True)
        self.assertEqual(len(forced["files"]), len(out["files"]))


if __name__ == "__main__":
    unittest.main()
