#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OVERLAY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$OVERLAY_DIR/../.." && pwd)"
REINSTALL="$OVERLAY_DIR/reinstall-official-067.sh"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/guru-reinstall-067-test.XXXXXX")"
TARGET="$TMP_ROOT/target"
TEST_HOME="$TMP_ROOT/home"
NPM_CACHE="$TMP_ROOT/npm-cache"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT INT TERM

fail() {
  printf 'REINSTALL_067_TEST_FAILED: %s\n' "$*" >&2
  exit 1
}

tree_digest() {
  python3 - "$1" <<'PY'
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

root = Path(sys.argv[1])
rows = []
for directory, dir_names, file_names in os.walk(root, topdown=True, followlinks=False):
    directory_path = Path(directory)
    if directory_path == root:
        dir_names[:] = [name for name in dir_names if name != ".git"]
    dir_names.sort()
    file_names.sort()
    for name in dir_names + file_names:
        path = directory_path / name
        info = path.lstat()
        relative = path.relative_to(root).as_posix()
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISLNK(info.st_mode):
            rows.append((relative, "symlink", mode, os.readlink(path)))
        elif stat.S_ISDIR(info.st_mode):
            rows.append((relative, "directory", mode))
        elif stat.S_ISREG(info.st_mode):
            rows.append((relative, "file", mode, hashlib.sha256(path.read_bytes()).hexdigest()))
        else:
            raise SystemExit(f"unsupported test path: {path}")
print(hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest())
PY
}

run_reinstall() {
  HOME="$TEST_HOME" npm_config_cache="$NPM_CACHE" bash "$REINSTALL" "$@"
}

git_index_digest() {
  GIT_OPTIONAL_LOCKS=0 git -C "$1" ls-files --stage -z | shasum -a 256 | awk '{print $1}'
}

mkdir -p "$TARGET" "$TEST_HOME/.codex/skills/global-sentinel" "$NPM_CACHE"
printf 'global-user-skill\n' > "$TEST_HOME/.codex/skills/global-sentinel/SKILL.md"

git -C "$TARGET" init -q
git -C "$TARGET" config user.name reinstall-test
git -C "$TARGET" config user.email reinstall-test@example.invalid

(
  cd "$TARGET"
  HOME="$TEST_HOME" npm_config_cache="$NPM_CACHE" \
    npx -y @mindfoldhq/trellis@0.6.7 init -y --codex --user reinstall-test
)

GURU_ADVERSARIAL_ENABLED=false bash "$OVERLAY_DIR/apply.sh" "$TARGET" flutter \
  --rollback-bundle "$TMP_ROOT/initial-overlay-rollback"

mkdir -p \
  "$TARGET/.trellis/tasks/07-15-project-history" \
  "$TARGET/.trellis/workspace/reinstall-test" \
  "$TARGET/.trellis/spec/flutter" \
  "$TARGET/.trellis/spec/conventions" \
  "$TARGET/.agents/skills/project-local" \
  "$TARGET/.claude/skills/project-local" \
  "$TARGET/.codex/skills/codex-project-local" \
  "$TARGET/.trellis/.runtime/sessions"

cat > "$TARGET/.trellis/tasks/07-15-project-history/task.json" <<'JSON'
{"name":"07-15-project-history","status":"in_progress","title":"Preserved history"}
JSON
printf '# Preserved task PRD\n' > "$TARGET/.trellis/tasks/07-15-project-history/prd.md"
printf '# Preserved workspace journal\n' > "$TARGET/.trellis/workspace/reinstall-test/journal-1.md"
printf '# Project-only Flutter rule\n' > "$TARGET/.trellis/spec/flutter/project-only.md"
printf '# Project conventions\n\nproject: reinstall-fixture\n' \
  > "$TARGET/.trellis/spec/conventions/project-conventions.md"
printf '%s\n' '---' 'name: project-local' '---' '# Project local skill' \
  > "$TARGET/.agents/skills/project-local/SKILL.md"
cp -R "$TARGET/.agents/skills/project-local/." "$TARGET/.claude/skills/project-local/"
printf '%s\n' '---' 'name: codex-project-local' '---' '# Codex project local skill' \
  > "$TARGET/.codex/skills/codex-project-local/SKILL.md"
printf '{"task":"stale-pointer"}\n' > "$TARGET/.trellis/.runtime/sessions/stale.json"
printf '# obsolete Guru runtime\n' > "$TARGET/.trellis/scripts/guru/obsolete-guru-runtime.py"
cat >> "$TARGET/AGENTS.md" <<'EOF'

<!-- project-rules:start -->
# Project-owned agent rules
<!-- project-rules:end -->
EOF

git -C "$TARGET" add -A
git -C "$TARGET" -c core.hooksPath=/dev/null commit -qm 'fixture: old local guru install'

ORIGINAL_DIGEST="$(tree_digest "$TARGET")"
TASKS_DIGEST="$(tree_digest "$TARGET/.trellis/tasks")"
WORKSPACE_DIGEST="$(tree_digest "$TARGET/.trellis/workspace")"
INDEX_DIGEST="$(git_index_digest "$TARGET")"

run_reinstall --dry-run --backup-dir "$TMP_ROOT/dry-run-backup" "$TARGET"
[ ! -e "$TMP_ROOT/dry-run-backup" ] || fail "dry-run created the requested backup directory"
[ "$(tree_digest "$TARGET")" = "$ORIGINAL_DIGEST" ] || fail "dry-run changed the target"
[ "$(git_index_digest "$TARGET")" = "$INDEX_DIGEST" ] || \
  fail "dry-run changed the Git index"

set +e
GURU_REINSTALL_TEST_FAIL_AT=after-uninstall run_reinstall \
  --keep-backup --backup-dir "$TMP_ROOT/failure-backup" "$TARGET"
failure_rc=$?
set -e
[ "$failure_rc" -eq 1 ] || fail "forced failure returned $failure_rc instead of 1"
[ "$(tree_digest "$TARGET")" = "$ORIGINAL_DIGEST" ] || fail "forced failure did not restore target digest"
[ -f "$TMP_ROOT/failure-backup/rollback-report.json" ] || fail "rollback report missing"

set +e
GURU_REINSTALL_TEST_FAIL_AT=after-overlay run_reinstall \
  --keep-backup --backup-dir "$TMP_ROOT/overlay-failure-backup" "$TARGET"
overlay_failure_rc=$?
set -e
[ "$overlay_failure_rc" -eq 1 ] || fail "forced overlay failure returned $overlay_failure_rc instead of 1"
[ "$(tree_digest "$TARGET")" = "$ORIGINAL_DIGEST" ] || \
  fail "forced overlay failure did not restore target digest"
[ -f "$TMP_ROOT/overlay-failure-backup/rollback-report.json" ] || \
  fail "overlay failure rollback report missing"

run_reinstall --keep-backup --backup-dir "$TMP_ROOT/success-backup" "$TARGET"

[ "$(tree_digest "$TARGET/.trellis/tasks")" = "$TASKS_DIGEST" ] || fail "tasks were not byte-preserved"
[ "$(tree_digest "$TARGET/.trellis/workspace")" = "$WORKSPACE_DIGEST" ] || fail "workspace was not byte-preserved"
[ ! -e "$TARGET/.trellis/.runtime/sessions/stale.json" ] || fail "stale runtime pointer was restored"
[ ! -e "$TARGET/.trellis/scripts/guru/obsolete-guru-runtime.py" ] || fail "obsolete Guru runtime survived"
grep -q '<!-- project-rules:start -->' "$TARGET/AGENTS.md" || \
  fail "project-owned AGENTS.md content was not preserved"
[ -f "$TARGET/.trellis/spec/flutter/project-only.md" ] || fail "project-only Spec was not restored"
grep -q 'project: reinstall-fixture' "$TARGET/.trellis/spec/conventions/project-conventions.md" || \
  fail "project conventions were not restored"
[ -f "$TARGET/.agents/skills/project-local/SKILL.md" ] || fail ".agents project Skill missing"
[ -f "$TARGET/.claude/skills/project-local/SKILL.md" ] || fail ".claude project Skill missing"
[ -f "$TARGET/.codex/skills/codex-project-local/SKILL.md" ] || fail ".codex project Skill missing"
diff -rq -x .DS_Store -x __pycache__ "$TARGET/.agents/skills" "$TARGET/.claude/skills" >/dev/null || \
  fail ".agents and .claude Skill roots differ"
grep -q '^    provider: codex$' "$TARGET/.trellis/config.yaml" || fail "Codex provider missing"
grep -q '^    high_risk_review_provider_policy: codex$' "$TARGET/.trellis/config.yaml" || \
  fail "Codex high-risk review policy missing"
grep -q '^    adversarial_enabled: false$' "$TARGET/.trellis/config.yaml" || fail "adversarial disable missing"
[ "$(cat "$TARGET/.trellis/.version")" = '0.6.7' ] || fail "official target version is not 0.6.7"
[ "$(cat "$TEST_HOME/.codex/skills/global-sentinel/SKILL.md")" = 'global-user-skill' ] || \
  fail "global user Skill was changed"
[ "$(git_index_digest "$TARGET")" = "$INDEX_DIGEST" ] || \
  fail "Git index changed during successful reinstall"
python3 - "$TMP_ROOT/success-backup/reinstall-result.json" <<'PY'
import json
import sys

result = json.load(open(sys.argv[1], encoding="utf-8"))
assert result["rollback_mode"] == "external-managed-snapshot-v1", result
assert "AGENTS.md" in result["root_documents_restored"], result
PY

python3 - "$TMP_ROOT/success-backup/spec-reconcile-report.json" \
  "$TMP_ROOT/success-backup/skill-reconcile-report.json" <<'PY'
import json
import sys

spec = json.load(open(sys.argv[1], encoding="utf-8"))
skills = json.load(open(sys.argv[2], encoding="utf-8"))
assert not spec["conflicts"], spec
assert not skills["conflicts"], skills
assert spec["project_conventions_restored"] is True
assert ".agents/skills/project-local" in skills["project_restored"] or \
    ".agents/skills/project-local" in skills["identical"]
assert skills["global_roots_touched"] is False
PY

printf '# intentionally old same-path Spec\n' > "$TARGET/.trellis/spec/guides/golden-path.md"
mkdir -p \
  "$TARGET/.agents/skills/project-mirror-conflict" \
  "$TARGET/.claude/skills/project-mirror-conflict"
printf '# agents project winner\n' \
  > "$TARGET/.agents/skills/project-mirror-conflict/SKILL.md"
printf '# claude project conflict\n' \
  > "$TARGET/.claude/skills/project-mirror-conflict/SKILL.md"
set +e
run_reinstall --backup-dir "$TMP_ROOT/conflict-backup" "$TARGET"
conflict_rc=$?
set -e
[ "$conflict_rc" -eq 3 ] || fail "Spec conflict returned $conflict_rc instead of 3"
cmp -s \
  "$REPO_ROOT/guru-template/specs/guru-flutter-client/guides/golden-path.md" \
  "$TARGET/.trellis/spec/guides/golden-path.md" || fail "new managed Spec did not win conflict"
python3 - \
  "$TMP_ROOT/conflict-backup/spec-reconcile-report.json" \
  "$TMP_ROOT/conflict-backup/skill-reconcile-report.json" <<'PY'
import json
import sys

spec = json.load(open(sys.argv[1], encoding="utf-8"))
skills = json.load(open(sys.argv[2], encoding="utf-8"))
assert any(row["path"] == "guides/golden-path.md" for row in spec["conflicts"]), spec
assert any(
    row["path"] == ".agents/.claude mirror/project-mirror-conflict"
    for row in skills["conflicts"]
), skills
PY
[ -f "$TMP_ROOT/conflict-backup/conflicts/spec/old/guides/golden-path.md" ] || \
  fail "old Spec conflict copy missing"
[ -f "$TMP_ROOT/conflict-backup/conflicts/spec/new/guides/golden-path.md" ] || \
  fail "new Spec conflict copy missing"
[ "$(cat "$TARGET/.agents/skills/project-mirror-conflict/SKILL.md")" = '# agents project winner' ] || \
  fail ".agents project Skill did not win mirror conflict"
cmp -s \
  "$TARGET/.agents/skills/project-mirror-conflict/SKILL.md" \
  "$TARGET/.claude/skills/project-mirror-conflict/SKILL.md" || \
  fail "Skill mirror conflict did not reconcile both target roots"
[ -f "$TMP_ROOT/conflict-backup/conflicts/skills/preexisting-mirror/old/project-mirror-conflict/SKILL.md" ] || \
  fail "old Skill conflict copy missing"
[ -f "$TMP_ROOT/conflict-backup/conflicts/skills/preexisting-mirror/new/project-mirror-conflict/SKILL.md" ] || \
  fail "new Skill conflict copy missing"

printf 'REINSTALL_067_TEST_OK official=0.6.7 dry_run=pass rollback=pass success=pass spec_conflict=pass skill_conflict=pass\n'
