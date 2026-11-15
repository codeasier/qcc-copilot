# 方法建议、规则适配与不足数据处理示例（4.4 / US03 / E06）

> 规则有来源、版本与适用条件；未执行活动不会因补写材料被标为已发生。

## 规则包与适用（4.1）

```bash
export QCC="PYTHONPATH=<包>/src python3 -m qcc_copilot"
$QCC methods.profile
# 预期：official_scoring_configured=false、has_official_weights=false、
#       三维（价值/推广/QCC 遵循）、universality_warning 说明固定十一阶段/特定模板不统一适用
```

## 示例 1：已有实施但缺基线（4.2）

```bash
cat > stage.json <<'JSON'
{"topic":{"facts":{}},
 "facts":{"problem_statement":true,"beneficiaries":true,
  "countermeasure":true,"implementation":{"filled":true,"verified":false},
  "baseline":false,"factor_verification":false,"improved_metric":false}}
JSON
$QCC methods.stage --input stage.json
```

预期：保留实施进展（`reusable_materials`），列出基线/要因验证缺口，`structure_and_evidence_separate=true`，
`current_stage` 不是 complete；允许回溯（`allows_backtrack`）与有依据的不适用（`not_applicable_supported`）。

## 示例 2：论证链检查（E06 / 4.3）

```bash
$QCC methods.check --input '{"topic":<tests/fixtures/e06_reasoning.json 的 topic>}'
```

预期：相关系数被保留为假设并建议现场/工程验证（相关性不单独确认因果）；
未关联已验证要因的对策列为 `link_gaps`；`evidence_sufficient=false`，不因表格已填判为方法完整。

## 示例 3：工作语言下一步建议

```bash
$QCC methods.recommend --input '{"topic":{},"gaps":[{"stage":"baseline","missing":["baseline"]}]}'
# 返回：question / recommended_method / reason / required_inputs / expected_output
# 前提不足时 if_insufficient 指出不适用原因与补充方案，不伪造已执行活动
```

## 示例 4：补证任务与新证据关闭

```bash
$QCC methods.gaps --input '{"gaps":[{"stage":"baseline","missing":["baseline"]}]}'   # 生成待办
$QCC methods.update_gaps --input '{"topic":<含 tasks 的档案>,
  "new_evidence":[{"fact_key":"baseline","supports":true,"verification_id":"v-01"}]}'
# 预期：t1 关闭且保留 closure_basis=v-01；其它缺口仍在；缺口未解决可继续形成明确草稿
```

## 规则适配说明

- 正式评奖条目、依据与适用范围作为**规则包新版本**接入，不改变交付流程。
- 通用方法参考明确标注，不与部门初始要求或官方细则混为一项。
- 统计方法前提不满足时指出不适用原因并建议补充数据或换验证方式。

## 验证点（4.4）

示例说明输入、推荐理由、产物和判断；补写材料不会把未执行活动标为已发生。
