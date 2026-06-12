#!/usr/bin/env bash
# PostToolUse(Write|Edit|MultiEdit)：prd/归属表草稿"成形"后自动提示加载 client-grill 拷问。
# 成形判定 = guru_gate 对应结构检查通过（半成品不打扰）；.grilled-<artifact> 标记幂等（只提示一次，
# 删除标记可重新触发）。exit 2 的 stderr 会反馈给 agent（PostToolUse 不阻塞已完成的写入）。
INPUT=$(cat)
FP=$(printf '%s' "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*:[[:space:]]*"//; s/"$//')
case "$FP" in
  *".trellis/tasks/"*"/prd.md")    KIND=requirements; ART=prd ;;
  *".trellis/tasks/"*"/design.md") KIND=overview;     ART=design ;;
  *) exit 0 ;;
esac
TASK_DIR=$(dirname "$FP")
MARK="$TASK_DIR/.grilled-$ART"
[ -f "$MARK" ] && exit 0
GATE=".trellis/scripts/guru/guru_gate.py"
[ -f "$GATE" ] || exit 0
if python3 "$GATE" "$KIND" "$TASK_DIR" >/dev/null 2>&1; then
  touch "$MARK"
  echo "📋 ${ART}.md 已通过结构检查（${KIND} Gate 口径）。按 workflow：送审前先加载 client-grill 拷问——对照 golden-path/项目约定/既有 BHV 磨术语、压测边界场景，决策当场固化进产物；拷问后再走对应 review 提交人工 Gate。（本提示仅一次；删除 $MARK 可重新触发）" >&2
  exit 2
fi
exit 0
