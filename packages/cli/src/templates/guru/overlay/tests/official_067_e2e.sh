#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OVERLAY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
GURU_TEMPLATE_DIR="$(cd "$OVERLAY_DIR/.." && pwd)"
REPO_ROOT="$(cd "$GURU_TEMPLATE_DIR/.." && pwd)"
CATALOG_PY="$OVERLAY_DIR/verify/guru_catalog.py"
FIXTURE_PY="$SCRIPT_DIR/https_git_fixture.py"
OFFICIAL_PACKAGE='@mindfoldhq/trellis'
OFFICIAL_VERSION='0.6.7'
OFFICIAL_E2E_TMP=''

fail() {
  printf 'OFFICIAL_067_E2E_FAILED: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command is unavailable: $1"
}

verify_official_package() {
  local prefix="$1"
  local package_json="$prefix/node_modules/@mindfoldhq/trellis/package.json"
  local binary="$prefix/node_modules/.bin/trellis"
  test -f "$package_json" || fail "official package.json is missing"
  test -x "$binary" || fail "official trellis binary is missing"
  node - "$package_json" "$OFFICIAL_PACKAGE" "$OFFICIAL_VERSION" <<'NODE'
const fs = require("node:fs");
const [packageJson, expectedName, expectedVersion] = process.argv.slice(2);
const parsed = JSON.parse(fs.readFileSync(packageJson, "utf8"));
if (parsed.name !== expectedName || parsed.version !== expectedVersion) {
  throw new Error(`package mismatch: ${parsed.name}@${parsed.version}`);
}
NODE
  local binary_real
  local package_real
  binary_real="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$binary")"
  package_real="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$prefix/node_modules/@mindfoldhq/trellis")"
  case "$binary_real" in
    "$package_real"/*) ;;
    *) fail "binary realpath does not belong to exact official package: $binary_real" ;;
  esac
  printf 'OFFICIAL_PACKAGE_OK name=%s version=%s binary=%s\n' \
    "$OFFICIAL_PACKAGE" "$OFFICIAL_VERSION" "$binary_real"
}

verify_registry_config() {
  local prefix="$1"
  local stage="$2"
  local expected_source="$3"
  local expected_template="$4"
  local module="$prefix/node_modules/@mindfoldhq/trellis/dist/utils/registry-config.js"
  node --input-type=module - "$module" "$stage" "$expected_source" "$expected_template" <<'NODE'
import { pathToFileURL } from "node:url";
const [modulePath, stage, expectedSource, expectedTemplate] = process.argv.slice(2);
const { loadSpecRegistryConfig } = await import(pathToFileURL(modulePath).href);
const actual = loadSpecRegistryConfig(stage);
if (actual?.source !== expectedSource || actual?.template !== expectedTemplate) {
  throw new Error(`registry.spec mismatch: ${JSON.stringify(actual)}`);
}
NODE
}

verify_non_native_hash_boundary() {
  local stage="$1"
  node - "$stage/.trellis/.template-hashes.json" <<'NODE'
const fs = require("node:fs");
const manifest = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
if (manifest.__version !== 2 || typeof manifest.hashes !== "object" || manifest.hashes === null) {
  throw new Error("template hash manifest schema mismatch");
}
if (Object.prototype.hasOwnProperty.call(manifest.hashes, ".trellis/workflow.md")) {
  throw new Error("non-native workflow is incorrectly Trellis hash-owned");
}
NODE
}

run_stack() {
  local binary="$1"
  local prefix="$2"
  local stage_parent="$3"
  local spec_id="$4"
  local workflow_id="$5"
  local workflow_file="$6"
  local stage="$stage_parent/$workflow_id"
  local stdout_file="$stage_parent/$workflow_id.stdout"
  local stderr_file="$stage_parent/$workflow_id.stderr"

  rm -rf "$stage"
  mkdir -p "$stage"
  set +e
  (
    cd "$stage"
    PATH="${GURU_OFFICIAL_PATH:?}" "$binary" init -y --codex \
      --registry "$GURU_HTTPS_SOURCE" \
      --template "$spec_id" \
      --workflow-source "$GURU_HTTPS_SOURCE" \
      --workflow "$workflow_id"
  ) >"$stdout_file" 2>"$stderr_file"
  local raw_rc=$?
  set -e

  local observation
  if ! observation="$(python3 "$CATALOG_PY" observe-official \
    --returncode "$raw_rc" \
    --stdout-file "$stdout_file" \
    --stderr-file "$stderr_file" \
    --stage-root "$stage")"; then
    printf '%s\n' "${observation:-NO_OBSERVATION_OUTPUT}" >&2
    printf '%s\n' '--- official stdout ---' >&2
    sed -n '1,240p' "$stdout_file" >&2
    printf '%s\n' '--- official stderr ---' >&2
    sed -n '1,240p' "$stderr_file" >&2
    fail "$workflow_id raw official result was rejected"
  fi
  test "$raw_rc" -eq 0 || fail "$workflow_id official init returned $raw_rc"
  if grep -Eqi 'falling back to blank templates|bundled guru' "$stdout_file" "$stderr_file"; then
    fail "$workflow_id observed an official fallback"
  fi
  python3 "$CATALOG_PY" compare-tree \
    "$GURU_TEMPLATE_DIR/specs/$spec_id" \
    "$stage/.trellis/spec" >/dev/null || fail "$spec_id installed spec tree differs from candidate"
  cmp -s "$GURU_TEMPLATE_DIR/workflows/$workflow_file" "$stage/.trellis/workflow.md" || \
    fail "$workflow_id installed workflow bytes differ from candidate"
  verify_registry_config "$prefix" "$stage" "$GURU_HTTPS_SOURCE" "$spec_id"
  verify_non_native_hash_boundary "$stage"
  printf 'OFFICIAL_STACK_OK spec=%s workflow=%s\n' "$spec_id" "$workflow_id"
}

run_blank_fallback_observation() {
  local binary="$1"
  local stage_parent="$2"
  local stage="$stage_parent/raw-blank-fallback"
  local stdout_file="$stage_parent/raw-blank-fallback.stdout"
  local stderr_file="$stage_parent/raw-blank-fallback.stderr"

  rm -rf "$stage"
  mkdir -p "$stage"
  set +e
  (
    cd "$stage"
    PATH="${GURU_OFFICIAL_PATH:?}" "$binary" init -y --codex \
      --registry "$GURU_HTTPS_SOURCE" \
      --template __missing_guru_template__
  ) >"$stdout_file" 2>"$stderr_file"
  local raw_rc=$?
  set -e

  grep -Eqi 'falling back to blank templates' "$stdout_file" "$stderr_file" || \
    fail "exact official negative fixture did not expose the expected raw blank fallback"
  if python3 "$CATALOG_PY" observe-official \
    --returncode "$raw_rc" \
    --stdout-file "$stdout_file" \
    --stderr-file "$stderr_file" \
    --stage-root "$stage" >/dev/null 2>&1; then
    fail "raw official blank fallback was normalized to success"
  fi
  printf 'OFFICIAL_RAW_FALLBACK_REJECTED raw_rc=%s\n' "$raw_rc"
}

inside_fixture() {
  local binary="$1"
  local prefix="$2"
  local stage_parent="$3"
  test -n "${GURU_HTTPS_SOURCE:-}" || fail "fixture source environment is missing"
  test -n "${GURU_FIXTURE_COMMIT:-}" || fail "fixture commit environment is missing"
  test -n "${GURU_OFFICIAL_PATH:-}" || fail "sanitized official PATH is missing"
  test "$GURU_FIXTURE_CANDIDATE_DIGEST" = "$GURU_FIXTURE_RECLONED_DIGEST" || \
    fail "candidate and recloned source digests differ"
  mkdir -p "$stage_parent"
  run_stack "$binary" "$prefix" "$stage_parent" \
    guru-flutter-client guru-client guru-client-workflow.md
  run_stack "$binary" "$prefix" "$stage_parent" \
    guru-go-backend guru-go guru-go-workflow.md
  run_stack "$binary" "$prefix" "$stage_parent" \
    guru-h5-web guru-h5 guru-h5-workflow.md
  run_stack "$binary" "$prefix" "$stage_parent" \
    guru-ios-native guru-ios guru-ios-workflow.md
  run_blank_fallback_observation "$binary" "$stage_parent"
  printf 'OFFICIAL_067_CATALOG_OK commit=%s tag=%s\n' \
    "$GURU_FIXTURE_COMMIT" "$GURU_FIXTURE_TAG"
}

main() {
  case "${1:-}" in
    --catalog)
      require_command git
      require_command node
      require_command npm
      require_command openssl
      require_command python3
      OFFICIAL_E2E_TMP="$(mktemp -d "${TMPDIR:-/tmp}/guru-official-067.XXXXXX")"
      trap 'rm -rf "${OFFICIAL_E2E_TMP:?}"' EXIT INT TERM
      local prefix="$OFFICIAL_E2E_TMP/npm-prefix"
      local stage_parent="$OFFICIAL_E2E_TMP/stages"
      npm install --prefix "$prefix" --ignore-scripts --no-audit --no-fund --silent \
        "$OFFICIAL_PACKAGE@$OFFICIAL_VERSION"
      verify_official_package "$prefix"
      local binary="$prefix/node_modules/.bin/trellis"
      local system_path
      system_path="$(python3 - "$REPO_ROOT" "${PATH:-}" <<'PY'
import os
import sys

repo_root = os.path.realpath(sys.argv[1])
safe = []
for entry in sys.argv[2].split(os.pathsep):
    if not entry:
        continue
    real_entry = os.path.realpath(entry)
    try:
        inside_repo = os.path.commonpath((repo_root, real_entry)) == repo_root
    except ValueError:
        inside_repo = False
    if not inside_repo:
        safe.append(entry)
print(os.pathsep.join(safe))
PY
)"
      export GURU_OFFICIAL_PATH="$prefix/node_modules/.bin:$system_path"
      python3 "$FIXTURE_PY" run \
        --source-root "$GURU_TEMPLATE_DIR" \
        -- bash "$BASH_SOURCE" --inside-fixture "$binary" "$prefix" "$stage_parent"
      ;;
    --inside-fixture)
      shift
      test "$#" -eq 3 || fail "inside-fixture requires binary, prefix, and stage root"
      inside_fixture "$1" "$2" "$3"
      ;;
    *)
      fail "usage: $0 --catalog"
      ;;
  esac
}

main "$@"
