from __future__ import annotations

import json

from . import FORMAT_VERSION
from .contracts import blank, validate
from .errors import ContractError, UnknownFormatVersion
from .util import canonical_json, content_hash as _hash, new_id, utc_now, write_json, write_text

# 语义内容摘要排除"格式标识"与"导出时间"：仅导出时间变化不参与冲突判断。
_HASH_EXCLUDE = {"content_hash", "exported_at", "schema_version", "format_version"}


def summary_semantic(s):
    return {k: v for k, v in s.items() if k not in _HASH_EXCLUDE}


def compute_summary_hash(s):
    return _hash(summary_semantic(s))


def export_summary(ws):
    """按需导出标准摘要，保留缺口与假设，不把估算写成已实现成果。"""
    topic = ws.load()
    claims = topic.get("claims", [])
    s = blank(
        "summary",
        format_version=FORMAT_VERSION,
        topic_id=topic["topic_id"],
        revision=topic["revision"],
        owner=topic.get("owner", ""),
        problem=(topic.get("problem", {}) or {}).get("statement", ""),
        benefit={
            "calculations": [c["calculation_id"] for c in topic.get("calculations", [])],
            "status": "measured_only_if_supported",
            "note": "收益状态沿用课题档案，不因汇总改写估算为已实现",
        },
        reuse={"status": topic.get("reuse", {}).get("status", "not_recorded"),
               "note": "潜在适用/复现/实际采用分开"},
        dimensions={
            "value": _dim_status(claims, "benefit"),
            "reuse": _dim_status(claims, "reuse"),
            "method": _dim_status(claims, "effect"),
        },
        stage=topic.get("status", {}).get("stage", "topic"),
        gaps=[t["description"] for t in topic.get("tasks", []) if not t.get("closed")],
        next=topic.get("next", ""),
        status={"claims_needing_review": [c["claim_id"] for c in claims if c.get("needs_review")]},
        exported_at=utc_now(),
        source_scope_note="标准摘要包不含全部原始代码/日志/数据；负责人不声称已独立核验未提供依据",
    )
    s["content_hash"] = compute_summary_hash(s)
    validate("summary", s)
    ws.exports_dir.mkdir(parents=True, exist_ok=True)
    write_json(ws.exports_dir / f"summary-{s['topic_id']}-r{s['revision']}.json", s)
    write_text(ws.exports_dir / f"summary-{s['topic_id']}-r{s['revision']}.md", _summary_md(s))
    return s


def _dim_status(claims, category):
    rel = [c for c in claims if c.get("category") == category]
    if not rel:
        return "无记录"
    if any(c.get("support") == "conflicting" for c in rel):
        return "有冲突"
    if all(c.get("support") == "supported" and not c.get("needs_review") for c in rel):
        return "已支持"
    return "待核验"


def _summary_md(s):
    from .deliverables import render_template

    return render_template("summary.md.tpl", {
        "title": f"课题 {s['topic_id']}", "topic_id": s["topic_id"],
        "format_version": s["format_version"], "revision": s["revision"],
        "exported_at": s["exported_at"], "owner": s.get("owner", ""),
        "stage": s.get("stage", ""), "problem": s.get("problem", ""),
        "benefit": json.dumps(s.get("benefit", {}), ensure_ascii=False),
        "reuse": json.dumps(s.get("reuse", {}), ensure_ascii=False),
        "dimensions": json.dumps(s.get("dimensions", {}), ensure_ascii=False),
        "gaps": "\n".join(f"- {g}" for g in s.get("gaps", [])) or "（无）",
        "next": s.get("next", ""),
        "source_scope_note": s.get("source_scope_note", ""),
    })


def normalize_summary(raw):
    s = dict(raw)
    s.setdefault("format_version", FORMAT_VERSION)
    s.setdefault("exported_at", utc_now())
    s["content_hash"] = compute_summary_hash(s)
    return s


def import_summary(raw):
    """导入校验：未知版本或缺标识不破坏已有聚合，返回明确错误。"""
    try:
        s = normalize_summary(raw)
        validate("summary", s)
        return {"ok": True, "summary": s}
    except (ContractError, UnknownFormatVersion) as exc:
        return {"ok": False, "error": exc.as_dict()}


def aggregate(summaries):
    """按标识+修订+语义内容摘要聚合；重复/旧版/更新版/冲突分别处理。"""
    topics, history, conflicts, audit, invalid = {}, [], [], [], []
    for raw in summaries:
        imp = import_summary(raw)
        if not imp["ok"]:
            invalid.append({"error": imp["error"], "topic_id": raw.get("topic_id")})
            continue
        s = imp["summary"]
        tid, rev, hsh = s["topic_id"], s["revision"], s["content_hash"]
        history.append({"topic_id": tid, "revision": rev, "exported_at": s.get("exported_at"),
                        "content_hash": hsh})
        cur = topics.get(tid)
        if cur is None:
            topics[tid] = {"summary": s, "revision": rev, "content_hash": hsh}
            audit.append({"topic_id": tid, "revision": rev, "action": "new"})
            continue
        if rev < cur["revision"]:
            audit.append({"topic_id": tid, "revision": rev, "action": "older_skip_no_rollback",
                          "note": "保留导入审计，不回退当前聚合"})
        elif rev > cur["revision"]:
            topics[tid] = {"summary": s, "revision": rev, "content_hash": hsh}
            audit.append({"topic_id": tid, "revision": rev, "action": "update_higher_revision"})
        else:
            if hsh == cur["content_hash"]:
                audit.append({"topic_id": tid, "revision": rev, "action": "duplicate_skip",
                              "note": "相同标识/修订/语义内容，或仅导出时间变化；不重复计数"})
            else:
                conflicts.append(
                    {"topic_id": tid, "revision": rev,
                     "current_content_hash": cur["content_hash"], "incoming_content_hash": hsh,
                     "note": "同版本不同内容，保留冲突及双方来源，不自动择一"}
                )
                audit.append({"topic_id": tid, "revision": rev, "action": "conflict_kept"})
    return {
        "topics": {t: v["summary"] for t, v in topics.items()},
        "conflicts": conflicts, "history": history, "audit": audit, "invalid": invalid,
        "counts": {"topics": len(topics), "conflicts": len(conflicts),
                   "invalid": len(invalid), "duplicates": sum(1 for a in audit if a["action"] == "duplicate_skip"),
                   "older_skips": sum(1 for a in audit if a["action"] == "older_skip_no_rollback")},
        "note": "聚合只表示已导入快照；尚未收到新摘要不解释为实时无进展",
    }


def aggregate_views(agg):
    rows = []
    lines = ["# 负责人轻量汇总（已导入快照）", "",
             "> 仅反映各摘要导出时的快照；陈旧/冲突/缺失可见，未收到更新不代表课题无进展。", ""]
    for tid, s in agg["topics"].items():
        conflict = any(c["topic_id"] == tid for c in agg["conflicts"])
        dims = s.get("dimensions", {})
        lines += [f"## {tid}（修订 {s['revision']} · 快照 {s.get('exported_at')}）",
                  f"- 阶段：{s.get('stage')}｜负责人：{s.get('owner', '')}",
                  f"- 三维：价值 {dims.get('value')} / 推广 {dims.get('reuse')} / 方法 {dims.get('method')}",
                  f"- 关键缺口：{', '.join(s.get('gaps', [])) or '（无）'}",
                  f"- 下一步：{s.get('next', '')}",
                  f"- 冲突：{'是（同版本不同内容，需人工确认）' if conflict else '否'}",
                  "- 更新状态：仅最新导入快照；未收到后续导入时进展未知", ""]
        rows.append({
            "topic_id": tid, "revision": s["revision"], "stage": s.get("stage", ""),
            "value": dims.get("value", ""), "reuse": dims.get("reuse", ""),
            "method": dims.get("method", ""), "gaps": "|".join(s.get("gaps", [])),
            "next": s.get("next", ""), "exported_at": s.get("exported_at", ""),
            "conflict": conflict, "freshness": "snapshot_only",
        })
    csv_lines = []
    if rows:
        cols = list(rows[0].keys())
        csv_lines.append(",".join(cols))
        for r in rows:
            csv_lines.append(",".join(str(r[c]).replace(",", ";") for c in cols))
    return {"markdown": "\n".join(lines), "csv": "\n".join(csv_lines), "rows": rows,
            "conflicts_visible": True, "snapshot_time_visible": True}


def export_feedback(topic_id, target_revision, author, content, ws=None):
    fb = blank("feedback", feedback_id=new_id("fb"), topic_id=topic_id,
               target_revision=int(target_revision), author=author, content=content,
               created_at=utc_now())
    validate("feedback", fb)
    if ws:
        ws.exports_dir.mkdir(parents=True, exist_ok=True)
        write_json(ws.exports_dir / f"feedback-{fb['feedback_id']}.json", fb)
    return fb


def import_feedback(ws, feedback):
    """反馈进入建议/待办，不自动改变事实、收益或验证状态；旧修订标差异。"""
    validate("feedback", dict(feedback))
    topic, rev, hsh = ws.snapshot()
    current_rev = topic["revision"]
    diff = feedback["target_revision"] < current_rev
    entry = {
        "feedback_id": feedback["feedback_id"], "author": feedback["author"],
        "content": feedback["content"], "target_revision": feedback["target_revision"],
        "version_diff": diff, "created_at": feedback["created_at"],
        "role": "suggestion_or_todo",
    }
    topic.setdefault("feedback", []).append(entry)
    topic.setdefault("tasks", []).append(
        {"task_id": new_id("task"), "fact_key": "lead_feedback", "stage": "guidance",
         "description": f"负责人反馈: {feedback['content']}", "needed_evidence": "成员后续处理",
         "closed": False, "created_at": utc_now(),
         "version_diff_note": "反馈针对旧修订，标明版本差异供成员处理" if diff else ""}
    )
    ws.save(topic, rev, hsh)
    return {"imported": True, "role": "suggestion_or_todo", "version_diff": diff,
            "facts_changed": False, "benefit_changed": False, "verification_changed": False}
