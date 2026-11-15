from __future__ import annotations

from .contracts import blank, validate
from .util import new_id
from . import evidence as ev
from . import workspace as W


def refine_improvement(supplied):
    """提炼已有改进：区分实施事实、收益假设与待验证结果，不重做已有工作。"""
    facts = supplied.get("facts", []) or []
    feature_implemented = any(
        f.get("kind") in ("feature_implemented", "deployment") for f in facts
    )
    measured = supplied.get("measured_outcome")
    benefit_proven = bool(measured)
    adopted = supplied.get("adoption_by_other_teams")

    benefit_claim = None
    if supplied.get("benefit_claim"):
        benefit_claim = ev.make_claim(
            text=supplied["benefit_claim"],
            origin="member_statement",
            category="benefit",
            evidence=[{"source_id": f.get("source_id", ""), "proves": ["deployment"]}
                      for f in facts if f.get("kind") == "deployment"],
            requested_support="supported",
        )

    result = {
        "problem": supplied.get("description", ""),
        "implementation": {
            "status": supplied.get("implementation_status", "unknown"),
            "facts": facts,
            "feature_implemented": feature_implemented,
        },
        "benefit": {
            "hypothesis": supplied.get("benefit_claim"),
            "measured_outcome": measured,
            "benefit_proven": benefit_proven,
            "claim": benefit_claim,
        },
        "adoption": {
            "by_other_teams": adopted,
            "adopted_proven": bool(adopted),
        },
        "unknowns": list(supplied.get("unknowns", []) or []),
        "classification_note": "功能已实现 / 已证明收益 / 已被其他团队采用 分别判断；口述收益不自动成为实测",
    }
    validate("claim", benefit_claim) if benefit_claim else None
    return result


def _to_candidate(card):
    srcs = card.get("sources") or card.get("source_refs") or []
    obj = blank(
        "candidate",
        candidate_id=card.get("candidate_id") or new_id("cand"),
        problem=card["problem"],
        sources=list(srcs),
        value_hypothesis=card.get("value_hypothesis", ""),
        common_scenarios=card.get("common_scenarios", []),
        constraints=card.get("constraints", []),
        unknowns=card.get("unknowns", []),
        validation_suggestions=card.get("validation_suggestions", []),
        beneficiaries=card.get("beneficiaries", []),
        dedup_key=card.get("dedup_key", ""),
        relations=card.get("relations", []),
    )
    validate("candidate", obj)
    return obj


def discover_candidates(request):
    """候选发现由宿主推理后提交结构化卡；工具校验、允许零候选、绑定覆盖边界。"""
    cards = request.get("candidate_cards_submitted_by_host", []) or []
    coverage = request.get("coverage")
    valid, rejected = [], []
    for card in cards:
        if not card.get("problem") or not (card.get("sources") or card.get("source_refs")):
            rejected.append({"problem": card.get("problem", ""), "reason": "缺问题陈述或来源依据"})
            continue
        valid.append(_to_candidate(card))

    if not valid:
        return {
            "candidates": [],
            "insufficient": True,
            "rejected": rejected,
            "note": "已读资料不足以支持明确问题/改进机会，报告不足并建议补充信息，不强行凑出固定数量候选",
            "coverage": coverage,
            "source_scope": request.get("scope_note", ""),
        }
    return {
        "candidates": valid,
        "insufficient": False,
        "rejected": rejected,
        "note": "候选含依据、价值假设、共性场景、约束与未知项；推广效果为待验证",
        "coverage": coverage,
        "source_scope": request.get("scope_note", ""),
        "full_coverage": coverage.get("full_coverage") if isinstance(coverage, dict) else None,
    }


def reconcile_candidates(candidates):
    """去重（保留多来源）、聚焦与拆分合并；选择范围前不把仓库全部功能计入课题。"""
    by_key = {}
    order = []
    merges = []
    for c in candidates:
        key = c.get("dedup_key") or c["candidate_id"]
        if key in by_key:
            canon = by_key[key]
            union = list(dict.fromkeys((canon.get("sources") or []) + (c.get("sources") or [])))
            canon["sources"] = union
            canon.setdefault("relations", []).append(
                {"type": "merged_duplicate", "candidate_id": c["candidate_id"],
                 "note": "重复叙述合并，保留各来源，不重复计算收益"}
            )
            merges.append({"dedup_key": key, "kept": canon["candidate_id"],
                           "merged": c["candidate_id"], "sources_preserved": union})
        else:
            by_key[key] = c
            order.append(key)

    result = [by_key[k] for k in order]
    splits = []
    for c in result:
        problems = c.get("independent_problems") or []
        if len(problems) > 1:
            c["split_suggested"] = True
            splits.append({"candidate_id": c["candidate_id"],
                           "independent_problems": problems,
                           "note": "含目标/验证范围不同的多个问题，建议聚焦或拆题后分别建档"})

    return {
        "candidates": result,
        "merges": merges,
        "splits": splits,
        "duplicate_sources_preserved": True,
        "note": "成员确定范围后才形成对应课题；单仓库多个功能不会自动全部计入同一课题",
    }


def select_candidate(base, candidate, *, title=None, owner=""):
    """选定范围后建档：课题范围仅来自该候选，不自动纳入仓库全部功能或收益。"""
    problem = {
        "statement": candidate["problem"],
        "sources": list(candidate.get("sources", [])),
        "value_hypothesis": candidate.get("value_hypothesis", ""),
        "unknowns": list(candidate.get("unknowns", [])),
        "candidate_id": candidate["candidate_id"],
        "scope_note": "课题范围来自所选候选；未选择的功能与收益不计入本课题",
    }
    r = W.Workspace.init(base, title=title or candidate["problem"][:40], owner=owner, problem=problem)
    ws = r["workspace"]
    topic, rev, hsh = ws.snapshot()
    topic["next"] = "确认问题与受益对象，识别当前阶段与可沿用材料"
    ws.save(topic, rev, hsh)
    return {"workspace": ws, "topic": topic, "selected_scope_only": True}
