#!/usr/bin/env bash
# guru_gate.py 夹具测试：合格通过(0)、缺章/断链被拦(2)、trace-matrix 矩阵与孤儿清单。
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
GATE="$HERE/../guru_gate.py"
TMP="$(mktemp -d)"
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

echo "----"; echo "结果: $pass 通过 / $failn 失败"
[ "$failn" = 0 ]
