#!/usr/bin/env bash
# PreToolUse(Write)：拦截在老目录新建文件（golden-path §10 / 项目约定 SLOT-12）。
# 安装时按目标项目 project-conventions SLOT-12 填写 LEGACY_PATTERNS（grep -E 语法，| 分隔）。
# 示例 calorie: LEGACY_PATTERNS='lib/ui/pages/|lib/data/repositories/'
# 示例 seek:    LEGACY_PATTERNS='lib/domain/|lib/infrastructure/|lib/application/'
LEGACY_PATTERNS=''
[ -z "$LEGACY_PATTERNS" ] && exit 0
INPUT=$(cat)
FILE_PATH=$(printf '%s' "$INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*:[[:space:]]*"//; s/"$//')
if printf '%s' "$FILE_PATH" | grep -qE "$LEGACY_PATTERNS"; then
  echo "BLOCKED: $FILE_PATH 位于老目录（SLOT-12 禁止新建）。新代码请进 SLOT-02 的 canonical 目录；确属维护存量文件请用户确认后操作。" >&2
  exit 2
fi
exit 0
