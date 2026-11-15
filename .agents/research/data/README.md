# data/ — 数据集与采集工具

本目录保存调研的**结构化数据**与**可复现采集脚本**，是主报告所有数字的来源。

## 文件说明

| 文件 | 内容 | 用法 |
|---|---|---|
| `repos-meta.tsv` | 69 个仓库的元数据快照（12 字段，见下） | 排序/筛选/复算统计 |
| `repos-watchlist.txt` | 69 个候选仓库全名清单（一行一个） | `collect.sh meta` 的输入 |
| `readme-priority.txt` | 精读优先级清单 | `collect.sh readme` 的输入 |
| `search-queries.txt` | 36 组检索参数（`query\|标签`） | `collect.sh search` 的输入 |
| `collect.sh` | 采集脚本（search / meta / readme / all） | 见下方"复现" |

## `repos-meta.tsv` 字段定义

制表符分隔，12 列，无表头。按 `stars` 降序排列即得热度榜。

| # | 字段 | 示例 | 说明 |
|---|---|---|---|
| 1 | `stars` | `3312` | 星标数 |
| 2 | `forks` | `210` | Fork 数 |
| 3 | `language` | `Python` | 主语言，`-` 表示未识别 |
| 4 | `license` | `MIT` | SPDX 标识，`-` 表示**无 License**（不可商用） |
| 5 | `created_at` | `2026-10-16` | 仓库创建日期 |
| 6 | `pushed_at` | `2026-11-15` | 最后推送日期（活跃度代理指标） |
| 7 | `size` | `6026` | 仓库体积（KB） |
| 8 | `open_issues` | `0` | 未关闭 Issue 数 |
| 9 | `topics` | `fmea,quality` | Topic 列表，逗号分隔 |
| 10 | `archived` | `false` | 是否已归档 |
| 11 | `full_name` | `owner/repo` | 仓库全名 |
| 12 | `description` | `...` | 仓库描述（已截断至 200 字符、去除换行） |

### 常用查询

```bash
# 按星标排序看 TOP 20
sort -t$'\t' -k1 -nr repos-meta.tsv | head -20 \
  | awk -F'\t' '{printf "%-6s %-55s %-10s %-11s %s\n",$1,$11,$3,$4,$6}'

# 无 License 的项目（商用风险）
awk -F'\t' '$4=="-"{print $1"\t"$11}' repos-meta.tsv | sort -nr

# 2026 年之后仍在更新的
awk -F'\t' '$6>="2026-06"{print $11"\t"$6}' repos-meta.tsv | sort -k2 -r

# 统计口径复算
echo "样本 $(wc -l < repos-meta.tsv) / 无License $(awk -F'\t' '$4=="-"' repos-meta.tsv | wc -l)"
```

## 复现

```bash
gh auth status        # 需已认证；search API 限速 30 次/分钟
./collect.sh search   # 36 组检索 → evidence/search-raw/*.tsv（约 90 秒）
./collect.sh meta     # 刷新 repos-meta.tsv
./collect.sh readme   # 抓 README → evidence/readmes/
./collect.sh all
```

> 重跑会覆盖快照。本次数据快照固定为 **2026-11-15**，star 数与提交数之后会漂移。

## 口径说明

- **"有效样本 69"** = watchlist 中能取到元数据的仓库数；另有 9 个仓库（制药 QMS 多智能体、Odoo QMS 模块等）在报告中列出但未纳入统计口径。
- **"无 License"** 指 GitHub API 未识别到 SPDX 许可（可能确实无 LICENSE 文件，也可能 README 里口头声明但未落地）——两种都按不可商用处理。
- **"活跃度"** 用 `pushed_at` 而非 `commits` 数；两者背离时（如 QCmaker 9 次提交却有 211 个文件），报告中会单独标注。
