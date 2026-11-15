# GitHub 社区「AI / Agent 辅助 QCC」开源项目深度调研

> 调研时间：2026-11-15　|　样本：GitHub 全站检索 + 69 个仓库逐一核验　|　方法：GitHub REST Search/Code Search + 仓库元数据 + README/源码结构 + 提交历史核验

---

## 0. 一页速览（TL;DR）

**结论一：真正的「QCC（Quality Control Circle，品管圈）+ LLM」项目在全 GitHub 上不超过 5 个，且没有一个超过 10 star。**
全站搜 `"quality control circle"` 只有 **3 个**仓库；`topic:qcc` 的 13 个仓库里**零个**是品管圈；中文生态里真正跑通"全流程"的只有 `monkbird/QCmaker`（8★，9 次提交）。

**结论二：这不是"没人做"，而是"做的人都落错了地方"——QCC 的 AI 化需求真实存在，只是被四个更大的同名事物（企查查、量子计算、Qualcomm QCC 芯片、QuakeC 编译器）彻底淹没了可发现性。**
`qcc in:name` 返回 1621 个仓库，前 20 名分别是剪贴板工具、企查查爬虫、量子计算教材、C 编译器、Qualcomm 芯片库 —— 没有一个是品管圈。

**结论三：生态真正的重心已经从"应用"迁移到"Agent Skill 包"。**
质量领域唯一破千星的仓库是 `jherrodthomas/automotive-skills-suite`（3312★，152 个 Claude Skill），它的护城河不是模型，而是 **"builder + reviewer 成对 + xlsx 文件契约"**。2026 年新增的质量类项目中，Skill 形态占比已经超过 Web 应用。

**结论四：最拥挤的是"原因分析"，最空白的是"对策实施 / 标准化 / 检讨"。**
把 11 个 QCC 阶段拆开看：鱼骨图、5Why、柏拉图有十来个项目覆盖；**「要因确认」「对策实施」「标准化」「检讨与下一步」四个阶段几乎无人覆盖**。所有项目都停在"分析出原因 + 生成一份漂亮报告"，没有一个闭环到"改进被执行、被验证、被固化"。

**结论五：质量 AI 的产品骨架已经收敛，同质化严重。**
几乎所有 8D/CAPA 项目都是同一套：`语义检索历史质量文档 → 结构化表单引导 → 生成-审校双模型 → 人工确认门`。差异只在 UI 和文档解析。

**结论六：统计学正确性才是真护城河，而不是生成能力。**
`Hulk-Zhao/Hogo-QA-tool` 专门在 README 里强调"修正了旧工具 Pp 恒等于 Cp 的缺陷"；`M1ndSmith/ASPC` 强调 "formula fidelity ≠ Minitab/JMP parity"。质量人对数字错误零容忍——AI 只能做解读，不能做计算。

**一句话给 qcc-copilot：** 这个赛道在 GitHub 上几乎是空的，但空的原因不是没需求，而是**没人把"QCC 方法学约束"当成一等公民来工程化**。`zhiwuli0228/skill-stock` 已经证明这条路可行（把 11 步编译成 11 类强制页面 + 合规审计脚本），但它 0★、无 License、只做 PPT。这正是可以正面切入的位置。

---

## 1. 调研方法与边界

### 1.1 先澄清一个致命歧义：QCC 指什么

在 GitHub 上搜 "QCC"，你会同时撞上四类同名事物，而真正的品管圈排在最后：

| 缩写 | 实际含义 | 体量 | 代表仓库 |
|---|---|---|---|
| **QCC** | 企查查（qcc.com） | 数百仓库，最高 335★ | `zhaoboy9692/qccspider`、`zhanglunet/qcc`（146 个 MCP tool） |
| **QCC** | Quantum Computing / Quantum Compiler | 上百仓库 | `qcc4cp/qcc`（122★，教材源码） |
| **QCC** | Qualcomm QCC51xx 蓝牙芯片 | 数十仓库 | `fjpolo/Qualcomm_QCC51xx-OpenSourceCapabilities` |
| **QCC** | QuakeC 编译器 | 数十仓库 | `lbsmith/ProQCC`、`maekawatoshiki/qcc` |
| **QCC** | **Quality Control Circle（本次调研对象）** | **≤5 仓库，最高 8★** | `monkbird/QCmaker` |

> 这个歧义不是花边，它是**本次调研最重要的发现之一**：品管圈社区在 GitHub 上几乎没有"自我标识"能力，导致任何想找这类项目的人（包括 AI 搜索）都会被导流到错误方向。反过来，这也意味着这个位置**没有既有玩家把守**。

本次调研同时覆盖两条线，因为中文语境里"质量管理圈"既可指**品管圈活动**，也可泛指**质量管理圈子**：

- **A 线（狭义）**：QCC / 品管圈 / QC 小组活动全流程 —— 主题选定 → 现状调查 → 目标设定 → 原因分析 → 要因确认 → 对策拟定 → 对策实施 → 效果确认 → 标准化 → 检讨与下一步。
- **B 线（广义）**：AI/Agent 辅助质量工程 —— 8D、RCA、FMEA、APQP/PPAP、SPC/MSA、QMS 审核、CAPA、NCR、供应商质量。

### 1.2 检索策略

共执行 **40+ 组检索**，四类通道并用：

1. **仓库名/描述检索**：`qcc in:name`、`qcc in:description`、`"quality control circle"`、`"QC circle"`、`QC小组`、`品管圈`、`鱼骨图`、`柏拉图`、`QC七大手法`
2. **README 全文检索**：`品管圈 in:readme`、`QC小组 in:readme`（GitHub 对中文 README 的索引噪音大，需人工二次筛选）
3. **代码检索**（关键突破点）：`"品管圈" language:Python`、`"要因确认"`、`"QC story"`、`"品管圈" filename:README.md` —— 这是唯一能穿透"项目没打 tag"的通道，**直接命中了本次最有价值的项目 `zhiwuli0228/skill-stock`**
4. **Topic 检索**：`topic:quality-management`(283)、`topic:qms`(72)、`topic:spc`(227)、`topic:six-sigma`(150)、`topic:fmea`(70)、`topic:qcc`(13，全是噪音)

关键词矩阵（节选）：

```
质量方法论   quality control circle / QC circle / QCC / QC story / PDCA / DMAIC / PDCA / kaizen / lean
七手法      fishbone / ishikawa / pareto / control chart / histogram / scatter / check sheet / 柏拉图 / 鱼骨图
问题解决    8D / CAPA / NCR / SCAR / RCA / 5 whys / root cause / nonconformance
风险与策划  FMEA / DFMEA / PFMEA / APQP / PPAP / control plan / MSA / gage R&R / SPC / Cpk
体系与审核  ISO 9001 / IATF 16949 / ISO 13485 / ISO 17025 / VDA 6.3 / audit / QMS
AI 载体     agent skills / claude skill / MCP server / copilot / RAG / multi-agent / llm
中文场景    品管圈 / QC小组 / 质量改进 / 品质管理 / 智能体 / 质量报告 / 不良分析
```

### 1.3 评分口径

对每个候选仓库核验 8 个维度，避免被"README 吹牛"误导：

| 维度 | 怎么核验 | 为什么重要 |
|---|---|---|
| 真实体量 | `commits` 总数 + `contributors` 数 | 9 次提交 / 211 个文件 = 打包式发布，不是持续开发 |
| 活跃度 | `pushed_at` + 创建时间 | 区分"新项目"和"死项目" |
| 交付形态 | Web / 桌面 / CLI / Skill / MCP | 决定可复用性 |
| 方法论深度 | 是否覆盖标准条款、是否有校验器 | 质量场景的真门槛 |
| 统计正确性 | 是否区分 Cp/Cpk 与 Pp/Ppk、是否用 AP 替代 RPN | 质量人的底线 |
| 证据链 | 数字能否追溯到源文件 | QCC 评审的硬要求 |
| License | 是否可商用 | GPL/AGPL 会传染 |
| 中文适配 | 是否理解 T/CAQ、国卫办文件、双归零 | 本土化壁垒 |

---

## 2. 生态全景：六层结构

```
┌──────────────────────────────────────────────────────────────────────┐
│ L6  交付层    PPT/Word 编译、版式审计、评审模拟                        │
│      QCmaker · skill-stock(qcc-ppt-*) · cy556-like · Novushisi        │
├──────────────────────────────────────────────────────────────────────┤
│ L5  流程 Copilot  8D / RCA / CAPA / 供应商质量 的引导式闭环            │
│      kolmag/8d-expert-workbench · orcunku · mickemora · Recalltrace   │
├──────────────────────────────────────────────────────────────────────┤
│ L4  方法学 Skill 包   把标准条款编译成 Agent 可执行指令                │
│      automotive-skills-suite(3312★) · Quality-Engineering-Skills(47★) │
│      skill-qc-tools · skill-apqp · iso-17025-skill · six-sigma-in-r   │
├──────────────────────────────────────────────────────────────────────┤
│ L3  单点工具层   FMEA / SPC / MSA / 柏拉图 / 鱼骨图                    │
│      LLMRiskAnalyzer(41★) · open-fmea(47★) · Hogo-QA-tool · ASPC      │
├──────────────────────────────────────────────────────────────────────┤
│ L2  统计内核层   控制图、过程能力、判异规则（AI 不可替代）             │
│      luca-scr/qcc(61★) · py-qcc · shewhart · cassini · quality-platform│
├──────────────────────────────────────────────────────────────────────┤
│ L1  数据与平台层   QMS / MES / MCP / 证据库                            │
│      OpenQMS(32★) · AI-QMS · factorysemantics-mes · mcp-qms · 1factory│
└──────────────────────────────────────────────────────────────────────┘
        ▲ 越往上越"像 AI 产品"，越往下越"像基础设施"
        ▲ 越往上越稀缺，越往下越拥挤
```

一个反直觉的结构特征：**层数越往上，项目越少、越不成熟；层数越往下，项目越多、越工程化。** 这和一般软件生态（应用层繁荣、基础设施稀缺）正好相反。原因是质量管理的价值密度在"方法学约束"而非"生成能力"——而方法学约束最难工程化。

> **阅读顺序说明**：第 3–8 章按「与 QCC 的相关距离」排列（本体 → 方法学 → 流程 → 单点工具 → 统计内核 → 平台），层号 L1–L6 只是分类标签，不表示章节先后。

---

## 3. L6 交付层：QCC / 品管圈本体项目（逐项深评）

这一层是本次调研的核心，也是全 GitHub 最荒芜的地方。全部候选只有 9 个，其中 3 个是空壳或周边玩具。

### 3.1 `monkbird/QCmaker` —— 唯一跑通"QCC 全流程"的开源应用

| 项 | 值 |
|---|---|
| 地址 | https://github.com/monkbird/QCmaker |
| 星标 / Fork | 8 / 0 |
| 语言 / 许可 | Python / MIT |
| 提交 / 贡献者 | **9 次 / 1 人**（211 个文件，典型"打包式发布"） |
| 创建 / 最近更新 | 2025-11-26 / 2026-09-17 |
| 形态 | 前后端分离 Web 应用（FastAPI + React 19） |

**它做了什么（六步向导）：**

1. **系统配置** —— 支持任意 OpenAI 兼容 API（DeepSeek、Moonshot）或本地 Ollama；内置 Token 消耗监控与预算保护。
2. **QC 选题顾问** —— 自然语言对话挖掘痛点，基于 **SMART 原则**自动评估选题可行性；支持 Word/Excel/PPT/PDF/CSV 入知识库做 RAG。
3. **数据清洗与预览** —— 缺失值/异常值/格式问题检测，交互式分页确认（异常值默认保留）。
4. **多模型研讨室** —— LangGraph 编排"数据分析师 / 质量专家 / 主持人"三个角色，WebSocket 流式研讨，自动出会议纪要。
5. **可视化与决策** —— 按数据特征推荐图表类型，ECharts 渲染，带"图表拦截器"防幻觉图。
6. **终稿生成** —— python-pptx 输出标准汇报 PPT，支持本地模板。

**工程上真正值得抄的地方**（比它的 QCC 方法论更值钱）：

- **预算预留-结算-对账闭环**：请求前预留 token 额度，未发出请求自动回收，已发出但费用未知的持续占用需对账，供应商超额熔断 —— 这是企业级 LLM 应用该有的成本治理。
- **PII 边界感知脱敏**：手机号/身份证/邮箱在聊天输入输出与 embedding 全链路脱敏，原文仅存本地。
- **SSRF 防护**：模型 API 地址强制 http(s)、禁内网/元数据地址、禁带凭据、禁环境代理与重定向。
- **版本化数据契约**：`project_id + dataset_id + revision` 三元组，改课题或数据后下游成果自动失效。

**它缺什么（也是整个赛道的通病）：**

- ❌ **没有"现状调查 → 目标设定 → 要因确认 → 效果确认"的显式阶段**。它的流程是"选题→清洗→研讨→图表→PPT"，本质是"AI 帮你写份报告"，而不是"AI 陪你走完 QC 十步"。
- ❌ **图表是通用图表推荐**（柱/折/饼），不是 QC 手法强制（柏拉图必须有累计百分比 80% 线、鱼骨图必须有六大类分支、控制图必须判异）。这在正式评审里会被扣分。
- ❌ **没有证据链**。生成的数字无法回溯到源文件，评审时无法自证。
- ❌ 单用户 / 团队共享令牌模型，无多租户。
- ❌ 9 次提交说明社区协作≈0，Issue 区基本空白。

> **判读**：这是目前"完成度最高"的 QCC AI 应用，但它的完成度体现在**工程安全与成本治理**，而不是**方法学严谨性**。它更像一个"LLM 应用脚手架 + QCC 皮"，而不是"QCC 专家系统"。

### 3.2 `zhiwuli0228/skill-stock` —— 方法论最严谨的实现（本次最大发现）

| 项 | 值 |
|---|---|
| 地址 | https://github.com/zhiwuli0228/skill-stock |
| 星标 / Fork | **0 / 0** |
| 语言 / 许可 | Python / **无 License**（重要风险） |
| 提交 / 贡献者 | 22 次 / 1 人 |
| 形态 | Agent Skill 集合（3 个 QCC 变体） |

一个中文开发者的私有 Skill 仓库，里面藏着 GitHub 上**最完整的 QCC 方法学工程化实现**。三个变体：

- `qcc-ppt-baseline-producer`（v2.9）—— 面向"低能力 Agent"的基线产线
- `qcc-ppt-method-compliant-producer` —— 方法学合规版
- `qcc-ppt-visual-enhancer` —— 视觉增强版

**核心设计：把 QCC 方法学编译成"强制页面链 + 数据契约 + 审计脚本"。**

它规定的 11 页强制方法链（缺一页就不算合格的品管圈成果）：

| QCC 阶段 | 强制方法页 | 强制视觉形态 |
|---|---|---|
| 主题评审 | 头脑风暴 | 左主题锚点 + 2×3 想法卡，**禁止放射状连线**（截图会糊） |
| 主题评审 | 亲和图 | 聚类卡片 + 分组标签 |
| 主题评审 | 检查表 | 评分矩阵 + TOP 汇总卡（分数框要放得下两位数） |
| 把握现状 | **SIPOC** | 供/入/流程/出/客 五列表 |
| 把握现状 | **柏拉图** | 降序柱 + 累计百分比 + 80% 标线 |
| 把握现状 | 子流程图 | 流程卡 + 痛点标记 |
| 根因分析 | **鱼骨图** | 分支必须收敛到一个关键治理缺口 |
| 根因分析 | 矩阵图 | 原因评分 + 保留/剔除结论 |
| 根因分析 | 根因验证 | 方法/证据/结果/结论 四列表 |
| 拟定对策/实施 | 5W | What/Why/Who/When/Where |
| 成果固化 | 标准化清单 | 标准化资产 + 后续检查项 |

**它的数据契约（`qcc-data.yaml`）规定了"每个数字必须有证据"：**

```yaml
meta: {}      # 项目元信息
circle: {}    # 圈名、课题、活动周期、圈长、辅导员、圈员及分工
qcc_process: {}
results: {}
standardization: {}
promotion: {}
```

> 每个核心数字必须携带 `evidence_ids: [E001]` 或 `evidence_ref: docs/...`，**否则必须标 `evidence_status: missing` 并显示为「待补充」，不得进入正式页**。

**它还带了 6 个审计脚本**（这是它和所有其他项目的本质差异）：

| 脚本 | 作用 |
|---|---|
| `validate_qcc_data.py` | 数据契约校验 |
| `check_qcc_method_compliance.py` | 方法学合规检查（页面级） |
| `audit_qcc_ppt_format.py` | 格式审计 |
| `audit_qcc_visual_heuristics.py` | 视觉启发式审计（布局/密度/溢出） |
| `layout_lint.py` / `placeholder_lint.py` | 版式与占位符 lint |
| `render_check.py` | LibreOffice 渲染回读校验 |

它甚至规定了**"降级策略"**：`当不确定时，优先保证方法可辨识度而非视觉创意。评审者应该能在三秒内从标题和布局识别出这是什么方法页。`

> **判读**：这个项目的价值不在代码量（build 脚本 50KB 是真实现），而在于它**第一次把"QCC 评审员的眼光"翻译成了可执行的机器规则**。它证明了这条路的可行性，同时暴露了三个问题：0 star（没有传播）、无 License（无法复用）、只做 PPT（没有流程、没有数据采集、没有效果验证）。

### 3.3 `Hulk-Zhao/Hogo-QA-tool` —— 最像"一线质量员真正会用"的工具

| 项 | 值 |
|---|---|
| 地址 | https://github.com/Hulk-Zhao/Hogo-QA-tool |
| 星标 | 2 |
| 语言 / 许可 | TypeScript / MIT |
| 形态 | **单文件离线网页**（构建产物是一个 `index.html`，双击即用） |

**能力清单：**

- 导入 Excel 尺寸/不良数据 → 自动识别列名 → 校验（特性数/测量值数/不良类型数）
- **Cp / Cpk（组内 σ）与 Pp / Ppk（整体 σ）并列展示**，直方图叠加规格限，双西格玛水平标注
- Xbar-R 双图 + 分区带 + 违规点标红，**12 条判异准则逐条开关**（含西方电气规则），下方给判异明细
- 柏拉图：双 Y 轴、80% 分界线（示例数据里"毛刺+尺寸超差+划伤"三类占 81.31%）
- 报表导出：7 项逐项勾选，Excel 导出时图表内嵌进 `[图表]` sheet
- 项目库：IndexedDB 持久化，刷新自动恢复
- **可选 AI**：接任意 OpenAI 兼容服务做解读；**不配即为纯离线工具，功能一样不少**

**工程质量信号（很扎实）：**

- README 里的 6 张截图是 `.probe/p13-readme-shots.mjs` 在**真 Chrome** 里自动拍的，可复现
- CI badge + `npm test` + `npm run verify`（typecheck + lint + 单测）
- README 专门写了一段解释为什么旧工具"Pp 恒等于 Cp"是错的

> **判读**：这是本次调研里**"质量意识"最强的小工具**。它没有 LLM 也能活，AI 只是"可选解读"——这个产品判断非常对：一线质量员要的是"数字对、能导出、不外泄"，不是"AI 帮我写作文"。它的"单文件离线"策略对工厂内网环境是绝杀。

### 3.4 `Novushisi/medical-slide-spec` —— 医院品管圈演示的"证据门禁"方案

| 项 | 值 |
|---|---|
| 地址 | https://github.com/Novushisi/medical-slide-spec |
| 星标 / 许可 | 4 / MIT |
| 形态 | Codex Skill（医疗护理演示逐页内容规格） |

**适用场景明确列出：护理查房、教学查房、护理个案、`PDCA`、`品管圈`、`RCA`、患者宣教、科研开题、答辩、述职竞聘。**

**它的核心机制是"证据分级 + 内容锁"：**

- 区分四类内容：客户事实 / 建议补全 / 待确认项 / 模拟内容 —— **不许混淆**
- **E0—E3 证据分级**：E0 无来源，E1 一般文献，E2 当次权威来源（需时效核验），E3 核心主张必须映射到指南/DOI/PMID/官方链接
- **高风险医学主张门禁**：E3 级主张没有权威映射就不许进 PPT
- `content_lock_id` 保证"客户终版"和"视觉 AI 投喂版"两版可见内容同源
- 对患者身份信息强制去标识化

> **判读**：这是"医院品管圈"场景最值得借鉴的设计。品管圈在医院是**评审导向**的，评委最爱问的一句话是"你这个数据哪来的"。`medical-slide-spec` 用"证据等级 + 内容锁"直接回答了这个问题。它的方法论价值 > 代码价值。

### 3.5 `duyunzhoudyz/dyz-gongwen-skills`（815★）—— 借道"公文"进入医院 PDCA

| 项 | 值 |
|---|---|
| 地址 | https://github.com/duyunzhoudyz/dyz-gongwen-skills |
| 星标 / 许可 | **815** / NOASSERTION（自定义） |
| 形态 | 公文写作 Agent Skill 集（含 `gongwen-hospital` 医院版） |

名义上是"AI 公文写作助手（防编造、守保密、GB/T 9704 一键排版）"，但它的 `gongwen-hospital` skill 里藏着一份**极其专业的 RCA / PDCA 写作规范**，是本次调研中方法论密度最高的中文材料之一：

- 引用《医疗质量管理办法》（国家卫生计生委令第 10 号）第三十四条、第四十七条；《患者安全专项行动方案（2023—2025年）》（国卫办医政发〔2023〕13 号）第十条、第十二条及附件 2
- 明确边界："RCA 不是事故责任认定，也不是医疗纠纷处理意见"
- **原因三层分解**：直接原因 / 促成因素（人员、任务与流程、设备与信息系统、环境、沟通与交接、组织与管理六类）/ 根本原因（系统层面 1–3 条）
- **改进措施强度分级**（参考 RCA² 思路）：
  - **强**：改环境/设备/流程本身，让错误难以发生（强制拦截、统一设备、简化流程）
  - **中**：降低对记忆与注意力的依赖（增人手、调排班、系统提醒、核查表）
  - **弱**：靠人自觉（双人核对、警示标识、修订制度、发通知、培训）
- 写作红线："个人表现写成可观察的行为，不写品质评价"——写"护理记录中 2 时无约束评估记录"，不写"责任心不强"
- 有 `evals/` 目录存实际产出（"降低术后肺部感染 PDCA"、"三季度医疗质量分析报告"等）

> **判读**：815★ 说明**中文质量写作的真实需求量级**——不是"生成图表"，而是"写出一份不会被质控科打回的文书"。这份 skill 里的"措施强度分级"和"三层原因分解"，比任何 QCC 软件的功能列表都更接近品管圈的本质。

### 3.6 `chrisliuu345/AKIA-local` —— 最完整的质量工程桌面软件（可惜 AI 只是插件）

| 项 | 值 |
|---|---|
| 地址 | https://github.com/chrisliuu345/AKIA-local |
| 星标 | 0（但 **549 次提交**，v4.6.4） |
| 语言 / 许可 | Python / Apache-2.0 |
| 形态 | 本地优先桌面应用（Linux AppImage / Windows exe / 源码） |

**能力覆盖（几乎把质量工程全吃下）：**

- **IE 工具**：时间研究、OEE、SMED、TPM、线平衡、价值流图、技能约束排班
- **统计与质量**：SPC、过程能力、MSA、假设检验、DOE、可靠性、时间序列与预测
- **改善闭环**：改善案例、标准版本记录、**证据账本**、8D、FMEA、控制计划、PPAP
- **实时分析**：实时 SPC、设备数据接入、产线拓扑、告警与看板
- **可复现分析**：已知值测试、抽样决定记录、判定凭证、可独立校验的**证据包**
- **可选 AI 助手**：本地 Ollama 或自带 OpenAI 兼容服务，密钥加密，**本地模型调用审计**，在线评分仅"供人工复核"
- **开放接口**：无界面 CLI/SDK、**本地 MCP stdio 服务**、版本化规则包、插件脚手架

> **判读**：这是 GitHub 上**质量工程功能面最全**的开源实现，549 次提交说明是真项目。但它的定位是"本地优先的分析工具"，AI 是可选附件而非核心。它的 `.qda` 证据包设计（带版本号 + 逐项哈希）值得直接借鉴——这正是 QCC 评审最需要的"可追溯"。

### 3.7 长尾与噪音（必须点名，避免误判）

| 仓库 | 星 | 真相 |
|---|---|---|
| `huahongzheng/QCC` | 0 | 描述"QC小组项目管理信息系统"，仓库 **0KB，空壳** |
| `Squama/Master` | 1 | 早年 Java 系统，有 `QCproject.java` + `Qc/addIndex.html`，字段含"要因确认"，但 2022 年后停更，与 AI 无关 |
| `jegunk/QCC-Precision-Stopwatch` | 0 | QCC 发表**计时器**（印尼），纯工具 |
| `panjibudiman111-hub/QCC_Monitoring` | 0 | "Quality_Control_Circle" 命名的监控小项目 |
| `keepgrowing27/Quality-Control-Circle` | 0 | 只有一篇推广文章 |
| `duhu2000/qcc-agent-cli` / `zhanglunet/qcc` | 8 / 2 | **企查查** Agent/MCP，与品管圈无关，但会污染搜索结果 |
| `luca-scr/qcc` | 61 | R 语言的 **Quality Control Charts** 包，同缩写不同义 |

---

## 4. L4 方法学 Skill 层：2025–2026 的新物种

这是本次调研中**唯一"有生态感"的一层**。Agent Skill（Claude Skill / Codex Skill / agentskills.io 格式）正在成为质量管理知识的最佳载体——比 SaaS 轻（一个文件夹就能装）、比 prompt 重（能带脚本、模板、校验器）。

### 4.1 `jherrodthomas/automotive-skills-suite`（3312★）—— 质量领域唯一的千星项目

| 项 | 值 |
|---|---|
| 星标 / 许可 | **3312** / MIT |
| 提交 / 贡献者 | 132 / 1 |
| 形态 | 152 个可安装 Claude Skill（**76 builder + 76 reviewer 成对**） |

**覆盖范围（远超"质量"）：**

ISO 26262 功能安全（HARA→FSC→TSC→FMEDA→安全案例）、ISO/SAE 21434 网络安全（TARA→目标→概念→架构→IR 计划）、ISO 21448 SOTIF、**AIAG-VDA 质量（APQP→DFMEA→PFMEA→控制计划→PPAP）**、Automotive SPICE、通信协议（DBC/LDF/ARXML/FlexRay/以太网/K-Matrix）、诊断（UDS/DTC/CDD/ODX/DEM）、AUTOSAR、标定（A2L/DCM）、MBSE（ARCADIA）、SysML、V&V、**持续改善（8D、5-Why、鱼骨图、MSA Gauge R&R、SPC）**。

**它真正的护城河，README 里写得很直白：**

> "The chain is the moat — every downstream skill consumes the upstream skill's xlsx output as a stable file-format contract."
> （链条就是护城河——每个下游 skill 消费上游 skill 的 xlsx 输出，作为稳定的文件格式契约。）

以及：

> "Every artifact-producing skill is paired with a confirmation reviewer. Reviewer outputs include a visual dashboard with KPI tiles, charts, and findings tables."
> （每个产出物的 skill 都配一个确认审查器，审查器输出带 KPI 卡片、图表和问题表的可视化看板。）

**为什么这个设计赢了：**

1. **成对设计**解决了 LLM 自评过宽的问题（生成者和审查者是两个独立 skill）
2. **xlsx 作为契约**解决了"多步流程中状态怎么传"的问题——不靠上下文，靠文件
3. **reviewer 出看板**让"审查结果"本身可交付，符合质量体系的"记录"要求

### 4.2 `RBraga01/Quality-Engineering-Skills`（47★）—— 最"正统"的质量 Skill 包

| 项 | 值 |
|---|---|
| 星标 / 许可 | 47 / MIT |
| 提交 / 贡献者 | 116 / 4（**4 个贡献者，是本次样本里协作最好的质量项目**） |
| 形态 | 23 个 skill + 8 个 agent，兼容 agentskills.io / Claude Code / Codex / Cursor / Gemini CLI |
| 安装 | `npx skills add RBraga01/Quality-Engineering-Skills` |

**覆盖矩阵（每个 skill 都映射到标准条款）：**

| 域 | Skills | 标准 |
|---|---|---|
| 问题解决 | 8D(D0–D8)、5-Why、鱼骨图、Is/Is-Not、PDCA、DMAIC、**双归零** | ISO 9001 §10.2、IATF 16949 §10.2.3、**GB/T 29076—2021** |
| 风险分析 | PFMEA、DFMEA、Action Priority(AP) | AIAG-VDA FMEA 2019、IATF 16949 §8.3 |
| 策划 | PPAP(5 级/18 元素)、APQP(5 阶段)、控制计划、DVP&R | AIAG PPAP 4th、IATF 16949 §8.3.4 |
| 测量 | MSA / Gauge R&R、SPC / 控制图 | AIAG MSA 4th、AIAG SPC 2nd |
| 文档 | NCR、CAR、8D 客户报告 | ISO 9001 §7.5、§8.7、§10.2 |
| 审核 | ISO 9001 内审、IATF 16949 补充、VDA 6.3 | ISO 9001:2015、IATF 16949:2016、VDA 6.3 2023 |
| 供应商 | SCAR、纠正措施升级 | ISO 9001 §8.4、IATF 16949 §8.4.1 |

**8 个 agent 里最值得看的三个：**

- `/8d-coach` —— 走完 D0→D8，**拒绝"人为失误"作为根因**（除非有系统性分析），D4 前必须先验证围堵措施，D7 必须检查预防措施更新
- `/rca-facilitator` —— 结构化 5-Why，**每一层"为什么"都要求证据**，区分症状性 vs 系统性根因，检测循环论证，产出可逆的 Why 链
- `/fmea-reviewer` —— 按 AIAG-VDA 2019 审已有 PFMEA/DFMEA，输出缺口报告：缺失失效模式、错误的 AP 评级、未处理的 H-AP 项、缺失的特殊特性

> **判读**：`双归零（GB/T 29076—2021）` 的出现说明作者懂中国航天/军工质量体系（技术归零五条 + 管理归零五条）。这是本土化深度的信号。4 个贡献者也说明它有真实协作。

### 4.3 中文质量 Skill 的三个样本

| 项目 | 星 | 能力 | 判断 |
|---|---|---|---|
| `cy556-like/automotive-quality-engineer-skills` | 6 | 五大工具 + 8D/VDA 6.3/DMAIC，**输出 Word/PPT/Excel 三件套**（`qi-docx`/`qi-pptx`/`qi-xlsx`），带 `spc_analysis.py`、`fmea_risk_eval.py`、`ppap_checklist.py` 等 CLI 脚本 | 最"实用主义"：不追求 Agent 智能，追求"一条命令出交付物"。但**完全没覆盖 QC 七手法和品管圈** |
| `duding-engicool/skill-qc-tools` | 3 | 柏拉图、鱼骨图、直方图、控制图、散布图自动生成，**明确标注"覆盖 QC 七大手法"** | 中文生态里**唯一直接对标七手法**的 skill，但体量小、无 License |
| `dungnotnull/industrial-qa-qc-audit-agent-skill` | 4 | 工业 QA/QC 过程审核，用 Six Sigma / Lean / SPC 与国际标准打分 | 审核向，偏"评估"不偏"生产" |

同一作者 `duding-engicool` 还有 `skill-apqp-project-manager`（APQP 五阶段 + FMEA/PPAP/控制计划文档生成 + 甘特图）和 `skill-csr-analyzer`（判断文档是否属于 IATF 16949 客户特定要求）——**这是本次样本里唯一在"按质量方法论拆 skill"的中文作者**，思路值得关注。

### 4.4 其他值得记一笔的 Skill

| 项目 | 星 | 亮点 |
|---|---|---|
| `cleverlab-ai/iso-17025-skill` | 13 | ISO/IEC 17025:2017 实验室认可专家顾问，支持 30+ 工具 |
| `robustagile/six-sigma-in-r-skill` | 12 | 教 Agent 写**正确的 R 代码**做六西格玛/SPC（控制图、能力分析），避免 LLM 瞎编统计函数 |
| `oliviakey-oliviasmuse/control-plan-builder` | 0 | 从 PFMEA 失效模式逐行构建控制计划，含 SPC 分析、控制限计算、反应计划 |
| `walterkken/popular-process-skills` | 0 | GTD/OKR/**PDSA**/**DMAIC**/设计思维/精益创业/OODA 的通用流程 skill |
| `hypergraphdev/abs-skills` | 2 | Lean 与运营卓越方法，带来源引用与排程计划 |
| `imnoo-team/quality-control-plan-mcp` | 1 | **从工程图纸 PDF 抽公差/配合/螺纹/GD&T，生成控制计划与检验报告**（MCP 形态，Dockerfile 分发） |

---

## 5. L5 流程 Copilot：8D / RCA / CAPA / 供应商质量

这是"AI + 质量"最热闹的细分，也是最同质化的。样本里 20+ 个项目，骨架几乎完全一样。

### 5.1 标准骨架（已被验证的架构）

```
用户描述问题（自然语言 / 上传 PDF）
        ↓
① 查询改写          LLM 生成 3 个替代表述
        ↓
② 语义检索          向量库 top-K（历史 8D / NCR / PFMEA / 控制计划 / PPAP / 客诉 / 工程偏差 / 作业指导书）
        ↓
③ 重排              cross-encoder（如 bge-reranker-v2-m3）取 top-5
        ↓
④ 生成              大模型基于检索结果起草
        ↓
⑤ groundedness 检查  小模型剥离无依据的断言
        ↓
⑥ 人工确认门        工程师审核后才入库/发出
```

### 5.2 代表项目对比

| 项目 | 星 | 提交 | 亮点 | 短板 |
|---|---|---|---|---|
| `kolmag/8d-expert-workbench` | 2 | — | **双标签联动**：8D 表单每个 D 都有「AI Suggest」和「↗ Ask Expert」，后者把当前报告状态拼成问题、自动切标签。14 份 CAPA/8D 知识库文档。**生成器与审查器用不同尺寸模型**（gpt-oss-120b 生成 / gpt-oss-20b 审计）以降低自我宽容 | 单机 Streamlit，无多用户 |
| `orcunku/supplier-quality-8d-copilot` | 0 | **4** | 65 份**合成**汽车质量文档（15 个历史 8D、10 NCR、8 PPAP、5 PFMEA、5 控制计划、10 客诉、5 工程偏差、7 作业指导书），构造了"压接/HV 连接/超声焊/密封/端子保持力"的关联失效网；有 Streamlit 在线 Demo | 4 次提交 = demo 级；无真实数据 |
| `mickemora/supplier-quality-copilot` | 0 | — | 航空航天与国防场景：NCR/8D 抽取、**重复根因检测**、带引用的 SCAR 起草 | 无 License，demo |
| `joel5638/Recalltrace-ai` | 0 | — | LangGraph + 证据检索 + agent 工作流 + **human approval** 的对话式供应商质量调查 | 无文档深度 |
| `eakarsu/ai-supplier-quality-capa-8d` | 0 | — | CAPA + 8D 合体 | 66KB，空壳感强 |
| `aken1023/panjit-8d-report-ai` | 1 | — | 强茂半导体真实场景，DeepSeek API + Flask 的 8D 品质报告智慧问答 | 13KB 单页 |
| `LouisBoBo/pythonProject_8D_Report` | 2 | — | 中文 8D 报告生成 | 无说明 |
| `Laurenceku2026/AI-FA_8D` | 1 | — | 失效分析（FA）+ 8D 报告双输出 | 无说明 |
| `saikrish-code/Root-Cause-Analysis` | 0 | — | 上传 PDF/粘贴事件 → 抽取数据 → 跑 5Why，**质量调查专用** | 24MB，可能含大文件 |
| `Sviless/ai-root-cause-coach` | 0 | — | 本地优先 Lean RCA：5Whys + 鱼骨 + 原因/证据矩阵 + 对策 | 单人 Streamlit |
| `quality-pixel/Rootcause-analysis*` | 0 | — | 鱼骨 + 5Whys + 结构化报告，同作者 4 个重复仓库 | 碎片化 |

### 5.3 FMEA 的 AI 化：一条被忽略的方法论断层

| 项目 | 星 | 做法 | 问题 |
|---|---|---|---|
| `YuchenXia/LLMRiskAnalyzer` | **41** | LLM 辅助 FMEA（JS，2024 年创建） | 2026-06-18 后停更，RPN 导向 |
| `lukasbahr/kg-rag-fmea` | **33** | 知识图谱 + RAG 做 FMEA | 仅 23KB，2025-03 停更 |
| `dromation/open-fmea` | **47** | 开源 FMEA 工具（Python/GPL-3.0） | 传统工具，非 AI |
| `Abinash009/iso26262-agent` | 18 | HARA/FMEA/安全需求生成，RAG+LLM+**MCP** | 功能安全域，非制造质量 |
| `MasrourTawfik/DFMEA-LLM-Enhanced` | 3 | 学术项目：LLM 融入 DFMEA 风险分析流程 | 只有文档，16MB |
| `Mohamed-Elsafty23/LLM-FMEA-Analyzer` | 0 | 从**非结构化客户评论**生成 FMEA 风险表，含 S/O/D + RPN + 柏拉图 | 输入源很聪明（VOC→FMEA） |
| `Amirkhaji/fmea-automation-using-LLM` | 0 | 从文档抽组件 → 分配 S/O/D | 基础 |
| `ranjith-24-prog/fmea_ppr_validation` | 0 | **LLM+RAG 复用历史 FMEA 分析 + 专家复核**（IEEE ETFA 2026） | 学术，质量最高 |
| `aoyexiaoqi/fmeaflow` | 0 | **PFMEA 与控制计划一致性检查** | 痛点极准，但体量小 |
| `genkidesu7/agentic-star-...-pfmea-to-control-plan` | 0 | 上传 PFMEA + 控制计划 → agent 解析比对 | 同类 |

> **关键洞察**：绝大多数 FMEA 项目还在用 **RPN**，而 AIAG-VDA FMEA 2019 已经用 **Action Priority (AP)** 表替代 RPN。`YuchenXia/LLMRiskAnalyzer`（41★，该领域最高星）就是 RPN 导向——**这个领域星标最高的项目，方法论上是过时的**。这说明：质量 AI 项目的 star 数与方法论正确性**负相关**（越通俗越多人 star）。

### 5.4 制药 / 医疗器械：模板化复制的重灾区

样本里至少 6 个高度雷同的项目：

- `07pavan/Pharmaceutical_AI` —— "企业级医疗器械与制药 QMS，LangGraph 多智能体"
- `rizzit17/pharmassist` —— "制药 QMS，多节点 LangGraph 受理 copilot"
- `nick-devart/Ai_Customer_Care` —— "制药 QMS 客诉分析，React + FastAPI + LangGraph"
- `dark-abhaypydev/pharma-complaint-ai-agent` —— "LangGraph + FastAPI + Groq + React + SQLAlchemy"
- `PratikPatil2345/Pharma-Customer-Complaint-Management-System` —— "API & FDF 客诉管理"
- `TMBIA-Tmti/AI-QMS`（4★）—— ISO 13485，文档控制 + OCR + 防篡改审计链

前五个几乎可以确认是**同一课程/教程的变体**（技术栈完全一致、star 数为 0-1、无 License）。唯一有真实设计感的是 `TMBIA-Tmti/AI-QMS` 的"防篡改审计链"。

---

## 6. L3 单点工具层：七手法与可视化

| 类别 | 项目 | 星 | 说明 |
|---|---|---|---|
| 鱼骨图 | `hophiphip/react-fishbone` | 9 | React 组件（MIT） |
| 鱼骨图 | `JetBrains-Research/fishbone` | 4 | JetBrains 研究院，构图与可视化 |
| 鱼骨图 | `expectedparrot/ishikawa` | 0 | **agent-friendly Python CLI**，结构化因果分析（EDA 团队出品，设计规范） |
| 鱼骨图 | `alfredang/fishbone` | 1 | 面向六西格玛学习者 |
| 鱼骨图 | `Pakawat-Dev/Root_Cause_Analysis_Langgraph` | 0 | LangGraph 驱动的 AI 鱼骨图 |
| 鱼骨图 | `joshuagodwin/Ai-Ishikawa-Diagram-Builder` | 0 | AI 辅助构建 |
| 鱼骨图 | `fjgonzalezmgt/ishikawa` | 0 | 鱼骨 + RCA 工具集 |
| 鱼骨图 | `SouravNeatC/fishbone-analysis-visual-powerbi` | 0 | Power BI 自定义视觉对象（D3） |
| 柏拉图 | `Hulk-Zhao/Hogo-QA-tool` | 2 | 见 §3.3，PQ 双轴 + 80% 线 |
| 柏拉图 | `duding-engicool/skill-qc-tools` | 3 | Claude Skill，七手法合集 |
| 控制图 | `KensoBI/spc-chart` | 13 | Grafana 面板插件，Xbar-R/Xbar-S/XmR |
| 控制图 | `petermgates/py-qcc` | 7 | Python 版 R `qcc` 包（GPL-3.0） |
| 控制图 | `bertanucar/shewhart` | 3 | 纯 SPC 库，**对标已发表参考数据做过验证** |
| 控制图 | `luca-scr/qcc` | **61** | R 语言经典，QCC 统计口径的"事实标准" |

> **判读**：这一层是**最健康的一层**——项目小、职责单一、有测试、有 License。但它们和 AI 基本无关，是"AI 应该去调用的工具"，而不是"AI 产品"。`expectedparrot/ishikawa` 的 "agent-friendly CLI" 定位是正确方向。

---

## 7. L2 统计内核层：AI 不可替代的部分

| 项目 | 星 | 提交 | 硬核点 |
|---|---|---|---|
| `M1ndSmith/ASPC` | 15 | 35 | **Phase I 建立并冻结控制限 → Phase II 用冻结限评估新数据**；9 种图（I-MR/Xbar-R/Xbar-S/P/NP/C/U/EWMA/CUSUM）；MSA 全项（ANOVA/极差 Gage R&R、偏倚、线性、稳定性、NDC、10:1 分辨率门）；能力分析参数/变换/非参三路；**ok/warn/stop 三级闸门 + 10 项上线检查清单**；FastAPI + CLI + JWT + WebSocket 实时告警 + SSE 回放；Docker Compose 全家桶（Redpanda/Mosquitto/TimescaleDB/Redis） |
| `Siddardth7/quality-platform` | 4 | **511** | **2502 个测试通过、核心 100% 覆盖、SPC ≥95%**；FMEA / SPC / 控制计划 / MSA 共享一个 typed core（`quality_core`）；**MCP server + Agent Skills 双通道**；真半导体数据（SECOM）验证；关键设计：**SPC 证据只"提议"发生度评分，绝不自动改写** |
| `saturnis-io/cassini` | 5 | — | 开源 SPC 平台：实时控制图、能力分析、Gage R&R、FAI 管理（29MB） |
| `DailyDana/process-capability-analyzer` | 5 | — | Xbar-R/Xbar-S/I-MR + 西方电气与 Nelson 规则 + Cpk/Ppk + Gage R&R |
| `luca-scr/qcc` | 61 | — | R 经典包，控制图 + 能力分析 + 帕累托 + 因果图 |
| `petermgates/py-qcc` | 7 | — | Python 移植（GPL-3.0，商用需注意） |

**两个关键设计值得直接拿：**

1. **`ASPC` 的 Phase I/II 分离**：先建立并**冻结**控制限（带门禁），再用冻结限做在线判异。这是工业 SPC 的正统做法，但绝大多数"AI SPC"项目直接对全量数据算限——统计上是错的（用未来数据定义基线）。
2. **`quality-platform` 的"AI 不许改数字"**：SPC 证据只能"提议"FMEA 的发生度评分，必须人工确认。它在 README 里明确写了 "The last leg is deliberately not automatic"。这是所有质量 AI 产品都该抄的一条铁律。

---

## 8. L1 数据与平台层：QMS / MES / MCP

### 8.1 开源 QMS

| 项目 | 星 | 说明 |
|---|---|---|
| `C-realize/OpenQMS` | 32 | OpenQMS.net，轻量云原生 QMS（JS/AGPL-3.0）。**AGPL 会传染**，商用需谨慎 |
| `TMBIA-Tmti/AI-QMS` | 4 | 医疗器械 ISO 13485 QMS：智能文档控制、OCR、**防篡改审计链** |
| `jonaesantos/odoo-qms-iso9001` | 30 | Odoo 上的 ISO 9001 QMS 模块 |
| `evolunis/openQMS` | 11 | ISO 13485 QMS |
| `esclaudio/paraiso-lite` | 6 | ISO 9001:2015 QMS 软件 |
| `Erwinya/qms-ncr-service` + `ncr-console` | 1 + 0 | NCR 的 REST API + 浏览器控制台（MIT，小而干净） |

### 8.2 体系审核的 AI 化

| 项目 | 星 | 做法 |
|---|---|---|
| `kolmag/auditor-expert` | 1 | ISO 9001 / IATF 16949 / AS9100D 的 RAG 审核专家问答，**610 题评测集、8 模型横评**（同类里唯一做了严肃评测的） |
| `dbaklesis/DigiAuditor` | 0 | ISO 9001 & ISO 14001 的数字审核员 |
| `DesarrollosLAM/trinorma-ai-auditor` | 0 | RAG 架构的整合管理体系审核 copilot（西语） |
| `SouleymaneDiallo04/QMS_Chatbot` | 1 | ISO 9001/IATF 16949 聊天机器人：语义检索 + 审核清单生成 + 分析 |
| `karlosmahecha/ISO-9001` | 0 | 最早的"AI 做 ISO 9001 审核"想法之一（2024-08，未实现） |
| `cleverlab-ai/iso-17025-skill` | 13 | ISO 17025 实验室认可 skill |

### 8.3 MCP 层：刚开始，但是明确趋势

| 项目 | 星 | 说明 |
|---|---|---|
| `imnoo-team/quality-control-plan-mcp` | 1 | 工程图纸 PDF → 公差/配合/螺纹/GD&T → 控制计划 + 检验报告。**Docker 分发**，MIT |
| `zavora-ai/mcp-qms` | 1 | Rust 实现 QMS MCP：供应商、批次与 QC 放行、检验、NCR、CAPA、投诉、HACCP（食品饮料） |
| `alexcroston79/1factory-mcp` | 0 | 商业 QMS（1Factory API v24.31）的 MCP 封装，19 个工具，SSE 传输 |
| `factorysemantics/factorysemantics-mes` | 17 | **agent-native MES**：OPC UA 输入、真实 OEE 输出、ERPNext 连接器、MCP 接口 |
| `chrisliuu345/AKIA-local` | 0 | 内置本地 MCP stdio 服务（见 §3.6） |

**为什么 MCP 对质量管理特别关键：** 质量数据天生在多个孤岛（MES/ERP/QMS/检验设备/LIMS），而 LLM 最不擅长的就是"跨系统取数"。MCP 把"取数"标准化后，Agent 才可能真正做根因分析而不是编故事。`1factory` 这种"给商业 QMS 套 MCP"的做法，可能是未来 2 年最务实的一条路。

### 8.4 一个被低估的相邻项：工业视觉质检 Agent

严格说这不属于 QCC（品管圈），但属于"质量管理圈"的 AI 化，且是**唯一有真实生产部署**的方向：

| 项目 | 星 | 说明 |
|---|---|---|
| `peige-guo/Multimodal_Industrial_Inspection_Agent` | 7 | 多模态工业质检：视觉 + 标准 RAG + 严重度判定 + 结构化报告 |
| `ITU-AI-ML-in-5G-Challenge/wearedge-opea-manufacturing` | 1 | OPEA 制造 agent 套件（维护/质检/换型/作业指导），Docker 可跑 |
| `arslan-kursad/aiqs-agent` | 0 | 工业视觉质检的 **agentic 裁决层**：成本感知、校准、可弃权决策 |
| `chq20010205-arch/nana-quality-inspection-agent` | 1 | 现场巡视问题 → 自动匹配规章条款 → 生成整改通知书 |
| `SKby0/quality-inspection-review-agent` | 1 | 质检报告审核 |
| `xkkkkkkm/e-commerce-copy-quality-inspection-agent` | 9 | 电商文案质检（规则兜底 + 租户隔离 + 可审计发布决策） |

> **判读**：视觉质检是"AI + 质量"里唯一天然适合多模态大模型的场景，也是唯一能直接算 ROI 的场景（替代目检人力）。但它和 QCC 是两套语言——QCC 关心"为什么会有不良"，视觉质检关心"这一件是不是不良"。

---

## 9. 能力矩阵：QCC 十一阶段 × 项目覆盖度

这是本次调研最核心的一张表。把标准的品管圈十一阶段拆开，逐个看"有没有项目真正覆盖"。

> 覆盖度定义：**强** = 有专门实现且质量可用；**中** = 有实现但浅/间接；**弱** = 只有字段或模板痕迹；**空白** = 无任何项目覆盖。

| # | QCC 阶段 | 关键方法/产物 | 有覆盖的项目 | 覆盖度 |
|---|---|---|---|---|
| 1 | 圈介绍 / 圈能力 | 圈名、圈徽、圈员分工、能力雷达、活动计划 | `skill-stock`（圈档案页，明确要求"建立可信度"而非装饰性名单） | **弱** |
| 2 | 主题选定 | 头脑风暴、亲和图、检查表、评价矩阵、SMART | `QCmaker`（SMART 评估 + 知识库）、`skill-stock`（三页强制方法） | **中** |
| 3 | 现状调查 | SIPOC、柏拉图、子流程图、层别法、检查表 | `skill-stock`（SIPOC + 柏拉图 + 子流程）、`Hogo-QA-tool`（柏拉图）、`skill-qc-tools` | **中** |
| 4 | 目标设定 | 基线、目标值、设定依据、可行性分析 | `QCmaker`、`skill-stock`（metric/baseline/target/rationale 四要素） | **中** |
| 5 | 原因分析 | 鱼骨图、系统图、关联图、5Why | `QCmaker`（多智能体研讨）、`skill-qc-tools`、`AKIA-local`、十余个 RCA 项目 | **强** |
| 6 | 要因确认 | 矩阵图、散布图、现场验证、**要因 vs 非要因判定** | `skill-stock`（矩阵图 + 根因验证页）、`dyz-gongwen`（语料含"要因确认"）、`Squama/Master`（字段） | **弱** |
| 7 | 对策拟定 | 5W1H、对策评价矩阵、防呆设计 | `skill-stock`（5W 页）、`RBraga01`（控制计划/反应计划） | **弱** |
| 8 | 对策实施 | 实施计划、甘特图、过程监控、异常处置 | `skill-apqp-project-manager`（甘特 + 阶段）、`cy556-like`（文档生成） | **很弱** |
| 9 | 效果确认 | 前后对比、柏拉图对比、**假设检验**、经济效益 | `Hogo-QA-tool`（Cpk/控制图）、`ASPC`、`quality-platform`、`skill-stock`（before/after 页） | **中** |
| 10 | 标准化 | 作业标准、图纸/工艺修订、**防反弹机制** | `skill-stock`（标准化清单） | **弱** |
| 11 | 检讨与下一步 | 残留问题、下一圈主题、横向展开 | 无 | **空白** |

**这张表读出来的三件事：**

1. **曲线是"中间高、两头低"**：第 5 阶段（原因分析）拥挤到十几家在做，第 6/7/8/10/11 阶段几乎无人问津。这说明整个生态的注意力都集中在"AI 最擅长的那一步"（生成分析），而绕开了"AI 最不擅长的那几步"（现场验证、执行、固化）。
2. **"要因确认"是最大的方法论断点**。品管圈评审里最容易被挑刺的就是"你怎么证明这个是要因而不是拍脑袋"——需要矩阵图打分、散布图相关性、现场验证三件套。全 GitHub 只有一个 0★ 项目做了页面级实现。
3. **"效果确认"被简化成了"画个对比柱状图"**。QCC 教材要求的是"柏拉图前后对比 + 目标达成率 + 经济效益核算 + （必要时）假设检验"。除 `Hogo-QA-tool` 和 `ASPC` 有真正的统计能力外，其余都是装饰。

---

## 10. 七个关键洞察

### 洞察 1：QCC 在 GitHub 上"术语塌陷"，可发现性接近于零

`qcc in:name` → 1621 个仓库，前 20 名全部是无关项目。
`"quality control circle"` → 全站 3 个。
`topic:qcc` → 13 个，0 个是品管圈。

**含义**：任何想找这类工具的人（包括 AI 搜索、投资机构、采购）都会被导流到企查查/量子计算。这既是坏消息（无社区、无讨论、无 issue 生态），也是好消息（**没有既有玩家把守，冷启动不需要打败谁**）。

**对策含义**：如果要在这个赛道做产品，**SEO/可发现性本身就是核心竞争力之一**。仓库名、README 首段、topic 都要主动做歧义消解（例如 `topic:quality-control-circle`、`topic:qcc-quality-circle`）。

### 洞察 2：真正的竞争不在"生成"，而在"合规"

对比两个项目：

- `QCmaker`（8★）：把 QCC 做成"AI 帮你写报告"，工程很扎实，但方法学是松的。
- `skill-stock`（0★）：把 QCC 做成"11 类强制页面 + 合规审计脚本 + 证据契约"，工程很粗糙，但方法学是紧的。

**在真实评审场景里，后者赢。** 因为 QCC 的产出物是要被评委按方法学打分的——评委不会因为你 PPT 好看给分，但会因为"你没有做要因确认"扣分。`skill-stock` 的 `check_qcc_method_compliance.py` 本质上是一个"评委的机器替身"。

**含义**：QCC AI 产品的核心资产不是 prompt，而是**可执行的评分规则**。

### 洞察 3：生态重心已从"应用"迁移到"Skill 包"

时间线证据：

- 2025 年及以前：Web 应用 / 桌面工具（`AKIA-local`、`OpenQMS`、`open-fmea`）
- 2026 年上半年：单点 AI 工具（`LLMRiskAnalyzer`、`ASPC`、`Hogo-QA-tool`）
- 2026 年下半年：**Agent Skill 包爆发**（`automotive-skills-suite` 3312★、`Quality-Engineering-Skills` 47★、`skill-qc-tools`、`skill-apqp-*`、`iso-17025-skill`、`control-plan-builder`…）

**为什么是 Skill 而不是 SaaS：**

1. 质量知识是**企业私有 + 强合规**的，SaaS 卖不动，Skill 可以本地跑
2. 质量方法论是**结构化、可枚举**的（8D 有 9 个 D，FMEA 有 7 步，QCC 有 11 阶段），天然适合写成"带检查清单的指令"
3. Skill 能带**脚本和模板**（python-pptx、xlsx 生成器、校验器），比纯 prompt 强得多
4. 分发极轻（`npx skills add`、拷一个文件夹）

**含义**：qcc-copilot 如果只做 Web 应用，会错过整个分发红利；如果只做 Skill，会失去数据采集与流程能力。**最优解是"Skill 做方法学内核 + 轻应用做数据与交付"**。

### 洞察 4：质量 AI 的架构已经收敛，同质化是最大的机会

所有 8D/CAPA 项目都是：`语义检索 → 表单引导 → 生成 → groundedness 检查 → 人工确认`。

**同质化意味着两件事：**（a）这条路线已被验证可行，不需要再摸索；（b）差异化必须来自别处——**方法论深度、数据闭环、交付物合规、场景纵深**。

`kolmag/8d-expert-workbench` 提供了一个差异化样本：**用不同尺寸的模型做生成和审计**（120b 生成 / 20b 审计），因为"让同一个模型审自己会过于宽容"。这是很聪明的工程直觉，但几乎没有别的项目这么做。

### 洞察 5：统计学正确性是护城河，AI 只能做"解读"

三个证据：

- `Hogo-QA-tool` 在 README 里专门解释"为什么旧工具的 Pp 恒等于 Cp 是错的"（Cp/Cpk 用组内 σ，Pp/Ppk 用整体 σ）
- `ASPC` 明确写 "formula fidelity ≠ Minitab/JMP parity"，并给出可复现的 accuracy benchmark
- `quality-platform` 规定 "SPC evidence **proposes** an occurrence rating, it never rewrites one"

**含义**：在质量场景里，LLM 的正确位置是"解释数字、生成文字、检索历史"，而**不是"计算数字、判定合格、决定处置"**。任何让 LLM 算 Cpk 的产品都会在第一次评审时翻车。

### 洞察 6：中国场景是"双轨制"，两套方法论不通用

| | 制造业轨道 | 医疗轨道 |
|---|---|---|
| 方法论 | IATF 16949 + AIAG-VDA 五大工具 + 8D + 双归零(GB/T 29076) | PDCA / RCA / 品管圈 + 《医疗质量管理办法》+ 患者安全专项行动 |
| 交付物 | xlsx 表（FMEA/控制计划/PPAP）+ 8D 报告 | Word 报告 + PPT 汇报 + 质控指标 |
| 评审方 | 客户 SQE / 第三方认证机构 | 院内质控科 / 卫健委 / 品管圈竞赛评委 |
| 代表项目 | `RBraga01`、`cy556-like`、`skill-apqp` | `dyz-gongwen-skills`(815★)、`medical-slide-spec` |
| 用户画像 | 质量工程师（会用 Excel，能接受工具） | 护士/科室质控员（不会用 CLI，要"填表就能出"） |

**含义**：一个产品想同时服务两条轨道，几乎必然失败。`QCmaker` 的困境就在这里——它做了通用的"LLM 应用骨架"，但没有为任何一条轨道做深。

### 洞察 7：项目生命周期极短，绝大多数是"作品集/竞赛/hackathon 产物"

统计规律（69 个样本）：

- **星标中位数 = 1**，均值被 `automotive-skills-suite`(3312) 和 `dyz-gongwen`(815) 拉高
- **超过 50% 的项目 ≤ 10 次提交**
- **48%（33/69）无 License**（无法商用，法律风险）
- **约 30% 无 README 或只有一句话描述**
- 真正持续维护（>100 commits）的只有 4 个：`AKIA-local`(549)、`quality-platform`(511)、`automotive-skills-suite`(132)、`Quality-Engineering-Skills`(116)

**含义**：这个赛道的"技术供给"极度碎片化。任何认真做产品化的团队，都有机会在 6 个月内做到"GitHub 上最完整的 QCC AI 实现"——门槛低得惊人。

---

## 11. 空白地带与机会窗口

按"需求真实性 × 实现难度 × 竞争强度"排序：

### 🟢 高价值空白（需求真、几乎无人做、难度可控）

**① QCC 十一阶段状态机 + 产物契约**
现状：`skill-stock` 只做 PPT 生成，没有流程引擎；`QCmaker` 有五步但没有方法论约束。
机会：把 11 个阶段做成**显式状态机**，每阶段定义"输入契约 / 输出产物 / 校验规则 / 门禁条件"。阶段未通过校验就不许进入下一阶段。这是把"评审逻辑"前置到"生产过程"。

**② 要因确认的可计算化**
现状：全 GitHub 只有一个 0★ 项目做了页面级实现。
机会：矩阵图打分（相关性 × 频率 × 可检测性）+ 散布图相关系数 + 现场验证记录三者联动，自动判定"该原因是否构成要因"，并输出可辩护的判定依据。这是 QCC 评审最容易被挑刺的地方。

**③ 证据链 / 数字可追溯**
现状：只有 `skill-stock`（evidence_ids）和 `AKIA-local`（.qda 证据包）做了，且互不相通。
机会：建立"每个数字 → 源文件 + 单元格 + 时间戳 + 采集人"的追溯模型。评委问"这个 12.3% 哪来的"，一键展开。

**④ 评审模拟器（红队评委）**
现状：完全没有。
机会：用另一个模型扮演评委，按《质量管理小组活动准则》评分表逐项打分并提问，输出"预计扣分点 + 建议补强证据"。这是**极强的付费意愿点**——QCC 成果是要参赛评奖的，参赛者最怕的是"不知道评委会问什么"。

**⑤ 效果确认的统计严谨性**
现状：全部项目都停在"画个前后对比柱状图"。
机会：柏拉图前后对比（结构变化而不只是总量变化）、目标达成率、配对 t 检验/卡方、经济效益核算（工时/材料/不良损失三口径）。

### 🟡 中价值空白（需求真、有难度或需场景纵深）

**⑥ 圈能力与人员成长维度** —— QCC 标准页要求"圈员能力雷达图"，全站无人做。可结合培训记录自动生成。
**⑦ 中文 QCC 案例库** —— 历史优秀成果是本场景最高价值的语料，但涉及版权与保密，需要企业内私有化，不适合开源。
**⑧ 移动端 / 极简入口** —— 一线圈员是护士和班组长，不会用 CLI、不会配 API Key。`Hogo-QA-tool` 的"单文件 + 双击"是正确方向。
**⑨ 医院 HIS / 制造 MES 对接** —— 这是真正的护城河，但需要行业资源。
**⑩ 对策实施的过程追踪** —— 从"建议"到"执行"的闭环，需要项目管理能力（甘特、责任人、验证节点）。

### 🔴 不建议碰（已被卷死或价值低）

- **又一个 8D 报告生成器** —— 20+ 个项目，全是 demo，差异化空间为零。
- **又一个 FMEA 表单工具** —— `open-fmea`(47★) 已占位，且传统工具更成熟。
- **通用 RAG 知识库问答** —— 这是 Dify/RAGFlow 的地盘，做不出差异。
- **视觉质检** —— 与 QCC 方法论无关，且需要产线数据。

---

## 12. 对 qcc-copilot 的落地建议

### 12.1 定位建议

> **不要做"AI 帮你写 QCC 报告"，要做"QCC 方法学内核 + 证据链 + 评审对齐"。**

三句话版本：

- 对标 `skill-stock` 的方法学严谨性，但补上**流程引擎**和**数据采集**
- 对标 `QCmaker` 的工程完整度，但补上**方法论约束**和**证据链**
- 对标 `Hogo-QA-tool` 的统计正确性，但补上**全流程覆盖**

### 12.2 建议架构（三层）

```
┌─────────────────────────────────────────────────────────┐
│  Deliverable Compiler   PPT / Word / 看板 / 评审模拟     │
│  · python-pptx 模板引擎（参考 QCmaker）                  │
│  · 版式 lint / 占位符 lint / 渲染回读（参考 skill-stock）│
│  · 评审模拟器（红队评委，全新）                          │
├─────────────────────────────────────────────────────────┤
│  Evidence Ledger   证据账本                              │
│  · 每个数字 → 源文件 + 位置 + 时间 + 采集人              │
│  · evidence_status: verified / missing / inferred        │
│  · 禁止无证据数字进入正式页                              │
├─────────────────────────────────────────────────────────┤
│  Method Kernel   方法学内核（真正的护城河）              │
│  · 11 阶段状态机 + 每阶段产物契约                        │
│  · 12 类方法页的机器可校验定义（柏拉图必须有 80% 线…）   │
│  · 统计内核：Cp/Cpk vs Pp/Ppk、判异规则、假设检验        │
│  · 要因确认判定器（矩阵 + 相关性 + 验证记录）            │
└─────────────────────────────────────────────────────────┘
```

**为什么 Method Kernel 要独立成层：** 它同时是 Web 应用的引擎、Agent Skill 的指令源、评审模拟器的评分表。一份定义，三处消费——这是 `automotive-skills-suite` 用 "xlsx 文件契约" 实现的东西，但 QCC 场景更适合用"结构化 YAML + 校验器"。

### 12.3 可直接借鉴的清单（按价值排序）

| 优先级 | 来源 | 借什么 | 注意 |
|---|---|---|---|
| ⭐⭐⭐ | `zhiwuli0228/skill-stock` | 11 步强制方法链、12 类方法页的视觉规范、6 个审计脚本的设计、`evidence_status: missing → 待补充` 的降级策略 | **无 License，只能参考思想，不能复制代码** |
| ⭐⭐⭐ | `duyunzhoudyz/dyz-gongwen-skills` | 医院 PDCA/RCA 的文书结构、原因三层分解、**改进措施强度分级（强/中/弱）**、写作红线（不写品质评价） | 815★，NOASSERTION，同样需谨慎 |
| ⭐⭐⭐ | `RBraga01/Quality-Engineering-Skills` | 23 个 skill 的条款映射方式、`/8d-coach` 的"拒绝人为失误作根因"规则、**双归零 GB/T 29076** | MIT，可放心参考 |
| ⭐⭐⭐ | `Hulk-Zhao/Hogo-QA-tool` | Cp/Cpk 与 Pp/Ppk 的口径区分、12 条判异准则的开关设计、单文件离线分发 | MIT，可直接看实现 |
| ⭐⭐ | `M1ndSmith/ASPC` | Phase I 冻结限 → Phase II 评估的两段式、ok/warn/stop 三级闸门、10 项上线检查清单 | MIT |
| ⭐⭐ | `Siddardth7/quality-platform` | "AI 只提议不改写"的产品铁律、FMEA↔控制计划↔SPC 的闭环数据模型、MCP + Agent Skills 双通道 | 无 License，参考设计 |
| ⭐⭐ | `kolmag/8d-expert-workbench` | 5 段 RAG 流水线（改写→检索→重排→生成→groundedness）、**生成器与审查器用不同尺寸模型** | MIT |
| ⭐⭐ | `monkbird/QCmaker` | 预算熔断机制、PII 边界脱敏、SSRF 防护、版本化数据契约（project+dataset+revision） | MIT，工程质量高 |
| ⭐ | `chrisliuu345/AKIA-local` | `.qda` 证据包（版本号 + 逐项哈希）、本地 MCP stdio | Apache-2.0 |
| ⭐ | `expectedparrot/ishikawa` | "agent-friendly CLI" 的接口设计 | 无 License |
| ⭐ | `imnoo-team/quality-control-plan-mcp` | 图纸 → 控制计划的 MCP 工具设计 | MIT |

### 12.4 必须避开的坑

1. **License 传染**：`open-fmea`(GPL-3.0)、`py-qcc`(GPL-3.0)、`cassini`(NOASSERTION)、`OpenQMS`(AGPL-3.0) 都不适合直接并入商业产品。`luca-scr/qcc`(R) 无 License，只能参考公式。
2. **别让 LLM 算数字**：Cpk、Ppk、相关系数、假设检验必须用确定性代码。LLM 只做"解释这些数字意味着什么"。
3. **别用 RPN**：AIAG-VDA 2019 已用 Action Priority (AP)，用 RPN 会显得不专业（很多高星项目都犯了这个错）。
4. **别做通用图表推荐**：QCC 要的是"柏拉图必须有累计曲线和 80% 线"，不是"根据数据特征推荐柱状图还是折线图"。
5. **别忽略"待补充"状态**：QCC 现场经常没有数据。强制 AI 编数字是自杀行为，`evidence_status: missing → 显示"待补充"` 是正确设计。
6. **别只做 Web**：一线用户（护士/班组长）不会用复杂 Web 应用。要么做出能"单文件双击"的轻量版，要么做成 Agent Skill 让用户在自己熟悉的工具里用。

### 12.5 建议的 MVP 顺序

| 阶段 | 做什么 | 为什么先做这个 |
|---|---|---|
| **M1（4–6 周）** | Method Kernel：11 阶段 YAML 契约 + 12 类方法页定义 + 校验器 CLI | 这是唯一能形成壁垒的东西，且不依赖任何外部服务 |
| **M2（4 周）** | 数据接入 + 统计内核：Excel 导入 → 柏拉图/鱼骨/控制图/能力分析（复用 `Hogo-QA-tool` 口径） | 有了真数据才能做证据链，也才能证明"数字是对的" |
| **M3（3 周）** | Deliverable Compiler：python-pptx 出稿 + 版式 lint + 渲染回读 | 交付物是唯一能被评委看到的东西 |
| **M4（3 周）** | 证据账本：每个数字挂 evidence_id，缺证据显示"待补充" | 这是和所有竞品的分水岭 |
| **M5（4 周）** | 评审模拟器：另一模型按评分表打分 + 提问 | 最强的付费钩子，也是最好的自检工具 |
| **M6** | Agent Skill 封装（把 Method Kernel 暴露成 skill） | 借 `npx skills add` 的分发红利 |

### 12.6 一个战略判断

GitHub 上这个赛道的"技术供给"极度碎片化（中位数 1 星、半数 ≤10 次提交、四成无 License），而需求侧是刚性的（医院每年必须做品管圈、制造业必须过 IATF 审核）。

**供给碎片化 + 需求刚性 = 典型的产品化窗口。** 窗口期内最重要的不是"功能多"，而是"**在一件评委真正在意的事情上做到无可争议**"——最可能的那件事是：**你生成的每一个数字，都能一键追溯到证据**。

---

## 13. 附录

### 13.1 相关仓库清单（78 个，按层分组）

> 数据快照：2026-11-15。其中 **69 个完成了元数据 + 提交历史核验**（构成本次统计口径），其余 9 个为检索中确认相关、但未纳入精核样本的仓库（如 Odoo QMS 模块、制药 QMS 多智能体、电商文案质检 agent 等），列在此处保证覆盖完整。`★` = stars。

**A. QCC / 品管圈本体（9）**

| 仓库 | ★ | 语言 | L | 最后更新 | 一句话 |
|---|---|---|---|---|---|
| `monkbird/QCmaker` | 8 | Python | MIT | 2026-09-17 | LLM+多智能体辅助 QC 小组全流程 |
| `zhiwuli0228/skill-stock` | 0 | Python | 无 | 2026-09-13 | QCC PPT 方法学合规生成器（3 变体） |
| `duding-engicool/skill-qc-tools` | 3 | Python | 无 | 2026-09-06 | QC 七大手法图表自动生成 |
| `duding-engicool/skill-apqp-project-manager` | 1 | Python | 无 | 2026-09-06 | APQP 全流程 + FMEA/PPAP/控制计划 |
| `duding-engicool/skill-csr-analyzer` | 1 | Python | 无 | 2026-09-06 | IATF 16949 客户特定要求判定 |
| `Hulk-Zhao/Hogo-QA-tool` | 2 | TypeScript | MIT | 2026-09-23 | 离线 SPC/柏拉图/能力分析 + AI 解读 |
| `Novushisi/medical-slide-spec` | 4 | Python | MIT | 2026-08-20 | 医疗 PDCA/品管圈/RCA 演示内容规格 |
| `chrisliuu345/AKIA-local` | 0 | Python | Apache-2.0 | 2026-11-15 | 本地 IE+质量分析桌面（549 commits） |
| `Squama/Master` | 1 | Java | MIT | 2022-12-16 | 含 QC 立项/要因确认字段的老系统 |

**B. 质量方法论 Skill 包（9）**

| 仓库 | ★ | L | 说明 |
|---|---|---|---|
| `jherrodthomas/automotive-skills-suite` | **3312** | MIT | 152 skills（76 builder + 76 reviewer），xlsx 契约 |
| `RBraga01/Quality-Engineering-Skills` | 47 | MIT | 23 skills + 8 agents，含双归零 |
| `cleverlab-ai/iso-17025-skill` | 13 | MIT | ISO 17025 实验室认可 |
| `robustagile/six-sigma-in-r-skill` | 12 | Apache-2.0 | 教 Agent 写正确的 R |
| `cy556-like/automotive-quality-engineer-skills` | 6 | 无（README 标 MIT） | 中文五大工具 + 三件套文档输出 |
| `dungnotnull/industrial-qa-qc-audit-agent-skill` | 4 | 无 | 工业 QA/QC 过程审核 |
| `hypergraphdev/abs-skills` | 2 | MIT-0 | Lean/运营卓越方法 |
| `oliviakey-oliviasmuse/control-plan-builder` | 0 | MIT | 从 PFMEA 构建控制计划 |
| `walterkken/popular-process-skills` | 0 | NOASSERTION | PDSA/DMAIC 等通用流程 |

**C. 8D / RCA / CAPA（13）**

| 仓库 | ★ | 说明 |
|---|---|---|
| `kolmag/8d-expert-workbench` | 2 | 8D 引导 + RAG 专家，双模型生成/审计 |
| `orcunku/supplier-quality-8d-copilot` | 0 | 65 份合成文档语义检索（4 commits） |
| `mickemora/supplier-quality-copilot` | 0 | 航空航天 NCR/8D + 重复根因检测 |
| `joel5638/Recalltrace-ai` | 0 | LangGraph 供应商质量调查 + HITL |
| `eakarsu/ai-supplier-quality-capa-8d` | 0 | CAPA + 8D |
| `aken1023/panjit-8d-report-ai` | 1 | 强茂半导体真实场景 |
| `LouisBoBo/pythonProject_8D_Report` | 2 | 中文 8D 报告 |
| `Laurenceku2026/AI-FA_8D` | 1 | FA + 8D 双输出 |
| `saikrish-code/Root-Cause-Analysis` | 0 | PDF/事件 → 5Why 质量调查 |
| `Sviless/ai-root-cause-coach` | 0 | 本地 Lean RCA（5Why+鱼骨+矩阵） |
| `quality-pixel/Rootcause-analysis3` | 0 | 鱼骨 + 5Whys（同作者 4 仓库） |
| `Pakawat-Dev/Root_Cause_Analysis_Langgraph` | 0 | LangGraph 鱼骨图 |
| `expectedparrot/ishikawa` | 0 | agent-friendly 因果分析 CLI |

**D. FMEA / APQP（11）**

| 仓库 | ★ | 说明 |
|---|---|---|
| `dromation/open-fmea` | 47 | 开源 FMEA（GPL-3.0，非 AI） |
| `YuchenXia/LLMRiskAnalyzer` | 41 | LLM 辅助 FMEA（RPN 导向） |
| `lukasbahr/kg-rag-fmea` | 33 | KG + RAG 做 FMEA（已停更） |
| `Abinash009/iso26262-agent` | 18 | HARA/FMEA/安全需求，RAG+LLM+MCP |
| `MasrourTawfik/DFMEA-LLM-Enhanced` | 3 | 学术：LLM 融入 DFMEA |
| `Siddardth7/fmea-risk-analyzer` | 4 | RPN/AP + 柏拉图 + 热力图 |
| `Amirkhaji/fmea-automation-using-LLM` | 0 | 文档 → 组件 → S/O/D |
| `Mohamed-Elsafty23/LLM-FMEA-Analyzer` | 0 | 客评 → FMEA（VOC 驱动） |
| `ranjith-24-prog/fmea_ppr_validation` | 0 | LLM+RAG 复用历史 FMEA（IEEE ETFA 2026） |
| `aoyexiaoqi/fmeaflow` | 0 | PFMEA ↔ 控制计划一致性 |
| `genkidesu7/agentic-star-...-pfmea-to-control-plan` | 0 | PFMEA → 控制计划比对 agent |

**E. SPC / 统计（8）**

| 仓库 | ★ | 说明 |
|---|---|---|
| `luca-scr/qcc` | 61 | R 语言 QCC 经典包 |
| `M1ndSmith/ASPC` | 15 | Phase I/II + 9 种图 + MSA 全项 |
| `KensoBI/spc-chart` | 13 | Grafana SPC 面板 |
| `petermgates/py-qcc` | 7 | Python 移植（GPL-3.0） |
| `saturnis-io/cassini` | 5 | 开源 SPC 平台 |
| `DailyDana/process-capability-analyzer` | 5 | 控制图 + 能力 + Gage R&R |
| `Siddardth7/quality-platform` | 4 | 2502 测试，AIAG 闭环 + MCP（511 commits） |
| `bertanucar/shewhart` | 3 | 纯 SPC 库，对标参考数据验证 |

**F. QMS / 审核 / MCP / 视觉（18）**

| 仓库 | ★ | 说明 |
|---|---|---|
| `C-realize/OpenQMS` | 32 | 云原生 QMS（AGPL-3.0） |
| `jonaesantos/odoo-qms-iso9001` | 30 | Odoo ISO 9001 模块 |
| `factorysemantics/factorysemantics-mes` | 17 | agent-native MES + MCP |
| `evolunis/openQMS` | 11 | ISO 13485 QMS |
| `esclaudio/paraiso-lite` | 6 | ISO 9001:2015 QMS |
| `TMBIA-Tmti/AI-QMS` | 4 | ISO 13485 + OCR + 防篡改审计链 |
| `peige-guo/Multimodal_Industrial_Inspection_Agent` | 7 | 多模态工业质检 agent |
| `kolmag/auditor-expert` | 1 | ISO 9001/IATF/AS9100D RAG（610 题评测） |
| `imnoo-team/quality-control-plan-mcp` | 1 | 图纸 → 控制计划 MCP |
| `zavora-ai/mcp-qms` | 1 | QMS MCP（Rust，含 HACCP） |
| `Erwinya/qms-ncr-service` | 1 | NCR REST API（MIT） |
| `alexcroston79/1factory-mcp` | 0 | 商业 QMS 的 MCP（19 tools） |
| `dbaklesis/DigiAuditor` | 0 | ISO 9001/14001 AI 审核员 |
| `DesarrollosLAM/trinorma-ai-auditor` | 0 | 整合体系审核 copilot（RAG） |
| `SouleymaneDiallo04/QMS_Chatbot` | 1 | ISO 9001/IATF 聊天机器人 |
| `arslan-kursad/aiqs-agent` | 0 | 视觉质检的 agentic 裁决层 |
| `ITU-AI-ML-in-5G-Challenge/wearedge-opea-manufacturing` | 1 | OPEA 制造 agent 套件 |
| `xkkkkkkm/e-commerce-copy-quality-inspection-agent` | 9 | 电商文案质检 |

**G. DMAIC / 制药模板化项目（10）**

| 仓库 | ★ | 说明 |
|---|---|---|
| `psptpx/DMAIC-Bench` | 2 | 多阶段分析任务的 agent 自约束 benchmark（AGPL） |
| `virbahu/dmaic-toolkit` | 4 | DMAIC 统计检验工具 |
| `lalalumputan/dmaic-copilot` | 0 | DMAIC 六西格玛 agent 伴侣 |
| `brunodt98/DMAIC-Agent` | 0 | 六西格玛咨询 agent（Streamlit） |
| `EduReyeshub/dmaic-intelligence-agent` | 0 | DMAIC + ICH Q9(R1) + HITL |
| `07pavan/Pharmaceutical_AI` | 0 | 制药/器械 QMS（LangGraph 多智能体） |
| `rizzit17/pharmassist` | 1 | 制药 QMS 受理 copilot |
| `nick-devart/Ai_Customer_Care` | 0 | 制药 QMS 客诉分析 |
| `dark-abhaypydev/pharma-complaint-ai-agent` | 0 | 制药客诉 agent |
| `PratikPatil2345/Pharma-Customer-Complaint-Management-System` | 0 | API & FDF 客诉管理 |

### 13.2 检索关键词清单（可直接复现）

```bash
# 主口径（会大量撞名）
gh api -X GET search/repositories -f q='qcc in:name' -f sort=stars
gh api -X GET search/repositories -f q='qcc in:description' -f sort=stars
gh api -X GET search/repositories -f q='"quality control circle"' -f sort=stars
gh api -X GET search/repositories -f q='"QC circle"' -f sort=stars

# 中文口径
gh api -X GET search/repositories -f q='品管圈 in:readme' -f sort=stars
gh api -X GET search/repositories -f q='QC小组 in:readme' -f sort=stars
gh api -X GET search/repositories -f q='QC七大手法' -f sort=stars

# 代码口径（最关键，能穿透无 tag 项目）
gh api -X GET search/code -f q='"品管圈" language:Python'
gh api -X GET search/code -f q='"品管圈" in:file filename:README.md'
gh api -X GET search/code -f q='"要因确认"'
gh api -X GET search/code -f q='"QC story"'

# 方法论口径
gh api -X GET search/repositories -f q='FMEA llm' -f sort=stars
gh api -X GET search/repositories -f q='APQP PPAP' -f sort=stars
gh api -X GET search/repositories -f q='"IATF 16949"' -f sort=stars
gh api -X GET search/repositories -f q='DMAIC agent' -f sort=stars
gh api -X GET search/repositories -f q='"8D" quality corrective action' -f sort=stars

# Topic 口径
gh api -X GET search/repositories -f q='topic:quality-management' -f sort=stars
gh api -X GET search/repositories -f q='topic:qms' -f sort=stars
gh api -X GET search/repositories -f q='topic:spc' -f sort=stars
gh api -X GET search/repositories -f q='topic:six-sigma' -f sort=stars
gh api -X GET search/repositories -f q='topic:fmea' -f sort=stars
gh api -X GET search/repositories -f q='topic:qcc' -f sort=stars   # → 全是噪音
```

### 13.3 本次调研的局限

1. **GitHub 之外未系统覆盖**：Gitee、GitLab、企业内部项目、以及大量"用 Dify/Coze 搭的私有 QCC 助手"不在样本内。从公开信息看，国内医疗机构的"品管圈大模型"多为内部自研或 Dify 私有化魔改，不会开源。
2. **未做代码级审计**：69 个仓库中只精读了约 20 个的 README/文档/目录结构，未对全部做代码质量评审。部分"工程扎实"的判断基于 README 证据（CI badge、测试数、截图可复现性），可能存在夸大。
3. **star 数受时间影响**：样本里多个项目创建于 2026 年下半年，star 积累时间不足，不能完全代表质量。
4. **商业产品未纳入**：Minitab、InfinityQS、ETQ Reliance、Qualityze、以及国内的简道云/质量学院类 SaaS 未做对比。它们的 AI 能力是重要的竞争参照，但超出"GitHub 社区"范围。
5. **GitHub 搜索对中文支持有限**：`品管圈 in:readme` 返回 38017 条结果但前十全是无关大仓库，说明索引噪音极大。本次靠 code search 补足，仍可能有遗漏。

---

*报告完 · 2026-11-15 · 样本 69 仓库 / 40+ 组检索 / 5 类通道*
