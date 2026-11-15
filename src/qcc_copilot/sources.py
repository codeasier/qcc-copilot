from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path

from .contracts import blank, validate
from .util import canonical_json, stable_key


def remote_input_boundary():
    """宿主读取远端资料的统一输入边界说明。"""
    return {
        "boundary": "远端来源（Issue/PR/办公文档/运行平台）由宿主用其已有工具读取，"
                    "或由用户提供导出文件；来源适配器只输出统一 sources_doc 契约，"
                    "不为每个来源另建认证系统。",
        "accepted": ["inline content", "local export file (csv/json/text)"],
        "when_absent": "status=unread，记录未覆盖原因，不把未读当作无问题",
    }


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _index_one(base: Path, spec, max_bytes: int):
    kind = spec.get("kind", "file")
    locator = spec.get("locator", "")
    source_id = spec.get("source_id") or (Path(locator).stem if locator else stable_key(kind, locator))
    rec = {
        "source_id": source_id,
        "kind": kind,
        "locator": locator,
        "status": "unread",
        "version": None,
        "note": "",
        "bytes_total": 0,
        "bytes_indexed": 0,
        "truncated": False,
    }

    if spec.get("simulate_failure"):
        rec["status"] = "failed"
        rec["note"] = "读取/解析失败（模拟）"
        return rec

    if kind in ("remote", "connector"):
        content = spec.get("content")
        if content is None:
            rec["status"] = "unread"
            rec["note"] = "远端来源需宿主读取后以统一导出(content/本地文件)提供"
            rec["boundary"] = remote_input_boundary()
            return rec
        raw = content.encode("utf-8") if isinstance(content, str) else canonical_json(content).encode("utf-8")
        rec["status"] = "read"
        rec["version"] = _hash_bytes(raw)
        rec["bytes_total"] = len(raw)
        rec["bytes_indexed"] = len(raw)
        rec["note"] = "宿主提供的统一导出"
        return rec

    if spec.get("content") is not None:
        content = spec["content"]
        raw = content.encode("utf-8") if isinstance(content, str) else canonical_json(content).encode("utf-8")
        rec["status"] = "read"
        rec["version"] = _hash_bytes(raw)
        rec["bytes_total"] = len(raw)
        rec["bytes_indexed"] = len(raw)
        if kind == "csv":
            try:
                rec["rows"] = sum(1 for _ in csv.reader(io.StringIO(raw.decode("utf-8")))) - 1
            except Exception:
                rec["rows"] = None
        elif kind == "json":
            try:
                json.loads(raw.decode("utf-8"))
                rec["parsed"] = True
            except Exception:
                rec["parsed"] = False
                rec["note"] = "JSON 解析失败"
        return rec

    if kind == "git":
        return _index_git(base, spec, rec)

    # 本地文件：text/md/csv/json
    path = (base / locator) if not Path(locator).is_absolute() else Path(locator)
    if not path.exists():
        rec["status"] = "failed"
        rec["note"] = "文件不存在"
        return rec
    try:
        data = path.read_bytes()
    except Exception as exc:
        rec["status"] = "failed"
        rec["note"] = f"读取失败: {exc}"
        return rec
    rec["bytes_total"] = len(data)
    rec["version"] = _hash_bytes(data)
    if len(data) > max_bytes:
        rec["status"] = "truncated"
        rec["truncated"] = True
        rec["bytes_indexed"] = max_bytes
        rec["note"] = f"超出读取预算 {max_bytes} 字节，仅索引前段；未读部分不可当作已检查"
    else:
        rec["status"] = "read"
        rec["bytes_indexed"] = len(data)
    return rec


def _index_git(base: Path, spec, rec):
    limit = int(spec.get("git_log_limit", 20))
    try:
        head = subprocess.run(
            ["git", "-C", str(base), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        log = subprocess.run(
            ["git", "-C", str(base), "log", "--oneline", "-n", str(limit)],
            capture_output=True, text=True, timeout=10,
        )
        if head.returncode != 0 or log.returncode != 0:
            rec["status"] = "failed"
            rec["note"] = "非 git 仓库或 git 不可用"
            return rec
        rec["status"] = "read"
        rec["version"] = head.stdout.strip()
        rec["commit_lines"] = [l for l in log.stdout.splitlines() if l.strip()]
        rec["note"] = f"git log 最近 {len(rec['commit_lines'])} 条"
    except Exception as exc:
        rec["status"] = "failed"
        rec["note"] = f"git 读取失败: {exc}"
    return rec


def index_sources(base, source_specs, max_bytes=65536):
    """来源索引与覆盖：失败、未读、截断、可用版本分别记录。"""
    base = Path(base)
    records = [_index_one(base, s, int(max_bytes)) for s in source_specs]
    counts = {"read": 0, "unread": 0, "failed": 0, "truncated": 0}
    for r in records:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    unread_or_failed = [r["locator"] for r in records if r["status"] != "read"]
    coverage = {
        "total": len(records),
        "counts": counts,
        "full_coverage": all(r["status"] == "read" for r in records),
        "unread_or_failed": unread_or_failed,
        "boundary_note": "分析结论仅覆盖已读部分；未读/失败/截断不可表述为全范围已检查或不存在改进机会",
        "max_bytes": int(max_bytes),
    }
    doc = blank(
        "sources_doc",
        sources=records,
        coverage=coverage,
        requested_scope=[s.get("locator", "") for s in source_specs],
    )
    doc["remote_boundary"] = remote_input_boundary()
    validate("sources_doc", doc)
    return doc


def save_index(ws, doc):
    ws.save_sources(doc)
    return doc
