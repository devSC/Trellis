#!/usr/bin/env bash
# apply.sh 安装/升级器测试：三场景（通用项目 / 项目自带镜像 / 旧 core 警告）+ 幂等 + conventions 保护。
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APPLY="$HERE/../apply.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
pass=0; failn=0

ok()   { pass=$((pass+1)); echo "PASS  $1"; }
bad()  { failn=$((failn+1)); echo "FAIL  $1"; }

mk_target() { # mk_target <name> [with_blocking_core]
  local d="$TMP/$1"
  mkdir -p "$d/.trellis/scripts/common" "$d/.trellis/spec/conventions" "$d/.claude"
  if [ "${2:-yes}" = "yes" ]; then
    printf 'def run_blocking_task_hooks():\n    pass\n' > "$d/.trellis/scripts/common/task_utils.py"
  else
    printf 'def run_task_hooks():\n    pass\n' > "$d/.trellis/scripts/common/task_utils.py"
  fi
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
out=$(bash "$APPLY" "$T1" 2>&1); rc=$?
[ "$rc" = 0 ] && ok "场景1 apply 退出码 0" || { bad "场景1 退出码 (rc=$rc)"; echo "$out" | tail -10; }

diff -r "$T1/.agents/skills/client-design-overview-writing" "$T1/.claude/skills/client-design-overview-writing" >/dev/null 2>&1 \
  && ok "场景1 skills 镜像到 .claude/skills 且字节一致" || bad "场景1 .claude/skills 镜像缺失或不一致"

grep -q "my-custom-guard.sh" "$T1/.claude/settings.json" && grep -q "block-unconfirmed-start.sh" "$T1/.claude/settings.json" \
  && ok "场景1 settings.json 合并（用户 hook 保留 + 阻断 hook 接线）" || bad "场景1 settings.json 合并不完整"
python3 -c "import json;d=json.load(open('$T1/.claude/settings.json'));assert d['model']=='opus'" 2>/dev/null \
  && ok "场景1 settings.json 非 hooks 键保留" || bad "场景1 settings.json 用户键丢失"

[ -f "$T1/.trellis/workflow.md" ] && [ -f "$T1/.trellis/spec/harness/index.md" ] \
  && [ -f "$T1/.trellis/spec/guides/golden-path.md" ] && [ -f "$T1/.trellis/spec/guides/index.md" ] \
  && [ -f "$T1/.trellis/spec/conventions/index.md" ] \
  && ok "场景1 workflow + harness + guides(含 index) + conventions/index 同步" || bad "场景1 SSOT 同步不完整"

grep -q "SENTINEL_KEEP_ME" "$T1/.trellis/spec/conventions/project-conventions.md" \
  && ok "场景1 project-conventions.md 未被覆盖" || bad "场景1 项目约定被覆盖！"

grep -q "before_start" "$T1/.trellis/config.yaml" && ok "场景1 config.yaml before_start 接线" || bad "场景1 config 缺 before_start"

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
import sys
if "--sync" in sys.argv:
    open("MIRROR_SENTINEL", "w").write("synced")
sys.exit(0)
EOF
out=$(cd "$T2" && bash "$APPLY" "$T2" 2>&1); rc=$?
[ "$rc" = 0 ] && ok "场景2 apply 退出码 0" || { bad "场景2 退出码 (rc=$rc)"; echo "$out" | tail -5; }
[ -f "$T2/MIRROR_SENTINEL" ] && ok "场景2 项目镜像脚本被调用" || bad "场景2 镜像脚本未被调用"
[ ! -d "$T2/.claude/skills/client-design-overview-writing" ] \
  && ok "场景2 apply 未直写 .claude/skills（交镜像脚本管）" || bad "场景2 不应直写 .claude/skills"
rm -f "$T2/MIRROR_SENTINEL"

# ============ 场景 3：旧 core（缺 before_start 支持）→ 警告但不失败 ============
T3=$(mk_target oldcore no)
out=$(bash "$APPLY" "$T3" 2>&1); rc=$?
[ "$rc" = 0 ] && ok "场景3 旧 core 仅警告不失败" || bad "场景3 退出码应为 0 (rc=$rc)"
printf '%s' "$out" | grep -q "硬 Gate 不会拦截" && ok "场景3 输出含醒目警告" || bad "场景3 缺核心警告"

echo "----"; echo "结果: $pass 通过 / $failn 失败"
[ "$failn" = 0 ]
