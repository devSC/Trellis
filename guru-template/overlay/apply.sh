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
  flutter) SPEC_NAME="guru-flutter-client"; WF_NAME="guru-client"; ANALYZE_CMD="flutter analyze"; LAYERS="flutter service shared"; SKILL_GLOBS="client-* flutter-implementation-guru-*"; GRILL_SKILL="client-grill"; XTRA_HOOKS="block-l10n-sync.sh" ;;
  go)      SPEC_NAME="guru-go-backend";     WF_NAME="guru-go";     ANALYZE_CMD="go build ./... && go vet ./..."; LAYERS="backend shared"; SKILL_GLOBS="go-*"; GRILL_SKILL="go-design-grill"; XTRA_HOOKS="" ;;
  ios)     SPEC_NAME="guru-ios-native";     WF_NAME="guru-ios";    ANALYZE_CMD="xcodebuild build -quiet || swift build"; LAYERS="ios shared"; SKILL_GLOBS="ios-*"; GRILL_SKILL="ios-design-grill"; XTRA_HOOKS="" ;;
  h5)      SPEC_NAME="guru-h5-web";         WF_NAME="guru-h5";     ANALYZE_CMD="pnpm exec tsc --noEmit"; LAYERS="frontend backend shared"; SKILL_GLOBS="h5-*"; GRILL_SKILL="h5-design-grill"; XTRA_HOOKS="" ;;
  *) echo "ERROR: 未知平台 '$PLATFORM'（支持 flutter|go|ios|h5）"; exit 1 ;;
esac
[ -d "$ROOT/specs/$SPEC_NAME" ] || { echo "ERROR: spec 包不存在: specs/${SPEC_NAME}（先 pnpm -C packages/cli sync:guru 或确认 guru-template/specs/）"; exit 1; }
BOOTSTRAP_PRD="$HERE/bootstrap/${PLATFORM}-bootstrap-prd.md"

# guru-managed skill 全集（剪枝白名单：只删这些里的"非本平台"项，绝不碰用户自有/官方 trellis-* skill）
GURU_SKILLS="$(ls -d "$HERE"/agents-skills/*/ 2>/dev/null | xargs -n1 basename)"
# 平台无关 shared skill（每平台都装、不剪）：需求三件套被所有 workflow 的 Phase1(需求) 硬前置依赖。
SHARED_SKILLS="requirement-doc-standard requirement-writing requirement-review"
# skill 名是否该装：shared 始终装；否则按当前平台 SKILL_GLOBS 任一 glob 匹配。
skill_in_scope() {
  local n="$1" g
  case " $SHARED_SKILLS " in *" $n "*) return 0 ;; esac
  for g in $SKILL_GLOBS; do
    # shellcheck disable=SC2254
    case "$n" in $g) return 0 ;; esac
  done
  return 1
}

echo "== guru overlay 装配 → ${TARGET} （平台: ${PLATFORM} → spec=${SPEC_NAME} workflow=${WF_NAME}）=="

# 1) skills → .agents/skills/（装本平台集合 + shared 需求三件套，剪枝他平台 guru skill）
mkdir -p "$TARGET/.agents/skills"
agent_skill_n=0
# 单遍历 guru-managed 全集：属本平台或 shared → rm-then-cp 刷新装；否则剪枝（不碰用户自有/官方 trellis-*）
for gs in $GURU_SKILLS; do
  if skill_in_scope "$gs"; then
    rm -rf "$TARGET/.agents/skills/$gs"
    mkdir -p "$TARGET/.agents/skills/$gs"
    cp -R "$HERE/agents-skills/$gs/." "$TARGET/.agents/skills/$gs/"
    agent_skill_n=$((agent_skill_n + 1))
  else
    rm -rf "$TARGET/.agents/skills/$gs"
  fi
done
echo "  skills ×${agent_skill_n} → .agents/skills/（${PLATFORM} 平台 + shared 需求三件套）"

# 2) gate + after_create → .trellis/scripts/guru/
mkdir -p "$TARGET/.trellis/scripts/guru"
cp "$HERE/verify/guru_gate.py" "$HERE/hooks/guru_after_create.py" "$TARGET/.trellis/scripts/guru/"
chmod +x "$TARGET/.trellis/scripts/guru/"*.py
echo "  scripts: guru_gate.py, guru_after_create.py → .trellis/scripts/guru/"

# 3) 平台 hooks（Claude）+ trellis-local：只装共享 + 本平台专属 + 平台化 grill-nudge
mkdir -p "$TARGET/.claude/hooks" "$TARGET/.claude/skills/trellis-local"
SHARED_HOOKS="block-legacy-dirs.sh block-sanctioned-tlds.sh block-unconfirmed-start.sh"
INSTALLED_HOOKS="$SHARED_HOOKS grill-nudge.sh $XTRA_HOOKS"
# 剪枝：删目标里 guru-managed 但不属当前平台的旧 hook（含历史名 client-grill-nudge.sh、非 flutter 的 block-l10n-sync.sh）
GURU_HOOKS="$(ls "$HERE"/hooks/platform/*.sh 2>/dev/null | xargs -n1 basename) client-grill-nudge.sh"
for gh in $GURU_HOOKS; do
  case " $INSTALLED_HOOKS " in *" $gh "*) ;; *) rm -f "$TARGET/.claude/hooks/$gh" ;; esac
done
# 装共享 + 平台专属 hook
for h in $SHARED_HOOKS $XTRA_HOOKS; do
  cp "$HERE/hooks/platform/$h" "$TARGET/.claude/hooks/$h"
done
# grill-nudge 平台化：占位符替换成本平台 grill skill 名（flutter→client-grill、h5→h5-design-grill…）
sed "s/__GRILL_SKILL__/${GRILL_SKILL}/g" "$HERE/hooks/platform/grill-nudge.sh" > "$TARGET/.claude/hooks/grill-nudge.sh"
chmod +x "$TARGET/.claude/hooks/"*.sh
cp "$HERE/trellis-local/SKILL.md" "$TARGET/.claude/skills/trellis-local/"
echo "  hooks(platform): ${INSTALLED_HOOKS} + trellis-local"

# 4) 平台 skill 镜像（Claude Code 只读 .claude/skills；Codex 等读 .agents/skills）
MIRROR_SCRIPT="$TARGET/scripts/sync_platform_skills.py"
USED_PROJECT_MIRROR=0
if [ -f "$MIRROR_SCRIPT" ]; then
  # 项目自带镜像系统（如 himora）是该项目平台镜像的权威，交给它统一处理
  python3 "$MIRROR_SCRIPT" --sync --root "$TARGET"
  USED_PROJECT_MIRROR=1
  echo "  platform mirror: 项目镜像脚本 --sync 完成"
else
  # 单遍历 guru-managed 全集：属本平台或 shared → 镜像刷新；否则剪枝
  claude_skill_n=0
  for gs in $GURU_SKILLS; do
    if skill_in_scope "$gs"; then
      rm -rf "$TARGET/.claude/skills/$gs"
      mkdir -p "$TARGET/.claude/skills/$gs"
      cp -R "$HERE/agents-skills/$gs/." "$TARGET/.claude/skills/$gs/"
      claude_skill_n=$((claude_skill_n + 1))
    else
      rm -rf "$TARGET/.claude/skills/$gs"
    fi
  done
  echo "  platform mirror: skills ×${claude_skill_n} → .claude/skills/（${PLATFORM} 平台 + shared）"
fi

# 5) Claude settings.json hooks 接线（自动幂等合并：按 matcher 定位、按 command 去重，保留用户既有内容）
python3 - "$TARGET" "$HERE/config-snippets/claude-settings.hooks.json" "$INSTALLED_HOOKS" <<'PYEOF'
import json, os, re, sys
target_root, snippet_path = sys.argv[1], sys.argv[2]
installed_hooks = set(sys.argv[3].split()) if len(sys.argv) > 3 else None
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
        # 只注册 command 指向"已安装" hook 脚本的条目；漏装的 hook 不注册（避免 settings 悬空引用、触发时跑不存在脚本）
        if installed_hooks is not None:
            kept = []
            for h in entry.get("hooks", []):
                m = re.search(r"([A-Za-z0-9_.-]+\.sh)", h.get("command", "") if isinstance(h, dict) else "")
                if m and m.group(1) not in installed_hooks:
                    continue
                kept.append(h)
            if not kept:
                continue
            entry = {**entry, "hooks": kept}
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

# 7.5) by-layer 项目 spec 骨架 + bootstrap 任务接线
# 平台切换检测：.trellis/spec 下若有非当前平台、非方法学的层目录（前一平台残留），
# guru_after_create 会把它误注入后续任务基线（混入他平台上下文）→ 警告（不自动删，
# 用户可能有意保留多平台；如确属残留请手动归档/迁移）。
for D in "$TARGET/.trellis/spec"/*/; do
  [ -d "$D" ] || continue
  name="$(basename "$D")"
  case " $LAYERS harness conventions guides " in
    *" $name "*) ;;
    *) echo "  by-layer: ⚠ 检测到非当前平台层 spec/$name/（疑似前一平台残留，后续任务可能误加载，请确认是否归档/迁移）" ;;
  esac
done
# by-layer 空骨架随 spec 包由 `trellis init -t` 装入 .trellis/spec/<layer>/；此处兜底：
# 缺失则从 spec 包补装（不覆盖已被 bootstrap 填实的内容——目录已存在就跳过）。
mkdir -p "$TARGET/.trellis/spec"   # 非标准 target 可能有 .trellis 无 spec，先建父目录免 cp -R 失败
for L in $LAYERS; do
  # 缺失、或目录存在但为空（被外部清空 / 未填）都补装骨架；已被 bootstrap 填实(非空)的保留不覆盖。
  if [ -d "$SPEC_SRC/$L" ] && { [ ! -d "$TARGET/.trellis/spec/$L" ] || [ -z "$(ls -A "$TARGET/.trellis/spec/$L" 2>/dev/null)" ]; }; then
    rm -rf "$TARGET/.trellis/spec/$L"
    cp -R "$SPEC_SRC/$L" "$TARGET/.trellis/spec/$L"
    echo "  by-layer: 补装 spec/$L/（骨架）"
  fi
done
# bootstrap prd：init 生成的 native 版指向 guru 不安装的 backend/frontend（错配）；
# 覆盖成 guru 平台感知版（引导 agent 扫真实项目填 by-layer + conventions 槽位）。
BOOT_DIR="$TARGET/.trellis/tasks/00-bootstrap-guidelines"
# 写最小 task.json（对齐 init 的 24 字段）；新建任务、或目录已存在但缺 task.json 时复用。
write_boot_task_json() {
  local dev; dev="$(cat "$TARGET/.trellis/.developer" 2>/dev/null || echo guru)"
  python3 - "$BOOT_DIR" "$dev" "$PLATFORM" "$LAYERS" "$(date +%F)" <<'PYEOF'
import json, os, sys
boot_dir, dev, platform, layers, today = sys.argv[1:6]
related = [f".trellis/spec/{l}/" for l in layers.split()] + [".trellis/spec/conventions/project-conventions.md"]
task = {
    "id": "00-bootstrap-guidelines", "name": "00-bootstrap-guidelines",
    "title": "Bootstrap Guidelines",
    "description": "Fill in project development guidelines for AI agents",
    "status": "in_progress", "dev_type": "docs", "scope": None, "package": None,
    "priority": "P1", "creator": dev, "assignee": dev,
    "createdAt": today, "completedAt": None, "branch": None, "base_branch": None,
    "worktree_path": None, "commit": None, "pr_url": None,
    "subtasks": [], "children": [], "parent": None,
    "relatedFiles": related,
    "notes": f"guru bootstrap task (overlay-created, {platform} project)",
    "meta": {},
}
with open(os.path.join(boot_dir, "task.json"), "w", encoding="utf-8") as fh:
    json.dump(task, fh, ensure_ascii=False, indent=2)
PYEOF
}
if [ -f "$BOOTSTRAP_PRD" ]; then
  if [ -d "$BOOT_DIR" ]; then
    # 部分 init 可能留下任务目录却缺 task.json → 补建，避免下游任务工具见到非法任务目录
    if [ ! -f "$BOOT_DIR/task.json" ]; then
      echo "  bootstrap: ⚠ task.json 缺失，补建任务元数据"
      write_boot_task_json
    fi
    if [ -f "$BOOT_DIR/prd.md" ] && cmp -s "$BOOTSTRAP_PRD" "$BOOT_DIR/prd.md"; then
      echo "  bootstrap: prd.md 已是 guru ${PLATFORM} 版（幂等跳过）"
    elif [ -f "$BOOT_DIR/prd.md" ] && grep -q guru "$BOOT_DIR/prd.md"; then
      # 已是 guru 版（用户可能已编辑 / 他平台 guru 版）：不覆盖在制内容，仅备份留痕 + 提示手动切换。
      # （native 版无 "guru" 标记，必被下面 else 覆盖以修正错配；guru 版才走这里保留。）
      backup="$(mktemp "$BOOT_DIR/prd.md.pre-guru.$(date +%Y%m%d%H%M%S).XXXXXX")"
      cp "$BOOT_DIR/prd.md" "$backup"
      echo "  bootstrap: prd.md 已是 guru 版（保留在制内容，不覆盖）；备份 → ${backup#$TARGET/}"
      echo "  bootstrap: 如需重置为 guru ${PLATFORM} 模板：cp $BOOTSTRAP_PRD ${BOOT_DIR#$TARGET/}/prd.md"
    else
      # native 错配版（无 "guru" 标记，指向 guru 不装的 backend/frontend）或无 prd：覆盖成 guru 版。
      # 有旧文件先 mktemp 备份（防同秒重复 apply 覆盖上一份备份）。
      if [ -f "$BOOT_DIR/prd.md" ]; then
        backup="$(mktemp "$BOOT_DIR/prd.md.pre-guru.$(date +%Y%m%d%H%M%S).XXXXXX")"
        cp "$BOOT_DIR/prd.md" "$backup"
        echo "  bootstrap: 备份 native prd.md → ${backup#$TARGET/}"
      fi
      cp "$BOOTSTRAP_PRD" "$BOOT_DIR/prd.md"
      echo "  bootstrap: prd.md → guru ${PLATFORM} 平台感知版（覆盖 native 错配）"
    fi
  else
    # init 未建该任务（非首次 init / 已 archive）。先查归档：已归档=用户做完过，绝不复活成 in_progress。
    archived="$(find "$TARGET/.trellis/tasks/archive" -mindepth 2 -maxdepth 2 -type d -name '00-bootstrap-guidelines' -print -quit 2>/dev/null || true)"
    if [ -n "$archived" ]; then
      echo "  bootstrap: 已归档（${archived#$TARGET/}），跳过重建（避免复活已完成任务）"
    else
      # 按需建最小骨架
      mkdir -p "$BOOT_DIR"
      cp "$BOOTSTRAP_PRD" "$BOOT_DIR/prd.md"
      write_boot_task_json
      echo "  bootstrap: init 未建任务 → 已创建 00-bootstrap-guidelines（guru ${PLATFORM}）"
    fi
  fi
else
  echo "  ⚠ bootstrap prd 缺失: $BOOTSTRAP_PRD（跳过 bootstrap 接线）"
fi

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