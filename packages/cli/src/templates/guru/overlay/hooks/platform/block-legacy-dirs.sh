#!/usr/bin/env bash
# PreToolUse：拦截在老目录新建文件（golden-path §10 / 项目约定 SLOT-12）。双端通用脚本。
#   - Claude Code：matcher=Write，从 tool_input.file_path 取路径。
#   - Codex：matcher=apply_patch|Write，从 patch 文本的 "*** Add File: <path>" 取路径（仅新建，Update/Delete 不拦）。
# 安装时按目标项目 project-conventions SLOT-12 填写 LEGACY_PATTERNS（grep -E 语法，| 分隔）。
# 示例 calorie: LEGACY_PATTERNS='lib/ui/pages/|lib/data/repositories/'
# 示例 seek:    LEGACY_PATTERNS='lib/domain/|lib/infrastructure/|lib/application/'
LEGACY_PATTERNS=''
# 留空 = 该项目无老目录（SLOT-12 可显式留空，合规），拦截按设计不生效；非空才按 grep -E 拦截。
[ -z "$LEGACY_PATTERNS" ] && exit 0
INPUT=$(cat)
# Claude Write/Edit：tool_input.file_path 字段
FP=$(printf '%s' "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | sed 's/.*:[[:space:]]*"//; s/"$//')
# Codex apply_patch：patch 文本里的 "*** Add File: <path>"（仅新建才拦）
ADD=$(printf '%s' "$INPUT" | grep -oE '\*\*\* Add File: [^"\\]+' | sed 's/^\*\*\* Add File: //; s/[[:space:]]*$//')
HIT=$(printf '%s\n%s\n' "$FP" "$ADD" | grep -vE '^$' | grep -E "$LEGACY_PATTERNS" | head -1)
if [ -n "$HIT" ]; then
  echo "BLOCKED: $HIT 位于老目录（SLOT-12 禁止新建）。新代码请进 SLOT-02 的 canonical 目录；确属维护存量文件请用户确认后操作。" >&2
  exit 2
fi
exit 0
