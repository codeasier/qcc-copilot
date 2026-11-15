from __future__ import annotations

from decimal import Decimal

from .contracts import blank, validate
from .util import new_id, stable_key

_FORMULA = (
    "gross = Σ[可比事件数 × (基线人工小时 − 改善后人工小时)]; "
    "net = gross − 归属观察期成本人工小时; person_days = net / 每人天工时"
)
_FILLABLE_MODEL = {
    "baseline": "改善前同类事件单位人工小时（必填）",
    "improved": "改善后同类事件单位人工小时（必填）",
    "event_count": "可比事件数（必填）",
    "unit": "计量单位，基线/改善后须一致（必填）",
    "hours_per_person_day": "每人天工时换算参数，须显式记录（默认 8）",
    "attributable_cost_hours": "建设/运行/维护人工成本（可为 0 或使净收益为负）",
    "observation_period": "观察周期",
    "population": "事件/样本范围，前后须可比",
    "source_id": "数据来源标识",
}


def _D(x):
    return Decimal(str(x))


def validate_metric(metric):
    """检查可比口径：缺基线、不可比事件、单位不一致、零分母、等待时间等。"""
    problems = []
    for key in ("baseline", "improved"):
        if metric.get(key) is None:
            problems.append(f"missing_{key}: 缺少必要输入 {key}，不输出已验证人天收益")
    if metric.get("baseline") is None:
        problems.append("missing_baseline: 只有改善后耗时而没有可用基线，给出待补输入与测量建议")
    if metric.get("event_count") is None and metric.get("event_ids") is None:
        problems.append("missing_event_count: 缺少可比事件数（event_count 或完整 event_ids）")

    bp = metric.get("baseline_population")
    ip = metric.get("improved_population")
    if (bp and ip and bp != ip) or metric.get("comparable") is False:
        problems.append("incomparable_population: 基线与改善后事件类别/范围不可比，不能直接相减")

    bu = metric.get("baseline_unit", metric.get("unit"))
    iu = metric.get("improved_unit", metric.get("unit"))
    if bu and iu and bu != iu:
        problems.append("unit_mismatch: 基线与改善后计量单位不一致，需先换算或分层")

    if metric.get("hours_per_person_day") is not None and _D(metric["hours_per_person_day"]) == 0:
        problems.append("zero_divisor: 每人天工时为 0，无法换算人天")

    return problems


def _dedup_events(metric):
    # event_ids 若提供，即为完整的事件标识列表，以去重后的数量为准；
    # 否则使用显式声明的可比事件数 event_count（PRD 4.3 公式口径）。
    ids = metric.get("event_ids")
    if ids is None:
        return int(metric.get("event_count", 0)), {
            "dedup_applied": False,
            "note": "未提供 event_ids，事件数按显式 event_count 使用；多来源重复计入风险需另行去重依据",
        }
    unique = list(dict.fromkeys(ids))
    return len(unique), {
        "dedup_applied": True,
        "given": len(ids),
        "distinct": len(unique),
        "duplicates_removed": len(ids) - len(unique),
        "dedup_basis": "按事件标识去重；同一事件两个来源不重复计为两份收益",
    }


def compute_net_benefit(metric, calculation_id=None):
    """确定性净人工收益：保留公式/输入/单位/成本/假设，净收益可为负，等待时间不折人力。"""
    inputs = dict(metric)
    scenario = metric.get("scenario", "measured")
    problems = validate_metric(metric)

    # 机器运行/系统等待：不直接换算人力节省
    if metric.get("time_kind") in ("waiting", "machine_run", "queue") and not metric.get("human_work_changed", False):
        result = {
            "computable": False,
            "labor_benefit_computable": False,
            "present_as": "等待/交付周期改善",
            "gaps": ["waiting_only: 构建/排队等待缩短但无人工投入变化记录，不直接换算为人天"],
            "fillable_model": _FILLABLE_MODEL,
        }
        return _as_calculation(calculation_id, "net_labor_benefit", scenario, inputs, result,
                               assumptions=["等待时间未换算人力"], depends_on=_source_deps(metric))

    if problems:
        result = {"computable": False, "gaps": problems, "fillable_model": _FILLABLE_MODEL}
        return _as_calculation(calculation_id, "net_labor_benefit", scenario, inputs, result,
                               assumptions=["必要输入不足，未生成收益数字"], depends_on=_source_deps(metric))

    events, dedup = _dedup_events(metric)
    baseline = _D(metric["baseline"])
    improved = _D(metric["improved"])
    hpday = _D(metric.get("hours_per_person_day", 8))
    cost = _D(metric.get("attributable_cost_hours", 0) or 0)
    gross = _D(events) * (baseline - improved)
    net = gross - cost
    net_days = net / hpday

    result = {
        "computable": True,
        "gross_hours": float(gross),
        "attributable_cost_hours": float(cost),
        "net_hours": float(net),
        "net_person_days": float(net_days),
        "event_count_used": events,
        "cost_attribution": metric.get("cost_attribution", "unspecified"),
        "dedup": dedup,
        "negative_net_preserved": net < 0,
        "note": "净收益未截断为零；成本已按输入归集" if net < 0 else "确定性计算，可复算",
    }
    worksheet_lines = [
        f"events = {events}",
        f"gross = {events} × ({baseline} − {improved}) = {gross} 小时",
        f"net = {gross} − {cost} = {net} 小时",
        f"person_days = {net} / {hpday} = {net_days} 人天",
    ]
    calc = _as_calculation(
        calculation_id, "net_labor_benefit", scenario, inputs, result,
        assumptions=[
            f"每人天工时 = {hpday}",
            f"事件可比范围 = {metric.get('population', '未记录')}",
            f"观察周期 = {metric.get('observation_period', '未记录')}",
            f"成本归属 = {metric.get('cost_attribution', 'unspecified')}",
            f"场景 = {scenario}（实测/估算/预测分离）",
        ],
        depends_on=_source_deps(metric),
    )
    calc["worksheet"] = "\n".join(worksheet_lines)
    validate("calculation", calc)
    return calc


def _source_deps(metric):
    sid = metric.get("source_id")
    return [sid] if sid else []


def _as_calculation(calculation_id, kind, scenario, inputs, result, assumptions, depends_on):
    calc = blank(
        "calculation",
        calculation_id=calculation_id or new_id("calc"),
        kind=kind,
        inputs=inputs,
        result=result,
        formula=_FORMULA,
        unit="hours / person_days",
        scenario=scenario if scenario in ("measured", "member_provided", "estimate", "extrapolation") else "measured",
        assumptions=assumptions,
        worksheet="见 result 与 worksheet 字段；用户可按公式独立重算",
        needs_review=False,
        depends_on=depends_on,
    )
    validate("calculation", calc)
    return calc


def compute_ratio(numerator, denominator, unit="percent"):
    """比例指标：保存分子分母；零分母返回不可计算及原因。"""
    den = _D(denominator)
    if den == 0:
        return {"computable": False, "reason": "zero_denominator: 分母为零，不输出无穷值或误导百分比",
                "numerator": numerator, "denominator": denominator, "unit": unit}
    value = _D(numerator) / den
    return {"computable": True, "value": float(value), "percent": float(value * 100),
            "numerator": numerator, "denominator": denominator, "unit": unit}


def non_labor_metric(metric):
    """覆盖率/故障率/周期等价值：按原指标展示，不虚构人天换算。"""
    if metric.get("denominator") is not None:
        ratio = compute_ratio(metric.get("numerator", metric.get("improved", 0)),
                              metric["denominator"], metric.get("unit", "ratio"))
        return {"metric": metric.get("name", "质量/覆盖率指标"), "kind": "non_labor",
                "ratio": ratio, "person_day_conversion": None,
                "note": "以适当的质量/覆盖率/故障率/周期口径说明价值，不强制换算人天"}
    return {"metric": metric.get("name", "周期/质量指标"), "kind": "non_labor",
            "value": metric.get("value"), "unit": metric.get("unit"),
            "person_day_conversion": None,
            "note": "按原指标口径展示，无可靠人力换算依据时不虚构人天"}


def separate_scenarios(measured_calc, extrapolation_spec):
    """实测与外推分离：未来部门收益不并入已实现实测收益总额。"""
    measured_total = measured_calc["result"].get("net_hours") if measured_calc["result"].get("computable") else None
    extrapolation = {
        "scenario": "extrapolation",
        "assumed_teams": extrapolation_spec.get("assumed_teams"),
        "assumed_events_per_team": extrapolation_spec.get("assumed_events_per_team"),
        "note": "预测范围、频次假设与限制单列，不计入 measured_total",
        "merged_into_measured": False,
    }
    return {
        "measured_total_hours": measured_total,
        "extrapolation": extrapolation,
        "forward_looking_not_merged": True,
    }
