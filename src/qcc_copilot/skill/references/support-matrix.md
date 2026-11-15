# 支持矩阵与实测范围（9.3）

> 每项支持声明标注版本与验证范围；未测或仅部分受限的组合与已完成端到端验证的组合分开。默认无后台监听。

## 已实测组合（本变更实施会话）

| 宿主 | 系统 | 运行时 | 生成 | 独立渲染核验 | 范围 | 结果 |
|---|---|---|---|---|---|---|
| OpenCode（当前会话） | macOS / darwin | CPython 3.14.6，标准库 | 内置 stdlib OOXML PPTX | macOS Quick Look（Office 导入器） | 双入口 / 续接 / 计算 / 契约 / 证据 / 方法 / 推广 / 材料编译 / 真实 PPTX / 摘要聚合 / 反馈 / 端到端链路 | 已端到端验证（E01–E12、76 项单测） |

- 该组合完成 `verify_outputs(run_render=true)` → `render.status=passed`，`deliverable.status` 可达 `review-ready`。
- 默认按需调用，无后台扫描、提醒或常驻任务。

## 部分受限 / 未执行

| 能力 | 状态 | 说明 |
|---|---|---|
| LibreOffice/soffice 逐页版式渲染 | 未安装 → 受限/未执行 | 以 Quick Look 独立打开核验替代；仅证明可打开，不证明逐页版式无缺陷；缺失时 `overall` 不标 passed |
| python-pptx | 未安装（可选） | 改用内置 stdlib OOXML 生成器，仍产出真实可编辑 PPTX；能力检查会报告 | 

## 未验证组合（不宣称支持）

| 组合 | 状态 |
|---|---|
| 其它编程 Agent（Claude Code / Cursor / Copilot 等） | 未验证（理论上可读 Skill，未做工作流实测） |
| Windows / Linux 各发行版 | 未验证 |
| 企业 PPT 模板 / 视觉资产 / 字体 | 未配置 |
| 正式 QCC 评奖细则与官方权重 | 未配置（仅三维定性检查） |
| 真实成员试点、业务目标与阈值 | 未开展（见 D06） |

## 能力检查

```bash
PYTHONPATH=<包>/src python3 -m qcc_copilot capabilities
# 输出 kernel_version / python / core / optional / limited_steps / executable_steps
```

`official_scoring_configured=false`、`core.stdlib_ooxml_pptx=true`、`core.deterministic_calc=true` 恒为真；
`optional.renderer` 与 `limited_steps` 随环境变化，按实际结果记录，不笼统声明全部 Agent/平台均已支持。

## 声明原则

- "已验证" 需同时具备版本号、操作系统、验证范围与实测结果（见 `docs/acceptance-report.md`）。
- 未在矩阵中列出的组合保持"未验证"；能力不足时说明受影响步骤和可继续的工作。
