#!/usr/bin/env bash
# ============================================================================
# QCC AI 生态调研 · 可复现采集脚本
#
# 依赖: gh (GitHub CLI，需已认证；search API 限速 30 次/分钟)
# 用法:
#   ./collect.sh search    按 search-queries.txt 重跑全部关键词检索
#   ./collect.sh meta      抓取 repos-watchlist.txt 的仓库元数据
#   ./collect.sh readme    抓取 readme-priority.txt 的 README 原文
#   ./collect.sh all       全量重跑
#
# 说明: 搜索结果写入 evidence/search-raw/，元数据写入 data/repos-meta.tsv。
#       重跑会覆盖同名文件，请先备份需要保留的快照。
# ============================================================================
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
BASE="$(dirname "$HERE")"
RAW="${BASE}/evidence/search-raw"
READMES="${BASE}/evidence/readmes"
mkdir -p "$RAW" "$READMES"

SLEEP=2.2   # search API 限速 30/min，留余量

do_search() {
  local total=0
  while IFS='|' read -r q tag; do
    # 跳过注释与空行
    case "$q" in ''|'#'*) continue ;; esac
    [[ -z "${tag:-}" ]] && continue
    gh api -X GET search/repositories \
      -f q="$q" -f sort=stars -f order=desc -f per_page=30 \
      --jq '.total_count as $t | "TOTAL=\($t)", (.items[]|"\(.stargazers_count)\t\(.full_name)\t\(.language // "-")\t\(.pushed_at[0:10])\t\(.license.spdx_id // "-")\t\(.description // "" | gsub("[\n\t]";" ") | .[0:150])")' \
      > "${RAW}/${tag}.tsv" 2>&1
    echo "[search] ${tag}  <-  ${q}  ($(head -1 "${RAW}/${tag}.tsv"))"
    total=$((total + 1))
    sleep "$SLEEP"
  done < "${HERE}/search-queries.txt"
  echo "[search] 完成 ${total} 组"
}

do_meta() {
  : > "${HERE}/repos-meta.tsv"
  while IFS= read -r r; do
    case "$r" in ''|'#'*) continue ;; esac
    gh api "repos/$r" --jq '"\(.stargazers_count)\t\(.forks_count)\t\(.language // "-")\t\(.license.spdx_id // "-")\t\(.created_at[0:10])\t\(.pushed_at[0:10])\t\(.size)\t\(.open_issues_count)\t\(.topics|join(","))\t\(.archived)\t\(.full_name)\t\(.description // ""|gsub("[\n\t]";" ")|.[0:200])"' \
      >> "${HERE}/repos-meta.tsv" 2>/dev/null
    echo "[meta] $r"
  done < "${HERE}/repos-watchlist.txt"
  echo "[meta] 完成 $(grep -c . "${HERE}/repos-meta.tsv") 条"
}

do_readme() {
  while IFS= read -r r; do
    case "$r" in ''|'#'*) continue ;; esac
    local out="${READMES}/$(echo "$r" | tr '/' '_').md"
    local ok=0
    for f in README.md readme.md README.MD README.rst; do
      if gh api "repos/$r/contents/$f" -H "Accept: application/vnd.github.raw" > "$out" 2>/dev/null \
         && [ -s "$out" ] && ! head -c 60 "$out" | grep -q '"message"'; then
        ok=1; break
      fi
    done
    if [ "$ok" = "1" ]; then
      echo "[readme] OK $r ($(wc -l < "$out" | tr -d ' ') 行)"
    else
      rm -f "$out"; echo "[readme] MISS $r"
    fi
  done < "${HERE}/readme-priority.txt"
}

case "${1:-help}" in
  search) do_search ;;
  meta)   do_meta ;;
  readme) do_readme ;;
  all)    do_search; do_meta; do_readme ;;
  *) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//' ;;
esac
