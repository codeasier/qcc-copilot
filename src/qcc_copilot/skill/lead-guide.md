# 负责人使用与轻量汇总（9.4 / 8.5 / US09）

> 负责人通过标准摘要文件了解候选课题的价值、进展、证据缺口与参评准备情况；无需取得全部源代码、日志或原始数据，也不需要新增集中平台。

## 1. 收集与校验

成员通过现有共享渠道提供 `summary-<topic>-r<rev>.json`（及同名 `.md` 供阅读）。

```bash
export QCC="PYTHONPATH=<包>/src python3 -m qcc_copilot"
cat > one.json <<'JSON'
{"summary": <粘贴成员摘要 JSON>}
JSON
$QCC summary.import --input one.json
# 未知格式版本或缺课题标识会被明确拒绝，不破坏已有聚合
```

## 2. 聚合多份摘要

```bash
cat > batch.json <<'JSON'
{"summaries":[<摘要1>, <摘要2>, <摘要3> ...]}
JSON
$QCC summary.aggregate --input batch.json > agg.json
```

聚合规则（`aggregate.audit` 逐条可查）：

| 情况 | 处理 |
|---|---|
| 相同标识 + 相同修订 + 相同语义内容 | 重复，不重复计数 |
| 更低修订 | 保留导入审计，不回退当前聚合 |
| 更高修订 | 更新对应课题，保留历史 |
| 相同修订 + 不同语义内容 | 显式冲突，保留双方，不自动择一 |
| 仅导出时间变化 | 语义摘要相同 → 重复，不产生冲突 |

> 导出时间不参与语义内容摘要，避免"只改了导出时间"被误判为冲突。

## 3. 汇总视图

```bash
cat > views.json <<'JSON'
{"aggregate": <上一步 data.aggregate>}
JSON
$QCC summary.views --input views.json
# 输出 markdown 与 csv：按阶段、三维结论、缺口、下一步组织
```

- 显示各摘要的快照时间与冲突标记。
- 「未收到新摘要」展示为进展未知，**不解释为课题没有进展**。
- 负责人据此识别需辅导或适合继续打磨的对象。

## 4. 给出反馈（回流）

```bash
cat > fb.json <<'JSON'
{"workspace":<可选，用于把反馈文件写入某工作区>,"topic_id":"t1",
 "target_revision":3,"author":"负责人乙","content":"补充效果验证记录"}
JSON
$QCC feedback.export --input fb.json
# 把 feedback-*.json 交回成员
```

成员侧：

```bash
$QCC feedback.import --input '{"workspace":"./proj","topic_id":"t1","feedback":<反馈 JSON>}'
```

反馈带作者、标识与目标修订，进入**建议/待办**，不自动成为事实、收益或验证状态；针对旧修订时标明版本差异。

## 5. 无需新增平台的完整文件交换示例

```
成员 summary.export ──现有共享渠道──▶ 负责人 summary.import / aggregate / views
                                          │
                                          └── feedback.export ──▶ 成员 feedback.import ──▶ 续接
```

- 全过程只交换标准摘要与反馈文件，不上传全部原始资料，不部署账户或项目管理系统。
- 样例 `tests/fixtures/e11_summaries.json` 含旧版本、重复与同版本冲突，可直接用于 `summary.aggregate` 验证。

## 验证点（8.5 / 9.4）

- 不新增平台、不提交全部原始资料即可完成导出 → 聚合 → 辅导 → 回流。
- 陈旧、缺失、冲突摘要可见；反馈不改变事实与验证状态。
