#!/usr/bin/env bash
# guru_gate.py 夹具测试：合格通过(0)、缺章/断链被拦(2)、trace-matrix 矩阵与孤儿清单。
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
GATE="$HERE/../guru_gate.py"
TMP="$(mktemp -d)"
export GURU_GATE_ALLOW_ABS=1  # 夹具的 design_package 用绝对路径；生产环境默认拒绝绝对路径
trap 'rm -rf "$TMP"' EXIT
pass=0; failn=0

mk_good() {
  d="$TMP/good"; mkdir -p "$d"
  cat > "$d/prd.md" <<'EOF'
## 行为规格
### BHV-001 点击下单
Given 有库存 When 点击 Then 状态变更
### BHV-002 下单失败提示
Given 网络异常 When 点击 Then 提示重试
## 核心能力
- P0 下单
## 失败路径
网络失败→提示重试
## 验收场景
下单成功可见订单
## 未决问题
无（显式声明）
EOF
  cat > "$d/design.md" <<'EOF'
## §1 概要设计
归属表：BHV-001 → owner: UseCase。为什么属于它：业务规则；为什么不属于别人：controller 无规则；是否需独立存在：是。
归属表：BHV-002 → owner: Controller（error 态展示）。三问理由同上格式。
承接索引：chapter_target=下单 → doc_type=usecase
## §2 详细设计
### UNIT-order-usecase
承接的行为：BHV-001、BHV-002。失败收口：上抛枚举。测试映射：unit test 成功+失败各1。不得补造：不决定缓存策略。
EOF
  cat > "$d/implement.md" <<'EOF'
## 计划（切片）
片1：UNIT-order-usecase 接口与实现
## 执行（改动文件）
- lib/new/domain/...
## 证据
flutter analyze 通过；dart test 通过
## 阻塞与偏差
无
EOF
  echo "$d"
}

expect() { # expect <desc> <want_rc> <cmd...>
  desc="$1"; want="$2"; shift 2
  out=$("$@" 2>&1); rc=$?
  if [ "$rc" = "$want" ]; then pass=$((pass+1)); echo "PASS  $desc"
  else failn=$((failn+1)); echo "FAIL  $desc (want=$want got=$rc)"; echo "$out" | head -4; fi
}
expect_grep() { # expect_grep <desc> <pattern> <cmd...>
  desc="$1"; pat="$2"; shift 2
  out=$("$@" 2>&1)
  if printf '%s' "$out" | grep -q "$pat"; then pass=$((pass+1)); echo "PASS  $desc"
  else failn=$((failn+1)); echo "FAIL  $desc (未匹配: $pat)"; echo "$out" | head -4; fi
}

G=$(mk_good)
expect "requirements 合格通过" 0 python3 "$GATE" requirements "$G"
expect "overview 合格通过"     0 python3 "$GATE" overview "$G"
expect "detail 合格通过"       0 python3 "$GATE" detail "$G"
expect "implement 合格通过"    0 python3 "$GATE" implement "$G"
expect "trace-matrix 闭合通过(strict)" 0 python3 "$GATE" trace-matrix "$G" --strict
expect_grep "trace-matrix 含矩阵行" "BHV-001" python3 "$GATE" trace-matrix "$G"

# 缺章样本
B="$TMP/bad-req"; mkdir -p "$B"; grep -v "失败路径\|网络失败" "$G/prd.md" > "$B/prd.md"
expect "requirements 缺失败路径被拦" 2 python3 "$GATE" requirements "$B"
B0="$TMP/bad-nobhv"; mkdir -p "$B0"; sed 's/### BHV-[0-9]*//' "$G/prd.md" > "$B0/prd.md"
expect "requirements 无 BHV 编号被拦" 2 python3 "$GATE" requirements "$B0"
B2="$TMP/bad-ov"; mkdir -p "$B2"; cp "$G/prd.md" "$B2/"; sed 's/承接索引.*//' "$G/design.md" > "$B2/design.md"
expect "overview 缺承接索引被拦" 2 python3 "$GATE" overview "$B2"

# 断链样本1：UNIT 引用幽灵 BHV
B3="$TMP/bad-ghost"; mkdir -p "$B3"; cp "$G/prd.md" "$B3/"; cp "$G/implement.md" "$B3/"
sed 's/BHV-002、*//; s/承接的行为：BHV-001/承接的行为：BHV-001、BHV-099/' "$G/design.md" > "$B3/design.md"
expect "detail 幽灵 BHV 引用被拦" 2 python3 "$GATE" detail "$B3"
expect_grep "detail 幽灵报错指名 BHV-099" "BHV-099" python3 "$GATE" detail "$B3"

# 断链样本2：行为无单元承接
B4="$TMP/bad-orphan"; mkdir -p "$B4"; cp "$G/prd.md" "$B4/"; cp "$G/implement.md" "$B4/"
sed 's/、BHV-002//' "$G/design.md" > "$B4/design.md"
expect "detail 行为无承接被拦" 2 python3 "$GATE" detail "$B4"
expect "trace-matrix strict 断链被拦" 2 python3 "$GATE" trace-matrix "$B4" --strict

# 断链样本3：切片引用幽灵 UNIT
B5="$TMP/bad-slice"; mkdir -p "$B5"; cp "$G/prd.md" "$G/design.md" "$B5/"
sed 's/UNIT-order-usecase/UNIT-ghost-unit/' "$G/implement.md" > "$B5/implement.md"
expect "implement 幽灵 UNIT 切片被拦" 2 python3 "$GATE" implement "$B5"

# --write
python3 "$GATE" trace-matrix "$G" --write >/dev/null
[ -f "$G/trace-matrix.md" ] && { pass=$((pass+1)); echo "PASS  trace-matrix --write 落盘"; } || { failn=$((failn+1)); echo "FAIL  --write"; }

# ============ 双轨制：full 链目录级设计包 ============
mk_pkg() { # mk_pkg <name> → 输出 task_dir；设计包在 <task_dir>-docs
  d="$TMP/$1"; pkg="$TMP/$1-docs"; mkdir -p "$d" "$pkg/chapters"
  cp "$G/prd.md" "$G/implement.md" "$d/"
  printf '{"guru_chain": "full", "design_package": "%s"}\n' "$pkg" > "$d/task.json"
  echo "# 设计包导航" > "$pkg/README.md"
  cat > "$pkg/design-main.md" <<'EOF'
# 概要主定义
## 设计约束与输入
承接 P0 下单。
## 行为集合
BHV-001、BHV-002
## 归属判定表
BHV-001 → owner: UseCase。为什么属于它：业务规则；为什么不属于别人：controller 无规则；是否需独立存在：是。
BHV-002 → owner: Controller。三问理由同上格式。
## 技术决策承接
无新增三方依赖。
## 架构总览
```mermaid
graph TD
    OP[OrderPage] --> OC[OrderController]
    OC --> OU[OrderUseCase]
```
时序图策略：UC-01 豁免 理由：链路单一（最小行为链 BHV-001→BHV-002）。
## 详细设计承接索引
- chapter_target=order → doc_type=usecase → chapters/order-usecase.md
## 未决问题
无
## 架构就绪自检
G1~G8 逐项通过（行为覆盖/归属/合规/索引/未决/图表/时序/技术决策）。
EOF
  cat > "$pkg/chapters/order-usecase.md" <<'EOF'
### UNIT-order-usecase
承接的行为：BHV-001、BHV-002。失败收口：上抛枚举。测试映射：unit test 成功+失败各1。不得补造：不决定缓存策略。
EOF
  echo "$d"
}

PK=$(mk_pkg pkg-good)
expect "full 概要：设计包合格通过" 0 python3 "$GATE" overview "$PK"
expect "full 详细：章节闭合通过"   0 python3 "$GATE" detail "$PK"
expect "full auto 渐进通过"        0 python3 "$GATE" auto "$PK"

PK2=$(mk_pkg pkg-nochain); printf '{"guru_chain": "full"}\n' > "$PK2/task.json"
expect "full 链缺 design_package 被拦" 2 python3 "$GATE" overview "$PK2"
expect "full 链缺包时 auto 渐进放行" 0 python3 "$GATE" auto "$PK2"
expect_grep "auto 显式提示包未声明" "尚未声明 design_package" python3 "$GATE" auto "$PK2"

# 穿越用例必须在生产模式（ALLOW_ABS=0）下断言：测试逃生口会在穿越检查之前直接返回路径
PK2A=$(mk_pkg pkg-traversal); printf '{"guru_chain": "full", "design_package": "../outside-docs"}\n' > "$PK2A/task.json"
expect "full 链 design_package .. 穿越被拦" 2 env GURU_GATE_ALLOW_ABS=0 python3 "$GATE" overview "$PK2A"
out=$(GURU_GATE_ALLOW_ABS=0 python3 "$GATE" overview "$TMP/pkg-good" 2>&1); rc=$?
if [ "$rc" = 2 ]; then pass=$((pass+1)); echo "PASS  生产模式拒绝绝对路径 design_package"
else failn=$((failn+1)); echo "FAIL  绝对路径应被拒 (got=$rc)"; fi

# 生产模式 realpath 围栏：相对路径词法合法，但符号链接目标在仓库外 → 拒绝
mkdir -p "$TMP/outside-docs"; cp -R "$TMP/pkg-good-docs"/. "$TMP/outside-docs/"
SYR="$TMP/symlink-repo"; mkdir -p "$SYR"
ln -s "$TMP/outside-docs" "$SYR/link-docs"
PK2S="$SYR/pkg-symlink"; mkdir -p "$PK2S"; cp "$G/prd.md" "$G/implement.md" "$PK2S/"
printf '{"guru_chain": "full", "design_package": "link-docs"}\n' > "$PK2S/task.json"
out=$(cd "$SYR" && GURU_GATE_ALLOW_ABS=0 python3 "$GATE" overview "$PK2S" 2>&1); rc=$?
if [ "$rc" = 2 ]; then pass=$((pass+1)); echo "PASS  design_package 符号链接逃逸被拦"
else failn=$((failn+1)); echo "FAIL  符号链接逃逸应被拒 (got=$rc)"; echo "$out" | head -3; fi

PK2B=$(mk_pkg pkg-brokenpkg); python3 -c "
import json; p='$PK2B/task.json'; d=json.load(open(p)); d['design_package']='$PK2B-nonexistent'; json.dump(d,open(p,'w'))"
expect "full 链包声明但目录不存在 auto 拦截" 2 python3 "$GATE" auto "$PK2B"

PK3=$(mk_pkg pkg-noready); sed -i '' '/架构就绪自检/d' "$PK3-docs/design-main.md" 2>/dev/null || sed -i '/架构就绪自检/d' "$PK3-docs/design-main.md"
expect "full 概要缺就绪自检被拦" 2 python3 "$GATE" overview "$PK3"

PK4=$(mk_pkg pkg-missingchap); rm "$PK4-docs/chapters/order-usecase.md"
expect "full 详细索引引用缺文件被拦" 2 python3 "$GATE" detail "$PK4"

PK5=$(mk_pkg pkg-orphan); echo "### UNIT-extra" > "$PK5-docs/chapters/extra.md"
expect "full 详细孤儿章节被拦" 2 python3 "$GATE" detail "$PK5"

PK7=$(mk_pkg pkg-nomermaid); sed -i '' '/mermaid/d' "$PK7-docs/design-main.md" 2>/dev/null || sed -i '/mermaid/d' "$PK7-docs/design-main.md"
expect "full 概要缺 mermaid 图被拦" 2 python3 "$GATE" overview "$PK7"

PK8=$(mk_pkg pkg-noseq); sed -i '' '/时序图策略/d' "$PK8-docs/design-main.md" 2>/dev/null || sed -i '/时序图策略/d' "$PK8-docs/design-main.md"
expect "full 概要缺时序策略被拦" 2 python3 "$GATE" overview "$PK8"
expect_grep "时序缺口报错指向 L1 §2.5" "时序图" python3 "$GATE" overview "$PK8"

PK6=$(mk_pkg pkg-pending)
printf -- "- chapter_target=page → doc_type=page-entry → chapters/page-entry.md\n" >> "$PK6-docs/design-main.md"
cat > "$PK6-docs/chapters/page-entry.md" <<'EOF'
### UNIT-page-entry
承接的行为：BHV-002。失败收口：上抛。测试映射：widget test。不得补造：无。
EOF
expect "full 详细 pending L2 无豁免被拦" 2 python3 "$GATE" detail "$PK6"
expect_grep "pending 报错指名 page-entry" "page-entry" python3 "$GATE" detail "$PK6"
printf "L2豁免：page-entry 理由：首发版页面结构简单，按 L1 八问展开\n" >> "$PK6-docs/design-main.md"
expect "full 详细 pending L2 显式豁免放行" 0 python3 "$GATE" detail "$PK6"

# 豁免理由里的普通英文词不得豁免其他类型（service 在理由中出现 ≠ 豁免 service）
PK6B=$(mk_pkg pkg-exempt-word)
printf -- "- chapter_target=svc → doc_type=service → chapters/svc-service.md\n" >> "$PK6B-docs/design-main.md"
cat > "$PK6B-docs/chapters/svc-service.md" <<'EOF'
### UNIT-svc-service
承接的行为：BHV-002。失败收口：上抛。测试映射：unit test。不得补造：无。
EOF
printf "L2豁免：page-entry 理由：this service layer is simple\n" >> "$PK6B-docs/design-main.md"
expect "豁免理由含 service 一词不豁免 service 类型" 2 python3 "$GATE" detail "$PK6B"

# pending L2：表格行形式（无 doc_type= 前缀）也必须被识别
PK9=$(mk_pkg pkg-tablerow)
printf -- "| page | page-entry | chapters/page-entry.md |\n" >> "$PK9-docs/design-main.md"
cat > "$PK9-docs/chapters/page-entry.md" <<'EOF'
### UNIT-page-entry
承接的行为：BHV-002。失败收口：上抛。测试映射：widget test。不得补造：无。
EOF
expect "full 详细表格形式 pending 被拦" 2 python3 "$GATE" detail "$PK9"

# 人工 Gate：confirm 无 TTY 被拒（agent 代跑场景）
echo '{}' > "$G/task.json"
expect "confirm 无 TTY 被拒" 2 python3 "$GATE" confirm requirements "$G"
expect_grep "confirm 拒绝信息指向用户终端" "交互式终端" python3 "$GATE" confirm requirements "$G"
expect "confirm 未知 gate 被拒" 2 python3 "$GATE" confirm nonsense "$G"

# 人工 Gate：check 缺确认拦截 / 全确认放行
expect "check 零确认被拦" 2 python3 "$GATE" check "$G"
expect_grep "check 报缺需求确认" "需求" python3 "$GATE" check "$G"
cat > "$G/task.json" <<'EOF'
{"guru_gates": {"requirements": {"confirmed_by": "tester", "confirmed_at": "2026-01-01T00:00:00+00:00"},
                "overview": {"confirmed_by": "tester", "confirmed_at": "2026-01-01T00:00:00+00:00"}}}
EOF
expect "check 缺 detail 确认被拦" 2 python3 "$GATE" check "$G"
# 缺 artifact_digest 的确认记录（手写伪造/旧版）不放行
cat > "$G/task.json" <<'EOF'
{"guru_gates": {"requirements": {"confirmed_by": "tester", "confirmed_at": "2026-01-01T00:00:00+00:00"},
                "overview": {"confirmed_by": "tester", "confirmed_at": "2026-01-01T00:00:00+00:00"},
                "detail": {"confirmed_by": "tester", "confirmed_at": "2026-01-01T00:00:00+00:00"}}}
EOF
expect "check 缺确认快照被拦" 2 python3 "$GATE" check "$G"
expect_grep "缺快照报错指明 confirm 来源" "缺确认快照" python3 "$GATE" check "$G"

DG_REQ=$(python3 "$GATE" digest requirements "$G")
DG_OV=$(python3 "$GATE" digest overview "$G")
DG_DT=$(python3 "$GATE" digest detail "$G")
cat > "$G/task.json" <<EOF
{"guru_gates": {"requirements": {"confirmed_by": "tester", "confirmed_at": "x", "artifact_digest": "$DG_REQ"},
                "overview": {"confirmed_by": "tester", "confirmed_at": "x", "artifact_digest": "$DG_OV"},
                "detail": {"confirmed_by": "tester", "confirmed_at": "x", "artifact_digest": "$DG_DT"}}}
EOF
expect "check 三确认放行" 0 python3 "$GATE" check "$G"
expect "status 可运行" 0 python3 "$GATE" status "$G"
expect_grep "status 显示确认人" "tester" python3 "$GATE" status "$G"

# TASK_JSON_PATH env 解析（before_start 钩子路径）
out=$(TASK_JSON_PATH="$G/task.json" python3 "$GATE" check 2>&1); rc=$?
if [ "$rc" = 0 ] && printf '%s' "$out" | grep -q "放行"; then pass=$((pass+1)); echo "PASS  check 经 TASK_JSON_PATH 解析任务"
else failn=$((failn+1)); echo "FAIL  check TASK_JSON_PATH (rc=$rc)"; echo "$out" | head -3; fi

# check 复跑结构 Gate：确认落盘后产物被改坏 → 拦截（确认时效）
GS="$TMP/stale"; mkdir -p "$GS"; cp "$G"/*.md "$GS/" 2>/dev/null; cp "$G/task.json" "$GS/"
grep -v "失败路径\|网络失败" "$G/prd.md" > "$GS/prd.md"
expect "check 确认后产物破坏被拦" 2 python3 "$GATE" check "$GS"
expect_grep "check 报结构 Gate 未通过" "结构 Gate" python3 "$GATE" check "$GS"

# 确认快照：digest 一致放行；结构仍合格但内容被改 → 快照失配拦截
GD="$TMP/digest"; mkdir -p "$GD"; cp "$G/prd.md" "$G/design.md" "$G/implement.md" "$GD/"
D_REQ=$(python3 "$GATE" digest requirements "$GD")
D_OV=$(python3 "$GATE" digest overview "$GD")
D_DT=$(python3 "$GATE" digest detail "$GD")
cat > "$GD/task.json" <<EOF
{"guru_gates": {
  "requirements": {"confirmed_by": "t", "confirmed_at": "x", "artifact_digest": "$D_REQ"},
  "overview":     {"confirmed_by": "t", "confirmed_at": "x", "artifact_digest": "$D_OV"},
  "detail":       {"confirmed_by": "t", "confirmed_at": "x", "artifact_digest": "$D_DT"}}}
EOF
expect "check 快照一致放行" 0 python3 "$GATE" check "$GD"
printf '\n语义改动：阈值从 8s 调成 30s\n' >> "$GD/design.md"
expect "check 快照失配被拦" 2 python3 "$GATE" check "$GD"
expect_grep "快照失配指明重新确认" "重新人工确认" python3 "$GATE" check "$GD"

# confirm 写保护：经 pty 真正走到写路径（TTY 通过、回答 yes），非法 JSON 必须被解析守卫拒绝且不重写
GJ="$TMP/badjson"; mkdir -p "$GJ"; cp "$G/prd.md" "$GJ/"; printf '[broken' > "$GJ/task.json"
out=$(python3 - "$GATE" "$GJ" <<'PY'
import os, pty, select, sys, time
gate, gj = sys.argv[1], sys.argv[2]
pid, fd = pty.fork()
if pid == 0:
    os.execvp("python3", ["python3", gate, "confirm", "requirements", gj])
buf, sent = b"", False
deadline = time.time() + 30  # 防 pty 挂死：超时以 124 退出
while True:
    if time.time() > deadline:
        sys.stdout.write(buf.decode(errors="replace"))
        sys.exit(124)
    r, _, _ = select.select([fd], [], [], 0.2)
    if not r:
        continue
    try:
        d = os.read(fd, 1024)
    except OSError:
        break
    if not d:
        break
    buf += d
    if not sent and "确认请输入".encode() in buf:
        os.write(fd, b"yes\n"); sent = True
_, st = os.waitpid(pid, 0)
sys.stdout.write(buf.decode(errors="replace"))
sys.exit(os.waitstatus_to_exitcode(st))
PY
); rc=$?
if [ "$rc" = 2 ] && [ "$(cat "$GJ/task.json")" = "[broken" ] && printf '%s' "$out" | grep -q "格式非法"; then
  pass=$((pass+1)); echo "PASS  confirm 写路径拒绝非法 task.json（pty 实测）"
else
  failn=$((failn+1)); echo "FAIL  confirm 写路径守卫 (rc=$rc)"; printf '%s\n' "$out" | tail -3
fi

# full 链确认快照：README 属包骨架，改动同样触发失配
GF=$(mk_pkg pkg-digest-full)
F_REQ=$(python3 "$GATE" digest requirements "$GF")
F_OV=$(python3 "$GATE" digest overview "$GF")
F_DT=$(python3 "$GATE" digest detail "$GF")
python3 - "$GF" "$F_REQ" "$F_OV" "$F_DT" <<'PY'
import json, sys
gf, req, ov, dt = sys.argv[1:5]
p = f"{gf}/task.json"
d = json.load(open(p))
d["guru_gates"] = {
    "requirements": {"confirmed_by": "t", "confirmed_at": "x", "artifact_digest": req},
    "overview": {"confirmed_by": "t", "confirmed_at": "x", "artifact_digest": ov},
    "detail": {"confirmed_by": "t", "confirmed_at": "x", "artifact_digest": dt},
}
json.dump(d, open(p, "w"), ensure_ascii=False, indent=2)
PY
expect "full check 快照一致放行" 0 python3 "$GATE" check "$GF"
printf '\n导航入口调整\n' >> "$GF-docs/README.md"
expect "full check README 快照失配被拦" 2 python3 "$GATE" check "$GF"
expect_grep "README 快照失配指明重新确认" "重新人工确认" python3 "$GATE" check "$GF"
expect_grep "status 与 check 同口径呈现失配" "快照失配" python3 "$GATE" status "$GF"

# 累积快照：上游 prd 改动 + 只重确认 requirements → 下游 overview/detail 失配
GF2=$(mk_pkg pkg-cumulative)
python3 - "$GF2" "$GATE" <<'PY'
import json, subprocess, sys
gf, gate = sys.argv[1], sys.argv[2]
def dig(g): return subprocess.run(["python3", gate, "digest", g, gf], capture_output=True, text=True).stdout.strip()
d = json.load(open(f"{gf}/task.json"))
d["guru_gates"] = {g: {"confirmed_by": "t", "confirmed_at": "x", "artifact_digest": dig(g)}
                   for g in ("requirements", "overview", "detail")}
json.dump(d, open(f"{gf}/task.json", "w"), ensure_ascii=False, indent=2)
PY
expect "累积快照：基线放行" 0 python3 "$GATE" check "$GF2"
# 结构中性的上游改动（不新增 BHV，避免结构 Gate 先拦导致测不到快照路径）
printf '\n需求补充说明：下单成功后展示订单编号。\n' >> "$GF2/prd.md"
python3 - "$GF2" "$GATE" <<'PY'
import json, subprocess, sys
gf, gate = sys.argv[1], sys.argv[2]
dig = subprocess.run(["python3", gate, "digest", "requirements", gf], capture_output=True, text=True).stdout.strip()
d = json.load(open(f"{gf}/task.json"))
d["guru_gates"]["requirements"]["artifact_digest"] = dig
json.dump(d, open(f"{gf}/task.json", "w"), ensure_ascii=False, indent=2)
PY
expect "累积快照：上游改动后下游确认失配被拦" 2 python3 "$GATE" check "$GF2"
expect_grep "累积快照：拦截原因是下游快照失配" "确认快照失配" python3 "$GATE" check "$GF2"

# PreToolUse hook：shlex token 识别（引号字面量不触发；真实 start 命令触发并拦截）
HOOK="$HERE/../../hooks/platform/block-unconfirmed-start.sh"
out=$(printf '%s' '{"tool_input":{"command":"echo '\''task.py start docs'\''"}}' | bash "$HOOK" 2>&1); rc=$?
if [ "$rc" = 0 ]; then pass=$((pass+1)); echo "PASS  hook 引号字面量不触发"
else failn=$((failn+1)); echo "FAIL  hook 引号字面量误拦 (rc=$rc)"; fi
# 正例需要真实项目骨架：否则会因找不到 gate 脚本而"碰巧"退出 2（错误原因的通过）
HP="$TMP/hook-project"; mkdir -p "$HP/.trellis/scripts/guru"
ln -sf "$GATE" "$HP/.trellis/scripts/guru/guru_gate.py"
out=$(printf '{"tool_input":{"command":"python3 .trellis/scripts/task.py start %s"}}' "$GD" | CLAUDE_PROJECT_DIR="$HP" bash "$HOOK" 2>&1); rc=$?
if [ "$rc" = 2 ] && printf '%s' "$out" | grep -q "确认快照失配"; then pass=$((pass+1)); echo "PASS  hook 真实 start 命令被拦（拦截原因=快照失配）"
else failn=$((failn+1)); echo "FAIL  hook 应以快照失配拦截 (rc=$rc)"; echo "$out" | head -3; fi
out=$(printf '{"tool_input":{"file_path":"a.md","content":"task.py start"}}' | bash "$HOOK" 2>&1); rc=$?
if [ "$rc" = 0 ]; then pass=$((pass+1)); echo "PASS  hook 非命令字段不触发"
else failn=$((failn+1)); echo "FAIL  hook 非命令字段误拦 (rc=$rc)"; fi
out=$(printf '{"tool_input":{"command":"echo python3 .trellis/scripts/task.py start x"}}' | bash "$HOOK" 2>&1); rc=$?
if [ "$rc" = 0 ]; then pass=$((pass+1)); echo "PASS  hook 参数位（echo 未引号）不触发"
else failn=$((failn+1)); echo "FAIL  hook 参数位误拦 (rc=$rc)"; fi
# 标点粘连：`start; echo ok` 仍须识别（punctuation_chars 切分）
out=$(printf '{"tool_input":{"command":"python3 .trellis/scripts/task.py start %s; echo ok"}}' "$GD" | CLAUDE_PROJECT_DIR="$HP" bash "$HOOK" 2>&1); rc=$?
if [ "$rc" = 2 ]; then pass=$((pass+1)); echo "PASS  hook 分号粘连命令仍被识别拦截"
else failn=$((failn+1)); echo "FAIL  hook 分号粘连漏判 (rc=$rc)"; echo "$out" | head -2; fi
# 多行命令：第二行的 start 仍在命令位，须被识别
out=$(printf '{"tool_input":{"command":"echo prep\\npython3 .trellis/scripts/task.py start %s"}}' "$GD" | CLAUDE_PROJECT_DIR="$HP" bash "$HOOK" 2>&1); rc=$?
if [ "$rc" = 2 ]; then pass=$((pass+1)); echo "PASS  hook 多行命令第二行被识别拦截"
else failn=$((failn+1)); echo "FAIL  hook 多行命令漏判 (rc=$rc)"; echo "$out" | head -2; fi
# env 前缀：VAR=1 python3 task.py start 仍是命令位
out=$(printf '{"tool_input":{"command":"TRELLIS_X=1 python3 .trellis/scripts/task.py start %s"}}' "$GD" | CLAUDE_PROJECT_DIR="$HP" bash "$HOOK" 2>&1); rc=$?
if [ "$rc" = 2 ]; then pass=$((pass+1)); echo "PASS  hook env 前缀命令被识别拦截"
else failn=$((failn+1)); echo "FAIL  hook env 前缀漏判 (rc=$rc)"; echo "$out" | head -2; fi

# 非对象根 task.json：读路径不崩溃（status 正常报未确认）
GN="$TMP/nondict"; mkdir -p "$GN"; printf '[1, 2]' > "$GN/task.json"
expect "status 非对象 task.json 不崩溃" 0 python3 "$GATE" status "$GN"

# planning fallback：扫描遇到非对象根不崩溃，仍能定位唯一 planning 任务
FB="$TMP/fbroot"; mkdir -p "$FB/.trellis/tasks/aa" "$FB/.trellis/tasks/bb"
printf '[1]' > "$FB/.trellis/tasks/aa/task.json"
printf '{"status": "planning"}' > "$FB/.trellis/tasks/bb/task.json"
out=$(cd "$FB" && python3 "$GATE" status 2>&1); rc=$?
if [ "$rc" = 0 ] && printf '%s' "$out" | grep -q "bb"; then pass=$((pass+1)); echo "PASS  fallback 跳过非对象根并定位 planning 任务"
else failn=$((failn+1)); echo "FAIL  fallback 崩溃或未定位 (rc=$rc)"; echo "$out" | head -3; fi

# basename 精确匹配：mytask.py start 不触发
out=$(printf '{"tool_input":{"command":"python3 mytask.py start x"}}' | bash "$HOOK" 2>&1); rc=$?
if [ "$rc" = 0 ]; then pass=$((pass+1)); echo "PASS  hook 不误伤 mytask.py"
else failn=$((failn+1)); echo "FAIL  hook 误伤 mytask.py (rc=$rc)"; fi

echo "----"; echo "结果: $pass 通过 / $failn 失败"
[ "$failn" = 0 ]
