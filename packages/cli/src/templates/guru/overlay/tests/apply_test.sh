#!/usr/bin/env bash
# apply.sh 安装/升级器测试：blocking/official Core、项目镜像、幂等和可撤销 ownership。
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
printf 'guru:\n  supervision:\n    adversarial_enabled: true\n' > "$T1/.trellis/config.yaml"
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
grep -q '^    adversarial_enabled: false$' "$T1/.trellis/config.yaml" \
  && ! grep -q 'adversarial_claude_model' "$T1/.trellis/config.yaml" \
  && ok "场景1 Custom 默认 Codex-only：关闭 opposite-provider 且不注入 Claude model" \
  || bad "场景1 config 仍可能默认启动非 Codex adversarial review"
[ -x "$T1/.trellis/scripts/guru/guru_task.py" ] \
  && [ -f "$T1/.trellis/scripts/guru/guru_delivery_policy.py" ] \
  && [ -f "$T1/.trellis/policy/delivery-policy.json" ] \
  && grep -q "guru_after_start.py" "$T1/.trellis/config.yaml" \
  && ok "场景1 delivery policy + guarded lifecycle runtime 已安装" \
  || bad "场景1 缺 delivery policy/guard/after_start runtime"
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

exact_snapshot() { # 类型、mode、文件内容、link target；根级 .git 按 rollback 合同排除
  python3 - "$1" <<'PYS'
import hashlib
import os
import stat
import sys

root = os.path.realpath(sys.argv[1])
digest = hashlib.sha256()
for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
    dirnames[:] = sorted(name for name in dirnames if not (dirpath == root and name == ".git"))
    filenames = sorted(name for name in filenames if not (dirpath == root and name == ".git"))
    for name in [*dirnames, *filenames]:
        path = os.path.join(dirpath, name)
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode):
            kind, payload = "link", os.readlink(path).encode("utf-8", "surrogateescape")
        elif stat.S_ISDIR(info.st_mode):
            kind, payload = "dir", b""
        elif stat.S_ISREG(info.st_mode):
            kind = "file"
            with open(path, "rb") as fh:
                payload = fh.read()
        else:
            kind, payload = "other", b""
        digest.update(f"{rel}\0{kind}\0{stat.S_IMODE(info.st_mode):o}\0".encode())
        digest.update(payload)
        digest.update(b"\0")
print(digest.hexdigest())
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

# ============ 场景 3：official Core（无 blocking before_start）→ compensated Custom lifecycle ============
T3=$(mk_target oldcore no)
out=$(bash "$APPLY" "$T3" 2>&1); rc=$?
[ "$rc" = 0 ] && ok "场景3 official Core compensated apply 通过" || { bad "场景3 official Core apply 失败 (rc=$rc)"; echo "$out" | tail -10; }
printf '%s' "$out" | grep -q "official Core compensated" \
  && ok "场景3 明确报告 compensated capability" || bad "场景3 缺 compensated capability 报告"
grep -q "guru_gate.py check-start" "$T3/.trellis/config.yaml" \
  && bad "场景3 official Core 不得写入无效 before_start hard Gate" \
  || ok "场景3 official Core 未伪装 before_start hard Gate"
[ -x "$T3/.trellis/scripts/guru/guru_task.py" ] \
  && [ -f "$T3/.trellis/scripts/guru/guru_delivery_policy.py" ] \
  && [ -f "$T3/.trellis/policy/delivery-policy.json" ] \
  && grep -q "guru_after_start.py" "$T3/.trellis/config.yaml" \
  && ok "场景3 official Core 可运行 policy/guard/after_start" \
  || bad "场景3 official Core compensated runtime 不完整"
grep -q 'python3 .trellis/scripts/guru/guru_task.py start' "$T3/.trellis/workflow.md" \
  && python3 "$T3/.trellis/scripts/guru/guru_task.py" start --help >/dev/null 2>&1 \
  && ok "场景3 installed workflow 的 Full 正常入口可执行" \
  || bad "场景3 installed workflow 未指向可执行 guarded wrapper"
grep -q '下一步仅可运行 `task.py start`\|然后运行 `task.py start' "$T3/.trellis/workflow.md" \
  && bad "场景3 installed workflow 仍把 direct task.py start 当 Full 正常入口" \
  || ok "场景3 installed workflow 未绕过 guarded wrapper"

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

T14_HIGH=$(mk_target after-create-high-description yes)
mkdir -p "$T14_HIGH/.trellis/tasks/t-high"
printf '%s\n' '{"id":"t-high","title":"bounded cleanup","description":"change workflow hook gate runtime","affected_paths":[".trellis/workflow.md"],"commit_requested":true}' > "$T14_HIGH/.trellis/tasks/t-high/task.json"
TASK_JSON_PATH="$T14_HIGH/.trellis/tasks/t-high/task.json" python3 "$HERE/../hooks/guru_after_create.py" >/dev/null 2>&1
python3 - "$T14_HIGH/.trellis/tasks/t-high" <<'PY'
import json
import os
import sys

task_dir = sys.argv[1]
task = json.load(open(os.path.join(task_dir, "task.json"), encoding="utf-8"))
contract = json.load(open(os.path.join(task_dir, "gate-contract.json"), encoding="utf-8"))
assert task["guru_chain"] == "full"
assert contract["route"] == "full_chain"
assert contract["risk"] == "high"
assert contract["assessment"]["risk_flags"]
assert "execution_policy" not in contract
encoded = json.dumps(contract, sort_keys=True)
assert "managed_parallel" not in encoded
assert "capability_probe_digest" not in encoded
assert '"enforcement_mode": "enforced"' not in encoded
PY
[ "$?" = 0 ] \
  && ok "场景14 high-risk description 生成 honest full_chain/high contract" \
  || bad "场景14 after_create 忽略 high-risk description 或伪造执行能力"

T14_AMBIGUOUS=$(mk_target after-create-ambiguous-description yes)
mkdir -p "$T14_AMBIGUOUS/.trellis/tasks/t-ambiguous"
printf '%s\n' '{"id":"t-ambiguous","title":"Fix unclear task","description":"fix unclear behavior"}' > "$T14_AMBIGUOUS/.trellis/tasks/t-ambiguous/task.json"
TASK_JSON_PATH="$T14_AMBIGUOUS/.trellis/tasks/t-ambiguous/task.json" python3 "$HERE/../hooks/guru_after_create.py" >/dev/null 2>&1
python3 - "$T14_AMBIGUOUS/.trellis/tasks/t-ambiguous" <<'PY'
import json
import os
import sys

task_dir = sys.argv[1]
contract = json.load(open(os.path.join(task_dir, "gate-contract.json"), encoding="utf-8"))
execution = contract["execution_policy"]
assert contract["route"] == "lite_task"
assert contract["risk"] == "medium"
assert execution["brainstorm_required"] is True
assert execution["budget"]["confirmation_batches"] == 1
assert execution["budget"]["started_workers"] == 0
PY
[ "$?" = 0 ] \
  && ok "场景14 显式歧义 description 生成 Lite bounded Brainstorm contract" \
  || bad "场景14 after_create 未把显式歧义绑定到 Lite Brainstorm"

T14_CACHE=$(mk_target after-create-evidence-cache yes)
bash "$APPLY" "$T14_CACHE" >/dev/null 2>&1
git -C "$T14_CACHE" init -q
mkdir -p "$T14_CACHE/lib/ui" "$T14_CACHE/.trellis/tasks/t-cache-prior"
printf 'v1\n' > "$T14_CACHE/lib/ui/button.dart"
python3 - "$T14_CACHE" <<'PY'
import json
import os
import sys

root = os.path.abspath(sys.argv[1])
sys.path.insert(0, os.path.join(root, ".trellis", "scripts", "guru"))
import guru_delivery_policy as policy

request = policy.IntakeRequest(
    description="change local button behavior",
    affected_paths=("lib/ui/button.dart",),
)
selection = policy.resolve_project_delivery_selection(request, root, capability_report={})
assert selection.evidence_reused is False
record = {
    "schema_version": 1,
    "kind": "delivery_evidence_cache",
    "status": "passed",
    "outcome": "passed",
    "evidence_cache_key": selection.evidence_cache_key,
    "target_digest": policy.guru_review_record.target_snapshot_digest(
        root, ["lib/ui/button.dart"], "worktree"
    ),
    "docs_code_test_digest": policy.project_docs_code_test_digest(root),
}
with open(os.path.join(root, ".trellis", "tasks", "t-cache-prior", "verification-evidence.jsonl"), "w", encoding="utf-8") as fh:
    fh.write(json.dumps(record, sort_keys=True) + "\n")
PY
mkdir -p "$T14_CACHE/.trellis/tasks/t-cache-warm"
printf '%s\n' '{"id":"t-cache-warm","description":"change local button behavior","affected_paths":["lib/ui/button.dart"]}' > "$T14_CACHE/.trellis/tasks/t-cache-warm/task.json"
TASK_JSON_PATH="$T14_CACHE/.trellis/tasks/t-cache-warm/task.json" python3 "$T14_CACHE/.trellis/scripts/guru/guru_after_create.py" >/dev/null 2>&1
printf 'v2\n' > "$T14_CACHE/lib/ui/button.dart"
mkdir -p "$T14_CACHE/.trellis/tasks/t-cache-drift"
printf '%s\n' '{"id":"t-cache-drift","description":"change local button behavior","affected_paths":["lib/ui/button.dart"]}' > "$T14_CACHE/.trellis/tasks/t-cache-drift/task.json"
TASK_JSON_PATH="$T14_CACHE/.trellis/tasks/t-cache-drift/task.json" python3 "$T14_CACHE/.trellis/scripts/guru/guru_after_create.py" >/dev/null 2>&1
python3 - "$T14_CACHE" <<'PY'
import json
import os
import sys

root = sys.argv[1]
warm = json.load(open(os.path.join(root, ".trellis", "tasks", "t-cache-warm", "gate-contract.json"), encoding="utf-8"))
drift = json.load(open(os.path.join(root, ".trellis", "tasks", "t-cache-drift", "gate-contract.json"), encoding="utf-8"))
assert warm["execution_policy"]["evidence_reused"] is True
assert warm["execution_policy"]["planning_cost_ratio_percent"] == 70
assert drift["execution_policy"]["evidence_reused"] is False
assert drift["execution_policy"]["planning_cost_ratio_percent"] == 100
PY
[ "$?" = 0 ] \
  && ok "场景14 official after_create 自动复用 exact evidence，target drift 自动失效" \
  || bad "场景14 evidence cache 仅停留在库 API 或 drift 未失效"

T14_REJECTED=$(mk_target after-create-rejected-scope yes)
mkdir -p "$T14_REJECTED/.trellis/tasks/t-rejected"
printf '%s\n' '{"id":"t-rejected","title":"fix typo","affected_paths":["lib/a.dart","lib/a.dart"],"commit_requested":true}' > "$T14_REJECTED/.trellis/tasks/t-rejected/task.json"
TASK_JSON_PATH="$T14_REJECTED/.trellis/tasks/t-rejected/task.json" python3 "$HERE/../hooks/guru_after_create.py" >/dev/null 2>&1
python3 - "$T14_REJECTED/.trellis/tasks/t-rejected" <<'PY'
import json
import os
import sys

task_dir = sys.argv[1]
task = json.load(open(os.path.join(task_dir, "task.json"), encoding="utf-8"))
contract = json.load(open(os.path.join(task_dir, "gate-contract.json"), encoding="utf-8"))
assert task["guru_chain"] == "full"
assert contract["route"] == "full_chain"
assert contract["risk"] == "unknown"
assert contract["assessment"]["risk_flags"] == ["delivery_policy_rejected"]
assert "duplicate affected paths" in contract["assessment"]["reasons"][0]
PY
[ "$?" = 0 ] \
  && ok "场景14 rejected scope fail-closed 到 full_chain/unknown" \
  || bad "场景14 rejected scope 错误回落到较轻 route"

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

# ============ 场景 25：apply 自检失败自动恢复；并发目标漂移时 CAS 拒绝覆盖 ============
T25=$(mk_target partial-apply-recovery no)
mkdir -p "$T25/.git" "$T25/user-owned" "$T25/scripts"
printf 'RECOVERY_INDEX_SENTINEL\n' > "$T25/.git/index"
printf 'RECOVERY_USER_SENTINEL\n' > "$T25/user-owned/keep.txt"
printf 'raise SystemExit(1)\n' > "$T25/scripts/check_workflow_compliance.py"
T25_BEFORE=$(snapshot "$T25")
T25_BUNDLE="$TMP/partial-apply-recovery-bundle"
out=$(bash "$APPLY" "$T25" flutter --rollback-bundle "$T25_BUNDLE" 2>&1); rc=$?
T25_AFTER=$(snapshot "$T25")
if [ "$rc" != 0 ] \
  && [ "$T25_BEFORE" = "$T25_AFTER" ] \
  && [ ! -e "$T25/.trellis/scripts/guru/guru_gate.py" ] \
  && grep -qx 'RECOVERY_INDEX_SENTINEL' "$T25/.git/index" \
  && grep -qx 'RECOVERY_USER_SENTINEL' "$T25/user-owned/keep.txt" \
  && python3 - "$T25_BUNDLE/manifest.json" <<'PY'
import json
import sys

manifest = json.load(open(sys.argv[1], encoding="utf-8"))
assert manifest["state"] == "recovered"
assert manifest["post_apply_digest"] is None
assert manifest["git_internals_owned"] is False
assert manifest["recovery"]["status"] == "succeeded"
PY
then
  ok "场景25 apply 自检失败自动恢复精确 preimage 且不触碰 .git"
else
  bad "场景25 apply 自检失败未自动恢复 (rc=$rc)"
  echo "$out" | tail -12
fi
printf '%s' "$out" | grep -q 'RECOVERED:.*精确 preimage' \
  && ok "场景25 自动恢复输出明确成功状态" || bad "场景25 自动恢复未输出成功状态"
T25_RECOVERED_BEFORE=$(snapshot "$T25")
out=$(bash "$APPLY" --unapply "$T25" "$T25_BUNDLE" 2>&1); rc=$?
T25_RECOVERED_AFTER=$(snapshot "$T25")
[ "$rc" != 0 ] \
  && [ "$T25_RECOVERED_BEFORE" = "$T25_RECOVERED_AFTER" ] \
  && printf '%s' "$out" | grep -q '未处于 applied 状态' \
  && ok "场景25 recovered bundle 不可伪装为成功 unapply" \
  || bad "场景25 recovered bundle 被错误接受为 unapply (rc=$rc)"

T26=$(mk_target partial-apply-cas-drift yes)
mkdir -p "$T26/.git" "$T26/user-owned" "$T26/scripts"
printf 'CAS_INDEX_SENTINEL\n' > "$T26/.git/index"
printf 'CAS_USER_BEFORE\n' > "$T26/user-owned/keep.txt"
cat > "$T26/scripts/check_workflow_compliance.py" <<'PY'
import time

time.sleep(2)
PY
T26_BUNDLE="$TMP/partial-apply-cas-drift-bundle"
T26_OUT="$TMP/partial-apply-cas-drift.out"
bash "$APPLY" "$T26" flutter --rollback-bundle "$T26_BUNDLE" >"$T26_OUT" 2>&1 &
T26_PID=$!
T26_CHECKPOINTED=0
for _ in $(seq 1 300); do
  if python3 - "$T26_BUNDLE/manifest.json" <<'PY' 2>/dev/null
import json
import sys

manifest = json.load(open(sys.argv[1], encoding="utf-8"))
raise SystemExit(0 if manifest.get("recovery", {}).get("status") == "checkpointed" else 1)
PY
  then
    T26_CHECKPOINTED=1
    break
  fi
  sleep 0.01
done
printf 'CAS_USER_EXTERNAL_DRIFT\n' > "$T26/user-owned/keep.txt"
wait "$T26_PID"; rc=$?
if [ "$T26_CHECKPOINTED" = 1 ] \
  && [ "$rc" != 0 ] \
  && grep -qx 'CAS_USER_EXTERNAL_DRIFT' "$T26/user-owned/keep.txt" \
  && grep -qx 'CAS_INDEX_SENTINEL' "$T26/.git/index" \
  && [ -e "$T26/.trellis/scripts/guru/guru_gate.py" ] \
  && python3 - "$T26_BUNDLE/manifest.json" <<'PY'
import json
import sys

manifest = json.load(open(sys.argv[1], encoding="utf-8"))
assert manifest["state"] == "prepared"
assert manifest["post_apply_digest"] is None
assert manifest["recovery"]["status"] == "manual_required"
PY
then
  ok "场景25 checkpoint 后外部漂移使 recovery CAS fail-closed 并保留 bundle"
else
  bad "场景25 外部漂移未使 recovery fail-closed (checkpointed=$T26_CHECKPOINTED rc=$rc)"
  tail -12 "$T26_OUT"
fi
grep -q 'MANUAL RECOVERY REQUIRED' "$T26_OUT" \
  && ok "场景25 CAS 拒绝后输出明确人工恢复指引" || bad "场景25 CAS 拒绝后缺人工恢复指引"
T26_STATUS_TARGET_BEFORE=$(exact_snapshot "$T26")
T26_STATUS_BUNDLE_BEFORE=$(exact_snapshot "$T26_BUNDLE")
status_out=$(bash "$APPLY" --status "$T26" "$T26_BUNDLE" 2>&1); status_rc=$?
verify_out=$(bash "$APPLY" --verify "$T26" "$T26_BUNDLE" 2>&1); verify_rc=$?
if [ "$status_rc" = 0 ] \
  && [ "$verify_rc" != 0 ] \
  && printf '%s' "$status_out" | grep -q '^status=drifted$' \
  && printf '%s' "$verify_out" | grep -q '^status=drifted$' \
  && [ "$T26_STATUS_TARGET_BEFORE" = "$(exact_snapshot "$T26")" ] \
  && [ "$T26_STATUS_BUNDLE_BEFORE" = "$(exact_snapshot "$T26_BUNDLE")" ]
then
  ok "场景25 manual_required prepared bundle 报 drifted 且 status/verify 零 mutation"
else
  bad "场景25 manual_required prepared bundle 被假报 not-applied (status=$status_rc verify=$verify_rc)"
fi
T26_MANUAL_BEFORE=$(snapshot "$T26")
out=$(bash "$APPLY" --unapply "$T26" "$T26_BUNDLE" 2>&1); rc=$?
T26_MANUAL_AFTER=$(snapshot "$T26")
[ "$rc" != 0 ] \
  && [ "$T26_MANUAL_BEFORE" = "$T26_MANUAL_AFTER" ] \
  && grep -qx 'CAS_USER_EXTERNAL_DRIFT' "$T26/user-owned/keep.txt" \
  && printf '%s' "$out" | grep -q '未处于 applied 状态' \
  && ok "场景25 manual_required bundle 不可伪装为成功 unapply" \
  || bad "场景25 manual_required bundle 被错误接受为 unapply (rc=$rc)"

# ============ 场景 26：rollback bundle 路径不能用 symlink 绕回目标内部 ============
T27=$(mk_target rollback-bundle-symlink yes)
mkdir -p "$T27/inside-bundle"
T27_LINK="$TMP/rollback-bundle-link"
ln -s "$T27/inside-bundle" "$T27_LINK"
out=$(bash "$APPLY" "$T27" flutter --rollback-bundle "$T27_LINK" 2>&1); rc=$?
if [ "$rc" != 0 ] \
  && [ ! -e "$T27/inside-bundle/preimage" ] \
  && printf '%s' "$out" | grep -q 'rollback bundle 路径不得是符号链接'
then
  ok "场景26 rollback bundle symlink 绕回目标内部时 fail-closed"
else
  bad "场景26 rollback bundle symlink 未在复制前阻断 (rc=$rc)"
  echo "$out" | tail -8
fi

# ============ 场景 27：无关用户改动不阻断 managed-asset unapply ==========
T28=$(mk_target managed-unapply-unrelated yes)
mkdir -p "$T28/.git" "$T28/user-owned"
printf 'MANAGED_UNRELATED_INDEX\n' > "$T28/.git/index"
printf 'USER_BEFORE\n' > "$T28/user-owned/keep.txt"
T28_EXPECTED="$TMP/managed-unapply-unrelated-expected"
python3 - "$T28" "$T28_EXPECTED" <<'PY'
import shutil
import sys

shutil.copytree(sys.argv[1], sys.argv[2], symlinks=True)
PY
T28_BUNDLE="$TMP/managed-unapply-unrelated-bundle"
out=$(bash "$APPLY" "$T28" flutter --rollback-bundle "$T28_BUNDLE" 2>&1); rc=$?
[ "$rc" = 0 ] && python3 - "$T28_BUNDLE/manifest.json" <<'PY'
import json
import sys

manifest = json.load(open(sys.argv[1], encoding="utf-8"))
assert manifest["schema_version"] == 2
assert manifest["state"] == "applied"
assert manifest["managed_assets"]["count"] > 0
PY
if [ "$?" = 0 ]; then
  ok "场景27 apply 发布 deterministic managed-asset manifest"
else
  bad "场景27 managed-asset manifest 未发布 (rc=$rc)"
  echo "$out" | tail -10
fi
printf 'USER_AFTER\n' > "$T28/user-owned/keep.txt"
printf 'USER_NEW\n' > "$T28/user-owned/new.txt"
printf 'TOP_LEVEL_NEW\n' > "$T28/new-user-file.txt"
printf 'USER_AFTER\n' > "$T28_EXPECTED/user-owned/keep.txt"
printf 'USER_NEW\n' > "$T28_EXPECTED/user-owned/new.txt"
printf 'TOP_LEVEL_NEW\n' > "$T28_EXPECTED/new-user-file.txt"
out=$(bash "$APPLY" --unapply "$T28" "$T28_BUNDLE" 2>&1); rc=$?
if [ "$rc" = 0 ] \
  && [ "$(exact_snapshot "$T28")" = "$(exact_snapshot "$T28_EXPECTED")" ] \
  && grep -qx 'MANAGED_UNRELATED_INDEX' "$T28/.git/index" \
  && [ ! -e "$T28/.trellis/scripts/guru/guru_gate.py" ]
then
  ok "场景27 unapply 只恢复 managed assets 并逐字节保留无关用户改动/.git"
else
  bad "场景27 无关改动错误阻断或被 unapply 覆盖 (rc=$rc)"
  echo "$out" | tail -10
fi

# ============ 场景 28：managed asset 漂移在首个 target mutation 前 fail-closed ==========
T29=$(mk_target managed-unapply-conflict yes)
mkdir -p "$T29/user-owned"
printf 'USER_BEFORE\n' > "$T29/user-owned/keep.txt"
T29_BUNDLE="$TMP/managed-unapply-conflict-bundle"
bash "$APPLY" "$T29" flutter --rollback-bundle "$T29_BUNDLE" >/dev/null 2>&1
printf '\nMANAGED_USER_EDIT\n' >> "$T29/.trellis/scripts/guru/guru_gate.py"
printf 'USER_AFTER\n' > "$T29/user-owned/keep.txt"
T29_TARGET_BEFORE=$(exact_snapshot "$T29")
T29_BUNDLE_BEFORE=$(exact_snapshot "$T29_BUNDLE")
out=$(bash "$APPLY" --unapply "$T29" "$T29_BUNDLE" 2>&1); rc=$?
if [ "$rc" != 0 ] \
  && [ "$T29_TARGET_BEFORE" = "$(exact_snapshot "$T29")" ] \
  && [ "$T29_BUNDLE_BEFORE" = "$(exact_snapshot "$T29_BUNDLE")" ] \
  && grep -q 'MANAGED_USER_EDIT' "$T29/.trellis/scripts/guru/guru_gate.py" \
  && grep -qx 'USER_AFTER' "$T29/user-owned/keep.txt" \
  && [ -e "$T29/.trellis/scripts/guru/guru_contract.py" ] \
  && printf '%s' "$out" | grep -q 'managed asset 已漂移'
then
  ok "场景28 managed asset 漂移时整批 unapply 零 target/bundle mutation"
else
  bad "场景28 managed asset 漂移未在首个 mutation 前阻断 (rc=$rc)"
  echo "$out" | tail -10
fi

# ============ 场景 29：overlay-created 目录内用户文件保留，目录仅空时剪枝 ==========
T30=$(mk_target managed-unapply-user-child yes)
T30_BUNDLE="$TMP/managed-unapply-user-child-bundle"
bash "$APPLY" "$T30" flutter --rollback-bundle "$T30_BUNDLE" >/dev/null 2>&1
printf 'USER_CHILD_KEEP\n' > "$T30/.agents/skills/user-owned-note.txt"
out=$(bash "$APPLY" --unapply "$T30" "$T30_BUNDLE" 2>&1); rc=$?
if [ "$rc" = 0 ] \
  && grep -qx 'USER_CHILD_KEEP' "$T30/.agents/skills/user-owned-note.txt" \
  && [ ! -e "$T30/.agents/skills/requirement-writing" ] \
  && [ ! -e "$T30/.trellis/scripts/guru/guru_gate.py" ] \
  && python3 - "$T30_BUNDLE/manifest.json" <<'PY'
import json
import sys

manifest = json.load(open(sys.argv[1], encoding="utf-8"))
assert manifest["state"] == "restored"
retained = manifest["unapply"]["retained_user_directories"]
assert ".agents" in retained
assert ".agents/skills" in retained
PY
then
  ok "场景29 overlay-created 目录只移除 managed children，用户文件/非空目录保留"
else
  bad "场景29 用户新增 child 被删除或错误阻断 (rc=$rc)"
  echo "$out" | tail -10
fi

# ============ 场景 30：managed evidence/manifest 篡改均在 target mutation 前阻断 ==========
T31=$(mk_target managed-unapply-tamper yes)
T31_BUNDLE="$TMP/managed-unapply-tamper-bundle"
bash "$APPLY" "$T31" flutter --rollback-bundle "$T31_BUNDLE" >/dev/null 2>&1
cp "$T31_BUNDLE/managed-assets.json" "$TMP/managed-assets.original.json"
printf ' ' >> "$T31_BUNDLE/managed-assets.json"
T31_TARGET_BEFORE=$(exact_snapshot "$T31")
out=$(bash "$APPLY" --unapply "$T31" "$T31_BUNDLE" 2>&1); rc=$?
[ "$rc" != 0 ] \
  && [ "$T31_TARGET_BEFORE" = "$(exact_snapshot "$T31")" ] \
  && printf '%s' "$out" | grep -q 'managed manifest integrity 不匹配' \
  && ok "场景30 managed evidence 篡改在 target mutation 前阻断" \
  || { bad "场景30 managed evidence 篡改未阻断 (rc=$rc)"; echo "$out" | tail -8; }
cp "$TMP/managed-assets.original.json" "$T31_BUNDLE/managed-assets.json"
python3 - "$T31_BUNDLE/manifest.json" <<'PY'
import json
import sys

path = sys.argv[1]
manifest = json.load(open(path, encoding="utf-8"))
manifest["tampered"] = True
with open(path, "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, ensure_ascii=False, indent=2, sort_keys=True)
    fh.write("\n")
PY
out=$(bash "$APPLY" --unapply "$T31" "$T31_BUNDLE" 2>&1); rc=$?
[ "$rc" != 0 ] \
  && [ "$T31_TARGET_BEFORE" = "$(exact_snapshot "$T31")" ] \
  && printf '%s' "$out" | grep -q 'manifest integrity 不匹配' \
  && ok "场景30 top-level manifest 篡改在 target mutation 前阻断" \
  || { bad "场景30 top-level manifest 篡改未阻断 (rc=$rc)"; echo "$out" | tail -8; }

# ============ 场景 31：legacy schema-v1 applied bundle 保留 whole-target CAS fallback ==========
T32=$(mk_target legacy-unapply-fallback yes)
T32_BEFORE=$(exact_snapshot "$T32")
T32_BUNDLE="$TMP/legacy-unapply-fallback-bundle"
bash "$APPLY" "$T32" flutter --rollback-bundle "$T32_BUNDLE" >/dev/null 2>&1
python3 - "$T32_BUNDLE/manifest.json" <<'PY'
import json
import os
import sys

path = sys.argv[1]
manifest = json.load(open(path, encoding="utf-8"))
manifest["schema_version"] = 1
manifest.pop("managed_assets", None)
with open(path, "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, ensure_ascii=False, indent=2, sort_keys=True)
    fh.write("\n")
bundle = os.path.dirname(path)
os.unlink(os.path.join(bundle, "managed-assets.json"))
os.unlink(os.path.join(bundle, "manifest.sha256"))
PY
out=$(bash "$APPLY" --unapply "$T32" "$T32_BUNDLE" 2>&1); rc=$?
[ "$rc" = 0 ] \
  && [ "$T32_BEFORE" = "$(exact_snapshot "$T32")" ] \
  && ok "场景31 legacy applied bundle 沿用 whole-target exact-digest unapply" \
  || { bad "场景31 legacy schema-v1 fallback 失效 (rc=$rc)"; echo "$out" | tail -8; }

# ============ CUSTOM-LIFECYCLE：只读 plan/status/verify + 显式 upgrade 回滚到紧邻 pre-state ==========
out=$(bash "$APPLY" --help 2>&1); rc=$?
if [ "$rc" = 0 ]; then
  help_ok=1
  for token in --plan --status --verify --upgrade --unapply --rollback-bundle; do
    printf '%s' "$out" | grep -q -- "$token" || help_ok=0
  done
  [ "$help_ok" = 1 ] && ok "Custom lifecycle help 完整列出兼容命令" || bad "Custom lifecycle help 缺命令"
else
  bad "Custom lifecycle --help 失败 (rc=$rc)"
fi

T33=$(mk_target custom-lifecycle yes)
mkdir -p "$T33/user-owned"
printf 'UPGRADE_USER_FILE\n' > "$T33/user-owned/keep.txt"
T33_USAGE_BEFORE=$(exact_snapshot "$T33")
out=$(bash "$APPLY" --upgrade "$T33" flutter 2>&1); rc=$?
[ "$rc" = 2 ] \
  && printf '%s' "$out" | grep -q -- '--upgrade 必须指定新的 --rollback-bundle' \
  && [ "$T33_USAGE_BEFORE" = "$(exact_snapshot "$T33")" ] \
  && ok "Custom lifecycle upgrade 缺新 bundle 时按 usage 阻断且零 mutation" \
  || { bad "Custom lifecycle upgrade 缺 bundle 未阻断 (rc=$rc)"; echo "$out" | tail -8; }
T33_PLAN_BUNDLE="$TMP/custom-lifecycle-plan-bundle"
mkdir -p "$T33_PLAN_BUNDLE"
T33_PLAN_TARGET_BEFORE=$(exact_snapshot "$T33")
T33_PLAN_BUNDLE_BEFORE=$(exact_snapshot "$T33_PLAN_BUNDLE")
out=$(bash "$APPLY" --plan "$T33" flutter --rollback-bundle "$T33_PLAN_BUNDLE" 2>&1); rc=$?
if [ "$rc" = 0 ] \
  && printf '%s' "$out" | grep -q '^status=ready$' \
  && printf '%s' "$out" | grep -q '^mutation=none$' \
  && [ "$T33_PLAN_TARGET_BEFORE" = "$(exact_snapshot "$T33")" ] \
  && [ "$T33_PLAN_BUNDLE_BEFORE" = "$(exact_snapshot "$T33_PLAN_BUNDLE")" ]
then
  ok "Custom lifecycle plan 对 target/bundle 字节只读"
else
  bad "Custom lifecycle plan 非只读或输出不稳定 (rc=$rc)"
  echo "$out" | tail -8
fi

T33_MISSING_BUNDLE="$TMP/custom-lifecycle-not-applied"
T33_NOT_APPLIED_BEFORE=$(exact_snapshot "$T33")
out=$(bash "$APPLY" --status "$T33" "$T33_MISSING_BUNDLE" 2>&1); rc=$?
[ "$rc" = 0 ] \
  && printf '%s' "$out" | grep -q '^status=not-applied$' \
  && [ "$T33_NOT_APPLIED_BEFORE" = "$(exact_snapshot "$T33")" ] \
  && [ ! -e "$T33_MISSING_BUNDLE" ] \
  && ok "Custom lifecycle status 对未安装 target 稳定只读" \
  || { bad "Custom lifecycle not-applied status 错误 (rc=$rc)"; echo "$out" | tail -8; }

T33_BUNDLE="$TMP/custom-lifecycle-apply-bundle"
out=$(bash "$APPLY" "$T33" flutter --rollback-bundle "$T33_BUNDLE" 2>&1); rc=$?
[ "$rc" = 0 ] || { bad "Custom lifecycle 基线 apply 失败 (rc=$rc)"; echo "$out" | tail -10; }
T33_CURRENT_TARGET_BEFORE=$(exact_snapshot "$T33")
T33_CURRENT_BUNDLE_BEFORE=$(exact_snapshot "$T33_BUNDLE")
status_out=$(bash "$APPLY" --status "$T33" "$T33_BUNDLE" 2>&1); status_rc=$?
verify_out=$(bash "$APPLY" --verify "$T33" "$T33_BUNDLE" 2>&1); verify_rc=$?
if [ "$status_rc" = 0 ] \
  && [ "$verify_rc" = 0 ] \
  && printf '%s' "$status_out" | grep -q '^status=installed-current$' \
  && printf '%s' "$verify_out" | grep -q '^status=installed-current$' \
  && [ "$T33_CURRENT_TARGET_BEFORE" = "$(exact_snapshot "$T33")" ] \
  && [ "$T33_CURRENT_BUNDLE_BEFORE" = "$(exact_snapshot "$T33_BUNDLE")" ]
then
  ok "Custom lifecycle status/verify 复用 managed evidence 且字节只读"
else
  bad "Custom lifecycle installed-current status/verify 失败 (status=$status_rc verify=$verify_rc)"
  echo "$status_out" | tail -5
  echo "$verify_out" | tail -5
fi

printf '\nUPGRADE_PRESTATE_MANAGED_DRIFT\n' >> "$T33/.trellis/scripts/guru/guru_gate.py"
printf '\nSLOT-99: UPGRADE_CONVENTION_KEEP\n' >> "$T33/.trellis/spec/conventions/project-conventions.md"
printf '\nuser_upgrade_setting: keep\n' >> "$T33/.trellis/config.yaml"
T33_DRIFT_TARGET_BEFORE=$(exact_snapshot "$T33")
T33_DRIFT_BUNDLE_BEFORE=$(exact_snapshot "$T33_BUNDLE")
status_out=$(bash "$APPLY" --status "$T33" "$T33_BUNDLE" 2>&1); status_rc=$?
verify_out=$(bash "$APPLY" --verify "$T33" "$T33_BUNDLE" 2>&1); verify_rc=$?
if [ "$status_rc" = 0 ] \
  && [ "$verify_rc" != 0 ] \
  && printf '%s' "$status_out" | grep -q '^status=drifted$' \
  && printf '%s' "$verify_out" | grep -q '^status=drifted$' \
  && [ "$T33_DRIFT_TARGET_BEFORE" = "$(exact_snapshot "$T33")" ] \
  && [ "$T33_DRIFT_BUNDLE_BEFORE" = "$(exact_snapshot "$T33_BUNDLE")" ]
then
  ok "Custom lifecycle managed drift：status 报告、verify 非零、双方零 mutation"
else
  bad "Custom lifecycle managed drift 未被只读检测 (status=$status_rc verify=$verify_rc)"
  echo "$status_out" | tail -5
  echo "$verify_out" | tail -5
fi

T33_PRE_UPGRADE=$(exact_snapshot "$T33")
T33_UPGRADE_BUNDLE="$TMP/custom-lifecycle-upgrade-bundle"
out=$(bash "$APPLY" --upgrade "$T33" flutter --rollback-bundle "$T33_UPGRADE_BUNDLE" 2>&1); rc=$?
if [ "$rc" = 0 ] \
  && printf '%s' "$out" | grep -q 'guru overlay 显式升级' \
  && grep -q 'UPGRADE_CONVENTION_KEEP' "$T33/.trellis/spec/conventions/project-conventions.md" \
  && grep -q 'user_upgrade_setting: keep' "$T33/.trellis/config.yaml" \
  && ! grep -q 'UPGRADE_PRESTATE_MANAGED_DRIFT' "$T33/.trellis/scripts/guru/guru_gate.py"
then
  ok "Custom lifecycle upgrade 复用 apply 并保留用户 config/conventions"
else
  bad "Custom lifecycle upgrade 未刷新 managed 内容或丢用户约定 (rc=$rc)"
  echo "$out" | tail -10
fi
out=$(bash "$APPLY" --verify "$T33" "$T33_UPGRADE_BUNDLE" 2>&1); rc=$?
[ "$rc" = 0 ] && printf '%s' "$out" | grep -q '^status=installed-current$' \
  && ok "Custom lifecycle upgrade bundle 可立即 verify" \
  || { bad "Custom lifecycle upgrade verify 失败 (rc=$rc)"; echo "$out" | tail -8; }
out=$(bash "$APPLY" --unapply "$T33" "$T33_UPGRADE_BUNDLE" 2>&1); rc=$?
[ "$rc" = 0 ] \
  && [ "$T33_PRE_UPGRADE" = "$(exact_snapshot "$T33")" ] \
  && grep -q 'UPGRADE_PRESTATE_MANAGED_DRIFT' "$T33/.trellis/scripts/guru/guru_gate.py" \
  && grep -q 'UPGRADE_CONVENTION_KEEP' "$T33/.trellis/spec/conventions/project-conventions.md" \
  && grep -q 'user_upgrade_setting: keep' "$T33/.trellis/config.yaml" \
  && ok "Custom lifecycle upgrade->unapply 精确恢复紧邻升级前状态" \
  || { bad "Custom lifecycle upgrade rollback 未恢复 immediate pre-state (rc=$rc)"; echo "$out" | tail -8; }

T34=$(mk_target custom-lifecycle-tamper yes)
T34_BUNDLE="$TMP/custom-lifecycle-tamper-bundle"
bash "$APPLY" "$T34" flutter --rollback-bundle "$T34_BUNDLE" >/dev/null 2>&1
printf ' ' >> "$T34_BUNDLE/managed-assets.json"
T34_TARGET_BEFORE=$(exact_snapshot "$T34")
T34_BUNDLE_BEFORE=$(exact_snapshot "$T34_BUNDLE")
status_out=$(bash "$APPLY" --status "$T34" "$T34_BUNDLE" 2>&1); status_rc=$?
verify_out=$(bash "$APPLY" --verify "$T34" "$T34_BUNDLE" 2>&1); verify_rc=$?
if [ "$status_rc" = 0 ] \
  && [ "$verify_rc" != 0 ] \
  && printf '%s' "$status_out" | grep -q '^status=drifted$' \
  && printf '%s' "$verify_out" | grep -q 'managed manifest integrity 不匹配' \
  && [ "$T34_TARGET_BEFORE" = "$(exact_snapshot "$T34")" ] \
  && [ "$T34_BUNDLE_BEFORE" = "$(exact_snapshot "$T34_BUNDLE")" ]
then
  ok "Custom lifecycle bundle tamper：status/verify 检出且零 mutation"
else
  bad "Custom lifecycle bundle tamper 未 fail-closed (status=$status_rc verify=$verify_rc)"
  echo "$status_out" | tail -5
  echo "$verify_out" | tail -5
fi

T_ROUTE_IOS=$(mk_target route-contract-ios yes)
out=$(bash "$APPLY" "$T_ROUTE_IOS" ios 2>&1); rc=$?
if [ "$rc" = 0 ] \
  && [ -f "$T_ROUTE_IOS/.agents/skills/ios-small-iteration-dev/SKILL.md" ] \
  && grep -q '0/0/1/1 batch' "$T_ROUTE_IOS/.agents/skills/ios-small-iteration-dev/SKILL.md" \
  && grep -q '官方标准 task' "$T_ROUTE_IOS/.trellis/workflow.md" \
  && grep -q 'bounded Brainstorm' "$T_ROUTE_IOS/.trellis/workflow.md"
then
  ok "四端路由安装：iOS standard Lite task/one-confirmation contract 可读"
else
  bad "四端路由安装：iOS skill/workflow contract 缺失 (rc=$rc)"
  echo "$out" | tail -8
fi

v0_consistency_check() { # v0_consistency_check <guru-template-root> [events-jsonl]
  python3 - "$1" "${2:-}" <<'PY'
import json
import os
import sys
from pathlib import PurePosixPath

root, events = sys.argv[1:3]
matrix = {
    "docs": [
        "overlay/README.md",
        "workflows/guru-client-workflow.md",
        "workflows/guru-go-workflow.md",
        "workflows/guru-h5-workflow.md",
        "workflows/guru-ios-workflow.md",
        "overlay/agents-skills/client-small-iteration-dev/SKILL.md",
        "overlay/agents-skills/go-small-iteration-dev/SKILL.md",
        "overlay/agents-skills/h5-small-iteration-dev/SKILL.md",
        "overlay/agents-skills/ios-small-iteration-dev/SKILL.md",
    ],
    "code": [
        "overlay/apply.sh",
        "overlay/policy/delivery-policy.json",
        "overlay/verify/guru_contract.py",
        "overlay/verify/guru_config_patch.py",
        "overlay/verify/guru_delivery_policy.py",
        "overlay/verify/guru_gate.py",
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

for workflow in (
    "workflows/guru-client-workflow.md",
    "workflows/guru-go-workflow.md",
    "workflows/guru-h5-workflow.md",
    "workflows/guru-ios-workflow.md",
):
    content = open(os.path.join(root, workflow), encoding="utf-8").read()
    if "python3 .trellis/scripts/guru/guru_task.py start" not in content:
        raise SystemExit(f"docs/code/tests mismatch: {workflow} missing guarded Full entry")
    if "下一步仅可运行 `task.py start`" in content or "然后运行 `task.py start" in content:
        raise SystemExit(f"docs/code/tests mismatch: {workflow} documents direct Full start")
    if "host-inline" not in content or "deterministic_final" not in content:
        raise SystemExit(f"docs/code/tests mismatch: {workflow} lost Lite execution path")
    if "overview/detail 仍要当前 digest 双 clean" in content:
        raise SystemExit(f"docs/code/tests mismatch: {workflow} restored stale Lite planning review")
    for stale in ("lite 不强制", "lite bounded", "轻量链允许", "Gate 口径不降"):
        if stale in content:
            raise SystemExit(f"docs/code/tests mismatch: {workflow} restored stale Lite Full-Gate phrase {stale}")
    for required in (
        "官方 `task.py create`",
        "repo evidence",
        "bounded Brainstorm",
        "一次需求确认",
        "Worker 0",
        "无 Overview/Detail planning review",
        "0/0/1/1 batch",
        "commit intent",
        "selection_generation",
        "scope_fingerprint",
        "首次写入后只允许升级",
        "Full 在实现 Worker 前",
        "不得再以 requirements/detail/commit",
        "不得运行 opposite-provider adversarial worker",
        "以下 2.1/2.2 的 `check-implementation`、dispatcher 和 Worker 协议仅适用于 Full",
    ):
        if required not in content:
            raise SystemExit(f"docs/code/tests mismatch: {workflow} missing route boundary: {required}")
    for stale in (
        "Lite 直接 host-inline 实现并运行 scoped deterministic_final，确认 0",
        "no pre-code review/confirm/Worker",
        "Lite=compact intake",
        "low + commit -> micro_task",
    ):
        if stale in content:
            raise SystemExit(f"docs/code/tests mismatch: {workflow} retains obsolete route contract: {stale}")
    for stale in ("**light 链**", "light=design.md", "默认写入 `guru_chain: full`"):
        if stale in content:
            raise SystemExit(f"docs/code/tests mismatch: {workflow} retains contradictory Lite planning path: {stale}")

for skill in (
    "overlay/agents-skills/client-small-iteration-dev/SKILL.md",
    "overlay/agents-skills/go-small-iteration-dev/SKILL.md",
    "overlay/agents-skills/h5-small-iteration-dev/SKILL.md",
    "overlay/agents-skills/ios-small-iteration-dev/SKILL.md",
):
    content = open(os.path.join(root, skill), encoding="utf-8").read()
    for required in (
        "官方 `task.py create`",
        "repo evidence",
        "bounded Brainstorm",
        "task-local `prd.md`",
        "确认一次",
        "Worker 0",
        "无 Overview/Detail planning review",
        "`selection_generation`",
        "`scope_fingerprint`",
        "High-risk/unknown-high",
        "首次写入后只允许升级",
        "0/0/1/1 batch",
        "确认后自动",
    ):
        if required not in content:
            raise SystemExit(f"docs/code/tests mismatch: {skill} missing Lite route contract: {required}")
    for stale in (
        "overview/detail 仍需当前 digest 两条 clean",
        "进入轻量链（prd 简版 + 所碰层 design 合同 + 实现/验证）",
        "每步人工 Gate",
        "Lite 固定为 compact intake",
    ):
        if stale in content:
            raise SystemExit(f"docs/code/tests mismatch: {skill} retains Lite Full-Gate path: {stale}")

gate_help = open(os.path.join(root, "overlay/verify/guru_gate.py"), encoding="utf-8").read()
if "`gate-contract.json.route` 是执行权威" not in gate_help or "light 仅是存量" not in gate_help:
    raise SystemExit("docs/code/tests mismatch: guru_gate usage still derives Lite from guru_chain/light")
if "after_create 默认 full" in gate_help:
    raise SystemExit("docs/code/tests mismatch: guru_gate usage retains obsolete after_create default")
for token in (
    "verification-evidence.jsonl",
    "deterministic_final",
    "selection_generation",
    "scope_fingerprint",
    "target_digest",
    "docs_code_test_consistency",
    "spec_sync",
):
    if token not in gate_help:
        raise SystemExit(f"docs/code/tests mismatch: guru_gate missing Lite exact verification evidence field {token}")

readme = open(os.path.join(root, "overlay/README.md"), encoding="utf-8").read()
apply_source = open(os.path.join(root, "overlay/apply.sh"), encoding="utf-8").read()
test_source = open(os.path.join(root, "overlay/tests/apply_test.sh"), encoding="utf-8").read()
for token in (
    "commit intent",
    "selection_generation",
    "scope_fingerprint",
    "官方 `task.py create`",
    "bounded Brainstorm",
    "0/0/1/1 batch",
    "verification-evidence.jsonl",
    "target_digest",
    "docs_code_test_consistency",
    "spec_sync",
    "不得生成 Claude plan/event",
    "adversarial_enabled: false",
):
    if token not in readme:
        raise SystemExit(f"docs/code/tests mismatch: README missing route contract {token}")
for token in ("--plan", "--status", "--verify", "--upgrade", "--rollback-bundle", "--unapply", "apply_test.sh"):
    if token not in readme:
        raise SystemExit(f"docs/code/tests mismatch: README missing {token}")
for token in ("--plan", "--status", "--verify", "--upgrade", "--unapply"):
    if token not in apply_source:
        raise SystemExit(f"docs/code/tests mismatch: apply.sh missing {token}")
if "V0-ROUNDTRIP" not in test_source or "CUSTOM-LIFECYCLE" not in test_source:
    raise SystemExit("docs/code/tests mismatch: lifecycle code/test coverage missing")
if any("manual_required" not in source for source in (readme, apply_source, test_source)):
    raise SystemExit("docs/code/tests mismatch: failed-apply recovery coverage missing")
if any("managed-assets.json" not in source for source in (readme, apply_source, test_source)):
    raise SystemExit("docs/code/tests mismatch: managed-asset unapply coverage missing")

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
        description="fix typo", affected_paths=(PurePosixPath("lib/ui/label.dart"),), commit_requested=True),
    "micro_task": policy.IntakeRequest(
        description="change local validation behavior",
        affected_paths=(PurePosixPath("lib/validation.dart"),),
        requirements_clear=True,
        coupling="local",
        reversible=True,
        verification_scope="focused",
    ),
    "lite_task": policy.IntakeRequest(description="bounded behavior change"),
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

V0_STALE="$TMP/v0-stale-lite-contract"
mkdir -p "$V0_STALE"
cp -R "$GURU_TEMPLATE_ROOT/." "$V0_STALE/"
printf '\noverview/detail 仍需当前 digest 两条 clean\n' >> "$V0_STALE/overlay/agents-skills/client-small-iteration-dev/SKILL.md"
if v0_consistency_check "$V0_STALE" >/dev/null 2>&1; then
  bad "V0 stale Lite Full-Gate contract 未被阻断"
else
  ok "V0 stale Lite Full-Gate contract fail-closed"
fi

V0_ZERO_CONFIRM="$TMP/v0-zero-confirm-lite-contract"
mkdir -p "$V0_ZERO_CONFIRM"
cp -R "$GURU_TEMPLATE_ROOT/." "$V0_ZERO_CONFIRM/"
printf '\nLite 直接 host-inline 实现并运行 scoped deterministic_final，确认 0、Worker 0、无 pre-code Gate。\n' >> "$V0_ZERO_CONFIRM/workflows/guru-client-workflow.md"
if v0_consistency_check "$V0_ZERO_CONFIRM" >/dev/null 2>&1; then
  bad "V0 Lite zero-confirmation contract 未被阻断"
else
  ok "V0 Lite zero-confirmation contract fail-closed"
fi

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
