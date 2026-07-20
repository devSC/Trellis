#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OVERLAY_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_ROOT="$(cd "$OVERLAY_DIR/.." && pwd)"
REINSTALL="$OVERLAY_DIR/reinstall-official-067.sh"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/guru-reinstall-067-test.XXXXXX")"
TARGET="$TMP_ROOT/target "
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
  run_reinstall_with "$REINSTALL" "$@"
}

run_reinstall_with() {
  local script="$1"
  shift
  HOME="$TEST_HOME" npm_config_cache="$NPM_CACHE" bash "$script" "$@"
}

git_index_digest() {
  GIT_OPTIONAL_LOCKS=0 python3 - "$1" <<'PY'
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import sys

result = subprocess.run(
    [
        "git",
        "-C",
        sys.argv[1],
        "rev-parse",
        "--git-path",
        "index",
    ],
    capture_output=True,
    check=True,
    env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
)
assert result.stdout.endswith(b"\n")
raw_path = result.stdout[:-1]
assert raw_path and b"\0" not in raw_path
if not os.path.isabs(raw_path):
    raw_path = os.path.abspath(os.path.join(os.fsencode(sys.argv[1]), raw_path))
decoded_path = os.fsdecode(raw_path)
assert os.fsencode(decoded_path) == raw_path
assert Path(decoded_path).is_absolute()
try:
    info = os.lstat(raw_path)
except FileNotFoundError:
    state = b"missing"
    raw_before = b""
    records = []
else:
    assert stat.S_ISREG(info.st_mode)
    with open(raw_path, "rb") as handle:
        raw_before = handle.read()
    state = b"file"
    commands = (
        ("stage-assume", ("ls-files", "--stage", "-v", "-z")),
        ("stage-skip", ("ls-files", "--stage", "-t", "-z")),
        ("resolve-undo", ("ls-files", "--resolve-undo", "-z")),
        (
            "ita-invisible",
            (
                "diff",
                "--cached",
                "--raw",
                "--no-abbrev",
                "-z",
                "--no-ext-diff",
                "--ita-invisible-in-index",
            ),
        ),
        (
            "ita-visible",
            (
                "diff",
                "--cached",
                "--raw",
                "--no-abbrev",
                "-z",
                "--no-ext-diff",
                "--ita-visible-in-index",
            ),
        ),
    )
    records = []
    for label, arguments in commands:
        query = subprocess.run(
            ["git", "-C", sys.argv[1], *arguments],
            capture_output=True,
            check=True,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
        records.append((label.encode(), query.stdout))
    with open(raw_path, "rb") as handle:
        assert handle.read() == raw_before

parts = [
    b"independent-test-effective-index-logical-v2\0",
    len(raw_path).to_bytes(8, "big"),
    raw_path,
    len(state).to_bytes(8, "big"),
    state,
]
for label, content in records:
    parts.extend(
        (
            len(label).to_bytes(8, "big"),
            label,
            len(content).to_bytes(8, "big"),
            content,
        )
    )
record = b"".join(parts)
print(hashlib.sha256(record).hexdigest())
PY
}

git_index_bytes_digest() {
  GIT_OPTIONAL_LOCKS=0 python3 - "$1" <<'PY'
import hashlib
import os
import subprocess
import sys

result = subprocess.run(
    [
        "git",
        "-C",
        sys.argv[1],
        "rev-parse",
        "--git-path",
        "index",
    ],
    capture_output=True,
    check=True,
    env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
)
assert result.stdout.endswith(b"\n")
raw_path = result.stdout[:-1]
assert raw_path and b"\0" not in raw_path
if not os.path.isabs(raw_path):
    raw_path = os.path.abspath(os.path.join(os.fsencode(sys.argv[1]), raw_path))
with open(raw_path, "rb") as handle:
    print(hashlib.sha256(handle.read()).hexdigest())
PY
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
INDEX_BYTES_DIGEST="$(git_index_bytes_digest "$TARGET")"

SOURCE_CHECKOUT="$TMP_ROOT/source-checkout "
FIXTURE_TEMPLATE_ROOT="$SOURCE_CHECKOUT/fixtures/guru"
mkdir -p "$FIXTURE_TEMPLATE_ROOT"
cp -R "$TEMPLATE_ROOT/." "$FIXTURE_TEMPLATE_ROOT/"
find "$FIXTURE_TEMPLATE_ROOT" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$FIXTURE_TEMPLATE_ROOT" -type f -name '*.pyc' -delete
find "$FIXTURE_TEMPLATE_ROOT" -type f -name .DS_Store -delete
printf '/fixtures/guru/overlay/ignored-provenance.txt\n' > "$SOURCE_CHECKOUT/.gitignore"
git -C "$SOURCE_CHECKOUT" init -q
git -C "$SOURCE_CHECKOUT" config user.name reinstall-source-test
git -C "$SOURCE_CHECKOUT" config user.email reinstall-source-test@example.invalid
git -C "$SOURCE_CHECKOUT" add -A
git -C "$SOURCE_CHECKOUT" -c core.hooksPath=/dev/null commit -qm 'fixture: clean Guru source'
SOURCE_CHECKOUT="$(cd "$SOURCE_CHECKOUT" && pwd -P)"
FIXTURE_TEMPLATE_ROOT="$SOURCE_CHECKOUT/fixtures/guru"
FIXTURE_REINSTALL="$FIXTURE_TEMPLATE_ROOT/overlay/reinstall-official-067.sh"
FIXTURE_HEAD="$(git -C "$SOURCE_CHECKOUT" rev-parse HEAD)"

CLEAN_SOURCE_INDEX_BYTES="$(git_index_bytes_digest "$SOURCE_CHECKOUT")"
CLEAN_SOURCE_INDEX_DIGEST="$(git_index_digest "$SOURCE_CHECKOUT")"
clean_source_output="$(
  run_reinstall_with "$FIXTURE_REINSTALL" \
    --dry-run --backup-dir "$TMP_ROOT/clean-source-dry-run-backup" "$TARGET" 2>&1
)" || fail "clean Git source dry-run failed"
[ "$(git_index_bytes_digest "$SOURCE_CHECKOUT")" = "$CLEAN_SOURCE_INDEX_BYTES" ] || \
  fail "clean source resolver probe mutated the source Git index"
[ "$(git_index_digest "$SOURCE_CHECKOUT")" = "$CLEAN_SOURCE_INDEX_DIGEST" ] || \
  fail "clean source resolver probe changed the source effective-index record"
printf '%s\n' "$clean_source_output" | \
  grep -Fq "source_provenance=git_commit:$FIXTURE_HEAD" || \
  fail "clean Git source provenance did not use the exact fixture HEAD"
printf '%s\n' "$clean_source_output" | \
  grep -Fq "source_checkout_root=$SOURCE_CHECKOUT" || \
  fail "clean Git source provenance did not report its checkout root"

python3 - "$FIXTURE_REINSTALL" "$TMP_ROOT" <<'PY'
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

installer = Path(sys.argv[1])
shell_source = installer.read_text(encoding="utf-8")
marker = "exec python3 - \"$@\" <<'PY'\n"
python_source = shell_source.split(marker, 1)[1].rsplit("\nPY\n", 1)[0]
namespace = {"__name__": "reinstall_official_067_provenance_test"}
exec(compile(python_source, str(installer), "exec"), namespace)

decode_git_checkout_root = namespace["decode_git_checkout_root"]
canonical_digest = namespace["canonical_digest"]
write_json = namespace["write_json"]
ReinstallError = namespace["ReinstallError"]
decode_git_index_path = namespace["decode_git_index_path"]
installer_git_index_digest = namespace["git_index_digest"]

raw_path_cases = [
    os.path.join(os.fsencode(sys.argv[2]), b"index-path" + suffix)
    for suffix in (b" ", b"\t", b"\r", b"\n", b"\xff")
]
raw_path_cases.append(
    os.fsencode(sys.argv[2]).rstrip(b"/")
    + b"//redundant-separator/index-path"
)
for raw_path in raw_path_cases:
    decoded_raw, decoded_path = decode_git_index_path(raw_path + b"\n")
    assert decoded_raw == raw_path
    assert os.fsencode(os.fsdecode(decoded_raw)) == decoded_raw
    assert decoded_path.is_absolute()
    assert decoded_path == Path(os.fsdecode(raw_path))

for malformed in (
    b"",
    b"\n",
    b"relative\n",
    b"/malformed\0index\n",
    os.path.join(os.fsencode(sys.argv[2]), b"unterminated"),
):
    try:
        decode_git_index_path(malformed)
    except ReinstallError:
        pass
    else:
        raise AssertionError(f"malformed Git index path was accepted: {malformed!r}")

host_index_override = os.environ.pop("GIT_INDEX_FILE", None)
raw_index_repo = Path(sys.argv[2]) / "raw-index-repo"
raw_index_repo.mkdir()

def git(*args: str, cwd: Path = raw_index_repo) -> bytes:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        check=True,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    ).stdout

git("init", "-q")
git("config", "user.name", "raw-index-test")
git("config", "user.email", "raw-index-test@example.invalid")
(raw_index_repo / "tracked.txt").write_bytes(b"tracked\n")
git("add", "--", "tracked.txt")
git("-c", "core.hooksPath=/dev/null", "commit", "-qm", "raw index fixture")

baseline_stage = git("ls-files", "--stage", "-z")
baseline_digest = installer_git_index_digest(raw_index_repo)
git("update-index", "--skip-worktree", "--", "tracked.txt")
try:
    assert git("ls-files", "--stage", "-z") == baseline_stage
    assert installer_git_index_digest(raw_index_repo) != baseline_digest
finally:
    git("update-index", "--no-skip-worktree", "--", "tracked.txt")
assert git("ls-files", "-v", "--", "tracked.txt") == b"H tracked.txt\n"
assert git("ls-files", "--stage", "-z") == baseline_stage
baseline_digest = installer_git_index_digest(raw_index_repo)

git("update-index", "--assume-unchanged", "--", "tracked.txt")
try:
    assert git("ls-files", "--stage", "-z") == baseline_stage
    assert installer_git_index_digest(raw_index_repo) != baseline_digest
finally:
    git("update-index", "--no-assume-unchanged", "--", "tracked.txt")
assert git("ls-files", "-v", "--", "tracked.txt") == b"H tracked.txt\n"
assert git("ls-files", "--stage", "-z") == baseline_stage
baseline_digest = installer_git_index_digest(raw_index_repo)

intent_path = raw_index_repo / "intent.txt"
intent_path.write_bytes(b"")
git("add", "--", "intent.txt")
normal_empty_stage = git("ls-files", "--stage", "-z")
normal_empty_digest = installer_git_index_digest(raw_index_repo)
git("reset", "-q", "--", "intent.txt")
git("add", "-N", "--", "intent.txt")
try:
    assert git("ls-files", "--stage", "-z") == normal_empty_stage
    assert installer_git_index_digest(raw_index_repo) != normal_empty_digest
finally:
    git("reset", "-q", "--", "intent.txt")
    intent_path.unlink()
assert git("ls-files", "--stage", "-z") == baseline_stage
assert installer_git_index_digest(raw_index_repo) == baseline_digest

raw_index_output = git(
    "rev-parse",
    "--path-format=absolute",
    "--git-path",
    "index",
)
raw_index_path, _ = decode_git_index_path(raw_index_output)
valid_index = open(raw_index_path, "rb").read()

tracked_path = raw_index_repo / "tracked.txt"
tracked_stat = tracked_path.stat()
os.utime(
    tracked_path,
    ns=(tracked_stat.st_atime_ns, tracked_stat.st_mtime_ns + 2_000_000_000),
)
git("update-index", "--refresh")
stat_refreshed_index = open(raw_index_path, "rb").read()
assert stat_refreshed_index != valid_index
assert git("ls-files", "--stage", "-z") == baseline_stage
assert installer_git_index_digest(raw_index_repo) == baseline_digest
valid_index = stat_refreshed_index

alternate_index = raw_index_repo / "alternate index"
alternate_index.write_bytes(valid_index)
previous_index_override = os.environ.get("GIT_INDEX_FILE")
try:
    os.environ["GIT_INDEX_FILE"] = alternate_index.name
    assert git("ls-files", "--stage", "-z") == baseline_stage
    assert installer_git_index_digest(raw_index_repo) != baseline_digest
finally:
    if previous_index_override is None:
        os.environ.pop("GIT_INDEX_FILE", None)
    else:
        os.environ["GIT_INDEX_FILE"] = previous_index_override
alternate_index.unlink()

try:
    with open(raw_index_path, "wb") as handle:
        handle.write(valid_index + b"\xffraw-index-byte")
    try:
        installer_git_index_digest(raw_index_repo)
    except ReinstallError:
        pass
    else:
        raise AssertionError("corrupt Git index bytes were accepted")
finally:
    with open(raw_index_path, "wb") as handle:
        handle.write(valid_index)
assert installer_git_index_digest(raw_index_repo) == baseline_digest

saved_index = os.path.join(os.fsencode(sys.argv[2]), b"saved-raw-index")
os.replace(raw_index_path, saved_index)
try:
    missing_digest = installer_git_index_digest(raw_index_repo)
    assert missing_digest != baseline_digest
finally:
    os.replace(saved_index, raw_index_path)
assert installer_git_index_digest(raw_index_repo) == baseline_digest

os.replace(raw_index_path, saved_index)
try:
    os.symlink(saved_index, raw_index_path)
    try:
        installer_git_index_digest(raw_index_repo)
    except ReinstallError:
        pass
    else:
        raise AssertionError("symlink Git index was accepted")
    os.unlink(raw_index_path)
    os.mkdir(raw_index_path)
    try:
        installer_git_index_digest(raw_index_repo)
    except ReinstallError:
        pass
    else:
        raise AssertionError("directory Git index was accepted")
    os.rmdir(raw_index_path)
finally:
    if os.path.lexists(raw_index_path):
        if os.path.isdir(raw_index_path):
            os.rmdir(raw_index_path)
        else:
            os.unlink(raw_index_path)
    os.replace(saved_index, raw_index_path)
assert installer_git_index_digest(raw_index_repo) == baseline_digest

linked_worktree = Path(sys.argv[2]) / "raw-index-linked-worktree"
git("worktree", "add", "--detach", "-q", str(linked_worktree), "HEAD")
linked_index_output = git(
    "rev-parse",
    "--path-format=absolute",
    "--git-path",
    "index",
    cwd=linked_worktree,
)
linked_index_path, _ = decode_git_index_path(linked_index_output)
assert linked_index_path != os.fsencode(linked_worktree / ".git/index")
assert os.path.isfile(linked_index_path)
assert installer_git_index_digest(linked_worktree) != baseline_digest
if host_index_override is not None:
    os.environ["GIT_INDEX_FILE"] = host_index_override

record_root = os.path.join(os.fsencode(sys.argv[2]), b"git-root-records")
os.mkdir(record_root)
for suffix in (b" ", b"\t", b"\r", b"\n", b"\xff"):
    raw_path = os.path.join(record_root, b"checkout" + suffix)
    try:
        os.mkdir(raw_path)
    except OSError as error:
        if suffix != b"\xff" or error.errno not in {errno.EILSEQ, errno.EPERM}:
            raise
        decoded = os.fsdecode(raw_path)
        assert os.fsencode(decoded) == raw_path
        continue
    resolved = decode_git_checkout_root(raw_path + b"\n")
    assert os.fsencode(resolved) == os.path.realpath(raw_path), (suffix, resolved)

missing = os.path.join(record_root, b"missing")
for malformed in (b"", b"\n", b"relative\n", missing + b"\n", record_root):
    try:
        decode_git_checkout_root(malformed)
    except ReinstallError:
        pass
    else:
        raise AssertionError(f"malformed Git root was accepted: {malformed!r}")

valid_value = {"path": "valid-\u4e2d\u6587"}
expected_valid_digest = hashlib.sha256(
    json.dumps(
        valid_value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
).hexdigest()
assert canonical_digest(valid_value) == expected_valid_digest

invalid_record = {
    "path": os.fsdecode(b"invalid-\xff"),
    "target": os.fsdecode(b"target-\xfe"),
}
lookalike_record = {"path": "invalid-\ufffd", "target": "target-\ufffd"}
invalid_digest = canonical_digest(invalid_record)
assert invalid_digest == canonical_digest(invalid_record)
assert invalid_digest != canonical_digest(lookalike_record)
report_path = Path(sys.argv[2]) / "surrogate-report.json"
write_json(report_path, {**invalid_record, "unicode": "\u4e2d\u6587"})
raw_report = report_path.read_bytes()
assert b"\\udcff" in raw_report, raw_report
assert b"\\udcfe" in raw_report, raw_report
assert "\u4e2d\u6587".encode() in raw_report, raw_report
parsed_report = json.loads(raw_report.decode("utf-8"))
assert parsed_report == {**invalid_record, "unicode": "\u4e2d\u6587"}

known_skill_digests = namespace["KNOWN_GURU_SKILL_DIGESTS"][
    "guru-bug-fast-path"
]
pre_generation_digest = (
    "a05f456ee66ea001ae408f74692d1ee96dc0006524eabbfd990ef0930c1b3212"
)
reviewed_digest = (
    "d7df7d1d0f53e5b529c530ffa3e82340b0e7543cac4b7abbd2278ee9912b3242"
)
assert {pre_generation_digest, reviewed_digest}.issubset(known_skill_digests)

guru_skill_was_managed = namespace["guru_skill_was_managed"]
namespace["paths_equal"] = lambda *_args, **_kwargs: False
for expected_digest in (pre_generation_digest, reviewed_digest):
    namespace["path_records"] = lambda *_args, digest=expected_digest, **_kwargs: [
        {"path": ".", "type": "directory"},
        {
            "path": "SKILL.md",
            "type": "file",
            "sha256": digest,
        },
    ]
    assert guru_skill_was_managed(
        ".agents/skills",
        Path("/nonexistent/legacy-guru-bug-fast-path"),
        "guru-bug-fast-path",
        {},
        Path("/nonexistent/overlay"),
    )
PY

reset_source_fixture() {
  local tracked_state
  git -C "$SOURCE_CHECKOUT" update-index \
    --no-assume-unchanged -- fixtures/guru/overlay/README.md
  git -C "$SOURCE_CHECKOUT" update-index \
    --no-skip-worktree -- fixtures/guru/overlay/README.md
  tracked_state="$(
    git -C "$SOURCE_CHECKOUT" ls-files -v -- fixtures/guru/overlay/README.md
  )"
  [ "$tracked_state" = "H fixtures/guru/overlay/README.md" ] || \
    fail "source fixture flags did not clear to a normal entry: $tracked_state"
  git -C "$SOURCE_CHECKOUT" reset --hard -q HEAD
  git -C "$SOURCE_CHECKOUT" clean -fdxq -- fixtures/guru
}

assert_tree_source_provenance() {
  local label="$1"
  local backup="$TMP_ROOT/$label-source-dry-run-backup"
  local output
  local source_index_before
  local source_index_record_before
  local target_index_before
  local target_index_bytes_before
  source_index_before="$(git_index_bytes_digest "$SOURCE_CHECKOUT")"
  source_index_record_before="$(git_index_digest "$SOURCE_CHECKOUT")"
  target_index_before="$(git_index_digest "$TARGET")"
  target_index_bytes_before="$(git_index_bytes_digest "$TARGET")"
  output="$(
    run_reinstall_with "$FIXTURE_REINSTALL" \
      --dry-run --backup-dir "$backup" "$TARGET" 2>&1
  )" || fail "$label Git source dry-run failed"
  [ "$(git_index_bytes_digest "$SOURCE_CHECKOUT")" = "$source_index_before" ] || \
    fail "$label source resolver probe mutated the source Git index"
  [ "$(git_index_digest "$SOURCE_CHECKOUT")" = "$source_index_record_before" ] || \
    fail "$label source resolver probe changed the source effective-index record"
  [ "$(git_index_digest "$TARGET")" = "$target_index_before" ] || \
    fail "$label provenance dry-run changed the target effective-index record"
  [ "$(git_index_bytes_digest "$TARGET")" = "$target_index_bytes_before" ] || \
    fail "$label provenance dry-run mutated the target raw Git index bytes"
  PROVENANCE_DIGEST="$(
    printf '%s\n' "$output" |
      sed -n 's/^.*source_provenance=template_tree_sha256:\([0-9a-f]*\).*$/\1/p' |
      tail -n 1
  )"
  [ "${#PROVENANCE_DIGEST}" -eq 64 ] || \
    fail "$label source did not use a SHA-256 tree provenance"
  printf '%s\n' "$output" | \
    grep -Fq "source_checkout_root=$SOURCE_CHECKOUT" || \
    fail "$label Git source provenance lost its checkout root"
  [ ! -e "$backup" ] || fail "$label source dry-run created its backup directory"
}

reset_source_fixture
printf '\nprovenance fixture staged change\n' \
  >> "$FIXTURE_TEMPLATE_ROOT/overlay/README.md"
git -C "$SOURCE_CHECKOUT" add -- fixtures/guru/overlay/README.md
git -C "$SOURCE_CHECKOUT" restore --source=HEAD --worktree -- \
  fixtures/guru/overlay/README.md
assert_tree_source_provenance "staged"

reset_source_fixture
printf '\nprovenance fixture unstaged change\n' \
  >> "$FIXTURE_TEMPLATE_ROOT/overlay/README.md"
assert_tree_source_provenance "unstaged"

reset_source_fixture
printf 'provenance fixture untracked file\n' \
  > "$FIXTURE_TEMPLATE_ROOT/overlay/untracked-provenance.txt"
assert_tree_source_provenance "untracked"
UNTRACKED_TREE_DIGEST="$PROVENANCE_DIGEST"
assert_tree_source_provenance "untracked-repeat"
[ "$PROVENANCE_DIGEST" = "$UNTRACKED_TREE_DIGEST" ] || \
  fail "repeated unchanged dirty source tree digests were not stable"

reset_source_fixture
printf 'provenance fixture ignored file\n' \
  > "$FIXTURE_TEMPLATE_ROOT/overlay/ignored-provenance.txt"
assert_tree_source_provenance "ignored"

reset_source_fixture
git -C "$SOURCE_CHECKOUT" update-index \
  --assume-unchanged -- fixtures/guru/overlay/README.md
printf '\nprovenance fixture assume-unchanged change\n' \
  >> "$FIXTURE_TEMPLATE_ROOT/overlay/README.md"
assert_tree_source_provenance "assume-unchanged"

reset_source_fixture
git -C "$SOURCE_CHECKOUT" update-index \
  --skip-worktree -- fixtures/guru/overlay/README.md
printf '\nprovenance fixture skip-worktree change\n' \
  >> "$FIXTURE_TEMPLATE_ROOT/overlay/README.md"
assert_tree_source_provenance "skip-worktree"

reset_source_fixture
mkdir "$FIXTURE_TEMPLATE_ROOT/overlay/empty-provenance-directory"
assert_tree_source_provenance "empty-directory"

reset_source_fixture
chmod +x "$FIXTURE_TEMPLATE_ROOT/overlay/README.md"
assert_tree_source_provenance "executable-mode"

reset_source_fixture
rm "$FIXTURE_TEMPLATE_ROOT/overlay/README.md"
mkdir "$FIXTURE_TEMPLATE_ROOT/overlay/README.md"
printf 'tracked file replaced by directory\n' \
  > "$FIXTURE_TEMPLATE_ROOT/overlay/README.md/replacement.txt"
assert_tree_source_provenance "file-directory-replacement"

reset_source_fixture
rm "$FIXTURE_TEMPLATE_ROOT/overlay/README.md"
ln -s apply.sh "$FIXTURE_TEMPLATE_ROOT/overlay/README.md"
assert_tree_source_provenance "symlink-replacement"

reset_source_fixture
python3 - "$FIXTURE_TEMPLATE_ROOT" <<'PY'
import errno
import os
import sys

overlay = os.path.join(os.fsencode(sys.argv[1]), b"overlay")
invalid_file = os.path.join(overlay, b"non-utf8-\xff")
try:
    descriptor = os.open(
        invalid_file,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o644,
    )
except OSError as error:
    if error.errno not in {errno.EILSEQ, errno.EPERM}:
        raise
    assert os.fsencode(os.fsdecode(invalid_file)) == invalid_file
    print(f"NON_UTF8_FILENAME_FIXTURE_UNSUPPORTED errno={error.errno}")
else:
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(b"invalid filename bytes\n")
    assert b"non-utf8-\xff" in os.listdir(overlay)
invalid_link = os.path.join(overlay, b"non-utf8-link")
os.symlink(b"target-\xfe", invalid_link)
assert os.readlink(invalid_link) == b"target-\xfe"
PY
assert_tree_source_provenance "non-utf8-bytes"
NON_UTF8_TREE_DIGEST="$PROVENANCE_DIGEST"
assert_tree_source_provenance "non-utf8-bytes-repeat"
[ "$PROVENANCE_DIGEST" = "$NON_UTF8_TREE_DIGEST" ] || \
  fail "repeated non-UTF-8 source tree digests were not stable"

reset_source_fixture
python3 - "$FIXTURE_TEMPLATE_ROOT" <<'PY'
import os
from pathlib import Path
import sys

overlay = Path(sys.argv[1]) / "overlay"
(overlay / "non-utf8-\ufffd").write_bytes(b"invalid filename bytes\n")
os.symlink("target-\ufffd", overlay / "non-utf8-link")
PY
assert_tree_source_provenance "valid-utf8-lookalike"
[ "$PROVENANCE_DIGEST" != "$NON_UTF8_TREE_DIGEST" ] || \
  fail "raw invalid bytes collapsed into valid UTF-8 lookalike bytes"

reset_source_fixture
printf 'provenance fixture ignored file\n' \
  > "$FIXTURE_TEMPLATE_ROOT/overlay/ignored-provenance.txt"
assert_tree_source_provenance "ignored-final"
IGNORED_TREE_DIGEST="$PROVENANCE_DIGEST"
REINSTALL="$FIXTURE_REINSTALL"

NO_NETWORK_BIN="$TMP_ROOT/no-network-bin"
NETWORK_SENTINEL="$TMP_ROOT/source-target-network-invoked"
mkdir -p "$NO_NETWORK_BIN"
cat > "$NO_NETWORK_BIN/npm" <<'EOF'
#!/usr/bin/env bash
: > "${GURU_REINSTALL_NETWORK_SENTINEL:?}"
exit 99
EOF
chmod +x "$NO_NETWORK_BIN/npm"
set +e
same_checkout_output="$(
  PATH="$NO_NETWORK_BIN:$PATH" \
    GURU_REINSTALL_NETWORK_SENTINEL="$NETWORK_SENTINEL" \
    run_reinstall_with "$FIXTURE_REINSTALL" --dry-run "$SOURCE_CHECKOUT" 2>&1
)"
same_checkout_rc=$?
set -e
[ "$same_checkout_rc" -eq 1 ] || \
  fail "dirty source checkout target returned $same_checkout_rc instead of 1"
printf '%s\n' "$same_checkout_output" | \
  grep -Fq 'target must not be this Guru source checkout' || \
  fail "dirty Git provenance did not preserve the source-checkout safety guard"
[ ! -e "$NETWORK_SENTINEL" ] || \
  fail "dirty self-target guard ran npm before blocking"

[ ! -e "$TMP_ROOT/clean-source-dry-run-backup" ] || \
  fail "clean source dry-run created the requested backup directory"
[ "$(tree_digest "$TARGET")" = "$ORIGINAL_DIGEST" ] || fail "dry-run changed the target"
[ "$(git_index_digest "$TARGET")" = "$INDEX_DIGEST" ] || \
  fail "dry-run changed the Git index"
[ "$(git_index_bytes_digest "$TARGET")" = "$INDEX_BYTES_DIGEST" ] || \
  fail "dry-run changed the raw Git index bytes"

DETACHED_TEMPLATE_ROOT="$TMP_ROOT/detached-package/guru"
mkdir -p "$DETACHED_TEMPLATE_ROOT"
cp -R "$TEMPLATE_ROOT/." "$DETACHED_TEMPLATE_ROOT/"
detached_output="$(
  run_reinstall_with \
    "$DETACHED_TEMPLATE_ROOT/overlay/reinstall-official-067.sh" \
    --dry-run --backup-dir "$TMP_ROOT/detached-dry-run-backup" "$TARGET" 2>&1
)" || fail "detached package dry-run failed"
printf '%s' "$detached_output" | grep -q 'source_provenance=template_tree_sha256:' || \
  fail "detached package did not use template-tree provenance"
printf '%s\n' "$detached_output" | grep -Fq 'source_checkout_root=none' || \
  fail "detached package unexpectedly reported a Git checkout root"
[ ! -e "$TMP_ROOT/detached-dry-run-backup" ] || \
  fail "detached package dry-run created the requested backup directory"
[ "$(tree_digest "$TARGET")" = "$ORIGINAL_DIGEST" ] || \
  fail "detached package dry-run changed the target"
[ "$(git_index_digest "$TARGET")" = "$INDEX_DIGEST" ] || \
  fail "detached package dry-run changed the Git index"
[ "$(git_index_bytes_digest "$TARGET")" = "$INDEX_BYTES_DIGEST" ] || \
  fail "detached package dry-run changed the raw Git index bytes"

set +e
GURU_REINSTALL_TEST_FAIL_AT=after-uninstall run_reinstall \
  --keep-backup --backup-dir "$TMP_ROOT/failure-backup" "$TARGET"
failure_rc=$?
set -e
[ "$failure_rc" -eq 1 ] || fail "forced failure returned $failure_rc instead of 1"
[ "$(tree_digest "$TARGET")" = "$ORIGINAL_DIGEST" ] || fail "forced failure did not restore target digest"
[ "$(git_index_digest "$TARGET")" = "$INDEX_DIGEST" ] || \
  fail "forced failure rollback changed the logical index record"
[ -f "$TMP_ROOT/failure-backup/rollback-report.json" ] || fail "rollback report missing"

set +e
GURU_REINSTALL_TEST_FAIL_AT=after-overlay run_reinstall \
  --keep-backup --backup-dir "$TMP_ROOT/overlay-failure-backup" "$TARGET"
overlay_failure_rc=$?
set -e
[ "$overlay_failure_rc" -eq 1 ] || fail "forced overlay failure returned $overlay_failure_rc instead of 1"
[ "$(tree_digest "$TARGET")" = "$ORIGINAL_DIGEST" ] || \
  fail "forced overlay failure did not restore target digest"
[ "$(git_index_digest "$TARGET")" = "$INDEX_DIGEST" ] || \
  fail "forced overlay rollback changed the logical index record"
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
  fail "logical Git index changed during successful reinstall"
python3 - \
  "$TMP_ROOT/success-backup/reinstall-result.json" \
  "$TMP_ROOT/success-backup/snapshot-manifest.json" \
  "$SOURCE_CHECKOUT" \
  "$IGNORED_TREE_DIGEST" <<'PY'
import json
import sys

result = json.load(open(sys.argv[1], encoding="utf-8"))
snapshot = json.load(open(sys.argv[2], encoding="utf-8"))
assert result["rollback_mode"] == "external-managed-snapshot-v1", result
assert result["git_index_unchanged"] is True, result
assert "AGENTS.md" in result["root_documents_restored"], result
assert result["source_commit"] is None, result
assert result["source_provenance"] == {
    "checkout_root": sys.argv[3],
    "kind": "template_tree_sha256",
    "revision": sys.argv[4],
}, result
assert snapshot["git_index_digest_kind"] == "git-effective-index-logical-record-v3", snapshot
assert snapshot["git_index_sha256"], snapshot
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
printf '# user-owned same-name bug fast path\n' \
  > "$TARGET/.agents/skills/guru-bug-fast-path/SKILL.md"
printf '# user-owned same-name bug fast path\n' \
  > "$TARGET/.claude/skills/guru-bug-fast-path/SKILL.md"
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
  "$TEMPLATE_ROOT/specs/guru-flutter-client/guides/golden-path.md" \
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
assert {
    ".agents/skills/guru-bug-fast-path",
    ".claude/skills/guru-bug-fast-path",
}.issubset({row["path"] for row in skills["conflicts"]}), skills
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
grep -q 'user-owned same-name bug fast path' \
  "$TMP_ROOT/conflict-backup/conflicts/skills/old/.agents/skills/guru-bug-fast-path/SKILL.md" || \
  fail "old .agents same-name Skill conflict copy missing"
grep -q 'user-owned same-name bug fast path' \
  "$TMP_ROOT/conflict-backup/conflicts/skills/old/.claude/skills/guru-bug-fast-path/SKILL.md" || \
  fail "old .claude same-name Skill conflict copy missing"
cmp -s \
  "$TEMPLATE_ROOT/overlay/agents-skills/guru-bug-fast-path/SKILL.md" \
  "$TARGET/.agents/skills/guru-bug-fast-path/SKILL.md" || \
  fail "new managed bug fast path did not win .agents conflict"
cmp -s \
  "$TARGET/.agents/skills/guru-bug-fast-path/SKILL.md" \
  "$TARGET/.claude/skills/guru-bug-fast-path/SKILL.md" || \
  fail "new managed bug fast path did not reconcile both target roots"
[ "$(git_index_digest "$TARGET")" = "$INDEX_DIGEST" ] || \
  fail "conflict reinstall changed the logical index record"

printf 'REINSTALL_067_TEST_OK official=0.6.7 dry_run=pass detached_package=pass byte_provenance=pass rollback=pass success=pass spec_conflict=pass skill_conflict=pass\n'
