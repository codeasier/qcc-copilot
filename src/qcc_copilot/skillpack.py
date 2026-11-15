from __future__ import annotations

from importlib import resources
from pathlib import Path

from . import __version__
from .errors import QccError


def _skill_root():
    return resources.files("qcc_copilot").joinpath("skill")


def _iter_files():
    root = _skill_root()
    for entry in sorted(root.iterdir(), key=lambda item: item.name):
        if entry.is_file():
            yield entry.name, entry
        elif entry.is_dir() and entry.name == "references":
            for sub in sorted(entry.iterdir(), key=lambda item: item.name):
                if sub.is_file():
                    yield f"references/{sub.name}", sub


def export(dest: str, force: bool = False):
    """把包内 Skill 文档导出到宿主 skills 目录；不覆盖非空目录，除非 force=true。"""
    if not dest:
        raise QccError("missing required field 'dest'")
    target = Path(dest).expanduser().resolve()
    if target.exists() and not target.is_dir():
        raise QccError(f"destination '{target}' is not a directory")
    if target.exists() and any(target.iterdir()) and not force:
        raise QccError(
            f"destination '{target}' is not empty",
            details=["pass force=true to overwrite the exported skill files"],
        )
    target.mkdir(parents=True, exist_ok=True)
    exported = []
    for rel, entry in _iter_files():
        out = target / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(entry.read_bytes())
        exported.append(rel)
    return {"dest": str(target), "files": exported, "skill": "qcc-copilot", "version": __version__}
