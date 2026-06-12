#!/usr/bin/env bash
# guru_gate.py 最小夹具测试：合格样本通过(0)、缺章样本被拦(2)且提示含缺口关键词。
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
行为1：Given 有库存 When 点击 Then 状态变更
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
归属表：行为1 → owner: UseCase。为什么属于它：业务规则；为什么不属于别人：controller 无规则；是否需独立存在：是。
承接索引：chapter_target=下单 → doc_type=usecase
## §2 详细设计
承接的行为：行为1。失败收口：上抛枚举。测试映射：unit test 成功+失败各1。不得补造：不决定缓存策略。
EOF
  cat > "$d/implement.md" <<'EOF'
## 计划（切片）
片1：usecase 接口
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
  else failn=$((failn+1)); echo "FAIL  $desc (want=$want got=$rc)"; echo "$out" | head -3; fi
}

G=$(mk_good)
expect "requirements 合格通过" 0 python3 "$GATE" requirements "$G"
expect "overview 合格通过"     0 python3 "$GATE" overview "$G"
expect "detail 合格通过"       0 python3 "$GATE" detail "$G"
expect "implement 合格通过"    0 python3 "$GATE" implement "$G"

B="$TMP/bad-req"; mkdir -p "$B"; grep -v "失败路径\|网络失败" "$G/prd.md" > "$B/prd.md"
expect "requirements 缺失败路径被拦" 2 python3 "$GATE" requirements "$B"

B2="$TMP/bad-ov"; mkdir -p "$B2"; cp "$G/prd.md" "$B2/"; sed 's/承接索引.*//' "$G/design.md" > "$B2/design.md"
expect "overview 缺承接索引被拦" 2 python3 "$GATE" overview "$B2"

B3="$TMP/bad-dt"; mkdir -p "$B3"; cp "$G/prd.md" "$B3/"; sed 's/不得补造.*//' "$G/design.md" > "$B3/design.md"; cp "$G/implement.md" "$B3/"
expect "detail 缺不得补造声明被拦" 2 python3 "$GATE" detail "$B3"

B4="$TMP/bad-imp"; mkdir -p "$B4"; cp "$G/prd.md" "$G/design.md" "$B4/" 2>/dev/null; cp "$G/design.md" "$B4/"; grep -v "证据\|analyze" "$G/implement.md" > "$B4/implement.md"
expect "implement 缺证据节被拦" 2 python3 "$GATE" implement "$B4"

echo "----"; echo "结果: $pass 通过 / $failn 失败"
[ "$failn" = 0 ]
