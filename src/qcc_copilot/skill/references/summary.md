# 成员与负责人文件交换示例（8.5 / US09 / E11）

> 完整负责人使用见 `../lead-guide.md`；本文件给出最小交换契约与验证点，无需新增平台或提交全部原始资料。

## 交换边界

| 文件 | 方向 | 命令 |
|---|---|---|
| `summary-<topic>-r<rev>.json` / `.md` | 成员 → 负责人 | `summary.export` → `summary.import` |
| 汇总 Markdown / CSV | 负责人内部 | `summary.aggregate` → `summary.views` |
| `feedback-<id>.json` | 负责人 → 成员 | `feedback.export` → `feedback.import` |

标准摘要含标识、修订、格式版本、语义内容摘要、三维结论、阶段、缺口、下一步、导出时间；
不包含全部代码/日志/原始数据，负责人不声称已独立核验未提供依据。

## 端到端最小示例

```bash
export QCC="PYTHONPATH=<包>/src python3 -m qcc_copilot"
# 成员（即使有收益/方法缺口也保留状态）
$QCC summary.export --input '{"workspace":"./p","topic_id":"t1"}' > member.json
# 负责人：导入校验 + 聚合 + 视图
$QCC summary.import --input '{"summary":<member 摘要>}'
$QCC summary.aggregate --input '{"summaries":[<摘要1>,<摘要2>...]}' > agg.json
$QCC summary.views --input '{"aggregate":<agg.data.aggregate>}'
# 负责人：反馈
$QCC feedback.export --input '{"topic_id":"t1","target_revision":3,"author":"负责人","content":"补基线"}'
# 成员：回流
$QCC feedback.import --input '{"workspace":"./p","topic_id":"t1","feedback":<反馈>}'
```

## 聚合行为（E11）

- 重复（同标识/修订/语义内容）不重复计数；仅导出时间变化不算新内容。
- 更低修订保留审计、不回退当前聚合；更高修订更新并保留历史。
- 同修订不同语义内容 → 显式冲突，保留双方，不自动选择收益更高或更晚的一份。
- 未知格式版本或缺标识的摘要被拒绝，不破坏已有聚合。
- 汇总只表示已导入快照，未收到更新不解释为实时无进展。

## 验证点（8.5 / 9.4）

无需新增平台、不提交全部原始资料，即可完成导出 → 聚合 → 辅导 → 回流全过程；
陈旧、缺失与冲突摘要可见，反馈只进入建议/待办，不改变事实、收益或验证状态。
