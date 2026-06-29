#!/usr/bin/env bash
# guru_gate.py 夹具测试：合格通过(0)、缺章/断链被拦(2)、trace-matrix 矩阵与孤儿清单。
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
GATE="$HERE/../guru_gate.py"
TMP="$(mktemp -d)"
export GURU_GATE_ALLOW_ABS=1  # 夹具的 design_package 用绝对路径；生产环境默认拒绝绝对路径
export GURU_GATE_ALLOW_ENV_SOFT=1  # 允许夹具用 env 开 soft；生产降级只能改 config（留 git 痕迹）
export PYTHONDONTWRITEBYTECODE=1  # 测试不得在可打包 overlay 中留下 __pycache__
trap 'rm -rf "$TMP"' EXIT
pass=0; failn=0

append_detail_chapter() { # append_detail_chapter <file> [unit] [type_heading] [test_hint]
  file="$1"
  unit="${2:-UNIT-order-usecase}"
  type_heading="${3:-Widget 设计}"
  test_hint="${4:-unit test}"
  cat >> "$file" <<EOF
### ${unit}
## 1. 单元职责
${unit}：承接的行为：BHV-001、BHV-002；owner 为 UseCase；不拥有 UI 状态。
## 2. 行为定义
### 2.1 行为清单
- 下单成功：承接的行为：BHV-001。
- 下单失败提示：承接的行为：BHV-002。
### 2.2 接口定义
- execute(input: OrderInput) -> OrderResult（签名级）。
## 3. 核心数据结构
### 3.1 数据模型
- OrderInput / OrderResult：签名级结构。
### 3.2 错误类型表
- NetworkError：失败收口：上抛枚举并保留重试。
## 4. 逐行为设计
### 4.1 下单成功
1. 校验输入。
2. 调用 repository 创建订单。
3. 失败如何收口：上抛错误并保留重试入口。
## 5. 状态管理
N/A：本单元无持久状态；理由：状态 owner 在概要归属表。
## 6. ${type_heading}
N/A：本单元不拥有平台 UI/数据合同；理由：按 L1 八问展开。
## 7. 测试映射
- BHV-001：${test_hint} 成功路径 1 条。
- BHV-002：${test_hint} 失败路径 1 条。
## 8. 不得补造清单
- 不得补造：不决定缓存策略。
- 不在此补造接口事实。
EOF
}

write_detail_chapter() { # write_detail_chapter <file> [unit] [type_heading] [test_hint]
  : > "$1"
  append_detail_chapter "$@"
}

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
## Brainstorm Evidence
- Skill loaded: trellis-brainstorm loaded for fixture setup
- Repository evidence inspected: fixture PRD/design/implement inspected
- Domain/terminology triggers: none — no new terms or code/user-intent conflict in fixture
- Current code vs user intent conflicts: none — fixture uses generated local artifacts only
- Product decisions confirmed:
  - DEC-001: fixture behavior and acceptance criteria confirmed
    - user_quote: "fixture confirms DEC-001"
    - confirmed_ref: fixture-session DEC-001
- Open product/scope/risk questions: none — fixture explicitly declares no unresolved questions
EOF
  cat > "$d/design.md" <<'EOF'
## §1 概要设计
归属表：BHV-001 → owner: UseCase。为什么属于它：业务规则；为什么不属于别人：controller 无规则；是否需独立存在：是。
归属表：BHV-002 → owner: Controller（error 态展示）。三问理由同上格式。
承接索引：chapter_target=下单 → doc_type=usecase
## §2 详细设计
EOF
  append_detail_chapter "$d/design.md"
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

make_gate_case() { # make_gate_case <name>
  d="$TMP/$1"; mkdir -p "$d"
  cp "$G/prd.md" "$G/design.md" "$G/implement.md" "$d/"
  echo '{}' > "$d/task.json"
  echo "$d"
}

mark_low_risk() { # mark_low_risk <task_dir>
  python3 - "$1/task.json" <<'PY'
import json, sys
p = sys.argv[1]
try:
    d = json.load(open(p, encoding="utf-8"))
except Exception:
    d = {}
d["guru_chain"] = "light"
d["risk_level"] = "low"
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
PY
}

mark_high_risk() { # mark_high_risk <task_dir>
  python3 - "$1/task.json" <<'PY'
import json, sys
p = sys.argv[1]
try:
    d = json.load(open(p, encoding="utf-8"))
except Exception:
    d = {}
d["guru_chain"] = "light"
d["risk_level"] = "high"
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
PY
}

grill_done() { # grill_done <gate> <task_dir>
  env GURU_GATE_MODE=soft python3 "$GATE" grill-done "$1" "$2" --via-agent --user-quote "已完成 $1 grill" >/dev/null
}

grill_skip() { # grill_skip <gate> <task_dir>
  env GURU_GATE_MODE=soft python3 "$GATE" grill-skip "$1" "$2" --via-agent --user-quote "用户选择跳过 $1 grill" >/dev/null
}

write_grills_all_done() { # write_grills_all_done <task_dir>
  grill_done requirements "$1"
  grill_done overview "$1"
  grill_done detail "$1"
}

write_grills_low_risk_skip() { # write_grills_low_risk_skip <task_dir>
  mark_low_risk "$1"
  grill_done requirements "$1"
  grill_skip overview "$1"
  grill_skip detail "$1"
}

write_confirms_all() { # write_confirms_all <task_dir>
  python3 - "$GATE" "$1" <<'PY'
import json, subprocess, sys
gate, task_dir = sys.argv[1], sys.argv[2]
def digest(g):
    return subprocess.run(["python3", gate, "digest", g, task_dir], capture_output=True, text=True, check=True).stdout.strip()
p = f"{task_dir}/task.json"
try:
    data = json.load(open(p, encoding="utf-8"))
except Exception:
    data = {}
gates = data.setdefault("guru_gates", {})
for g in ("requirements", "detail"):
    entry = gates.setdefault(g, {})
    entry["confirmed_by"] = "tester"
    entry["confirmed_at"] = "x"
    entry["artifact_digest"] = digest(g)
open(p, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
PY
}

write_req_confirm() { # write_req_confirm <task_dir>
  python3 - "$GATE" "$1" <<'PY'
import json, subprocess, sys
gate, task_dir = sys.argv[1], sys.argv[2]
dig = subprocess.run(["python3", gate, "digest", "requirements", task_dir], capture_output=True, text=True, check=True).stdout.strip()
p = f"{task_dir}/task.json"
try:
    data = json.load(open(p, encoding="utf-8"))
except Exception:
    data = {}
gates = data.setdefault("guru_gates", {})
gates["requirements"] = {"confirmed_by": "tester", "confirmed_at": "x", "artifact_digest": dig}
open(p, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
PY
}

write_requirements_review() { # write_requirements_review <task_dir> <status> [reason]
  python3 - "$GATE" "$1" "$2" "${3:-fixture}" <<'PY'
import json, sys, importlib.util
gate, task_dir, status, reason = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
spec = importlib.util.spec_from_file_location("gg", gate)
gg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gg)
p = f"{task_dir}/task.json"
try:
    data = json.load(open(p, encoding="utf-8"))
except Exception:
    data = {}
gates = data.setdefault("guru_gates", {})
gates["requirements_review"] = {
    "action": "requirements",
    "provider": "claude",
    "current_provider": "codex",
    "adversarial": True,
    "status": status,
    "artifact_digest": gg._gate_digest(task_dir, "requirements"),
    "run_id": "requirements-review-fixture",
    "channel": "guru-fixture",
    "worker": "requirements-claude-fixture",
    "reason": reason,
    "timestamp": "2026-06-20T00:00:00+00:00",
}
open(p, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
PY
}

write_clean_reviews() { # write_clean_reviews <gate> <task_dir>
  if [ "$1" = "detail" ]; then
    python3 "$GATE" record-review "$1" "$2" --result clean --max-severity none --reviewer clean-context --run-id "$1-clean-a" --evidence "$1 clean a" --deletion-audit "none" >/dev/null
    python3 "$GATE" record-review "$1" "$2" --result clean --max-severity low --reviewer clean-context-adversarial-codex --run-id "$1-clean-adversarial-codex" --evidence "$1 adversarial clean" --deletion-audit "none" >/dev/null
  else
    python3 "$GATE" record-review "$1" "$2" --result clean --max-severity none --reviewer clean-context --run-id "$1-clean-a" --evidence "$1 clean a" >/dev/null
    python3 "$GATE" record-review "$1" "$2" --result clean --max-severity low --reviewer clean-context-adversarial-codex --run-id "$1-clean-adversarial-codex" --evidence "$1 adversarial clean" >/dev/null
  fi
}

write_reviews_all() { # write_reviews_all <task_dir>
  write_clean_reviews overview "$1"
  write_clean_reviews detail "$1"
}

write_new_gate_ready() { # write_new_gate_ready <task_dir>
  write_confirms_all "$1"
  write_reviews_all "$1"
}

mutate_gate_artifact() { # mutate_gate_artifact <gate> <task_dir>
  case "$1" in
    requirements) printf '\n需求补充说明：结构中性变更。\n' >> "$2/prd.md" ;;
    overview)     printf '\n概要补充说明：结构中性变更。\n' >> "$2/design.md" ;;
    detail)       printf '\n实现补充说明：结构中性变更。\n' >> "$2/implement.md" ;;
  esac
}

setup_grills_for_gate_state() { # setup_grills_for_gate_state <target_gate> <state> <task_dir>
  for g in requirements overview detail; do
    if [ "$g" = "$1" ]; then
      case "$2" in
        missing) ;;
        done) grill_done "$g" "$3" ;;
        skip) grill_skip "$g" "$3" ;;
        mismatch) grill_done "$g" "$3"; mutate_gate_artifact "$g" "$3" ;;
      esac
    else
      grill_done "$g" "$3"
    fi
  done
}

judge_grill_case() { # judge_grill_case <desc> <gate> <state> <want_rc> <got_rc>
  desc="$1"; gate="$2"; state="$3"; want="$4"; got="$5"
  if [ "$got" != "$want" ]; then
    failn=$((failn+1)); echo "FAIL  $desc (want=$want got=$got)"; echo "$out" | head -4
  elif [ "$state" = "missing" ] && ! printf '%s' "$out" | grep -q "grill-done $gate"; then
    failn=$((failn+1)); echo "FAIL  $desc (缺 grill-done 提示)"; echo "$out" | head -4
  elif [ "$state" = "mismatch" ] && ! printf '%s' "$out" | grep -q "digest 失配"; then
    failn=$((failn+1)); echo "FAIL  $desc (缺 digest 失配提示)"; echo "$out" | head -4
  else
    pass=$((pass+1)); echo "PASS  $desc"
  fi
}

# grill-done / grill-skip 命令可用性：真实写入 guru_gates[gate].grill
GC=$(make_gate_case grillcmd)
out=$(env GURU_GATE_MODE=soft python3 "$GATE" grill-done requirements "$GC" --via-agent --user-quote "已拷问" 2>&1); rc=$?
if [ "$rc" = 0 ] && python3 - "$GC/task.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
g = d["guru_gates"]["requirements"]["grill"]
assert g["status"] == "done" and g["by"] and g["at"] and g["digest"] and g["policy"] == "required"
PY
then pass=$((pass+1)); echo "PASS  grill-done 命令写入 guru_gates[requirements].grill"
else failn=$((failn+1)); echo "FAIL  grill-done 命令写入 (rc=$rc)"; echo "$out" | head -4; fi
out=$(env GURU_GATE_MODE=soft python3 "$GATE" grill-skip requirements "$GC" --via-agent --user-quote "需求也跳过" 2>&1); rc=$?
if [ "$rc" = 2 ] && printf '%s' "$out" | grep -q "不允许跳过"; then
  pass=$((pass+1)); echo "PASS  requirements grill-skip 被拒"
else failn=$((failn+1)); echo "FAIL  requirements grill-skip 应被拒 (rc=$rc)"; echo "$out" | head -4; fi
mark_low_risk "$GC"
out=$(env GURU_GATE_MODE=soft python3 "$GATE" grill-skip overview "$GC" --via-agent --user-quote "本轮无需拷问" 2>&1); rc=$?
if [ "$rc" = 0 ] && python3 - "$GC/task.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
g = d["guru_gates"]["overview"]["grill"]
assert g["status"] == "skipped" and g["reason"] == "本轮无需拷问" and g["by"] and g["at"]
assert g["policy"] == "skippable" and g["guru_chain"] == "light" and g["risk_level"] == "low"
PY
then pass=$((pass+1)); echo "PASS  grill-skip 命令写入 guru_gates[overview].grill"
else failn=$((failn+1)); echo "FAIL  grill-skip 命令写入 (rc=$rc)"; echo "$out" | head -4; fi

UNK=$(make_gate_case grill-skip-unknown)
out=$(env GURU_GATE_MODE=soft python3 "$GATE" grill-skip overview "$UNK" --via-agent --user-quote "未分级跳过" 2>&1); rc=$?
if [ "$rc" = 2 ] && printf '%s' "$out" | grep -q "risk_level"; then
  pass=$((pass+1)); echo "PASS  未显式 low-risk 的 overview grill-skip 被拒"
else failn=$((failn+1)); echo "FAIL  未分级 overview grill-skip 应被拒 (rc=$rc)"; echo "$out" | head -4; fi

HIGH=$(make_gate_case grill-skip-high); mark_high_risk "$HIGH"
out=$(env GURU_GATE_MODE=soft python3 "$GATE" grill-skip detail "$HIGH" --via-agent --user-quote "高风险跳过" 2>&1); rc=$?
if [ "$rc" = 2 ] && printf '%s' "$out" | grep -q "risk_level=high"; then
  pass=$((pass+1)); echo "PASS  high-risk detail grill-skip 被拒"
else failn=$((failn+1)); echo "FAIL  high-risk detail grill-skip 应被拒 (rc=$rc)"; echo "$out" | head -4; fi

# status #1 回归保护：confirm 全绿但 review 缺失时，footer 不得提示"可 task.py start"
SS=$(make_gate_case statusfooter)
if python3 - "$SS" "$GATE" >/dev/null <<'PY'
import sys, json, os, importlib.util
ss, gp = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("gg", gp); gg = importlib.util.module_from_spec(spec); spec.loader.exec_module(gg)
tj = os.path.join(ss, "task.json"); d = json.load(open(tj)); gates = d.setdefault("guru_gates", {})
for g in ("requirements", "detail"):
    gates[g] = {"confirmed_by": "T", "confirmed_at": "2026", "artifact_digest": gg._gate_digest(ss, g)}
json.dump(d, open(tj, "w"))
PY
then
  out=$(python3 "$GATE" status "$SS" 2>&1)
  if printf '%s' "$out" | grep -q "可 task.py start"; then
    failn=$((failn+1)); echo "FAIL  status confirm全绿+review缺失误报可start"; printf '%s\n' "$out" | tail -2
  else pass=$((pass+1)); echo "PASS  status confirm全绿+review缺失不误报可start"; fi
else failn=$((failn+1)); echo "FAIL  status footer 测试 setup 失败（task.json 未就绪）"; fi
# status legacy grill 渲染：仅兼容展示，不提示必跑/跳过策略
SS2=$(make_gate_case statusrender); write_grills_all_done "$SS2"
out=$(python3 "$GATE" status "$SS2" 2>&1)
if printf '%s' "$out" | grep -q "legacy grill present:done/current (ignored by current Gate model)" \
  && ! printf '%s' "$out" | grep -q "grill ⬜ 必跑"; then
  pass=$((pass+1)); echo "PASS  status legacy grill 仅作兼容展示"
else failn=$((failn+1)); echo "FAIL  status legacy grill 展示误导"; printf '%s\n' "$out" | tail -4; fi
SS3=$(make_gate_case status-next-review)
env GURU_GATE_MODE=soft python3 "$GATE" confirm requirements "$SS3" --via-agent --user-quote "确认需求" >/dev/null
out=$(python3 "$GATE" status "$SS3" 2>&1)
if printf '%s' "$out" | grep -q "record-review overview"; then
  pass=$((pass+1)); echo "PASS  status 需求确认后提示 overview record-review"
else failn=$((failn+1)); echo "FAIL  status 未提示 overview record-review"; printf '%s\n' "$out" | tail -6; fi

RR_STATUS=$(make_gate_case requirements-review-status)
write_requirements_review "$RR_STATUS" clean "review_result=clean/requirements-ready"
expect_grep "status 显示 requirements adversarial clean/current" "需求对抗 Review — ✅ clean/current" python3 "$GATE" status "$RR_STATUS"
printf '\n需求补充：触发 requirements digest 变化。\n' >> "$RR_STATUS/prd.md"
expect_grep "status 显示 requirements adversarial stale" "需求对抗 Review — ⚠️ clean/stale" python3 "$GATE" status "$RR_STATUS"

RR_CONFIRM_MISSING=$(make_gate_case requirements-review-confirm-missing)
out=$(env GURU_GATE_MODE=soft python3 "$GATE" confirm requirements "$RR_CONFIRM_MISSING" --via-agent --user-quote "用户接受风险并确认需求" 2>&1); rc=$?
if [ "$rc" = 0 ] && printf '%s' "$out" | grep -q "缺少 clean/current 的对抗审查证据"; then
  pass=$((pass+1)); echo "PASS  confirm requirements 缺对抗审查时警告但不硬阻断"
else failn=$((failn+1)); echo "FAIL  confirm requirements 缺对抗审查警告/放行异常 (rc=$rc)"; echo "$out" | head -5; fi

RR_CONFIRM_DEFERRED=$(make_gate_case requirements-review-confirm-deferred)
write_requirements_review "$RR_CONFIRM_DEFERRED" deferred "provider launch failed"
out=$(env GURU_GATE_MODE=soft python3 "$GATE" confirm requirements "$RR_CONFIRM_DEFERRED" --via-agent --user-quote "用户接受 deferred 风险" 2>&1); rc=$?
if [ "$rc" = 0 ] && printf '%s' "$out" | grep -q "requirements adversarial review deferred"; then
  pass=$((pass+1)); echo "PASS  confirm requirements deferred 对抗审查时警告但不硬阻断"
else failn=$((failn+1)); echo "FAIL  confirm requirements deferred 警告/放行异常 (rc=$rc)"; echo "$out" | head -5; fi

LOSS=$(make_gate_case detail-skeleton-loss)
cat > "$LOSS/design.md" <<'EOF'
## §1 概要设计
归属表：BHV-001 → owner: UseCase。为什么属于它：业务规则；为什么不属于别人：controller 无规则；是否需独立存在：是。
归属表：BHV-002 → owner: Controller。三问理由同上格式。
承接索引：chapter_target=下单 → doc_type=usecase
## §2 详细设计
### UNIT-order-usecase
| endpoint | method | BHV | error | test | non-goal |
|---|---|---|---|---|---|
| /orders | POST | 承接的行为：BHV-001、BHV-002 | 失败收口：上抛枚举 | 测试映射：unit test 成功+失败各1 | 不得补造：不决定缓存策略 |
EOF
expect "detail skeleton loss：保留 UNIT/BHV/测试/红线但删除 L1 章节被拦" 2 python3 "$GATE" detail "$LOSS"
expect_grep "detail skeleton loss：报错指向缺 L1 章节" "缺 L1 章节" python3 "$GATE" detail "$LOSS"
expect "requirements 合格通过" 0 python3 "$GATE" requirements "$G"
expect "overview 合格通过"     0 python3 "$GATE" overview "$G"
expect "detail 合格通过"       0 python3 "$GATE" detail "$G"
expect "implement 合格通过"    0 python3 "$GATE" implement "$G"
expect "trace-matrix 闭合通过(strict)" 0 python3 "$GATE" trace-matrix "$G" --strict
expect_grep "trace-matrix 含矩阵行" "BHV-001" python3 "$GATE" trace-matrix "$G"
expect_grep "status 显示 Brainstorm Evidence present" "Brainstorm Evidence.*present" python3 "$GATE" status "$G"

# 缺章样本
B="$TMP/bad-req"; mkdir -p "$B"; grep -v "失败路径\|网络失败" "$G/prd.md" > "$B/prd.md"
expect "requirements 缺失败路径被拦" 2 python3 "$GATE" requirements "$B"
B0="$TMP/bad-nobhv"; mkdir -p "$B0"; sed 's/### BHV-[0-9]*//' "$G/prd.md" > "$B0/prd.md"
expect "requirements 无 BHV 编号被拦" 2 python3 "$GATE" requirements "$B0"
BMISS="$TMP/bad-brainstorm-missing"; mkdir -p "$BMISS"; awk 'BEGIN{drop=0} /^## Brainstorm Evidence/{drop=1} /^## Notes/{drop=0} !drop{print}' "$G/prd.md" > "$BMISS/prd.md"
expect "requirements 缺 Brainstorm Evidence 被拦" 2 python3 "$GATE" requirements "$BMISS"
expect_grep "requirements 缺 Brainstorm Evidence 给恢复步骤" "load trellis-brainstorm" python3 "$GATE" requirements "$BMISS"
expect_grep "status 显示 Brainstorm Evidence missing" "Brainstorm Evidence.*missing" python3 "$GATE" status "$BMISS"
BPEND="$TMP/bad-brainstorm-pending"; mkdir -p "$BPEND"; sed 's/Skill loaded:.*/Skill loaded: pending/' "$G/prd.md" > "$BPEND/prd.md"
expect "requirements pending Brainstorm Evidence 被拦" 2 python3 "$GATE" requirements "$BPEND"
BNOREASON="$TMP/bad-brainstorm-no-reason"; mkdir -p "$BNOREASON"; perl -pe 's#Domain/terminology triggers:.*#Domain/terminology triggers: none#' "$G/prd.md" > "$BNOREASON/prd.md"
expect "requirements 负证据无原因被拦" 2 python3 "$GATE" requirements "$BNOREASON"
BALIAS="$TMP/good-brainstorm-alias"; mkdir -p "$BALIAS"; perl -pe 's/Domain\/terminology triggers:/Domain Grill triggers:/' "$G/prd.md" > "$BALIAS/prd.md"
expect "requirements 接受 Domain Grill triggers 兼容别名" 0 python3 "$GATE" requirements "$BALIAS"

BNOQUOTE="$TMP/bad-brainstorm-decision-no-quote"; mkdir -p "$BNOQUOTE"; cp "$G/prd.md" "$BNOQUOTE/prd.md"
python3 - "$BNOQUOTE/prd.md" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
s = s.replace('    - user_quote: "fixture confirms DEC-001"\n', '')
s = s.replace('    - confirmed_ref: fixture-session DEC-001\n', '')
open(p, "w", encoding="utf-8").write(s)
PY
expect "requirements positive Product decisions 缺 user_quote/confirmed_ref 被拦" 2 python3 "$GATE" requirements "$BNOQUOTE"

BOQ="$TMP/bad-brainstorm-multiple-oq-no-next"; mkdir -p "$BOQ"; cp "$G/prd.md" "$BOQ/prd.md"
python3 - "$BOQ/prd.md" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
s = s.replace(
    "- Open product/scope/risk questions: none — fixture explicitly declares no unresolved questions\n",
    "- Open product/scope/risk questions:\n"
    "  - OQ-001: 是否调整 P0 范围\n"
    "    - risk: changes launch scope\n"
    "  - OQ-002: 是否调整验收口径\n"
    "    - risk: changes acceptance\n",
)
open(p, "w", encoding="utf-8").write(s)
PY
expect "requirements 多个 OQ 缺单一 next_action 被拦" 2 python3 "$GATE" requirements "$BOQ"

BOQOK="$TMP/good-brainstorm-multiple-oq-next"; mkdir -p "$BOQOK"; cp "$BOQ/prd.md" "$BOQOK/prd.md"
cat >> "$BOQOK/prd.md" <<'EOF'
  - next_question: OQ-001
  - next_action: ask user one question; OQ-002 remains open
EOF
expect "requirements 多个 OQ 有单一 next_action 放行" 0 python3 "$GATE" requirements "$BOQOK"

BUC="$TMP/bad-user-confirmed-no-evidence"; mkdir -p "$BUC"; cp "$G/prd.md" "$BUC/prd.md"
cat >> "$BUC/prd.md" <<'EOF'

## 核心能力确认
- DEC-002:
  - confirmation_status=user_confirmed
EOF
expect "requirements user_confirmed 缺确认引用被拦" 2 python3 "$GATE" requirements "$BUC"

BTABLE="$TMP/bad-user-confirmed-table-no-evidence"; mkdir -p "$BTABLE"; cp "$G/prd.md" "$BTABLE/prd.md"
cat >> "$BTABLE/prd.md" <<'EOF'

## 核心能力表格确认
| decision | confirmation_status |
| --- | --- |
| DEC-002 | user_confirmed |
EOF
expect "requirements 表格 user_confirmed 缺确认引用被拦" 2 python3 "$GATE" requirements "$BTABLE"

BEV="$TMP/bad-evidence-ready-upgrade"; mkdir -p "$BEV"; cp "$G/prd.md" "$BEV/prd.md"
cat >> "$BEV/prd.md" <<'EOF'

## 核心能力确认
- DEC-002:
  - confirmation_status=evidence_ready
  - user_quote: "historical quote"
- DEC-003:
  - confirmation_status=user_confirmed
  - user_quote: "historical quote"
EOF
expect "requirements evidence_ready 静默升级 user_confirmed 被拦" 2 python3 "$GATE" requirements "$BEV"

BEVTABLE="$TMP/bad-evidence-ready-table-upgrade"; mkdir -p "$BEVTABLE"; cp "$G/prd.md" "$BEVTABLE/prd.md"
cat >> "$BEVTABLE/prd.md" <<'EOF'

## 核心能力表格确认
| decision | confirmation_status | user_quote |
| --- | --- | --- |
| DEC-002 | evidence_ready | historical quote |
| DEC-003 | user_confirmed | historical quote |
EOF
expect "requirements 表格 evidence_ready 静默升级 user_confirmed 被拦" 2 python3 "$GATE" requirements "$BEVTABLE"

BEVTABLEOK="$TMP/good-evidence-ready-table-current-turn"; mkdir -p "$BEVTABLEOK"; cp "$BEVTABLE/prd.md" "$BEVTABLEOK/prd.md"
cat >> "$BEVTABLEOK/prd.md" <<'EOF'
- current-turn-confirmation: DEC-003 confirmed by current user answer
EOF
expect "requirements 表格 user_confirmed 有引用和 current-turn 放行" 0 python3 "$GATE" requirements "$BEVTABLEOK"

BEVOK="$TMP/good-evidence-ready-current-turn"; mkdir -p "$BEVOK"; cp "$BEV/prd.md" "$BEVOK/prd.md"
cat >> "$BEVOK/prd.md" <<'EOF'
- current-turn-confirmation: DEC-003 confirmed by current user answer
EOF
expect "requirements evidence_ready 有 current-turn-confirmation 放行" 0 python3 "$GATE" requirements "$BEVOK"

BMIX="$TMP/good-independent-evidence-ready-and-confirmed"; mkdir -p "$BMIX"; cp "$G/prd.md" "$BMIX/prd.md"
cat >> "$BMIX/prd.md" <<'EOF'

## 核心能力确认
- DEC-010:
  - confirmation_status=evidence_ready
  - user_quote: "repository evidence only"
- DEC-011:
  - confirmation_status=user_confirmed
  - user_quote: "current user confirmed another decision"
EOF
expect "requirements 独立 evidence_ready 与 user_confirmed 混合状态放行" 0 python3 "$GATE" requirements "$BMIX"

BST="$TMP/bad-stale-confirmation-continue"; mkdir -p "$BST"; cp "$G/prd.md" "$BST/prd.md"
cat >> "$BST/prd.md" <<'EOF'

## Continue planning state
- DEC-004:
  - confirmation_status=evidence_ready
  - user_quote: "old confirmed quote"
- DEC-005:
  - confirmation_status=user_confirmed_with_edits
  - user_quote: "old confirmed quote"
EOF
expect "requirements stale confirmation 不作 current-turn 放行" 2 python3 "$GATE" requirements "$BST"

BBATCH="$TMP/good-explicit-batch-confirmation"; mkdir -p "$BBATCH"; cp "$G/prd.md" "$BBATCH/prd.md"
cat >> "$BBATCH/prd.md" <<'EOF'

## 批量确认记录
- DEC-006:
  - confirmation_status=user_confirmed
  - user_quote: "批量确认 OQ-006/OQ-007 都按推荐处理"
  - covered_oq: OQ-006
- DEC-007:
  - confirmation_status=user_confirmed
  - user_quote: "批量确认 OQ-006/OQ-007 都按推荐处理"
  - covered_oq: OQ-007
EOF
expect "requirements 显式批量确认逐项覆盖放行" 0 python3 "$GATE" requirements "$BBATCH"

BVAGUE="$TMP/bad-vague-batch-confirmation"; mkdir -p "$BVAGUE"; cp "$G/prd.md" "$BVAGUE/prd.md"
cat >> "$BVAGUE/prd.md" <<'EOF'

## 批量确认记录
- DEC-008:
  - confirmation_status=user_confirmed
  - user_quote: "好，批量确认"
EOF
expect "requirements 模糊批量确认缺 covered id 被拦" 2 python3 "$GATE" requirements "$BVAGUE"

BNOLOG="$TMP/good-no-question-loop-log"; mkdir -p "$BNOLOG"; cp "$G/prd.md" "$BNOLOG/prd.md"
expect "requirements 缺 Question loop log 但有最小确认引用放行" 0 python3 "$GATE" requirements "$BNOLOG"
B2="$TMP/bad-ov"; mkdir -p "$B2"; cp "$G/prd.md" "$B2/"; sed 's/承接索引.*//' "$G/design.md" > "$B2/design.md"
expect "overview 缺承接索引被拦" 2 python3 "$GATE" overview "$B2"

# 断链样本1：UNIT 引用幽灵 BHV
B3="$TMP/bad-ghost"; mkdir -p "$B3"; cp "$G/prd.md" "$B3/"; cp "$G/implement.md" "$B3/"
sed 's/BHV-002、*//; s/承接的行为：BHV-001/承接的行为：BHV-001、BHV-099/' "$G/design.md" > "$B3/design.md"
expect "detail 幽灵 BHV 引用被拦" 2 python3 "$GATE" detail "$B3"
expect_grep "detail 幽灵报错指名 BHV-099" "BHV-099" python3 "$GATE" detail "$B3"

# 断链样本2：行为无单元承接
B4="$TMP/bad-orphan"; mkdir -p "$B4"; cp "$G/prd.md" "$B4/"; cp "$G/implement.md" "$B4/"
sed 's/BHV-002/BHV-001/g' "$G/design.md" > "$B4/design.md"
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
  write_detail_chapter "$pkg/chapters/order-usecase.md"
  echo "$d"
}

PK=$(mk_pkg pkg-good)
expect "full 概要：设计包合格通过" 0 python3 "$GATE" overview "$PK"
expect "full 详细：章节闭合通过"   0 python3 "$GATE" detail "$PK"
write_req_confirm "$PK"
write_reviews_all "$PK"
expect "full auto 渐进通过"        0 python3 "$GATE" auto "$PK"
out=$(env GURU_GATE_MODE=soft python3 "$GATE" grill-skip overview "$PK" --via-agent --user-quote "full 也跳过" 2>&1); rc=$?
if [ "$rc" = 2 ] && printf '%s' "$out" | grep -q "guru_chain=full"; then
  pass=$((pass+1)); echo "PASS  full 链 overview grill-skip 被拒"
else failn=$((failn+1)); echo "FAIL  full 链 overview grill-skip 应被拒 (rc=$rc)"; echo "$out" | head -4; fi

PK2=$(mk_pkg pkg-nochain); printf '{"guru_chain": "full"}\n' > "$PK2/task.json"
expect "full 链缺 design_package 被拦" 2 python3 "$GATE" overview "$PK2"
write_req_confirm "$PK2"
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
write_req_confirm "$PK2B"
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
write_detail_chapter "$PK6-docs/chapters/page-entry.md" UNIT-page-entry "Widget 设计" "widget test"
expect "full 详细 pending L2 无豁免被拦" 2 python3 "$GATE" detail "$PK6"
expect_grep "pending 报错指名 page-entry" "page-entry" python3 "$GATE" detail "$PK6"
printf "L2豁免：page-entry 理由：首发版页面结构简单，按 L1 八问展开\n" >> "$PK6-docs/design-main.md"
expect "full 详细 pending L2 显式豁免放行" 0 python3 "$GATE" detail "$PK6"

# ============ review_runs 新 Gate：overview/detail 双 clean + detail confirm ============
RV=$(make_gate_case review-model)
write_req_confirm "$RV"
expect "confirm overview 被拒（新模型不支持）" 2 env GURU_GATE_MODE=soft python3 "$GATE" confirm overview "$RV" --via-agent --user-quote "确认概要"
expect "auto 缺 overview review 被拦" 2 python3 "$GATE" auto "$RV"
expect_grep "auto 缺 overview review 提示 record-review" "record-review overview" python3 "$GATE" auto "$RV"
write_clean_reviews overview "$RV"
expect "auto 缺 detail review 被拦" 2 python3 "$GATE" auto "$RV"
write_clean_reviews detail "$RV"
expect "auto 双 clean 后渐进放行（不要求 detail confirm）" 0 python3 "$GATE" auto "$RV"
expect "check 双 clean 但缺 detail confirm 被拦" 2 python3 "$GATE" check "$RV"
env GURU_GATE_MODE=soft python3 "$GATE" confirm detail "$RV" --via-agent --user-quote "确认详细" >/dev/null
expect "check 双 clean + detail confirm 放行" 0 python3 "$GATE" check "$RV"

RV2=$(make_gate_case review-record)
out=$(python3 "$GATE" record-review overview "$RV2" --result clean --max-severity low --reviewer clean-context --run-id same --evidence "clean" 2>&1); rc=$?
if [ "$rc" = 0 ] && grep -q '"review_runs"' "$RV2/task.json"; then pass=$((pass+1)); echo "PASS  record-review clean 写入 review_runs"
else failn=$((failn+1)); echo "FAIL  record-review clean 写入 (rc=$rc)"; echo "$out" | head -4; fi
expect "record-review 重复 run-id 被拒" 2 python3 "$GATE" record-review overview "$RV2" --result clean --max-severity low --reviewer clean-context --run-id same --evidence "dup"
expect "record-review reviewer 非 clean-context 被拒" 2 python3 "$GATE" record-review overview "$RV2" --result clean --max-severity low --reviewer casual-reviewer --run-id casual-review --evidence "bad"
expect "record-review requirements 被拒（需求不写 review_runs）" 2 python3 "$GATE" record-review requirements "$RV2" --result clean --max-severity none --reviewer clean-context --run-id req-clean --evidence "bad"
expect "record-review clean 带 finding_class 被拒" 2 python3 "$GATE" record-review overview "$RV2" --result clean --max-severity low --finding-class OVERVIEW_DEFECT --reviewer clean-context --run-id clean-class --evidence "bad"
expect "record-review findings 缺 finding_class 被拒" 2 python3 "$GATE" record-review overview "$RV2" --result findings --max-severity medium --reviewer clean-context --run-id finding-no-class --evidence "bad"
expect "record-review findings 带路由码可写入" 0 python3 "$GATE" record-review overview "$RV2" --result findings --max-severity medium --finding-class OVERVIEW_DEFECT --reviewer clean-context --run-id finding-a --evidence "overview defect"
RV_DA=$(make_gate_case review-detail-audit)
expect "record-review detail clean 缺 deletion audit 被拒" 2 python3 "$GATE" record-review detail "$RV_DA" --result clean --max-severity low --reviewer clean-context --run-id detail-no-audit --evidence "detail clean"
expect "record-review detail clean 带 deletion audit 可写入" 0 python3 "$GATE" record-review detail "$RV_DA" --result clean --max-severity low --reviewer clean-context --run-id detail-audit --evidence "detail clean" --deletion-audit "none"
expect_grep "status 显示 detail deletion audit" "deletion-audit ✅ none" python3 "$GATE" status "$RV_DA"
RV_DUP=$(make_gate_case review-duplicate-status)
python3 - "$GATE" "$RV_DUP" <<'PY'
import json, subprocess, sys
gate, task_dir = sys.argv[1], sys.argv[2]
digest = subprocess.run(["python3", gate, "digest", "overview", task_dir], capture_output=True, text=True, check=True).stdout.strip()
data = {
    "guru_gates": {
        "review_runs": {
            "overview": [
                {"run_id": "dup-run", "reviewer": "clean-context", "recorded_at": "x", "artifact_digest": digest, "result": "clean", "max_severity": "none", "evidence": "first clean"},
                {"run_id": "dup-run", "reviewer": "clean-context", "recorded_at": "x", "artifact_digest": digest, "result": "clean", "max_severity": "low", "evidence": "duplicate clean"},
            ]
        }
    }
}
open(f"{task_dir}/task.json", "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
PY
expect_grep "status 明示重复 clean run-id 不计入双 clean" "重复 clean review run_id" python3 "$GATE" status "$RV_DUP"
RV_ADV=$(make_gate_case review-adversarial-required)
write_req_confirm "$RV_ADV"
python3 "$GATE" record-review overview "$RV_ADV" --result clean --max-severity none --reviewer clean-context --run-id normal-a --evidence "normal clean a" >/dev/null
python3 "$GATE" record-review overview "$RV_ADV" --result clean --max-severity low --reviewer clean-context --run-id normal-b --evidence "normal clean b" >/dev/null
expect "auto 双 clean 但缺 adversarial review 被拦" 2 python3 "$GATE" auto "$RV_ADV"
expect_grep "status 指明缺 adversarial clean review" "adversarial" python3 "$GATE" status "$RV_ADV"
python3 "$GATE" record-review overview "$RV_ADV" --result clean --max-severity low --reviewer clean-context-adversarial-claude --run-id adversarial-claude --evidence "opposite provider clean" >/dev/null
expect_grep "adversarial clean 后 auto 前进到 detail review 缺口" "record-review detail" python3 "$GATE" auto "$RV_ADV"
RV_REQ=$(make_gate_case review-req-blocker)
write_req_confirm "$RV_REQ"
python3 "$GATE" record-review overview "$RV_REQ" --result findings --max-severity high --finding-class REQ_BLOCKER --reviewer clean-context --run-id req-blocker-a --evidence "requirements boundary missing" >/dev/null
expect_grep "status 中 REQ_BLOCKER 回到需求" "需求澄清" python3 "$GATE" status "$RV_REQ"
expect_grep "check 中 REQ_BLOCKER 回到需求" "需求澄清" python3 "$GATE" check "$RV_REQ"

# 豁免理由里的普通英文词不得豁免其他类型（service 在理由中出现 ≠ 豁免 service）
PK6B=$(mk_pkg pkg-exempt-word)
printf -- "- chapter_target=svc → doc_type=service → chapters/svc-service.md\n" >> "$PK6B-docs/design-main.md"
write_detail_chapter "$PK6B-docs/chapters/svc-service.md" UNIT-svc-service "数据合同" "unit test"
printf "L2豁免：page-entry 理由：this service layer is simple\n" >> "$PK6B-docs/design-main.md"
expect "豁免理由含 service 一词不豁免 service 类型" 2 python3 "$GATE" detail "$PK6B"

# pending L2：表格行形式（无 doc_type= 前缀）也必须被识别
PK9=$(mk_pkg pkg-tablerow)
printf -- "| page | page-entry | chapters/page-entry.md |\n" >> "$PK9-docs/design-main.md"
write_detail_chapter "$PK9-docs/chapters/page-entry.md" UNIT-page-entry "Widget 设计" "widget test"
expect "full 详细表格形式 pending 被拦" 2 python3 "$GATE" detail "$PK9"

# 人工 Gate：confirm 无 TTY 被拒（agent 代跑场景）
echo '{}' > "$G/task.json"
expect "confirm 无 TTY 被拒" 2 python3 "$GATE" confirm requirements "$G"
expect_grep "confirm 拒绝信息指向用户终端" "交互式终端" python3 "$GATE" confirm requirements "$G"
expect "confirm 未知 gate 被拒" 2 python3 "$GATE" confirm nonsense "$G"

# 人工 Gate：check 按需求确认 → overview review → detail review → detail confirm 拦截 / 全证据放行
write_grills_all_done "$G"
expect "check 零确认被拦" 2 python3 "$GATE" check "$G"
expect_grep "check 报缺需求确认" "需求" python3 "$GATE" check "$G"
write_req_confirm "$G"
expect "check 缺 overview review 被拦" 2 python3 "$GATE" check "$G"
write_clean_reviews overview "$G"
expect "check 缺 detail review 被拦" 2 python3 "$GATE" check "$G"
write_clean_reviews detail "$G"
expect "check 缺 detail 确认被拦" 2 python3 "$GATE" check "$G"
# 缺 artifact_digest 的确认记录（手写伪造/旧版）不放行
cat > "$G/task.json" <<'EOF'
{"guru_gates": {"requirements": {"confirmed_by": "tester", "confirmed_at": "2026-01-01T00:00:00+00:00"},
                "detail": {"confirmed_by": "tester", "confirmed_at": "2026-01-01T00:00:00+00:00"}}}
EOF
write_reviews_all "$G"
expect "check 缺确认快照被拦" 2 python3 "$GATE" check "$G"
expect_grep "缺快照报错指明 confirm 来源" "缺确认快照" python3 "$GATE" check "$G"

DG_REQ=$(python3 "$GATE" digest requirements "$G")
DG_DT=$(python3 "$GATE" digest detail "$G")
cat > "$G/task.json" <<EOF
{"guru_gates": {"requirements": {"confirmed_by": "tester", "confirmed_at": "x", "artifact_digest": "$DG_REQ"},
                "detail": {"confirmed_by": "tester", "confirmed_at": "x", "artifact_digest": "$DG_DT"}}}
EOF
write_reviews_all "$G"
expect "check 新 Gate 证据齐全放行" 0 python3 "$GATE" check "$G"
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

GOV="$TMP/overview-structure"; mkdir -p "$GOV"; cp "$G"/*.md "$GOV/"; cp "$G/task.json" "$GOV/"
grep -v "承接索引" "$G/design.md" > "$GOV/design.md"
out=$(python3 "$GATE" check "$GOV" 2>&1); rc=$?
if [ "$rc" = 2 ] \
  && printf '%s' "$out" | grep -q "record-review overview" \
  && ! printf '%s' "$out" | grep -Eq "重新人工确认|请用户.*人工确认"; then
  pass=$((pass+1)); echo "PASS  check overview 结构失败不提示人工确认"
else failn=$((failn+1)); echo "FAIL  check overview 结构失败提示错误"; printf '%s\n' "$out" | head -4; fi

# 确认快照与 review digest：一致放行；结构仍合格但内容被改 → 当前 digest review evidence 失效
GD="$TMP/digest"; mkdir -p "$GD"; cp "$G/prd.md" "$G/design.md" "$G/implement.md" "$GD/"
D_REQ=$(python3 "$GATE" digest requirements "$GD")
D_DT=$(python3 "$GATE" digest detail "$GD")
cat > "$GD/task.json" <<EOF
{"guru_gates": {
  "requirements": {"confirmed_by": "t", "confirmed_at": "x", "artifact_digest": "$D_REQ"},
  "detail":       {"confirmed_by": "t", "confirmed_at": "x", "artifact_digest": "$D_DT"}}}
EOF
write_reviews_all "$GD"
expect "check 快照一致放行" 0 python3 "$GATE" check "$GD"
printf '\n语义改动：阈值从 8s 调成 30s\n' >> "$GD/design.md"
expect "check 设计改动后 review evidence 失效被拦" 2 python3 "$GATE" check "$GD"
expect_grep "review 失效指明 record-review" "record-review overview" python3 "$GATE" check "$GD"
expect_grep "status 设计改动后明示 review digest 失配" "digest 失配" python3 "$GATE" status "$GD"

# 写保护：经 grill-done 写路径触发，非法 JSON 必须被解析守卫拒绝且不重写
GJ="$TMP/badjson"; mkdir -p "$GJ"; cp "$G/prd.md" "$GJ/"; printf '[broken' > "$GJ/task.json"
out=$(GURU_GATE_MODE=soft python3 "$GATE" grill-done requirements "$GJ" --via-agent --user-quote "已完成 grill" 2>&1); rc=$?
if [ "$rc" = 2 ] && [ "$(cat "$GJ/task.json")" = "[broken" ] && printf '%s' "$out" | grep -q "格式非法"; then
  pass=$((pass+1)); echo "PASS  grill 写路径拒绝非法 task.json"
else
  failn=$((failn+1)); echo "FAIL  grill 写路径守卫 (rc=$rc)"; printf '%s\n' "$out" | tail -3
fi

# full 链确认快照：README 属包骨架，改动同样触发失配
GF=$(mk_pkg pkg-digest-full)
F_REQ=$(python3 "$GATE" digest requirements "$GF")
F_DT=$(python3 "$GATE" digest detail "$GF")
python3 - "$GF" "$F_REQ" "$F_DT" <<'PY'
import json, sys
gf, req, dt = sys.argv[1:4]
p = f"{gf}/task.json"
d = json.load(open(p))
d["guru_gates"] = {
    "requirements": {"confirmed_by": "t", "confirmed_at": "x", "artifact_digest": req},
    "detail": {"confirmed_by": "t", "confirmed_at": "x", "artifact_digest": dt},
}
json.dump(d, open(p, "w"), ensure_ascii=False, indent=2)
PY
write_reviews_all "$GF"
expect "full check 快照一致放行" 0 python3 "$GATE" check "$GF"
printf '\n导航入口调整\n' >> "$GF-docs/README.md"
expect "full check README 改动后 review evidence 失效被拦" 2 python3 "$GATE" check "$GF"
expect_grep "README 改动后提示 review evidence" "record-review overview" python3 "$GATE" check "$GF"
expect_grep "status 与 check 同口径呈现 review 缺口" "record-review overview" python3 "$GATE" status "$GF"

# 累积快照：上游 prd 改动 + 只重确认 requirements → 下游 overview/detail 失配
GF2=$(mk_pkg pkg-cumulative)
python3 - "$GF2" "$GATE" <<'PY'
import json, subprocess, sys
gf, gate = sys.argv[1], sys.argv[2]
def dig(g): return subprocess.run(["python3", gate, "digest", g, gf], capture_output=True, text=True).stdout.strip()
d = json.load(open(f"{gf}/task.json"))
d["guru_gates"] = {g: {"confirmed_by": "t", "confirmed_at": "x", "artifact_digest": dig(g)}
                   for g in ("requirements", "detail")}
json.dump(d, open(f"{gf}/task.json", "w"), ensure_ascii=False, indent=2)
PY
write_reviews_all "$GF2"
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
expect "累积快照：上游改动后下游 review evidence 失效被拦" 2 python3 "$GATE" check "$GF2"
expect_grep "累积快照：拦截原因是 overview review 缺口" "record-review overview" python3 "$GATE" check "$GF2"

# PreToolUse hook：shlex token 识别（引号字面量不触发；真实 start 命令触发并拦截）
HOOK="$HERE/../../hooks/platform/block-unconfirmed-start.sh"
out=$(printf '%s' '{"tool_input":{"command":"echo '\''task.py start docs'\''"}}' | bash "$HOOK" 2>&1); rc=$?
if [ "$rc" = 0 ]; then pass=$((pass+1)); echo "PASS  hook 引号字面量不触发"
else failn=$((failn+1)); echo "FAIL  hook 引号字面量误拦 (rc=$rc)"; fi
# 正例需要真实项目骨架：否则会因找不到 gate 脚本而"碰巧"退出 2（错误原因的通过）
HP="$TMP/hook-project"; mkdir -p "$HP/.trellis/scripts/guru"
ln -sf "$GATE" "$HP/.trellis/scripts/guru/guru_gate.py"
out=$(printf '{"tool_input":{"command":"python3 .trellis/scripts/task.py start %s"}}' "$GD" | CLAUDE_PROJECT_DIR="$HP" bash "$HOOK" 2>&1); rc=$?
if [ "$rc" = 2 ] && printf '%s' "$out" | grep -q "record-review overview"; then pass=$((pass+1)); echo "PASS  hook 真实 start 命令被拦（拦截原因=review evidence 缺口）"
else failn=$((failn+1)); echo "FAIL  hook 应以 review evidence 缺口拦截 (rc=$rc)"; echo "$out" | head -3; fi
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

# ============ gate_mode（strict/soft 双通道）============
SM="$TMP/softmode"; mkdir -p "$SM"; cp "$G/prd.md" "$G/design.md" "$G/implement.md" "$SM/"
expect "strict（默认）下 --via-agent 仍被拒" 2 python3 "$GATE" confirm requirements "$SM" --via-agent
grill_done requirements "$SM"
out=$(GURU_GATE_MODE=soft python3 "$GATE" confirm requirements "$SM" --via-agent --user-quote "确认，进概要" 2>&1); rc=$?
if [ "$rc" = 0 ] && grep -q '"via": "agent"' "$SM/task.json" && grep -q '确认，进概要' "$SM/task.json"; then
  pass=$((pass+1)); echo "PASS  soft 单 gate 代跑成功且留痕（via/user_quote）"
else failn=$((failn+1)); echo "FAIL  soft 代跑 (rc=$rc)"; echo "$out" | head -3; fi
expect "soft 代跑缺 --user-quote 被拒" 2 env GURU_GATE_MODE=soft python3 "$GATE" confirm "$SM" --via-agent
write_reviews_all "$SM"
expect "soft 零参数批量代跑剩余 detail Gate" 0 env GURU_GATE_MODE=soft python3 "$GATE" confirm "$SM" --via-agent --user-quote "确认全部"
expect "soft 批量后 check 放行" 0 python3 "$GATE" check "$SM"
expect_grep "status 显示 soft 留痕" "soft" python3 "$GATE" status "$SM"

# config.yaml 文件判定（无 env）：guru.gate_mode: soft
CFGROOT="$TMP/cfgroot"; mkdir -p "$CFGROOT/.trellis"
printf 'guru:\n  gate_mode: soft\n' > "$CFGROOT/.trellis/config.yaml"
SM2="$TMP/softmode2"; mkdir -p "$SM2"; cp "$G/prd.md" "$SM2/"
grill_done requirements "$SM2"
out=$(cd "$CFGROOT" && python3 "$GATE" confirm requirements "$SM2" --via-agent --user-quote "确认" 2>&1); rc=$?
if [ "$rc" = 0 ]; then pass=$((pass+1)); echo "PASS  config.yaml gate_mode: soft 生效"
else failn=$((failn+1)); echo "FAIL  config soft (rc=$rc)"; echo "$out" | head -3; fi

# env soft 需要测试专用双开关：生产环境单设 GURU_GATE_MODE=soft 不得绕过 strict
out=$(env -u GURU_GATE_ALLOW_ENV_SOFT GURU_GATE_MODE=soft python3 "$GATE" confirm requirements "$SM2" --via-agent --user-quote "x" 2>&1); rc=$?
if [ "$rc" = 2 ]; then pass=$((pass+1)); echo "PASS  env soft 无测试开关不生效（防 agent 单次注入）"
else failn=$((failn+1)); echo "FAIL  env soft 绕过 (rc=$rc)"; fi

# gate_mode 只认顶层 guru 块：其他配置节的同名键不得误开 soft
CFGROOT2="$TMP/cfgroot2"; mkdir -p "$CFGROOT2/.trellis"
printf 'other:\n  gate_mode: soft\n' > "$CFGROOT2/.trellis/config.yaml"
SM3="$TMP/softmode3"; mkdir -p "$SM3"; cp "$G/prd.md" "$SM3/"
out=$(cd "$CFGROOT2" && python3 "$GATE" confirm requirements "$SM3" --via-agent --user-quote "x" 2>&1); rc=$?
if [ "$rc" = 2 ]; then pass=$((pass+1)); echo "PASS  非 guru 块的 gate_mode 不生效（保持 strict）"
else failn=$((failn+1)); echo "FAIL  gate_mode 作用域泄漏 (rc=$rc)"; fi

# TTY 零参数批量确认（pty 逐个 y）
PT="$TMP/ptybatch"; mkdir -p "$PT"; cp "$G/prd.md" "$G/design.md" "$G/implement.md" "$PT/"
write_reviews_all "$PT"
out=$(python3 - "$GATE" "$PT" <<'PY'
import os, pty, select, sys, time
gate, td = sys.argv[1], sys.argv[2]
pid, fd = pty.fork()
if pid == 0:
    os.execvp("python3", ["python3", gate, "confirm", td])
buf, answered = b"", 0
deadline = time.time() + 30
PROMPT = "确认请输入".encode()
while True:
    if time.time() > deadline:
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
    if buf.count(PROMPT) > answered:
        os.write(fd, b"y\n"); answered += 1
_, st = os.waitpid(pid, 0)
sys.stdout.write(buf.decode(errors="replace"))
sys.exit(os.waitstatus_to_exitcode(st))
PY
); rc=$?
if [ "$rc" = 0 ] && python3 "$GATE" check "$PT" >/dev/null 2>&1; then
  pass=$((pass+1)); echo "PASS  TTY 零参数批量确认（pty 双 y）"
else failn=$((failn+1)); echo "FAIL  pty 批量 (rc=$rc)"; echo "$out" | tail -3; fi

# ===== light 链 _design_sections 分割正则盲区：'## 详细设计承接索引' 标题 + 行内 §2 不误切（修 #7）=====
HDR="$TMP/light-hdr-index"; mkdir -p "$HDR"
cp "$G/prd.md" "$G/implement.md" "$HDR/"
cat > "$HDR/design.md" <<'EOF'
## §1 概要设计
归属表：BHV-001 → owner: UseCase。为什么属于它：业务规则；为什么不属于别人：controller 无规则；是否需独立存在：是。详见 §2。
归属表：BHV-002 → owner: Controller。三问理由同上格式。
## 详细设计承接索引
chapter_target=下单 → doc_type=usecase
## §2 详细设计
EOF
append_detail_chapter "$HDR/design.md"
expect "light overview：'## 详细设计承接索引'标题+行内§2 不误拦（#7）" 0 python3 "$GATE" overview "$HDR"
expect "light detail：同上仍正确从 §2 切出 UNIT（#7）" 0 python3 "$GATE" detail "$HDR"

# ===== check_requirements P0/P1 与 CJK 紧贴（优先级P0）也识别（修 #8，对齐头部反 \b 纪律）=====
CJKP="$TMP/cjk-p0"; mkdir -p "$CJKP"
cat > "$CJKP/prd.md" <<'EOF'
## 行为规格
### BHV-001 点击
Given a When b Then c
## 核心能力
优先级P0：下单
## 失败路径
x
## 验收场景
y
## 未决问题
无
## Brainstorm Evidence
- Skill loaded: trellis-brainstorm loaded for CJK P0 fixture
- Repository evidence inspected: fixture PRD inspected
- Domain/terminology triggers: none — no new terms in fixture
- Current code vs user intent conflicts: none — fixture is requirements-only
- Product decisions confirmed:
  - DEC-001: CJK-adjacent P0 parsing confirmed
    - user_quote: "fixture confirms CJK P0"
- Open product/scope/risk questions: none — fixture declares no unresolved questions
EOF
expect "requirements：'优先级P0' CJK 紧贴被识别（#8）" 0 python3 "$GATE" requirements "$CJKP"

# ===== #2 回归：light 链 §2 标题 CJK 紧贴（## §2详细设计 无空格）detail 仍正确切出 UNIT（修 §\s*2\b 的 CJK 漏切）=====
NSP="$TMP/light-nospace"; mkdir -p "$NSP"
cp "$G/prd.md" "$G/implement.md" "$NSP/"
cat > "$NSP/design.md" <<'EOF'
## §1 概要设计
归属表：BHV-001 → owner: UseCase。为什么属于它：业务规则；为什么不属于别人：controller 无规则；是否需独立存在：是。
归属表：BHV-002 → owner: Controller。三问理由同上格式。
承接索引：chapter_target=下单 → doc_type=usecase
## §2详细设计
EOF
append_detail_chapter "$NSP/design.md"
expect "light detail：'## §2详细设计' CJK 紧贴仍正确从 §2 切出 UNIT（#2 回归）" 0 python3 "$GATE" detail "$NSP"

# ===== #8 假阳性闭合：核心能力段仅含 snake_case 标识符(user_P0_flag)无真实 P0/P1 → 仍被拦 =====
FP="$TMP/p0-falsepos"; mkdir -p "$FP"
cat > "$FP/prd.md" <<'EOF'
## 行为规格
### BHV-001 点击
Given a When b Then c
## 核心能力
下单功能（见 user_P0_flag 字段控制开关）
## 失败路径
x
## 验收场景
y
## 未决问题
无
EOF
expect "requirements：仅 user_P0_flag 无真 P0/P1 被正确拦（#8 假阳性闭合）" 2 python3 "$GATE" requirements "$FP"

# ===== #3 full 链 config-l10n（九类唯一带数字的 doc_type）pending-L2 豁免能放行（修 [a-z][a-z-]* 漏数字）=====
PKL=$(mk_pkg pkg-l10n)
printf -- "- chapter_target=l10n → doc_type=config-l10n → chapters/l10n-config.md\n" >> "$PKL-docs/design-main.md"
write_detail_chapter "$PKL-docs/chapters/l10n-config.md" UNIT-l10n-config "Widget 设计" "unit test"
expect "full 详细 config-l10n 无豁免被拦（前提）" 2 python3 "$GATE" detail "$PKL"
printf "L2豁免：config-l10n 理由：本地化资源章节首发按 L1 八问展开\n" >> "$PKL-docs/design-main.md"
expect "full 详细 config-l10n 显式豁免放行（#3：数字 doc_type 不再死锁）" 0 python3 "$GATE" detail "$PKL"

# ===== #1 跨平台：gate 运行时从已装 SSOT 解析 doc_type，非 flutter(go) 的 pending 类也能拦/豁免 =====
GOROOT="$TMP/go-proj"; mkdir -p "$GOROOT/.trellis/spec/harness/detail" "$GOROOT/task" "$GOROOT/task-docs/chapters"
printf '%s\n' '## 2. 七类 detail_doc_type' '| doc_type | 覆盖对象 | 落点 | L2 状态 |' '|---|---|---|---|' '| `biz` | 业务核心 | service/ | **v1 提供** |' '| `domain` | 领域实体 | domain/ | pending |' > "$GOROOT/.trellis/spec/harness/detail/detail-structure-single-source.md"
cp "$G/prd.md" "$G/implement.md" "$GOROOT/task/"
printf '{"guru_chain":"full","design_package":"task-docs"}\n' > "$GOROOT/task/task.json"
echo "# nav" > "$GOROOT/task-docs/README.md"
printf '%s\n' '# 概要' '## 详细设计承接索引' '- chapter_target=d → doc_type=domain → chapters/d.md' > "$GOROOT/task-docs/design-main.md"
write_detail_chapter "$GOROOT/task-docs/chapters/d.md" UNIT-order-usecase "数据合同" "unit test"
out=$(cd "$GOROOT" && python3 "$GATE" detail task 2>&1); rc=$?
{ [ "$rc" = 2 ] && printf '%s' "$out" | grep -q domain; } && { pass=$((pass+1)); echo "PASS  非flutter(go) domain(pending) 无豁免被拦（#1 运行时 SSOT taxonomy）"; } || { failn=$((failn+1)); echo "FAIL  go domain 应被拦 (rc=$rc)"; printf '%s\n' "$out" | head -2; }
printf 'L2豁免：domain 理由：领域模型首发按八问展开\n' >> "$GOROOT/task-docs/design-main.md"
out=$(cd "$GOROOT" && python3 "$GATE" detail task 2>&1); rc=$?
[ "$rc" = 0 ] && { pass=$((pass+1)); echo "PASS  非flutter(go) domain 显式豁免放行（#1）"; } || { failn=$((failn+1)); echo "FAIL  go domain 豁免应放行 (rc=$rc)"; printf '%s\n' "$out" | head -2; }

# ===== #4 制裁 TLD hook：host 段拦截、path 段(.cu 文件)不误拦（host 锚定回归）=====
TLD="$HERE/../../hooks/platform/block-sanctioned-tlds.sh"
tld_rc() { printf '{"tool_input":{"content":"%s"}}' "$1" | bash "$TLD" >/dev/null 2>&1; echo $?; }
[ "$(tld_rc 'https://bank.ir/')" = 2 ] && { pass=$((pass+1)); echo "PASS  制裁TLD host 段 bank.ir 拦截"; } || { failn=$((failn+1)); echo "FAIL  bank.ir 应拦"; }
[ "$(tld_rc '[doc](https://x.sy)')" = 2 ] && { pass=$((pass+1)); echo "PASS  制裁TLD host 段 markdown ) 收尾拦截"; } || { failn=$((failn+1)); echo "FAIL  x.sy) 应拦"; }
[ "$(tld_rc 'https://github.com/x/kernel.cu)')" = 0 ] && { pass=$((pass+1)); echo "PASS  制裁TLD path 段 .cu 文件不误拦（host 锚定，修 #4 回归）"; } || { failn=$((failn+1)); echo "FAIL  path .cu 被误拦"; }
[ "$(tld_rc 'https://iranian-news.com/')" = 0 ] && { pass=$((pass+1)); echo "PASS  制裁TLD 合法域 iranian-news.com 不误拦"; } || { failn=$((failn+1)); echo "FAIL  iranian-news 误拦"; }

# ===== 档3：requirements digest 纳入正式需求包（requirement_package）=====
# 共享 digest helper + namespaced key + 稳定排序 + manifest fail-closed + 向后兼容

# 向后兼容：无 requirement_package 任务 requirements digest 必须与历史 basename 公式逐字节一致
RPC=$(make_gate_case rp-compat)
RPC_OLD=$(python3 - "$RPC" <<'PY'
import hashlib, sys
h = hashlib.sha256(); p = sys.argv[1] + "/prd.md"
h.update(b"prd.md"); h.update(b"\0")
h.update(open(p, encoding="utf-8").read().encode("utf-8")); h.update(b"\0")
print(h.hexdigest())
PY
)
RPC_NEW=$(python3 "$GATE" digest requirements "$RPC")
if [ "$RPC_OLD" = "$RPC_NEW" ]; then pass=$((pass+1)); echo "PASS  无 requirement_package requirements digest 与历史 basename 公式一致"
else failn=$((failn+1)); echo "FAIL  无指针 digest 漂移（old=$RPC_OLD new=$RPC_NEW）"; fi

# requirement_package 版本目录：canonical 文件入 digest（namespaced）；snapshots/changes 排除
mk_req_pkg() { # mk_req_pkg <name> → 输出 task_dir；正式需求包在 <task_dir>-reqpkg
  d="$TMP/$1"; rp="$TMP/$1-reqpkg"; mkdir -p "$d" "$rp/modules" "$rp/snapshots" "$rp/changes/changes"
  cp "$G/prd.md" "$d/"
  printf '{"requirement_package": "%s"}\n' "$rp" > "$d/task.json"
  echo "# 正式需求包导航" > "$rp/README.md"
  echo "# 需求主定义 v1" > "$rp/requirement-main.md"
  echo "# 页面模块需求" > "$rp/modules/requirement-page.md"
  echo "# 关键节点快照" > "$rp/snapshots/rc.md"
  echo "# 变更日志" > "$rp/changes/change-log.md"
  echo "$d"
}

RP=$(mk_req_pkg rp-digest)
RP_KEYS=$(python3 - "$GATE" "$RP" <<'PY'
import importlib.util, sys
gate, task_dir = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("gg", gate); gg = importlib.util.module_from_spec(spec); spec.loader.exec_module(gg)
print(" ".join(sorted(a["key"] for a in gg._gate_artifacts(task_dir, "requirements"))))
PY
)
if printf '%s' "$RP_KEYS" | grep -q "task:prd.md" \
  && printf '%s' "$RP_KEYS" | grep -q "requirements:README.md" \
  && printf '%s' "$RP_KEYS" | grep -q "requirements:requirement-main.md" \
  && printf '%s' "$RP_KEYS" | grep -q "requirements:modules/requirement-page.md" \
  && ! printf '%s' "$RP_KEYS" | grep -q "snapshot" \
  && ! printf '%s' "$RP_KEYS" | grep -q "changes"; then
  pass=$((pass+1)); echo "PASS  requirement_package canonical 文件入 digest（namespaced），snapshots/changes 排除"
else failn=$((failn+1)); echo "FAIL  requirement_package 取材错误：$RP_KEYS"; fi

RP_D0=$(python3 "$GATE" digest requirements "$RP")
printf '\n新增需求规则。\n' >> "$RP-reqpkg/requirement-main.md"
RP_D1=$(python3 "$GATE" digest requirements "$RP")
if [ "$RP_D0" != "$RP_D1" ]; then pass=$((pass+1)); echo "PASS  改正式需求包 canonical 正文 → requirements digest 变（confirm/review 失效）"
else failn=$((failn+1)); echo "FAIL  canonical 正文改动未改 digest"; fi
printf '\n快照补充。\n' >> "$RP-reqpkg/snapshots/rc.md"
printf '\n变更补充。\n' >> "$RP-reqpkg/changes/change-log.md"
RP_D2=$(python3 "$GATE" digest requirements "$RP")
if [ "$RP_D1" = "$RP_D2" ]; then pass=$((pass+1)); echo "PASS  改 snapshots/changes 子树 → requirements digest 不变"
else failn=$((failn+1)); echo "FAIL  excluded 子树改动误改 digest"; fi

# 共享 digest helper：guru_supervise 与 guru_gate 对 requirements digest 同口径（解 codex blocker）
SUP="$HERE/../guru_supervise.py"
RP_GATE_DIG=$(python3 "$GATE" digest requirements "$RP")
RP_SUP_DIG=$(python3 - "$SUP" "$RP" <<'PY'
import importlib.util, os, sys
sup, task_dir = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.abspath(sup)))
spec = importlib.util.spec_from_file_location("guru_supervise", sup)
gs = importlib.util.module_from_spec(spec); sys.modules["guru_supervise"] = gs; spec.loader.exec_module(gs)
from pathlib import Path
print(gs._requirements_digest(Path(task_dir)))
PY
)
if [ "$RP_GATE_DIG" = "$RP_SUP_DIG" ]; then pass=$((pass+1)); echo "PASS  guru_supervise._requirements_digest 与 guru_gate digest 同口径（共享 helper，解 blocker）"
else failn=$((failn+1)); echo "FAIL  supervise/gate digest 分叉（gate=$RP_GATE_DIG sup=$RP_SUP_DIG）"; fi

# namespace 碰撞：正式需求包 README + design_package README 同存不碰撞（overview gate）
RPN="$TMP/rp-namespace"; RPNRP="$TMP/rp-namespace-reqpkg"; RPNDP="$TMP/rp-namespace-docs"
mkdir -p "$RPN" "$RPNRP" "$RPNDP/chapters"
cp "$G/prd.md" "$G/implement.md" "$RPN/"
printf '{"guru_chain": "full", "design_package": "%s", "requirement_package": "%s"}\n' "$RPNDP" "$RPNRP" > "$RPN/task.json"
echo "# 正式需求包 README" > "$RPNRP/README.md"
echo "# 需求主定义" > "$RPNRP/requirement-main.md"
echo "# 设计包 README" > "$RPNDP/README.md"
echo "# 概要主定义" > "$RPNDP/design-main.md"
echo "# 章节" > "$RPNDP/chapters/a.md"
RPN_OVKEYS=$(python3 - "$GATE" "$RPN" <<'PY'
import importlib.util, sys
gate, task_dir = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("gg", gate); gg = importlib.util.module_from_spec(spec); spec.loader.exec_module(gg)
print(" ".join(sorted(a["key"] for a in gg._gate_artifacts(task_dir, "overview"))))
PY
)
if printf '%s' "$RPN_OVKEYS" | grep -q "design:README.md" \
  && printf '%s' "$RPN_OVKEYS" | grep -q "requirements:README.md"; then
  pass=$((pass+1)); echo "PASS  namespace 碰撞解决：design:README.md 与 requirements:README.md 各自独立"
else failn=$((failn+1)); echo "FAIL  README namespace 碰撞未解决：$RPN_OVKEYS"; fi
# overview digest 不崩溃且确定
RPN_OV1=$(python3 "$GATE" digest overview "$RPN"); RPN_OV2=$(python3 "$GATE" digest overview "$RPN")
if [ -n "$RPN_OV1" ] && [ "$RPN_OV1" = "$RPN_OV2" ]; then pass=$((pass+1)); echo "PASS  含正式需求包+设计包的 overview digest 确定且不崩溃"
else failn=$((failn+1)); echo "FAIL  overview digest 不确定/崩溃"; fi

# 稳定排序：不同枚举/创建顺序 → 同一 digest
SORT_A=$(python3 - "$GATE" "$TMP" <<'PY'
import importlib.util, json, os, sys, tempfile
gate, root = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("gg", gate); gg = importlib.util.module_from_spec(spec); spec.loader.exec_module(gg)
def build(order):
    base = tempfile.mkdtemp(dir=root); d = os.path.join(base, "task"); pkg = os.path.join(base, "pkg")
    os.makedirs(os.path.join(d)); os.makedirs(os.path.join(pkg, "modules"))
    open(os.path.join(d, "prd.md"), "w").write("# PRD\n### BHV-001 x\n")
    json.dump({"requirement_package": pkg}, open(os.path.join(d, "task.json"), "w"))
    files = [("a.md", "A"), ("z.md", "Z"), ("modules/m.md", "M"), ("modules/b.md", "B")]
    for rel, body in (files if order == "fwd" else list(reversed(files))):
        fp = os.path.join(pkg, rel); os.makedirs(os.path.dirname(fp), exist_ok=True); open(fp, "w").write(body)
    return gg._gate_digest(d, "requirements")
print("EQUAL" if build("fwd") == build("rev") else "DIFFER")
PY
)
[ "$SORT_A" = "EQUAL" ] && { pass=$((pass+1)); echo "PASS  稳定排序：不同创建顺序 requirements digest 一致"; } || { failn=$((failn+1)); echo "FAIL  排序不稳定（$SORT_A）"; }

# manifest 缺失 → fallback（requirements gate 不阻断）
RPMF=$(mk_req_pkg rp-manifest-missing)
expect "manifest 缺失 requirements gate fallback 放行" 0 python3 "$GATE" requirements "$RPMF"

# manifest 自定义 canonical_root + 内联 excludes
RPMC="$TMP/rp-manifest-custom"; RPMCRP="$TMP/rp-manifest-custom-reqpkg"
mkdir -p "$RPMC" "$RPMCRP/v/draft" "$RPMCRP/v/snap"
cp "$G/prd.md" "$RPMC/"
printf '{"requirement_package": "%s"}\n' "$RPMCRP" > "$RPMC/task.json"
printf 'canonical_root: v\ncanonical_excludes: [draft, snap]\n' > "$RPMCRP/manifest.yaml"
echo "# 主" > "$RPMCRP/v/requirement-main.md"
echo "# 草稿" > "$RPMCRP/v/draft/wip.md"
echo "# 快照" > "$RPMCRP/v/snap/old.md"
RPMC_KEYS=$(python3 - "$GATE" "$RPMC" <<'PY'
import importlib.util, sys
gate, task_dir = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("gg", gate); gg = importlib.util.module_from_spec(spec); spec.loader.exec_module(gg)
print(" ".join(sorted(a["key"] for a in gg._gate_artifacts(task_dir, "requirements"))))
PY
)
if printf '%s' "$RPMC_KEYS" | grep -q "requirements:v/requirement-main.md" \
  && ! printf '%s' "$RPMC_KEYS" | grep -q "draft" \
  && ! printf '%s' "$RPMC_KEYS" | grep -q "snap"; then
  pass=$((pass+1)); echo "PASS  manifest 自定义 canonical_root + 内联 excludes 生效"
else failn=$((failn+1)); echo "FAIL  manifest 自定义 root/excludes 错误：$RPMC_KEYS"; fi

# manifest 非法（excludes 非列表）→ requirements gate fail-closed 阻断 + 修复提示
RPMB=$(mk_req_pkg rp-manifest-bad)
printf 'canonical_excludes: notalist\n' > "$RPMB-reqpkg/manifest.yaml"
expect "manifest 非法 requirements gate 阻断（fail-closed）" 2 python3 "$GATE" requirements "$RPMB"
expect_grep "manifest 非法报错给修复提示" "manifest 非法" python3 "$GATE" requirements "$RPMB"
expect_grep "manifest 非法 digest 子命令也阻断" "manifest 非法" python3 "$GATE" digest requirements "$RPMB"
expect_grep "manifest 非法 status 也阻断" "manifest" python3 "$GATE" status "$RPMB"

# manifest 非法（canonical_root 为列表）→ 阻断
RPMB2=$(mk_req_pkg rp-manifest-bad-root)
printf 'canonical_root: [a, b]\n' > "$RPMB2-reqpkg/manifest.yaml"
expect "manifest canonical_root 列表非法阻断" 2 python3 "$GATE" requirements "$RPMB2"

# requirement_package 端到端：confirm requirements → 改正式需求包 canonical → 确认快照失配
RPE2E=$(mk_req_pkg rp-e2e)
write_req_confirm "$RPE2E"
expect "requirement_package 基线：requirements 确认快照一致（check 报缺 overview 而非快照失配）" 2 python3 "$GATE" check "$RPE2E"
# check 在 requirements 确认快照一致后应推进到 overview review 缺口，而非需求确认失配
out=$(python3 "$GATE" check "$RPE2E" 2>&1)
if printf '%s' "$out" | grep -q "record-review overview" && ! printf '%s' "$out" | grep -q "需求 Gate.*确认快照失配"; then
  pass=$((pass+1)); echo "PASS  requirement_package 基线 requirements 确认快照一致（推进到 overview）"
else failn=$((failn+1)); echo "FAIL  requirement_package 基线确认快照异常"; printf '%s\n' "$out" | head -3; fi
printf '\n正式需求包正文变更：新增验收口径。\n' >> "$RPE2E-reqpkg/requirement-main.md"
out=$(python3 "$GATE" status "$RPE2E" 2>&1)
if printf '%s' "$out" | grep -q "确认快照失配"; then
  pass=$((pass+1)); echo "PASS  改正式需求包正文 → requirements 确认快照失配（confirm 失效）"
else failn=$((failn+1)); echo "FAIL  正式需求包正文改动未触发 requirements 确认失配"; printf '%s\n' "$out" | head -4; fi

# ===== 档3 返工（codex 代码审查 Needs-rework，逐条回归）=====

# [blocker] cwd≠root + --root + relative requirement_package：supervise 写入 digest 必须 == gate current digest
# 旧实现 _requirement_package_dir 用 os.getcwd() 当 repo root，supervise --root（cwd≠root）会把
# docs/... 解析成 <cwd>/docs/...（空包/错包）→ 与 gate 从 repo root 算的 digest 分叉、review 立刻 stale。
# 此用例不开 GURU_GATE_ALLOW_ABS（走生产围栏），requirement_package 为 repo-root 相对路径。
BLK_OUT=$(env -u GURU_GATE_ALLOW_ABS python3 - "$GATE" "$SUP" "$TMP" <<'PY'
import importlib.util, json, os, sys
from pathlib import Path
gate, sup, tmp = sys.argv[1], sys.argv[2], sys.argv[3]
repo = os.path.join(tmp, "blk-repo")
tdir = os.path.join(repo, ".trellis", "tasks", "t")
rel = "docs/requirements/versions/v1"
apkg = os.path.join(repo, rel)
os.makedirs(tdir); os.makedirs(apkg)
open(os.path.join(tdir, "prd.md"), "w").write("# PRD\n### BHV-001 x\n")
open(os.path.join(apkg, "README.md"), "w").write("# req readme\n")
open(os.path.join(apkg, "requirement-main.md"), "w").write("# req main\n")
json.dump({"requirement_package": rel}, open(os.path.join(tdir, "task.json"), "w"))
spec = importlib.util.spec_from_file_location("gg", gate); gg = importlib.util.module_from_spec(spec); spec.loader.exec_module(gg)
spec2 = importlib.util.spec_from_file_location("guru_supervise", sup)
gs = importlib.util.module_from_spec(spec2); sys.modules["guru_supervise"] = gs
sys.path.insert(0, os.path.dirname(os.path.abspath(sup))); spec2.loader.exec_module(gs)
# gate: cwd == repo root, repo_root=None（relative 解析 vs cwd）
cwd0 = os.getcwd(); os.chdir(repo)
gate_dig = gg.requirements_digest(os.path.join(".trellis", "tasks", "t"))
os.chdir(cwd0)
# supervise: cwd == cwd0 (绝对不等于 repo)，显式传 repo_root=repo（模拟 --root）
assert os.path.realpath(os.getcwd()) != os.path.realpath(repo)
sup_dig = gs._requirements_digest(Path(tdir), Path(repo))
# buggy 对照：supervise 不传 repo_root（按错 cwd 解析）→ 必须与 gate 分叉（证明 param 是必需的）
import hashlib
prd = hashlib.sha256(); prd.update(b"prd.md"); prd.update(b"\0")
prd.update(open(os.path.join(tdir, "prd.md"), encoding="utf-8").read().encode("utf-8")); prd.update(b"\0")
includes_pkg = gate_dig != prd.hexdigest()
print("SAME" if gate_dig == sup_dig else "DIFF", "INCLPKG" if includes_pkg else "PRDONLY")
PY
)
if [ "$BLK_OUT" = "SAME INCLPKG" ]; then pass=$((pass+1)); echo "PASS  [blocker] cwd≠root + --root + relative pkg：supervise digest == gate digest 且纳入正式需求包"
else failn=$((failn+1)); echo "FAIL  [blocker] cwd≠root supervise/gate 分叉或未纳入包（$BLK_OUT）"; fi

# [major] 向后兼容：无指针 overview/detail digest 与历史 basename 公式逐字节一致（含重复 basename 设计包）
# 复刻 HEAD _gate_digest（sorted by basename，stable）；重复 basename：chapters/design-main.md + chapters/implement.md。
BC_OUT=$(python3 - "$GATE" "$TMP" <<'PY'
import hashlib, importlib.util, json, os, sys
gate, tmp = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("gg", gate); gg = importlib.util.module_from_spec(spec); spec.loader.exec_module(gg)
base = os.path.join(tmp, "bc-dup"); task = os.path.join(base, "t"); pkg = os.path.join(base, "pkg")
os.makedirs(os.path.join(pkg, "chapters")); os.makedirs(task)
open(os.path.join(task, "prd.md"), "w").write("# PRD\n### BHV-001 x\n")
open(os.path.join(task, "implement.md"), "w").write("# IMP\nplan UNIT-x\n")
open(os.path.join(pkg, "README.md"), "w").write("# readme\n")
open(os.path.join(pkg, "design-main.md"), "w").write("# main\n")
open(os.path.join(pkg, "chapters", "design-main.md"), "w").write("# CHAP dup design-main\n")
open(os.path.join(pkg, "chapters", "implement.md"), "w").write("# CHAP dup implement\n")
open(os.path.join(pkg, "chapters", "a.md"), "w").write("# chap a\n")
json.dump({"guru_chain": "full", "design_package": pkg}, open(os.path.join(task, "task.json"), "w"))
def old_arts(gate_name):
    req = [os.path.join(task, "prd.md")]
    if gate_name == "requirements": return req
    ov = req + [os.path.join(pkg, "README.md"), os.path.join(pkg, "design-main.md")]
    if gate_name == "overview": return ov
    dt = [os.path.join(pkg, "chapters", n) for n in gg._chapter_files(pkg)]
    dt.append(os.path.join(task, "implement.md"))
    seen, out = set(), []
    for p in ov + dt:
        if p not in seen: seen.add(p); out.append(p)
    return out
def old_digest(gate_name):
    h = hashlib.sha256()
    for p in sorted(old_arts(gate_name), key=os.path.basename):
        h.update(os.path.basename(p).encode()); h.update(b"\0")
        h.update(gg.read(p).encode()); h.update(b"\0")
    return h.hexdigest()
ok = all(gg._gate_digest(task, g) == old_digest(g) for g in ("requirements", "overview", "detail"))
dup = "design-main.md" in gg._chapter_files(pkg) and "implement.md" in gg._chapter_files(pkg)
print("EQUAL" if ok and dup else "DIFFER")
PY
)
# GURU_GATE_ALLOW_ABS=1 已全局导出（abs design_package 夹具需要）
[ "$BC_OUT" = "EQUAL" ] && { pass=$((pass+1)); echo "PASS  [major] 无指针 overview/detail digest 与历史 basename 公式一致（含重复 basename 设计包）"; } || { failn=$((failn+1)); echo "FAIL  [major] 无指针 overview/detail byte-compat 破坏（$BC_OUT）"; }

# [minor] 合同：后补 requirement_package = 需求取材范围变化，必须使下游 cumulative digest stale（预期）
ST_OUT=$(python3 - "$GATE" "$TMP" <<'PY'
import importlib.util, json, os, sys
gate, tmp = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("gg", gate); gg = importlib.util.module_from_spec(spec); spec.loader.exec_module(gg)
base = os.path.join(tmp, "rp-late"); task = os.path.join(base, "t"); pkg = os.path.join(base, "pkg")
os.makedirs(task); os.makedirs(pkg)
open(os.path.join(task, "prd.md"), "w").write("# PRD\n### BHV-001 x\n")
open(os.path.join(pkg, "requirement-main.md"), "w").write("# req main\n")
json.dump({}, open(os.path.join(task, "task.json"), "w"))
before = gg._gate_digest(task, "requirements")
json.dump({"requirement_package": pkg}, open(os.path.join(task, "task.json"), "w"))
after = gg._gate_digest(task, "requirements")
print("STALE" if before != after else "SAME")
PY
)
[ "$ST_OUT" = "STALE" ] && { pass=$((pass+1)); echo "PASS  [minor] 后补 requirement_package → requirements digest 变更（取材范围变化使下游 stale，预期）"; } || { failn=$((failn+1)); echo "FAIL  [minor] 后补 requirement_package 未触发 digest 变更（$ST_OUT）"; }

# [major] 围栏 fail-closed：requirement_package 目录不存在 → requirements gate 阻断（不空枚举）
RPMISS="$TMP/rp-missing"; mkdir -p "$RPMISS"
cp "$G/prd.md" "$RPMISS/"
printf '{"requirement_package": "%s/rp-missing-nope"}\n' "$TMP" > "$RPMISS/task.json"
expect "[major] requirement_package 目录不存在 fail-closed 阻断" 2 python3 "$GATE" requirements "$RPMISS"
expect_grep "[major] 目录不存在报错给修复提示" "版本目录不存在" python3 "$GATE" requirements "$RPMISS"

# [major] 围栏 fail-closed：canonical_root 穿越包外 → 阻断
RPESC=$(mk_req_pkg rp-root-escape)
printf 'canonical_root: ../../..\n' > "$RPESC-reqpkg/manifest.yaml"
expect "[major] canonical_root 穿越包外 fail-closed 阻断" 2 python3 "$GATE" requirements "$RPESC"
expect_grep "[major] canonical_root 越界报错给提示" "canonical_root" python3 "$GATE" requirements "$RPESC"

# [major] 围栏 fail-closed：canonical_root 目录不存在 → 阻断（不空枚举）
RPCRM=$(mk_req_pkg rp-canonical-missing)
printf 'canonical_root: v999\n' > "$RPCRM-reqpkg/manifest.yaml"
expect "[major] canonical_root 目录不存在 fail-closed 阻断" 2 python3 "$GATE" requirements "$RPCRM"

# [major] manifest fail-closed 补全：顶层无法解析的目标键/语法行必须阻断（不静默 fallback）
RPNC=$(mk_req_pkg rp-manifest-nocolon)
printf 'canonical_excludes [snapshots, changes]\n' > "$RPNC-reqpkg/manifest.yaml"
expect "[major] manifest 无冒号目标行 fail-closed 阻断" 2 python3 "$GATE" requirements "$RPNC"
RPEQ=$(mk_req_pkg rp-manifest-eq)
printf 'canonical_root = v\n' > "$RPEQ-reqpkg/manifest.yaml"
expect "[major] manifest equals-assignment fail-closed 阻断" 2 python3 "$GATE" requirements "$RPEQ"
RPTY=$(mk_req_pkg rp-manifest-typo)
printf 'canoncal_excludes: [a]\nrandombareword\n' > "$RPTY-reqpkg/manifest.yaml"
expect "[major] manifest typo bareword 行 fail-closed 阻断" 2 python3 "$GATE" requirements "$RPTY"
RPUC=$(mk_req_pkg rp-manifest-unclosed)
printf 'canonical_excludes: [a, b\n' > "$RPUC-reqpkg/manifest.yaml"
expect "[major] manifest 内联列表未闭合 fail-closed 阻断" 2 python3 "$GATE" requirements "$RPUC"
RPBD=$(mk_req_pkg rp-manifest-blockbad)
printf 'canonical_excludes:\n  notadash\n' > "$RPBD-reqpkg/manifest.yaml"
expect "[major] manifest 块列表非 dash-item fail-closed 阻断" 2 python3 "$GATE" requirements "$RPBD"

# [major] manifest 块列表（合法）+ 非目标键块列表（supersedes）容忍：canonical 取材正确
RPBL="$TMP/rp-manifest-block"; RPBLRP="$TMP/rp-manifest-block-reqpkg"
mkdir -p "$RPBL" "$RPBLRP/v1/modules" "$RPBLRP/v1/snapshots"
cp "$G/prd.md" "$RPBL/"
printf '{"requirement_package": "%s"}\n' "$RPBLRP" > "$RPBL/task.json"
printf 'version: v1\nsupersedes:\n  - v0\ncanonical_root: v1\ncanonical_excludes:\n  - snapshots\n  - changes\n' > "$RPBLRP/manifest.yaml"
echo "# 主" > "$RPBLRP/v1/requirement-main.md"
echo "# 页面" > "$RPBLRP/v1/modules/requirement-page.md"
echo "# 快照" > "$RPBLRP/v1/snapshots/rc.md"
RPBL_KEYS=$(python3 - "$GATE" "$RPBL" <<'PY'
import importlib.util, sys
gate, task_dir = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("gg", gate); gg = importlib.util.module_from_spec(spec); spec.loader.exec_module(gg)
print(" ".join(sorted(a["key"] for a in gg._gate_artifacts(task_dir, "requirements"))))
PY
)
if printf '%s' "$RPBL_KEYS" | grep -q "requirements:v1/requirement-main.md" \
  && printf '%s' "$RPBL_KEYS" | grep -q "requirements:v1/modules/requirement-page.md" \
  && ! printf '%s' "$RPBL_KEYS" | grep -q "snapshot"; then
  pass=$((pass+1)); echo "PASS  [major] manifest 块列表 excludes 生效 + 非目标键块列表(supersedes)容忍"
else failn=$((failn+1)); echo "FAIL  [major] manifest 块列表取材错误：$RPBL_KEYS"; fi

# ============================================================================
# P0 ②③ 控制流测试：guru_risk 触发判定 / run_implement_check provider 隔离 /
# collect_gate_artifacts fail-closed / _package_dir cwd≠root 锚定。
# 注：本块在 python 内 pop GURU_GATE_ALLOW_ABS 以测**生产语义**（拒绝绝对、按 repo_root 锚定）；
# run_tests 全局 export 它=1 会让 _package_dir 提前返回、绕过 repo_root 锚定，掩盖 cwd≠root 修复。
# ============================================================================
P0_OUT="$(PYTHONPATH="$HERE/.." python3 - <<'PY'
import io, os, json, sys, tempfile, subprocess, argparse, contextlib
os.environ.pop("GURU_GATE_ALLOW_ABS", None)   # 测生产语义，不走夹具逃生口
os.environ.pop("GURU_GATE_ALLOW_ENV_SOFT", None)
import guru_risk as R
import guru_gate as G
import guru_supervise as gs

np = nf = 0
def ok(desc, cond):
    global np, nf
    if cond:
        np += 1; print(f"PASS  {desc}")
    else:
        nf += 1; print(f"FAIL  {desc}")

def mk(git=True, risk=None, guru_risk=None, design_package=None, requirement_package=None,
       guru_chain=None, files=(), prd=False):
    root = tempfile.mkdtemp()
    tdir = os.path.join(root, ".trellis", "tasks", "06-29-x")
    os.makedirs(tdir)
    tj = {"id": "x", "status": "in_progress"}
    if risk is not None: tj["risk_level"] = risk
    if guru_risk is not None: tj["guru_risk"] = guru_risk
    if design_package is not None: tj["design_package"] = design_package
    if requirement_package is not None: tj["requirement_package"] = requirement_package
    if guru_chain is not None: tj["guru_chain"] = guru_chain
    with open(os.path.join(tdir, "task.json"), "w", encoding="utf-8") as fh:
        json.dump(tj, fh)
    if prd:
        with open(os.path.join(tdir, "prd.md"), "w", encoding="utf-8") as fh:
            fh.write("# prd\n### BHV-001 x\nGiven When Then\n")
    for f in files:
        p = os.path.join(root, f)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write("x")
    if git:
        subprocess.run(["git", "-C", root, "init", "-q"], check=True)
    return root, tdir

APPROVED = {"level": "low", "reviewer_approved": True,
            "approved_by": "r", "approved_at": "2026-06-29", "evidence": "e"}

# ---- ③ implement_check_independent_required 触发判定 ----
root, tdir = mk(risk="low", guru_risk=APPROVED, files=["lib/main.dart"])
req, why = R.implement_check_independent_required(tdir, "flutter", root)
ok("③d flutter 合法 approved-low + 无跨层 → 不要求独立 check", req is False)

root, tdir = mk(files=["lib/main.dart"])
req, why = R.implement_check_independent_required(tdir, "flutter", root)
ok("③d2 flutter 缺 risk 元数据 → unknown fail-closed 要求", req is True and "unknown" in why)

root, tdir = mk(risk="low", files=["lib/data/order_datasource.dart"])
req, why = R.implement_check_independent_required(tdir, "flutter", root)
ok("③d3a flutter 裸 low + untracked datasource(storage 信号) → 要求", req is True and "cross-layer" in why)

root, tdir = mk(risk="low", guru_risk=APPROVED,
                files=["lib/api/order_api.dart", "lib/page/order_page.dart"])
req, why = R.implement_check_independent_required(tdir, "flutter", root)
ok("③d3a2 flutter approved-low 但 api+ui 跨 2 层 → 仍要求(跨层 override approval)",
   req is True and "cross-layer" in why)

root, tdir = mk(risk="low", files=["lib/main.dart"])
req, why = R.implement_check_independent_required(tdir, "flutter", root)
ok("③d3b flutter 裸 low 无合法 approval + 无跨层 → 要求(非 true-low)",
   req is True and "bare low" in why)

root, tdir = mk(git=False, risk="low", files=["lib/main.dart"])
req, why = R.implement_check_independent_required(tdir, "flutter", root)
ok("③d4 非 git root(porcelain 失败) → unknown_scan_failed fail-closed 要求",
   req is True and "unknown_scan_failed" in why)

root, tdir = mk(risk="high", files=["lib/data/x_datasource.dart"])
req, why = R.implement_check_independent_required(tdir, "go", root)
ok("③ 非 flutter(go) high → 不要求(仅 flutter 生效)", req is False and why == "non-flutter")

# ---- ③ run_implement_check dry-run：provider 隔离 ----
def workers_for(platform, risk, provider="codex"):
    root, tdir = mk(risk=risk, files=["lib/main.dart"])
    args = argparse.Namespace(task_dir=tdir, root=root, platform=platform, provider=provider,
                              adversarial=False, trellis_bin="trellis", run_id="RID", dry_run=True)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = gs.run_implement_check(args)
    workers = [l.split("=", 1)[1] for l in out.getvalue().splitlines() if l.startswith("WORKER=")]
    return rc, workers, err.getvalue()

rc, w, err = workers_for("flutter", "high")
ok("③a flutter high dry-run → implement=codex, check=对立(claude) + 审计行",
   rc == 0 and len(w) == 2 and "codex" in w[0] and "claude" in w[1] and "独立实现期 review ON" in err)

rc, w, err = workers_for("go", "high")
ok("③ go high dry-run → check 同 provider(codex)，不隔离",
   rc == 0 and len(w) == 2 and "codex" in w[1] and "独立实现期 review ON" not in err)

# ---- ② _package_dir cwd≠root 锚定（生产语义）----
root, tdir = mk(design_package="design/pkg", guru_chain="full")
os.makedirs(os.path.join(root, "design", "pkg"))
got = G._package_dir(tdir, repo_root=root)
ok("②cwd _package_dir(repo_root=root) → 锚定 root 的绝对(realpath)路径",
   got is not None and os.path.isabs(got)
   and os.path.realpath(got) == os.path.realpath(os.path.join(root, "design/pkg")))

prev = os.getcwd()
try:
    other = tempfile.mkdtemp()
    os.chdir(other)
    got_none = G._package_dir(tdir, repo_root=None)
    ok("②cwd _package_dir(repo_root=None) → 历史相对语义(不锚 root)",
       got_none == "design/pkg")
finally:
    os.chdir(prev)

root_e, tdir_e = mk(design_package="../escape", guru_chain="full")
ok("②cwd _package_dir 拒绝 `..` 穿越(repo_root 给定)",
   G._package_dir(tdir_e, repo_root=root_e) is None)

# ---- ② collect_gate_artifacts fail-closed ----
root, tdir = mk(requirement_package="docs/req/missing", prd=True)
try:
    G.collect_gate_artifacts(tdir, "detail", repo_root=root)
    ok("②fc requirement_package 版本目录不存在 → 抛 GateArtifactError", False)
except G.GateArtifactError:
    ok("②fc requirement_package 版本目录不存在 → 抛 GateArtifactError", True)

root, tdir = mk(requirement_package="../escape", prd=True)
try:
    G.collect_gate_artifacts(tdir, "detail", repo_root=root)
    ok("②fc requirement_package `..` 穿越 → 抛 GateArtifactError", False)
except G.GateArtifactError:
    ok("②fc requirement_package `..` 穿越 → 抛 GateArtifactError", True)

root, tdir = mk(design_package="design/missing", guru_chain="full", prd=True)
try:
    G.collect_gate_artifacts(tdir, "detail", repo_root=root)
    ok("②fc full 链 design_package 目录不存在 → 抛 GateArtifactError", False)
except G.GateArtifactError:
    ok("②fc full 链 design_package 目录不存在 → 抛 GateArtifactError", True)

# ② 正常：cwd≠root + 合法 design_package（完整骨架 README+design-main+chapters）+ 无 req pkg → 不抛
root, tdir = mk(design_package="design/pkg", guru_chain="full", prd=True)
_pkgdir = os.path.join(root, "design", "pkg")
os.makedirs(os.path.join(_pkgdir, "chapters"))
open(os.path.join(_pkgdir, "design-main.md"), "w", encoding="utf-8").write("# d\n")
open(os.path.join(_pkgdir, "README.md"), "w", encoding="utf-8").write("# nav\n")
prev = os.getcwd()
try:
    os.chdir(tempfile.mkdtemp())
    try:
        G.collect_gate_artifacts(tdir, "detail", repo_root=root)
        ok("②ok cwd≠root + 合法 design_package + 无 req pkg → 不抛(锚定 root)", True)
    except G.GateArtifactError as exc:
        ok(f"②ok cwd≠root + 合法 design_package + 无 req pkg → 不抛(锚定 root)：{exc}", False)
finally:
    os.chdir(prev)

# ---- ③ finding1: implement-check 强制 non-advisory（外部 --adversarial 不得降级 check 失败为 rc0）----
captured = []
real_execute = gs._execute_plan
def fake_execute(plan, cfg):
    captured.append((plan.action, cfg.adversarial))
    # implement 成功、check 失败：实现期独立 check 失败必须阻断（不得走 _skip_adversarial 的 rc0）
    return (1, "error", "") if plan.action == "check" else (0, "done", "")
gs._execute_plan = fake_execute
try:
    root, tdir = mk(risk="high", files=["lib/main.dart"])
    args = argparse.Namespace(task_dir=tdir, root=root, platform="flutter", provider="codex",
                              adversarial=True, trellis_bin="trellis", run_id="RID", dry_run=False)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = gs.run_implement_check(args)
    adv_flags = [a for (_, a) in captured]
    ok("③f1 implement-check 内部强制 non-advisory（即便外部传 --adversarial=True）",
       len(adv_flags) >= 1 and all(a is False for a in adv_flags))
    ok("③f1 独立 check 失败 → run_implement_check rc≠0 阻断（非 advisory rc0）", rc != 0)
finally:
    gs._execute_plan = real_execute

# ---- ② finding2: full 链缺 design_package 字段 → collect_gate_artifacts fail-closed ----
root, tdir = mk(guru_chain="full", prd=True)  # guru_chain=full 但完全无 design_package 字段
try:
    G.collect_gate_artifacts(tdir, "detail", repo_root=root)
    ok("②fc full 链缺 design_package 字段 → 抛 GateArtifactError", False)
except G.GateArtifactError:
    ok("②fc full 链缺 design_package 字段 → 抛 GateArtifactError", True)

# ---- ③ finding3: 路径匹配精化（消除子串误报、保留真命中）----
root, tdir = mk(risk="low", guru_risk=APPROVED, files=["lib/feedback/feedback_helper.dart"])
req, why = R.implement_check_independent_required(tdir, "flutter", root)
ok("③f3 lib/feedback(含子串 db) approved-low → 不误判 storage、不要求", req is False)

root, tdir = mk(risk="low", guru_risk=APPROVED, files=["lib/utils/block_parser.dart"])
req, why = R.implement_check_independent_required(tdir, "flutter", root)
ok("③f3 block_parser(含子串 bloc) approved-low → 不误判 controller 跨层、不要求", req is False)

root, tdir = mk(risk="low", guru_risk=APPROVED,
                files=["lib/data/order_database_helper.dart", "lib/page/order_page.dart"])
req, why = R.implement_check_independent_required(tdir, "flutter", root)
ok("③f3 真 database+ui 跨层(精化后仍检出) → 要求", req is True and "cross-layer" in why)

# ---- ③ R2-blocker: high 信号不被 nested low_risk 抢先吞掉（high 全局优先 fail-closed）----
root, tdir = mk(risk="high",
                guru_risk={"low_risk": True, "level": "low", "reviewer_approved": True,
                           "approved_by": "r", "approved_at": "2026-06-29", "evidence": "e"},
                files=["lib/main.dart"])
req, why = R.implement_check_independent_required(tdir, "flutter", root)
ok("③R2b flutter risk_level=high 叠加 nested approved-low → 仍要求(high 优先，不被吞)",
   req is True and why == "high-risk")

# ---- ③ R2-should_fix: implement-check --adversarial 不翻转 implement provider ----
root, tdir = mk(risk="high", files=["lib/main.dart"])
args = argparse.Namespace(task_dir=tdir, root=root, platform="flutter", provider="codex",
                          adversarial=True, trellis_bin="trellis", run_id="RID", dry_run=True)
out, err = io.StringIO(), io.StringIO()
with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    rc = gs.run_implement_check(args)
w = [l.split("=", 1)[1] for l in out.getvalue().splitlines() if l.startswith("WORKER=")]
ok("③R2f2 implement-check --adversarial：implement 仍用 codex(不翻转)、check 用对立 claude",
   rc == 0 and len(w) == 2 and "codex" in w[0] and "claude" in w[1])

# ---- ② R2-should_fix: full design_package 目录在但缺核心骨架文件 → fail-closed ----
root, tdir = mk(design_package="design/pkg2", guru_chain="full", prd=True)
_p = os.path.join(root, "design", "pkg2")
os.makedirs(os.path.join(_p, "chapters"))
open(os.path.join(_p, "README.md"), "w", encoding="utf-8").write("# nav\n")  # 缺 design-main.md
try:
    G.collect_gate_artifacts(tdir, "detail", repo_root=root)
    ok("②R2f3 full design_package 目录在但缺 design-main.md → 抛 GateArtifactError", False)
except G.GateArtifactError:
    ok("②R2f3 full design_package 目录在但缺 design-main.md → 抛 GateArtifactError", True)

root, tdir = mk(design_package="design/pkg3", guru_chain="full", prd=True)
_p = os.path.join(root, "design", "pkg3")
os.makedirs(_p)  # 无 chapters/
open(os.path.join(_p, "README.md"), "w", encoding="utf-8").write("# nav\n")
open(os.path.join(_p, "design-main.md"), "w", encoding="utf-8").write("# d\n")
try:
    G.collect_gate_artifacts(tdir, "detail", repo_root=root)
    ok("②R2f3 full design_package 缺 chapters/ (detail) → 抛 GateArtifactError", False)
except G.GateArtifactError:
    ok("②R2f3 full design_package 缺 chapters/ (detail) → 抛 GateArtifactError", True)

print(f"COUNT {np} {nf}")
sys.exit(0 if nf == 0 else 1)
PY
)"
echo "$P0_OUT" | grep -v '^COUNT '
read P0P P0F <<<"$(printf '%s\n' "$P0_OUT" | sed -n 's/^COUNT //p')"
pass=$((pass + ${P0P:-0})); failn=$((failn + ${P0F:-1}))

# ============================================================================
# P1a 测试:guru_review_record packet schema(两层非空)/reader/writer/preflight +
# guru_risk slice_packet_risk / implement_check_independent_required(unit_id) 三分支。
# ============================================================================
P1A_OUT="$(PYTHONPATH="$HERE/.." python3 - <<'PY'
import os, json, sys, tempfile, subprocess
import guru_review_record as R
import guru_risk as K

np = nf = 0
def ok(d, c):
    global np, nf
    if c: np += 1; print(f"PASS  {d}")
    else: nf += 1; print(f"FAIL  {d}")

def mktask():
    root = tempfile.mkdtemp(); tdir = os.path.join(root, ".trellis/tasks/x"); os.makedirs(tdir); return root, tdir

def write_packet(tdir, unit, **over):
    d = os.path.join(tdir, "slice-packets"); os.makedirs(d, exist_ok=True)
    pkt = {"schema_version": 1, "slice_id": unit, "owner_unit": unit, "target_kind": "staged",
           "target_paths": ["lib/x.dart"],
           "invariants": [{"invariant_id": "INV-1", "rule": "r", "source": "detail", "owner": "DAO",
                           "positive_case": "p", "negative_case": "n", "route_if_missing": "DETAIL_DEFECT"}]}
    pkt.update(over)
    open(os.path.join(d, f"{unit}.json"), "w", encoding="utf-8").write(json.dumps(pkt))

def mkgit(risk=None):
    root, tdir = mktask()
    open(os.path.join(tdir, "task.json"), "w", encoding="utf-8").write(
        json.dumps({"risk_level": risk} if risk else {}))
    subprocess.run(["git", "-C", root, "init", "-q"], check=True)
    return root, tdir

# --- load_packet schema(两层非空)---
root, tdir = mktask(); write_packet(tdir, "UNIT-a")
try:
    R.load_packet(tdir, "UNIT-a"); ok("P1a load_packet 合法 packet 通过", True)
except Exception as e:
    ok(f"P1a 合法 packet 应通过:{e}", False)

for case, over in [("空 invariants", {"invariants": []}), ("空 target_paths", {"target_paths": []}),
                   ("未知 schema_version", {"schema_version": 2}),
                   ("risk=medium", {"risk": "medium"}),
                   ("provider=manual+required", {"semantic_review_provider": {"required": True, "provider": "manual"}})]:
    root, tdir = mktask(); write_packet(tdir, "U", **over)
    try:
        R.load_packet(tdir, "U"); ok(f"P1a {case} → PACKET_INVALID", False)
    except R.ReviewRecordError:
        ok(f"P1a {case} → PACKET_INVALID", True)

root, tdir = mktask(); write_packet(tdir, "U", risk="unknown")
ok("P1a risk=unknown → None 不 raise", R.load_packet(tdir, "U")["risk"] is None)
root, tdir = mktask()
try:
    R.load_packet(tdir, "missing"); ok("P1a 缺失 packet → ReviewRecordError", False)
except R.ReviewRecordError:
    ok("P1a 缺失 packet → ReviewRecordError", True)

# --- append_record / preflight_failure_record ---
root, tdir = mktask()
R.append_record(tdir, {"run_id": "r", "slice_id": "UNIT-a", "review_target": "slice:UNIT-a",
                       "review_result": "clean", "route_class": "none"})
rec = json.loads(open(os.path.join(tdir, "review-records/implementation-reviews.jsonl"), encoding="utf-8").readline())
ok("P1a append_record 写出含 review_target 可读", rec.get("review_target") == "slice:UNIT-a")
pf = R.preflight_failure_record("PACKET_MISSING", "r", unit_id="UNIT-a")
ok("P1a preflight PACKET_MISSING: route_class=none + repairable=false(非 PROCESS_DEFECT)",
   pf["route_class"] == "none" and pf["repairable"] is False and pf["supervisor_failure"] == "PACKET_MISSING")
pf2 = R.preflight_failure_record("PACKET_AMBIGUOUS", "r", candidates=["UNIT-a", "UNIT-b"])
ok("P1a preflight 无 unit → slice:unknown + candidates 回读",
   pf2["review_target"] == "slice:unknown" and pf2.get("candidates") == ["UNIT-a", "UNIT-b"])

# --- slice_packet_risk ---
root, tdir = mktask(); write_packet(tdir, "U", risk="high")
ok("P1a slice_packet_risk high", K.slice_packet_risk(tdir, "U") == "high")
root, tdir = mktask(); write_packet(tdir, "U", risk="low")
ok("P1a slice_packet_risk low", K.slice_packet_risk(tdir, "U") == "low")
root, tdir = mktask(); write_packet(tdir, "U", risk_reasons=["cross_layer"])
ok("P1a slice_packet_risk risk_reasons→high", K.slice_packet_risk(tdir, "U") == "high")

# --- implement_check_independent_required(unit_id) 三分支 ---
root, tdir = mkgit("low"); write_packet(tdir, "U", risk="high")
req, why = K.implement_check_independent_required(tdir, "flutter", root, unit_id="U")
ok("P1a packet.risk=high override task low → required", req is True and "slice-packet high" in why)
root, tdir = mkgit("high"); write_packet(tdir, "U", risk="low")
req, why = K.implement_check_independent_required(tdir, "flutter", root, unit_id="U")
ok("P1a packet.risk=low override task high → 不 required(R8-F1 slice low)", req is False and "slice-packet low" in why)
root, tdir = mkgit(); write_packet(tdir, "U")  # packet 无 risk + task unknown
req, why = K.implement_check_independent_required(tdir, "flutter", root, unit_id="U")
ok("P1a packet 无 risk + task unknown → 回落 P0 required", req is True)
root, tdir = mkgit("high")
req, why = K.implement_check_independent_required(tdir, "flutter", root)  # unit_id=None
ok("P1a unit_id=None → P0 字节兼容(task high→required)", req is True and why == "high-risk")

print(f"COUNT {np} {nf}")
sys.exit(0 if nf == 0 else 1)
PY
)"
echo "$P1A_OUT" | grep -v '^COUNT '
read P1AP P1AF <<<"$(printf '%s\n' "$P1A_OUT" | sed -n 's/^COUNT //p')"
pass=$((pass + ${P1AP:-0})); failn=$((failn + ${P1AF:-1}))

# ============================================================================
# P1b 测试:run_implement_check 的 packet resolve + packet/scope preflight
# (PACKET_MISSING/AMBIGUOUS/SCOPE_INVALID 硬停 exit2 不进 repairable;单 packet auto;无 packet 回落 P0)。
# ============================================================================
P1B_OUT="$(PYTHONPATH="$HERE/.." python3 - <<'PY'
import os, json, sys, tempfile, subprocess, io, contextlib, argparse
import guru_review_record as R  # noqa: F401
import guru_supervise as gs

np = nf = 0
def ok(d, c):
    global np, nf
    if c: np += 1; print(f"PASS  {d}")
    else: nf += 1; print(f"FAIL  {d}")

def mkgit():
    root = tempfile.mkdtemp(); tdir = os.path.join(root, ".trellis/tasks/x"); os.makedirs(tdir)
    open(os.path.join(tdir, "task.json"), "w", encoding="utf-8").write("{}")
    subprocess.run(["git", "-C", root, "init", "-q"], check=True)
    return root, tdir

def write_packet(tdir, unit, **over):
    d = os.path.join(tdir, "slice-packets"); os.makedirs(d, exist_ok=True)
    pkt = {"schema_version": 1, "slice_id": unit, "owner_unit": unit, "target_kind": "staged",
           "target_paths": ["lib/x.dart"],
           "invariants": [{"invariant_id": "INV-1", "rule": "r", "source": "detail", "owner": "DAO",
                           "positive_case": "p", "negative_case": "n", "route_if_missing": "DETAIL_DEFECT"}]}
    pkt.update(over)
    open(os.path.join(d, f"{unit}.json"), "w", encoding="utf-8").write(json.dumps(pkt))

def run_ic(tdir, root, slice=None):
    args = argparse.Namespace(task_dir=tdir, root=root, platform="flutter", provider="codex",
                              adversarial=False, trellis_bin="trellis", run_id="RID", dry_run=True, slice=slice)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = gs.run_implement_check(args)
    return rc, out.getvalue(), err.getvalue()

def jsonl_last(tdir):
    p = os.path.join(tdir, "review-records/implementation-reviews.jsonl")
    return json.loads(open(p, encoding="utf-8").readlines()[-1]) if os.path.exists(p) else None

# 1. --slice 指定但 packet 缺失 → PACKET_MISSING exit2(repairable=false, route_class=none)
root, tdir = mkgit()
rc, o, e = run_ic(tdir, root, slice="UNIT-missing")
rec = jsonl_last(tdir)
ok("P1b --slice 缺失 packet → exit2 + PACKET_MISSING(repairable=false,route=none)",
   rc == 2 and rec and rec["supervisor_failure"] == "PACKET_MISSING" and rec["repairable"] is False and rec["route_class"] == "none")

# 2. 多 packet 无 --slice → PACKET_AMBIGUOUS exit2 + candidates
root, tdir = mkgit(); write_packet(tdir, "UNIT-a"); write_packet(tdir, "UNIT-b")
rc, o, e = run_ic(tdir, root)
rec = jsonl_last(tdir)
ok("P1b 多 packet 无 --slice → exit2 + PACKET_AMBIGUOUS + candidates",
   rc == 2 and rec and rec["supervisor_failure"] == "PACKET_AMBIGUOUS" and rec.get("candidates") == ["UNIT-a", "UNIT-b"])

# 3. 单 packet auto-select + scope clean(无代码 dirty)→ dry-run rc0
root, tdir = mkgit(); write_packet(tdir, "UNIT-a")
rc, o, e = run_ic(tdir, root)
ok("P1b 单 packet auto-select + scope clean → dry-run rc0 不硬停", rc == 0)

# 4. scope invalid(untracked 越界 .dart)→ SCOPE_INVALID exit2
root, tdir = mkgit(); write_packet(tdir, "UNIT-a")
os.makedirs(os.path.join(root, "lib")); open(os.path.join(root, "lib/other.dart"), "w", encoding="utf-8").write("x")
rc, o, e = run_ic(tdir, root)
rec = jsonl_last(tdir)
ok("P1b scope invalid(越界 lib/other.dart)→ exit2 + SCOPE_INVALID",
   rc == 2 and rec and rec["supervisor_failure"] == "SCOPE_INVALID")

# 5. dirty 属 target_paths → 不硬停 rc0
root, tdir = mkgit(); write_packet(tdir, "UNIT-a")
os.makedirs(os.path.join(root, "lib")); open(os.path.join(root, "lib/x.dart"), "w", encoding="utf-8").write("x")
rc, o, e = run_ic(tdir, root)
ok("P1b dirty 属 target_paths → 不硬停 rc0", rc == 0)

# 6. 无 packet → P0 路径 dry-run rc0(不强制 packet)
root, tdir = mkgit()
rc, o, e = run_ic(tdir, root)
ok("P1b 无 packet → P0 路径 dry-run rc0(不硬停)", rc == 0)

print(f"COUNT {np} {nf}")
sys.exit(0 if nf == 0 else 1)
PY
)"
echo "$P1B_OUT" | grep -v '^COUNT '
read P1BP P1BF <<<"$(printf '%s\n' "$P1B_OUT" | sed -n 's/^COUNT //p')"
pass=$((pass + ${P1BP:-0})); failn=$((failn + ${P1BF:-1}))

echo "----"; echo "结果: $pass 通过 / $failn 失败"
[ "$failn" = 0 ]
