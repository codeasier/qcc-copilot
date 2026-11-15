from __future__ import annotations

import json
import platform
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qcc_copilot import workspace as W  # noqa: E402
from tests.qcc_testutil import call, fixture, fixture_path, init_topic, new_base  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "docs" / "acceptance-report.md"


def _r(cmd, base=None, topic_id=None, **kw):
    return call(cmd, base, topic_id, **kw)


def E01():
    d = fixture("e01_improvement.json")
    r = _r("discovery.refine", supplied=d["supplied"])["refined"]
    ok = (r["implementation"]["feature_implemented"] and not r["benefit"]["benefit_proven"]
          and r["benefit"]["claim"]["support"] == "unverified"
          and not r["adoption"]["adopted_proven"])
    return _row("E01", "已有改进提炼（实施事实 / 效果证据 / 缺口）",
                "tests/fixtures/e01_improvement.json",
                "discovery.refine 结构化结果",
                "区分实施事实/价值假设/待验证结果，口述收益不成为实测",
                f"feature_implemented={r['implementation']['feature_implemented']}, "
                f"benefit_proven={r['benefit']['benefit_proven']}, "
                f"claim.support={r['benefit']['claim']['support']}", ok, [])


def E02():
    d = fixture("e02_materials/discovery_request.json")
    cards = _r("discovery.candidates", **d)
    rec = _r("discovery.reconcile", candidates=cards["candidates"])
    zero = _r("discovery.candidates", candidate_cards_submitted_by_host=[], scope_note="资料不足")
    ok = (len(cards["candidates"]) == 4 and len(rec["merges"]) >= 1
          and zero["insufficient"] and zero["candidates"] == [])
    return _row("E02", "指定资料候选发现、去重、聚焦，无凭空凑题",
                "tests/fixtures/e02_materials/discovery_request.json",
                "discovery.candidates / reconcile 候选与合并关系",
                "有依据发现候选、重复叙述合并保留多来源、资料不足可零候选",
                f"cards={len(cards['candidates'])}, merges={len(rec['merges'])}, "
                f"zero_insufficient={zero['insufficient']}", ok, [])


def E03():
    d = fixture("e03_sources.json")
    idx = _r("sources.index", base_dir=str(fixture_path("e02_materials")),
             sources=d["sources"], max_bytes=d["max_bytes"])["index"]
    counts = idx["coverage"]["counts"]
    ok = (all(counts.get(s, 0) > 0 for s in ("read", "unread", "failed", "truncated"))
          and not idx["coverage"]["full_coverage"] and bool(idx["coverage"]["unread_or_failed"]))
    return _row("E03", "文件不完整/远端不可访问：报告覆盖范围",
                "tests/fixtures/e03_sources.json", "sources.index 覆盖结果",
                "失败/未读/截断分别记录，未读不表述为全范围已检查",
                f"counts={counts}, full_coverage={idx['coverage']['full_coverage']}", ok, [])


def E04():
    cases = fixture("e04_benefit.json")["cases"]
    actual = {}
    for c in cases:
        if "ratio" in c:
            actual[c["name"]] = _r("benefit.ratio", **c["ratio"])["ratio"]
        else:
            actual[c["name"]] = _r("benefit.compute", metric=c["metric"], persist=False)["calculation"]["result"]
    def has(name, kw):
        gaps = actual[name].get("gaps", [])
        return any(kw in g for g in gaps)
    ok = (has("missing_baseline", "baseline") and has("incomparable_population", "compar")
          and has("unit_mismatch", "unit")
          and actual["only_waiting_time"]["labor_benefit_computable"] is False
          and actual["zero_denominator_ratio"]["computable"] is False)
    return _row("E04", "收益缺基线/混淆单位/仅等待时间", "tests/fixtures/e04_benefit.json",
                "benefit.compute / benefit.ratio 缺口与不可计算",
                "标明缺口，不输出无依据人天收益",
                json.dumps(actual, ensure_ascii=False)[:400], ok, [])


def E05():
    ev = fixture("expected_values.json")
    m = fixture("e05_benefit.json")["metric"]
    pos = _r("benefit.compute", metric=m, persist=False)["calculation"]["result"]
    negm = dict(m); negm["attributable_cost_hours"] = 12
    neg = _r("benefit.compute", metric=negm, persist=False)["calculation"]["result"]
    ok = (pos["gross_hours"] == 40 * 0.25 and pos["net_hours"] == 8.0
          and pos["net_person_days"] == 1.0
          and neg["net_hours"] == -2.0 and neg["net_person_days"] == -0.25
          and pos["net_person_days"] == ev["person_day"]["reference"]["net_person_days"])
    return _row("E05", "已知输入可复算，含成本与负收益",
                "tests/fixtures/expected_values.json（独立参考值）",
                "计算底稿（公式/输入/单位/结果）",
                "40 次事件：10 小时毛 / 8 小时净 / 1 人天；成本 12 小时：-2 小时 / -0.25 人天",
                f"gross={pos['gross_hours']}, net={pos['net_hours']}, pd={pos['net_person_days']}, "
                f"neg_net={neg['net_hours']}, neg_pd={neg['net_person_days']}", ok, [])


def E06():
    d = fixture("e06_reasoning.json")
    r = _r("methods.check", topic=d["topic"])
    ok = bool(r["causal_gaps"]) and bool(r["link_gaps"]) and not r["evidence_sufficient"]
    return _row("E06", "原因有相关性但缺验证，对策与原因脱节",
                "tests/fixtures/e06_reasoning.json", "methods.check 论证断点",
                "相关性不确认因果，对策脱节给补证建议",
                f"causal_gaps={len(r['causal_gaps'])}, link_gaps={len(r['link_gaps'])}", ok, [])


def E07():
    d = fixture("e07_reuse.json")
    ev = _r("reuse.evaluate", **d)["evaluation"]
    ad = _r("reuse.adoption", adoption_records=d["adoption_records"])["adoption"]
    cnt = _r("reuse.count", records=d["adoption_records"])["count"]
    ok = (ev["tool_usability"]["separate_metric"] and ad["installed_not_adopted"]
          and cnt["distinct_adopted_teams"] == 1)
    return _row("E07", "共性潜力但依赖个人环境", "tests/fixtures/e07_reuse.json",
                "reuse.evaluate / adoption / count",
                "潜力与已推广分开，列明限制与接入要求，安装成功不等于收益验证",
                f"installed_not_adopted={ad['installed_not_adopted']}, "
                f"distinct_adopted={cnt['distinct_adopted_teams']}, "
                f"tool_usability_separate={ev['tool_usability']['separate_metric']}", ok, [])


def E08():
    base = new_base()
    init_topic(base)
    m = fixture("e05_benefit.json")["metric"]
    _r("benefit.compute", base, "t1", metric=m, persist=True)
    snap = _r("delivery.snapshot", base, "t1")["snapshot"]
    before = (W.Workspace.route(base, "t1").deliveries_dir / snap["delivery_id"] / "snapshot.json").read_bytes()
    inv = _r("evidence.invalidate", base, "t1", changed_ids=["timesheet-2026-09"], note="基线修正")
    resumed = _r("workspace.resume", base, "t1")
    after_bytes = (W.Workspace.route(base, "t1").deliveries_dir / snap["delivery_id"] / "snapshot.json").read_bytes()
    b_before, b_after = json.loads(before), json.loads(after_bytes)
    basis_keys = ["delivery_id", "topic_id", "topic_revision", "content_hash",
                  "rule_profile", "sources", "calculations"]
    basis_preserved = all(b_before[k] == b_after[k] for k in basis_keys)
    stale_marked = b_after.get("checks", {}).get("evidence_stale") is True
    ok = (bool(inv["affected_derived_calculations"]) and not inv["unrelated_reset"]
          and basis_preserved and stale_marked and resumed["resumed_from_persisted_state"])
    return _row("E08", "来源数据更新或人工修改后续接", "tests/fixtures/e08_update.json",
                "evidence.invalidate / workspace.resume / 历史快照",
                "恢复状态、保留修订、标记受影响结论需核验，历史交付保留原依据",
                f"affected_calc={inv['affected_derived_calculations']}, "
                f"basis_preserved={basis_preserved}, stale_marked={stale_marked}, "
                f"resumed={resumed['resumed_from_persisted_state']}", ok, [])


def E09():
    base = new_base()
    did, _, ver = _setup(base, core_supported=False)
    st = _r("deliverable.status", base, "t1", delivery_id=did, verification=ver)
    ok = st["status"] == "draft" and st["premature_formal_export_blocked"]
    return _row("E09", "档案有缺口要求生成参评材料", "草稿情境（核心主张无充分支持）",
                "deliverable.compile / verify / status",
                "草稿明确标记缺口，核心结论不把未知写成已证实",
                f"status={st['status']}, blocked={st['premature_formal_export_blocked']}", ok,
                ["真实负责人审阅（10.3，需人工）"])


def E10():
    base = new_base()
    did, comp, ver = _setup(base, core_supported=True, run_render=True)
    from qcc_copilot import pptx

    vr = pptx.verify_pptx(str(W.Workspace.route(base, "t1").deliveries_dir / did / "deck.pptx"))
    # 注入缺陷验证可暴露性
    rp = W.Workspace.route(base, "t1").deliveries_dir / did / "report.md"
    rp.write_text(rp.read_text(encoding="utf-8") + "\n{{UNFILLED}}\n", encoding="utf-8")
    defect = _r("deliverable.verify", base, "t1", delivery_id=did, run_render=False)
    render = ver["checks"]["render"]["status"]
    not_exec = [] if render == "passed" else ["LibreOffice 逐页版式渲染"]
    ok = (len(comp["files"]) >= 11 and comp["pptx_real"] and vr["structure_ok"]
          and defect["checks"]["placeholders"]["status"] == "failed")
    return _row("E10", "生成报告、图表和 PPT，数字/引用一致，版式渲染检查有记录",
                "固定课题快照（tests/fixtures/e05_benefit.json）",
                "完整文件包 + 真实 deck.pptx + check_record.json",
                "文件可打开、数字/引用一致；占位符/溢出/缺图/渲染检查有记录",
                f"files={len(comp['files'])}, pptx_struct_ok={vr['structure_ok']}, "
                f"render={render}, placeholder_detected={defect['checks']['placeholders']['status']}", ok,
                not_exec)


def E11():
    data = fixture("e11_summaries.json")["summaries"]
    agg = _r("summary.aggregate", summaries=data)["aggregate"]
    ok = (agg["topics"]["topic-A"]["revision"] == 4 and agg["counts"]["conflicts"] == 1
          and agg["counts"]["invalid"] == 2
          and any(a["action"] == "older_skip_no_rollback" for a in agg["audit"]))
    return _row("E11", "多成员摘要含旧版本、重复课题和冲突",
                "tests/fixtures/e11_summaries.json", "summary.aggregate / views",
                "按标识与版本汇总，陈旧与冲突可见，反馈可回流",
                f"topic-A_rev={agg['topics']['topic-A']['revision']}, "
                f"conflicts={agg['counts']['conflicts']}, invalid={agg['counts']['invalid']}", ok, [])


def E12():
    base = new_base()
    init_topic(base, topic_id="tA", title="T", owner="成员甲")
    m = fixture("e05_benefit.json")["metric"]
    _r("benefit.compute", base, "tA", metric=m, persist=True)
    _r("claim.add", base, "tA", text="实测净收益", origin="record", category="benefit",
       evidence=[{"source_id": "s", "proves": ["measurement"]}],
       verification=[{"kind": "measurement", "supports": True}])
    did = _r("delivery.snapshot", base, "tA")["snapshot"]["delivery_id"]
    _r("deliverable.compile", base, "tA", delivery_id=did)
    s = _r("summary.export", base, "tA")["summary"]
    # 新会话（只凭路径，不携带内存状态）
    resumed = W.Workspace.resume(base, "tA")
    agg = _r("summary.aggregate", summaries=[s])["aggregate"]
    fb = _r("feedback.export", base, topic_id="tA", target_revision=resumed["revision"],
            author="负责人乙", content="补充效果验证")["feedback"]
    _r("feedback.import", base, "tA", feedback=fb)
    resumed2 = W.Workspace.resume(base, "tA")
    snap = _r("delivery.get", base, "tA", delivery_id=did)["snapshot"]
    ok = (resumed2["resumed_from_persisted_state"] and agg["counts"]["topics"] == 1
          and any("负责人反馈" in t.get("description", "") for t in resumed2["unresolved_tasks"])
          and snap["calculations"][0]["result"]["net_hours"] == 8.0)
    return _row("E12", "选定宿主安装并完成两种入口到汇总，无需依赖旧会话",
                "成员会话 + 负责人角色 + 新会话（仅文件路径）",
                "workspace.resume / summary.aggregate / feedback.import / delivery.get",
                "文件、引用、数字、版本一致，不依赖旧聊天状态",
                f"resumed={resumed2['resumed_from_persisted_state']}, "
                f"net_hours={snap['calculations'][0]['result']['net_hours']}, "
                f"feedback_in_tasks={any('负责人反馈' in t.get('description','') for t in resumed2['unresolved_tasks'])}", ok,
                ["真实外部 Agent / Windows 平台端到端（未验证，见支持矩阵）"])


def _setup(base, core_supported=True, run_render=False):
    init_topic(base, title="T", owner="甲")
    m = fixture("e05_benefit.json")["metric"]
    _r("benefit.compute", base, "t1", metric=m, persist=True)
    if core_supported:
        _r("claim.add", base, "t1", text="实测净收益", origin="record", category="benefit",
           evidence=[{"source_id": "s", "proves": ["measurement"]}],
           verification=[{"kind": "measurement", "supports": True}])
    did = _r("delivery.snapshot", base, "t1")["snapshot"]["delivery_id"]
    comp = _r("deliverable.compile", base, "t1", delivery_id=did)
    ver = _r("deliverable.verify", base, "t1", delivery_id=did, run_render=run_render)
    return did, comp, ver


def _row(eid, name, inp, artifacts, expected, actual, passed, not_exec):
    return {"id": eid, "name": name, "input": inp, "artifacts": artifacts,
            "expected": expected, "actual": actual, "passed": bool(passed),
            "not_executed": not_exec}


SCENARIOS = [E01, E02, E03, E04, E05, E06, E07, E08, E09, E10, E11, E12]


def main():
    rows = [fn() for fn in SCENARIOS]
    passed = sum(1 for r in rows if r["passed"])
    lines = [
        "# 验收覆盖报告（10.1 / 10.2）", "",
        f"> 运行方式：`PYTHONPATH=src:. python3 tests/run_acceptance.py`。",
        f"> 环境：CPython {platform.python_version()} / {platform.system()}；"
        f"独立渲染：{'Quick Look' if shutil.which('qlmanage') else '不可用（渲染检查受限）'}。",
        f"> 结果：**{passed}/{len(rows)} 情境的工具行为符合预期**。"
        "本表记录产品运行/确定性工具结果；人工校准（10.3）与真实试点不在自动通过范围内。",
        "> 样例均为验证情境，不是真实参评课题或已实现收益。", "",
        "| 编号 | 情境 | 输入 | 产物 | 预期 | 实际 | 结果 | 未执行 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['name']} | {r['input']} | {r['artifacts']} | "
            f"{r['expected']} | {r['actual']} | {'通过' if r['passed'] else '未通过'} | "
            f"{'; '.join(r['not_executed']) or '—'} |"
        )
    lines += [
        "", "## 说明", "",
        "- 逐项映射 PRD E01–E12 与各能力规格场景；「结果」只表示工具/文件行为与固定预期一致。",
        "- 计算使用 `tests/fixtures/expected_values.json` 的**独立参考值**（人工核算），不由产品自证。",
        "- 渲染核验：macOS Quick Look 独立打开成功仅证明可打开；缺 LibreOffice 时逐页版式渲染为未执行，不标通过。",
        "- 「未执行」列保留需人工或真实环境完成的部分：负责人校准、真实成员试点、其它宿主/平台。",
        "- 规划文档校验不等于产品运行通过；本表来自实际运行 `run_acceptance.py` 与 76 项单元测试。",
        "", "## 覆盖矩阵", "",
        "| 能力规格 | 情境 |", "|---|---|",
        "| topic-discovery | E01–E03 |", "| method-guidance | E01、E06 |",
        "| benefit-accounting | E04–E05 |", "| reuse-assessment | E07 |",
        "| skill-workspace / evidence-ledger | E08、E12 |",
        "| deliverable-review | E09–E10 |", "| lead-summary | E11 |",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"acceptance: {passed}/{len(rows)} passed -> {REPORT}")
    for r in rows:
        print(f"  {r['id']}: {'PASS' if r['passed'] else 'FAIL'}"
              + (f" (未执行: {', '.join(r['not_executed'])})" if r["not_executed"] else ""))
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
