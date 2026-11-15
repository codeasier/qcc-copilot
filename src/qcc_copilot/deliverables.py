from __future__ import annotations

import hashlib
import json
import os
import re

from . import capability, pptx
from .deliveries import get_snapshot, set_material_status, create_snapshot, flag_stale
from .util import canonical_json, load_text_resource, write_json, write_text

CORE_CATEGORIES = {"benefit", "effect", "reuse", "adoption"}


def render_template(name, mapping):
    tpl = load_text_resource(f"templates/{name}")

    def repl(m):
        return str(mapping.get(m.group(1), ""))

    return re.sub(r"\{\{(\w+)\}\}", repl, tpl)


def _checksum(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _claims_text(snapshot):
    claims = snapshot.get("claims", [])
    if not claims:
        return "（无主张记录，作为缺口列出）"
    lines = []
    for c in claims:
        nr = " [需重新核验]" if c.get("needs_review") else ""
        lines.append(
            f"- {c['claim_id']}｜{c.get('origin')}｜{c.get('support')}｜{c.get('category') or '未分类'}"
            f"{nr}：{c.get('text', '')}"
        )
    return "\n".join(lines)


def _benefit_section(snapshot):
    calcs = snapshot.get("calculations", [])
    lines, points = [], []
    if not calcs:
        lines.append("（无收益计算记录：核心收益缺底稿，标记为缺口）")
    for c in calcs:
        r = c.get("result", {})
        if r.get("computable"):
            lines.append(
                f"- {c['calculation_id']}（{c.get('scenario')}）：毛 {r['gross_hours']} 小时，"
                f"成本 {r['attributable_cost_hours']} 小时，净 {r['net_hours']} 小时 = "
                f"{r['net_person_days']} 人天"
            )
            points.append({"label": c["calculation_id"], "value": r["net_hours"]})
        else:
            lines.append(f"- {c['calculation_id']}：不可计算/缺口 {r.get('gaps') or r.get('present_as')}")
    return "\n".join(lines), points


def _chart_svg(points):
    if not points:
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="200">'
                '<text x="20" y="40" font-size="16" fill="#888">无可用收益数据（缺数据/缺图标记）</text></svg>')
    w, h = 480, 220
    maxv = max(abs(p["value"]) for p in points) or 1
    bars = []
    x = 30
    bw = max(20, (w - 60) // max(1, len(points)) - 20)
    for p in points:
        bh = int(abs(p["value"]) / maxv * 140)
        y = 180 - bh
        color = "#2E75B6" if p["value"] >= 0 else "#C00000"
        bars.append(
            f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" fill="{color}"/>'
            f'<text x="{x}" y="{196}" font-size="11">{p["label"][:8]}</text>'
            f'<text x="{x}" y="{y - 4}" font-size="11">{p["value"]}</text>'
        )
        x += bw + 20
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">' + "".join(bars) + "</svg>"


def _slides(snapshot, benefit_lines, points):
    s = snapshot
    calc0 = s.get("calculations", [{}])[0] if s.get("calculations") else {}
    r0 = calc0.get("result", {})
    return [
        {"title": "课题与问题", "bullets": [s.get("topic_id", ""),
                                          "问题与受益对象见课题报告",
                                          f"快照修订 {s['topic_revision']}"]},
        {"title": "收益核算（快照同源）",
         "bullets": [l.replace("- ", "") for l in benefit_lines.splitlines()] or ["无收益计算"]},
        {"title": "收益底稿表",
         "table": {"columns": ["项", "值", "单位"],
                   "rows": [["毛收益", r0.get("gross_hours", "—"), "小时"],
                            ["归属成本", r0.get("attributable_cost_hours", "—"), "小时"],
                            ["净收益", r0.get("net_hours", "—"), "小时"],
                            ["净人天", r0.get("net_person_days", "—"), "人天"]]}},
        {"title": "推广与复用", "bullets": ["共性问题与价值依据", "适用条件与接入成本",
                                          "潜在适用 / 复现 / 实际采用分别说明"]},
        {"title": "评审自检", "bullets": ["价值 / 推广 / QCC 方法 / PPT 论证 定性检查",
                                        "未配置官方评分细则，不生成分数",
                                        "缺证据与冲突作为待补证列出"]},
    ]


def compile_bundle(ws, delivery_id=None, request=None):
    """从同一固定快照生成全部材料；生成期间只使用入口时捕获的快照，不混用新旧输入。"""
    request = request or {}
    if not delivery_id:
        delivery_id = create_snapshot(ws)["delivery_id"]
    snap = get_snapshot(ws, delivery_id)  # 固定一次
    if not snap:
        raise ValueError(f"delivery {delivery_id} 不存在")
    ddir = ws.deliveries_dir / delivery_id

    benefit_lines, points = _benefit_section(snap)
    theme = json.loads(load_text_resource("templates/neutral_theme.json"))
    profile = snap["rule_profile"]

    mapping = {
        "title": f"课题 {snap['topic_id']}",
        "material_status": snap.get("material_status", "draft"),
        "delivery_id": snap["delivery_id"],
        "topic_revision": snap["topic_revision"],
        "rule_id": profile.get("id"),
        "rule_version": profile.get("version"),
        "problem": "见课题档案 problem 字段（本快照同源）",
        "stage": "见课题快照对应阶段",
        "structure_status": "结构完整性按方法规则单独判断",
        "evidence_status": "证据充分性按主张支持状态单独判断",
        "next": "见下一步与补证任务",
        "claims": _claims_text(snap),
        "benefit": benefit_lines,
        "reuse": "见复用说明文件 reuse.md",
        "review": "见 review_questions.md / review.json",
        "sources": ", ".join(f"{x['source_id']}({x['status']})" for x in snap["sources"]) or "（无来源记录）",
        "calculations": ", ".join(c["calculation_id"] for c in snap["calculations"]) or "（无计算）",
        "checks": "见 check_record.json（由 verify_outputs 写入）",
        "common_problem": "见课题档案 reuse 字段",
        "value_basis": "收益以底稿为准；潜力与已采用分离",
        "beneficiaries": "见复用说明",
        "potential": "潜在适用待验证",
        "constraints": "见复用说明约束",
        "assets": "见复用包",
        "steps": "见复用包",
        "validation": "见复用包",
        "maintenance_cost": "见复用包",
        "limits": "缺失项在复用包中可见",
        "count_unit": "团队",
        "dedup_key": "stable(team, dedup_key)",
        "adoption": "潜在 / 复现 / 实际采用分别记录",
    }

    files = {}

    def put(name, text):
        write_text(ddir / name, text)
        files[name] = {"bytes": len(text.encode("utf-8")), "sha256_16": _checksum(text)}

    put("report.md", render_template("report.md.tpl", mapping))
    put("benefit.md", "# 收益说明（快照同源）\n\n" + benefit_lines + "\n")
    put("reuse.md", render_template("reuse.md.tpl", mapping))
    put("data_worksheet.md", "# 数据底稿\n\n" + benefit_lines + "\n\n> 数字/单位/周期/结论与快照 " + snap["delivery_id"] + " 一致。\n")
    put("chart_data.json", json.dumps({"delivery_id": snap["delivery_id"],
                                      "data_points": points, "unit": "hours"}, ensure_ascii=False, indent=2))
    put("chart.svg", _chart_svg(points))

    review_obj = review(snap)
    put("review.json", json.dumps(review_obj, ensure_ascii=False, indent=2))
    put("review_questions.md", _review_md(review_obj))

    slides = _slides(snap, benefit_lines, points)
    put("slides.json", json.dumps({"editable": True, "slides": slides}, ensure_ascii=False, indent=2))

    deck = pptx.Presentation(f"课题 {snap['topic_id']} QCC 成果")
    for s in slides:
        deck.add_slide(s["title"], s.get("bullets"), s.get("table"))
    deck_path = ddir / "deck.pptx"
    deck.save(str(deck_path))
    files["deck.pptx"] = {"bytes": deck_path.stat().st_size,
                          "sha256_16": hashlib.sha256(deck_path.read_bytes()).hexdigest()[:16],
                          "real_pptx": True}

    manifest = {
        "delivery_id": snap["delivery_id"],
        "snapshot": {"topic_revision": snap["topic_revision"], "content_hash": snap["content_hash"],
                     "rule_profile": snap["rule_profile"]},
        "theme": theme["id"],
        "files": files,
        "note": "全部材料来自同一固定快照；生成期间输入变化不会混入本包",
    }
    put("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return {"delivery_id": snap["delivery_id"], "files": sorted(files), "pptx_real": True,
            "snapshot_used": snap["delivery_id"]}


def review(snapshot):
    """独立起草后的三维语义检查；未配置官方细则不生成虚构分数/权重/获奖概率。"""
    claims = snapshot.get("claims", [])
    calcs = snapshot.get("calculations", [])
    findings = []

    def finding(dim, problem, impact, advice, basis, to_verify):
        findings.append({"dimension": dim, "依据": basis, "问题": problem,
                         "影响": impact, "建议": advice, "待补证": to_verify})

    unverified = [c for c in claims if c.get("support") in ("unverified", "insufficient")]
    conflicting = [c for c in claims if c.get("support") == "conflicting"]
    stale = [c for c in claims if c.get("needs_review")]
    noncomputable = [c for c in calcs if not c.get("result", {}).get("computable")]

    for c in conflicting:
        finding("value", f"核心主张 {c['claim_id']} 存在未解决冲突", "结论不可靠，不能进入正式结论",
                "核验冲突来源并保留依据，不择一", "快照主张 support=conflicting", ["冲突核验记录"])
    for c in unverified:
        finding("value", f"主张 {c['claim_id']} 缺充分证据", "只能作为草稿，不能标为已证实",
                "补充可定位证据与核验记录", f"origin={c.get('origin')}, support={c.get('support')}",
                ["证据片段", "核验记录"])
    for c in stale:
        finding("method", f"主张 {c['claim_id']} 因输入变化需重新核验", "材料失去当前有效状态",
                "重新计算并检查后更新", "needs_review=true", ["重算底稿"])
    for c in noncomputable:
        finding("value", f"计算 {c['calculation_id']} 不可计算/缺输入", "无依据收益数字不可用",
                "补齐可比口径与输入", "result.computable=false", ["基线/单位/事件数"])
    finding("reuse", "推广潜力与实际采用需分别核对", "潜力不可写成已推广成果",
            "核对采用记录与效果反馈", "三维规则 reuse 检查项", ["采用证据", "效果反馈"])
    finding("method", "问题-原因-对策-效果关联需逐项可追溯", "页面齐全不等于论证通过",
            "检查关联与要因验证记录", "三维规则 method 检查项", ["关联记录", "要因验证"])
    finding("presentation", "报告/PPT 数字与引用与快照一致", "不一致会误导评审",
            "以固定快照编译并做一致性检查", "同源编译", ["一致性检查记录"])

    return {
        "check_kind": "qualitative_three_dimension_plus_presentation",
        "official_scoring_configured": False,
        "official_scores_generated": False,
        "award_probability_generated": False,
        "dimensions": ["value", "reuse", "method", "presentation"],
        "finding_count": len(findings),
        "findings": findings,
        "note": "没有具体评分细则时输出定性检查及其依据；自检不等同官方评审通过",
    }


def _review_md(review_obj):
    lines = ["# 评审自检问题清单（独立步骤）", "",
             f"> 官方评分细则已配置：{review_obj['official_scoring_configured']}；"
             f"生成官方分数/权重/获奖概率：{review_obj['official_scores_generated']}", ""]
    for f in review_obj["findings"]:
        lines += [f"## [{f['dimension']}] {f['问题']}",
                  f"- 依据：{f['依据']}", f"- 影响：{f['影响']}", f"- 建议：{f['建议']}",
                  f"- 待补证：{', '.join(f['待补证'])}", ""]
    return "\n".join(lines)


_PLACEHOLDER_RE = re.compile(r"\{\{[A-Za-z0-9_]+\}\}|\bTODO\b|\bTBD\b|占位符|待填写")


def verify_outputs(ws, delivery_id, run_render=True):
    """检查覆盖/占位符/可检测溢出/独立渲染；失败与未执行都不标为通过。"""
    ddir = ws.deliveries_dir / delivery_id
    snap = get_snapshot(ws, delivery_id)
    theme = json.loads(load_text_resource("templates/neutral_theme.json"))
    required = ["report.md", "benefit.md", "reuse.md", "chart_data.json", "chart.svg",
                "data_worksheet.md", "review_questions.md", "review.json",
                "slides.json", "deck.pptx", "manifest.json"]
    checks = {}

    missing = [f for f in required if not (ddir / f).exists()]
    checks["coverage"] = {"status": "passed" if not missing else "failed",
                          "required": required, "missing": missing}

    ph = []
    for f in required:
        p = ddir / f
        if p.exists() and f.endswith((".md", ".json", ".svg")):
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if _PLACEHOLDER_RE.search(line):
                    ph.append(f"{f}:{i}")
    checks["placeholders"] = {"status": "failed" if ph else "passed", "found": ph}

    # 可检测溢出 + 缺图/缺数据
    overflow, chart_missing = [], False
    slides_path = ddir / "slides.json"
    if slides_path.exists():
        data = json.loads(slides_path.read_text(encoding="utf-8"))
        for idx, s in enumerate(data.get("slides", []), 1):
            if len(s.get("title", "")) > theme["max_title_chars"]:
                overflow.append(f"slide {idx} 标题超长")
            body = "".join(s.get("bullets", []))
            if len(body) > theme["max_body_chars_per_slide"]:
                overflow.append(f"slide {idx} 正文超出可容纳字数")
            if s.get("table") and len(s["table"].get("rows", [])) > 12:
                overflow.append(f"slide {idx} 表格行数过多可能溢出")
    chart_path = ddir / "chart_data.json"
    if chart_path.exists():
        cd = json.loads(chart_path.read_text(encoding="utf-8"))
        if not cd.get("data_points"):
            chart_missing = True
            overflow.append("chart_data.json 无数据点（缺图/缺数据）")
    pptx_struct = pptx.verify_pptx(str(ddir / "deck.pptx")) if (ddir / "deck.pptx").exists() else {"structure_ok": False, "errors": ["deck.pptx 缺失"]}
    if not pptx_struct.get("structure_ok"):
        overflow.append("deck.pptx 结构检查未通过")
    checks["overflow_and_chart"] = {
        "status": "failed" if (overflow or chart_missing) else "passed",
        "issues": overflow, "chart_data_missing": chart_missing,
        "pptx_structure": {"ok": pptx_struct.get("structure_ok"), "slides": pptx_struct.get("slides")},
    }

    if run_render:
        checks["render"] = capability.independent_render(str(ddir / "deck.pptx"))
    else:
        checks["render"] = {"status": "not_run", "reason": "调用方要求跳过独立渲染"}

    statuses = [c["status"] for c in checks.values()]
    if "failed" in statuses:
        overall = "failed"
    elif "not_run" in statuses:
        overall = "partial_not_run"
    else:
        overall = "passed"
    record = {"delivery_id": delivery_id, "checks": checks, "overall": overall,
              "note": "失败/未执行/受限都不标为通过；仅检查文件存在或文案长度不等于渲染验证通过"}
    write_json(ddir / "check_record.json", record)
    if snap:
        set_material_status(ws, delivery_id, "draft", {"last_verification": overall})
    return record


def decide_status(ws, delivery_id, verification=None):
    """缺证据/严重冲突/检查未通过只得到草稿；否则可标为 review-ready。"""
    snap = get_snapshot(ws, delivery_id)
    ver = verification or (json.loads((ws.deliveries_dir / delivery_id / "check_record.json").read_text(encoding="utf-8"))
                           if (ws.deliveries_dir / delivery_id / "check_record.json").exists() else {})
    core = [c for c in snap["claims"] if c.get("category") in CORE_CATEGORIES]
    core_unready = [c for c in core if c.get("support") != "supported" or c.get("needs_review")]
    conflicts = [c for c in snap["claims"] if c.get("support") == "conflicting"]
    stale = snap.get("checks", {}).get("evidence_stale")
    checks_passed = ver.get("overall") == "passed"
    ready = not core_unready and not conflicts and not stale and checks_passed
    status = "review-ready" if ready else "draft"
    reasons = []
    if core_unready:
        reasons.append(f"核心主张未获充分支持: {[c['claim_id'] for c in core_unready]}")
    if conflicts:
        reasons.append("存在未解决严重冲突")
    if stale:
        reasons.append("引用证据/规则已变化，需重新核验")
    if not checks_passed:
        reasons.append(f"材料检查未全部通过: {ver.get('overall')}")
    result = {"status": status, "ready": ready, "reasons": reasons,
              "premature_formal_export_blocked": not ready}
    set_material_status(ws, delivery_id, status, {"status_reasons": reasons})
    return result
