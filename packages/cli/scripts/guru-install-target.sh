#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/guru-install-target.sh <platform> <target> [options]

Platforms:
  flutter, go, ios, h5

Options:
  --skip-source-prepare  Skip sync:guru:check and build.
  --no-init              Fail if the target does not already have .trellis/.
  -h, --help             Show this help.
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

SKIP_SOURCE_PREPARE=0
ALLOW_INIT=1
POSITIONAL=()

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

if [ "${#POSITIONAL[@]}" -ne 2 ]; then
  usage >&2
  exit 1
fi

PLATFORM="${POSITIONAL[0]}"
TARGET_INPUT="${POSITIONAL[1]}"
validate_platform "$PLATFORM"

SCRIPT_DIR="$(resolve_script_dir)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." >/dev/null 2>&1 && pwd)"
TRELLIS_BIN="$REPO_ROOT/packages/cli/bin/trellis.js"

[ -d "$TARGET_INPUT" ] || die "Target directory not found: $TARGET_INPUT"
TARGET_ABS="$(cd "$TARGET_INPUT" >/dev/null 2>&1 && pwd)"
[ -f "$TRELLIS_BIN" ] || die "Local Trellis CLI entrypoint not found: $TRELLIS_BIN"

CLEANUP_ON_EXIT=0
cleanup_on_exit() {
  local rc=$?
  if [ "$rc" -ne 0 ] && [ "$CLEANUP_ON_EXIT" -eq 1 ]; then
    cleanup_pycache "$TARGET_ABS" || true
  fi
}
trap cleanup_on_exit EXIT

phase "Preflight"
info "source root: $REPO_ROOT"
info "target: $TARGET_ABS"
info "platform: $PLATFORM"
require_command pnpm
require_command node
require_command python3

phase "Source preparation"
if [ "$SKIP_SOURCE_PREPARE" -eq 1 ]; then
  info "skipped (--skip-source-prepare)"
else
  run_in "$REPO_ROOT" pnpm --filter @devsc/trellis run sync:guru:check
  run_in "$REPO_ROOT" pnpm --filter @devsc/trellis run build
fi

phase "Target initialization"
if [ -d "$TARGET_ABS/.trellis" ]; then
  info "target already has .trellis; skipping init"
elif [ "$ALLOW_INIT" -eq 0 ]; then
  die "Target lacks .trellis and --no-init was set: $TARGET_ABS"
else
  TEMPLATE_ID="$(platform_template "$PLATFORM")"
  WORKFLOW_ID="$(platform_workflow "$PLATFORM")"
  USER_NAME="${USER:-devSC}"
  [ -n "$USER_NAME" ] || USER_NAME="devSC"
  info "initializing with template=$TEMPLATE_ID workflow=$WORKFLOW_ID user=$USER_NAME"
  run_in "$TARGET_ABS" node "$TRELLIS_BIN" init \
    --template "$TEMPLATE_ID" \
    --workflow "$WORKFLOW_ID" \
    --codex \
    --claude \
    --yes \
    --user "$USER_NAME" \
    --no-monorepo
fi

phase "Overlay apply"
run_in "$REPO_ROOT" node "$TRELLIS_BIN" guru apply "$PLATFORM" "$TARGET_ABS"

phase "Target smoke checks"
CLEANUP_ON_EXIT=1
compile_guru_scripts "$TARGET_ABS"

run_in "$TARGET_ABS" python3 .trellis/scripts/get_context.py

BOOTSTRAP_TASK=".trellis/tasks/00-bootstrap-guidelines"
if [ -d "$TARGET_ABS/$BOOTSTRAP_TASK" ]; then
  run_in "$TARGET_ABS" python3 .trellis/scripts/guru/guru_gate.py status "$BOOTSTRAP_TASK"

  printf '  [%s]\n' "$TARGET_ABS"
  print_command python3 .trellis/scripts/guru/guru_gate.py check-start "$BOOTSTRAP_TASK"
  set +e
  (cd "$TARGET_ABS" && python3 .trellis/scripts/guru/guru_gate.py check-start "$BOOTSTRAP_TASK")
  CHECK_START_RC=$?
  set -e
  case "$CHECK_START_RC" in
    0)
      info "bootstrap check-start passed"
      ;;
    2)
      info "bootstrap check-start blocked with rc=2; advisory only"
      ;;
    *)
      die "bootstrap check-start failed with unexpected rc=$CHECK_START_RC"
      ;;
  esac
else
  info "no bootstrap task at $BOOTSTRAP_TASK; skipping bootstrap gate smoke"
fi

phase "Cleanup"
cleanup_pycache "$TARGET_ABS"
CLEANUP_ON_EXIT=0
info "removed any __pycache__ directories under target .trellis/scripts"

phase "Done"
info "Guru overlay install wrapper completed"
