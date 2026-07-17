#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GURU_TEMPLATE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPO_ROOT="$(cd "$GURU_TEMPLATE_DIR/.." && pwd)"
PACKAGE_GURU_DIR="$REPO_ROOT/packages/cli/src/templates/guru"
MODE=check

fail() {
  printf 'SLICE_PLANNING_POLICY_TEST_FAILED: %s\n' "$*" >&2
  exit 1
}

usage() {
  printf 'Usage: %s [--sync]\n' "${0##*/}" >&2
}

case "$#" in
  0) ;;
  1)
    [ "$1" = "--sync" ] || {
      usage
      fail "unsupported argument: $1"
    }
    MODE=sync
    ;;
  *)
    usage
    fail "expected no arguments or exactly --sync"
    ;;
esac

PAIR_TABLE='guru-template/overlay/policy/delivery-policy.json|packages/cli/src/templates/guru/overlay/policy/delivery-policy.json
guru-template/workflows/guru-client-workflow.md|packages/cli/src/templates/guru/workflows/guru-client.md
guru-template/workflows/guru-go-workflow.md|packages/cli/src/templates/guru/workflows/guru-go.md
guru-template/workflows/guru-h5-workflow.md|packages/cli/src/templates/guru/workflows/guru-h5.md
guru-template/workflows/guru-ios-workflow.md|packages/cli/src/templates/guru/workflows/guru-ios.md
guru-template/overlay/agents-skills/client-design-detail-writing/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/client-design-detail-writing/SKILL.md
guru-template/overlay/agents-skills/client-design-detail-review/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/client-design-detail-review/SKILL.md
guru-template/overlay/agents-skills/go-design-detail-writing/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/go-design-detail-writing/SKILL.md
guru-template/overlay/agents-skills/go-design-detail-review/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/go-design-detail-review/SKILL.md
guru-template/overlay/agents-skills/h5-design-detail-writing/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/h5-design-detail-writing/SKILL.md
guru-template/overlay/agents-skills/h5-design-detail-review/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/h5-design-detail-review/SKILL.md
guru-template/overlay/agents-skills/ios-design-detail-writing/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/ios-design-detail-writing/SKILL.md
guru-template/overlay/agents-skills/ios-design-detail-review/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/ios-design-detail-review/SKILL.md
guru-template/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md|packages/cli/src/templates/guru/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md
guru-template/specs/guru-go-backend/harness/implementation/implementation-trace-contract.md|packages/cli/src/templates/guru/specs/guru-go-backend/harness/implementation/implementation-trace-contract.md
guru-template/specs/guru-h5-web/harness/implementation/implementation-trace-contract.md|packages/cli/src/templates/guru/specs/guru-h5-web/harness/implementation/implementation-trace-contract.md
guru-template/specs/guru-ios-native/harness/implementation/implementation-trace-contract.md|packages/cli/src/templates/guru/specs/guru-ios-native/harness/implementation/implementation-trace-contract.md
guru-template/overlay/agents-skills/flutter-implementation-guru-review/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/flutter-implementation-guru-review/SKILL.md
guru-template/overlay/agents-skills/go-implementation-guru-review/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/go-implementation-guru-review/SKILL.md
guru-template/overlay/agents-skills/h5-implementation-guru-review/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/h5-implementation-guru-review/SKILL.md
guru-template/overlay/agents-skills/ios-implementation-guru-review/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/ios-implementation-guru-review/SKILL.md
guru-template/overlay/agents-skills/flutter-implementation-guru-writing/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/flutter-implementation-guru-writing/SKILL.md
guru-template/overlay/agents-skills/go-implementation-guru-writing/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/go-implementation-guru-writing/SKILL.md
guru-template/overlay/agents-skills/h5-implementation-guru-writing/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/h5-implementation-guru-writing/SKILL.md
guru-template/overlay/agents-skills/ios-implementation-guru-writing/SKILL.md|packages/cli/src/templates/guru/overlay/agents-skills/ios-implementation-guru-writing/SKILL.md
guru-template/specs/guru-go-backend/harness/implementation/implementation-go-guru-standard.md|packages/cli/src/templates/guru/specs/guru-go-backend/harness/implementation/implementation-go-guru-standard.md
guru-template/specs/guru-h5-web/harness/implementation/implementation-h5-standard.md|packages/cli/src/templates/guru/specs/guru-h5-web/harness/implementation/implementation-h5-standard.md
guru-template/specs/guru-ios-native/harness/implementation/implementation-ios-standard.md|packages/cli/src/templates/guru/specs/guru-ios-native/harness/implementation/implementation-ios-standard.md
guru-template/overlay/tests/slice_planning_policy_test.sh|packages/cli/src/templates/guru/overlay/tests/slice_planning_policy_test.sh'

require_literal() {
  local needle="$1"
  local path="$2"
  grep -Fq -- "$needle" "$path" || \
    fail "required policy text is missing from ${path#$REPO_ROOT/}: $needle"
}

forbid_literal() {
  local needle="$1"
  local path="$2"
  grep -Fq -- "$needle" "$path" && \
    fail "obsolete policy text remains in ${path#$REPO_ROOT/}: $needle"
  return 0
}

reject_affirmative_ordinary_global_check() {
  local path="$1"
  local command_pattern="$2"
  local offending_line

  offending_line="$({
    awk -v command_pattern="$command_pattern" '
      $0 ~ command_pattern &&
      $0 ~ /(Full\/high ordinary|逐片验证|每片)/ &&
      $0 !~ /(Integration|non-Full|Small|Micro|Lite|v1|不运行|不得|禁止|只由|只在|才运行|不得升级)/ {
        print NR ":" $0
        exit
      }
    ' "$path"
  } || true)"

  [ -z "$offending_line" ] || \
    fail "ordinary scope still requires a global check in ${path#$REPO_ROOT/}: $offending_line"
}

expected_peer_for() {
  local source_rel="$1"
  local suffix="${source_rel#guru-template/}"
  local workflow_name

  case "$source_rel" in
    guru-template/workflows/*-workflow.md)
      workflow_name="${source_rel#guru-template/workflows/}"
      workflow_name="${workflow_name%-workflow.md}"
      printf 'packages/cli/src/templates/guru/workflows/%s.md\n' "$workflow_name"
      ;;
    *)
      printf 'packages/cli/src/templates/guru/%s\n' "$suffix"
      ;;
  esac
}

validate_relative_path() {
  local path="$1"
  case "$path" in
    ""|/*|../*|*/../*|*/..|*//*)
      fail "unsafe or non-relative table path: $path"
      ;;
  esac
}

pair_count=0
seen_sources='
'
seen_peers='
'
ordinary_sources='
'

while IFS='|' read -r source_rel peer_rel; do
  [ -n "$source_rel" ] || continue
  [ -n "$peer_rel" ] || fail "missing peer for source: $source_rel"
  validate_relative_path "$source_rel"
  validate_relative_path "$peer_rel"

  case "$source_rel" in
    guru-template/*) ;;
    *) fail "source is outside guru-template: $source_rel" ;;
  esac
  case "$peer_rel" in
    packages/cli/src/templates/guru/*) ;;
    *) fail "peer is outside the package Guru bundle: $peer_rel" ;;
  esac

  expected_peer="$(expected_peer_for "$source_rel")"
  [ "$peer_rel" = "$expected_peer" ] || \
    fail "peer mapping is outside the declared source mapping: $source_rel -> $peer_rel"

  case "$seen_sources" in
    *"
$source_rel
"*) fail "duplicate source in pair table: $source_rel" ;;
  esac
  case "$seen_peers" in
    *"
$peer_rel
"*) fail "duplicate peer in pair table: $peer_rel" ;;
  esac
  seen_sources="${seen_sources}${source_rel}
"
  seen_peers="${seen_peers}${peer_rel}
"
  pair_count=$((pair_count + 1))

  source_path="$REPO_ROOT/$source_rel"
  peer_path="$REPO_ROOT/$peer_rel"
  [ -f "$source_path" ] || fail "declared source is missing: $source_rel"
  [ -d "$(dirname "$peer_path")" ] || \
    fail "declared peer parent directory is missing: ${peer_rel%/*}"

  if [ "$source_rel" != "guru-template/overlay/tests/slice_planning_policy_test.sh" ]; then
    ordinary_sources="${ordinary_sources}${source_rel}
"
  fi

  if [ "$MODE" = sync ]; then
    cp "$source_path" "$peer_path"
  else
    [ -f "$peer_path" ] || fail "declared peer is missing: $peer_rel"
  fi

  cmp -s "$source_path" "$peer_path" || \
    fail "canonical/package bytes differ: $source_rel -> $peer_rel"
done <<< "$PAIR_TABLE"

[ "$pair_count" -eq 29 ] || fail "expected exactly 29 source/peer pairs, found $pair_count"

active_worker_files='guru-template/overlay/agents-skills/flutter-implementation-guru-writing/SKILL.md
guru-template/overlay/agents-skills/go-implementation-guru-writing/SKILL.md
guru-template/overlay/agents-skills/h5-implementation-guru-writing/SKILL.md
guru-template/overlay/agents-skills/ios-implementation-guru-writing/SKILL.md
guru-template/specs/guru-go-backend/harness/implementation/implementation-go-guru-standard.md
guru-template/specs/guru-h5-web/harness/implementation/implementation-h5-standard.md
guru-template/specs/guru-ios-native/harness/implementation/implementation-ios-standard.md'

while IFS= read -r active_rel; do
  [ -n "$active_rel" ] || continue
  case "$seen_sources" in
    *"
$active_rel
"*) ;;
    *) fail "active implementation consumer is missing from the bounded sync table: $active_rel" ;;
  esac
done <<< "$active_worker_files"

external_drift_paths='packages/cli/src/templates/guru/overlay/reinstall-official-067.sh
packages/cli/src/templates/guru/overlay/tests/reinstall_official_067_test.sh
packages/cli/src/templates/guru/overlay/verify/tests/test_slice_commit_lifecycle.py
packages/cli/src/templates/guru/overlay/README.md
packages/cli/src/templates/guru/overlay/verify/guru_gate.py
packages/cli/src/templates/guru/overlay/verify/guru_review_record.py
packages/cli/src/templates/guru/overlay/verify/guru_supervise.py'

while IFS= read -r external_rel; do
  [ -n "$external_rel" ] || continue
  case "$seen_peers" in
    *"
$external_rel
"*) fail "external baseline drift entered the bounded sync table: $external_rel" ;;
  esac
  git -C "$REPO_ROOT" diff --quiet -- "$external_rel" || \
    fail "external baseline drift path was modified: $external_rel"
  git -C "$REPO_ROOT" diff --cached --quiet -- "$external_rel" || \
    fail "external baseline drift path was staged: $external_rel"
done <<< "$external_drift_paths"

while IFS= read -r ordinary_rel; do
  [ -n "$ordinary_rel" ] || continue
  git -C "$REPO_ROOT" diff --quiet -- "$ordinary_rel" || \
    fail "Integration rewrote ordinary canonical bytes: $ordinary_rel"
  git -C "$REPO_ROOT" diff --cached --quiet -- "$ordinary_rel" || \
    fail "Integration staged ordinary canonical bytes: $ordinary_rel"
done <<< "$ordinary_sources"

policy="$GURU_TEMPLATE_DIR/overlay/policy/delivery-policy.json"
python3 -m json.tool "$policy" >/dev/null
require_literal '"full_high_default_strategy": "minimum_commit_stable_parallel_first"' "$policy"
require_literal '"max_ordinary_slices": 4' "$policy"
require_literal '"mutable_path_overlap": 0' "$policy"
require_literal '"review_context_target_bytes": 262144' "$policy"
require_literal '"ordinary_depends_on_default": []' "$policy"
require_literal '"single_integration_slice": true' "$policy"
require_literal '"formal_evidence_control_worktree": "serial"' "$policy"

workflow_files='guru-template/workflows/guru-client-workflow.md
guru-template/workflows/guru-go-workflow.md
guru-template/workflows/guru-h5-workflow.md
guru-template/workflows/guru-ios-workflow.md'
while IFS= read -r workflow_rel; do
  [ -n "$workflow_rel" ] || continue
  workflow="$REPO_ROOT/$workflow_rel"
  require_literal 'full_high_default_strategy=minimum_commit_stable_parallel_first' "$workflow"
  require_literal 'mutable_path_overlap=0' "$workflow"
  require_literal 'implement-slices ... --dry-run' "$workflow"
  require_literal '同一 snapshot 只启动一个 semantic reviewer' "$workflow"
  require_literal 'Full/high ordinary 只运行 packet 声明的 `deterministic_checks` 与 focused evidence' "$workflow"
  require_literal 'Integration Slice` 才运行 project-wide' "$workflow"
  require_literal 'Small、Micro、Lite、non-Full 和 v1 保留原 route verification' "$workflow"
done <<< "$workflow_files"

detail_skill_files='guru-template/overlay/agents-skills/client-design-detail-writing/SKILL.md
guru-template/overlay/agents-skills/client-design-detail-review/SKILL.md
guru-template/overlay/agents-skills/go-design-detail-writing/SKILL.md
guru-template/overlay/agents-skills/go-design-detail-review/SKILL.md
guru-template/overlay/agents-skills/h5-design-detail-writing/SKILL.md
guru-template/overlay/agents-skills/h5-design-detail-review/SKILL.md
guru-template/overlay/agents-skills/ios-design-detail-writing/SKILL.md
guru-template/overlay/agents-skills/ios-design-detail-review/SKILL.md'
while IFS= read -r skill_rel; do
  [ -n "$skill_rel" ] || continue
  skill="$REPO_ROOT/$skill_rel"
  require_literal 'mutable owner' "$skill"
  require_literal 'covered_units' "$skill"
  require_literal 'resource_locks' "$skill"
  require_literal '262144' "$skill"
done <<< "$detail_skill_files"

trace_files='guru-template/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md
guru-template/specs/guru-go-backend/harness/implementation/implementation-trace-contract.md
guru-template/specs/guru-h5-web/harness/implementation/implementation-trace-contract.md
guru-template/specs/guru-ios-native/harness/implementation/implementation-trace-contract.md'
while IFS= read -r trace_rel; do
  [ -n "$trace_rel" ] || continue
  trace="$REPO_ROOT/$trace_rel"
  require_literal 'review_evidence_schema_version=2' "$trace"
  require_literal 'requirements_design_inputs' "$trace"
  require_literal 'integration_owned_paths' "$trace"
  require_literal 'full regression' "$trace"
done <<< "$trace_files"

reviewer_files='guru-template/overlay/agents-skills/flutter-implementation-guru-review/SKILL.md
guru-template/overlay/agents-skills/go-implementation-guru-review/SKILL.md
guru-template/overlay/agents-skills/h5-implementation-guru-review/SKILL.md
guru-template/overlay/agents-skills/ios-implementation-guru-review/SKILL.md'
while IFS= read -r reviewer_rel; do
  [ -n "$reviewer_rel" ] || continue
  reviewer="$REPO_ROOT/$reviewer_rel"
  require_literal '一个 current snapshot 恰好由一个 semantic reviewer' "$reviewer"
  require_literal 'review_evidence_schema_version=2' "$reviewer"
  require_literal 'integration_owned_paths' "$reviewer"
  require_literal '不得运行 full regression' "$reviewer"
  require_literal '第一段只能逐行输出以下 7 个字段' "$reviewer"
  require_literal 'findings=none' "$reviewer"
  require_literal '不运行开放式再发现 probe，不输出 multiline probe' "$reviewer"
  forbid_literal '结论（三选一，置顶）' "$reviewer"
done <<< "$reviewer_files"

legacy_slice_phrases='人工确认从最小切片开始
人工确认从最小可独立编译的切片开始
人工确认从最小可独立通过 `tsc` 的切片开始
每片小到可独立 review
从最小切片开始'

while IFS= read -r active_rel; do
  [ -n "$active_rel" ] || continue
  active="$REPO_ROOT/$active_rel"
  require_literal 'Full/high ordinary' "$active"
  require_literal 'packet `deterministic_checks`' "$active"
  require_literal 'focused checks' "$active"
  require_literal 'Integration' "$active"
  require_literal 'Small、Micro、Lite、non-Full' "$active"

  while IFS= read -r legacy_phrase; do
    [ -n "$legacy_phrase" ] || continue
    forbid_literal "$legacy_phrase" "$active"
  done <<< "$legacy_slice_phrases"
done <<< "$active_worker_files"

forbid_literal 'golangci-lint run →' \
  "$REPO_ROOT/guru-template/overlay/agents-skills/go-implementation-guru-writing/SKILL.md"
forbid_literal '    - tsc --noEmit' \
  "$REPO_ROOT/guru-template/overlay/agents-skills/h5-implementation-guru-writing/SKILL.md"
forbid_literal '    - next lint' \
  "$REPO_ROOT/guru-template/overlay/agents-skills/h5-implementation-guru-writing/SKILL.md"
forbid_literal '    - 编译：xcodebuild build' \
  "$REPO_ROOT/guru-template/overlay/agents-skills/ios-implementation-guru-writing/SKILL.md"

for writer_rel in \
  guru-template/overlay/agents-skills/go-implementation-guru-writing/SKILL.md \
  guru-template/overlay/agents-skills/h5-implementation-guru-writing/SKILL.md \
  guru-template/overlay/agents-skills/ios-implementation-guru-writing/SKILL.md; do
  require_literal '仅当 current packet 或 planning audit' "$REPO_ROOT/$writer_rel"
  require_literal 'undeclared tests' "$REPO_ROOT/$writer_rel"
done

for standard_rel in \
  guru-template/specs/guru-go-backend/harness/implementation/implementation-go-guru-standard.md \
  guru-template/specs/guru-h5-web/harness/implementation/implementation-h5-standard.md \
  guru-template/specs/guru-ios-native/harness/implementation/implementation-ios-standard.md; do
  standard="$REPO_ROOT/$standard_rel"
  forbid_literal '所有 current packets' "$standard"
  require_literal 'singular current packet' "$standard"
  require_literal '完整依赖 packet set 均有 current receipt' "$standard"
  require_literal '所有计划设计单元 slices' "$standard"
  require_literal '| Full/high ordinary evidence |' "$standard"
  require_literal 'test / startup / Secret 仅在 packet/audit 明确声明时记录' "$standard"
  require_literal '| Integration evidence |' "$standard"
  require_literal '| non-Full/v1 evidence |' "$standard"
done

for trace_rel in \
  guru-template/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md \
  guru-template/specs/guru-go-backend/harness/implementation/implementation-trace-contract.md \
  guru-template/specs/guru-h5-web/harness/implementation/implementation-trace-contract.md \
  guru-template/specs/guru-ios-native/harness/implementation/implementation-trace-contract.md; do
  trace="$REPO_ROOT/$trace_rel"
  require_literal 'current packet 或 planning audit focused checks 明确声明测试时' "$trace"
  require_literal 'undeclared tests' "$trace"
done

for reviewer_rel in \
  guru-template/overlay/agents-skills/flutter-implementation-guru-review/SKILL.md \
  guru-template/overlay/agents-skills/go-implementation-guru-review/SKILL.md \
  guru-template/overlay/agents-skills/h5-implementation-guru-review/SKILL.md \
  guru-template/overlay/agents-skills/ios-implementation-guru-review/SKILL.md; do
  reviewer="$REPO_ROOT/$reviewer_rel"
  require_literal 'current packet 或 planning audit focused checks 明确声明测试时' "$reviewer"
  require_literal 'undeclared tests' "$reviewer"
done

forbid_literal '| 测试 | 每个切片对应的测试命令' \
  "$REPO_ROOT/guru-template/specs/guru-flutter-client/harness/implementation/implementation-trace-contract.md"
forbid_literal '| 测试 | 每个切片对应的测试命令' \
  "$REPO_ROOT/guru-template/specs/guru-go-backend/harness/implementation/implementation-trace-contract.md"
forbid_literal '| 单元测试 | `pnpm vitest run <path>`' \
  "$REPO_ROOT/guru-template/specs/guru-h5-web/harness/implementation/implementation-trace-contract.md"
forbid_literal '| 测试 | 每个切片对应测试命令' \
  "$REPO_ROOT/guru-template/specs/guru-ios-native/harness/implementation/implementation-trace-contract.md"
forbid_literal 'G4 测试证据：每个切片有测试名级别结果' \
  "$REPO_ROOT/guru-template/specs/guru-go-backend/harness/implementation/implementation-trace-contract.md"

forbid_literal '| 启动验证 |' \
  "$REPO_ROOT/guru-template/specs/guru-go-backend/harness/implementation/implementation-go-guru-standard.md"
forbid_literal '| Secret 残留 |' \
  "$REPO_ROOT/guru-template/specs/guru-go-backend/harness/implementation/implementation-go-guru-standard.md"
forbid_literal '| 启动/冒烟 |' \
  "$REPO_ROOT/guru-template/specs/guru-h5-web/harness/implementation/implementation-h5-standard.md"
forbid_literal '| Secret 残留 |' \
  "$REPO_ROOT/guru-template/specs/guru-h5-web/harness/implementation/implementation-h5-standard.md"
forbid_literal '| 静态/告警 |' \
  "$REPO_ROOT/guru-template/specs/guru-ios-native/harness/implementation/implementation-ios-standard.md"
forbid_literal '| 启动/冒烟 |' \
  "$REPO_ROOT/guru-template/specs/guru-ios-native/harness/implementation/implementation-ios-standard.md"
forbid_literal '| Secret 残留 |' \
  "$REPO_ROOT/guru-template/specs/guru-ios-native/harness/implementation/implementation-ios-standard.md"

while IFS= read -r workflow_rel; do
  [ -n "$workflow_rel" ] || continue
  workflow="$REPO_ROOT/$workflow_rel"
  while IFS= read -r legacy_phrase; do
    [ -n "$legacy_phrase" ] || continue
    forbid_literal "$legacy_phrase" "$workflow"
  done <<< "$legacy_slice_phrases"
done <<< "$workflow_files"

reject_affirmative_ordinary_global_check \
  "$REPO_ROOT/guru-template/overlay/agents-skills/flutter-implementation-guru-writing/SKILL.md" \
  'flutter analyze|full regression'
reject_affirmative_ordinary_global_check \
  "$REPO_ROOT/guru-template/overlay/agents-skills/go-implementation-guru-writing/SKILL.md" \
  'go build \\.\/\\.\\.\\.|go vet \\.\/\\.\\.\\.|golangci-lint run|go test \\.\/\\.\\.\\.|full regression'
reject_affirmative_ordinary_global_check \
  "$REPO_ROOT/guru-template/overlay/agents-skills/h5-implementation-guru-writing/SKILL.md" \
  'tsc --noEmit|next build|eslint \\.|full regression'
reject_affirmative_ordinary_global_check \
  "$REPO_ROOT/guru-template/overlay/agents-skills/ios-implementation-guru-writing/SKILL.md" \
  'xcodebuild|swiftlint|full regression'
reject_affirmative_ordinary_global_check \
  "$REPO_ROOT/guru-template/specs/guru-go-backend/harness/implementation/implementation-go-guru-standard.md" \
  'go build \\.\/\\.\\.\\.|go vet \\.\/\\.\\.\\.|golangci-lint run|go test \\.\/\\.\\.\\.|full regression'
reject_affirmative_ordinary_global_check \
  "$REPO_ROOT/guru-template/specs/guru-h5-web/harness/implementation/implementation-h5-standard.md" \
  'tsc --noEmit|next build|eslint \\.|full regression'
reject_affirmative_ordinary_global_check \
  "$REPO_ROOT/guru-template/specs/guru-ios-native/harness/implementation/implementation-ios-standard.md" \
  'xcodebuild|swiftlint|full regression'

printf 'SLICE_PLANNING_POLICY_OK mode=%s pairs=%s package_root=%s\n' \
  "$MODE" "$pair_count" "${PACKAGE_GURU_DIR#$REPO_ROOT/}"
