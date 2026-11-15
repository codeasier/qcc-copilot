# 成员快速开始（9.4）

> 面向普通使用者；无需了解 QCC 全套方法即可开始。示例为验证情境，不是真实参评课题或已实现收益。

## 1. 安装 / 能力检查

分发包为 `skills/qcc-copilot/`（Skill 指令 + 参考）与 `src/qcc_copilot/`（确定性工具 + 资源）。
要求 Python >= 3.11；本内核**零第三方依赖**（pip 不可用亦可运行）。

```bash
export QCC="PYTHONPATH=<包根目录>/src python3 -m qcc_copilot"
$QCC version
$QCC capabilities     # 列出可执行步骤与受限步骤（如渲染检查）
```

`capabilities` 若提示渲染依赖缺失，材料生成仍可进行，但渲染检查会标为未执行/受限，不会被当作通过。

## 2. 开始一个课题（两种入口）

**入口 A：我已有改进**

```bash
cat > refine.json <<'JSON'
{"supplied":{"description":"已上线构建校验脚本，但没有工时测量","implementation_status":"implemented",
  "facts":[{"kind":"feature_implemented","text":"脚本已上线","source_id":"git-1"}],
  "benefit_claim":"大概能省一些人天","unknowns":["无基线","无事件数"]}}
JSON
$QCC discovery.refine --input refine.json
# 预期：feature_implemented=true，benefit_proven=false，收益主张 support=unverified
```

**入口 B：从指定资料发现候选**

```bash
cat > sources.json <<'JSON'
{"base_dir":"materials","sources":[{"locator":"issue-12.md","kind":"file"},
  {"locator":"https://remote/42","kind":"remote"}],"max_bytes":65536}
JSON
$QCC sources.index --input sources.json
# 预期：read / unread / failed / truncated 分别记录，未读不表述为全范围已检查
# 宿主阅读已读资料后，把推理得到的候选卡交给：
$QCC discovery.candidates --input candidate_cards.json
$QCC discovery.reconcile --input reconcile.json
```

选定一个候选后建档（只纳入该候选范围）：

```bash
$QCC discovery.select --input select.json   # 含 workspace 与 candidate
```

## 3. 持续推进（新会话恢复）

```bash
$QCC workspace.resume --input '{"workspace":"./proj","topic_id":"t1"}'
# 恢复阶段、未解决补证任务与下一步；不依赖旧聊天记录
```

把工具生成的 `next` 与 `tasks` 作为下一轮工作输入；成员补充真实记录后调用
`methods.update_gaps`、`benefit.compute`、`claim.add` 更新档案。

## 4. 生成成果

```bash
$QCC delivery.snapshot --input '{"workspace":"./proj","topic_id":"t1"}'
$QCC deliverable.compile --input '{"workspace":"./proj","topic_id":"t1","delivery_id":"<id>"}'
$QCC deliverable.review --input '{"workspace":"./proj","topic_id":"t1","delivery_id":"<id>"}'
$QCC deliverable.verify --input '{"workspace":"./proj","topic_id":"t1","delivery_id":"<id>"}'
$QCC deliverable.status --input '{"workspace":"./proj","topic_id":"t1","delivery_id":"<id>"}'
```

产出在 `.qcc/t1/deliveries/<id>/`：报告、收益说明、复用说明、图表与底稿、真实 `deck.pptx`、
评审问题清单、检查记录。缺证据或检查未通过只会得到 `draft`。

## 5. 导出摘要给负责人

```bash
$QCC summary.export --input '{"workspace":"./proj","topic_id":"t1"}'
# 把 .qcc/t1/exports/summary-*.json 通过现有共享渠道交给负责人
```

## 6. 回收反馈并继续

```bash
$QCC feedback.import --input feedback.json
$QCC workspace.resume --input '{"workspace":"./proj","topic_id":"t1"}'
# 反馈进入建议/待办，不改变事实、收益或验证状态
```

## 验证点（9.4）

- 普通使用者按上述命令即可完成安装、开始、新会话恢复。
- 回滚/升级不删除成员来源资料与历史快照，见 `upgrade-rollback.md`。
