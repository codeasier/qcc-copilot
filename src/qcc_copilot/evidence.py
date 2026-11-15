from __future__ import annotations

from .contracts import blank, validate
from .errors import ContractError
from .util import new_id, utc_now

# 主张来源(origin)与支持状态(support)是两组独立属性。
ORIGINS = ["record", "member_statement", "ai_inference", "estimate", "example"]
SUPPORTS = ["unverified", "supported", "insufficient", "conflicting"]

# 只有"上线/功能存在"类证据，不能证明收益/效果/采用。
_LAUNCH_ONLY_PROVES = {"deployment", "feature_present", "link", "上线"}
_VALUE_PROVES = {"effect", "measurement", "usage", "adoption", "工时", "收益", "采用"}
_STRONG_VERIFICATION = {"measurement", "effect_verification", "causal_verification", "usage_record"}


def evaluate_support(claim):
    """确定性地判定支持状态，避免把口述/链接/自评当成实测或充分证据。"""
    reasons = []
    if claim.get("conflicts"):
        return "conflicting", ["存在冲突来源，保留双方，不静默择一"]

    origin = claim.get("origin")
    category = claim.get("category", "")
    evidence = claim.get("evidence", []) or []
    verification = claim.get("verification", []) or []
    measured = any(v.get("supports") and v.get("kind") in _STRONG_VERIFICATION for v in verification)

    if origin == "member_statement":
        if not measured:
            return "unverified", ["成员口述无测量/核验记录，不自动成为实测或已支持"]
        reasons.append("成员口述有测量记录支持")

    # 收益/效果/推广类主张：上线链接不足以证明
    if category in ("benefit", "effect", "reuse", "adoption") and evidence:
        proves = set()
        for ev in evidence:
            proves |= set(ev.get("proves", []) or [])
        if not (proves & _VALUE_PROVES):
            if not measured:
                return "insufficient", ["引用仅证明功能上线/存在，不能证明收益、效果或采用"]
            reasons.append("证据本身不直接证明收益，但有独立测量核验")

    if measured and any(
        set(ev.get("proves", []) or []) & _VALUE_PROVES for ev in evidence
    ):
        return "supported", reasons + ["存在可定位证据与相应核验记录"]
    if measured:
        return "supported", reasons + ["存在核验记录"]
    return "unverified", reasons + ["尚无充分证据或核验记录"]


def make_claim(*, text, origin, category="", evidence=None, verification=None,
               depends_on=None, requested_support=None, claim_id=None, conflicts=None):
    support, reasons = evaluate_support(
        {
            "origin": origin,
            "category": category,
            "evidence": evidence or [],
            "verification": verification or [],
            "conflicts": conflicts or [],
        }
    )
    claim = blank(
        "claim",
        claim_id=claim_id or new_id("claim"),
        text=text,
        origin=origin,
        category=category,
        support=support,
        evidence=evidence or [],
        verification=verification or [],
        needs_review=False,
        depends_on=depends_on or [],
    )
    claim["support_reasons"] = reasons
    if conflicts:
        claim["conflicts"] = conflicts
    # 即便宿主请求更高状态，也以规则为准，并记录被降级的请求。
    if requested_support and requested_support != support:
        claim["requested_support"] = requested_support
        claim["downgraded_from"] = requested_support
    validate("claim", claim)
    return claim


def idempotent_event(topic, dedup_key, event):
    """相同输入重跑不重复创建业务事实；返回 (created, event_or_none)。"""
    events = topic.setdefault("events", [])
    for e in events:
        if e.get("dedup_key") == dedup_key:
            return False, e
    record = dict(event)
    record.update({"id": new_id("evt"), "dedup_key": dedup_key, "at": utc_now()})
    events.append(record)
    return True, record


def build_dependency_edges(topic):
    edges = []
    for c in topic.get("claims", []):
        if c.get("depends_on"):
            edges.append((c["claim_id"], "claim", list(c["depends_on"])))
    for calc in topic.get("calculations", []):
        if calc.get("depends_on"):
            edges.append((calc["calculation_id"], "calculation", list(calc["depends_on"])))
    for dep in topic.get("dependencies", []):
        edges.append((dep["derived_id"], dep.get("kind", "derived"), list(dep.get("depends_on", []))))
    for d in topic.get("deliveries", []):
        did = d.get("delivery_id")
        if did:
            deps = d.get("depends_on") or [c["claim_id"] for c in topic.get("claims", [])]
            deps += [calc["calculation_id"] for calc in topic.get("calculations", [])]
            edges.append((did, "delivery", deps))
    return edges


def compute_invalidation(topic, changed_ids):
    """定向失效：仅使依赖受影响来源/输入的派生结果失去当前有效状态。"""
    changed = set(changed_ids)
    affected = set(changed)
    edges = build_dependency_edges(topic)
    progress = True
    while progress:
        progress = False
        for derived, _kind, deps in edges:
            if derived not in affected and (set(deps) & affected):
                affected.add(derived)
                progress = True

    derived_ids = affected - changed
    touched_claims, touched_calcs, touched_deliveries = [], [], []
    for c in topic.get("claims", []):
        if c["claim_id"] in derived_ids:
            c["needs_review"] = True
            touched_claims.append(c["claim_id"])
    for calc in topic.get("calculations", []):
        if calc["calculation_id"] in derived_ids:
            calc["needs_review"] = True
            touched_calcs.append(calc["calculation_id"])
    for d in topic.get("deliveries", []):
        if d.get("delivery_id") in derived_ids:
            d["needs_review"] = True
            touched_deliveries.append(d["delivery_id"])
    return {
        "changed_ids": sorted(changed),
        "affected_derived_claims": touched_claims,
        "affected_derived_calculations": touched_calcs,
        "affected_deliveries": touched_deliveries,
        "unrelated_reset": False,
    }


def invalidate(ws, changed_ids, change_note=""):
    def mutate(topic):
        result = compute_invalidation(topic, changed_ids)
        created, _ = idempotent_event(
            topic,
            dedup_key="|".join(sorted(changed_ids)) + "|" + change_note,
            event={"type": "source_or_input_change", "changed_ids": sorted(changed_ids), "note": change_note},
        )
        topic["_last_invalidation"] = {**result, "event_created": created}
        return result

    topic, rev, hsh = ws.snapshot()
    result = mutate(topic)
    ws.save(topic, rev, hsh)
    return result


def add_claim(ws, spec):
    claim = make_claim(**spec)
    topic, rev, hsh = ws.snapshot()
    topic["claims"].append(claim)
    ws.save(topic, rev, hsh)
    return claim


def add_conflict(ws, claim_id, conflicting_source):
    """保留冲突双方来源与核验事项，不选择更有利于评奖的结论。"""
    topic, rev, hsh = ws.snapshot()
    target = next((c for c in topic["claims"] if c["claim_id"] == claim_id), None)
    if target is None:
        raise ContractError(f"claim '{claim_id}' not found")
    target.setdefault("conflicts", []).append(conflicting_source)
    target["support"] = "conflicting"
    target.setdefault("verification", []).append(
        {"id": new_id("ver"), "kind": "conflict_review", "supports": False,
         "note": "需人工核验冲突来源，不静默择一", "at": utc_now()}
    )
    ws.save(topic, rev, hsh)
    return target


def link_dependency(ws, derived_id, kind, depends_on):
    topic, rev, hsh = ws.snapshot()
    topic.setdefault("dependencies", [])
    topic["dependencies"] = [d for d in topic["dependencies"] if d["derived_id"] != derived_id]
    topic["dependencies"].append(
        {"derived_id": derived_id, "kind": kind, "depends_on": list(depends_on)}
    )
    ws.save(topic, rev, hsh)
    return topic["dependencies"]
