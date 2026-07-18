#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
GURU_TEMPLATE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
REPO_ROOT="$(cd "$GURU_TEMPLATE_DIR/.." && pwd -P)"
PACKAGE_GURU_DIR="$REPO_ROOT/packages/cli/src/templates/guru"
MODE=check

fail() {
  printf 'INTEGRATION_PROOF_RUNTIME_TEST_FAILED: %s\n' "$*" >&2
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

PAIR_TABLE='guru-template/overlay/verify/guru_supervise.py|packages/cli/src/templates/guru/overlay/verify/guru_supervise.py
guru-template/overlay/verify/guru_review_record.py|packages/cli/src/templates/guru/overlay/verify/guru_review_record.py
guru-template/overlay/verify/guru_gate.py|packages/cli/src/templates/guru/overlay/verify/guru_gate.py
guru-template/overlay/verify/tests/test_slice_commit_lifecycle.py|packages/cli/src/templates/guru/overlay/verify/tests/test_slice_commit_lifecycle.py
guru-template/overlay/verify/tests/test_integration_proof_context.py|packages/cli/src/templates/guru/overlay/verify/tests/test_integration_proof_context.py
guru-template/overlay/verify/tests/test_integration_verdict_retry.py|packages/cli/src/templates/guru/overlay/verify/tests/test_integration_verdict_retry.py
guru-template/overlay/tests/integration_proof_runtime_test.sh|packages/cli/src/templates/guru/overlay/tests/integration_proof_runtime_test.sh'

validate_relative_path() {
  local path="$1"

  case "$path" in
    ""|/*|.|..|./*|../*|*/./*|*/../*|*/..|*//*|*'\'*)
      fail "unsafe or non-relative table path: $path"
      ;;
  esac
}

expected_peer_for() {
  local source_rel="$1"

  case "$source_rel" in
    guru-template/*)
      printf 'packages/cli/src/templates/guru/%s\n' \
        "${source_rel#guru-template/}"
      ;;
    *)
      fail "source is outside guru-template: $source_rel"
      ;;
  esac
}

require_parent_within() {
  local path="$1"
  local allowed_root="$2"
  local label="$3"
  local parent_real

  [ -d "$(dirname "$path")" ] || \
    fail "$label parent directory is missing: ${path#$REPO_ROOT/}"
  parent_real="$(cd "$(dirname "$path")" && pwd -P)"
  case "$parent_real" in
    "$allowed_root"|"$allowed_root"/*) ;;
    *) fail "$label parent escapes its managed root: ${path#$REPO_ROOT/}" ;;
  esac
}

reject_deleted_path() {
  local rel="$1"

  git -C "$REPO_ROOT" diff --quiet --diff-filter=D -- "$rel" || \
    fail "declared path is deleted from the worktree: $rel"
  git -C "$REPO_ROOT" diff --cached --quiet --diff-filter=D -- "$rel" || \
    fail "declared path is staged as deleted: $rel"
}

pair_count=0
seen_sources='
'
seen_peers='
'
ordinary_sources='
'

while IFS= read -r pair_line; do
  [ -n "$pair_line" ] || continue
  case "$pair_line" in
    *'|'*'|'*) fail "ambiguous pair has more than one separator: $pair_line" ;;
    *'|'*) ;;
    *) fail "missing peer separator in pair table: $pair_line" ;;
  esac

  source_rel="${pair_line%%|*}"
  peer_rel="${pair_line#*|}"
  [ -n "$source_rel" ] || fail "missing source in pair table: $pair_line"
  [ -n "$peer_rel" ] || fail "missing peer for source: $source_rel"
  validate_relative_path "$source_rel"
  validate_relative_path "$peer_rel"

  case "$source_rel" in
    guru-template/overlay/*) ;;
    *) fail "source is outside the canonical Guru overlay: $source_rel" ;;
  esac
  case "$peer_rel" in
    packages/cli/src/templates/guru/overlay/*) ;;
    *) fail "peer is outside the package Guru overlay: $peer_rel" ;;
  esac

  expected_peer="$(expected_peer_for "$source_rel")"
  [ "$peer_rel" = "$expected_peer" ] || \
    fail "ambiguous or external peer mapping: $source_rel -> $peer_rel"

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
  [ ! -L "$source_path" ] || fail "declared source is a symlink: $source_rel"
  require_parent_within "$source_path" "$GURU_TEMPLATE_DIR" "source"
  require_parent_within "$peer_path" "$PACKAGE_GURU_DIR" "peer"
  reject_deleted_path "$source_rel"
  reject_deleted_path "$peer_rel"

  if [ "$source_rel" != \
    "guru-template/overlay/tests/integration_proof_runtime_test.sh" ]; then
    ordinary_sources="${ordinary_sources}${source_rel}
"
  fi

  if [ -e "$peer_path" ] || [ -L "$peer_path" ]; then
    [ -f "$peer_path" ] || fail "declared peer is not a regular file: $peer_rel"
    [ ! -L "$peer_path" ] || fail "declared peer is a symlink: $peer_rel"
  elif [ "$MODE" != sync ]; then
    fail "declared peer is missing: $peer_rel"
  fi

  if [ "$MODE" = sync ]; then
    cp "$source_path" "$peer_path"
  fi

  cmp -s "$source_path" "$peer_path" || \
    fail "canonical/package bytes differ: $source_rel -> $peer_rel"
done <<< "$PAIR_TABLE"

[ "$pair_count" -eq 7 ] || \
  fail "expected exactly 7 source/peer pairs, found $pair_count"

while IFS= read -r ordinary_rel; do
  [ -n "$ordinary_rel" ] || continue
  git -C "$REPO_ROOT" diff --quiet -- "$ordinary_rel" || \
    fail "Integration rewrote ordinary canonical bytes: $ordinary_rel"
  git -C "$REPO_ROOT" diff --cached --quiet -- "$ordinary_rel" || \
    fail "Integration staged ordinary canonical bytes: $ordinary_rel"
done <<< "$ordinary_sources"

printf 'INTEGRATION_PROOF_RUNTIME_TEST_PASSED: mode=%s pairs=%s\n' \
  "$MODE" "$pair_count"
