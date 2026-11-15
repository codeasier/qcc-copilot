# 双入口与覆盖说明使用示例（3.5 / US01 / US02 / E01–E03）

> 同一支持宿主可分别从"改进描述"与"资料目录"进入，得到有效候选或有依据的不足报告。
> 样例来自 `tests/fixtures/`，是验证情境，不是真实参评课题或已实现收益。

## 入口 A：成员已有改进（E01 / US01）

```bash
export QCC="PYTHONPATH=<包>/src python3 -m qcc_copilot"
cat > a.json <<'JSON'
{"supplied":{
  "description":"已上线构建校验脚本，但没有收益测量",
  "implementation_status":"implemented",
  "facts":[{"kind":"feature_implemented","text":"脚本已上线","source_id":"git-1"},
           {"kind":"deployment","text":"流水线已接入","source_id":"link-1"}],
  "benefit_claim":"成员口述省了人天","measured_outcome":null,
  "adoption_by_other_teams":null,"unknowns":["无基线","无事件数"]}}
JSON
$QCC discovery.refine --input a.json
```

预期：区分「功能已实现 / 已证明收益 / 已被其他团队采用」；`benefit_proven=false`，
收益主张 `support=unverified`；保留 `unknowns`，不把补写材料当成当时已执行的测量。

## 入口 B：指定资料发现候选（E02 / US02）

```bash
cat > b1.json <<'JSON'
{"base_dir":"tests/fixtures/e02_materials","max_bytes":200,
 "sources":[{"locator":"issue-12.md","kind":"file"},{"locator":"issue-19.md","kind":"file"},
            {"locator":"retro-01.md","kind":"file","simulate_failure":true},
            {"locator":"missing.md","kind":"file"},
            {"locator":"https://remote/42","kind":"remote"}]}
JSON
$QCC sources.index --input b1.json > coverage.json
```

预期（覆盖说明，E03）：`counts` 含 `read / unread / failed / truncated`；`full_coverage=false`；
`unread_or_failed` 列出未读项；分析结论仅限实际已读部分，不把未读当作无问题。

宿主读已读资料后提交候选卡：

```bash
# candidate_cards.json 含 candidate_cards_submitted_by_host + coverage
$QCC discovery.candidates --input candidate_cards.json
$QCC discovery.reconcile --input reconcile.json
```

预期：每卡含问题、来源、价值假设、共性场景、约束、未知项与验证建议；重复 `dedup_key` 合并并保留多来源；
资料不足时 `insufficient=true`、`candidates=[]`，不按固定数量凑题。

## 入口 B 的"资料不足"路径

```bash
$QCC discovery.candidates --input '{"candidate_cards_submitted_by_host":[],"scope_note":"仅一份空文件"}'
# 预期：insufficient=true，note 说明资料不足与建议补充的信息
```

## 选择后建档（不整仓计入）

```bash
$QCC discovery.select --input '{"workspace":"./p","candidate":<所选候选>}'
# 预期：selected_scope_only=true，课题 problem 仅含该候选的来源与价值假设
```

## 验证点（3.5）

同一支持宿主从两种入口进入均得到有效候选或有依据的不足报告；单仓库多个功能不会自动全部计入同一课题。
