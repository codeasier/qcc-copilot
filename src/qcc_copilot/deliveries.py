from __future__ import annotations

from .contracts import blank, validate
from .util import new_id, read_json, utc_now, write_json


def _source_index(ws):
    try:
        doc = ws.load_sources()
    except Exception:
        doc = {"sources": []}
    out = []
    for s in doc.get("sources", []):
        out.append(
            {
                "source_id": s.get("source_id", s.get("locator", "")),
                "locator": s.get("locator", ""),
                "version": s.get("version"),
                "status": s.get("status", "unknown"),
            }
        )
    return out


def create_snapshot(ws):
    """固定课题/规则/证据/计算清单；历史材料保留原依据，不被当前数据改写。"""
    topic = ws.load()
    delivery_id = new_id("delivery")
    ddir = ws.deliveries_dir / delivery_id
    ddir.mkdir(parents=True, exist_ok=True)
    snapshot = blank(
        "delivery_snapshot",
        delivery_id=delivery_id,
        topic_id=topic["topic_id"],
        topic_revision=topic["revision"],
        content_hash=topic["content_hash"],
        rule_profile=dict(topic["rule_profile"]),
        sources=_source_index(ws),
        calculations=[
            {
                "calculation_id": c["calculation_id"],
                "kind": c.get("kind"),
                "scenario": c.get("scenario"),
                "result": c.get("result"),
                "needs_review": c.get("needs_review", False),
            }
            for c in topic.get("calculations", [])
        ],
        claims=[
            {
                "claim_id": c["claim_id"],
                "text": c.get("text"),
                "origin": c.get("origin"),
                "category": c.get("category", ""),
                "support": c.get("support"),
                "needs_review": c.get("needs_review", False),
            }
            for c in topic.get("claims", [])
        ],
        created_at=utc_now(),
        material_status="draft",
        checks={},
    )
    validate("delivery_snapshot", snapshot)
    write_json(ddir / "snapshot.json", snapshot)

    topic, rev, hsh = ws.snapshot()
    topic.setdefault("deliveries", []).append(
        {"delivery_id": delivery_id, "created_at": snapshot["created_at"],
         "topic_revision": snapshot["topic_revision"], "needs_review": False}
    )
    ws.save(topic, rev, hsh)
    return snapshot


def get_snapshot(ws, delivery_id):
    path = ws.deliveries_dir / delivery_id / "snapshot.json"
    if not path.exists():
        return None
    return validate("delivery_snapshot", read_json(path))


def _write_snapshot(ws, snapshot):
    validate("delivery_snapshot", snapshot)
    write_json(ws.deliveries_dir / snapshot["delivery_id"] / "snapshot.json", snapshot)


def flag_stale(ws, delivery_id, affected_parts):
    snapshot = get_snapshot(ws, delivery_id)
    if not snapshot:
        return None
    checks = snapshot.setdefault("checks", {})
    checks["evidence_stale"] = True
    checks["stale_parts"] = sorted(set(affected_parts))
    checks["stale_note"] = "引用的证据或计算已变化，需重新核验与生成；历史快照保留原依据"
    _write_snapshot(ws, snapshot)
    return snapshot


def set_material_status(ws, delivery_id, status, checks=None):
    snapshot = get_snapshot(ws, delivery_id)
    if not snapshot:
        return None
    snapshot["material_status"] = status
    if checks:
        snapshot["checks"].update(checks)
    _write_snapshot(ws, snapshot)
    return snapshot


def list_snapshots(ws):
    out = []
    if not ws.deliveries_dir.exists():
        return out
    for d in sorted(ws.deliveries_dir.iterdir()):
        p = d / "snapshot.json"
        if p.exists():
            s = read_json(p)
            out.append(
                {"delivery_id": s.get("delivery_id"), "topic_revision": s.get("topic_revision"),
                 "material_status": s.get("material_status"), "created_at": s.get("created_at")}
            )
    return out
