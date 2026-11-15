from __future__ import annotations

from .util import load_json_resource, new_id, utc_now

# 阶段到事实键的映射：结构(filled)与证据(verified)分别判断。
STAGE_FACT_KEYS = {
    "topic": ["problem_statement", "beneficiaries"],
    "baseline": ["baseline", "target", "unit"],
    "cause": ["cause_hypothesis", "factor_verification"],
    "countermeasure": ["countermeasure", "implementation"],
    "effect": ["improved_metric", "comparable"],
    "standardize": ["standardize_action", "reuse_note"],
}

_GAP_PLAYBOOK = {
    "problem_statement": ("当前要解决的具体问题是什么？", "问题陈述与现状描述", "明确选题范围"),
    "beneficiaries": ("谁会因此受益？", "受益对象分析", "支撑共性判断"),
    "baseline": ("改善前的基线值是多少？", "基线采集/记录任务", "提供可比口径"),
    "target": ("目标值定为多少？", "目标设定", "衡量效果"),
    "unit": ("用什么单位与周期计量？", "计量口径定义", "保证可比"),
    "cause_hypothesis": ("可能的原因有哪些？", "原因假设整理", "建立论证起点"),
    "factor_verification": ("要因是否已用现场/工程数据验证？", "要因验证（非相关性/评分）", "确认因果"),
    "countermeasure": ("对策对应哪个已验证要因？", "对策设计", "避免对策脱节"),
    "implementation": ("实施过程是否有记录？", "实施记录归档", "保留已有进展"),
    "improved_metric": ("改善后指标是多少？", "效果测量", "与基线对比"),
    "comparable": ("前后数据口径是否可比？", "可比性检查", "避免无效结论"),
    "standardize_action": ("如何固化做法？", "标准化动作", "防止反弹"),
    "reuse_note": ("其它团队如何采用？", "复用说明", "支撑推广"),
}


def load_profile():
    profile = load_json_resource("methods/method_profile_v1.json")
    validate_profile(profile)
    return profile


def validate_profile(profile):
    problems = []
    for key in ("id", "version", "basis", "dimensions", "stages"):
        if key not in profile:
            problems.append(f"missing {key}")
    if profile.get("official_scoring_configured") is not False:
        # 未配置官方细则时不得出现权重/得分
        if "weights" in profile or "official_score" in profile:
            problems.append("未配置官方细则却出现权重/官方得分")
    if any("weight" in d for d in profile.get("dimensions", [])):
        problems.append("维度含权重，但官方细则未配置")
    if problems:
        from .errors import ContractError

        raise ContractError("方法规则包校验失败: " + "; ".join(problems), details=problems)
    return profile


def profile_summary():
    p = load_profile()
    return {
        "id": p["id"], "version": p["version"], "basis": p["basis"],
        "official_scoring_configured": p["official_scoring_configured"],
        "weight_note": p["weight_note"],
        "universality_warning": p["universality_warning"],
        "dimensions": [d["name"] for d in p["dimensions"]],
        "has_official_weights": False,
        "note": "仅提供可解释的定性检查；固定十一阶段/特定模板不作为全部课题统一标准",
    }


def _normalize_fact(value):
    if isinstance(value, dict):
        return {"filled": bool(value.get("filled")), "verified": bool(value.get("verified"))}
    return {"filled": bool(value), "verified": bool(value)}


def assess_stage(topic, facts=None):
    """识别当前阶段；结构完整性与证据充分性分别呈现，允许回溯与不适用说明。"""
    profile = load_profile()
    raw = facts if facts is not None else topic.get("facts", {})
    factmap = {k: _normalize_fact(v) for k, v in raw.items()}

    stage_status = {}
    gaps = []
    reusable = []
    current_stage = None
    for st in profile["stages"]:
        sid = st["id"]
        keys = STAGE_FACT_KEYS.get(sid, [])
        filled = all(factmap.get(k, {}).get("filled") for k in keys)
        verified = all(factmap.get(k, {}).get("verified") for k in keys)
        stage_status[sid] = {"name": st["name"], "structure": filled, "evidence": verified}
        missing = [k for k in keys if not factmap.get(k, {}).get("verified")]
        if not verified and current_stage is None:
            current_stage = sid
            gaps.append({"stage": sid, "stage_name": st["name"], "missing": missing,
                         "reason": "相关环节缺数据或验证，不因页面齐全判为完成"})
        if filled:
            reusable.append({"stage": sid, "name": st["name"], "note": "已有材料可沿用"})

    return {
        "profile": {"id": profile["id"], "version": profile["version"]},
        "current_stage": current_stage or "complete",
        "stage_status": stage_status,
        "structure_complete": all(s["structure"] for s in stage_status.values()),
        "evidence_sufficient": all(s["evidence"] for s in stage_status.values()),
        "structure_and_evidence_separate": True,
        "reusable_materials": reusable,
        "gaps": gaps,
        "can_continue_with_existing_implementation": True,
        "allows_backtrack": True,
        "not_applicable_supported": True,
        "note": "已有实施但缺基线/要因验证时保留进展并列出缺口，不标记全部阶段完成",
    }


def recommend(topic, gaps):
    """用工作语言给出下一步：问题 / 方法 / 理由 / 输入 / 预期产物。"""
    out = []
    for gap in gaps:
        for key in gap["missing"]:
            q, method, reason = _GAP_PLAYBOOK.get(key, (f"补充 {key}？", "资料补充", "补齐缺口"))
            out.append(
                {
                    "fact_key": key,
                    "stage": gap["stage"],
                    "question": q,
                    "recommended_method": method,
                    "reason": reason,
                    "required_inputs": ["与该事实对应的可定位记录或数据"],
                    "expected_output": f"形成可核验的 {key} 记录并更新阶段状态",
                    "if_insufficient": "前提不足时指出不适用原因并建议补充数据或换用其它验证方式，不伪造已执行活动",
                }
            )
    return {"recommendations": out, "count": len(out)}


def check_reasoning(topic):
    """检查问题-原因-对策-实施-效果-标准化关联；相关性/评分不单独确认因果。"""
    cause_gaps, link_gaps, notes = [], [], []
    causes = topic.get("cause_hypotheses", []) or []
    countermeasures = topic.get("countermeasures", []) or []
    for c in causes:
        evidence_type = c.get("evidence_type", "")
        if c.get("verified") is not True:
            if evidence_type in ("correlation_coefficient", "vote", "subjective_score", "score"):
                cause_gaps.append(
                    {"cause_id": c.get("id"), "reason": "相关性/投票/评分不单独构成因果验证",
                     "suggestion": "补充现场或工程验证记录后再确认要因", "kept_as": "hypothesis"}
                )
                notes.append("假设状态保留，不直接确认为根因")
            else:
                cause_gaps.append(
                    {"cause_id": c.get("id"), "reason": "要因尚无验证记录",
                     "suggestion": "设计适用的验证任务", "kept_as": "hypothesis"}
                )
    verified_ids = {c.get("id") for c in causes if c.get("verified") is True}
    for m in countermeasures:
        if not m.get("linked_cause_id") or m.get("linked_cause_id") not in verified_ids:
            link_gaps.append(
                {"countermeasure_id": m.get("id"), "reason": "对策未关联已验证要因或无法关联到问题",
                 "suggestion": "补建与问题/要因证据的关联", "kept_as": "gap"}
            )
    return {
        "causal_gaps": cause_gaps,
        "link_gaps": link_gaps,
        "structure_complete": not link_gaps,
        "evidence_sufficient": not cause_gaps and not link_gaps,
        "conclusion": "存在论证断点；对策表格已填写不等于方法完整" if (cause_gaps or link_gaps)
        else "论证链关联完整（仍需对应证据）",
        "notes": notes,
    }


def make_tasks_from_gaps(gaps):
    tasks = []
    for gap in gaps:
        for key in gap["missing"]:
            tasks.append(
                {"task_id": new_id("task"), "fact_key": key, "stage": gap["stage"],
                 "description": _GAP_PLAYBOOK.get(key, ("", "", ""))[1],
                 "needed_evidence": f"可定位的 {key} 记录", "closed": False,
                 "created_at": utc_now()}
            )
    return tasks


def update_gaps(topic, new_evidence):
    """新证据有依据地关闭任务，保留关闭依据与其它未解决缺口。"""
    provided = {e["fact_key"]: e for e in new_evidence if e.get("supports")}
    closed, still_open = [], []
    for t in topic.get("tasks", []):
        if t.get("fact_key") in provided and not t.get("closed"):
            t["closed"] = True
            t["closure_basis"] = provided[t["fact_key"]].get("verification_id", "")
            t["closed_at"] = utc_now()
            closed.append(t["task_id"])
        elif not t.get("closed"):
            still_open.append(t["task_id"])
    return {
        "closed": closed, "still_open": still_open,
        "closure_requires_basis": True,
        "note": "关闭依据已保留；未解决缺口可继续形成明确标记的草稿，不伪造活动已执行",
    }
