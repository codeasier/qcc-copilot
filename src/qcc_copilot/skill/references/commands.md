# 领域操作命令与输入契约（9.1）

所有命令：`PYTHONPATH=<包>/src python3 -m qcc_copilot <command> [--input req.json | stdin] [--workspace <根>]`；
pip 安装后 `qcc` 等价于该入口。
输出统一为 `{"ok":true,"command":...,"data":...}` 或 `{"ok":false,"command":...,"error":{"code","message","details"}}`。
`--workspace` 会注入请求的 `workspace` 字段；多课题续接务必带 `topic_id`。

## 契约与能力

| 命令 | 关键输入 | 产物 |
|---|---|---|
| `version` / `capabilities` | — | 版本、依赖、受限步骤 |
| `contract.types` | — | 全部契约类型 |
| `contract.validate` | `type`, `object` | 校验通过或明确失败（缺标识/错类型/未知版本） |
| `skill.export` | `dest`, `force?` | 把随包 Skill 文档导出到宿主目录（非空目录需 `force=true`） |

## 工作区与证据账本（2.x）

| 命令 | 关键输入 | 说明 |
|---|---|---|
| `workspace.init` | `workspace`,`topic_id?`,`title`,`owner` | 建档；已存在档案不覆盖 |
| `workspace.list` | `workspace` | 列出课题（含损坏标记） |
| `workspace.route` | `workspace`,`topic_id?` | 多课题路由，歧义报错 |
| `workspace.resume` | `workspace`,`topic_id?` | 恢复阶段/未解决事项/下一步 |
| `workspace.status` | `workspace`,`topic_id` | 摘要状态 |
| `claim.add` | `text`,`origin`,`category`,`evidence`,`verification` | 主张按规则定支持状态 |
| `claim.conflict` | `claim_id`,`source` | 保留冲突双方，不择一 |
| `dependency.link` | `derived_id`,`kind`,`depends_on` | 登记依赖 |
| `evidence.invalidate` | `changed_ids`,`note` | 定向失效并标记相关交付待核验 |
| `delivery.snapshot` | `workspace`,`topic_id` | 固定课题/规则/证据/计算清单 |
| `delivery.list` / `delivery.get` | `delivery_id?` | 历史快照 |

`origin ∈ {record, member_statement, ai_inference, estimate, example}`；
`support ∈ {unverified, supported, insufficient, conflicting}`；`needs_review` 表示失效影响。

## 双入口发现（3.x）

| 命令 | 关键输入 | 说明 |
|---|---|---|
| `sources.index` | `base_dir`,`sources[{locator,kind,content?,simulate_failure?}]`,`max_bytes` | 覆盖状态 read/unread/failed/truncated + 版本 |
| `sources.boundary` | — | 远端资料统一输入边界 |
| `discovery.refine` | `supplied` | 提炼已有改进，区分实施/收益/采用 |
| `discovery.candidates` | `candidate_cards_submitted_by_host`,`coverage` | 候选卡，允许零候选 |
| `discovery.reconcile` | `candidates` | 去重/聚焦/拆分合并 |
| `discovery.select` | `workspace`,`candidate` | 仅按所选范围建档 |

`kind ∈ {file, csv, json, git, remote, connector}`

## 方法、收益、推广（4–6.x）

| 命令 | 关键输入 |
|---|---|
| `methods.profile` | — |
| `methods.stage` | `facts`（各事实 `filled`/`verified`） |
| `methods.recommend` | `gaps` |
| `methods.check` | `topic`（问题/原因/对策/实施/效果） |
| `methods.gaps` / `methods.update_gaps` | `gaps` / `topic`,`new_evidence` |
| `benefit.compute` | `metric`（baseline/improved/event_count/unit/cost/hours_per_person_day…） |
| `benefit.ratio` / `benefit.nonlabor` / `benefit.separate` | `numerator`,`denominator` / `metric` / `measured`,`extrapolation` |
| `reuse.evaluate` / `reuse.package` / `reuse.adoption` / `reuse.count` / `reuse.feedback` | 结构化复用记录 |

## 成果与汇总（7–8.x）

| 命令 | 关键输入 | 说明 |
|---|---|---|
| `deliverable.compile` | `workspace`,`topic_id`,`delivery_id?` | 从固定快照生成全部材料 + 真实 PPTX |
| `deliverable.review` | `delivery_id` | 独立三维定性检查 |
| `deliverable.verify` | `delivery_id`,`run_render?` | 覆盖/占位符/溢出/独立渲染 |
| `deliverable.status` | `delivery_id`,`verification?` | draft / review-ready |
| `deliverable.pptx_verify` | `path` | PPTX 结构核验 |
| `summary.export` / `summary.import` | `topic_id` / `summary` | 标准摘要导出/校验 |
| `summary.aggregate` / `summary.views` | `summaries` / `aggregate` | 按标识+修订+语义摘要聚合 |
| `feedback.export` / `feedback.import` | `topic_id`,`target_revision`,`author`,`content` / `feedback` | 反馈回流 |

## 最小示例

```bash
# 建档 + 校验一个主张
printf '%s' '{"workspace":"./proj","topic_id":"t1","title":"构建失败定位","owner":"甲"}' \
  | python3 -m qcc_copilot workspace.init
printf '%s' '{"workspace":"./proj","topic_id":"t1","text":"省了人天","origin":"member_statement","category":"benefit","requested_support":"supported"}' \
  | python3 -m qcc_copilot claim.add
# 预期：support=unverified（口述不自动成为实测），并保留 downgraded_from=supported
```
