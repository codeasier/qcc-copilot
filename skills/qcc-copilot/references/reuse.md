# 推广状态、计数单位与反馈更新说明（6.4 / US05 / E07）

> 成果推广性从选题共性痛点与受益价值判断；工具使用便利性是单独指标，不替代成果可推广性。

## 三种状态分别检查（6.3）

| 状态 | 含义 | 证据要求 |
|---|---|---|
| 潜在适用 (`potential`) | 可能有共性价值 | 共性依据 + 待验证需求 |
| 已复现 (`reproduced`) | 其它团队复现验证 | 复现记录 |
| 实际采用 (`adopted`) | 已用于实际工作并获益 | 使用记录 + 效果反馈 |

安装成功、演示、成员口述或预计收益**不自动**成为已采用并获益。

## 示例 1：共性潜力但依赖个人环境（E07 / 6.1 / 6.2）

```bash
export QCC="PYTHONPATH=<包>/src python3 -m qcc_copilot"
$QCC reuse.evaluate --input '{"common_problem":"多平台构建失败","common_problem_sources":["issue-12"],
  "value_basis":"减少排查（假设）","beneficiaries":["其它团队"],
  "tool_usability_gain":{"metric":"member_tool_time_saved_hours","value":2}}'
# 预期：potential_only=true，tool_usability.separate_metric=true（材料整理耗时不证明可推广）

$QCC reuse.package --input '{"conditions":["统一镜像"],"steps":["接入流水线"],
  "depends_on_personal_infra":true}'
# 预期：personal_infra_flagged=true、decoupling_needed=true、missing 列出资产/验证/维护/成本
```

## 示例 2：安装 ≠ 收益验证；采用计数去重（6.3 / E07）

```bash
$QCC reuse.adoption --input '{"adoption_records":[
  {"team":"团队A","status":"installed"},
  {"team":"团队B","status":"adopted","effect_feedback":"周均减少 3 次重复构建"}]}'
# 预期：installed_not_adopted=true；团队B benefit_verified=true

$QCC reuse.count --input '{"records":[
  {"team":"团队B","status":"adopted","source_id":"log1","dedup_key":"k"},
  {"team":"团队B","status":"adopted","source_id":"log2","dedup_key":"k"}]}'
# 预期：distinct_adopted_teams=1，duplicate_sources_not_double_counted=true
```

计数单位默认 `team`，去重键 `stable(team, dedup_key)` 显式保存在返回值；同团队多来源/多版本不重复增加推广部门数。

## 示例 3：复现失败反馈缩小适用范围（6.3）

```bash
$QCC reuse.feedback --input '{"package":<上一步 package>,
  "feedback":[{"team":"团队C","feedback":"缺少所需权限，无法适用"}]}'
# 预期：applicability_narrowed=true，validation_tasks 含依据；不再对该场景无条件宣称可复制
```

## 验证点（6.4）

示例中潜力、采用与收益证据可分别检查；个人环境依赖、缺失项与接入要求不被生成文案隐去；
工具易用性与成果推广性分别计量。
