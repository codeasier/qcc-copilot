# 验收覆盖报告（10.1 / 10.2）

> 运行方式：`PYTHONPATH=src:. python3 tests/run_acceptance.py`。
> 环境：CPython 3.14.6 / Darwin；独立渲染：Quick Look。
> 结果：**12/12 情境的工具行为符合预期**。本表记录产品运行/确定性工具结果；人工校准（10.3）与真实试点不在自动通过范围内。
> 样例均为验证情境，不是真实参评课题或已实现收益。

| 编号 | 情境 | 输入 | 产物 | 预期 | 实际 | 结果 | 未执行 |
|---|---|---|---|---|---|---|---|
| E01 | 已有改进提炼（实施事实 / 效果证据 / 缺口） | tests/fixtures/e01_improvement.json | discovery.refine 结构化结果 | 区分实施事实/价值假设/待验证结果，口述收益不成为实测 | feature_implemented=True, benefit_proven=False, claim.support=unverified | 通过 | — |
| E02 | 指定资料候选发现、去重、聚焦，无凭空凑题 | tests/fixtures/e02_materials/discovery_request.json | discovery.candidates / reconcile 候选与合并关系 | 有依据发现候选、重复叙述合并保留多来源、资料不足可零候选 | cards=4, merges=1, zero_insufficient=True | 通过 | — |
| E03 | 文件不完整/远端不可访问：报告覆盖范围 | tests/fixtures/e03_sources.json | sources.index 覆盖结果 | 失败/未读/截断分别记录，未读不表述为全范围已检查 | counts={'read': 3, 'unread': 1, 'failed': 2, 'truncated': 1}, full_coverage=False | 通过 | — |
| E04 | 收益缺基线/混淆单位/仅等待时间 | tests/fixtures/e04_benefit.json | benefit.compute / benefit.ratio 缺口与不可计算 | 标明缺口，不输出无依据人天收益 | {"missing_baseline": {"computable": false, "gaps": ["missing_baseline: 缺少必要输入 baseline，不输出已验证人天收益", "missing_baseline: 只有改善后耗时而没有可用基线，给出待补输入与测量建议"], "fillable_model": {"baseline": "改善前同类事件单位人工小时（必填）", "improved": "改善后同类事件单位人工小时（必填）", "event_count": "可比事件数（必填）", "unit": "计量单位，基线/改善后须一致（必填）", "hours_per_person_day": "每人天工时换算参数，须显式记录（默认 8）", "attributable_cost_hours": "建设/运行/维护人工成本（可为 0 或使净收益为负）", "o | 通过 | — |
| E05 | 已知输入可复算，含成本与负收益 | tests/fixtures/expected_values.json（独立参考值） | 计算底稿（公式/输入/单位/结果） | 40 次事件：10 小时毛 / 8 小时净 / 1 人天；成本 12 小时：-2 小时 / -0.25 人天 | gross=10.0, net=8.0, pd=1.0, neg_net=-2.0, neg_pd=-0.25 | 通过 | — |
| E06 | 原因有相关性但缺验证，对策与原因脱节 | tests/fixtures/e06_reasoning.json | methods.check 论证断点 | 相关性不确认因果，对策脱节给补证建议 | causal_gaps=1, link_gaps=1 | 通过 | — |
| E07 | 共性潜力但依赖个人环境 | tests/fixtures/e07_reuse.json | reuse.evaluate / adoption / count | 潜力与已推广分开，列明限制与接入要求，安装成功不等于收益验证 | installed_not_adopted=True, distinct_adopted=1, tool_usability_separate=True | 通过 | — |
| E08 | 来源数据更新或人工修改后续接 | tests/fixtures/e08_update.json | evidence.invalidate / workspace.resume / 历史快照 | 恢复状态、保留修订、标记受影响结论需核验，历史交付保留原依据 | affected_calc=['calc-5efae3b49281'], basis_preserved=True, stale_marked=True, resumed=True | 通过 | — |
| E09 | 档案有缺口要求生成参评材料 | 草稿情境（核心主张无充分支持） | deliverable.compile / verify / status | 草稿明确标记缺口，核心结论不把未知写成已证实 | status=draft, blocked=True | 通过 | 真实负责人审阅（10.3，需人工） |
| E10 | 生成报告、图表和 PPT，数字/引用一致，版式渲染检查有记录 | 固定课题快照（tests/fixtures/e05_benefit.json） | 完整文件包 + 真实 deck.pptx + check_record.json | 文件可打开、数字/引用一致；占位符/溢出/缺图/渲染检查有记录 | files=11, pptx_struct_ok=True, render=passed, placeholder_detected=failed | 通过 | — |
| E11 | 多成员摘要含旧版本、重复课题和冲突 | tests/fixtures/e11_summaries.json | summary.aggregate / views | 按标识与版本汇总，陈旧与冲突可见，反馈可回流 | topic-A_rev=4, conflicts=1, invalid=2 | 通过 | — |
| E12 | 选定宿主安装并完成两种入口到汇总，无需依赖旧会话 | 成员会话 + 负责人角色 + 新会话（仅文件路径） | workspace.resume / summary.aggregate / feedback.import / delivery.get | 文件、引用、数字、版本一致，不依赖旧聊天状态 | resumed=True, net_hours=8.0, feedback_in_tasks=True | 通过 | 真实外部 Agent / Windows 平台端到端（未验证，见支持矩阵） |

## 说明

- 逐项映射 PRD E01–E12 与各能力规格场景；「结果」只表示工具/文件行为与固定预期一致。
- 计算使用 `tests/fixtures/expected_values.json` 的**独立参考值**（人工核算），不由产品自证。
- 渲染核验：macOS Quick Look 独立打开成功仅证明可打开；缺 LibreOffice 时逐页版式渲染为未执行，不标通过。
- 「未执行」列保留需人工或真实环境完成的部分：负责人校准、真实成员试点、其它宿主/平台。
- 规划文档校验不等于产品运行通过；本表来自实际运行 `run_acceptance.py` 与 71 项单元测试。

## 覆盖矩阵

| 能力规格 | 情境 |
|---|---|
| topic-discovery | E01–E03 |
| method-guidance | E01、E06 |
| benefit-accounting | E04–E05 |
| reuse-assessment | E07 |
| skill-workspace / evidence-ledger | E08、E12 |
| deliverable-review | E09–E10 |
| lead-summary | E11 |
