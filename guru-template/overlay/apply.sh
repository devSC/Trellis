#!/usr/bin/env bash
set -euo pipefail
# guru-template overlay 安装器：装配官方 init -t/--workflow 覆盖不到的部分。
# 用法: ./apply.sh <目标项目路径>
# 前提: 目标项目已 trellis init（存在 .trellis/）并已装 guru spec（-t guru-flutter-client）。

HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:?用法: apply.sh <目标项目路径>}"
TARGET="$(cd "$TARGET" && pwd)"
[ -d "$TARGET/.trellis" ] || { echo "ERROR: $TARGET 不是 Trellis 项目（缺 .trellis/），先 trellis init"; exit 1; }

echo "== guru overlay 装配 → $TARGET =="

# 1) client-* skills → .agents/skills/
mkdir -p "$TARGET/.agents/skills"
for s in "$HERE"/agents-skills/*/; do
  name="$(basename "$s")"
  mkdir -p "$TARGET/.agents/skills/$name"
  cp "$s/SKILL.md" "$TARGET/.agents/skills/$name/"
  echo "  skill: $name"
done

# 2) gate + after_create → .trellis/scripts/guru/
mkdir -p "$TARGET/.trellis/scripts/guru"
cp "$HERE/verify/guru_gate.py" "$HERE/hooks/guru_after_create.py" "$TARGET/.trellis/scripts/guru/"
chmod +x "$TARGET/.trellis/scripts/guru/"*.py
echo "  scripts: guru_gate.py, guru_after_create.py → .trellis/scripts/guru/"

# 3) 平台 hooks（Claude）
mkdir -p "$TARGET/.claude/hooks" "$TARGET/.claude/skills/trellis-local"
cp "$HERE"/hooks/platform/*.sh "$TARGET/.claude/hooks/"
chmod +x "$TARGET/.claude/hooks/"*.sh
cp "$HERE/trellis-local/SKILL.md" "$TARGET/.claude/skills/trellis-local/"
echo "  hooks(platform) ×$(ls "$HERE"/hooks/platform/*.sh | wc -l | tr -d ' ') + trellis-local"

# 4) config 合并（幂等：marker 检测）
python3 - "$TARGET" <<'PYEOF'
import os, sys
t = sys.argv[1]
MARK = "# >>> guru-overlay >>>"
END = "# <<< guru-overlay <<<"

def merge(path, block, create_header=""):
    cur = open(path, encoding="utf-8").read() if os.path.isfile(path) else create_header
    if MARK in cur:
        import re
        cur = re.sub(rf"{MARK}.*?{END}\n?", "", cur, flags=re.S)
    cur = cur.rstrip() + "\n\n" + MARK + "\n" + block.strip() + "\n" + END + "\n"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(cur)
    print(f"  merged: {os.path.relpath(path, t)}")

merge(os.path.join(t, ".trellis", "worktree.yaml"),
"""verify:
  - "python3 .trellis/scripts/guru/guru_gate.py auto"
  - "flutter analyze"
  # - "dart run custom_lint"   # guru_lints 建成后启用""")

merge(os.path.join(t, ".trellis", "config.yaml"),
"""hooks:
  after_create:
    - "python3 .trellis/scripts/guru/guru_after_create.py\"""")
PYEOF

echo ""
echo "== 装配完成。必做收尾 =="
echo "1) 项目约定：按模板填 $TARGET/.trellis/spec/conventions/project-conventions.md（或从 seek/calorie 取值复制改名）"
echo "2) SLOT-12：填 $TARGET/.claude/hooks/block-legacy-dirs.sh 的 LEGACY_PATTERNS"
echo "3) Claude hooks：合并 $HERE/config-snippets/claude-settings.hooks.json → $TARGET/.claude/settings.json"
echo "4) 注意：worktree.yaml/config.yaml 用 guru-overlay marker 块追加；若同文件已有同名键（verify:/hooks:）请人工合并去重"
