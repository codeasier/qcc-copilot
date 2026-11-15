# 收益口径与成本归属说明（5.4 / US04 / E04–E05）

> 收益走确定性工具，输出公式、输入、单位、结果、假设与底稿；用户可从底稿独立重算。
> 不要求所有价值都换算成人天。

## 公式与口径

```
毛节省人工小时 = Σ[可比事件数 ×（基线人工小时 − 改善后人工小时）]
净节省人工小时 = 毛节省 − 归属观察期的建设/运行/维护人工小时
净节省人天     = 净节省人工小时 / 每人天工时
```

- 事件、周期、适用范围须可比；工时换算参数（`hours_per_person_day`）显式记录。
- 等待/排队/机器运行时间不自动折算人力；净收益可为负；成本一次归集或摊销方式记录在 `cost_attribution`。
- 同一事件/团队/收益不重复计入；`event_ids` 提供时按标识去重。
- 零分母返回不可计算及原因，不输出无穷值或误导百分比。

## 示例 1：可复算正/负收益（E05，独立参考值）

```bash
export QCC="PYTHONPATH=<包>/src python3 -m qcc_copilot"
$QCC benefit.compute --input '{"metric":{
  "scenario":"measured","event_count":40,"baseline":0.5,"improved":0.25,"unit":"hours",
  "time_kind":"human_operation","hours_per_person_day":8,"attributable_cost_hours":2}}'
```

预期（与 `tests/fixtures/expected_values.json` 的人工核算一致）：
`gross_hours=10`、`net_hours=8`、`net_person_days=1`，`worksheet` 给出逐行重算。

把 `attributable_cost_hours` 改为 `12`：`net_hours=-2`、`net_person_days=-0.25`，负收益不截断为零。

## 示例 2：缺基线 / 不可比 / 单位 / 等待（E04）

```bash
$QCC benefit.compute --input '{"metric":{"improved":0.25,"unit":"hours","event_count":10}}'
# 缺基线：computable=false，gaps 含 baseline，附 fillable_model
$QCC benefit.compute --input '{"metric":{"baseline":60,"improved":20,"unit":"minutes","event_count":10,"time_kind":"waiting"}}'
# 仅等待缩短：labor_benefit_computable=false，present_as=等待/交付周期改善
$QCC benefit.ratio --input '{"numerator":5,"denominator":0}'
# 零分母：computable=false，reason 含 denominator
```

## 示例 3：实测/估算/预测分离（5.3）

```bash
$QCC benefit.separate --input '{"measured":<上方 calculation>,"extrapolation":{"assumed_teams":3,"assumed_events_per_team":40}}'
# 预期：forward_looking_not_merged=true，预测范围/频次假设/限制单列，不并入 measured_total
```

## 非人力价值示例（5.4，不虚构人天换算）

```bash
$QCC benefit.nonlabor --input '{"metric":{"name":"验证覆盖率","numerator":85,"denominator":100,"unit":"percent"}}'
# 预期：按覆盖率口径展示 value=0.85 / percent=85，person_day_conversion=null
```

质量、覆盖率、故障率、周期等指标按原口径说明价值；无可靠人力换算依据时不虚构人天收益。

## 成本归属说明

建设/运行/维护人工成本通过 `attributable_cost_hours` 计入，可为 0 或使净收益为负；
`cost_attribution` 记录 `one_time_in_observation_period` 或摊销方式。工具不假装运行未配置的统计检验。

## 验证点（5.4）

用户可从底稿逐行重算 10/8/1 与 -2/-0.25；覆盖率等价值无需虚构人天换算。
