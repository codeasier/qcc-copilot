from __future__ import annotations

from . import benefits, capability, contracts, deliverables, deliveries, discovery
from . import evidence, methods, pptx, reuse, sources, summary
from . import workspace as W
from .errors import QccError


def _require(request, key):
    if key not in request:
        raise QccError(f"missing required field '{key}'")
    return request[key]


def _ws(request):
    base = _require(request, "workspace")
    return W.Workspace.route(base, request.get("topic_id"))


# ---- 工作区 / 契约 / 证据账本 ----
def cmd_workspace_init(r):
    out = W.Workspace.init(
        _require(r, "workspace"), topic_id=r.get("topic_id"),
        title=r.get("title", ""), owner=r.get("owner", ""),
        problem=r.get("problem"), rule_profile=r.get("rule_profile"),
    )
    return {"created": out["created"], "topic_id": out["topic"].get("topic_id"),
            "revision": out["topic"]["revision"], "path": str(out["workspace"].dir)}


def cmd_workspace_list(r):
    return {"topics": W.Workspace.list_topics(_require(r, "workspace"))}


def cmd_workspace_route(r):
    return {"topic_id": _ws(r).topic_id}


def cmd_workspace_resume(r):
    return W.Workspace.resume(_require(r, "workspace"), r.get("topic_id"))


def cmd_workspace_status(r):
    t = _ws(r).load()
    return {"topic_id": t["topic_id"], "revision": t["revision"], "stage": t["status"].get("stage"),
            "next": t["next"], "claims": len(t["claims"]), "calculations": len(t["calculations"]),
            "tasks_open": sum(1 for x in t["tasks"] if not x.get("closed")),
            "deliveries": len(t["deliveries"]), "content_hash": t["content_hash"]}


def cmd_contract_types(r):
    return {"types": contracts.KNOWN_TYPES}


def cmd_contract_validate(r):
    return {"valid": True, "type": contracts.validate(_require(r, "type"), _require(r, "object"))}


def cmd_claim_add(r):
    ws = _ws(r)
    spec = {k: v for k, v in r.items() if k in
            ("text", "origin", "category", "evidence", "verification", "depends_on",
             "requested_support", "claim_id", "conflicts")}
    return {"claim": evidence.add_claim(ws, spec)}


def cmd_claim_conflict(r):
    return {"claim": evidence.add_conflict(_ws(r), _require(r, "claim_id"), _require(r, "source"))}


def cmd_evidence_invalidate(r):
    ws = _ws(r)
    result = evidence.invalidate(ws, _require(r, "changed_ids"), r.get("note", ""))
    for did in result["affected_deliveries"]:
        deliveries.flag_stale(ws, did, result["affected_derived_calculations"] + result["affected_derived_claims"])
    return result


def cmd_dependency_link(r):
    return {"dependencies": evidence.link_dependency(_ws(r), _require(r, "derived_id"),
                                                     r.get("kind", "derived"), _require(r, "depends_on"))}


def cmd_delivery_snapshot(r):
    return {"snapshot": deliveries.create_snapshot(_ws(r))}


def cmd_delivery_list(r):
    return {"snapshots": deliveries.list_snapshots(_ws(r))}


def cmd_delivery_get(r):
    return {"snapshot": deliveries.get_snapshot(_ws(r), _require(r, "delivery_id"))}


# ---- 双入口课题发现 ----
def cmd_sources_index(r):
    doc = sources.index_sources(
        r.get("base_dir", "."), _require(r, "sources"), r.get("max_bytes", 65536)
    )
    saved = False
    if r.get("workspace"):
        try:
            W.Workspace.route(r["workspace"], r.get("topic_id")).save_sources(doc)
            saved = True
        except QccError:
            saved = False
    return {"index": doc, "saved_to_workspace": saved}


def cmd_sources_boundary(r):
    return sources.remote_input_boundary()


def cmd_discovery_refine(r):
    return {"refined": discovery.refine_improvement(_require(r, "supplied"))}


def cmd_discovery_candidates(r):
    return discovery.discover_candidates(r)


def cmd_discovery_reconcile(r):
    return discovery.reconcile_candidates(_require(r, "candidates"))


def cmd_discovery_select(r):
    out = discovery.select_candidate(_require(r, "workspace"), _require(r, "candidate"),
                                     title=r.get("title"), owner=r.get("owner", ""))
    return {"topic_id": out["topic"]["topic_id"], "revision": out["topic"]["revision"],
            "selected_scope_only": out["selected_scope_only"]}


# ---- 方法规则与过程引导 ----
def cmd_methods_profile(r):
    return methods.profile_summary()


def cmd_methods_stage(r):
    topic = _ws(r).load() if r.get("workspace") else r.get("topic", {})
    return methods.assess_stage(topic, r.get("facts"))


def cmd_methods_recommend(r):
    return methods.recommend(r.get("topic", {}), _require(r, "gaps"))


def cmd_methods_check(r):
    return methods.check_reasoning(_require(r, "topic"))


def cmd_methods_gaps(r):
    return {"tasks": methods.make_tasks_from_gaps(_require(r, "gaps"))}


def cmd_methods_update_gaps(r):
    return methods.update_gaps(_require(r, "topic"), _require(r, "new_evidence"))


# ---- 价值与收益核算 ----
def cmd_benefit_compute(r):
    calc = benefits.compute_net_benefit(_require(r, "metric"), r.get("calculation_id"))
    if r.get("workspace") and r.get("persist", True):
        ws = _ws(r)
        t, rev, h = ws.snapshot()
        t["calculations"] = [c for c in t["calculations"] if c["calculation_id"] != calc["calculation_id"]]
        t["calculations"].append(calc)
        ws.save(t, rev, h)
    return {"calculation": calc}


def cmd_benefit_ratio(r):
    return {"ratio": benefits.compute_ratio(_require(r, "numerator"), _require(r, "denominator"),
                                            r.get("unit", "percent"))}


def cmd_benefit_nonlabor(r):
    return {"metric": benefits.non_labor_metric(_require(r, "metric"))}


def cmd_benefit_separate(r):
    return benefits.separate_scenarios(_require(r, "measured"), _require(r, "extrapolation"))


# ---- 推广性与复用说明 ----
def cmd_reuse_evaluate(r):
    return {"evaluation": reuse.evaluate_common_value(r)}


def cmd_reuse_package(r):
    return {"package": reuse.generate_reuse_package(r)}


def cmd_reuse_adoption(r):
    return {"adoption": reuse.assess_adoption(r)}


def cmd_reuse_count(r):
    return {"count": reuse.count_adoption(_require(r, "records"), r.get("unit", "team"))}


def cmd_reuse_feedback(r):
    return reuse.apply_failure_feedback(_require(r, "package"), _require(r, "feedback"))


# ---- 成果编译与评审自检 ----
def cmd_deliverable_compile(r):
    return deliverables.compile_bundle(_ws(r), r.get("delivery_id"), r)


def cmd_deliverable_review(r):
    snap = deliveries.get_snapshot(_ws(r), _require(r, "delivery_id"))
    if not snap:
        raise QccError("delivery not found")
    return {"review": deliverables.review(snap)}


def cmd_deliverable_verify(r):
    return deliverables.verify_outputs(_ws(r), _require(r, "delivery_id"), r.get("run_render", True))


def cmd_deliverable_status(r):
    return deliverables.decide_status(_ws(r), _require(r, "delivery_id"), r.get("verification"))


def cmd_deliverable_pptx_verify(r):
    return {"structure": pptx.verify_pptx(_require(r, "path"))}


# ---- 负责人轻量汇总与反馈 ----
def cmd_summary_export(r):
    return {"summary": summary.export_summary(_ws(r))}


def cmd_summary_import(r):
    return summary.import_summary(_require(r, "summary"))


def cmd_summary_aggregate(r):
    return {"aggregate": summary.aggregate(_require(r, "summaries"))}


def cmd_summary_views(r):
    return {"views": summary.aggregate_views(_require(r, "aggregate"))}


def cmd_feedback_export(r):
    ws = _ws(r) if r.get("workspace") else None
    return {"feedback": summary.export_feedback(
        _require(r, "topic_id"), _require(r, "target_revision"),
        _require(r, "author"), _require(r, "content"), ws)}


def cmd_feedback_import(r):
    return summary.import_feedback(_ws(r), _require(r, "feedback"))


def cmd_capabilities(r):
    return capability.check()


HANDLERS = {
    "workspace.init": cmd_workspace_init,
    "workspace.list": cmd_workspace_list,
    "workspace.route": cmd_workspace_route,
    "workspace.resume": cmd_workspace_resume,
    "workspace.status": cmd_workspace_status,
    "contract.types": cmd_contract_types,
    "contract.validate": cmd_contract_validate,
    "claim.add": cmd_claim_add,
    "claim.conflict": cmd_claim_conflict,
    "evidence.invalidate": cmd_evidence_invalidate,
    "dependency.link": cmd_dependency_link,
    "delivery.snapshot": cmd_delivery_snapshot,
    "delivery.list": cmd_delivery_list,
    "delivery.get": cmd_delivery_get,
    "sources.index": cmd_sources_index,
    "sources.boundary": cmd_sources_boundary,
    "discovery.refine": cmd_discovery_refine,
    "discovery.candidates": cmd_discovery_candidates,
    "discovery.reconcile": cmd_discovery_reconcile,
    "discovery.select": cmd_discovery_select,
    "methods.profile": cmd_methods_profile,
    "methods.stage": cmd_methods_stage,
    "methods.recommend": cmd_methods_recommend,
    "methods.check": cmd_methods_check,
    "methods.gaps": cmd_methods_gaps,
    "methods.update_gaps": cmd_methods_update_gaps,
    "benefit.compute": cmd_benefit_compute,
    "benefit.ratio": cmd_benefit_ratio,
    "benefit.nonlabor": cmd_benefit_nonlabor,
    "benefit.separate": cmd_benefit_separate,
    "reuse.evaluate": cmd_reuse_evaluate,
    "reuse.package": cmd_reuse_package,
    "reuse.adoption": cmd_reuse_adoption,
    "reuse.count": cmd_reuse_count,
    "reuse.feedback": cmd_reuse_feedback,
    "deliverable.compile": cmd_deliverable_compile,
    "deliverable.review": cmd_deliverable_review,
    "deliverable.verify": cmd_deliverable_verify,
    "deliverable.status": cmd_deliverable_status,
    "deliverable.pptx_verify": cmd_deliverable_pptx_verify,
    "summary.export": cmd_summary_export,
    "summary.import": cmd_summary_import,
    "summary.aggregate": cmd_summary_aggregate,
    "summary.views": cmd_summary_views,
    "feedback.export": cmd_feedback_export,
    "feedback.import": cmd_feedback_import,
    "capabilities": cmd_capabilities,
}
