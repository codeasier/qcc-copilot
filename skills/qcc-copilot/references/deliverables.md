# 材料生成、企业模板替换与检查受限说明（7.6 / US07 / E09 / E10）

> 所有材料从**同一固定快照**编译，数字/单位/周期/结论/引用一致；只有大纲或文件生成失败不算 PPT 完成。

## 完整文件包导出（7.1 / 7.2）

```bash
export QCC="PYTHONPATH=<包>/src python3 -m qcc_copilot"
$QCC delivery.snapshot --input '{"workspace":"./p","topic_id":"t1"}'      # 得到 delivery_id
$QCC deliverable.compile --input '{"workspace":"./p","topic_id":"t1","delivery_id":"<id>"}'
```

产物在 `.qcc/t1/deliveries/<id>/`：

| 文件 | 内容 |
|---|---|
| `report.md` | 课题报告（含主张来源/支持状态） |
| `benefit.md` / `data_worksheet.md` | 收益说明与可复算底稿 |
| `reuse.md` | 复用说明（条件/资产/步骤/验证/维护/成本/限制） |
| `chart_data.json` / `chart.svg` | 图表结构化底稿与可视底稿 |
| `review.json` / `review_questions.md` | 独立三维语义检查 |
| `slides.json` | 可编辑逐页大纲 |
| `deck.pptx` | **真实 PPTX**：文字与表格可编辑（stdlib OOXML） |
| `manifest.json` | 文件清单 + 快照（课题修订/内容摘要/规则） |
| `check_record.json` | 由 `deliverable.verify` 写入的检查记录 |

- 生成期间只使用入口时捕获的快照；此后输入变化不会混入本包（仍标识实际使用的快照）。
- 仅有 `slides.json` 逐页文案而缺 `deck.pptx` 时，`verify` 的 `coverage` 失败，不算 PPT 交付完成。

## 企业模板替换（7.2）

- 主题：`src/qcc_copilot/resources/templates/neutral_theme.json`（颜色/字体/尺寸/可编辑声明）。
- 文本模板：`templates/*.tpl`（`{{placeholder}}` 由快照值填充）。
- 替换主题或模板文件即接入企业视觉资产，**不改变业务契约、交付快照与检查流程**；未配置的企业资产列为受限/未验证。

## 独立自检与状态（7.3 / 7.5 / E09）

```bash
$QCC deliverable.review --input '{"workspace":"./p","topic_id":"t1","delivery_id":"<id>"}'
# 预期：官方评分未配置时不生成分数/权重/获奖概率；findings 含 依据/问题/影响/建议/待补证

$QCC deliverable.verify --input '{"workspace":"./p","topic_id":"t1","delivery_id":"<id>"}'
$QCC deliverable.status --input '{"workspace":"./p","topic_id":"t1","delivery_id":"<id>"}'
```

- 缺证据、严重冲突或检查未通过 → `draft`，`premature_formal_export_blocked=true`。
- 核心主张已支持且全部检查通过 → 可 `review-ready`。
- 自检独立于起草；模型自检不等同官方评审通过。

## 检查受限说明（7.4 / E10）

`verify` 的四类检查及状态：

| 检查 | 通过条件 | 受限时 |
|---|---|---|
| 覆盖 | 全部必需文件存在 | 缺文件 → `failed` |
| 占位符 | 无 `{{...}}`/TODO/TBD | 检出 → `failed` 并定位文件行 |
| 可检测溢出 / 缺图 | 标题/正文长度、表格行数、图表数据点、PPTX 结构 | 超长或无数据点 → `failed` |
| 独立渲染 | macOS Quick Look 或 LibreOffice 实际打开 | 无渲染能力 → `not_run`，`overall` 不标 `passed` |

> 依赖缺失与检查未执行**不会**标为通过；仅检查文件存在或文案长度不等于渲染验证通过。
> Quick Look 成功只证明可打开并渲染，不证明逐页版式无缺陷，溢出/占位符/缺图由结构化检查负责。

验证样例可暴露缺陷：向 `report.md` 注入 `{{UNFILLED}}` 或清空 `chart_data.json` 数据点后重跑 `verify`，
对应检查变 `failed`，`status` 保持 `draft`。

## 验证点（7.6）

按说明可从样例导出完整文件包，核对 `manifest.json` 的快照与 `check_record.json` 的检查结果；
真实 PPTX 可打开、可检查、可修改，只有大纲不算完成。
