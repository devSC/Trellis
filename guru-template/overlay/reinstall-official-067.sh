#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export GURU_REINSTALL_SCRIPT_DIR="$SCRIPT_DIR"

exec python3 - "$@" <<'PY'
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Iterable


OFFICIAL_PACKAGE = "@mindfoldhq/trellis"
OFFICIAL_VERSION = "0.6.7"
CONFLICT_EXIT = 3
ROLLBACK_FAILURE_EXIT = 70
STRUCTURED_MANIFEST_PATHS = {
    "AGENTS.md",
    "CLAUDE.md",
    ".claude/settings.json",
    ".gemini/settings.json",
    ".factory/settings.json",
    ".codebuddy/settings.json",
    ".qoder/settings.json",
    ".codex/hooks.json",
    ".cursor/hooks.json",
    ".github/copilot/hooks.json",
    ".opencode/package.json",
    ".pi/settings.json",
    ".codex/config.toml",
}
FIXED_MANAGED_SCOPES = (
    ".trellis",
    ".agents",
    ".claude",
    ".codex",
    ".cursor",
    ".opencode",
    ".pi",
    ".kiro",
    ".gemini",
    ".qoder",
    ".codebuddy",
    ".factory",
    ".github",
    ".kilo",
    ".antigravity",
    ".devin",
    ".reasonix",
    ".zcode",
    ".omp",
    ".trae",
    "AGENTS.md",
    "CLAUDE.md",
)
SKILL_ROOTS = (
    ".agents/skills",
    ".claude/skills",
    ".codex/skills",
    ".cursor/skills",
    ".opencode/skills",
    ".pi/skills",
    ".kiro/skills",
    ".gemini/skills",
    ".qoder/skills",
    ".codebuddy/skills",
    ".factory/skills",
    ".github/skills",
)
CLIENT_FLAGS = {
    ".cursor": "--cursor",
    ".claude": "--claude",
    ".opencode": "--opencode",
    ".agents": "--codex",
    ".codex": "--codex",
    ".kilo": "--kilo",
    ".kiro": "--kiro",
    ".gemini": "--gemini",
    ".antigravity": "--antigravity",
    ".devin": "--devin",
    ".qoder": "--qoder",
    ".codebuddy": "--codebuddy",
    ".github": "--copilot",
    ".factory": "--droid",
    ".pi": "--pi",
    ".reasonix": "--reasonix",
    ".zcode": "--zcode",
    ".omp": "--omp",
    ".trae": "--trae",
}
PLATFORM_SPECS = {
    "flutter": ("guru-flutter-client", "guru-client-workflow.md"),
    "go": ("guru-go-backend", "guru-go-workflow.md"),
    "ios": ("guru-ios-native", "guru-ios-workflow.md"),
    "h5": ("guru-h5-web", "guru-h5-workflow.md"),
}


class ReinstallError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ReinstallError(message)


def log(message: str) -> None:
    print(f"[guru-reinstall-067] {message}", flush=True)


def command_text(command: Iterable[str]) -> str:
    return shlex.join([str(item) for item in command])


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    log(f"run: {command_text(command)}" + (f" (cwd={cwd})" if cwd else ""))
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture,
        check=False,
    )
    if result.returncode != 0:
        if capture:
            if result.stdout:
                sys.stderr.write(result.stdout)
            if result.stderr:
                sys.stderr.write(result.stderr)
        fail(f"command failed with rc={result.returncode}: {command_text(command)}")
    return result


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        fail(f"required command is unavailable: {name}")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(encoded)


def path_exists(path: Path) -> bool:
    return os.path.lexists(path)


def remove_path(path: Path) -> None:
    if not path_exists(path):
        return
    if path.is_symlink() or not path.is_dir():
        path.unlink()
    else:
        shutil.rmtree(path)


def copy_path(source: Path, destination: Path) -> None:
    if not path_exists(source):
        fail(f"copy source is missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    remove_path(destination)
    if source.is_symlink():
        destination.symlink_to(os.readlink(source), target_is_directory=source.is_dir())
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True, copy_function=shutil.copy2)
    else:
        shutil.copy2(source, destination, follow_symlinks=False)


def describe_entry(path: Path, relative: str) -> dict[str, Any]:
    info = path.lstat()
    mode = stat.S_IMODE(info.st_mode)
    if stat.S_ISLNK(info.st_mode):
        return {"path": relative, "type": "symlink", "mode": mode, "target": os.readlink(path)}
    if stat.S_ISDIR(info.st_mode):
        return {"path": relative, "type": "directory", "mode": mode}
    if stat.S_ISREG(info.st_mode):
        return {
            "path": relative,
            "type": "file",
            "mode": mode,
            "size": info.st_size,
            "sha256": sha256_file(path),
        }
    fail(f"unsupported managed-surface file type: {path}")
    raise AssertionError("unreachable")


def path_records(root: Path, *, ignore_noise: bool = False) -> list[dict[str, Any]]:
    if not path_exists(root):
        return [{"path": ".", "type": "missing"}]
    records = [describe_entry(root, ".")]
    if root.is_symlink() or not root.is_dir():
        return records
    for directory, dir_names, file_names in os.walk(root, topdown=True, followlinks=False):
        if ignore_noise:
            dir_names[:] = sorted(name for name in dir_names if name not in {"__pycache__"})
            file_names = sorted(name for name in file_names if name != ".DS_Store" and not name.endswith(".pyc"))
        else:
            dir_names.sort()
            file_names.sort()
        directory_path = Path(directory)
        for name in dir_names:
            child = directory_path / name
            relative = child.relative_to(root).as_posix()
            records.append(describe_entry(child, relative))
        for name in file_names:
            child = directory_path / name
            relative = child.relative_to(root).as_posix()
            records.append(describe_entry(child, relative))
    return sorted(records, key=lambda row: row["path"])


def path_digest(path: Path, *, ignore_noise: bool = False) -> str:
    return canonical_digest(path_records(path, ignore_noise=ignore_noise))


def paths_equal(left: Path, right: Path, *, ignore_noise: bool = False) -> bool:
    return path_digest(left, ignore_noise=ignore_noise) == path_digest(right, ignore_noise=ignore_noise)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def load_hashes(target: Path) -> dict[str, str]:
    path = target / ".trellis/.template-hashes.json"
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"cannot read target Trellis manifest {path}: {error}")
    hashes = parsed.get("hashes") if isinstance(parsed, dict) and "hashes" in parsed else parsed
    if not isinstance(hashes, dict) or not hashes:
        fail(f"target Trellis manifest has no managed paths: {path}")
    normalized: dict[str, str] = {}
    for raw_path, raw_digest in hashes.items():
        if not isinstance(raw_path, str) or not raw_path or raw_path.startswith("/") or ".." in Path(raw_path).parts:
            fail(f"target Trellis manifest contains an invalid path: {raw_path!r}")
        if raw_path == ".git" or raw_path.startswith(".git/"):
            fail("target Trellis manifest must not own .git")
        normalized[raw_path] = str(raw_digest)
    return normalized


def target_git_root(target: Path) -> Path:
    result = run(["git", "-C", str(target), "rev-parse", "--show-toplevel"], capture=True)
    return Path(result.stdout.strip()).resolve()


def git_index_digest(target: Path) -> str:
    result = run(
        ["git", "-C", str(target), "ls-files", "--stage", "-z"],
        capture=True,
    )
    return sha256_bytes(result.stdout.encode("utf-8"))


def verify_git_index_unchanged(target: Path, expected: str, phase: str) -> None:
    actual = git_index_digest(target)
    if actual != expected:
        fail(f"{phase} changed .git/index: expected {expected}, got {actual}")


def parse_simple_yaml_scalar(path: Path, wanted: tuple[str, ...]) -> str | None:
    if not path.is_file():
        return None
    stack: list[tuple[int, str]] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        match = re.match(r"^(\s*)([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*(?:#.*)?$", raw_line)
        if not match:
            continue
        indent = len(match.group(1).replace("\t", "    "))
        key = match.group(2)
        value = match.group(3).strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        current = tuple(item[1] for item in stack) + (key,)
        if value and current == wanted:
            return value.strip("'\"")
        if not value:
            stack.append((indent, key))
    return None


def detect_platform(target: Path, override: str | None) -> str:
    if override:
        return override
    configured = parse_simple_yaml_scalar(target / ".trellis/config.yaml", ("guru", "platform"))
    if configured in PLATFORM_SPECS:
        return configured
    spec = target / ".trellis/spec"
    candidates: set[str] = set()
    if (spec / "flutter").is_dir():
        candidates.add("flutter")
    if (spec / "ios").is_dir():
        candidates.add("ios")
    if (spec / "frontend").is_dir():
        candidates.add("h5")
    if (spec / "backend").is_dir() and not (spec / "frontend").is_dir():
        candidates.add("go")
    if len(candidates) != 1:
        fail("cannot determine one Guru platform; pass --platform flutter|go|ios|h5")
    return next(iter(candidates))


def detect_clients(hashes: dict[str, str]) -> list[str]:
    top_levels = {Path(path).parts[0] for path in hashes}
    flags = {"--codex"}
    for root, flag in CLIENT_FLAGS.items():
        if root in top_levels:
            flags.add(flag)
    return sorted(flags)


def original_developer(target: Path) -> str | None:
    path = target / ".trellis/.developer"
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("name=") and line[5:].strip():
            return line[5:].strip()
    return None


def managed_scopes(hashes: dict[str, str]) -> list[str]:
    scopes = set(FIXED_MANAGED_SCOPES)
    for manifest_path in hashes:
        top = Path(manifest_path).parts[0]
        if top != ".git":
            scopes.add(top)
    return sorted(scopes)


def validate_backup_path(target: Path, requested: Path | None) -> Path | None:
    if requested is None:
        return None
    expanded = requested.expanduser().absolute()
    if path_exists(expanded) and expanded.is_symlink():
        fail(f"backup path must not be a symlink: {expanded}")
    resolved_parent = expanded.parent.resolve()
    candidate = resolved_parent / expanded.name
    try:
        if os.path.commonpath((str(target), str(candidate))) == str(target):
            fail("backup directory must be outside the target")
    except ValueError:
        pass
    if candidate.exists() and any(candidate.iterdir()):
        fail(f"backup directory must be missing or empty: {candidate}")
    return candidate


def create_backup_path(target: Path, requested: Path | None) -> Path:
    if requested is None:
        return Path(tempfile.mkdtemp(prefix=f"{target.name}-trellis-067-backup-"))
    requested.parent.mkdir(parents=True, exist_ok=True)
    requested.mkdir(parents=False, exist_ok=True)
    return requested


def create_snapshot(
    target: Path,
    backup: Path,
    scopes: list[str],
    index_digest: str,
    hashes: dict[str, str],
    source_commit: str,
) -> dict[str, Any]:
    original = backup / "original"
    original.mkdir(parents=True, exist_ok=True)
    scope_rows: list[dict[str, Any]] = []
    for scope in scopes:
        source = target / scope
        records = path_records(source)
        scope_rows.append({"path": scope, "digest": canonical_digest(records), "records": records})
        if path_exists(source):
            copy_path(source, original / scope)
    manifest = {
        "schema_version": 1,
        "target": str(target),
        "source_commit": source_commit,
        "official_package": OFFICIAL_PACKAGE,
        "official_version": OFFICIAL_VERSION,
        "git_index_sha256": index_digest,
        "git_index_digest_kind": "git-ls-files-stage-v1",
        "scopes": scope_rows,
        "old_template_hashes_sha256": canonical_digest(hashes),
        "tasks_digest": path_digest(target / ".trellis/tasks"),
        "workspace_digest": path_digest(target / ".trellis/workspace"),
    }
    write_json(backup / "snapshot-manifest.json", manifest)
    log(f"external snapshot complete: {backup}")
    return manifest


def restore_snapshot(target: Path, backup: Path, manifest: dict[str, Any]) -> None:
    log("rollback: restoring original managed surfaces")
    original = backup / "original"
    for row in manifest["scopes"]:
        scope = row["path"]
        live = target / scope
        remove_path(live)
        saved = original / scope
        if path_exists(saved):
            copy_path(saved, live)
    mismatches = []
    for row in manifest["scopes"]:
        actual = path_digest(target / row["path"])
        if actual != row["digest"]:
            mismatches.append(row["path"])
    if mismatches:
        fail(f"rollback digest mismatch: {', '.join(mismatches)}")
    if git_index_digest(target) != manifest["git_index_sha256"]:
        fail("rollback detected a changed .git/index")
    write_json(backup / "rollback-report.json", {"status": "restored", "verified_scopes": len(manifest["scopes"])})
    log("rollback: original managed-surface digest restored")


def verify_official_package(prefix: Path) -> Path:
    package_root = prefix / "node_modules/@mindfoldhq/trellis"
    package_json = package_root / "package.json"
    binary = prefix / "node_modules/.bin/trellis"
    if not package_json.is_file() or not os.access(binary, os.X_OK):
        fail("exact official package or executable is missing from temporary npm prefix")
    parsed = json.loads(package_json.read_text(encoding="utf-8"))
    if parsed.get("name") != OFFICIAL_PACKAGE or parsed.get("version") != OFFICIAL_VERSION:
        fail(f"official package mismatch: {parsed.get('name')}@{parsed.get('version')}")
    package_real = package_root.resolve()
    binary_real = binary.resolve()
    try:
        binary_real.relative_to(package_real)
    except ValueError:
        fail(f"official binary does not resolve inside exact package: {binary_real}")
    version_output = run([str(binary), "--version"], capture=True).stdout
    version_lines = [line.strip() for line in version_output.splitlines() if line.strip()]
    version = version_lines[-1] if version_lines else ""
    if version != OFFICIAL_VERSION:
        fail(f"official binary reported version {version!r}, expected {OFFICIAL_VERSION}")
    log(f"official package verified: {OFFICIAL_PACKAGE}@{OFFICIAL_VERSION}")
    return binary


def install_official_prefix(work_root: Path) -> tuple[Path, dict[str, str]]:
    prefix = work_root / "npm-prefix"
    environment = os.environ.copy()
    environment.setdefault("npm_config_cache", str(work_root / "npm-cache"))
    run(
        [
            "npm",
            "install",
            "--prefix",
            str(prefix),
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
            "--silent",
            f"{OFFICIAL_PACKAGE}@{OFFICIAL_VERSION}",
        ],
        env=environment,
    )
    binary = verify_official_package(prefix)
    environment["PATH"] = str(prefix / "node_modules/.bin") + os.pathsep + environment.get("PATH", "")
    return binary, environment


def verify_uninstalled(target: Path, old_hashes: dict[str, str]) -> None:
    if path_exists(target / ".trellis"):
        fail("official uninstall returned success but .trellis still exists")
    residue = []
    for manifest_path in old_hashes:
        if manifest_path.startswith(".trellis/") or manifest_path in STRUCTURED_MANIFEST_PATHS:
            continue
        if path_exists(target / manifest_path):
            residue.append(manifest_path)
    if residue:
        fail("official uninstall left opaque manifest-owned paths: " + ", ".join(residue[:20]))


def guru_skill_names(overlay_dir: Path) -> set[str]:
    inventory = overlay_dir / "agents-skills"
    names = {path.name for path in inventory.iterdir() if path.is_dir()}
    names.update({"trellis-local", "design-grill"})
    return names


def clear_project_skill_roots(target: Path) -> None:
    for relative in SKILL_ROOTS:
        remove_path(target / relative)


def write_codex_policy(config_path: Path) -> None:
    text = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
    if re.search(r"(?m)^guru\s*:", text):
        fail("fresh official config unexpectedly already contains a top-level guru section")
    block = """
# Fresh reinstall policy: Codex only; current overlay fills remaining defaults.
guru:
  supervision:
    provider: codex
    high_risk_review_provider_policy: codex
    adversarial_enabled: false
"""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(text.rstrip() + "\n" + block.lstrip(), encoding="utf-8")


def restore_exact_data(target: Path, backup: Path, manifest: dict[str, Any]) -> None:
    original_trellis = backup / "original/.trellis"
    for relative in ("tasks", "workspace"):
        live = target / ".trellis" / relative
        saved = original_trellis / relative
        remove_path(live)
        if path_exists(saved):
            copy_path(saved, live)
    saved_developer = original_trellis / ".developer"
    if path_exists(saved_developer):
        copy_path(saved_developer, target / ".trellis/.developer")
    remove_path(target / ".trellis/.runtime")
    if path_digest(target / ".trellis/tasks") != manifest["tasks_digest"]:
        fail("restored .trellis/tasks digest differs from original")
    if path_digest(target / ".trellis/workspace") != manifest["workspace_digest"]:
        fail("restored .trellis/workspace digest differs from original")


def reconcile_root_documents(target: Path, backup: Path) -> dict[str, list[str]]:
    block_pattern = re.compile(
        r"<!-- TRELLIS:START -->.*?<!-- TRELLIS:END -->",
        flags=re.DOTALL,
    )
    report: dict[str, list[str]] = {
        "external_content_restored": [],
        "unchanged": [],
    }
    for relative in ("AGENTS.md", "CLAUDE.md"):
        saved = backup / "original" / relative
        live = target / relative
        if not path_exists(saved):
            continue
        if not path_exists(live):
            copy_path(saved, live)
            report["external_content_restored"].append(relative)
            continue
        saved_text = saved.read_text(encoding="utf-8", errors="replace")
        live_text = live.read_text(encoding="utf-8", errors="replace")
        managed_match = block_pattern.search(live_text)
        if managed_match is None:
            report["unchanged"].append(relative)
            continue
        saved_external = block_pattern.sub("", saved_text).strip()
        live_external = block_pattern.sub("", live_text).strip()
        sections = [managed_match.group(0).strip()]
        if live_external:
            sections.append(live_external)
        if saved_external and saved_external not in live_external:
            sections.append(saved_external)
            report["external_content_restored"].append(relative)
        else:
            report["unchanged"].append(relative)
        live.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    write_json(backup / "root-document-reconcile-report.json", report)
    return report


def iter_leaf_paths(root: Path) -> Iterable[Path]:
    if not path_exists(root):
        return
    if root.is_symlink() or not root.is_dir():
        yield root
        return
    for directory, dir_names, file_names in os.walk(root, topdown=True, followlinks=False):
        dir_names.sort()
        file_names.sort()
        directory_path = Path(directory)
        for name in dir_names:
            child = directory_path / name
            if child.is_symlink():
                yield child
        for name in file_names:
            yield directory_path / name


def save_conflict(old: Path, new: Path, root: Path, relative: Path) -> None:
    if path_exists(old):
        copy_path(old, root / "old" / relative)
    if path_exists(new):
        copy_path(new, root / "new" / relative)


def reconcile_spec(target: Path, backup: Path) -> dict[str, Any]:
    old_root = backup / "original/.trellis/spec"
    new_root = target / ".trellis/spec"
    conflict_root = backup / "conflicts/spec"
    report: dict[str, Any] = {
        "new_managed_base_kept": True,
        "project_conventions_restored": False,
        "project_only_restored": [],
        "identical": [],
        "conflicts": [],
    }
    project_conventions = Path("conventions/project-conventions.md")
    old_conventions = old_root / project_conventions
    if path_exists(old_conventions):
        copy_path(old_conventions, new_root / project_conventions)
        report["project_conventions_restored"] = True
    if path_exists(old_root):
        for old_path in iter_leaf_paths(old_root):
            relative = old_path.relative_to(old_root)
            if relative == project_conventions:
                continue
            new_path = new_root / relative
            if not path_exists(new_path):
                copy_path(old_path, new_path)
                report["project_only_restored"].append(relative.as_posix())
            elif paths_equal(old_path, new_path):
                report["identical"].append(relative.as_posix())
            else:
                save_conflict(old_path, new_path, conflict_root, relative)
                report["conflicts"].append({"path": relative.as_posix(), "target_winner": "new"})
    write_json(backup / "spec-reconcile-report.json", report)
    return report


def official_skill_ownership(hashes: dict[str, str]) -> set[tuple[str, str]]:
    owned: set[tuple[str, str]] = set()
    for manifest_path in hashes:
        parts = Path(manifest_path).parts
        if len(parts) >= 3 and parts[1] == "skills":
            owned.add((f"{parts[0]}/skills", parts[2]))
    return owned


def reconcile_one_project_skill(
    source: Path,
    destination: Path,
    relative_label: str,
    conflict_root: Path,
    report: dict[str, Any],
) -> None:
    if not path_exists(destination):
        copy_path(source, destination)
        report["project_restored"].append(relative_label)
    elif paths_equal(source, destination, ignore_noise=True):
        report["identical"].append(relative_label)
    else:
        save_conflict(source, destination, conflict_root, Path(relative_label))
        report["conflicts"].append({"path": relative_label, "target_winner": "new"})


def reconcile_skills(
    target: Path,
    backup: Path,
    old_hashes: dict[str, str],
    overlay_dir: Path,
) -> dict[str, Any]:
    original = backup / "original"
    official_owned = official_skill_ownership(old_hashes)
    guru_owned = guru_skill_names(overlay_dir)
    report: dict[str, Any] = {
        "official_refreshed": [],
        "guru_refreshed": [],
        "project_restored": [],
        "identical": [],
        "conflicts": [],
        "global_roots_touched": False,
    }
    for root, name in sorted(official_owned):
        if path_exists(target / root / name):
            report["official_refreshed"].append(f"{root}/{name}")
    for root in (".agents/skills", ".claude/skills"):
        for name in sorted(guru_owned):
            if path_exists(target / root / name):
                report["guru_refreshed"].append(f"{root}/{name}")

    conflict_root = backup / "conflicts/skills"
    mirrored_sources: dict[str, Path] = {}
    for root in (".agents/skills", ".claude/skills"):
        old_root = original / root
        if not old_root.is_dir():
            continue
        for child in sorted(old_root.iterdir(), key=lambda item: item.name):
            key = (root, child.name)
            if key in official_owned or child.name in guru_owned:
                continue
            previous = mirrored_sources.get(child.name)
            if previous is None:
                mirrored_sources[child.name] = child
            elif not paths_equal(previous, child, ignore_noise=True):
                save_conflict(previous, child, conflict_root / "preexisting-mirror", Path(child.name))
                report["conflicts"].append(
                    {"path": f".agents/.claude mirror/{child.name}", "target_winner": ".agents if present"}
                )
                if root == ".agents/skills":
                    mirrored_sources[child.name] = child
    for name, source in sorted(mirrored_sources.items()):
        for root in (".agents/skills", ".claude/skills"):
            label = f"{root}/{name}"
            reconcile_one_project_skill(source, target / label, label, conflict_root, report)

    for root in SKILL_ROOTS:
        if root in {".agents/skills", ".claude/skills"}:
            continue
        old_root = original / root
        if not old_root.is_dir():
            continue
        for child in sorted(old_root.iterdir(), key=lambda item: item.name):
            if (root, child.name) in official_owned:
                continue
            label = f"{root}/{child.name}"
            reconcile_one_project_skill(child, target / label, label, conflict_root, report)

    agents = target / ".agents/skills"
    claude = target / ".claude/skills"
    if path_digest(agents, ignore_noise=True) != path_digest(claude, ignore_noise=True):
        fail("post-install skill invariant failed: .agents/skills != .claude/skills")
    write_json(backup / "skill-reconcile-report.json", report)
    return report


def verify_codex_policy(target: Path) -> None:
    config = target / ".trellis/config.yaml"
    expected = {
        ("guru", "supervision", "provider"): "codex",
        ("guru", "supervision", "high_risk_review_provider_policy"): "codex",
        ("guru", "supervision", "adversarial_enabled"): "false",
    }
    for path, wanted in expected.items():
        actual = parse_simple_yaml_scalar(config, path)
        if actual != wanted:
            fail(f"config {'.'.join(path)}={actual!r}; expected {wanted!r}")


def verify_route_matrix(target: Path) -> None:
    resolver = target / ".trellis/scripts/guru/guru_delivery_policy.py"
    cases = {
        "small_inline": ["--description", "fix typo in button label text", "--path", "lib/ui/title.dart"],
        "micro_task": [
            "--description",
            "change local button behavior",
            "--path",
            "lib/ui/button.dart",
            "--commit-requested",
            "--max-files",
            "1",
            "--requirements-clear",
            "--coupling",
            "local",
            "--reversible",
            "--verification-scope",
            "focused",
        ],
        "lite_task": [
            "--description",
            "change local button behavior",
            "--commit-requested",
        ],
        "full_chain": [
            "--description",
            "change workflow hook gate runtime",
            "--path",
            ".trellis/workflow.md",
            "--commit-requested",
        ],
    }
    for expected, args in cases.items():
        result = run(["python3", str(resolver), *args], cwd=target, capture=True)
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            fail(f"route smoke returned invalid JSON for {expected}: {error}")
        if parsed.get("execution_route") != expected:
            fail(f"route smoke expected {expected}, got {parsed.get('execution_route')}")


def verify_current_overlay(target: Path, repo_root: Path, platform: str) -> None:
    overlay = repo_root / "guru-template/overlay"
    target_verify = target / ".trellis/scripts/guru"
    runtime_sources = [
        overlay / "verify/guru_gate.py",
        overlay / "verify/guru_risk.py",
        overlay / "verify/guru_contract.py",
        overlay / "verify/guru_delivery_policy.py",
        overlay / "verify/guru_review_record.py",
        overlay / "hooks/guru_after_create.py",
        overlay / "hooks/guru_after_start.py",
        overlay / "hooks/guru_task.py",
        overlay / "verify/guru_config_patch.py",
        overlay / "verify/guru_supervise.py",
    ]
    expected_names = {source.name for source in runtime_sources}
    actual_names = {path.name for path in target_verify.glob("*.py")}
    if actual_names != expected_names:
        fail(
            "target Guru runtime inventory mismatch: "
            f"missing={sorted(expected_names - actual_names)} extra={sorted(actual_names - expected_names)}"
        )
    for source in runtime_sources:
        destination = target_verify / source.name
        if not destination.is_file() or sha256_file(source) != sha256_file(destination):
            fail(f"target Guru runtime differs from current checkout: {destination}")
        compile(source.read_text(encoding="utf-8"), str(source), "exec")
        compile(destination.read_text(encoding="utf-8"), str(destination), "exec")
    source_policy = overlay / "policy/delivery-policy.json"
    target_policy = target / ".trellis/policy/delivery-policy.json"
    if not target_policy.is_file() or sha256_file(source_policy) != sha256_file(target_policy):
        fail("target delivery policy differs from current checkout")
    _, workflow_name = PLATFORM_SPECS[platform]
    source_workflow = repo_root / "guru-template/workflows" / workflow_name
    if sha256_file(source_workflow) != sha256_file(target / ".trellis/workflow.md"):
        fail("target workflow differs from current checkout")
    version = (target / ".trellis/.version").read_text(encoding="utf-8").strip()
    if version != OFFICIAL_VERSION:
        fail(f"target .trellis/.version is {version!r}, expected {OFFICIAL_VERSION}")


def verify_task_readback(target: Path) -> None:
    clean_env = os.environ.copy()
    for name in (
        "TRELLIS_CONTEXT_ID",
        "OPENCODE_RUN_ID",
        "CODEX_THREAD_ID",
        "CLAUDE_SESSION_ID",
    ):
        clean_env.pop(name, None)
    run(["python3", ".trellis/scripts/task.py", "list"], cwd=target, env=clean_env, capture=True)
    run(["python3", ".trellis/scripts/get_context.py"], cwd=target, env=clean_env, capture=True)


def maybe_fail_for_test(phase: str) -> None:
    if os.environ.get("GURU_REINSTALL_TEST_FAIL_AT") == phase:
        fail(f"forced test failure at phase {phase}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="reinstall-official-067.sh",
        description="Reinstall exact official Trellis 0.6.7 plus this checkout's Guru Custom overlay."
    )
    parser.add_argument("target", help="target Git/Trellis repository root")
    parser.add_argument("--platform", choices=sorted(PLATFORM_SPECS), help="override detected Guru platform")
    parser.add_argument("--dry-run", action="store_true", help="validate and print the plan without target/backup mutation")
    parser.add_argument("--backup-dir", help="external missing-or-empty backup directory")
    parser.add_argument("--keep-backup", action="store_true", help="keep the successful external snapshot and reports")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    # Read-only Git probes must not refresh index stat-cache bytes.
    os.environ["GIT_OPTIONAL_LOCKS"] = "0"
    script_dir = Path(os.environ["GURU_REINSTALL_SCRIPT_DIR"]).resolve()
    repo_root = script_dir.parent.parent.resolve()
    overlay_script = script_dir / "apply.sh"
    target = Path(args.target).expanduser().resolve()
    requested_backup = validate_backup_path(target, Path(args.backup_dir) if args.backup_dir else None)

    for command in ("bash", "git", "node", "npm", "python3"):
        require_command(command)
    if not target.is_dir():
        fail(f"target directory does not exist: {target}")
    if target in {Path("/").resolve(), Path.home().resolve()}:
        fail(f"unsafe target directory: {target}")
    if target == repo_root:
        fail("target must not be this Guru source checkout")
    if not path_exists(target / ".git"):
        fail(f"target is not a Git repository root: {target}")
    if target_git_root(target) != target:
        fail(f"target must be the Git top-level directory: {target}")
    if not overlay_script.is_file():
        fail(f"current checkout overlay is missing: {overlay_script}")

    hashes = load_hashes(target)
    platform = detect_platform(target, args.platform)
    clients = detect_clients(hashes)
    developer = original_developer(target)
    scopes = managed_scopes(hashes)
    source_commit = run(["git", "-C", str(repo_root), "rev-parse", "HEAD"], capture=True).stdout.strip()
    index_before = git_index_digest(target)

    work_root = Path(tempfile.mkdtemp(prefix="guru-reinstall-067-work-"))
    backup: Path | None = None
    snapshot: dict[str, Any] | None = None
    mutation_started = False
    completed = False
    try:
        official_binary, official_env = install_official_prefix(work_root)
        run(["bash", str(overlay_script), "--plan", str(target), platform])
        log(f"plan target={target}")
        log(f"plan platform={platform} official={OFFICIAL_PACKAGE}@{OFFICIAL_VERSION}")
        log(f"plan clients={' '.join(clients)}")
        log("plan preserve=.trellis/tasks,.trellis/workspace,project Spec,project Skills")
        log("plan replace=.trellis/scripts,.trellis/workflow.md,.trellis/.runtime,official/Guru managed Skills")
        log("plan global_skill_roots_touched=false claude_invocation=false git_index_write=false")
        if args.dry_run:
            log("DRY_RUN_OK target and backup state were not modified")
            return 0

        backup = create_backup_path(target, requested_backup)
        snapshot = create_snapshot(target, backup, scopes, index_before, hashes, source_commit)
        mutation_started = True

        uninstall_env = official_env.copy()
        uninstall_env["TRELLIS_ALLOW_DIRTY_UNINSTALL"] = "1"
        run([str(official_binary), "uninstall", "--yes"], cwd=target, env=uninstall_env)
        verify_uninstalled(target, hashes)
        verify_git_index_unchanged(target, index_before, "official uninstall")
        clear_project_skill_roots(target)
        maybe_fail_for_test("after-uninstall")

        init_command = [str(official_binary), "init", "--yes", "--force", *clients]
        if developer:
            init_command.extend(["--user", developer])
        run(init_command, cwd=target, env=official_env)
        verify_git_index_unchanged(target, index_before, "official init")
        write_codex_policy(target / ".trellis/config.yaml")
        maybe_fail_for_test("after-init")

        overlay_env = official_env.copy()
        overlay_env["GURU_ADVERSARIAL_ENABLED"] = "false"
        run(
            [
                "bash",
                str(overlay_script),
                str(target),
                platform,
            ],
            env=overlay_env,
        )
        verify_git_index_unchanged(target, index_before, "Guru overlay apply")
        maybe_fail_for_test("after-overlay")

        restore_exact_data(target, backup, snapshot)
        root_document_report = reconcile_root_documents(target, backup)
        spec_report = reconcile_spec(target, backup)
        skill_report = reconcile_skills(target, backup, hashes, script_dir)
        verify_git_index_unchanged(target, index_before, "project-data reconciliation")
        maybe_fail_for_test("after-reconcile")

        verify_codex_policy(target)
        verify_task_readback(target)
        verify_route_matrix(target)
        verify_current_overlay(target, repo_root, platform)
        run([str(official_binary), "uninstall", "--dry-run"], cwd=target, env=official_env, capture=True)
        if git_index_digest(target) != index_before:
            fail("final verification detected a changed .git/index")

        conflicts = len(spec_report["conflicts"]) + len(skill_report["conflicts"])
        result = {
            "status": "candidate usable" if conflicts == 0 else "candidate usable with manual reconciliation",
            "official": f"{OFFICIAL_PACKAGE}@{OFFICIAL_VERSION}",
            "source_commit": source_commit,
            "target": str(target),
            "platform": platform,
            "tasks_digest": snapshot["tasks_digest"],
            "workspace_digest": snapshot["workspace_digest"],
            "spec_conflicts": len(spec_report["conflicts"]),
            "skill_conflicts": len(skill_report["conflicts"]),
            "root_documents_restored": root_document_report["external_content_restored"],
            "claude_invoked": False,
            "global_skill_roots_touched": False,
            "git_index_unchanged": True,
            "rollback_mode": "external-managed-snapshot-v1",
            "backup": str(backup),
        }
        write_json(backup / "reinstall-result.json", result)
        completed = True
        log(json.dumps(result, ensure_ascii=False, sort_keys=True))

        if conflicts:
            log(f"REINSTALL_CONFLICTS: reports retained at {backup}")
            return CONFLICT_EXIT
        if args.keep_backup:
            log(f"REINSTALL_OK: backup retained at {backup}")
        else:
            shutil.rmtree(backup)
            log("REINSTALL_OK: verified backup removed (use --keep-backup to retain it)")
        return 0
    except Exception as error:
        sys.stderr.write(f"REINSTALL_FAILED: {error}\n")
        if mutation_started and not completed and backup is not None and snapshot is not None:
            try:
                restore_snapshot(target, backup, snapshot)
            except Exception as rollback_error:
                sys.stderr.write(f"ROLLBACK_FAILED: {rollback_error}\n")
                return ROLLBACK_FAILURE_EXIT
            sys.stderr.write(f"ROLLBACK_OK: original state restored; evidence retained at {backup}\n")
        return 1
    finally:
        shutil.rmtree(work_root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
PY
