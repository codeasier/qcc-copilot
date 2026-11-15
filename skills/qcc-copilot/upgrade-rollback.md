# 升级、回滚与格式迁移（2.7 / 9.4）

> 目标：升级格式或回滚版本不删除成员来源资料与历史交付；无法安全降级时明确报告。

## 1. 档案布局（事实源）

```
<工作区根>/.qcc/<topic-id>/
  topic.json           当前课题、规则版本、事实、主张、阶段、任务、下一步
  sources.json         来源位置、可用版本、读取覆盖
  revisions/           历次状态与修订依据（每次写入前的备份）
  calculations/        计算相关（登记于 topic.calculations）
  deliveries/<id>/     固定快照、产物清单、报告、PPT、检查记录
  exports/             摘要与反馈交换包
```

每个对象带 `schema_version`；课题有单调 `revision` 与 `content_hash`。

## 2. 人工修订与冲突处理示例（2.7）

```bash
export QCC="PYTHONPATH=<包>/src python3 -m qcc_copilot"
$QCC workspace.resume --input '{"workspace":"./proj","topic_id":"t1"}'
# 成员直接编辑 topic.json（人工修订）后，工具若基于旧视图写入：
# 返回 ok=false, error.code=revision_conflict，原有文件保留
```

处理：重新 `workspace.resume` 读取新状态 → 基于新 `revision`/`content_hash` 提交增量；需要合并时由成员明确决定，不静默覆盖。
并发工具写入同理：先写入者推进修订，后写者报冲突并保留档案。

## 3. 续接示例（2.7 / E08）

```bash
# 新会话（无任何内存/聊天状态）
$QCC workspace.resume --input '{"workspace":"./proj","topic_id":"t1"}'
# 预期：恢复 stage、unresolved_tasks、claims_needing_review、reusable_deliverables、next
# 来源或计算输入变化后：
$QCC evidence.invalidate --input '{"workspace":"./proj","topic_id":"t1","changed_ids":["timesheet-2026-09"],"note":"基线修正"}'
# 相关收益/主张/交付被标 needs_review / evidence_stale；无关结论不被重置
```

## 4. 格式升级 / 迁移（2.7）

- 未知 `schema_version` 的档案由 `workspace.load` 报 `damaged_workspace`（要求迁移），**不会**被重新初始化为空白课题。
- 升级流程：备份整个 `.qcc/<topic-id>/` → 用兼容版本工具读取 → 写出新格式 → 保留 `revisions/` 与 `deliveries/` 原快照。
- 历史交付保持原 `snapshot.json`（含当时课题修订、规则、证据与计算清单），不被当前数据改写。
- 无法安全降级的档案必须报告，不强行回写。

## 5. 回滚（9.4）

```bash
# 1) 使用兼容版本分发包（VERSION / dist-manifest.json 标识版本）
# 2) 保留并复制当前 .qcc/ 目录作为备份
cp -R ./proj/.qcc ./proj/.qcc.backup
# 3) 用兼容版本工具读取；不删除来源资料与历史交付
```

- 回滚不删除成员来源资料（`sources.json`）与 `deliveries/` 历史快照。
- 若新版已引入不兼容 `schema_version`，工具报 `unknown_format_version`，明确要求先迁移或使用兼容版本，不静默降级。

## 验证点（2.7 / 9.4）

- 按说明可完成恢复与冲突处理示例，原档案与历史交付均保留。
- 回滚后来源与历史快照仍可读取；不兼容降级被明确报告。
