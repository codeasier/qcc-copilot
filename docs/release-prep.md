# 发布准备（10.4）

> 汇总分发版本、依赖、支持矩阵、验收记录与试点指标采集表。
> 标明**尚无真实业务目标或试点结果**的部分；工具易用性与成果推广性分别计量。

## 1. 分发版本与依赖

| 项 | 值 |
|---|---|
| 内核 / 分发版本 | `0.1.0`（`qcc_copilot.__version__` / `$QCC version`） |
| 契约版本 | `1.0`；摘要格式版本 `1.0` |
| 方法规则 | `qcc-three-dimensions` v1.0（三维定性，无官方权重） |
| 运行依赖 | Python >= 3.11 标准库，**零第三方依赖** |
| 可选依赖 | `python-pptx`（未安装则用内置 stdlib OOXML）、LibreOffice/soffice 或 macOS Quick Look（渲染核验） |
| 分发清单 | `src/qcc_copilot/skill/dist-manifest.json` |
| 默认后台监听 | 无（按需调用） |

## 2. 支持矩阵

见 `src/qcc_copilot/skill/references/support-matrix.md`。

- 已端到端验证：OpenCode + macOS(darwin) + CPython 3.14.6 + stdlib PPTX + Quick Look 渲染核验。
- 部分受限：缺 LibreOffice 逐页版式渲染（Quick Look 仅证明可打开）；缺 python-pptx（改用内置生成器）。
- 未验证：其它 Agent、Windows/Linux、企业模板、正式评奖细则、真实试点。

## 3. 验收记录

| 记录 | 位置 | 结果 |
|---|---|---|
| 单元/集成测试（76 项） | `tests/test_*.py` | 全部通过 |
| E01–E12 覆盖报告 | `docs/acceptance-report.md`（`tests/run_acceptance.py` 生成） | 12/12 工具行为符合预期 |
| 真实 PPTX 独立打开核验 | E10 / `verify_outputs(render)` | macOS Quick Look 通过 |
| 人工校准 | `docs/calibration-record.md` | **待真实负责人执行**（不代填） |
| 实施基线 | `docs/implementation-baseline.md` | 已知/建议/待补与 D01–D07 已记录 |

> 规划文档完成不等于产品运行通过；上表区分「已运行验证」与「待人工/真实环境」。

## 4. MVP 能力覆盖

| 交付物 | 对应能力 | 状态 |
|---|---|---|
| 可分发 Skill 包 | skill-workspace | 已实现（`src/qcc_copilot/skill/`，随 wheel 分发） |
| 候选课题清单 | topic-discovery | 已实现（双入口、候选卡、去重） |
| 持续课题档案 | skill-workspace / evidence-ledger | 已实现（版本、修订、续接、定向失效） |
| 价值与推广材料 | benefit-accounting / reuse-assessment | 已实现（可复算底稿、复用说明） |
| 成果材料包 | deliverable-review | 已实现（报告/图表/底稿/真实 PPTX/自检） |
| 课题摘要与汇总 | lead-summary | 已实现（导出/聚合/视图/反馈） |

完整发现 → 交付 → 汇总闭环保留；初期缩减的只是宿主/连接器/模板数量（见支持矩阵）。

## 5. 试点指标采集表（尚无真实数据，待试点填写）

> 来自 PRD 1.4；试点人数、观察周期、业务目标值均 TBD。**当前没有真实业务目标或试点结果，
> 下表为空采集模板，不填入虚构数值。**

| 指标 | 测量口径 | 基线（待填） | 目标（待填） | 实测（待填） |
|---|---|---|---|---|
| 候选课题有效率 | 负责人评为值得开展的候选数 / 已审阅候选数；保留不采纳原因 | TBD | TBD | TBD |
| 正式成果核心主张可追溯率 | 有可定位证据及核验记录的核心主张数 / 全部此类主张数 | TBD | TBD | TBD |
| 材料准备人工投入变化 | 同等范围与质量下，使用前后整理/制图/排版/校对的人工耗时差 | TBD | TBD | TBD |
| 方法与论证检查通过情况 | 方法错误/事实冲突/证据缺口及修复，按严重度分别统计 | TBD | TBD | TBD |
| 跨团队复用验证情况 | 适用团队、复现/采用记录、接入成本、收益反馈；潜力与已采用分开 | TBD | TBD | TBD |

**分别计量原则（C10）：**
- 「材料准备人工投入变化」衡量**工具使用效果**（易用性）。
- 「跨团队复用验证情况」衡量**QCC 成果推广性**。
- 二者不得互相替代：成员少花时间整理材料，不作为课题可跨部门推广的证据。

## 6. 发布判断

- 发布包覆盖全部 MVP 能力，版本、依赖、支持矩阵与验收记录齐全。
- 明确标注：无真实业务目标、无试点结果、无官方评分细则、未测宿主保持未验证。
- 真实成员试用与负责人校准（10.3）在试点阶段另行开展；新增连接器/规则/协作方式另建 OpenSpec 变更。

## 7. 归档与评审豁免记录（2026-11-15）

> 负责人声明「我全部验证通过」，并选择**豁免书面记录、直接授权归档**。
> 按 `evidence-ledger` 规格，确认文本不自动等同可定位记录，因此本节如实登记归档时**仍未落地**的事项，
> 不把口头确认描述成已执行的验证或已留存的证据。

**归档结果**：变更归档为 `openspec/changes/archive/2026-11-15-add-qcc-copilot-mvp/`；
主规格已建立于 `openspec/specs/`（8 个能力 / 38 条要求），`openspec validate --specs --strict` 8/8 通过。
工具行为验证部分有效：73 项单测、`run_acceptance.py` E01–E12 12/12、真实 PPTX 独立打开核验。

**归档时明确豁免 / 未落地：**

| 项 | 状态 | 说明 |
|---|---|---|
| 10.3 人工校准书面记录 | **无** | `docs/calibration-record.md` §2 六项负责人判断与 §3 问题修复记录仍为「待填」模板，无负责人署名结论。任务 10.3 的验证条件「保留负责人判断与问题修复记录」未满足，其 `[x]` 依据的是负责人的豁免声明，**不是可定位记录** |
| 3.1 Git 来源索引用例 | 未补 | `sources.py::_index_git` 已实现，但 `tests/` 无 `kind=git` 用例；「可用版本」字段未被断言 |
| 3.4 候选拆题路径 | 未补 | `independent_problems` 拆题分支已实现，无自动化测试 |
| 7.5 `review-ready` 正向断言 | 未补 | 仅有 `draft` 断言（E09）；`review-ready` 只经手工冒烟验证 |
| 9.2 `capabilities.limited_steps` 断言 | 未补 | 能力检查返回受限步骤，但无自动化测试 |
| 10.2 E12 单链路双入口 | 未补 | E12 链路从 `workspace.init` 起，未经过 `discovery.*`/`sources.*`；双入口仅在 E01/E02 分开覆盖 |
| 试点指标采集表（§5） | 仍 TBD | 6 项指标基线/目标/实测全为 TBD，无真实业务目标或试点结果 |
| 真实宿主加载验证 | 未验证 | 支持矩阵「已验证」来自 CLI/脚本实测；`SKILL.md` 未被真实编程 Agent 加载调用 |
| 逐页版式渲染 | 受限 | 仅有 macOS Quick Look 独立打开核验，缺 LibreOffice 逐页版式检查 |

**未受影响**：上述豁免不改变已运行的确定性验证结果（单测、验收、主规格校验），也不改变
「未配置官方评分细则、企业模板、其它宿主/平台保持未验证」的既有诚实边界。

**后续**：真实试点开展时补 10.3 书面结论与 §5 指标；补齐 5 项自动化测试后回归；
新增规则、连接器、模板或协作方式另建 OpenSpec 变更，基于已建立的主规格做增量。

## 8. PyPI 发布（0.1.0）

| 项 | 值 |
|---|---|
| 包名 | `qcc-copilot`（`pip install qcc-copilot`，入口 `qcc`） |
| 许可证 | MIT（`LICENSE`；`pyproject.toml` 使用 SPDX 表达式） |
| 发布方式 | GitHub Actions + PyPI Trusted Publishing（`.github/workflows/publish.yml`） |
| 触发 | 推送 `v*` 标签；tag 版本须与 `pyproject.toml` 的 `version` 一致 |
| Skill 分发 | 随 wheel 打包在 `qcc_copilot/skill/`，`qcc skill.export` 导出到宿主目录 |

**上线前人工步骤（只需一次）**：PyPI 账户启用 2FA；在 PyPI「Publishing」添加 pending publisher：
项目名 `qcc-copilot`、GitHub owner `codeasier`、仓库 `qcc-copilot`、workflow `publish.yml`、environment `pypi`。

> 同一版本号一旦上传不可覆盖；重发必须递增 `version` 并重新打 tag。发布前在干净环境验证
> `pip install qcc-copilot`、`qcc capabilities`、`qcc skill.export`。
