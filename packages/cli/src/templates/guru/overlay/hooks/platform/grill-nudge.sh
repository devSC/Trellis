#!/usr/bin/env bash
# PostToolUse(Write|Edit|MultiEdit)：prd/归属表草稿"成形"后提示 Domain Grill / review evidence 下一步。
# 平台旧名 skill 仅保留为 legacy wrapper，不再作为新 Gate 前置。
# 成形判定 = guru_gate 对应结构检查通过（半成品不打扰）；.grill-nudged-<artifact> 标记仅用于提示幂等
#（只提示一次，删除标记可重新触发）。真正 Gate 状态以 confirm 快照与 review_runs 为准。
# exit 2 的 stderr 会反馈给 agent（PostToolUse 不阻塞已完成的写入）。
INPUT=$(cat)
FP=$(printf '%s' "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*:[[:space:]]*"//; s/"$//')
case "$FP" in
  *".trellis/tasks/"*"/prd.md")    KIND=requirements; ART=prd ;;
  *".trellis/tasks/"*"/design.md") KIND=overview;     ART=design ;;
  *) exit 0 ;;
esac
# 锚定项目根：先 cd，再解析 TASK_DIR/MARK。GATE 是相对路径，且 file_path 可能是相对项目根的相对路径——
# 必须先 cd 到项目根，相对 TASK_DIR/MARK 才能被正确解析（否则 cwd 非项目根时相对 file_path 会漏判已有标记）。
# 与兄弟 hook block-unconfirmed-start.sh 一致，遵循「不依赖进程 cwd」不变量。
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
TASK_DIR=$(dirname "$FP")
MARK="$TASK_DIR/.grill-nudged-$ART"
[ -f "$MARK" ] && exit 0
GATE=".trellis/scripts/guru/guru_gate.py"
[ -f "$GATE" ] || exit 0
if python3 "$GATE" "$KIND" "$TASK_DIR" >/dev/null 2>&1; then
  touch "$MARK"
  if [ "$ART" = "prd" ]; then
    echo "📋 prd.md 已通过结构检查。按 workflow：先在需求发现内完成 Domain Grill（术语、边界、当前代码事实 vs 用户意图），再由用户确认 requirements。（本提示仅一次；删除 $MARK 可重新触发）" >&2
  else
    echo "📋 design.md 已通过结构检查。按 workflow：运行 guru_supervise.py overview/detail 或对应 review skill 写入 record-review；overview 不走 confirm，detail 双 clean 后再等用户确认。（本提示仅一次；删除 $MARK 可重新触发）" >&2
  fi
  exit 2
fi
exit 0
