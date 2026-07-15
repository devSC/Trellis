#!/usr/bin/env bash
# apply.sh 安装/升级器测试：三场景（通用项目 / 项目自带镜像 / 旧 core 警告）+ 幂等 + conventions 保护。
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APPLY="$HERE/../apply.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"; rm -f "$HERE/../agents-skills/"*/.DS_Store 2>/dev/null' EXIT
pass=0; failn=0

ok()   { pass=$((pass+1)); echo "PASS  $1"; }
bad()  { failn=$((failn+1)); echo "FAIL  $1"; }

mk_target() { # mk_target <name> [with_blocking_core]
  local d="$TMP/$1"
  local active_task_src
  mkdir -p "$d/.trellis/scripts/common" "$d/.trellis/spec/conventions" "$d/.claude"
  if [ "${2:-yes}" = "yes" ]; then
    printf 'def run_blocking_task_hooks():\n    pass\n' > "$d/.trellis/scripts/common/task_utils.py"
  else
    printf 'def run_task_hooks():\n    pass\n' > "$d/.trellis/scripts/common/task_utils.py"
  fi
  # Support both packaged template layout and guru-template SSOT layout.
  for active_task_src in \
    "$HERE/../../../trellis/scripts/common/active_task.py" \
    "$HERE/../../../packages/cli/src/templates/trellis/scripts/common/active_task.py" \
    "$HERE/../../../packages/cli/dist/templates/trellis/scripts/common/active_task.py"; do
    if [ -f "$active_task_src" ]; then
      cp "$active_task_src" "$d/.trellis/scripts/common/active_task.py"
      break
    fi
  done
  [ -f "$d/.trellis/scripts/common/active_task.py" ] || {
    echo "missing active_task.py fixture source" >&2
    exit 1
  }
  # 已填写的项目约定（必须被保留）
  printf '# 项目约定\nSLOT-01: 已填写的真实取值 SENTINEL_KEEP_ME\n' > "$d/.trellis/spec/conventions/project-conventions.md"
  # 含用户自定义 hook 的 settings.json（必须被保留）
  cat > "$d/.claude/settings.json" <<'EOF'
{"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "my-custom-guard.sh"}]}]},
 "model": "opus"}
EOF
  echo "$d"
}

# ============ 场景 1：通用项目（无项目镜像脚本）============
T1=$(mk_target generic yes)
mkdir -p "$T1/.trellis/tasks/old-grill-marker"
: > "$T1/.trellis/tasks/old-grill-marker/.grilled-prd"
out=$(bash "$APPLY" "$T1" 2>&1); rc=$?
[ "$rc" = 0 ] && ok "场景1 apply 退出码 0" || { bad "场景1 退出码 (rc=$rc)"; echo "$out" | tail -10; }

diff -r "$T1/.agents/skills/client-design-overview-writing" "$T1/.claude/skills/client-design-overview-writing" >/dev/null 2>&1 \
  && ok "场景1 skills 镜像到 .claude/skills 且字节一致" || bad "场景1 .claude/skills 镜像缺失或不一致"

[ -d "$T1/.agents/skills/design-grill" ] && [ -d "$T1/.claude/skills/design-grill" ] \
  && diff -r "$T1/.agents/skills/design-grill" "$T1/.claude/skills/design-grill" >/dev/null 2>&1 \
  && ok "场景1 design-grill 两面存在且字节一致" || bad "场景1 design-grill 两面缺失或不一致"

[ ! -d "$T1/.trellis/backup/guru-legacy-skills" ] \
  && ok "场景1 无 legacy grill skill 不创建空备份" || bad "场景1 无旧名时不应创建 legacy 备份目录"

[ ! -e "$T1/.trellis/tasks/old-grill-marker/.grilled-prd" ] \
  && ok "场景1 清理旧 .grilled-* 提示标记" || bad "场景1 旧 .grilled-* 标记未清理"

if python3 - "$T1/.claude/settings.json" <<'PY'
import json
import sys
settings = json.load(open(sys.argv[1], encoding="utf-8"))
entries = settings.get("hooks", {}).get("PreToolUse", [])
bash_entries = [e for e in entries if e.get("matcher") == "Bash"]
hooks = [h for e in bash_entries for h in e.get("hooks", [])]
commands = [h.get("command") for h in hooks]
assert len(bash_entries) == 1
assert commands.count("my-custom-guard.sh") == 1
assert commands.count("\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-unconfirmed-start.sh") == 1
assert commands.count("\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-unstarted-commit.sh") == 1
PY
then ok "场景1 settings.json 合并（用户 hook 保留 + start/commit 阻断 hook 接线）"
else bad "场景1 settings.json 合并不完整"; fi
[ -x "$T1/.claude/hooks/block-unstarted-commit.sh" ] \
  && ok "场景1 Claude commit guard hook 已安装且可执行" || bad "场景1 Claude commit guard hook 缺失或不可执行"
python3 -c "import json;d=json.load(open('$T1/.claude/settings.json'));assert d['model']=='opus'" 2>/dev/null \
  && ok "场景1 settings.json 非 hooks 键保留" || bad "场景1 settings.json 用户键丢失"

[ -f "$T1/.trellis/workflow.md" ] && [ -f "$T1/.trellis/spec/harness/index.md" ] \
  && [ -f "$T1/.trellis/spec/guides/golden-path.md" ] && [ -f "$T1/.trellis/spec/guides/index.md" ] \
  && [ -f "$T1/.trellis/spec/conventions/index.md" ] \
  && ok "场景1 workflow + harness + guides(含 index) + conventions/index 同步" || bad "场景1 SSOT 同步不完整"

grep -q "SENTINEL_KEEP_ME" "$T1/.trellis/spec/conventions/project-conventions.md" \
  && ok "场景1 project-conventions.md 未被覆盖" || bad "场景1 项目约定被覆盖！"

grep -q "before_start" "$T1/.trellis/config.yaml" && ok "场景1 config.yaml before_start 接线" || bad "场景1 config 缺 before_start"
grep -qx ".claude/projects/" "$T1/.gitignore" \
  && grep -qx ".codex/sessions/" "$T1/.gitignore" \
  && grep -qx ".trellis/channels/" "$T1/.gitignore" \
  && ok "场景1 本地 AI/Trellis 运行日志写入 .gitignore" || bad "场景1 .gitignore 缺本地运行日志规则"

# 幂等：第二遍跑完无任何文件变化
snapshot() { # 可移植目录快照（macOS 无 sha256sum、Linux 无 md5 -q，统一用 python）
  python3 - "$1" <<'PYS'
import hashlib, os, sys
h = hashlib.sha256()
root = sys.argv[1]
for dirpath, dirnames, filenames in sorted(os.walk(root)):
    dirnames.sort()
    for name in sorted(filenames):
        p = os.path.join(dirpath, name)
        h.update(os.path.relpath(p, root).encode()); h.update(b"\0")
        h.update(open(p, "rb").read()); h.update(b"\0")
print(h.hexdigest())
PYS
}
SNAP1=$(snapshot "$T1") || { bad "场景1 快照失败（首次）"; SNAP1="__fail1__"; }
out=$(bash "$APPLY" "$T1" 2>&1); rc=$?
[ "$rc" = 0 ] && ok "场景1 二跑 apply 退出码 0" || { bad "场景1 二跑退出码 (rc=$rc)"; echo "$out" | tail -5; }
SNAP2=$(snapshot "$T1") || { bad "场景1 快照失败（二次）"; SNAP2="__fail2__"; }
[ "$SNAP1" = "$SNAP2" ] && ok "场景1 幂等（二跑无变化）" || bad "场景1 二跑产生了变化"

# ============ 场景 2：项目自带镜像脚本（himora 模式）============
T2=$(mk_target mirrored yes)
mkdir -p "$T2/scripts"
cat > "$T2/scripts/sync_platform_skills.py" <<'EOF'
import os
import shutil
import sys
root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.getcwd()
src = os.path.join(root, ".agents", "skills", "design-grill")
dst = os.path.join(root, ".claude", "skills", "design-grill")
if "--sync" in sys.argv:
    if os.path.isdir(src):
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
    open(os.path.join(root, "MIRROR_SENTINEL"), "w").write("synced")
if "--check" in sys.argv:
    if not (os.path.isdir(src) and os.path.isdir(dst)):
        sys.exit(1)
sys.exit(0)
EOF
out=$(cd "$T2" && bash "$APPLY" "$T2" 2>&1); rc=$?
[ "$rc" = 0 ] && ok "场景2 apply 退出码 0" || { bad "场景2 退出码 (rc=$rc)"; echo "$out" | tail -5; }
[ -f "$T2/MIRROR_SENTINEL" ] && ok "场景2 项目镜像脚本被调用" || bad "场景2 镜像脚本未被调用"
[ -d "$T2/.agents/skills/design-grill" ] && [ -d "$T2/.claude/skills/design-grill" ] \
  && ok "场景2 镜像模式 design-grill 两面存在" || bad "场景2 design-grill 未被镜像到两面"
[ ! -d "$T2/.claude/skills/client-design-overview-writing" ] \
  && ok "场景2 apply 未直写 .claude/skills（交镜像脚本管）" || bad "场景2 不应直写 .claude/skills"
rm -f "$T2/MIRROR_SENTINEL"

# ============ 场景 3：旧 core（缺 before_start 支持）→ 硬失败 exit 1（不再假安全，见 commit 258aca72）============
T3=$(mk_target oldcore no)
out=$(bash "$APPLY" "$T3" 2>&1); rc=$?
[ "$rc" = 1 ] && ok "场景3 旧 core 硬失败 exit 1（不再假安全）" || bad "场景3 退出码应为 1 (rc=$rc)"
printf '%s' "$out" | grep -q "硬 Gate 已接线但不会生效" && ok "场景3 输出含硬失败根因" || bad "场景3 缺核心警告"

# ============ 场景 4：skill 安装清理脏文件，.DS_Store 不泄漏进目标（修 C）============
ds_src="$HERE/../agents-skills/requirement-writing/.DS_Store"; : > "$ds_src"   # 临时埋点（EXIT trap 兜底清理）
T4=$(mk_target dotclean yes)
bash "$APPLY" "$T4" flutter >/dev/null 2>&1
rm -f "$ds_src"
n_ds=$(find "$T4/.agents/skills" "$T4/.claude/skills" -name .DS_Store 2>/dev/null | wc -l | tr -d ' ')
[ "$n_ds" = 0 ] && ok "场景4 skill 安装不泄漏 .DS_Store（C）" || bad "场景4 .DS_Store 泄漏 ×$n_ds"

# ============ 场景 5：切平台后 settings.json 清理悬空 hook 引用，不误删用户/有效 hook（修 A）============
T5=$(mk_target switchhook yes)
bash "$APPLY" "$T5" flutter >/dev/null 2>&1
grep -q "block-l10n-sync" "$T5/.claude/settings.json" && ok "场景5 flutter 装 block-l10n-sync 引用（前提）" || bad "场景5 flutter 应有 block-l10n-sync"
bash "$APPLY" "$T5" go >/dev/null 2>&1
[ ! -f "$T5/.claude/hooks/block-l10n-sync.sh" ] && ok "场景5 切 go 删除 block-l10n-sync.sh 文件" || bad "场景5 文件未删"
grep -q "block-l10n-sync" "$T5/.claude/settings.json" && bad "场景5 settings 残留悬空 block-l10n-sync（A 未修）" || ok "场景5 settings 无悬空引用（A）"
grep -q "block-unconfirmed-start" "$T5/.claude/settings.json" && ok "场景5 有效 hook 引用保留" || bad "场景5 误删有效 hook"
grep -q "my-custom-guard" "$T5/.claude/settings.json" && ok "场景5 用户自定义 hook 未被误删" || bad "场景5 误删用户 hook"

# ============ 场景 6：bootstrap（已是 guru 版被编辑）重复 apply 零累积备份、保留在制内容（修 B）============
T6=$(mk_target bootidem yes)
mkdir -p "$T6/.trellis/tasks/00-bootstrap-guidelines"
printf 'name=tester\n' > "$T6/.trellis/.developer"
printf '# Bootstrap (guru flutter) 用户在制内容 SENTINEL\nSLOT-A: 真实值\n' > "$T6/.trellis/tasks/00-bootstrap-guidelines/prd.md"
bash "$APPLY" "$T6" flutter >/dev/null 2>&1
bash "$APPLY" "$T6" flutter >/dev/null 2>&1
bash "$APPLY" "$T6" flutter >/dev/null 2>&1
n_bak=$(find "$T6/.trellis/tasks/00-bootstrap-guidelines" -name "prd.md.pre-guru.*" 2>/dev/null | wc -l | tr -d ' ')
[ "$n_bak" = 0 ] && ok "场景6 guru 版 bootstrap 重复 apply 零累积备份（B）" || bad "场景6 备份累积 ×$n_bak"
grep -q "SENTINEL" "$T6/.trellis/tasks/00-bootstrap-guidelines/prd.md" && ok "场景6 用户在制内容保留" || bad "场景6 在制内容丢失"

# ============ 场景 7：§4.5 双面对齐——引擎 skill 单面升级后内容跨面同步（修 D）============
T7=$(mk_target enginedrift yes)
mkdir -p "$T7/.claude/skills/trellis-brainstorm"
printf 'ENGINE v1\n' > "$T7/.claude/skills/trellis-brainstorm/SKILL.md"
bash "$APPLY" "$T7" flutter >/dev/null 2>&1
grep -q "ENGINE v1" "$T7/.agents/skills/trellis-brainstorm/SKILL.md" 2>/dev/null && ok "场景7 引擎 skill 首次对齐补到 .agents" || bad "场景7 首次对齐失败"
sleep 1
printf 'ENGINE v2\n' > "$T7/.claude/skills/trellis-brainstorm/SKILL.md"
bash "$APPLY" "$T7" flutter >/dev/null 2>&1
grep -q "ENGINE v2" "$T7/.agents/skills/trellis-brainstorm/SKILL.md" 2>/dev/null && ok "场景7 单面升级后跨面同步到 v2（D）" || bad "场景7 .agents 面陈旧（D 未修）"

# ============ 场景 8：legacy dirs（block-legacy-dirs LEGACY_PATTERNS）用户值不被二次 apply 覆盖（修 E）============
T8=$(mk_target slot12keep yes)
bash "$APPLY" "$T8" flutter >/dev/null 2>&1
python3 - "$T8/.claude/hooks/block-legacy-dirs.sh" <<'PYS'
import sys
p=sys.argv[1]; s=open(p).read()
open(p,'w').write(s.replace("LEGACY_PATTERNS=''","LEGACY_PATTERNS='lib/old/|lib/legacy/'",1))
PYS
bash "$APPLY" "$T8" flutter >/dev/null 2>&1
grep -q "LEGACY_PATTERNS='lib/old/|lib/legacy/'" "$T8/.claude/hooks/block-legacy-dirs.sh" && ok "场景8 LEGACY_PATTERNS 用户值保留（E）" || bad "场景8 LEGACY_PATTERNS 被模板覆盖（E 未修）"
bash "$APPLY" "$T8" flutter >/dev/null 2>&1
grep -q "LEGACY_PATTERNS='lib/old/|lib/legacy/'" "$T8/.claude/hooks/block-legacy-dirs.sh" && ok "场景8 三跑 LEGACY_PATTERNS 仍稳定（幂等）" || bad "场景8 LEGACY_PATTERNS 不稳定"

# ============ 场景 9：多文件 skill 内部非 SKILL.md 文件漂移也跨面同步（修 D 深化，填场景7 盲区）============
T9=$(mk_target multifiledrift yes)
mkdir -p "$T9/.claude/skills/trellis-meta/references"
printf 'META\n' > "$T9/.claude/skills/trellis-meta/SKILL.md"
printf 'GUIDE v1\n' > "$T9/.claude/skills/trellis-meta/references/core.md"
bash "$APPLY" "$T9" flutter >/dev/null 2>&1
grep -q "GUIDE v1" "$T9/.agents/skills/trellis-meta/references/core.md" 2>/dev/null && ok "场景9 多文件 skill 首次对齐补到 .agents" || bad "场景9 首次对齐失败"
sleep 1
printf 'GUIDE v2\n' > "$T9/.claude/skills/trellis-meta/references/core.md"   # 只改内部文件，不动 SKILL.md/目录
bash "$APPLY" "$T9" flutter >/dev/null 2>&1
grep -q "GUIDE v2" "$T9/.agents/skills/trellis-meta/references/core.md" 2>/dev/null && ok "场景9 内部文件漂移跨面同步到 v2（D 深化，子树最新 mtime）" || bad "场景9 内部文件漂移未同步（mtime 启发式盲区）"

# ============ 场景 10：basename 同名异路径的用户 hook 不被悬空清理误删（修 #5 路径锚定）============
T10=$(mk_target userhookname yes)
bash "$APPLY" "$T10" flutter >/dev/null 2>&1
python3 - "$T10/.claude/settings.json" <<'PY'
import json, sys
p = sys.argv[1]; d = json.load(open(p))
for e in d["hooks"]["PreToolUse"]:
    if e.get("matcher") == "Bash":
        e["hooks"].append({"type": "command", "command": "\"$HOME\"/my-tools/block-l10n-sync.sh --mine"})
json.dump(d, open(p, "w"), ensure_ascii=False, indent=2)
PY
bash "$APPLY" "$T10" go >/dev/null 2>&1   # 切 go：guru 的 block-l10n-sync 进 stale
grep -q 'my-tools/block-l10n-sync.sh' "$T10/.claude/settings.json" && ok "场景10 用户同名异路径 hook 保留（#5 路径锚定）" || bad "场景10 用户 hook 被误删"
grep -q '.claude/hooks/block-l10n-sync.sh' "$T10/.claude/settings.json" && bad "场景10 guru 悬空引用未清" || ok "场景10 guru 悬空引用仍被正确清理"

# ============ 场景 11：用户原本就空的 hooks 条目不被清理误删（修 #6）============
T11=$(mk_target emptyhookentry yes)
printf '%s\n' '{"hooks":{"PreToolUse":[{"matcher":"Read","hooks":[]}]}}' > "$T11/.claude/settings.json"
bash "$APPLY" "$T11" flutter >/dev/null 2>&1
python3 -c "import json,sys;d=json.load(open('$T11/.claude/settings.json'));sys.exit(0 if any(e.get('matcher')=='Read' for e in d['hooks']['PreToolUse']) else 1)" \
  && ok "场景11 用户原本就空的 hooks 条目保留（#6）" || bad "场景11 空条目被误删"

# ============ 场景 12：用户指向全局 ~/.claude/hooks/ 的同名 hook 不被悬空清理误删（修 #1 锚定 CLAUDE_PROJECT_DIR）============
T12=$(mk_target globalhook yes)
bash "$APPLY" "$T12" flutter >/dev/null 2>&1
python3 - "$T12/.claude/settings.json" <<'PY'
import json, sys
p = sys.argv[1]; d = json.load(open(p))
for e in d["hooks"]["PreToolUse"]:
    if e.get("matcher") == "Bash":
        e["hooks"].append({"type": "command", "command": "\"$HOME\"/.claude/hooks/block-l10n-sync.sh --personal"})
json.dump(d, open(p, "w"), ensure_ascii=False, indent=2)
PY
bash "$APPLY" "$T12" go >/dev/null 2>&1   # 切 go：guru 项目的 block-l10n-sync 进 stale
grep -q -- '--personal' "$T12/.claude/settings.json" && ok "场景12 用户全局 ~/.claude/hooks 同名 hook 保留（#1 锚定）" || bad "场景12 用户全局 hook 被误删"
python3 -c "
import json, sys
d = json.load(open('$T12/.claude/settings.json'))
stale = [h for e in d['hooks'].get('PreToolUse', []) for h in e.get('hooks', [])
         if 'CLAUDE_PROJECT_DIR' in h.get('command','') and 'block-l10n-sync.sh' in h.get('command','')]
sys.exit(1 if stale else 0)" && ok "场景12 guru 项目悬空引用仍正确清理" || bad "场景12 guru 项目悬空引用未清"

# ============ 场景 13：write_boot_task_json 从多行 .developer 只取 name= 值（修 #1，不污染 creator/assignee）============
T13=$(mk_target devname yes)
printf 'name=alice\ninitialized_at=2026-06-14T10:30:00.123456\n' > "$T13/.trellis/.developer"
bash "$APPLY" "$T13" flutter >/dev/null 2>&1
python3 -c "import json,sys;d=json.load(open('$T13/.trellis/tasks/00-bootstrap-guidelines/task.json'));sys.exit(0 if d.get('creator')=='alice' and d.get('assignee')=='alice' else 1)" \
  && ok "场景13 bootstrap task.json creator/assignee 为裸名 alice（#1）" || bad "场景13 creator/assignee 被 .developer 全文污染"

# ============ 场景 14：guru_after_create append_unique 不粘到无尾换行的既有 jsonl 末行（修 #5）============
T14=$(mk_target jsonlnl yes)
mkdir -p "$T14/.trellis/tasks/t1"
printf 'name=tester\n' > "$T14/.trellis/.developer"
printf '{"file":"existing.md","reason":"用户手编无尾换行"}' > "$T14/.trellis/tasks/t1/implement.jsonl"
printf '{"file":"existing.md","reason":"x"}' > "$T14/.trellis/tasks/t1/check.jsonl"
printf '{"id":"t1"}' > "$T14/.trellis/tasks/t1/task.json"
TASK_JSON_PATH="$T14/.trellis/tasks/t1/task.json" python3 "$HERE/../hooks/guru_after_create.py" >/dev/null 2>&1
python3 -c "
import json, sys
bad = 0
for line in open('$T14/.trellis/tasks/t1/implement.jsonl'):
    line = line.strip()
    if line:
        try: json.loads(line)
        except Exception: bad += 1
sys.exit(1 if bad else 0)" && ok "场景14 after_create 不粘到无尾换行末行（#5）" || bad "场景14 jsonl 出现粘行非法 JSON"

# ============ 场景 15：config.yaml 已有 marker 块外用户 hooks: 时警告（修 #2 重复键静默吞 hook）============
T15=$(mk_target cfghooks yes)
printf 'hooks:\n  after_finish:\n    - "echo done"\n' > "$T15/.trellis/config.yaml"
out=$(bash "$APPLY" "$T15" flutter 2>&1)
printf '%s' "$out" | grep -q "已有顶层 hooks" && ok "场景15 检测到 marker 块外用户 hooks: 并警告（#2）" || bad "场景15 未警告重复 hooks 键风险"

# ============ 场景 16：阶段 C legacy grill wrapper 安全清理：先备份再移除，二跑不建空备份 ============
T16=$(mk_target legacygrill yes)
legacy_client="client""-grill"
legacy_go="go""-design-grill"
legacy_h5="h5""-design-grill"
legacy_ios="ios""-design-grill"
mkdir -p "$T16/.agents/skills/$legacy_client" "$T16/.claude/skills/$legacy_client"
# 真实旧 wrapper 含 guru 特征（frontmatter「兼容 wrapper」描述），身份判断据此识别为 guru 托管、可清理
printf '# client-grill\n兼容 wrapper：加载 design-grill\nLEGACY agents side\n' > "$T16/.agents/skills/$legacy_client/SKILL.md"
printf '# client-grill\n兼容 wrapper：加载 design-grill\nLEGACY claude side\n' > "$T16/.claude/skills/$legacy_client/SKILL.md"
out=$(bash "$APPLY" "$T16" flutter 2>&1); rc=$?
[ "$rc" = 0 ] && ok "场景16 legacy 清理 apply 退出码 0" || { bad "场景16 apply 失败 (rc=$rc)"; echo "$out" | tail -5; }
[ ! -d "$T16/.agents/skills/$legacy_client" ] && [ ! -d "$T16/.claude/skills/$legacy_client" ] \
  && ok "场景16 旧 legacy client skill 从两面移除" || bad "场景16 legacy client skill 未从两面移除"
backup_agents=$(find "$T16/.trellis/backup/guru-legacy-skills" -path "*/$legacy_client/agents/SKILL.md" -print -quit 2>/dev/null || true)
backup_claude=$(find "$T16/.trellis/backup/guru-legacy-skills" -path "*/$legacy_client/claude/SKILL.md" -print -quit 2>/dev/null || true)
[ -n "$backup_agents" ] && grep -q "LEGACY agents side" "$backup_agents" \
  && [ -n "$backup_claude" ] && grep -q "LEGACY claude side" "$backup_claude" \
  && ok "场景16 legacy client skill 两面先备份" || bad "场景16 legacy 备份缺失或内容不对"
printf '%s' "$out" | grep -q "已备份并移除 legacy grill skill: $legacy_client" \
  && ok "场景16 输出 legacy 备份恢复提示" || bad "场景16 缺 legacy 备份提示"
before_backup_n=$(find "$T16/.trellis/backup/guru-legacy-skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
bash "$APPLY" "$T16" flutter >/dev/null 2>&1
after_backup_n=$(find "$T16/.trellis/backup/guru-legacy-skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
[ "$before_backup_n" = "$after_backup_n" ] && ok "场景16 无旧名二跑不创建新 legacy 备份" || bad "场景16 二跑创建了空/多余 legacy 备份"
old_grill_n=$(find "$T16/.agents/skills" "$T16/.claude/skills" \( -name "$legacy_client" -o -name "$legacy_go" -o -name "$legacy_h5" -o -name "$legacy_ios" \) -type d 2>/dev/null | wc -l | tr -d ' ')
[ "$old_grill_n" = 0 ] && ok "场景16 四个旧 grill 名均不在两面 skills" || bad "场景16 仍有旧 grill 名目录 ×$old_grill_n"

# ============ 场景 17：legacy 清理身份判断——无 guru 特征的同名 skill（疑似用户自建）受保护不被删除 ============
T17=$(mk_target legacyuserskill yes)
mkdir -p "$T17/.agents/skills/$legacy_go" "$T17/.claude/skills/$legacy_go"
printf '# my own go-design-grill\nuser custom skill, not guru managed\n' > "$T17/.agents/skills/$legacy_go/SKILL.md"
printf '# my own go-design-grill\nuser custom skill, not guru managed\n' > "$T17/.claude/skills/$legacy_go/SKILL.md"
out=$(bash "$APPLY" "$T17" go 2>&1); rc=$?
[ "$rc" = 0 ] && ok "场景17 apply 退出码 0" || { bad "场景17 apply 失败 (rc=$rc)"; echo "$out" | tail -5; }
[ -d "$T17/.agents/skills/$legacy_go" ] && [ -d "$T17/.claude/skills/$legacy_go" ] \
  && ok "场景17 无 guru 特征同名 skill 受保护未删" || bad "场景17 误删了用户自建同名 skill"
printf '%s' "$out" | grep -q "跳过疑似用户自建同名 skill" \
  && ok "场景17 输出用户自建跳过警告" || bad "场景17 缺用户自建跳过警告"

# ============ 场景 18：GitNexus opt-in bootstrap 默认不触发；显式开启后写目标项目 AGENTS 块且幂等 ============
T18=$(mk_target gitnexus yes)
cat > "$T18/AGENTS.md" <<'EOF'
# User instructions

Keep this user-owned preface.

<!-- TRELLIS:START -->
# Trellis Instructions
Managed by Trellis.
<!-- TRELLIS:END -->
EOF
fakebin="$TMP/fakebin-gitnexus"
mkdir -p "$fakebin"
cat > "$fakebin/npx" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_GITNEXUS_LOG:?}"
if [ "$1" = "gitnexus" ] && [ "$2" = "analyze" ]; then
  mkdir -p .gitnexus
  cat > .gitnexus/meta.json <<JSON
{"repoPath":"$PWD","indexedAt":"2026-06-19T00:00:00.000Z","stats":{"files":12,"nodes":34,"edges":56,"processes":7}}
JSON
elif [ "$1" = "gitnexus" ] && [ "$2" = "status" ]; then
  echo "Repository indexed."
else
  echo "unexpected fake npx args: $*" >&2
  exit 9
fi
EOF
chmod +x "$fakebin/npx"
gitnexus_log="$T18/gitnexus.log"
PATH="$fakebin:$PATH" FAKE_GITNEXUS_LOG="$gitnexus_log" bash "$APPLY" "$T18" flutter >/dev/null 2>&1
[ ! -f "$gitnexus_log" ] && ok "场景18 默认 apply 不调用 GitNexus" || bad "场景18 默认 apply 不应调用 GitNexus"
grep -q "gitnexus:start" "$T18/AGENTS.md" && bad "场景18 默认 apply 不应写 gitnexus 块" || ok "场景18 默认 apply 不写 gitnexus 块"

out=$(GURU_WITH_GITNEXUS=1 PATH="$fakebin:$PATH" FAKE_GITNEXUS_LOG="$gitnexus_log" bash "$APPLY" "$T18" flutter 2>&1); rc=$?
[ "$rc" = 0 ] && ok "场景18 opt-in apply 退出码 0" || { bad "场景18 opt-in apply 失败 (rc=$rc)"; echo "$out" | tail -5; }
grep -q '^gitnexus analyze$' "$gitnexus_log" && grep -q '^gitnexus status$' "$gitnexus_log" \
  && ok "场景18 opt-in 调用 gitnexus analyze/status" || bad "场景18 未调用 gitnexus analyze/status"
grep -q "Keep this user-owned preface" "$T18/AGENTS.md" && grep -q "TRELLIS:START" "$T18/AGENTS.md" \
  && ok "场景18 AGENTS 用户内容和 Trellis 块保留" || bad "场景18 AGENTS 既有内容丢失"
grep -q "GitNexus - Code Intelligence" "$T18/AGENTS.md" && grep -q "34 symbols" "$T18/AGENTS.md" \
  && grep -q "npx gitnexus setup" "$T18/AGENTS.md" \
  && ok "场景18 写入目标项目 GitNexus 指令块" || bad "场景18 GitNexus 指令块缺失或内容不完整"
block_n=$(grep -c "<!-- gitnexus:start -->" "$T18/AGENTS.md" || true)
[ "$block_n" = 1 ] && ok "场景18 GitNexus 块仅一份" || bad "场景18 GitNexus 块数量异常：$block_n"
agents_hash_before=$(python3 - "$T18/AGENTS.md" <<'PYS'
import hashlib, sys
print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())
PYS
)
GURU_WITH_GITNEXUS=1 PATH="$fakebin:$PATH" FAKE_GITNEXUS_LOG="$gitnexus_log" bash "$APPLY" "$T18" flutter >/dev/null 2>&1
agents_hash_after=$(python3 - "$T18/AGENTS.md" <<'PYS'
import hashlib, sys
print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())
PYS
)
block_n=$(grep -c "<!-- gitnexus:start -->" "$T18/AGENTS.md" || true)
[ "$block_n" = 1 ] && [ "$agents_hash_before" = "$agents_hash_after" ] \
  && ok "场景18 opt-in 二跑不重复/不改写 AGENTS" || bad "场景18 opt-in 二跑不幂等"

# ============ 场景 19：目标已有 .codex 时安装 commit guard 并幂等合并 .codex/hooks.json ============
T19=$(mk_target "codex hooks" yes)
mkdir -p "$T19/.codex"
cat > "$T19/.codex/hooks.json" <<'EOF'
{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"bash .codex/hooks/my-custom-codex-guard.sh","timeout":5},{"type":"command","command":"bash .codex/hooks/block-unstarted-commit.sh","timeout":1,"stale":true},{"type":"command","command":"bash /old/guru/project/.codex/hooks/block-unstarted-commit.sh","timeout":2,"stale_absolute":true}]},{"matcher":"Bash","hooks":[{"type":"command","command":"bash .codex/hooks/block-unstarted-commit.sh","timeout":2,"stale_duplicate":true}]}]}}
EOF
out=$(bash "$APPLY" "$T19" flutter 2>&1); rc=$?
[ "$rc" = 0 ] && ok "场景19 apply 退出码 0" || { bad "场景19 apply 失败 (rc=$rc)"; echo "$out" | tail -5; }
[ -x "$T19/.codex/hooks/block-unstarted-commit.sh" ] \
  && ok "场景19 Codex commit guard hook 已安装且可执行" || bad "场景19 Codex commit guard hook 缺失或不可执行"
python3 - "$T19/.codex/hooks.json" "$T19" <<'PY'
import json, shlex, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
expected_guard = "bash " + shlex.quote(sys.argv[2] + "/.codex/hooks/block-unstarted-commit.sh")
entries = d.get("hooks", {}).get("PreToolUse", [])
bash_entries = [e for e in entries if e.get("matcher") == "Bash"]
hooks = [h for e in bash_entries for h in e.get("hooks", [])]
custom = [h for h in hooks if h.get("command") == "bash .codex/hooks/my-custom-codex-guard.sh"]
guards = [h for h in hooks if h.get("command") == expected_guard]
legacy_guards = [h for h in hooks if h.get("command") == "bash .codex/hooks/block-unstarted-commit.sh"]
stale_absolute_guards = [h for h in hooks if h.get("command") == "bash /old/guru/project/.codex/hooks/block-unstarted-commit.sh"]
assert len(bash_entries) == 1
assert len(custom) == 1 and custom[0].get("timeout") == 5
assert guards == [{"type": "command", "command": expected_guard, "timeoutSec": 15}]
assert legacy_guards == []
assert stale_absolute_guards == []
PY
[ "$?" = 0 ] && ok "场景19 .codex/hooks.json 保留用户 hook 并刷新/去重 commit guard" || bad "场景19 .codex/hooks.json 合并不完整"
codex_hash_before=$(python3 - "$T19/.codex/hooks.json" <<'PYS'
import hashlib, sys
print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())
PYS
)
out=$(bash "$APPLY" "$T19" flutter 2>&1); rc=$?
[ "$rc" = 0 ] && ok "场景19 二跑 apply 退出码 0" || { bad "场景19 二跑 apply 失败 (rc=$rc)"; echo "$out" | tail -5; }
codex_hash_after=$(python3 - "$T19/.codex/hooks.json" <<'PYS'
import hashlib, sys
print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())
PYS
)
[ "$codex_hash_before" = "$codex_hash_after" ] \
  && ok "场景19 Codex hook 合并二跑幂等" || bad "场景19 Codex hook 合并二跑产生变化"

codex_guard_input() {
  python3 - "$1" "$2" <<'PY'
import json, sys
print(json.dumps({"tool_input": {"command": sys.argv[1]}, "cwd": sys.argv[2]}))
PY
}

# ============ 场景 20：目标没有 .codex 时也安装 commit guard，避免安装顺序造成治理空窗 ============
T20=$(mk_target "codex hooks fresh" yes)
out=$(bash "$APPLY" "$T20" flutter 2>&1); rc=$?
[ "$rc" = 0 ] && ok "场景20 apply 退出码 0" || { bad "场景20 apply 失败 (rc=$rc)"; echo "$out" | tail -5; }
[ -x "$T20/.codex/hooks/block-unstarted-commit.sh" ] \
  && ok "场景20 Codex commit guard hook 已安装且可执行" || bad "场景20 Codex commit guard hook 缺失或不可执行"
python3 - "$T20/.codex/hooks.json" "$T20" <<'PY'
import json, shlex, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
expected_guard = "bash " + shlex.quote(sys.argv[2] + "/.codex/hooks/block-unstarted-commit.sh")
guards = [
    h
    for e in d.get("hooks", {}).get("PreToolUse", [])
    if e.get("matcher") == "Bash"
    for h in e.get("hooks", [])
    if h.get("command") == expected_guard
]
assert guards == [{"type": "command", "command": expected_guard, "timeoutSec": 15}]
PY
[ "$?" = 0 ] && ok "场景20 .codex/hooks.json 新建并接入 commit guard" || bad "场景20 .codex/hooks.json 未接入 commit guard"
mkdir -p "$T20/sub/dir"
mkdir -p "$T20/.trellis/.runtime/sessions"
printf '{"current_task":".trellis/tasks/00-bootstrap-guidelines"}\n' > "$T20/.trellis/.runtime/sessions/codex-guard-test.json"
codex_guard_cmd=$(python3 - "$T20/.codex/hooks.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
for e in d.get("hooks", {}).get("PreToolUse", []):
    if e.get("matcher") == "Bash":
        for h in e.get("hooks", []):
            cmd = h.get("command", "")
            if "block-unstarted-commit.sh" in cmd:
                print(cmd)
                raise SystemExit(0)
raise SystemExit(1)
PY
)
out=$(printf '{"tool_input":{"command":"git commit -m test"},"cwd":"%s"}' "$T20/sub/dir" | (cd "$T20/sub/dir" && eval "$codex_guard_cmd") 2>&1); rc=$?
[ "$rc" = 2 ] && printf '%s' "$out" | grep -q "Guru task is not ready to commit" \
  && ok "场景20 Codex hook command nested cwd 可执行并阻断 commit" || { bad "场景20 Codex hook command nested cwd 未正确阻断 (rc=$rc)"; echo "$out" | head -4; }
out=$(codex_guard_input "echo 'git commit'" "$T20/sub/dir" | (cd "$T20/sub/dir" && eval "$codex_guard_cmd") 2>&1); rc=$?
[ "$rc" = 0 ] \
  && ok "场景20 Codex hook 不误拦 echo git commit 文本" || { bad "场景20 Codex hook echo 文本误拦 (rc=$rc)"; echo "$out" | head -4; }
out=$(codex_guard_input "git commit --amend --no-verify -m test" "$T20/sub/dir" | (cd "$T20/sub/dir" && eval "$codex_guard_cmd") 2>&1); rc=$?
[ "$rc" = 2 ] && printf '%s' "$out" | grep -q "Guru task is not ready to commit" \
  && ok "场景20 Codex hook 阻断 amend/no-verify commit" || { bad "场景20 Codex hook amend/no-verify 漏拦 (rc=$rc)"; echo "$out" | head -4; }
out=$(codex_guard_input "/usr/bin/env git commit --amend -m test" "$T20/sub/dir" | (cd "$T20/sub/dir" && eval "$codex_guard_cmd") 2>&1); rc=$?
[ "$rc" = 2 ] && printf '%s' "$out" | grep -q "Guru task is not ready to commit" \
  && ok "场景20 Codex hook 阻断 absolute env wrapper commit" || { bad "场景20 Codex hook absolute env wrapper 漏拦 (rc=$rc)"; echo "$out" | head -4; }
out=$(codex_guard_input "git -C '$T20' commit -m test" "$T20/sub/dir" | (cd "$T20/sub/dir" && eval "$codex_guard_cmd") 2>&1); rc=$?
[ "$rc" = 2 ] && printf '%s' "$out" | grep -q "repository-changing options" \
  && ok "场景20 Codex hook 对 git -C commit 保守阻断" || { bad "场景20 Codex hook git -C commit 未保守阻断 (rc=$rc)"; echo "$out" | head -4; }

# ============ 场景 21：Codex hooks.json 非法时不留下半安装 commit guard ============
T21=$(mk_target codexhooks-invalid yes)
mkdir -p "$T21/.codex"
printf '{not valid json\n' > "$T21/.codex/hooks.json"
out=$(bash "$APPLY" "$T21" flutter 2>&1); rc=$?
[ "$rc" != 0 ] && ok "场景21 非法 .codex/hooks.json apply 返回非 0" || bad "场景21 非法 .codex/hooks.json 不应成功"
[ ! -e "$T21/.codex/hooks/block-unstarted-commit.sh" ] \
  && ok "场景21 Codex hook 合并失败不复制 commit guard 脚本" || bad "场景21 合并失败后留下半安装 commit guard"
[ ! -e "$T21/.claude/hooks" ] && [ ! -e "$T21/.agents" ] \
  && ok "场景21 非法 Codex hooks 失败前未写入前置安装产物" || bad "场景21 非法 Codex hooks 失败后留下前置安装副作用"
printf '%s' "$out" | grep -q ".codex/hooks.json" && printf '%s' "$out" | grep -q "JSON" \
  && ok "场景21 输出非法 JSON 根因" || bad "场景21 未输出非法 JSON 根因"

# ============ 场景 22：Codex hooks.json shape 非法时在写入前 fail-closed ============
check_bad_codex_hooks_shape() {
  local name="$1" payload="$2" pattern="$3" t out rc
  t=$(mk_target "$name" yes)
  mkdir -p "$t/.codex"
  printf '%s\n' "$payload" > "$t/.codex/hooks.json"
  out=$(bash "$APPLY" "$t" flutter 2>&1); rc=$?
  if [ "$rc" != 0 ] && printf '%s' "$out" | grep -q "$pattern" && [ ! -e "$t/.codex/hooks/block-unstarted-commit.sh" ]; then
    ok "场景22 $name 非法 shape 被预检阻断"
  else
    bad "场景22 $name 非法 shape 未被预检阻断 (rc=$rc)"
    echo "$out" | head -4
  fi
}
check_bad_codex_hooks_shape "codex hooks null" '{"hooks":null}' "hooks"
check_bad_codex_hooks_shape "codex event object" '{"hooks":{"PreToolUse":{}}}' "PreToolUse"
check_bad_codex_hooks_shape "codex entry scalar" '{"hooks":{"PreToolUse":["bad"]}}' "PreToolUse"
check_bad_codex_hooks_shape "codex entry hooks object" '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":{}}]}}' "hooks"

# ============ 场景 23：Codex hooks.json 最终替换失败时恢复既有 guard ============
T23=$(mk_target "codex hooks rollback" yes)
mkdir -p "$T23/.codex/hooks"
printf '{"hooks":{}}\n' > "$T23/.codex/hooks.json"
printf '#!/usr/bin/env bash\necho old guard\n' > "$T23/.codex/hooks/block-unstarted-commit.sh"
chmod +x "$T23/.codex/hooks/block-unstarted-commit.sh"
old_guard_hash=$(python3 - "$T23/.codex/hooks/block-unstarted-commit.sh" <<'PY'
import hashlib, sys
print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())
PY
)
fake_mv_bin="$TMP/fake-mv-bin"; mkdir -p "$fake_mv_bin"
cat > "$fake_mv_bin/mv" <<'EOF'
#!/usr/bin/env bash
dest=""
for arg in "$@"; do dest="$arg"; done
case "$dest" in
  */.codex/hooks.json) exit 1 ;;
esac
exec /bin/mv "$@"
EOF
chmod +x "$fake_mv_bin/mv"
out=$(PATH="$fake_mv_bin:$PATH" bash "$APPLY" "$T23" flutter 2>&1); rc=$?
new_guard_hash=$(python3 - "$T23/.codex/hooks/block-unstarted-commit.sh" <<'PY'
import hashlib, sys
print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())
PY
)
[ "$rc" != 0 ] && [ "$old_guard_hash" = "$new_guard_hash" ] \
  && ok "场景23 hooks.json 替换失败恢复既有 Codex guard" || { bad "场景23 hooks.json 替换失败未恢复既有 Codex guard (rc=$rc)"; echo "$out" | head -4; }

# ============ V0-ROUNDTRIP：可撤销 Custom 安装 + 一致性/policy/Codex-only smoke ============
T24=$(mk_target v0-roundtrip yes)
mkdir -p "$T24/.git" "$T24/user-owned"
printf 'REAL_INDEX_SENTINEL\n' > "$T24/.git/index"
printf 'USER_FILE_SENTINEL\n' > "$T24/user-owned/keep.txt"
printf 'user config\n' > "$T24/unrelated.conf"
T24_BEFORE=$(snapshot "$T24")
T24_BUNDLE="$TMP/v0-roundtrip-bundle"
out=$(bash "$APPLY" "$T24" flutter --rollback-bundle "$T24_BUNDLE" 2>&1); rc=$?
[ "$rc" = 0 ] && [ -f "$T24/.trellis/scripts/guru/guru_gate.py" ] \
  && ok "V0 rollback-bundle apply 安装 Custom overlay" \
  || { bad "V0 rollback-bundle apply 失败 (rc=$rc)"; echo "$out" | tail -10; }
out=$(bash "$APPLY" --unapply "$T24" "$T24_BUNDLE" 2>&1); rc=$?
T24_AFTER=$(snapshot "$T24")
[ "$rc" = 0 ] && [ "$T24_BEFORE" = "$T24_AFTER" ] \
  && grep -qx 'REAL_INDEX_SENTINEL' "$T24/.git/index" \
  && grep -qx 'USER_FILE_SENTINEL' "$T24/user-owned/keep.txt" \
  && grep -qx 'user config' "$T24/unrelated.conf" \
  && ok "V0 unapply 字节恢复且保留 user-owned/.git" \
  || { bad "V0 unapply 未完整恢复 preimage (rc=$rc)"; echo "$out" | tail -10; }

v0_consistency_check() { # v0_consistency_check <guru-template-root> [events-jsonl]
  python3 - "$1" "${2:-}" <<'PY'
import json
import os
import sys
from pathlib import PurePosixPath

root, events = sys.argv[1:3]
matrix = {
    "docs": ["overlay/README.md"],
    "code": [
        "overlay/apply.sh",
        "overlay/policy/delivery-policy.json",
        "overlay/verify/guru_contract.py",
        "overlay/verify/guru_delivery_policy.py",
    ],
    "tests": [
        "overlay/tests/apply_test.sh",
        "overlay/verify/tests/test_delivery_policy.py",
    ],
}
missing = [f"{layer}:{rel}" for layer, paths in matrix.items() for rel in paths
           if not os.path.isfile(os.path.join(root, rel))]
if missing:
    raise SystemExit("docs/code/tests mismatch: " + ",".join(missing))

readme = open(os.path.join(root, "overlay/README.md"), encoding="utf-8").read()
apply_source = open(os.path.join(root, "overlay/apply.sh"), encoding="utf-8").read()
test_source = open(os.path.join(root, "overlay/tests/apply_test.sh"), encoding="utf-8").read()
for token in ("--rollback-bundle", "--unapply", "apply_test.sh"):
    if token not in readme:
        raise SystemExit(f"docs/code/tests mismatch: README missing {token}")
if "--unapply" not in apply_source or "V0-ROUNDTRIP" not in test_source:
    raise SystemExit("docs/code/tests mismatch: unapply code/test coverage missing")

index = json.load(open(os.path.join(root, "index.json"), encoding="utf-8"))
for entry in index.get("templates", []):
    if not os.path.exists(os.path.join(root, entry["path"])):
        raise SystemExit(f"docs/code/tests mismatch: missing index target {entry['path']}")

verify = os.path.join(root, "overlay/verify")
sys.path.insert(0, verify)
import guru_contract
import guru_delivery_policy as policy

capability = policy.managed_capability_report(parallel=False)
loaded = policy.load_policy(os.path.join(root, "overlay/policy/delivery-policy.json"))
requests = {
    "small_inline": policy.IntakeRequest(
        description="fix typo", affected_paths=(PurePosixPath("lib/ui/label.dart"),)),
    "micro_task": policy.IntakeRequest(
        description="fix typo", affected_paths=(PurePosixPath("lib/ui/label.dart"),), commit_requested=True),
    "lite_task": policy.IntakeRequest(description="bounded behavior change", commit_requested=True),
    "full_chain": policy.IntakeRequest(
        description="change workflow hook gate runtime",
        affected_paths=(PurePosixPath(".trellis/workflow.md"),), commit_requested=True),
}
rows = {name: policy.resolve_delivery_selection(req, loaded, capability_report=capability)
        for name, req in requests.items()}
expected = {
    "small_inline": guru_contract.ROUTE_SMALL_INLINE,
    "micro_task": guru_contract.ROUTE_MICRO_TASK,
    "lite_task": guru_contract.ROUTE_LITE_TASK,
    "full_chain": guru_contract.ROUTE_FULL_CHAIN,
}
for name, selection in rows.items():
    if selection.execution_route != expected[name]:
        raise SystemExit(f"route smoke mismatch: {name} -> {selection.execution_route}")
if rows["full_chain"].risk != guru_contract.RISK_HIGH or "risk_packet" not in rows["full_chain"].required_gate_ids:
    raise SystemExit("route smoke mismatch: full/high risk packet missing")

if events:
    for number, line in enumerate(open(events, encoding="utf-8"), 1):
        if line.strip():
            json.loads(line)
            if "claude" in line.lower():
                raise SystemExit(f"claude plan/event forbidden at line {number}")
PY
}

GURU_TEMPLATE_ROOT="$(cd "$HERE/../.." && pwd)"
v0_consistency_check "$GURU_TEMPLATE_ROOT" \
  && ok "V0 docs/code/tests consistency + 四路由 policy smoke" \
  || bad "V0 consistency/policy smoke 未通过"

V0_FAKE="$TMP/v0-consistency-mismatch"; mkdir -p "$V0_FAKE"
if v0_consistency_check "$V0_FAKE" >/dev/null 2>&1; then
  bad "V0 consistency mismatch 未被阻断"
else
  ok "V0 consistency mismatch fail-closed"
fi

V0_CODEX_EVENTS="$TMP/v0-codex-events.jsonl"
V0_CLAUDE_EVENTS="$TMP/v0-claude-events.jsonl"
printf '{"kind":"plan","provider":"codex"}\n' > "$V0_CODEX_EVENTS"
printf '{"kind":"event","provider":"claude"}\n' > "$V0_CLAUDE_EVENTS"
v0_consistency_check "$GURU_TEMPLATE_ROOT" "$V0_CODEX_EVENTS" \
  && ok "V0 Codex plan/event 放行" || bad "V0 Codex plan/event 被误拦"
if v0_consistency_check "$GURU_TEMPLATE_ROOT" "$V0_CLAUDE_EVENTS" >/dev/null 2>&1; then
  bad "V0 Claude plan/event 未被阻断"
else
  ok "V0 Claude plan/event fail-closed"
fi

echo "----"; echo "结果: $pass 通过 / $failn 失败"
[ "$failn" = 0 ]
