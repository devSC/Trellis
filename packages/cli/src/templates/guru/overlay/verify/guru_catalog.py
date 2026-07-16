#!/usr/bin/env python3
"""Fail-closed resolver for the dedicated Guru workflow/spec registry."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Protocol


EXPECTED_SPEC_IDS = (
    "guru-flutter-client",
    "guru-go-backend",
    "guru-h5-web",
    "guru-ios-native",
)
EXPECTED_WORKFLOW_IDS = (
    "guru-client",
    "guru-go",
    "guru-h5",
    "guru-ios",
)
EXPECTED_TEMPLATE_IDS = EXPECTED_SPEC_IDS + EXPECTED_WORKFLOW_IDS

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_WINDOWS_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:/")
_TOP_LEVEL_FIELDS = frozenset(("version", "templates"))
_ENTRY_FIELDS = frozenset(("id", "type", "name", "description", "path", "tags"))
_REQUIRED_ENTRY_FIELDS = frozenset(("id", "type", "name", "path"))
_BLANK_FALLBACK_MARKER = "falling back to blank templates"
_BUNDLED_FALLBACK_MARKER = "bundled guru"


class CatalogError(RuntimeError):
    """Base error for catalog and exact-official preflight failures."""


class CatalogRootInvalid(CatalogError):
    pass


class CatalogSchemaInvalid(CatalogError):
    pass


class TemplateIdDuplicate(CatalogSchemaInvalid):
    pass


class TemplatePathInvalid(CatalogError):
    pass


class TemplateMissing(CatalogError):
    pass


class SourceUnavailable(CatalogError):
    pass


class OfficialPackageMismatch(CatalogError):
    pass


class FallbackAttempted(CatalogError):
    pass


class HermeticFixtureInvalid(CatalogError):
    pass


class TemplateKind(str, Enum):
    WORKFLOW = "workflow"
    SPEC = "spec"


@dataclass(frozen=True)
class CatalogEntry:
    template_id: str
    kind: TemplateKind
    name: str
    description: str | None
    relative_path: PurePosixPath
    tags: tuple[str, ...]


@dataclass(frozen=True)
class CatalogV1:
    registry_root: Path
    root_identity: tuple[int, int]
    source_digest: str
    entries: tuple[CatalogEntry, ...]

    def entry(self, template_id: str) -> CatalogEntry:
        for candidate in self.entries:
            if candidate.template_id == template_id:
                return candidate
        raise CatalogSchemaInvalid(f'unknown Guru template id "{template_id}"')


@dataclass(frozen=True)
class ResolvedTemplate:
    entry: CatalogEntry
    registry_root: Path
    source_ref: str
    files: tuple[PurePosixPath, ...]
    content_digest: str


@dataclass(frozen=True)
class OfficialInstallObservation:
    raw_returncode: int
    raw_stdout: str
    raw_stderr: str
    staging_tree_digest: str
    blank_fallback_observed: bool
    bundled_fallback_observed: bool
    succeeded: bool
    failure_kind: str | None


class OfficialCatalogSource(Protocol):
    def materialize(self, source_ref: str) -> Path:
        """Return a dedicated registry root for exactly source_ref."""


@dataclass(frozen=True)
class _FileSnapshot:
    relative_path: PurePosixPath
    identity: tuple[int, ...]
    content: bytes


@dataclass(frozen=True)
class _ScannedNode:
    name: str
    identity: tuple[int, ...]


@dataclass(frozen=True)
class _InventoryNode:
    relative_path: PurePosixPath
    identity: tuple[int, ...]


class CatalogResolver:
    """Load and resolve the heterogeneous Guru marketplace catalog."""

    def load(self, registry_root: Path) -> CatalogV1:
        root = _validated_registry_root(registry_root)
        root_fd, root_identity = _open_bound_root_fd(root)
        try:
            raw = _read_fenced_file(
                root_fd,
                PurePosixPath("index.json"),
                missing_error=TemplateMissing,
            )
            parsed = _parse_catalog_json(raw)
            entries = _parse_entries(parsed["templates"])
            _require_stable_inventory(entries)
            ordered = tuple(entries[template_id] for template_id in EXPECTED_TEMPLATE_IDS)
            for entry in ordered:
                _collect_entry_files(root_fd, entry)
            if _read_fenced_file(
                root_fd,
                PurePosixPath("index.json"),
                missing_error=TemplateMissing,
            ) != raw:
                raise CatalogSchemaInvalid("catalog index changed while the pinned snapshot was loaded")
            _assert_root_path_identity(root, root_identity)
            return CatalogV1(
                registry_root=root,
                root_identity=root_identity,
                source_digest=hashlib.sha256(raw).hexdigest(),
                entries=ordered,
            )
        finally:
            os.close(root_fd)

    def resolve(
        self,
        catalog: CatalogV1,
        template_id: str,
        source_ref: str,
    ) -> ResolvedTemplate:
        _validate_source_ref(source_ref)
        root_fd, root_identity = _open_bound_root_fd(
            catalog.registry_root,
            expected_identity=catalog.root_identity,
        )
        try:
            current_index = _read_fenced_file(
                root_fd,
                PurePosixPath("index.json"),
                missing_error=TemplateMissing,
            )
            current_digest = hashlib.sha256(current_index).hexdigest()
            if current_digest != catalog.source_digest:
                raise CatalogSchemaInvalid("catalog index changed after load; reload before resolving")
            entry = catalog.entry(template_id)
            snapshots = _collect_entry_files(root_fd, entry)
            if _read_fenced_file(
                root_fd,
                PurePosixPath("index.json"),
                missing_error=TemplateMissing,
            ) != current_index:
                raise CatalogSchemaInvalid("catalog index changed while the pinned snapshot was resolved")
            digest = hashlib.sha256()
            _hash_field(digest, b"guru-catalog-content-v1")
            _hash_field(digest, entry.kind.value.encode("ascii"))
            _hash_field(digest, source_ref.encode("utf-8"))
            for snapshot in snapshots:
                _hash_field(digest, snapshot.relative_path.as_posix().encode("utf-8"))
                _hash_field(digest, snapshot.content)
            _assert_root_path_identity(catalog.registry_root, root_identity)
            return ResolvedTemplate(
                entry=entry,
                registry_root=catalog.registry_root,
                source_ref=source_ref,
                files=tuple(snapshot.relative_path for snapshot in snapshots),
                content_digest=digest.hexdigest(),
            )
        finally:
            os.close(root_fd)

    def verify_all(self, catalog: CatalogV1, source_ref: str) -> tuple[ResolvedTemplate, ...]:
        return tuple(self.resolve(catalog, entry.template_id, source_ref) for entry in catalog.entries)

    def resolve_official(
        self,
        source: OfficialCatalogSource,
        template_id: str,
        source_ref: str,
    ) -> ResolvedTemplate:
        """Resolve through one official source; no bundled source is accepted or consulted."""
        _validate_source_ref(source_ref)
        try:
            registry_root = source.materialize(source_ref)
        except SourceUnavailable:
            raise
        except OSError as error:
            raise SourceUnavailable(
                f'official source unavailable for immutable ref "{source_ref}": {error}'
            ) from error
        loaded = self.load(registry_root)
        return self.resolve(loaded, template_id, source_ref)


def observe_official_install(
    *,
    returncode: int,
    stdout: str,
    stderr: str,
    staging_root: Path,
) -> OfficialInstallObservation:
    """Preserve raw official output and normalize observed fallback to failure.

    A positive result only means the raw command may proceed to wrapper-owned
    postcondition checks. It is not proof that Template installation succeeded.
    """
    combined = f"{stdout}\n{stderr}".lower()
    blank_fallback = _BLANK_FALLBACK_MARKER in combined
    bundled_fallback = _BUNDLED_FALLBACK_MARKER in combined
    if blank_fallback:
        failure_kind = "OfficialBlankFallback"
    elif bundled_fallback:
        failure_kind = "FallbackAttempted"
    elif returncode != 0:
        failure_kind = "OfficialCommandFailed"
    else:
        failure_kind = None
    try:
        staging_digest = directory_digest(staging_root)
    except (OSError, CatalogError):
        staging_digest = ""
        if failure_kind is None:
            failure_kind = "OfficialStagingInvalid"
    return OfficialInstallObservation(
        raw_returncode=returncode,
        raw_stdout=stdout,
        raw_stderr=stderr,
        staging_tree_digest=staging_digest,
        blank_fallback_observed=blank_fallback,
        bundled_fallback_observed=bundled_fallback,
        succeeded=failure_kind is None,
        failure_kind=failure_kind,
    )


def directory_digest(root: Path) -> str:
    """Return a deterministic SHA-256 for one symlink-free directory tree."""
    path = Path(root)
    if path.is_symlink() or not path.exists() or not path.is_dir():
        raise TemplatePathInvalid(f"directory digest root is invalid: {path}")
    canonical = path.resolve(strict=True)
    root_fd, root_identity = _open_bound_root_fd(canonical)
    try:
        snapshots = _collect_regular_tree(root_fd, PurePosixPath())
        digest = hashlib.sha256()
        _hash_field(digest, b"guru-directory-v1")
        for snapshot in snapshots:
            _hash_field(digest, snapshot.relative_path.as_posix().encode("utf-8"))
            _hash_field(digest, snapshot.content)
        _assert_root_path_identity(canonical, root_identity)
        return digest.hexdigest()
    finally:
        os.close(root_fd)


def compare_directories(expected: Path, actual: Path) -> bool:
    return directory_digest(expected) == directory_digest(actual)


def _validated_registry_root(registry_root: Path) -> Path:
    requested = Path(registry_root)
    if requested.is_symlink():
        raise CatalogRootInvalid(f"dedicated registry root must not be a symlink: {requested}")
    if not requested.exists() or not requested.is_dir():
        raise CatalogRootInvalid(f"dedicated registry root is missing or not a directory: {requested}")
    try:
        return requested.resolve(strict=True)
    except OSError as error:
        raise CatalogRootInvalid(f"cannot resolve dedicated registry root {requested}: {error}") from error


def _parse_catalog_json(raw: bytes) -> dict[str, Any]:
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CatalogSchemaInvalid(f"index.json is not valid UTF-8 JSON: {error}") from error
    if not isinstance(parsed, dict):
        raise CatalogSchemaInvalid("index.json root must be an object")
    unknown = set(parsed) - _TOP_LEVEL_FIELDS
    missing = _TOP_LEVEL_FIELDS - set(parsed)
    if unknown or missing:
        raise CatalogSchemaInvalid(
            f"index.json fields invalid; missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    if type(parsed["version"]) is not int or parsed["version"] != 1:
        raise CatalogSchemaInvalid("index.json version must be integer 1")
    if not isinstance(parsed["templates"], list):
        raise CatalogSchemaInvalid("index.json templates must be an array")
    return parsed


def _parse_entries(raw_entries: list[Any]) -> dict[str, CatalogEntry]:
    parsed: dict[str, CatalogEntry] = {}
    conflicts: set[str] = set()
    for index, raw in enumerate(raw_entries):
        pointer = f"/templates/{index}"
        if not isinstance(raw, dict):
            raise CatalogSchemaInvalid(f"{pointer} must be an object")
        unknown = set(raw) - _ENTRY_FIELDS
        missing = _REQUIRED_ENTRY_FIELDS - set(raw)
        if unknown or missing:
            raise CatalogSchemaInvalid(
                f"{pointer} fields invalid; missing={sorted(missing)}, unknown={sorted(unknown)}"
            )
        template_id = _require_string(raw["id"], f"{pointer}/id")
        if not _ID_PATTERN.fullmatch(template_id) or not template_id.isascii():
            raise CatalogSchemaInvalid(f"{pointer}/id must be a stable lowercase ASCII id")
        kind_raw = _require_string(raw["type"], f"{pointer}/type")
        try:
            kind = TemplateKind(kind_raw)
        except ValueError as error:
            raise CatalogSchemaInvalid(f"{pointer}/type must be workflow or spec") from error
        name = _require_string(raw["name"], f"{pointer}/name")
        description_raw = raw.get("description")
        if description_raw is not None and not isinstance(description_raw, str):
            raise CatalogSchemaInvalid(f"{pointer}/description must be a string when present")
        tags_raw = raw.get("tags", [])
        if not isinstance(tags_raw, list) or not all(
            isinstance(item, str) and item for item in tags_raw
        ):
            raise CatalogSchemaInvalid(f"{pointer}/tags must be an array of non-empty strings")
        relative_path = _parse_relative_path(
            _require_string(raw["path"], f"{pointer}/path"),
            template_id,
        )
        if template_id in parsed:
            conflicts.add(template_id)
            continue
        parsed[template_id] = CatalogEntry(
            template_id=template_id,
            kind=kind,
            name=name,
            description=description_raw,
            relative_path=relative_path,
            tags=tuple(tags_raw),
        )
    if conflicts:
        raise TemplateIdDuplicate(f"duplicate template ids: {', '.join(sorted(conflicts))}")
    return parsed


def _require_stable_inventory(entries: dict[str, CatalogEntry]) -> None:
    actual = set(entries)
    expected = set(EXPECTED_TEMPLATE_IDS)
    if actual != expected:
        raise CatalogSchemaInvalid(
            f"Guru registry inventory mismatch; missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )
    for template_id in EXPECTED_SPEC_IDS:
        if entries[template_id].kind is not TemplateKind.SPEC:
            raise CatalogSchemaInvalid(f'{template_id} must have type "spec"')
    for template_id in EXPECTED_WORKFLOW_IDS:
        if entries[template_id].kind is not TemplateKind.WORKFLOW:
            raise CatalogSchemaInvalid(f'{template_id} must have type "workflow"')


def _parse_relative_path(raw_path: str, template_id: str) -> PurePosixPath:
    if not raw_path or not raw_path.isascii() or any(ord(character) < 32 for character in raw_path):
        raise TemplatePathInvalid(f"{template_id} path must be non-empty printable ASCII")
    if "\\" in raw_path:
        raise TemplatePathInvalid(f"{template_id} path must use POSIX separators")
    if raw_path.startswith("/") or _WINDOWS_DRIVE_PATTERN.match(raw_path):
        raise TemplatePathInvalid(f"{template_id} path must be repository-relative")
    parts = raw_path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise TemplatePathInvalid(f"{template_id} path must be canonical without empty, dot, or parent parts")
    parsed = PurePosixPath(raw_path)
    if parsed.is_absolute():
        raise TemplatePathInvalid(f"{template_id} path must be repository-relative")
    return parsed


def _collect_entry_files(root_fd: int, entry: CatalogEntry) -> tuple[_FileSnapshot, ...]:
    if entry.kind is TemplateKind.WORKFLOW:
        if entry.relative_path.suffix != ".md":
            raise TemplatePathInvalid(f"{entry.template_id} workflow path must end in .md")
        snapshot = _read_file_snapshot(
            root_fd,
            entry.relative_path,
            label=entry.template_id,
            missing_error=TemplateMissing,
        )
        return (snapshot,)
    snapshots = _collect_regular_tree(root_fd, entry.relative_path)
    if not snapshots:
        raise TemplateMissing(f"{entry.template_id} spec directory contains no regular files")
    return snapshots


def _collect_regular_tree(root_fd: int, relative_root: PurePosixPath) -> tuple[_FileSnapshot, ...]:
    inventory = _collect_tree_inventory(root_fd, relative_root)
    snapshots = _read_inventory_snapshots(root_fd, inventory)
    if _collect_tree_inventory(root_fd, relative_root) != inventory:
        raise TemplatePathInvalid(
            f"template tree changed while pinned snapshot was read: {relative_root.as_posix()}"
        )
    return snapshots


def _collect_tree_inventory(
    root_fd: int,
    relative_root: PurePosixPath,
) -> tuple[_InventoryNode, ...]:
    directory_fd = _open_directory_path_fd(
        root_fd,
        relative_root,
        label=relative_root.as_posix(),
        missing_error=TemplateMissing,
    )
    inventory: list[_InventoryNode] = []
    try:
        _walk_tree_inventory(directory_fd, relative_root, inventory)
        return tuple(sorted(inventory, key=lambda item: item.relative_path.as_posix()))
    finally:
        os.close(directory_fd)


def _walk_tree_inventory(
    directory_fd: int,
    relative_root: PurePosixPath,
    inventory: list[_InventoryNode],
) -> None:
    before = _scan_directory_fd(directory_fd, relative_root)
    for node in before:
        relative_path = relative_root / node.name
        mode = node.identity[2]
        if stat.S_ISLNK(mode):
            raise TemplatePathInvalid(f"symlink is not allowed in template tree: {relative_path}")
        inventory.append(_InventoryNode(relative_path, node.identity))
        if stat.S_ISDIR(mode):
            child_fd = _open_directory_component(
                directory_fd,
                node.name,
                relative_path.as_posix(),
                TemplateMissing,
            )
            try:
                _require_same_identity(child_fd, node.identity, relative_path)
                _walk_tree_inventory(child_fd, relative_path, inventory)
            finally:
                os.close(child_fd)
            continue
        if not stat.S_ISREG(mode):
            raise TemplatePathInvalid(f"non-regular template entry is not allowed: {relative_path}")
    if _scan_directory_fd(directory_fd, relative_root) != before:
        raise TemplatePathInvalid(f"template directory changed while inventory was collected: {relative_root}")


def _read_inventory_snapshots(
    root_fd: int,
    inventory: tuple[_InventoryNode, ...],
) -> tuple[_FileSnapshot, ...]:
    snapshots: list[_FileSnapshot] = []
    for node in inventory:
        if stat.S_ISDIR(node.identity[2]):
            continue
        snapshot = _read_file_snapshot(
            root_fd,
            node.relative_path,
            label=node.relative_path.as_posix(),
            missing_error=TemplateMissing,
        )
        if snapshot.identity != node.identity:
            raise TemplatePathInvalid(
                f"template entry changed while pinned snapshot was read: {node.relative_path}"
            )
        snapshots.append(snapshot)
    return tuple(snapshots)


def _read_fenced_file(
    root_fd: int,
    relative_path: PurePosixPath,
    *,
    missing_error: type[CatalogError] = TemplatePathInvalid,
) -> bytes:
    return _read_file_snapshot(
        root_fd,
        relative_path,
        label=relative_path.as_posix(),
        missing_error=missing_error,
    ).content


def _read_file_snapshot(
    root_fd: int,
    relative_path: PurePosixPath,
    *,
    label: str,
    missing_error: type[CatalogError],
) -> _FileSnapshot:
    first = _read_file_snapshot_once(
        root_fd,
        relative_path,
        label=label,
        missing_error=missing_error,
    )
    second = _read_file_snapshot_once(
        root_fd,
        relative_path,
        label=label,
        missing_error=missing_error,
    )
    if first != second:
        raise TemplatePathInvalid(f"template file changed while pinned snapshot was read: {relative_path}")
    return first


def _read_file_snapshot_once(
    root_fd: int,
    relative_path: PurePosixPath,
    *,
    label: str,
    missing_error: type[CatalogError],
) -> _FileSnapshot:
    if not relative_path.parts:
        raise TemplatePathInvalid(f"template file path is empty: {label}")
    parent_path = PurePosixPath(*relative_path.parts[:-1])
    parent_fd = _open_directory_path_fd(
        root_fd,
        parent_path,
        label=label,
        missing_error=missing_error,
    )
    try:
        before = _scan_directory_fd(parent_fd, parent_path)
        expected = next((node for node in before if node.name == relative_path.parts[-1]), None)
        if expected is None:
            raise missing_error(f"template path does not exist: {label}")
        if not stat.S_ISREG(expected.identity[2]):
            raise TemplatePathInvalid(f"template leaf is not one regular file: {label}")
        leaf_fd = _open_leaf_fd(parent_fd, expected.name, label, missing_error)
        try:
            snapshot = _read_open_file(
                leaf_fd,
                relative_path,
                expected_identity=expected.identity,
            )
        finally:
            os.close(leaf_fd)
        if _scan_directory_fd(parent_fd, parent_path) != before:
            raise TemplatePathInvalid(f"template directory changed while being read: {parent_path}")
        return snapshot
    finally:
        os.close(parent_fd)


def _read_open_file(
    file_descriptor: int,
    relative_path: PurePosixPath,
    *,
    expected_identity: tuple[int, ...],
) -> _FileSnapshot:
    _require_same_identity(file_descriptor, expected_identity, relative_path)
    chunks: list[bytes] = []
    try:
        while True:
            chunk = os.read(file_descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
    except OSError as error:
        raise TemplatePathInvalid(f"cannot read pinned template file {relative_path}: {error}") from error
    _require_same_identity(file_descriptor, expected_identity, relative_path)
    return _FileSnapshot(
        relative_path=relative_path,
        identity=expected_identity,
        content=b"".join(chunks),
    )


def _scan_directory_fd(
    directory_fd: int,
    relative_root: PurePosixPath,
) -> tuple[_ScannedNode, ...]:
    _require_descriptor_fencing()
    try:
        with os.scandir(directory_fd) as iterator:
            entries = sorted(iterator, key=lambda item: item.name)
        nodes = []
        for entry in entries:
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as error:
                raise TemplatePathInvalid(
                    f"cannot inspect template entry {relative_root / entry.name}: {error}"
                ) from error
            nodes.append(_ScannedNode(entry.name, _metadata_identity(metadata)))
        return tuple(nodes)
    except CatalogError:
        raise
    except OSError as error:
        raise TemplatePathInvalid(
            f"cannot enumerate pinned template directory {relative_root}: {error}"
        ) from error


def _require_descriptor_fencing() -> None:
    required_flags = ("O_DIRECTORY", "O_NOFOLLOW")
    missing_flags = [name for name in required_flags if not hasattr(os, name)]
    if missing_flags or os.open not in os.supports_dir_fd or os.scandir not in os.supports_fd:
        detail = ", ".join(missing_flags) if missing_flags else "dir_fd/scandir-fd"
        raise TemplatePathInvalid(f"descriptor-based path fencing is unavailable: {detail}")


def _directory_open_flags() -> int:
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _leaf_open_flags() -> int:
    return (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )


def _open_root_fd(root: Path) -> int:
    _require_descriptor_fencing()
    path = Path(root)
    if not path.is_absolute():
        raise CatalogRootInvalid(f"dedicated registry root must be absolute before descriptor fencing: {path}")
    try:
        descriptor = os.open(path.anchor, _directory_open_flags())
    except OSError as error:
        raise CatalogRootInvalid(f"cannot open filesystem root for dedicated registry {path}: {error}") from error
    try:
        for component in path.parts[1:]:
            try:
                next_descriptor = os.open(
                    component,
                    _directory_open_flags(),
                    dir_fd=descriptor,
                )
            except OSError as error:
                raise CatalogRootInvalid(
                    f"cannot open dedicated registry root without following any path component: "
                    f"{path}: {error}"
                ) from error
            os.close(descriptor)
            descriptor = next_descriptor
    except BaseException:
        os.close(descriptor)
        raise
    try:
        metadata = os.fstat(descriptor)
    except OSError as error:
        os.close(descriptor)
        raise CatalogRootInvalid(f"cannot inspect pinned registry root {path}: {error}") from error
    if not stat.S_ISDIR(metadata.st_mode):
        os.close(descriptor)
        raise CatalogRootInvalid(f"dedicated registry root is not a pinned directory: {path}")
    return descriptor


def _open_bound_root_fd(
    root: Path,
    *,
    expected_identity: tuple[int, int] | None = None,
) -> tuple[int, tuple[int, int]]:
    descriptor = _open_root_fd(root)
    identity = _root_identity(descriptor)
    if expected_identity is not None and identity != expected_identity:
        os.close(descriptor)
        raise CatalogRootInvalid(
            f"dedicated registry root identity changed; reload before resolving: {root}"
        )
    return descriptor, identity


def _assert_root_path_identity(root: Path, expected_identity: tuple[int, int]) -> None:
    descriptor = _open_root_fd(root)
    try:
        if _root_identity(descriptor) != expected_identity:
            raise CatalogRootInvalid(f"dedicated registry root changed during pinned read: {root}")
    finally:
        os.close(descriptor)


def _root_identity(descriptor: int) -> tuple[int, int]:
    try:
        metadata = os.fstat(descriptor)
    except OSError as error:
        raise CatalogRootInvalid(f"cannot inspect pinned registry root descriptor: {error}") from error
    return (metadata.st_dev, metadata.st_ino)


def _metadata_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _require_same_identity(
    descriptor: int,
    expected_identity: tuple[int, ...],
    relative_path: PurePosixPath,
) -> None:
    try:
        current = _metadata_identity(os.fstat(descriptor))
    except OSError as error:
        raise TemplatePathInvalid(f"cannot inspect pinned template entry {relative_path}: {error}") from error
    if current != expected_identity:
        raise TemplatePathInvalid(f"template entry changed while pinned snapshot was read: {relative_path}")


def _open_directory_component(
    parent_fd: int,
    component: str,
    label: str,
    missing_error: type[CatalogError],
) -> int:
    try:
        descriptor = os.open(component, _directory_open_flags(), dir_fd=parent_fd)
    except OSError as error:
        _raise_open_error(error, label, missing_error)
    try:
        metadata = os.fstat(descriptor)
    except OSError as error:
        os.close(descriptor)
        raise TemplatePathInvalid(f"cannot inspect pinned template directory {label}: {error}") from error
    if not stat.S_ISDIR(metadata.st_mode):
        os.close(descriptor)
        raise TemplatePathInvalid(f"template directory component is not a directory: {label}")
    return descriptor


def _open_directory_path_fd(
    root_fd: int,
    relative_path: PurePosixPath,
    *,
    label: str,
    missing_error: type[CatalogError],
) -> int:
    try:
        descriptor = os.dup(root_fd)
    except OSError as error:
        raise CatalogRootInvalid(f"cannot duplicate pinned registry root descriptor: {error}") from error
    try:
        for component in relative_path.parts:
            next_descriptor = _open_directory_component(
                descriptor,
                component,
                label,
                missing_error,
            )
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _open_leaf_fd(
    parent_fd: int,
    leaf: str,
    label: str,
    missing_error: type[CatalogError],
) -> int:
    try:
        descriptor = os.open(leaf, _leaf_open_flags(), dir_fd=parent_fd)
    except OSError as error:
        _raise_open_error(error, label, missing_error)
    try:
        metadata = os.fstat(descriptor)
    except OSError as error:
        os.close(descriptor)
        raise TemplatePathInvalid(f"cannot inspect pinned template leaf {label}: {error}") from error
    if not stat.S_ISREG(metadata.st_mode):
        os.close(descriptor)
        raise TemplatePathInvalid(f"template leaf is not one regular file: {label}")
    return descriptor


def _raise_open_error(
    error: OSError,
    label: str,
    missing_error: type[CatalogError],
) -> None:
    if error.errno == errno.ENOENT:
        raise missing_error(f"template path does not exist: {label}") from error
    if error.errno in (errno.ELOOP, errno.ENOTDIR):
        raise TemplatePathInvalid(f"template path contains a symlink or non-directory component: {label}") from error
    raise TemplatePathInvalid(f"cannot open fenced template path {label}: {error}") from error


def _require_string(value: Any, pointer: str) -> str:
    if not isinstance(value, str) or not value:
        raise CatalogSchemaInvalid(f"{pointer} must be a non-empty string")
    return value


def _validate_source_ref(source_ref: str) -> None:
    if not isinstance(source_ref, str) or not source_ref.strip():
        raise SourceUnavailable("official source ref must be non-empty")
    if source_ref != source_ref.strip() or any(character in source_ref for character in ("\x00", "\r", "\n")):
        raise SourceUnavailable("official source ref contains forbidden whitespace or control characters")


def _hash_field(digest: Any, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, byteorder="big", signed=False))
    digest.update(value)


def _resolved_to_json(resolved: ResolvedTemplate) -> dict[str, Any]:
    return {
        "template_id": resolved.entry.template_id,
        "kind": resolved.entry.kind.value,
        "registry_root": str(resolved.registry_root),
        "source_ref": resolved.source_ref,
        "files": [path.as_posix() for path in resolved.files],
        "content_digest": resolved.content_digest,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify", help="validate and resolve all catalog entries")
    verify.add_argument("registry_root", type=Path)
    verify.add_argument("--source-ref", required=True)

    resolve = subparsers.add_parser("resolve", help="resolve one typed catalog entry")
    resolve.add_argument("registry_root", type=Path)
    resolve.add_argument("template_id")
    resolve.add_argument("--source-ref", required=True)

    digest_tree = subparsers.add_parser("tree-digest", help="digest one symlink-free directory")
    digest_tree.add_argument("root", type=Path)

    compare_tree = subparsers.add_parser("compare-tree", help="compare two directory trees")
    compare_tree.add_argument("expected", type=Path)
    compare_tree.add_argument("actual", type=Path)

    observe = subparsers.add_parser("observe-official", help="normalize a raw official CLI result")
    observe.add_argument("--returncode", required=True, type=int)
    observe.add_argument("--stdout-file", required=True, type=Path)
    observe.add_argument("--stderr-file", required=True, type=Path)
    observe.add_argument("--stage-root", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "tree-digest":
            print(directory_digest(args.root))
            return 0
        if args.command == "compare-tree":
            if not compare_directories(args.expected, args.actual):
                print("TREE_MISMATCH", file=sys.stderr)
                return 4
            print("TREE_MATCH")
            return 0
        if args.command == "observe-official":
            observation = observe_official_install(
                returncode=args.returncode,
                stdout=args.stdout_file.read_text(encoding="utf-8", errors="replace"),
                stderr=args.stderr_file.read_text(encoding="utf-8", errors="replace"),
                staging_root=args.stage_root,
            )
            print(json.dumps(asdict(observation), sort_keys=True))
            return 0 if observation.succeeded else 5
        resolver = CatalogResolver()
        loaded = resolver.load(args.registry_root)
        if args.command == "resolve":
            print(json.dumps(_resolved_to_json(resolver.resolve(loaded, args.template_id, args.source_ref)), sort_keys=True))
            return 0
        resolved = resolver.verify_all(loaded, args.source_ref)
        print(
            json.dumps(
                {
                    "catalog_digest": loaded.source_digest,
                    "templates": [_resolved_to_json(item) for item in resolved],
                },
                sort_keys=True,
            )
        )
        return 0
    except CatalogError as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
