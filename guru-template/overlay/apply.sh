#!/usr/bin/env bash
set -euo pipefail
# guru-template overlay 安装/升级器：装配官方 init -t/--workflow 覆盖不到的部分，
# 并负责 guru 定制内容（workflow/harness SSOT/skills/hooks/settings 接线）的后续升级刷新。
# 用法: ./apply.sh <目标项目路径>
# 前提: 目标项目已 trellis init（存在 .trellis/）。幂等：重复执行不产生额外变化。
#
# 边界（本脚本不做）：
# - CLI core 脚本（task.py 等）：归 trellis update 的 hash 三方合并管理，这里只检测依赖并警告；
# - .codex/skills 项目级内容（如 guru-ai-guides 的 requirement-* 技能）：项目自有，入项目 git 管理；
# - AGENTS.md 项目自有区块。

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"   # guru-template/
TARGET="${1:?用法: apply.sh <目标项目路径>}"
TARGET="$(cd "$TARGET" && pwd)"
[ -d "$TARGET/.trellis" ] || { echo "ERROR: $TARGET 不是 Trellis 项目（缺 .trellis/），先 trellis init"; exit 1; }

# 平台选择（第二位置参数，默认 flutter）：决定 spec 包 / workflow / verify analyze 命令。
PLATFORM="${2:-flutter}"
case "$PLATFORM" in
  flutter) SPEC_NAME="guru-flutter-client"; WF_NAME="guru-client"; ANALYZE_CMD="flutter analyze" ;;
  go)      SPEC_NAME="guru-go-backend";     WF_NAME="guru-go";     ANALYZE_CMD="go build ./... && go vet ./..." ;;
  ios)     SPEC_NAME="guru-ios-native";     WF_NAME="guru-ios";    ANALYZE_CMD="xcodebuild build -quiet || swift build" ;;
  h5)      SPEC_NAME="guru-h5-web";         WF_NAME="guru-h5";     ANALYZE_CMD="pnpm exec tsc --noEmit" ;;
  *) echo "ERROR: 未知平台 '$PLATFORM'（支持 flutter|go|ios|h5）"; exit 1 ;;
esac
[ -d "$ROOT/specs/$SPEC_NAME" ] || { echo "ERROR: spec 包不存在: specs/${SPEC_NAME}（先 pnpm -C packages/cli sync:guru 或确认 guru-template/specs/）"; exit 1; }

echo "== guru overlay 装配 → ${TARGET} （平台: ${PLATFORM} → spec=${SPEC_NAME} workflow=${WF_NAME}）=="

# 1) skills → .agents/skills/（共享真源）
mkdir -p "$TARGET/.agents/skills"
for s in "$HERE"/agents-skills/*/; do
  name="$(basename "$s")"
  # 重装刷新语义：先清空再整目录拷贝（SKILL.md + references/），避免模板中已删除/改名的文件残留
  rm -rf "$TARGET/.agents/skills/$name"
  mkdir -p "$TARGET/.agents/skills/$name"
  cp -R "$s"/. "$TARGET/.agents/skills/$name/"
done
echo "  skills ×$(ls -d "$HERE"/agents-skills/*/ | wc -l | tr -d ' ') → .agents/skills/"

# 2) gate + after_create → .trellis/scripts/guru/
mkdir -p "$TARGET/.trellis/scripts/guru"
cp "$HERE/verify/guru_gate.py" "$HERE/hooks/guru_after_create.py" "$TARGET/.trellis/scripts/guru/"
chmod +x "$TARGET/.trellis/scripts/guru/"*.py
echo "  scripts: guru_gate.py, guru_after_create.py → .trellis/scripts/guru/"

# 3) 平台 hooks（Claude）+ trellis-local
mkdir -p "$TARGET/.claude/hooks" "$TARGET/.claude/skills/trellis-local"
cp "$HERE"/hooks/platform/*.sh "$TARGET/.claude/hooks/"
chmod +x "$TARGET/.claude/hooks/"*.sh
cp "$HERE/trellis-local/SKILL.md" "$TARGET/.claude/skills/trellis-local/"
echo "  hooks(platform) ×$(ls "$HERE"/hooks/platform/*.sh | wc -l | tr -d ' ') + trellis-local"

# 4) 平台 skill 镜像（Claude Code 只读 .claude/skills；Codex 等读 .agents/skills）
MIRROR_SCRIPT="$TARGET/scripts/sync_platform_skills.py"
USED_PROJECT_MIRROR=0
if [ -f "$MIRROR_SCRIPT" ]; then
  # 项目自带镜像系统（如 himora）是该项目平台镜像的权威，交给它统一处理
  python3 "$MIRROR_SCRIPT" --sync --root "$TARGET"
  USED_PROJECT_MIRROR=1
  echo "  platform mirror: 项目镜像脚本 --sync 完成"
else
  for s in "$HERE"/agents-skills/*/; do
    name="$(basename "$s")"
    rm -rf "$TARGET/.claude/skills/$name"
    mkdir -p "$TARGET/.claude/skills/$name"
    cp -R "$s"/. "$TARGET/.claude/skills/$name/"
  done
  echo "  platform mirror: skills 字节镜像 → .claude/skills/"
fi

# 5) Claude settings.json hooks 接线（自动幂等合并：按 matcher 定位、按 command 去重，保留用户既有内容）
python3 - "$TARGET" "$HERE/config-snippets/claude-settings.hooks.json" <<'PYEOF'
import json, os, sys
target_root, snippet_path = sys.argv[1], sys.argv[2]
settings_path = os.path.join(target_root, ".claude", "settings.json")
snippet = json.load(open(snippet_path, encoding="utf-8"))
if os.path.isfile(settings_path):
    try:
        settings = json.load(open(settings_path, encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  ERROR: .claude/settings.json 非法 JSON，跳过自动合并（请人工处理）：{e}", file=sys.stderr)
        sys.exit(1)
else:
    settings = {}
if not isinstance(settings, dict):
    print("  ERROR: .claude/settings.json 根节点必须是对象", file=sys.stderr)
    sys.exit(1)
hooks = settings.setdefault("hooks", {})
if not isinstance(hooks, dict):
    print("  ERROR: .claude/settings.json 的 hooks 必须是对象", file=sys.stderr)
    sys.exit(1)
added = 0
for event, entries in snippet.get("hooks", {}).items():
    cur = hooks.setdefault(event, [])
    if not isinstance(cur, list):
        print(f"  ERROR: .claude/settings.json 的 hooks.{event} 必须是数组", file=sys.stderr)
        sys.exit(1)
    for entry in entries:
        existing = next((e for e in cur if isinstance(e, dict) and e.get("matcher") == entry.get("matcher")), None)
        if existing is None:
            cur.append(entry)
            added += len(entry.get("hooks", []))
        else:
            existing_hooks = existing.setdefault("hooks", [])
            if not isinstance(existing_hooks, list):
                print(f"  ERROR: .claude/settings.json matcher={entry.get('matcher')} 的 hooks 必须是数组", file=sys.stderr)
                sys.exit(1)
            cmds = {h.get("command") for h in existing_hooks if isinstance(h, dict)}
            for h in entry.get("hooks", []):
                if h.get("command") not in cmds:
                    existing_hooks.append(h)
                    added += 1
os.makedirs(os.path.dirname(settings_path), exist_ok=True)
open(settings_path, "w", encoding="utf-8").write(json.dumps(settings, ensure_ascii=False, indent=2) + "\n")
print(f"  settings.json: hooks 接线完成（新增 {added} 条，已有内容保留）")
PYEOF

# 6) workflow + SSOT 同步（升级通道：CLI update 不跟踪非 native workflow，spec/ 又是其保护路径）
cp "$ROOT/workflows/${WF_NAME}-workflow.md" "$TARGET/.trellis/workflow.md"
echo "  workflow: ${WF_NAME}-workflow.md → .trellis/workflow.md"
SPEC_SRC="$ROOT/specs/${SPEC_NAME}"
mkdir -p "$TARGET/.trellis/spec/guides" "$TARGET/.trellis/spec/conventions"
rm -rf "$TARGET/.trellis/spec/harness"
cp -R "$SPEC_SRC/harness" "$TARGET/.trellis/spec/harness"
cp "$SPEC_SRC/guides/"*.md "$TARGET/.trellis/spec/guides/"
cp "$SPEC_SRC/README.md" "$TARGET/.trellis/spec/"
# RECONCILE.md 平台特定（目前仅 flutter 提供）。切到不提供它的平台时清掉上一平台残留，
# 避免旧 reconcile 指引被 agent 继续消费。
if [ -f "$SPEC_SRC/RECONCILE.md" ]; then
  cp "$SPEC_SRC/RECONCILE.md" "$TARGET/.trellis/spec/"
else
  rm -f "$TARGET/.trellis/spec/RECONCILE.md"
fi
# conventions：项目取值（project-conventions.md）绝不覆盖；模板/样例/索引可刷新
for f in "$SPEC_SRC/conventions/"*.md; do
  base="$(basename "$f")"
  if [ "$base" = "project-conventions.md" ] && [ -f "$TARGET/.trellis/spec/conventions/project-conventions.md" ]; then
    continue
  fi
  cp "$f" "$TARGET/.trellis/spec/conventions/$base"
done
if [ -f "$TARGET/.trellis/spec/conventions/project-conventions.md" ]; then
  echo "  spec: harness/guides/README 已刷新；conventions/project-conventions.md 保留未动"
else
  echo "  spec: harness/guides/README 已刷新；⚠ conventions/project-conventions.md 缺失（按模板填写，见收尾）"
fi

# 7) config 合并（幂等：marker 检测）
python3 - "$TARGET" "$ANALYZE_CMD" <<'PYEOF'
import os, sys
t = sys.argv[1]
analyze = sys.argv[2] if len(sys.argv) > 2 else "flutter analyze"
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
f'''verify:
  - "python3 .trellis/scripts/guru/guru_gate.py auto"
  - "{analyze}"''')

merge(os.path.join(t, ".trellis", "config.yaml"),
"""hooks:
  after_create:
    - "python3 .trellis/scripts/guru/guru_after_create.py"
  # 阻断式：三道人工 Gate 确认缺一，task.py start 直接失败
  before_start:
    - "python3 .trellis/scripts/guru/guru_gate.py check\"""")
PYEOF

# 8) 装配自检（失败即非零退出；警告不阻塞）
echo ""
echo "== 装配自检 =="
FAIL=0

# 用 ast.parse 做语法检查：py_compile 会写 __pycache__ 副产物，破坏装配幂等性
if python3 -c "import ast,sys; [ast.parse(open(f,encoding='utf-8').read()) for f in sys.argv[1:]]" \
    "$TARGET/.trellis/scripts/guru/guru_gate.py" "$TARGET/.trellis/scripts/guru/guru_after_create.py" 2>/dev/null; then
  echo "  ✓ guru 脚本语法"
else
  echo "  ✗ guru 脚本语法检查失败"; FAIL=1
fi

if python3 - "$TARGET" <<'PYEOF'
import re, sys
content = open(f"{sys.argv[1]}/.trellis/workflow.md", encoding="utf-8").read()
TAG = re.compile(r"\[workflow-state:([A-Za-z0-9_-]+)\]\s*\n(.*?)\n\s*\[/workflow-state:\1\]", re.DOTALL)
blocks = TAG.findall(content)
oversize = [n for n, b in blocks if len(b.strip().encode("utf-8")) > 400]
sys.exit(0 if len(blocks) >= 6 and not oversize else 1)
PYEOF
then
  echo "  ✓ workflow breadcrumb（≥6 块且均 ≤400B）"
else
  echo "  ✗ workflow breadcrumb 解析/字节预算失败"; FAIL=1
fi

if grep -q "run_blocking_task_hooks" "$TARGET/.trellis/scripts/common/task_utils.py" 2>/dev/null; then
  echo "  ✓ core 支持 before_start 阻断钩子"
else
  printf '  \033[31m⚠ core 缺 before_start 支持：硬 Gate 不会拦截 task.py start！\033[0m\n'
  echo "    升级：npm i -g @devsc/trellis@guru && cd $TARGET && trellis update"
fi

if [ -f "$TARGET/scripts/check_workflow_compliance.py" ]; then
  if (cd "$TARGET" && python3 scripts/check_workflow_compliance.py >/dev/null 2>&1); then
    echo "  ✓ 项目 workflow 合规检查"
  else
    echo "  ✗ 项目 workflow 合规检查未通过（cd $TARGET && python3 scripts/check_workflow_compliance.py）"; FAIL=1
  fi
fi

if [ "$USED_PROJECT_MIRROR" = 1 ]; then
  if python3 "$MIRROR_SCRIPT" --check --root "$TARGET" >/dev/null 2>&1; then
    echo "  ✓ 平台 skill 镜像无漂移"
  else
    echo "  ✗ 平台 skill 镜像漂移（python3 scripts/sync_platform_skills.py --check）"; FAIL=1
  fi
fi

echo ""
if [ "$FAIL" != 0 ]; then
  echo "== 装配完成但自检存在失败项（见上 ✗），请处理后重跑 =="
  exit 1
fi
echo "== 装配完成，自检通过。剩余人工事项 =="
echo "1) 项目约定：确认 $TARGET/.trellis/spec/conventions/project-conventions.md 已按模板填写（缺失时从 .template/样例取值建立）"
echo "2) SLOT-12：填 $TARGET/.claude/hooks/block-legacy-dirs.sh 的 LEGACY_PATTERNS"
echo "3) Codex hooks：用户级 ~/.codex/config.toml 开 [features].hooks=true，并在 Codex /hooks 中 trust 本项目 hooks"
echo "4) 人工 Gate 通道：默认 strict（用户终端）；如需对话确认+agent 代跑，在 config.yaml 顶层加 guru.gate_mode: soft（见 workflow 机制节）"