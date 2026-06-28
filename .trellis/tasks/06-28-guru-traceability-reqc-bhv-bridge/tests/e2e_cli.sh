#!/usr/bin/env bash
# CLI e2e：通过子进程驱动 guru_gate.py main() 分支 + 退出码（unit 测试直调函数绕过了 dispatch）。
# 覆盖：trace-aggregate fail-closed 拒写退出码、含 traceability 写入退出码、--require-req-uc 退出码、
#       trace-matrix 旧 task 默认不拦退出码、help 含新命令。
set -u
REPO="$(cd "$(dirname "$0")/../../../.." && pwd)"
GATE="$REPO/guru-template/overlay/verify/guru_gate.py"
PASS=0
FAIL=0
note() { echo "  [$1] $2"; if [ "$1" = "PASS" ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export GURU_GATE_ALLOW_ABS=1

mk_prd() { mkdir -p "$1"; cat > "$1/prd.md" <<'EOF'
# feat
### BHV-001 [REQ-UC-005] 选择
Given/When/Then P0 失败 验收 未决
EOF
cat > "$1/design.md" <<'EOF'
# d
## §1
BHV-001 owner
## §2
### UNIT-pick
承接 BHV-001 测试映射
EOF
}

echo "== e2e: help 含新命令 =="
HELP="$(python3 "$GATE" 2>&1 || true)"
echo "$HELP" | grep -q "trace-aggregate" && note PASS "help 含 trace-aggregate" || note FAIL "help 缺 trace-aggregate"
echo "$HELP" | grep -q -- "--require-req-uc" && note PASS "help 含 --require-req-uc" || note FAIL "help 缺 --require-req-uc"

echo "== e2e: trace-aggregate fail-closed 退出码 =="
V_NOEXC="$TMP/docs/v-noexc"; mkdir -p "$V_NOEXC"
cat > "$V_NOEXC/manifest.yaml" <<'EOF'
version: v1.0.0
app_version: 1.0.0
status: draft
canonical_excludes: [snapshots, changes]
EOF
T1="$TMP/.trellis/tasks/t1"; mk_prd "$T1"
echo "{\"requirement_package\": \"$V_NOEXC\"}" > "$T1/task.json"
( cd "$TMP" && python3 "$GATE" trace-aggregate "$V_NOEXC" >/dev/null 2>&1 )
[ $? -eq 2 ] && note PASS "excludes 不含 traceability → 退出码 2（拒写）" || note FAIL "拒写退出码错"
[ ! -f "$V_NOEXC/traceability.md" ] && note PASS "拒写未生成文件" || note FAIL "拒写却生成了文件"

echo "== e2e: trace-aggregate 含 traceability 写入退出码 =="
V_OK="$TMP/docs/v-ok"; mkdir -p "$V_OK"
cat > "$V_OK/manifest.yaml" <<'EOF'
version: v1.0.0
app_version: 1.0.0
status: draft
canonical_excludes: [snapshots, changes, traceability]
EOF
T2="$TMP/.trellis/tasks/t2"; mk_prd "$T2"
echo "{\"requirement_package\": \"$V_OK\"}" > "$T2/task.json"
( cd "$TMP" && python3 "$GATE" trace-aggregate "$V_OK" >/dev/null 2>&1 )
[ $? -eq 0 ] && note PASS "excludes 含 traceability → 退出码 0" || note FAIL "写入退出码错"
[ -f "$V_OK/traceability.md" ] && note PASS "生成 traceability.md" || note FAIL "未生成 traceability.md"
grep -q "REQ-UC-005" "$V_OK/traceability.md" && note PASS "traceability 含 REQ-UC-005" || note FAIL "traceability 缺 REQ-UC-005"

echo "== e2e: trace-matrix --require-req-uc 退出码 =="
T_OLD="$TMP/.trellis/tasks/old"; mkdir -p "$T_OLD"
cat > "$T_OLD/prd.md" <<'EOF'
# old
### BHV-001 老行为
Given/When/Then P0 失败 验收 未决
EOF
cat > "$T_OLD/design.md" <<'EOF'
# d
## §1
BHV-001 owner
## §2
### UNIT-old
承接 BHV-001 测试映射
EOF
echo "{}" > "$T_OLD/task.json"
# 旧 task 无 flag 默认不拦
( cd "$TMP" && python3 "$GATE" trace-matrix "$T_OLD" >/dev/null 2>&1 )
[ $? -eq 0 ] && note PASS "旧 task 默认 trace-matrix → 退出码 0" || note FAIL "旧 task 默认退出码错"
# CLI 显式 --require-req-uc 旧 task 缺 REQ-UC → 2
( cd "$TMP" && python3 "$GATE" trace-matrix "$T_OLD" --require-req-uc >/dev/null 2>&1 )
[ $? -eq 2 ] && note PASS "CLI --require-req-uc 旧 task 缺 REQ-UC → 退出码 2" || note FAIL "--require-req-uc 退出码错"
# task.json require_req_uc=true 缺 REQ-UC → 2（无 CLI flag）
echo '{"require_req_uc": true}' > "$T_OLD/task.json"
( cd "$TMP" && python3 "$GATE" trace-matrix "$T_OLD" >/dev/null 2>&1 )
[ $? -eq 2 ] && note PASS "task.json require_req_uc 缺 REQ-UC → 退出码 2" || note FAIL "task.json flag 退出码错"

echo ""
echo "==== e2e: $PASS passed, $FAIL failed ===="
[ "$FAIL" -eq 0 ]
