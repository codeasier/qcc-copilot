from __future__ import annotations

import fcntl
import json
from contextlib import contextmanager
from pathlib import Path

from . import DEFAULT_RULE_PROFILE, DEFAULT_RULE_VERSION
from .contracts import blank, validate
from .errors import (
    AmbiguousWorkspace,
    DamagedWorkspace,
    RevisionConflict,
    WorkspaceNotFound,
)
from .util import content_hash, new_id, read_json, utc_now, write_json


def make_rule_profile(profile_id=DEFAULT_RULE_PROFILE, version=DEFAULT_RULE_VERSION):
    return {"id": profile_id, "version": version}


def make_topic(topic_id: str, *, title="", owner="", problem=None, rule_profile=None):
    topic = blank(
        "topic",
        topic_id=topic_id,
        revision=0,
        title=title,
        owner=owner,
        problem=problem or {},
        rule_profile=rule_profile or make_rule_profile(),
        status={"stage": "topic", "structure": {}, "evidence": {}},
        claims=[],
        sources=[],
        calculations=[],
        reuse={},
        deliveries=[],
        feedback=[],
        events=[],
        dependencies=[],
        tasks=[],
        next="描述问题并确认受益对象",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    topic["content_hash"] = content_hash(topic)
    return topic


def make_sources_doc():
    return blank("sources_doc", sources=[], coverage={}, requested_scope=[])


class Workspace:
    """显式工作区：一个课题一个 .qcc/<topic-id>/ 目录。"""

    def __init__(self, base, topic_id: str):
        self.base = Path(base)
        self.topic_id = topic_id
        self.root = self.base / ".qcc"
        self.dir = self.root / topic_id
        self.topic_path = self.dir / "topic.json"
        self.sources_path = self.dir / "sources.json"
        self.revisions_dir = self.dir / "revisions"
        self.calculations_dir = self.dir / "calculations"
        self.deliveries_dir = self.dir / "deliveries"
        self.exports_dir = self.dir / "exports"
        self.lock_path = self.dir / ".write.lock"

    def _dirs(self):
        return [
            self.dir,
            self.revisions_dir,
            self.calculations_dir,
            self.deliveries_dir,
            self.exports_dir,
        ]

    @contextmanager
    def _lock(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        with open(self.lock_path, "w") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)

    def exists(self) -> bool:
        return self.topic_path.exists()

    def _load_raw(self):
        try:
            with open(self.topic_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise DamagedWorkspace(
                f"topic.json 无法解析 ({exc})；保留原档案并报告恢复/迁移要求",
                details=[str(self.topic_path)],
            )

    def load(self):
        raw = self._load_raw()
        try:
            return validate("topic", raw)
        except Exception as exc:
            raise DamagedWorkspace(
                f"课题档案格式不受支持或校验失败 ({exc})；保留原档案，不以重新初始化冒充恢复",
                details=[str(self.topic_path), str(exc)],
            )

    def load_sources(self):
        if not self.sources_path.exists():
            return make_sources_doc()
        try:
            return validate("sources_doc", read_json(self.sources_path))
        except Exception as exc:
            raise DamagedWorkspace(
                f"sources.json 无法读取或校验失败 ({exc})；保留原档案",
                details=[str(self.sources_path)],
            )

    def save_sources(self, doc):
        validate("sources_doc", doc)
        write_json(self.sources_path, doc)

    @staticmethod
    def init(base, topic_id=None, *, title="", owner="", problem=None, rule_profile=None):
        topic_id = topic_id or new_id("topic")
        ws = Workspace(base, topic_id)
        if ws.topic_path.exists():
            ws.load()
            return {"created": False, "workspace": ws, "topic": ws.load()}
        for d in ws._dirs():
            d.mkdir(parents=True, exist_ok=True)
        topic = make_topic(topic_id, title=title, owner=owner, problem=problem, rule_profile=rule_profile)
        validate("topic", topic)
        write_json(ws.topic_path, topic)
        ws.save_sources(make_sources_doc())
        return {"created": True, "workspace": ws, "topic": topic}

    @staticmethod
    def list_topics(base):
        root = Path(base) / ".qcc"
        out = []
        if not root.exists():
            return out
        for d in sorted(root.iterdir()):
            if d.is_dir() and (d / "topic.json").exists():
                try:
                    t = read_json(d / "topic.json")
                    out.append(
                        {"topic_id": t.get("topic_id", d.name), "title": t.get("title", ""),
                         "revision": t.get("revision"), "path": str(d)}
                    )
                except Exception:
                    out.append({"topic_id": d.name, "title": "", "revision": None,
                                "path": str(d), "damaged": True})
        return out

    @staticmethod
    def route(base, topic_id=None):
        """多课题路由：目标明确前不覆盖任何已有档案。"""
        topics = Workspace.list_topics(base)
        if topic_id:
            for t in topics:
                if t["topic_id"] == topic_id:
                    return Workspace(base, t["topic_id"])
            raise WorkspaceNotFound(f"未找到课题工作区 '{topic_id}'", details=[topic_id])
        if not topics:
            raise WorkspaceNotFound("当前工作区根目录下没有课题档案", details=[str(base)])
        if len(topics) > 1:
            raise AmbiguousWorkspace(
                "存在多个可匹配工作区，请明确课题标识后再更新",
                details=[t["topic_id"] for t in topics],
            )
        return Workspace(base, topics[0]["topic_id"])

    @staticmethod
    def resume(base, topic_id=None):
        """跨会话恢复：从持久档案恢复阶段、未解决事项与下一步；损坏档案不视为空白新课题。"""
        ws = Workspace.route(base, topic_id)
        topic = ws.load()
        unresolved = [t for t in topic.get("tasks", []) if not t.get("closed")]
        deliverables = topic.get("deliveries", [])
        return {
            "topic_id": topic["topic_id"],
            "revision": topic["revision"],
            "rule_profile": topic["rule_profile"],
            "stage": topic.get("status", {}).get("stage"),
            "next": topic.get("next"),
            "unresolved_tasks": unresolved,
            "claims_needing_review": [
                c["claim_id"] for c in topic.get("claims", []) if c.get("needs_review")
            ],
            "reusable_deliverables": deliverables,
            "resumed_from_persisted_state": True,
        }

    def snapshot(self):
        topic = self.load()
        return topic, topic["revision"], topic["content_hash"]

    def _backup(self, current):
        rev = current.get("revision", 0)
        dst = self.revisions_dir / f"rev-{rev}-{utc_now().replace(':', '')}.json"
        write_json(dst, current)
        return str(dst)

    def save(self, topic_new, expected_revision: int, expected_hash: str):
        """以读取时的修订与内容摘要为前提原子写入；人工修改/并发写入保留原文件并报冲突。"""
        with self._lock():
            current = self._load_raw()
            cur_rev = current.get("revision")
            cur_hash = content_hash(current)
            if cur_rev != expected_revision or cur_hash != expected_hash:
                raise RevisionConflict(
                    "课题档案在读取后发生变化（人工修订或并发写入）；保留现有文件，"
                    "请基于新状态重新处理或明确合并",
                    details=[
                        f"expected_revision={expected_revision}, on_disk_revision={cur_rev}",
                        f"expected_hash={expected_hash[:12]}, on_disk_hash={cur_hash[:12]}",
                        str(self.topic_path),
                    ],
                )
            self._backup(current)
            new = dict(topic_new)
            new["revision"] = cur_rev + 1
            new["updated_at"] = utc_now()
            new["content_hash"] = content_hash(new)
            validate("topic", new)
            write_json(self.topic_path, new)
            return new

    def update(self, mutator):
        """便捷入口：load → mutator(topic) → save（带修订前提）。返回 new_topic。"""
        topic, rev, hsh = self.snapshot()
        mutator(topic)
        return self.save(topic, rev, hsh)
