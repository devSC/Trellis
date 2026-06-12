#!/usr/bin/env bash
# PreToolUse(Write|Edit|MultiEdit)：合规红线——制裁地区 TLD 域名引用（继承团队 compliance 红线）。
INPUT=$(cat)
PATTERN='https?://[^" ]*\.(ir|kp|sy|cu)([/" ]|$)'
if printf '%s' "$INPUT" | grep -qE "$PATTERN"; then
  echo "BLOCKED: 检测到疑似制裁地区 TLD（.ir/.kp/.sy/.cu）域名引用，违反合规红线（团队 AGENTS.md MUST）。如属误报请用户确认后操作。" >&2
  exit 2
fi
exit 0
