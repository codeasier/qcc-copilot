from __future__ import annotations

import importlib.util
import shutil
import sys

from . import __version__


def _render_tool():
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return {"name": name, "path": found}
    mac = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    import os

    if os.path.exists(mac):
        return {"name": "libreoffice", "path": mac}
    return None


def independent_render(pptx_path):
    """独立渲染核验：优先 LibreOffice，其次 macOS Quick Look 的 Office 导入器。
    只证明文件可被真实渲染器打开，不证明逐页版式无缺陷；不可用返回 not_run。"""
    import os
    import platform
    import subprocess
    import tempfile

    renderer = _render_tool()
    if renderer:
        return {
            "status": "not_run",
            "renderer": renderer["name"],
            "reason": "已发现独立渲染器，但逐页版式核验需调用其转换流程；本环境未执行",
        }
    if platform.system() == "Darwin" and shutil.which("qlmanage"):
        tmp = tempfile.mkdtemp(prefix="qcc-render-")
        try:
            proc = subprocess.run(
                ["qlmanage", "-t", "-s", "160", "-o", tmp, str(pptx_path)],
                capture_output=True, text=True, timeout=60,
            )
            produced = [f for f in os.listdir(tmp) if f.endswith(".png")]
            return {
                "status": "passed" if produced else "failed",
                "renderer": "qlmanage (macOS Quick Look / Office 导入器)",
                "evidence": f"produced_thumbnail={bool(produced)}; rc={proc.returncode}",
                "note": "独立渲染器成功打开并渲染 PPTX；仅证明可打开，不证明逐页版式无缺陷，"
                        "溢出/占位符/缺图由结构化检查负责",
            }
        except Exception as exc:
            return {"status": "failed", "renderer": "qlmanage", "reason": str(exc)}
    return {
        "status": "not_run",
        "dependency": "未发现 LibreOffice/soffice，且当前非 macOS 或无 qlmanage",
        "reason": "缺少独立渲染能力；PPT 渲染检查未执行，不标为通过",
    }


def check():
    """启动时能力检查：明确可执行步骤与受限步骤，不把未执行检查标为通过。"""
    pptx_lib = importlib.util.find_spec("pptx") is not None
    renderer = _render_tool()
    limited = []
    if not renderer:
        limited.append(
            "渲染检查(render_check): 未发现 LibreOffice/soffice；"
            "在 macOS 尝试 Quick Look 独立打开核验，其余情况标记为未执行/受限，"
            "仅可做文件结构、占位符与可检测溢出检查"
        )
    if not pptx_lib:
        limited.append(
            "python-pptx 未安装：改用包内 stdlib OOXML 生成器（仍产出真实可编辑 PPTX）；"
            "该生成器不依赖 python-pptx"
        )
    return {
        "kernel_version": __version__,
        "python": sys.version.split()[0],
        "core": {
            "json_state": True,
            "deterministic_calc": True,
            "stdlib_ooxml_pptx": True,
            "official_scoring_configured": False,
        },
        "optional": {
            "python_pptx": pptx_lib,
            "renderer": renderer,
        },
        "limited_steps": limited,
        "executable_steps": [
            "workspace/状态/契约/来源索引/发现/方法/收益/推广/材料编译/PPTX 生成/摘要聚合/反馈",
        ],
    }
