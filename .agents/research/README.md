# QCC × AI 开源生态调研（归档）

> **调研对象**：GitHub 社区上面向 QCC（Quality Control Circle，品管圈）及广义质量管理的 AI / Agent 项目
> **调研时间**：2026-11-15
> **样本**：40+ 组关键词检索，69 个仓库完成元数据与提交历史核验，另 9 个相关仓库列入清单
> **主报告**：[`qcc-ai-github-survey.md`](./qcc-ai-github-survey.md)（约 4.3 万字符，14 章）

---

## 一句话结论

GitHub 上「QCC + AI」几乎是空白市场——不是没需求，而是**没人把"方法学约束"当成一等公民来工程化**。全站 `"quality control circle"` 仅 3 个仓库，`topic:qcc` 的 13 个仓库里零个是品管圈。

## 五条核心发现

| # | 发现 | 关键证据 |
|---|---|---|
| 1 | **术语塌陷，可发现性≈0** | `qcc in:name` 1621 个结果，前 20 名全是企查查/量子计算/C 编译器/Qualcomm 芯片 |
| 2 | **唯一全流程应用仅 8 星** | `monkbird/QCmaker`，9 次提交，工程扎实但方法学是松的 |
| 3 | **方法论最严谨的项目 0 星、无 License** | `zhiwuli0228/skill-stock`：11 页强制方法链 + 证据契约 + 6 个审计脚本 |
| 4 | **生态重心已迁到 Agent Skill** | `automotive-skills-suite` 3312★（152 skills），护城河是"builder+reviewer 成对 + xlsx 契约" |
| 5 | **分析层拥挤，后半程空白** | 原因分析十余个项目；「要因确认 / 对策实施 / 标准化 / 检讨」几乎无人覆盖 |

## 目录结构

```
.agents/research/
├── README.md                      ← 你在这里（索引与速查）
├── qcc-ai-github-survey.md        ← 主报告（完整调研结论）
├── data/
│   ├── README.md                  ← 数据文件字段说明
│   ├── collect.sh                 ← 可复现采集脚本（search / meta / readme）
│   ├── search-queries.txt         ← 36 组检索参数快照
│   ├── repos-watchlist.txt        ← 69 个候选仓库清单
│   ├── repos-meta.tsv             ← 69 个仓库元数据（star/fork/license/活跃度，12 字段）
│   └── readme-priority.txt        ← 精读优先级清单
└── evidence/
    ├── readmes/                   ← 21 份精读的 README / 方法学文档原文
    └── search-raw/                ← 43 份原始搜索结果（可追溯每个判断的来源）
```

## 按问题快速导航

| 你想知道 | 去主报告看 |
|---|---|
| 到底有几个真·QCC 项目 | §3（逐项深评 9 个）+ §0 |
| 哪些项目值得抄 | §12.3 借鉴清单（按优先级 ⭐⭐⭐/⭐⭐/⭐） |
| QCC 十一步哪步没人做 | §9 能力矩阵（11 阶段 × 覆盖度） |
| 为什么这个赛道是空的 | §10 七个洞察 |
| 有哪些机会窗口 | §11 空白地带（高/中/低价值分层） |
| 我该做什么产品 | §12 定位建议、三层架构、M1–M6 MVP 顺序 |
| 完整项目清单 | §13.1（78 个，按层分组） |
| 检索命令怎么写的 | §13.2 或 `data/search-queries.txt` |

## 复现方式

```bash
cd .agents/research/data
gh auth status          # 需要已认证的 GitHub CLI
./collect.sh search     # 重跑 36 组检索（约 90 秒，受 API 限速）
./collect.sh meta       # 刷新仓库元数据
./collect.sh readme     # 重新抓取 README
./collect.sh all        # 全量
```

> 注意：重跑会覆盖同名快照文件。GitHub 的 star 数、提交数会随时间变化，本归档保留的是 **2026-11-15** 的快照。

## 数据口径与局限

**口径**：每个仓库核验 8 个维度——真实体量（commits/contributors）、活跃度（pushed_at）、交付形态、方法论深度、统计正确性、证据链、License、中文适配。判断"工程扎实"优先看 CI badge、测试数、截图可复现性，而非 README 自述。

**已识别的局限**（主报告 §13.3 详述）：

1. GitHub 之外未系统覆盖——Gitee、GitLab、企业内部自研、Dify/Coze 私有化魔改均不在样本内
2. 未做全量代码审计——69 个中精读约 20 个，部分结论基于 README 证据
3. star 数受项目创建时间影响，2026 下半年新项目积累不足
4. 商业产品（Minitab / ETQ / InfinityQS / 简道云等）未纳入对比
5. GitHub 对中文检索支持差，靠 code search 补足，仍可能有遗漏

## 三条给工程的硬结论

1. **别让 LLM 算数字**——Cpk、Ppk、相关系数、假设检验必须走确定性代码；LLM 只解释"这些数字意味着什么"。
2. **别用 RPN**——AIAG-VDA FMEA 2019 已用 Action Priority (AP) 替代；该领域星标最高的项目恰恰还在用 RPN。
3. **别忽略"待补充"状态**——QCC 现场经常没数据，强制 AI 编数字是自杀；`evidence_status: missing → 显示「待补充」` 是正确设计。

---

*归档于 2026-11-15 · 原始工作目录 `research/` 已并入本目录*
