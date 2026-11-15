from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path


# 课题文件中属于"账本记账"而非业务事实的键；内容摘要排除它们，
# 使人工修改业务内容能被检测，而仅推进修订号/时间戳不会制造冲突。
_BOOKKEEPING_KEYS = {"revision", "updated_at", "content_hash"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def semantic_projection(topic: dict) -> dict:
    return {k: v for k, v in topic.items() if k not in _BOOKKEEPING_KEYS}


def content_hash(topic_or_semantic) -> str:
    if isinstance(topic_or_semantic, dict) and "schema_version" in topic_or_semantic:
        topic_or_semantic = semantic_projection(topic_or_semantic)
    return hashlib.sha256(canonical_json(topic_or_semantic).encode("utf-8")).hexdigest()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def stable_key(*parts) -> str:
    """由输入确定的去重键；相同输入重跑得到相同键（不制造新业务事实）。"""
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()[:24]


def read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj) -> None:
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_text(path, text: str) -> None:
    """原子写入：临时文件 + os.replace，避免半写文件。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".qcc-tmp-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)


def atomic_bytes(path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".qcc-tmp-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        tmp = None
    finally:
        if tmp is not None and os.path.exists(tmp):
            os.unlink(tmp)


def load_text_resource(relpath: str) -> str:
    """从包内 resources/ 加载文本资源（可分发、不依赖工作目录）。"""
    from importlib import resources

    base = resources.files("qcc_copilot").joinpath("resources")
    return base.joinpath(relpath).read_text(encoding="utf-8")


def load_json_resource(relpath: str):
    return json.loads(load_text_resource(relpath))
