#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/guru-install-target.sh <platform> <target> [options]
  bash scripts/guru-install-target.sh --targets [options]
  bash scripts/guru-install-target.sh --target <platform>:<target> [--target <platform>:<target> ...] [options]

Platforms:
  flutter, go, ios, h5

Batch target sources, in priority order:
  --target <platform>:<target>          Repeatable explicit target.
  --targets-file <file>                 TSV file: <platform><whitespace><target>.
  GURU_INSTALL_TARGETS                  Comma, semicolon, or newline separated <platform>:<target> specs.
  .trellis/workspace/<developer>/guru-install-targets.tsv
  .trellis/workspace/guru-install-targets.tsv

Options:
  --targets             Install all resolved targets.
  --target <spec>       Add an explicit batch target, e.g. h5:/path/to/repo.
  --targets-file <file> Read batch targets from a TSV file.
  --skip-source-prepare Skip sync:guru:check and build.
  --no-init             Fail if a target does not already have .trellis/.
  -h, --help            Show this help.
EOF
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

phase() {
  printf '\n== %s ==\n' "$*"
}

info() {
  printf '  %s\n' "$*"
}

print_command() {
  printf '  $'
  printf ' %q' "$@"
  printf '\n'
}

run_in() {
  local cwd="$1"
  shift
  printf '  [%s]\n' "$cwd"
  print_command "$@"
  (cd "$cwd" && "$@")
}

require_command() {
  local name="$1"
  command -v "$name" >/dev/null 2>&1 || die "Missing dependency: $name"
  info "$name: $(command -v "$name")"
}

trim() {
  printf '%s' "$1" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//'
}

platform_template() {
  case "$1" in
    flutter) printf 'guru-flutter-client' ;;
    go) printf 'guru-go-backend' ;;
    ios) printf 'guru-ios-native' ;;
    h5) printf 'guru-h5-web' ;;
    *) return 1 ;;
  esac
}

platform_workflow() {
  case "$1" in
    flutter) printf 'guru-client' ;;
    go) printf 'guru-go' ;;
    ios) printf 'guru-ios' ;;
    h5) printf 'guru-h5' ;;
    *) return 1 ;;
  esac
}

validate_platform() {
  case "$1" in
    flutter | go | ios | h5) return 0 ;;
    *) die "Unsupported platform '$1'. Expected one of: flutter, go, ios, h5" ;;
  esac
}

resolve_script_dir() {
  local source="${BASH_SOURCE[0]}"
  local dir
  while [ -h "$source" ]; do
    dir="$(cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd)"
    source="$(readlink "$source")"
    case "$source" in
      /*) ;;
      *) source="$dir/$source" ;;
    esac
  done
  cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd
}

cleanup_pycache() {
  local scripts_dir="$1/.trellis/scripts"
  if [ -d "$scripts_dir" ]; then
    find "$scripts_dir" -type d -name '__pycache__' -prune -exec rm -rf {} +
  fi
}

compile_guru_scripts() {
  local target="$1"
  local guru_dir="$target/.trellis/scripts/guru"
  local found=0
  local script

  [ -d "$guru_dir" ] || die "Guru script directory missing after apply: $guru_dir"

  while IFS= read -r -d '' script; do
    found=1
    info "py_compile ${script#"$target"/}"
    PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile "$script"
  done < <(find "$guru_dir" -type f -name '*.py' -print0)

  [ "$found" -eq 1 ] || die "No Guru Python scripts found under $guru_dir"
}

prepare_source() {
  phase "Source preparation"
  if [ "$SKIP_SOURCE_PREPARE" -eq 1 ]; then
    info "skipped (--skip-source-prepare)"
  else
    run_in "$REPO_ROOT" pnpm --filter @devsc/trellis run sync:guru:check
    run_in "$REPO_ROOT" pnpm --filter @devsc/trellis run build
  fi
}

install_target() {
  local platform="$1"
  local target_input="$2"
  local target_abs
  local template_id
  local workflow_id
  local user_name
  local check_start_rc
  local bootstrap_task=".trellis/tasks/00-bootstrap-guidelines"

  validate_platform "$platform"
  [ -d "$target_input" ] || die "Target directory not found: $target_input"
  target_abs="$(cd "$target_input" >/dev/null 2>&1 && pwd)"

  TARGET_FOR_CLEANUP="$target_abs"
  trap 'if [ -n "${TARGET_FOR_CLEANUP:-}" ]; then cleanup_pycache "$TARGET_FOR_CLEANUP" || true; fi' EXIT

  phase "Target preflight: $platform $target_abs"
  info "source root: $REPO_ROOT"
  info "target: $target_abs"
  info "platform: $platform"

  phase "Target initialization"
  if [ -d "$target_abs/.trellis" ]; then
    info "target already has .trellis; skipping init"
  elif [ "$ALLOW_INIT" -eq 0 ]; then
    die "Target lacks .trellis and --no-init was set: $target_abs"
  else
    template_id="$(platform_template "$platform")"
    workflow_id="$(platform_workflow "$platform")"
    user_name="${USER:-devSC}"
    [ -n "$user_name" ] || user_name="devSC"
    info "initializing with template=$template_id workflow=$workflow_id user=$user_name"
    run_in "$target_abs" node "$TRELLIS_BIN" init \
      --template "$template_id" \
      --workflow "$workflow_id" \
      --codex \
      --claude \
      --yes \
      --user "$user_name" \
      --no-monorepo
  fi

  phase "Overlay apply"
  run_in "$REPO_ROOT" node "$TRELLIS_BIN" guru apply "$platform" "$target_abs"

  phase "Target smoke checks"
  compile_guru_scripts "$target_abs"

  run_in "$target_abs" python3 .trellis/scripts/get_context.py

  if [ -d "$target_abs/$bootstrap_task" ]; then
    run_in "$target_abs" python3 .trellis/scripts/guru/guru_gate.py status "$bootstrap_task"

    printf '  [%s]\n' "$target_abs"
    print_command python3 .trellis/scripts/guru/guru_gate.py check-start "$bootstrap_task"
    set +e
    (cd "$target_abs" && python3 .trellis/scripts/guru/guru_gate.py check-start "$bootstrap_task")
    check_start_rc=$?
    set -e
    case "$check_start_rc" in
      0)
        info "bootstrap check-start passed"
        ;;
      2)
        info "bootstrap check-start blocked with rc=2; advisory only"
        ;;
      *)
        die "bootstrap check-start failed with unexpected rc=$check_start_rc"
        ;;
    esac
  else
    info "no bootstrap task at $bootstrap_task; skipping bootstrap gate smoke"
  fi

  phase "Cleanup"
  cleanup_pycache "$target_abs"
  info "removed any __pycache__ directories under target .trellis/scripts"

  phase "Done: $platform $target_abs"
  info "Guru overlay install wrapper completed"

  TARGET_FOR_CLEANUP=""
  trap - EXIT
}

add_batch_target() {
  local platform="$1"
  local target="$2"

  platform="$(trim "$platform")"
  target="$(trim "$target")"
  [ -n "$platform" ] || die "Batch target is missing platform"
  [ -n "$target" ] || die "Batch target is missing path for platform '$platform'"
  validate_platform "$platform"
  [ -d "$target" ] || die "Target directory not found: $target"

  BATCH_PLATFORMS+=("$platform")
  BATCH_TARGETS+=("$target")
}

add_batch_target_spec() {
  local spec="$1"
  local platform
  local target

  spec="$(trim "$spec")"
  [ -n "$spec" ] || return 0
  case "$spec" in
    *:*)
      platform="${spec%%:*}"
      target="${spec#*:}"
      ;;
    *)
      die "Malformed target spec '$spec'. Expected <platform>:<target>"
      ;;
  esac
  add_batch_target "$platform" "$target"
}

resolve_file_path() {
  local input="$1"
  local abs_dir

  case "$input" in
    /*) printf '%s' "$input" ;;
    *)
      if [ -f "$input" ]; then
        abs_dir="$(cd -P "$(dirname "$input")" >/dev/null 2>&1 && pwd)"
        printf '%s/%s' "$abs_dir" "$(basename "$input")"
      elif [ -f "$REPO_ROOT/$input" ]; then
        printf '%s/%s' "$REPO_ROOT" "$input"
      else
        printf '%s' "$input"
      fi
      ;;
  esac
}

load_targets_file() {
  local file_input="$1"
  local file_path
  local line
  local cleaned
  local platform
  local target

  file_path="$(resolve_file_path "$file_input")"
  [ -f "$file_path" ] || die "Targets file not found: $file_input"
  info "targets file: $file_path"

  while IFS= read -r line || [ -n "$line" ]; do
    cleaned="$(trim "${line%%#*}")"
    [ -n "$cleaned" ] || continue
    [[ "$cleaned" == *[[:space:]]* ]] || die "Malformed targets file row '$cleaned'. Expected <platform><whitespace><target>"
    platform="${cleaned%%[[:space:]]*}"
    target="$(trim "${cleaned#"$platform"}")"
    add_batch_target "$platform" "$target"
  done < "$file_path"
}

load_env_targets() {
  local normalized
  local spec

  [ -n "${GURU_INSTALL_TARGETS:-}" ] || return 1
  normalized="${GURU_INSTALL_TARGETS//$'\n'/,}"
  normalized="${normalized//;/,}"
  IFS=',' read -r -a ENV_TARGET_SPECS <<<"$normalized"
  for spec in "${ENV_TARGET_SPECS[@]}"; do
    add_batch_target_spec "$spec"
  done
  return 0
}

default_targets_file() {
  local developer="${USER:-devSC}"
  local dev_file
  local shared_file

  [ -n "$developer" ] || developer="devSC"
  dev_file="$REPO_ROOT/.trellis/workspace/$developer/guru-install-targets.tsv"
  shared_file="$REPO_ROOT/.trellis/workspace/guru-install-targets.tsv"

  if [ -f "$dev_file" ]; then
    printf '%s' "$dev_file"
  elif [ -f "$shared_file" ]; then
    printf '%s' "$shared_file"
  else
    return 1
  fi
}

resolve_batch_targets() {
  local spec
  local file_path

  if [ "${#TARGET_SPECS[@]}" -gt 0 ]; then
    for spec in "${TARGET_SPECS[@]}"; do
      add_batch_target_spec "$spec"
    done
  elif [ -n "$TARGETS_FILE" ]; then
    load_targets_file "$TARGETS_FILE"
  elif load_env_targets; then
    :
  elif file_path="$(default_targets_file)"; then
    load_targets_file "$file_path"
  else
    die "No batch targets configured. Use --target <platform>:<path>, --targets-file <file>, GURU_INSTALL_TARGETS, or .trellis/workspace/<developer>/guru-install-targets.tsv"
  fi

  [ "${#BATCH_TARGETS[@]}" -gt 0 ] || die "No batch targets resolved"
}

run_batch() {
  local index
  local platform
  local target
  local rc
  local succeeded=()
  local failed=()
  local succeeded_count=0
  local failed_count=0

  phase "Batch target resolution"
  resolve_batch_targets
  info "resolved targets: ${#BATCH_TARGETS[@]}"
  for index in "${!BATCH_TARGETS[@]}"; do
    info "$((index + 1)). ${BATCH_PLATFORMS[$index]} ${BATCH_TARGETS[$index]}"
  done

  prepare_source

  for index in "${!BATCH_TARGETS[@]}"; do
    platform="${BATCH_PLATFORMS[$index]}"
    target="${BATCH_TARGETS[$index]}"
    phase "Batch target $((index + 1))/${#BATCH_TARGETS[@]}: $platform $target"
    set +e
    (set -e; install_target "$platform" "$target")
    rc=$?
    set -e
    if [ "$rc" -eq 0 ]; then
      succeeded+=("$platform $target")
      succeeded_count=$((succeeded_count + 1))
    else
      failed+=("$platform $target rc=$rc")
      failed_count=$((failed_count + 1))
    fi
  done

  phase "Batch summary"
  info "succeeded: $succeeded_count"
  if [ "$succeeded_count" -gt 0 ]; then
    for target in "${succeeded[@]}"; do
      info "PASS $target"
    done
  fi
  info "failed: $failed_count"
  if [ "$failed_count" -gt 0 ]; then
    for target in "${failed[@]}"; do
      info "FAIL $target"
    done
  fi

  [ "$failed_count" -eq 0 ] || return 1
}

SKIP_SOURCE_PREPARE=0
ALLOW_INIT=1
BATCH_MODE=0
TARGETS_FILE=""
POSITIONAL=()
TARGET_SPECS=()
BATCH_PLATFORMS=()
BATCH_TARGETS=()
ENV_TARGET_SPECS=()
TARGET_FOR_CLEANUP=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --)
      if [ "${#POSITIONAL[@]}" -eq 0 ]; then
        shift
        continue
      fi
      shift
      while [ "$#" -gt 0 ]; do
        POSITIONAL+=("$1")
        shift
      done
      break
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    --targets)
      BATCH_MODE=1
      ;;
    --target)
      [ "$#" -ge 2 ] || die "--target requires <platform>:<target>"
      BATCH_MODE=1
      TARGET_SPECS+=("$2")
      shift
      ;;
    --targets-file)
      [ "$#" -ge 2 ] || die "--targets-file requires a file path"
      BATCH_MODE=1
      TARGETS_FILE="$2"
      shift
      ;;
    --skip-source-prepare)
      SKIP_SOURCE_PREPARE=1
      ;;
    --no-init)
      ALLOW_INIT=0
      ;;
    --*)
      die "Unknown option: $1"
      ;;
    *)
      POSITIONAL+=("$1")
      ;;
  esac
  shift
done

SCRIPT_DIR="$(resolve_script_dir)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." >/dev/null 2>&1 && pwd)"
TRELLIS_BIN="$REPO_ROOT/packages/cli/bin/trellis.js"

[ -f "$TRELLIS_BIN" ] || die "Local Trellis CLI entrypoint not found: $TRELLIS_BIN"

phase "Preflight"
info "source root: $REPO_ROOT"
require_command pnpm
require_command node
require_command python3

if [ "$BATCH_MODE" -eq 1 ]; then
  [ "${#POSITIONAL[@]}" -eq 0 ] || die "Batch mode does not accept positional <platform> <target> arguments"
  run_batch
else
  if [ "${#POSITIONAL[@]}" -ne 2 ]; then
    usage >&2
    exit 1
  fi
  PLATFORM="${POSITIONAL[0]}"
  TARGET_INPUT="${POSITIONAL[1]}"
  validate_platform "$PLATFORM"
  [ -d "$TARGET_INPUT" ] || die "Target directory not found: $TARGET_INPUT"
  prepare_source
  install_target "$PLATFORM" "$TARGET_INPUT"
fi
