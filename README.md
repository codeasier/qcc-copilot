# qcc-copilot

面向软件研发团队的 QCC（质量管理圈 / 品管圈）赋能工具。

通过成员现有的编程 Agent，帮助发现和提炼改进课题、落实 QCC 方法、积累证据、核算收益，并生成可复用、可参评的成果；负责人通过轻量汇总进行辅导和筛选。

## 当前阶段

产品方向已确认；OpenSpec 变更 `add-qcc-copilot-mvp` 的提案、规格、设计与 46 项任务已实施完成，并于 2026-11-15 归档、建立主规格（8 能力 / 38 要求）。当前为可分发 MVP：stdlib Python 确定性内核 + 成员侧 Skill + 负责人轻量汇总。

> OpenSpec 规划文档、变更归档与主规格（`openspec/`）**不纳入本仓库分发**，保留在本地工作区；后续变更基于该主规格另建。

## 安装

```bash
pip install qcc-copilot            # Python >= 3.11，零第三方依赖
qcc capabilities                   # 能力检查；受限步骤会明确列出
qcc skill.export --input '{"dest":"~/.config/opencode/skills/qcc-copilot"}'
```

`skill.export` 把随包分发的 Skill 文档（`SKILL.md`、快速开始、负责人指南、升级回滚与 references）导出到宿主 skills 目录；目标目录非空时需加 `"force": true`。

源码方式（不安装）：

```bash
git clone https://github.com/codeasier/qcc-copilot.git
PYTHONPATH=$PWD/qcc-copilot/src python3 -m qcc_copilot capabilities
```

## 快速验证

```bash
PYTHONPATH=src:. python3 -m unittest discover -s tests -t . -p 'test_*.py'   # 76 项
PYTHONPATH=src:. python3 tests/run_acceptance.py                              # E01–E12 覆盖报告
PYTHONPATH=src python3 -m qcc_copilot capabilities
```

## 文档

- [Skill 入口](https://github.com/codeasier/qcc-copilot/blob/main/src/qcc_copilot/skill/SKILL.md)：成员/负责人入口、命令契约、快速开始、升级回滚、支持矩阵（随 wheel 分发）。
- [产品需求与 MVP 边界](https://github.com/codeasier/qcc-copilot/blob/main/docs/product-requirements.md)：产品共识与需求背景，是 OpenSpec 规划的来源。
- [实施基线](https://github.com/codeasier/qcc-copilot/blob/main/docs/implementation-baseline.md)、[验收覆盖报告](https://github.com/codeasier/qcc-copilot/blob/main/docs/acceptance-report.md)、[人工校准记录](https://github.com/codeasier/qcc-copilot/blob/main/docs/calibration-record.md)、[发布准备](https://github.com/codeasier/qcc-copilot/blob/main/docs/release-prep.md)。
- [开源生态调研](https://github.com/codeasier/qcc-copilot/blob/main/.agents/research/README.md)：2026-11-15 的 GitHub 调研索引、主报告与证据。

主规格已在本地 `openspec/specs/` 建立，后续新增规则、连接器或模板基于主规格另建 OpenSpec 变更。归档时豁免与未落地事项（人工校准书面记录、5 项自动化证据缺口、试点指标）逐项登记于 [发布准备 §7](https://github.com/codeasier/qcc-copilot/blob/main/docs/release-prep.md#7-归档与评审豁免记录2026-11-15)。设计中的 Python、本地档案、PPTX 和文件式汇总属于**建议实施基线**（本次采用，零第三方依赖）；具体宿主支持、正式评奖细则、企业模板和试点参数仍按文档记录适配，里程碑日期尚未约定。仅 OpenCode + macOS 组合完成端到端验证，未测组合保持未验证。

许可证：[MIT](https://github.com/codeasier/qcc-copilot/blob/main/LICENSE)。
