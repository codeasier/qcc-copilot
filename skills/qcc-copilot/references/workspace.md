# 工作区、人工修订、续接与格式升级（2.7）

> 完整升级/回滚见 `../upgrade-rollback.md`；本文件给出可直接运行的恢复与冲突处理示例。

## 工作区结构

`.qcc/<topic-id>/`：`topic.json`（事实源）、`sources.json`、`revisions/`（写入前备份）、
`calculations/`、`deliveries/<id>/`、`exports/`。`topic.json` 带 `schema_version`、`revision`、`content_hash`。

## 示例 1：跨会话恢复（E08）

```bash
export QCC="PYTHONPATH=<包>/src python3 -m qcc_copilot"
$QCC workspace.init --input '{"workspace":"./p","topic_id":"t1","title":"T","owner":"甲"}'
$QCC workspace.resume --input '{"workspace":"./p","topic_id":"t1"}'
```

预期：`resumed_from_persisted_state=true`，恢复 `stage`、`unresolved_tasks`、`claims_needing_review`、
`reusable_deliverables`、`next`；损坏档案报 `damaged_workspace` 并保留原文件，不冒充空白新课题。

## 示例 2：读取后人工修改 → 冲突保留

```bash
# 工具基于 revision=2 读取；成员随后直接改 topic.json；工具再保存旧视图
$QCC claim.add --input '{"workspace":"./p","topic_id":"t1",...}'
# 若期间发生外部修改，返回 error.code=revision_conflict，topic.json 保持人工修改内容
```

预期：原档案与备份均在 `revisions/`，没有静默覆盖。

## 示例 3：定向失效 + 历史交付保留

```bash
$QCC evidence.invalidate --input '{"workspace":"./p","topic_id":"t1","changed_ids":["timesheet-09"]}'
$QCC delivery.get --input '{"workspace":"./p","topic_id":"t1","delivery_id":"<id>"}'
```

预期：仅依赖该来源的计算/主张/交付标 `needs_review` 或 `evidence_stale`；无关结论不重置；
历史 `snapshot.json` 保持原 `topic_revision` 与 `content_hash`。

## 示例 4：格式升级

未知 `schema_version` 的档案报 `unknown_format_version` / `damaged_workspace`，要求先备份再迁移；
升级保留 `revisions/` 与全部 `deliveries/`，历史交付不被当前数据改写；无法安全降级时明确报告。

## 验证点（2.7）

按说明可完成恢复与冲突处理，并保留原档案及历史交付。
