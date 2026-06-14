#!/usr/bin/env bash
# PreToolUse(Write|Edit|MultiEdit)：合规红线——制裁地区 TLD 域名引用（继承团队 compliance 红线）。
INPUT=$(cat)
# host 段用 [^/"? ]* 锚定（不跨第一个 / 或 ?，只看域名 authority、不进 path/query——避免误拦 path 里的
# .cu/.sy 文件名如 github.com/x/kernel.cu）；边界 [^a-z0-9.-] 覆盖 markdown )、逗号、] 等 host 侧常见收尾；
# grep -i 大小写不敏感（DNS 域名 .IR/.Ir 等价可解析）。
PATTERN='https?://[^/"? ]*\.(ir|kp|sy|cu)([^a-z0-9.-]|$)'
if printf '%s' "$INPUT" | grep -qiE "$PATTERN"; then
  echo "BLOCKED: 检测到疑似制裁地区 TLD（.ir/.kp/.sy/.cu）域名引用，违反合规红线（团队 AGENTS.md MUST）。如属误报请用户确认后操作。" >&2
  exit 2
fi
exit 0
