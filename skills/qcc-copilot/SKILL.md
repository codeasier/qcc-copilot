---
name: qcc-copilot
description: >
  在成员现有编程 Agent 中按需推进 QCC（品管圈）课题：从已有改进或指定资料发现课题、
  应用适用方法与证据账本、确定性核算收益、评估推广复用、从同一快照生成报告/图表/PPT、
  导出课题摘要供负责人汇总并回流反馈。当需要把研发改进落实为有收益、可复用、方法规范的
  QCC 成果，或整理参评材料时使用。不用于后台监听、官方评分或自动宣称获奖。
version: "0.1.0"
---

# qcc-copilot Skill（成员侧）

本 Skill 让宿主 Agent（模型推理 + 已有来源访问能力）与确定性工具协作。宿主负责理解资料、
生成候选、解释方法和起草文字；Python 工具负责契约校验、状态写入、数值计算、文件生成与检查。
**默认按需调用**：只有成员显式调用并指定改进描述 / 资料范围 / 课题时才启动，不在普通开发中后台监听。

## 0. 定位工具与当前工作区（不依赖全局配置）

分发包自带 `src/qcc_copilot/` 与 `resources/`，无需新增模型账号、中心数据库或平台服务。
进入一次任务先做能力检查，并显式定位工作区：

```bash
export QCC="PYTHONPATH=<包根目录>/src python3 -m qcc_copilot"   # 安装后可用 qcc
$QCC capabilities
$QCC workspace.list --input '{"workspace":"<项目根>"}'
$QCC workspace.resume --input '{"workspace":"<项目根>","topic_id":"<课题标识，可选>"}'
```

- 工具以结构化 JSON 输入输出：`--input <file>` 或 stdin；输出 `{ "ok": true, "data": ... }` 或 `{ "ok": false, "error": {...} }`。
- 工作区根默认是成员指定目录下的 `.qcc/<topic-id>/`；一个资料项目可有多个课题，续接时必须明确 `topic_id`。
- 多课题存在且未指定 → `ambiguous_workspace`，展示候选，不覆盖任何档案；档案损坏/未知版本 → `damaged_workspace`，保留原档案。
- 能力检查会列出缺失依赖导致的**受限步骤**（如缺少独立渲染器时渲染检查为未执行），不要把未执行检查当作通过。

## 1. 三种进入方式（按需）

| 入口 | 命令序列起点 | 参考 |
|---|---|---|
| 提交已有改进 | `discovery.refine` → `discovery.select` | `references/discovery.md` |
| 指定资料发现候选 | `sources.index` → `discovery.candidates` → `discovery.reconcile` → `discovery.select` | `references/discovery.md` |
| 续接已有课题 | `workspace.resume` → 按 `next` 继续 | `references/workspace.md` |

候选发现由宿主读取资料、推理后**提交结构化候选卡**，工具只校验、允许零候选、绑定覆盖边界，
不虚构题目数量或收益。选定范围后才建档，单仓库多个功能不自动计入同一课题。

## 2. 领域操作入口（命令 → 能力）

| 能力 | 命令 | 输入契约 |
|---|---|---|
| 分发/续接/兼容 | `capabilities`、`workspace.*` | `topic` |
| 双入口发现 | `sources.*`、`discovery.*` | `sources_doc`、`candidate` |
| 方法引导 | `methods.*` | `method_profile_v1.json` |
| 证据账本 | `claim.*`、`evidence.invalidate`、`dependency.link`、`delivery.snapshot` | `claim`、`delivery_snapshot` |
| 收益核算 | `benefit.*` | `calculation` |
| 推广复用 | `reuse.*` | 结构化复用记录 |
| 成果与自检 | `deliverable.*` | `delivery_snapshot` |
| 负责人汇总 | `summary.*`、`feedback.*` | `summary`、`feedback` |

完整命令、字段与示例见 `references/commands.md`。契约类型与版本见 `$QCC contract.types`。

## 3. 推荐闭环（discovery → deliverables → summary）

1. `workspace.init` 或 `discovery.select` 建档 → 得到 `topic_id`。
2. `sources.index` 记录覆盖范围（失败/未读/截断不可当作全范围已检查）。
3. `methods.stage` / `methods.check` / `methods.recommend` 给出下一步与补证任务，缺口写成 `tasks`。
4. `benefit.compute`（确定性、可复算）、`claim.add`（区分 origin/support）、`dependency.link`。
5. `reuse.*` 评估共性、生成复用说明、区分潜在/复现/实际采用。
6. `delivery.snapshot` 固定快照 → `deliverable.compile` 生成报告/收益/复用/图表/底稿/真实 PPTX/slides.json。
7. `deliverable.review`（独立三维定性检查）→ `deliverable.verify`（覆盖/占位符/可检测溢出/独立渲染）→ `deliverable.status`（draft / review-ready）。
8. `summary.export` 导出标准摘要；负责人 `summary.aggregate` + `summary.views` + `feedback.export`；成员 `feedback.import` 回流建议/待办。

## 4. 不可越过的规则（务必遵守）

- 成员口述收益、上线链接、AI 推断、估算、示例分别标记；口述不自动成为实测，只有上线链接不证明收益或采用。
- 相关性/投票/评分不单独确认因果；未执行活动不因补写材料被标为已发生。
- 收益走 `benefit.compute`，等待/机器耗时不直接折人力，净收益可为负，实测/估算/预测分离，重复事件去重。
- 资料不足允许零候选、草稿与补证任务；核心主张无支持或存在严重冲突时 `deliverable.status` 只能得到 `draft`。
- 未配置官方评奖细则：只做定性检查，**不生成官方分数、权重或获奖概率**；固定十一阶段/特定模板不作为所有课题统一标准。
- 工具易用性与成果推广性分别计量；"少花时间整理材料"不是课题可跨部门推广的证据。
- 所有写入带修订前提：发现人工修改/并发写入报 `revision_conflict`，保留原档案；相同输入重跑不重复生成业务事实。
- 历史交付保留原快照；输入变化通过 `evidence.invalidate` 定向失效并标记相关材料待核验。

## 5. 受限与诚实表达

- 缺少 LibreOffice/soffice 时，macOS 用 Quick Look 做「独立打开核验」，其它环境渲染检查为 `not_run`，
  `overall` 不会标为 `passed`；这只证明可打开，不证明逐页版式无缺陷。
- 负责人汇总只表示已导入快照，未收到更新不解释为课题无进展。
- 样例来自 `tests/fixtures/`，是验证情境，不是真实参评课题或已实现收益。

更多：成员快速开始 `quickstart.md`、负责人使用 `lead-guide.md`、升级回滚 `upgrade-rollback.md`、
支持矩阵 `references/support-matrix.md`。
