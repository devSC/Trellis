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
GURU_SKILLS="$(ls -d "$HERE"/agents-skills/*/ 2>/dev/null | xargs -n1 basename || true)"
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

# skill 目录安装：rm-then-cp 刷新 + 清理 macOS/py 脏文件（.DS_Store/__pycache__ 不随 cp -R 泄漏进目标）
install_skill_dir() {  # $1=源目录（内容到末尾）  $2=目标目录
  rm -rf "$2"; mkdir -p "$2"
  cp -R "$1/." "$2/"
  find "$2" \( -name .DS_Store -o -name __pycache__ \) -exec rm -rf {} + 2>/dev/null || true
}

# 平台-项目类型一致性兜底：漏传/传错第二位置参数会静默装错平台（默认 flutter）。
# 检测明显的项目标志文件，与 PLATFORM 矛盾时警告（不硬失败：monorepo/特殊布局可能合法）。
detect_hint=""
if [ -f "$TARGET/pubspec.yaml" ]; then detect_hint="${detect_hint:+$detect_hint,}flutter"; fi
if [ -f "$TARGET/go.mod" ]; then detect_hint="${detect_hint:+$detect_hint,}go"; fi
if [ -f "$TARGET/Package.swift" ] || ls "$TARGET"/*.xcodeproj >/dev/null 2>&1; then detect_hint="${detect_hint:+$detect_hint,}ios"; fi
if [ -f "$TARGET/package.json" ] && [ ! -f "$TARGET/pubspec.yaml" ]; then detect_hint="${detect_hint:+$detect_hint,}h5"; fi
case ",${detect_hint}," in
  ,,) ;;                          # 无可识别标志（空/特殊项目）：不校验
  *",${PLATFORM},"*) ;;           # 一致
  *) echo "  ⚠ 平台校验：传入平台 '${PLATFORM}' 与检测到的项目类型（${detect_hint}）不符——确认第二位置参数是否传错（apply.sh <目标> <flutter|go|ios|h5>）" ;;
esac

echo "== guru overlay 装配 → ${TARGET} （平台: ${PLATFORM} → spec=${SPEC_NAME} workflow=${WF_NAME}）=="

# 1) skills → .agents/skills/（装本平台集合 + shared 需求三件套，剪枝他平台 guru skill）
mkdir -p "$TARGET/.agents/skills"
agent_skill_n=0
# 单遍历 guru-managed 全集：属本平台或 shared → rm-then-cp 刷新装；否则剪枝（不碰用户自有/官方 trellis-*）
for gs in $GURU_SKILLS; do
  if skill_in_scope "$gs"; then
    install_skill_dir "$HERE/agents-skills/$gs" "$TARGET/.agents/skills/$gs"
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
GURU_HOOKS="$(ls "$HERE"/hooks/platform/*.sh 2>/dev/null | xargs -n1 basename || true) client-grill-nudge.sh"
for gh in $GURU_HOOKS; do
  case " $INSTALLED_HOOKS " in *" $gh "*) ;; *) rm -f "$TARGET/.claude/hooks/$gh" ;; esac
done
# 装共享 + 平台专属 hook。block-legacy-dirs.sh 含用户必填的 SLOT-12（LEGACY_PATTERNS）：
# cp 模板刷新脚本主体，但回填用户既有的非空值——否则二次 apply 用模板空值覆盖、老目录拦截静默失效。
for h in $SHARED_HOOKS $XTRA_HOOKS; do
  prev_slot12=""
  if [ "$h" = "block-legacy-dirs.sh" ] && [ -f "$TARGET/.claude/hooks/$h" ]; then
    prev_slot12="$(grep -m1 '^LEGACY_PATTERNS=' "$TARGET/.claude/hooks/$h" 2>/dev/null || true)"
  fi
  cp "$HERE/hooks/platform/$h" "$TARGET/.claude/hooks/$h"
  if [ -n "$prev_slot12" ] && [ "$prev_slot12" != "LEGACY_PATTERNS=''" ] && [ "$prev_slot12" != 'LEGACY_PATTERNS=""' ]; then
    python3 - "$TARGET/.claude/hooks/$h" "$prev_slot12" <<'PYEOF'
import sys
path, prev = sys.argv[1], sys.argv[2]
lines = open(path, encoding="utf-8").read().splitlines(keepends=True)
for i, ln in enumerate(lines):
    if ln.startswith("LEGACY_PATTERNS="):
        lines[i] = prev + "\n"
        break
open(path, "w", encoding="utf-8").write("".join(lines))
PYEOF
    echo "  hooks: 保留用户既有 SLOT-12（block-legacy-dirs.sh 的 LEGACY_PATTERNS 未被模板空值覆盖）"
  fi
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
      install_skill_dir "$HERE/agents-skills/$gs" "$TARGET/.claude/skills/$gs"
      claude_skill_n=$((claude_skill_n + 1))
    else
      rm -rf "$TARGET/.claude/skills/$gs"
    fi
  done
  echo "  platform mirror: skills ×${claude_skill_n} → .claude/skills/（${PLATFORM} 平台 + shared）"
fi

# 4.5) 两个 skill 面双向对齐（修「换客户端就少一批 skill」）：
#   trellis init 只把引擎 skill（trellis-*）装进 --client 对应目录（如 --claude → .claude/skills），
#   但 Codex/本地 agent 客户端读 .agents/skills。§4 的镜像又只搬 guru skill。结果 trellis-* 只在
#   .claude/skills、读 .agents/skills 的客户端永远看不到它们。这里把两面对齐成同一并集（guru 平台 +
#   shared + 引擎 trellis-* + trellis-local + 用户自有），任意客户端读哪个目录都是完整集合。
#   guru 越界项已在 §1/§4 从两面同时剪掉、且并集只补「非 guru」项，故不会复活被裁剪的他平台 guru skill。
if [ "$USED_PROJECT_MIRROR" = 0 ]; then
  mkdir -p "$TARGET/.agents/skills" "$TARGET/.claude/skills"
  recon_n=0; drift_n=0
  put_skill() {  # $1=源 skill 目录  $2=目标 skill 目录：rm-then-cp + 清理脏文件
    rm -rf "$2"; mkdir -p "$2"; cp -R "$1." "$2/"
    find "$2" \( -name .DS_Store -o -name __pycache__ \) -exec rm -rf {} + 2>/dev/null || true
  }
  drift_dir() {  # $1=src skill 目录  $2=dst skill 目录 → 输出 src|dst|equal（按整棵子树最新文件 mtime，排除脏文件）
    python3 - "$1" "$2" <<'PY'
import os, sys
def newest(root):
    best = -1.0
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d != "__pycache__"]
        for n in fns:
            if n == ".DS_Store":
                continue
            try:
                best = max(best, os.stat(os.path.join(dp, n)).st_mtime)
            except OSError:
                pass
    return best
a, b = newest(sys.argv[1]), newest(sys.argv[2])
print("src" if a > b else "dst" if b > a else "equal")
PY
  }
  reconcile_skills() {  # $1=源 skills 目录  $2=目标 skills 目录
    # 把源里"非 guru"的 skill 对齐到目标：缺失→补；两面都有但内容漂移→以「整棵子树最新文件 mtime」
    # 较新一侧为权威覆盖较旧侧（不只看 SKILL.md/目录 mtime——多文件 skill 改内部文件不会 bump 二者，
    #   旧实现会漏同步且可能判反方向）。mtime 严格相等无法判向时按当前源侧优先同步并告警。
    #   diff 排除脏文件，避免"源带 .DS_Store / 目标已清理"造成的假漂移破坏幂等。反向调用处理另一方向。
    local sd nm dir
    [ -d "$1" ] || return 0
    for sd in "$1"/*/; do
      [ -d "$sd" ] || continue
      nm="$(basename "$sd")"
      case " $GURU_SKILLS " in *" $nm "*) continue ;; esac   # guru-managed 由 §1/§4 按平台权威管理，不在此并集
      if [ ! -d "$2/$nm" ]; then
        put_skill "$sd" "$2/$nm"; recon_n=$((recon_n + 1))
      elif ! diff -rq -x .DS_Store -x __pycache__ "$sd" "$2/$nm" >/dev/null 2>&1; then
        dir="$(drift_dir "$sd" "$2/$nm")"
        if [ "$dir" = src ]; then
          put_skill "$sd" "$2/$nm"; drift_n=$((drift_n + 1))
        elif [ "$dir" = equal ]; then
          put_skill "$sd" "$2/$nm"; drift_n=$((drift_n + 1))
          echo "  ⚠ skill 双面对齐: $nm 两面内容不同但最新 mtime 相等，按当前源侧优先同步——如方向有误请手动核对" >&2
        fi
        # dir=dst：目标侧更新，反向调用会处理（此处不动）
      fi
    done
  }
  reconcile_skills "$TARGET/.claude/skills" "$TARGET/.agents/skills"   # 引擎 trellis-* / trellis-local → .agents
  reconcile_skills "$TARGET/.agents/skills" "$TARGET/.claude/skills"   # .agents 侧用户自有 skill → .claude
  echo "  skill 双面对齐: 补齐 ×${recon_n} + 内容同步 ×${drift_n}（引擎 trellis-*/trellis-local/用户自有，两面一致）"
fi

# 5) Claude settings.json hooks 接线（自动幂等合并：按 matcher 定位、按 command 去重，保留用户既有内容）
python3 - "$TARGET" "$HERE/config-snippets/claude-settings.hooks.json" "$INSTALLED_HOOKS" "$GURU_HOOKS" <<'PYEOF'
import json, os, re, sys
target_root, snippet_path = sys.argv[1], sys.argv[2]
installed_hooks = set(sys.argv[3].split()) if len(sys.argv) > 3 else None
managed_hooks = set(sys.argv[4].split()) if len(sys.argv) > 4 else None
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
# 清理 guru-managed 但本平台未安装的悬空引用：切平台后 §3 已删该 hook 脚本，settings 不应再引用它
# （否则 PreToolUse 每次触发都跑一个不存在的脚本）。只动 guru-managed 集合内的引用，绝不碰用户自定义 hook。
removed = 0
if managed_hooks is not None and installed_hooks is not None:
    stale = managed_hooks - installed_hooks
    for event in list(hooks.keys()):
        entries = hooks.get(event)
        if not isinstance(entries, list):
            continue
        cleaned = []
        for entry in entries:
            if not isinstance(entry, dict):
                cleaned.append(entry)
                continue
            eh = entry.get("hooks")
            if isinstance(eh, list):
                kept = []
                dropped = 0
                for h in eh:
                    cmd = h.get("command", "") if isinstance(h, dict) else ""
                    # 锚定到 guru 项目命令形态 $CLAUDE_PROJECT_DIR/.claude/hooks/<name>：既避免误删 basename
                    # 同名但别处路径的用户 hook，也不误删指向 $HOME/.claude/hooks 的用户全局 hook
                    m = re.search(r'CLAUDE_PROJECT_DIR"?/\.claude/hooks/([A-Za-z0-9_.-]+\.sh)', cmd)
                    if m and m.group(1) in stale:
                        removed += 1
                        dropped += 1
                        continue   # 丢弃悬空 guru hook 引用
                    kept.append(h)
                # 仅当本轮确有 guru 悬空被剔除且导致该 entry 变空，才移除空壳；
                # 用户原本就空的 hooks 条目（占位）原样保留，不越界。
                if not kept and dropped > 0:
                    continue
                entry = {**entry, "hooks": kept}
            cleaned.append(entry)
        hooks[event] = cleaned
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
                m = re.search(r'CLAUDE_PROJECT_DIR"?/\.claude/hooks/([A-Za-z0-9_.-]+\.sh)', h.get("command", "") if isinstance(h, dict) else "")
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
print(f"  settings.json: hooks 接线完成（新增 {added} 条、清理悬空 {removed} 条，已有内容保留）")
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
# 切平台残留治理：先清掉目标里他平台的样例 *.project-conventions.md（与 RECONCILE.md 同等对待，避免
# go 项目里躺着 flutter 的 calorie/seek 样例孤儿）。project-conventions.md 无前缀、不被该 glob 匹配，
# 且下方循环显式保护，用户权威取值绝不受损。
rm -f "$TARGET/.trellis/spec/conventions/"*.project-conventions.md 2>/dev/null || true
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

# config.yaml 若在 marker 块外已有未注释的顶层 hooks: 键，guru 块注入的 hooks: 会与之形成重复顶层键，
# YAML last-wins 会静默吞掉用户的 after_*/before_* → 警告（不自动解析合并用户 YAML，避免误判其结构）。
_cfg_path = os.path.join(t, ".trellis", "config.yaml")
if os.path.isfile(_cfg_path):
    import re as _re
    _outside = _re.sub(rf"{MARK}.*?{END}\n?", "", open(_cfg_path, encoding="utf-8").read(), flags=_re.S)
    if _re.search(r"(?m)^hooks\s*:", _outside):
        sys.stderr.write(
            "  ⚠ config.yaml 在 guru marker 块外已有顶层 hooks: 键：guru 注入的 hooks"
            "(after_create/before_start) 会形成重复顶层键，YAML last-wins 将静默覆盖你的 "
            "after_*/before_* hook。请把你的 hook 手动并入 guru-overlay marker 块内（或确认无冲突）。\n")

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
  # .developer 是多行 key=value（name=.. / initialized_at=..）：只取 name= 值（对齐官方 get_developer）。
  # cat 全文会把整文件塞进 task.json 的 creator/assignee（嵌字面换行 + name= 前缀），破坏 task.py --mine 过滤。
  # || true：.developer 缺失时 sed 经 pipefail 返回非 0，裸赋值在 set -e 下会中止脚本；缺失则 fallback guru。
  local dev
  dev="$(sed -n 's/^name=//p' "$TARGET/.trellis/.developer" 2>/dev/null | head -1)" || true
  [ -n "$dev" ] || dev=guru
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
      # 已是 guru 版（用户可能已编辑 / 他平台 guru 版）：保留在制内容，不覆盖、不备份。
      # （此分支无覆盖动作，备份纯属多余且每次 apply 累积一份 → 破坏幂等；native 错配版无 "guru"
      #   标记，走下面 else 覆盖修正，那里才有真实覆盖、才需备份。）
      echo "  bootstrap: prd.md 已是 guru 版（保留在制内容，不覆盖）"
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
  # §7 刚把 before_start→guru_gate.py 写进 config.yaml。若 core 不支持阻断钩子，该 Gate 被静默忽略
  # → 用户以为有硬 Gate、实则 task.py start 拦不住（最危险的失败：假安全）。故硬失败，不软警告。
  # 根因不在本 overlay：core 脚本归 trellis update 的哈希三方合并管理（见脚本头部边界），本 overlay
  # 按设计不碰 core。此缺口=项目用「上游」CLI init/update（.trellis/.version 不带 -guru），其 core 无此能力。
  ver="$(cat "$TARGET/.trellis/.version" 2>/dev/null || echo '未知')"
  printf '  \033[31m✗ core 缺 before_start 阻断支持：guru 硬 Gate 已接线但不会生效（task.py start 拦不住）！\033[0m\n'
  echo "    根因：本项目用上游 CLI 装的（.trellis/.version=${ver}，非 -guru）。修复=用 guru CLI 重新基线 core（可复现、哈希追踪）："
  echo "      npm i -g @devsc/trellis@guru   # 或用 fork 本地 bin：node <fork>/packages/cli/bin/trellis.js"
  echo "      cd $TARGET && trellis update    # 交互式：对 task.py / common/task_utils.py 选「取模板版」"
  FAIL=1
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
else
  # §4.5 双面对齐的不变量：.agents/skills 与 .claude/skills 必须内容一致（名字+内容，排除脏文件）。
  # 平台 configurator / trellis update 会向单面写 skill（如 Codex 的 trellis-start 只进 .agents），
  # 制造漂移；本检查在每次 apply 后做【内容级】断言（非仅目录名），兜底捕获 §4.5 自身的 bug（含
  # mtime 启发式在 equal-mtime / 多文件内部漂移下的盲区）。
  if diff -rq -x .DS_Store -x __pycache__ "$TARGET/.agents/skills" "$TARGET/.claude/skills" >/dev/null 2>&1; then
    echo "  ✓ skill 两面一致（.agents/skills == .claude/skills，含内容）"
  else
    echo "  ✗ skill 两面不一致（§4.5 对齐异常，见 diff）："
    diff -rq -x .DS_Store -x __pycache__ "$TARGET/.agents/skills" "$TARGET/.claude/skills" 2>&1 | sed 's/^/      /'
    FAIL=1
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
echo ""
echo "维护规约：每次 trellis update / 平台 reconfigure 后补跑一次本脚本。"
echo "  原因：平台 configurator 会向单面写 skill（如 Codex 的 trellis-start 只进 .agents/skills），"
echo "  使 .agents/skills 与 .claude/skills 漂移；重跑 apply.sh 的 §4.5 双面对齐即拉平（幂等）。"