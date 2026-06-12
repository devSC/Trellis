#!/usr/bin/env bash
# PreToolUse(Bash)：拦截 l10n 同步脚本——双向写共享 Google Sheet，属人工受控步骤（golden-path §7）。
# 脚本名清单按目标项目 project-conventions SLOT-07 调整。
INPUT=$(cat)
BLOCKED='sync_translate\.sh|seek_l10_sync\.sh|l10n sync_translate'
if printf '%s' "$INPUT" | grep -qE "$BLOCKED"; then
  echo "BLOCKED: l10n 同步脚本属人工受控步骤（SLOT-07），agent 禁止自动执行。需要同步请提示用户手动运行。" >&2
  exit 2
fi
exit 0
