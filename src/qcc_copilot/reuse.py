from __future__ import annotations

from .util import stable_key


def evaluate_common_value(request):
    """选题共性判断：有来源，工具易用性与成果推广性分别计量。"""
    common_problem = request.get("common_problem", "")
    source_refs = request.get("common_problem_sources", []) or []
    return {
        "common_problem": common_problem,
        "common_problem_basis": {
            "sources": source_refs,
            "has_source": bool(source_refs),
            "note": "共性依据需可定位；无来源时仅记为假设" if not source_refs else "共性判断有来源依据",
        },
        "value_basis": request.get("value_basis", ""),
        "beneficiaries": request.get("beneficiaries", []),
        "unknowns": ["跨团队需求未验证", "采用记录未取得"] if not request.get("demand_verified") else [],
        "potential_only": True,
        "tool_usability": {
            "separate_metric": True,
            "note": "成员使用 QCC 工具的投入（如材料整理耗时）单独计量，不作为课题可跨部门推广的证据",
            "given": request.get("tool_usability_gain"),
        },
        "note": "成果推广性首先从选题共性痛点与受益价值判断；潜力不等于已完成推广",
    }


def generate_reuse_package(request):
    """复用说明：条件/资产/步骤/验证/维护/成本/限制；缺失项可见。"""
    fields = {
        "conditions": request.get("conditions", []),
        "assets": request.get("assets", []),
        "steps": request.get("steps", []),
        "validation": request.get("validation", []),
        "maintenance": request.get("maintenance", []),
        "cost": request.get("cost"),
        "limits": list(request.get("limits", []) or []),
    }
    if request.get("depends_on_personal_infra") or request.get("personal_infra_items"):
        items = request.get("personal_infra_items") or ["发起人个人设备/专用配置/特殊权限"]
        fields["limits"].extend([f"依赖个人资源: {i}" for i in items])
        fields["personal_infra_flagged"] = True
        fields["decoupling_needed"] = True
    else:
        fields["personal_infra_flagged"] = False

    missing = [k for k, v in fields.items() if k in
               ("conditions", "assets", "steps", "validation", "maintenance", "cost") and not v]
    return {
        "fields": fields,
        "missing": missing,
        "complete": not missing,
        "note": "缺失条件明确标明，不以'可推广'口号代替可操作内容；"
                "另一团队可据此核对自身条件、资产、步骤、验证与维护责任",
        "current_reusable_scope": "当前依赖解耦前范围" if fields.get("personal_infra_flagged") else "所述条件内",
        "potential_after_decoupling": "解耦个人依赖后的潜在范围" if fields.get("personal_infra_flagged") else None,
    }


def assess_adoption(request):
    """区分潜在适用、复现、实际采用；安装/演示/口述/预计收益不自动成为已采用并获益。"""
    records = request.get("adoption_records", []) or []
    classified = []
    for r in records:
        status = r.get("status")
        effect = r.get("effect_feedback")
        if status == "installed":
            classified.append({"team": r.get("team"), "adoption_state": "prepared",
                               "benefit_verified": False,
                               "note": "仅完成安装/准备，尚未执行实际工作，不标为已验证采用收益"})
        elif status == "reproduced":
            classified.append({"team": r.get("team"), "adoption_state": "reproduced",
                               "benefit_verified": bool(effect),
                               "note": "已完成复现验证"})
        elif status == "adopted":
            classified.append({"team": r.get("team"), "adoption_state": "adopted",
                               "benefit_verified": bool(effect),
                               "note": "有实际使用记录与效果反馈" if effect else "缺效果反馈，不宣称收益"})
        elif status == "potential":
            classified.append({"team": r.get("team"), "adoption_state": "potential",
                               "benefit_verified": False, "note": "潜在适用，待验证需求"})
        else:
            classified.append({"team": r.get("team"), "adoption_state": "unknown",
                               "benefit_verified": False, "note": "状态未识别"})
    return {
        "classified": classified,
        "potential_vs_adopted_separate": True,
        "installed_not_adopted": any(c["adoption_state"] == "prepared" for c in classified),
        "tool_usability_not_reusability_evidence": True,
        "note": "演示/安装成功/成员口述/预计收益不自动成为其他部门已采用并获益的事实",
    }


def count_adoption(records, unit="team"):
    """计数单位与去重键显式保存；同团队多来源/多版本不重复计数。"""
    seen = {}
    feedback = []
    for r in records:
        team = r.get("team")
        key = stable_key(team, r.get("dedup_key", "")) if r.get("dedup_key") else stable_key(team)
        seen.setdefault(key, {"team": team, "sources": [], "state": "prepared"})
        seen[key]["sources"].append(r.get("source_id") or r.get("status"))
        state = r.get("status")
        order = {"prepared": 0, "potential": 1, "reproduced": 2, "adopted": 3}
        if order.get(state, 0) >= order.get(seen[key]["state"], 0):
            seen[key]["state"] = state or "prepared"
        if r.get("failure_feedback"):
            feedback.append({"team": team, "feedback": r["failure_feedback"]})
    return {
        "unit": unit,
        "dedup_key": "stable(team, dedup_key)",
        "distinct": len(seen),
        "distinct_adopted_teams": sum(1 for v in seen.values() if v["state"] == "adopted"),
        "items": list(seen.values()),
        "duplicate_sources_not_double_counted": True,
        "failure_feedback": feedback,
        "note": "同一团队重复提交按约定单位去重，不重复增加推广部门数",
    }


def apply_failure_feedback(package, feedback):
    """复现失败反馈保留，缩小适用范围并新增验证任务，不继续无条件宣称可复制。"""
    limits = package.setdefault("fields", {}).setdefault("limits", [])
    tasks = []
    for fb in feedback:
        limits.append(f"复现失败限制: {fb.get('feedback', fb)}")
        tasks.append({"type": "validation", "description": "更新适用条件并补充验证",
                      "basis": fb.get("feedback", fb)})
    return {
        "package": package,
        "applicability_narrowed": True,
        "validation_tasks": tasks,
        "note": "反馈及依据已保留，不再对该场景无条件宣称可复制",
    }
