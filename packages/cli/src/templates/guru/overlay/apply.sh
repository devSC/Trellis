#!/usr/bin/env bash
set -euo pipefail
# guru-template overlay 安装/升级器：装配官方 init -t/--workflow 覆盖不到的部分，
# 并负责 guru 定制内容（workflow/harness SSOT/skills/hooks/settings 接线）的后续升级刷新。
# 用法:
#   ./apply.sh --plan <目标项目路径> [flutter|go|ios|h5] [--rollback-bundle <外部目录>]
#   ./apply.sh <目标项目路径> [flutter|go|ios|h5] [--rollback-bundle <外部目录>]
#   ./apply.sh --upgrade <目标项目路径> [flutter|go|ios|h5] --rollback-bundle <新外部目录>
#   ./apply.sh --status <目标项目路径> <rollback-bundle>
#   ./apply.sh --verify <目标项目路径> <rollback-bundle>
#   ./apply.sh --unapply <目标项目路径> <rollback-bundle>
# 前提: 目标项目已 trellis init（存在 .trellis/）。幂等：重复执行不产生额外变化。
#
# 边界（本脚本不做）：
# - CLI core 脚本（task.py 等）：归 trellis update 的 hash 三方合并管理，这里只检测依赖并警告；
# - .codex/skills 项目级内容（如 guru-ai-guides 的 requirement-* 技能）：项目自有，入项目 git 管理；
# - AGENTS.md 项目自有区块（GURU_WITH_GITNEXUS=1 时仅刷新 gitnexus 受管块）。

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"   # guru-template/
APPLY_RECOVERY_ARMED=0
APPLY_RECOVERY_EXPECTED_DIGEST=""
APPLY_RECOVERY_BUNDLE=""

usage() {
  cat <<'EOF'
用法:
  apply.sh --plan <目标项目路径> [flutter|go|ios|h5] [--rollback-bundle <外部目录>]
  apply.sh <目标项目路径> [flutter|go|ios|h5] [--rollback-bundle <外部目录>]
  apply.sh --upgrade <目标项目路径> [flutter|go|ios|h5] --rollback-bundle <新外部目录>
  apply.sh --status <目标项目路径> <rollback-bundle>
  apply.sh --verify <目标项目路径> <rollback-bundle>
  apply.sh --unapply <目标项目路径> <rollback-bundle>

plan/status/verify 只读；upgrade 复用 apply，并要求新的外部 rollback bundle。
EOF
}

tree_digest() { # tree_digest <target>; excludes Git internals by contract
  python3 - "$1" <<'PYEOF'
import hashlib
import os
import stat
import sys

root = os.path.realpath(sys.argv[1])
digest = hashlib.sha256()
for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
    dirnames[:] = sorted(name for name in dirnames if not (dirpath == root and name == ".git"))
    filenames = sorted(name for name in filenames if not (dirpath == root and name == ".git"))
    for name in [*dirnames, *filenames]:
        path = os.path.join(dirpath, name)
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode):
            kind, payload = "link", os.readlink(path).encode("utf-8", "surrogateescape")
        elif stat.S_ISDIR(info.st_mode):
            kind, payload = "dir", b""
        elif stat.S_ISREG(info.st_mode):
            kind = "file"
            with open(path, "rb") as fh:
                payload = fh.read()
        else:
            kind, payload = "other", b""
        digest.update(f"{rel}\0{kind}\0{stat.S_IMODE(info.st_mode):o}\0".encode())
        digest.update(payload)
        digest.update(b"\0")
print(digest.hexdigest())
PYEOF
}

create_rollback_bundle() { # create_rollback_bundle <target> <external-bundle>
  local digest
  digest="$(tree_digest "$1")"
  python3 - "$1" "$2" "$digest" <<'PYEOF'
import json
import os
import shutil
import sys

target = os.path.realpath(sys.argv[1])
bundle_arg = os.path.abspath(sys.argv[2])
if os.path.lexists(bundle_arg) and os.path.islink(bundle_arg):
    raise SystemExit("ERROR: rollback bundle 路径不得是符号链接")
bundle = os.path.realpath(bundle_arg)
digest = sys.argv[3]
try:
    inside_target = os.path.commonpath((target, bundle)) == target
except ValueError:
    inside_target = False
if inside_target:
    raise SystemExit("ERROR: rollback bundle 必须位于目标项目外部")
if os.path.exists(bundle) and not os.path.isdir(bundle):
    raise SystemExit(f"ERROR: rollback bundle 必须是目录: {bundle}")
if os.path.exists(bundle) and os.listdir(bundle):
    raise SystemExit(f"ERROR: rollback bundle 必须不存在或为空: {bundle}")
os.makedirs(bundle, exist_ok=True)
preimage = os.path.join(bundle, "preimage")
shutil.copytree(
    target,
    preimage,
    symlinks=True,
    ignore=lambda path, names: [".git"] if os.path.realpath(path) == target and ".git" in names else [],
)
manifest = {
    "schema_version": 2,
    "state": "prepared",
    "target": target,
    "pre_apply_digest": digest,
    "post_apply_digest": None,
    "git_internals_owned": False,
    "recovery": {
        "status": "armed",
        "expected_target_digest": digest,
    },
}
with open(os.path.join(bundle, "manifest.json"), "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, ensure_ascii=False, indent=2, sort_keys=True)
    fh.write("\n")
PYEOF
}

checkpoint_rollback_bundle() { # checkpoint_rollback_bundle <target> <bundle>
  local digest
  digest="$(tree_digest "$1")"
  python3 - "$1" "$2" "$digest" <<'PYEOF'
import json
import os
import sys

target, bundle, digest = os.path.realpath(sys.argv[1]), os.path.abspath(sys.argv[2]), sys.argv[3]
path = os.path.join(bundle, "manifest.json")
with open(path, encoding="utf-8") as fh:
    manifest = json.load(fh)
if manifest.get("schema_version") not in {1, 2} or manifest.get("state") != "prepared":
    raise SystemExit("ERROR: rollback bundle 未处于 prepared 状态")
if manifest.get("target") != target:
    raise SystemExit("ERROR: rollback bundle 不属于该目标项目")
recovery = manifest.get("recovery")
if not isinstance(recovery, dict) or recovery.get("status") not in {"armed", "checkpointed"}:
    raise SystemExit("ERROR: rollback bundle recovery 元数据非法")
recovery["status"] = "checkpointed"
recovery["expected_target_digest"] = digest
with open(path, "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, ensure_ascii=False, indent=2, sort_keys=True)
    fh.write("\n")
PYEOF
  APPLY_RECOVERY_EXPECTED_DIGEST="$digest"
}

finalize_rollback_bundle() { # finalize_rollback_bundle <target> <bundle> [expected-digest]
  local digest
  digest="$(tree_digest "$1")"
  if [ -n "${3:-}" ] && [ "$digest" != "$3" ]; then
    echo "ERROR: 自检期间目标已偏离 apply checkpoint；拒绝发布 applied 状态" >&2
    return 1
  fi
  python3 - "$1" "$2" "$digest" <<'PYEOF'
import hashlib
import json
import os
import stat
import sys

target, bundle, digest = os.path.realpath(sys.argv[1]), os.path.abspath(sys.argv[2]), sys.argv[3]
path = os.path.join(bundle, "manifest.json")
with open(path, encoding="utf-8") as fh:
    manifest = json.load(fh)
if manifest.get("schema_version") != 2 or manifest.get("state") != "prepared" or manifest.get("target") != target:
    raise SystemExit("ERROR: rollback bundle 状态或目标不匹配")
preimage = os.path.join(bundle, "preimage")
if not os.path.isdir(preimage):
    raise SystemExit("ERROR: rollback preimage 缺失")


def describe(path):
    if not os.path.lexists(path):
        return {"type": "missing"}
    info = os.lstat(path)
    mode = stat.S_IMODE(info.st_mode)
    if stat.S_ISREG(info.st_mode):
        content = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                content.update(chunk)
        return {"type": "file", "mode": mode, "size": info.st_size, "sha256": content.hexdigest()}
    if stat.S_ISDIR(info.st_mode):
        return {"type": "dir", "mode": mode}
    if stat.S_ISLNK(info.st_mode):
        return {"type": "link", "mode": mode, "target": os.readlink(path)}
    return {"type": "other", "mode": mode}


def inventory(root):
    result = {}
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        if dirpath == root:
            dirnames[:] = [name for name in dirnames if name != ".git"]
            filenames = [name for name in filenames if name != ".git"]
        dirnames.sort()
        filenames.sort()
        for name in [*dirnames, *filenames]:
            asset_path = os.path.join(dirpath, name)
            rel = os.path.relpath(asset_path, root).replace(os.sep, "/")
            result[rel] = describe(asset_path)
    return result


def write_atomic(destination, content):
    temporary = destination + ".tmp"
    with open(temporary, "wb") as fh:
        fh.write(content)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(temporary, destination)


before = inventory(preimage)
after = inventory(target)
assets = []
for rel in sorted(set(before) | set(after)):
    pre_state = before.get(rel, {"type": "missing"})
    post_state = after.get(rel, {"type": "missing"})
    if pre_state == post_state:
        continue
    if "other" in {pre_state.get("type"), post_state.get("type")}:
        raise SystemExit(f"ERROR: managed asset 类型不支持: {rel}")
    assets.append({"path": rel, "pre": pre_state, "post": post_state})

managed = {"schema_version": 1, "assets": assets}
managed_bytes = (json.dumps(managed, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
managed_digest = hashlib.sha256(managed_bytes).hexdigest()
write_atomic(os.path.join(bundle, "managed-assets.json"), managed_bytes)
manifest["state"] = "applied"
manifest["post_apply_digest"] = digest
manifest["managed_assets"] = {
    "path": "managed-assets.json",
    "schema_version": 1,
    "sha256": managed_digest,
    "count": len(assets),
}
manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
write_atomic(os.path.join(bundle, "manifest.sha256"), (hashlib.sha256(manifest_bytes).hexdigest() + "\n").encode("ascii"))
write_atomic(path, manifest_bytes)
PYEOF
}

restore_rollback_bundle() { # restore_rollback_bundle <target> <bundle> [unapply|recovery] [expected-digest]
  python3 - "$1" "$2" "${3:-unapply}" "${4:-}" <<'PYEOF'
import hashlib
import json
import os
from pathlib import PurePosixPath
import shutil
import stat
import sys

target, bundle, mode, expected_digest = (
    os.path.realpath(sys.argv[1]),
    os.path.abspath(sys.argv[2]),
    sys.argv[3],
    sys.argv[4],
)
manifest_path = os.path.join(bundle, "manifest.json")
preimage = os.path.join(bundle, "preimage")


def write_atomic(destination, content):
    temporary = destination + ".tmp"
    with open(temporary, "wb") as fh:
        fh.write(content)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(temporary, destination)


def digest_tree(root):
    digest = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = sorted(name for name in dirnames if not (dirpath == root and name == ".git"))
        filenames = sorted(name for name in filenames if not (dirpath == root and name == ".git"))
        for name in [*dirnames, *filenames]:
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                kind, payload = "link", os.readlink(path).encode("utf-8", "surrogateescape")
            elif stat.S_ISDIR(info.st_mode):
                kind, payload = "dir", b""
            elif stat.S_ISREG(info.st_mode):
                kind = "file"
                with open(path, "rb") as fh:
                    payload = fh.read()
            else:
                kind, payload = "other", b""
            digest.update(f"{rel}\0{kind}\0{stat.S_IMODE(info.st_mode):o}\0".encode())
            digest.update(payload)
            digest.update(b"\0")
    return digest.hexdigest()


def checked_path(root, rel):
    pure = PurePosixPath(rel)
    if not rel or pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise SystemExit(f"ERROR: managed asset 路径非法: {rel!r}")
    if pure.parts[0] == ".git":
        raise SystemExit("ERROR: managed asset 不得包含 .git")
    current = root
    for part in pure.parts[:-1]:
        current = os.path.join(current, part)
        if not os.path.lexists(current):
            break
        info = os.lstat(current)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise SystemExit(f"ERROR: managed asset 父路径类型漂移: {rel}")
    return os.path.join(root, *pure.parts)


def describe(root, rel):
    asset_path = checked_path(root, rel)
    if not os.path.lexists(asset_path):
        return {"type": "missing"}
    info = os.lstat(asset_path)
    mode_bits = stat.S_IMODE(info.st_mode)
    if stat.S_ISREG(info.st_mode):
        content = hashlib.sha256()
        with open(asset_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                content.update(chunk)
        return {"type": "file", "mode": mode_bits, "size": info.st_size, "sha256": content.hexdigest()}
    if stat.S_ISDIR(info.st_mode):
        return {"type": "dir", "mode": mode_bits}
    if stat.S_ISLNK(info.st_mode):
        return {"type": "link", "mode": mode_bits, "target": os.readlink(asset_path)}
    return {"type": "other", "mode": mode_bits}


with open(manifest_path, "rb") as fh:
    manifest_bytes = fh.read()
try:
    manifest = json.loads(manifest_bytes)
except json.JSONDecodeError as exc:
    raise SystemExit(f"ERROR: rollback bundle manifest 非法: {exc}") from exc
schema_version = manifest.get("schema_version")
if schema_version not in {1, 2}:
    raise SystemExit("ERROR: rollback bundle schema 非法")
if manifest.get("target") != target:
    raise SystemExit("ERROR: rollback bundle 不属于该目标项目")
if not os.path.isdir(preimage):
    raise SystemExit("ERROR: rollback preimage 缺失")
if schema_version == 1 and (
    "managed_assets" in manifest
    or os.path.lexists(os.path.join(bundle, "managed-assets.json"))
    or os.path.lexists(os.path.join(bundle, "manifest.sha256"))
):
    raise SystemExit("ERROR: legacy rollback bundle 含不兼容 managed evidence；疑似被篡改")
if mode in {"unapply", "verify"}:
    if manifest.get("state") != "applied":
        raise SystemExit("ERROR: rollback bundle 未处于 applied 状态")
    if schema_version == 2:
        integrity_path = os.path.join(bundle, "manifest.sha256")
        try:
            with open(integrity_path, encoding="ascii") as fh:
                recorded_manifest_digest = fh.read().strip()
        except OSError as exc:
            raise SystemExit("ERROR: rollback bundle manifest integrity 缺失") from exc
        if recorded_manifest_digest != hashlib.sha256(manifest_bytes).hexdigest():
            raise SystemExit("ERROR: rollback bundle manifest integrity 不匹配")
        managed_ref = manifest.get("managed_assets")
        if not isinstance(managed_ref, dict) or managed_ref.get("path") != "managed-assets.json":
            raise SystemExit("ERROR: rollback bundle managed manifest 缺失或非法")
        managed_path = os.path.join(bundle, "managed-assets.json")
        try:
            with open(managed_path, "rb") as fh:
                managed_bytes = fh.read()
        except OSError as exc:
            raise SystemExit("ERROR: rollback bundle managed manifest 缺失") from exc
        if managed_ref.get("sha256") != hashlib.sha256(managed_bytes).hexdigest():
            raise SystemExit("ERROR: rollback bundle managed manifest integrity 不匹配")
        try:
            managed = json.loads(managed_bytes)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"ERROR: rollback bundle managed manifest 非法: {exc}") from exc
        assets = managed.get("assets") if isinstance(managed, dict) and managed.get("schema_version") == 1 else None
        if not isinstance(assets, list) or managed_ref.get("schema_version") != 1:
            raise SystemExit("ERROR: rollback bundle managed manifest schema 非法")
        if managed_ref.get("count") != len(assets):
            raise SystemExit("ERROR: rollback bundle managed manifest count 不匹配")
        paths = []
        allowed_types = {"missing", "file", "dir", "link"}
        for asset in assets:
            if not isinstance(asset, dict) or set(asset) != {"path", "pre", "post"}:
                raise SystemExit("ERROR: rollback bundle managed asset 记录非法")
            rel = asset.get("path")
            pre_state = asset.get("pre")
            post_state = asset.get("post")
            if not isinstance(rel, str) or not isinstance(pre_state, dict) or not isinstance(post_state, dict):
                raise SystemExit("ERROR: rollback bundle managed asset 字段非法")
            if pre_state.get("type") not in allowed_types or post_state.get("type") not in allowed_types:
                raise SystemExit(f"ERROR: rollback bundle managed asset 类型非法: {rel}")
            checked_path(target, rel)
            checked_path(preimage, rel)
            paths.append(rel)
        if paths != sorted(set(paths)):
            raise SystemExit("ERROR: rollback bundle managed asset 路径必须唯一且稳定排序")
        if digest_tree(preimage) != manifest.get("pre_apply_digest"):
            raise SystemExit("ERROR: rollback bundle preimage 已被篡改")

        conflicts = []
        for asset in assets:
            rel = asset["path"]
            if describe(target, rel) != asset["post"]:
                conflicts.append(rel)
            if describe(preimage, rel) != asset["pre"]:
                raise SystemExit(f"ERROR: rollback bundle managed preimage 证据不匹配: {rel}")
        if conflicts:
            raise SystemExit("ERROR: managed asset 已漂移；unapply 前未修改任何目标文件: " + ", ".join(conflicts[:8]))

        managed_paths = set(paths)
        for asset in assets:
            if asset["post"]["type"] != "dir" or asset["pre"]["type"] in {"dir", "missing"}:
                continue
            directory = checked_path(target, asset["path"])
            unowned_descendants = []
            for dirpath, dirnames, filenames in os.walk(directory, topdown=True, followlinks=False):
                dirnames.sort()
                filenames.sort()
                for name in [*dirnames, *filenames]:
                    child = os.path.join(dirpath, name)
                    child_rel = os.path.relpath(child, target).replace(os.sep, "/")
                    if child_rel not in managed_paths:
                        unowned_descendants.append(child_rel)
            if unowned_descendants:
                raise SystemExit(
                    "ERROR: managed directory 含用户新增内容，无法恢复原非目录类型；unapply 前未修改目标: "
                    + ", ".join(unowned_descendants[:8])
                )

        if mode == "verify":
            print(f"installed-current managed_assets={len(assets)}")
            raise SystemExit(0)

        retained_directories = []
        for asset in sorted(assets, key=lambda item: (-item["path"].count("/"), item["path"]), reverse=False):
            rel, pre_state, post_state = asset["path"], asset["pre"], asset["post"]
            destination = checked_path(target, rel)
            post_type = post_state["type"]
            if post_type in {"file", "link"}:
                os.unlink(destination)
            elif post_type == "dir" and pre_state["type"] != "dir":
                try:
                    os.rmdir(destination)
                except OSError:
                    if pre_state["type"] == "missing":
                        retained_directories.append(rel)
                    else:
                        raise

        for asset in sorted(assets, key=lambda item: (item["path"].count("/"), item["path"])):
            rel, pre_state = asset["path"], asset["pre"]
            source = checked_path(preimage, rel)
            destination = checked_path(target, rel)
            pre_type = pre_state["type"]
            if pre_type == "missing":
                continue
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            if pre_type == "dir":
                os.makedirs(destination, exist_ok=True)
                os.chmod(destination, pre_state["mode"])
            elif pre_type == "file":
                shutil.copy2(source, destination, follow_symlinks=False)
            elif pre_type == "link":
                os.symlink(os.readlink(source), destination)

        retained_set = set(retained_directories)
        for asset in assets:
            rel, pre_state, post_state = asset["path"], asset["pre"], asset["post"]
            current_state = describe(target, rel)
            if current_state == pre_state:
                continue
            if rel in retained_set and pre_state["type"] == "missing" and post_state["type"] == "dir" and current_state["type"] == "dir":
                continue
            raise SystemExit(f"ERROR: managed asset 恢复后状态不匹配: {rel}")

        manifest["state"] = "restored"
        manifest["unapply"] = {
            "mode": "managed_assets",
            "retained_user_directories": sorted(retained_set),
        }
        restored_manifest_bytes = (
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        write_atomic(
            os.path.join(bundle, "manifest.sha256"),
            (hashlib.sha256(restored_manifest_bytes).hexdigest() + "\n").encode("ascii"),
        )
        write_atomic(manifest_path, restored_manifest_bytes)
        raise SystemExit(0)

    current_digest = digest_tree(target)
    if manifest.get("post_apply_digest") != current_digest:
        raise SystemExit("ERROR: apply 后目标已有漂移；拒绝覆盖用户新改动")
    if mode == "verify":
        print("installed-current managed_assets=legacy-whole-target")
        raise SystemExit(0)
    restored_state = "restored"
elif mode == "recovery":
    current_digest = digest_tree(target)
    recovery = manifest.get("recovery")
    if manifest.get("state") != "prepared" or not isinstance(recovery, dict):
        raise SystemExit("ERROR: rollback bundle 未处于可自动恢复的 prepared 状态")
    if recovery.get("status") not in {"armed", "checkpointed"}:
        raise SystemExit("ERROR: rollback bundle recovery 状态不允许自动恢复")
    if not expected_digest or recovery.get("expected_target_digest") != expected_digest:
        raise SystemExit("ERROR: rollback bundle recovery CAS 元数据不匹配")
    if current_digest != expected_digest:
        raise SystemExit("ERROR: 当前目标不匹配本次 apply 的最后 CAS；拒绝覆盖非本进程改动")
    restored_state = "recovered"
else:
    raise SystemExit(f"ERROR: 未知 rollback restore mode: {mode}")

# Schema-v1 unapply compatibility and in-process failed-apply recovery retain the
# original exact whole-target restore. Schema-v2 ordinary unapply exits above.
for name in os.listdir(target):
    if name == ".git":
        continue
    path = os.path.join(target, name)
    if os.path.islink(path) or not os.path.isdir(path):
        os.unlink(path)
    else:
        shutil.rmtree(path)
for name in os.listdir(preimage):
    source, destination = os.path.join(preimage, name), os.path.join(target, name)
    if os.path.islink(source):
        os.symlink(os.readlink(source), destination)
    elif os.path.isdir(source):
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination, follow_symlinks=False)
if digest_tree(target) != manifest.get("pre_apply_digest"):
    raise SystemExit("ERROR: rollback preimage 恢复后 digest 不匹配；bundle 已保留，必须人工恢复")
manifest["state"] = restored_state
manifest["post_apply_digest"] = None if mode == "recovery" else manifest.get("post_apply_digest")
if mode == "recovery":
    manifest["recovery"] = {
        "status": "succeeded",
        "expected_target_digest": manifest.get("pre_apply_digest"),
    }
write_atomic(
    manifest_path,
    (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
)
PYEOF
}

rollback_bundle_state() { # rollback_bundle_state <target> <bundle>; rc 0=applied, 3=not-applied
  python3 - "$1" "$2" <<'PYEOF'
import hashlib
import json
import os
import sys

target, bundle = os.path.realpath(sys.argv[1]), os.path.abspath(sys.argv[2])
manifest_path = os.path.join(bundle, "manifest.json")
if not os.path.isfile(manifest_path):
    print("not-applied")
    raise SystemExit(3)
try:
    with open(manifest_path, "rb") as fh:
        manifest_bytes = fh.read()
    manifest = json.loads(manifest_bytes)
except (OSError, json.JSONDecodeError) as exc:
    raise SystemExit(f"rollback bundle manifest 非法: {exc}") from exc
if manifest.get("schema_version") not in {1, 2}:
    raise SystemExit("rollback bundle schema 非法")
if manifest.get("target") != target:
    raise SystemExit("rollback bundle 不属于该目标项目")

state = manifest.get("state")
managed_evidence = any(
    os.path.lexists(os.path.join(bundle, name))
    for name in ("managed-assets.json", "manifest.sha256")
) or "managed_assets" in manifest
if manifest.get("schema_version") == 2 and managed_evidence:
    try:
        with open(os.path.join(bundle, "manifest.sha256"), encoding="ascii") as fh:
            expected = fh.read().strip()
    except OSError as exc:
        raise SystemExit("rollback bundle manifest integrity 缺失") from exc
    if expected != hashlib.sha256(manifest_bytes).hexdigest():
        raise SystemExit("rollback bundle manifest integrity 不匹配")
if state == "applied":
    print("applied")
    raise SystemExit(0)
if state in {"recovered", "restored"}:
    print("not-applied")
    raise SystemExit(3)
if state == "prepared":
    raise SystemExit("rollback bundle 仍处于 prepared 状态；apply 未完成或需要人工恢复")
raise SystemExit("rollback bundle state 非法")
PYEOF
}

report_rollback_lifecycle() { # report_rollback_lifecycle <status|verify> <target> <bundle>
  local operation="$1" target="$2" bundle="$3" state rc=0 detail verify_output
  state="$(rollback_bundle_state "$target" "$bundle" 2>&1)" || rc=$?
  if [ "$rc" = 3 ]; then
    echo "status=not-applied"
    echo "target=$target"
    echo "rollback_bundle=$bundle"
    [ "$operation" = status ] && return 0
    echo "ERROR: Guru overlay 未处于 applied 状态" >&2
    return 1
  fi
  if [ "$rc" != 0 ]; then
    detail="${state//$'\n'/; }"
    echo "status=drifted"
    echo "target=$target"
    echo "rollback_bundle=$bundle"
    echo "detail=$detail"
    [ "$operation" = status ] && return 0
    return 1
  fi

  rc=0
  verify_output="$(restore_rollback_bundle "$target" "$bundle" verify 2>&1)" || rc=$?
  if [ "$rc" = 0 ]; then
    echo "status=installed-current"
    echo "target=$target"
    echo "rollback_bundle=$bundle"
    echo "$verify_output"
    return 0
  fi
  detail="${verify_output//$'\n'/; }"
  echo "status=drifted"
  echo "target=$target"
  echo "rollback_bundle=$bundle"
  echo "detail=$detail"
  [ "$operation" = status ] && return 0
  return 1
}

validate_planned_rollback_bundle() { # read-only validation for plan
  python3 - "$1" "$2" <<'PYEOF'
import os
import sys

target = os.path.realpath(sys.argv[1])
bundle_arg = os.path.abspath(sys.argv[2])
if os.path.lexists(bundle_arg) and os.path.islink(bundle_arg):
    raise SystemExit("ERROR: rollback bundle 路径不得是符号链接")
bundle = os.path.realpath(bundle_arg)
try:
    inside_target = os.path.commonpath((target, bundle)) == target
except ValueError:
    inside_target = False
if inside_target:
    raise SystemExit("ERROR: rollback bundle 必须位于目标项目外部")
if os.path.exists(bundle) and not os.path.isdir(bundle):
    raise SystemExit(f"ERROR: rollback bundle 必须是目录: {bundle}")
if os.path.isdir(bundle) and os.listdir(bundle):
    raise SystemExit(f"ERROR: rollback bundle 必须不存在或为空: {bundle}")
print(bundle)
PYEOF
}

mark_rollback_manual_recovery() { # mark_rollback_manual_recovery <bundle> <reason>
  python3 - "$1" "$2" <<'PYEOF'
import json
import os
import sys

bundle, reason = os.path.abspath(sys.argv[1]), sys.argv[2]
path = os.path.join(bundle, "manifest.json")
try:
    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)
except (OSError, json.JSONDecodeError):
    raise SystemExit(1)
if manifest.get("schema_version") not in {1, 2} or manifest.get("state") != "prepared":
    raise SystemExit(1)
recovery = manifest.get("recovery")
if not isinstance(recovery, dict):
    recovery = {}
    manifest["recovery"] = recovery
recovery["status"] = "manual_required"
recovery["reason"] = reason
with open(path, "w", encoding="utf-8") as fh:
    json.dump(manifest, fh, ensure_ascii=False, indent=2, sort_keys=True)
    fh.write("\n")
PYEOF
}

handle_failed_apply_exit() {
  local rc=$?
  trap - EXIT INT TERM HUP
  if [ "$rc" = 0 ] || [ "$APPLY_RECOVERY_ARMED" != 1 ]; then
    return
  fi
  set +e
  echo "ERROR: apply 未完成；正在用 rollback bundle 尝试自动恢复..." >&2
  if restore_rollback_bundle "$TARGET" "$APPLY_RECOVERY_BUNDLE" recovery "$APPLY_RECOVERY_EXPECTED_DIGEST"; then
    echo "RECOVERED: 已恢复 apply 前精确 preimage；.git 未读取或修改；bundle 状态为 recovered。" >&2
  else
    mark_rollback_manual_recovery "$APPLY_RECOVERY_BUNDLE" "cas_or_restore_failed" >/dev/null 2>&1 || true
    echo "ERROR: 自动恢复未获精确 CAS 或恢复失败，已拒绝覆盖并保留 rollback bundle。" >&2
    echo "MANUAL RECOVERY REQUIRED: 检查 $APPLY_RECOVERY_BUNDLE/preimage 与当前目标；该 bundle 不可作为成功 unapply 使用。" >&2
  fi
  exit "$rc"
}

handle_failed_apply_signal() { # handle_failed_apply_signal <exit-code> <signal-name>
  local rc="$1" signal_name="$2"
  echo "ERROR: apply 收到 ${signal_name}，将进入 rollback recovery。" >&2
  exit "$rc"
}

case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
  --status|--verify)
    LIFECYCLE_OPERATION="${1#--}"
    [ "$#" = 3 ] || { usage >&2; exit 2; }
    TARGET="$(cd "$2" && pwd)"
    [ -d "$TARGET/.trellis" ] || { echo "ERROR: $TARGET 不是 Trellis 项目（缺 .trellis/）"; exit 1; }
    report_rollback_lifecycle "$LIFECYCLE_OPERATION" "$TARGET" "$3"
    exit $?
    ;;
esac

if [ "${1:-}" = "--unapply" ]; then
  [ "$#" = 3 ] || { echo "用法: apply.sh --unapply <目标项目路径> <rollback-bundle>"; exit 2; }
  TARGET="$(cd "$2" && pwd)"
  [ -d "$TARGET/.trellis" ] || { echo "ERROR: $TARGET 不是 Trellis 项目（缺 .trellis/）"; exit 1; }
  restore_rollback_bundle "$TARGET" "$3" unapply
  echo "== guru overlay 已从 rollback bundle 恢复；.git 未被读取或修改 =="
  exit 0
fi

LIFECYCLE_OPERATION="apply"
case "${1:-}" in
  --plan|--upgrade)
    LIFECYCLE_OPERATION="${1#--}"
    shift
    ;;
esac
[ "$#" -gt 0 ] || { usage >&2; exit 2; }
TARGET="$1"
TARGET="$(cd "$TARGET" && pwd)"
[ -d "$TARGET/.trellis" ] || { echo "ERROR: $TARGET 不是 Trellis 项目（缺 .trellis/），先 trellis init"; exit 1; }
shift
PLATFORM="flutter"
if [ "$#" -gt 0 ] && [ "${1#--}" = "$1" ]; then
  PLATFORM="$1"
  shift
fi
ROLLBACK_BUNDLE=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --rollback-bundle)
      [ "$#" -ge 2 ] || { echo "ERROR: --rollback-bundle 缺目录参数"; exit 2; }
      ROLLBACK_BUNDLE="$2"
      shift 2
      ;;
    *) echo "ERROR: 未知参数: $1"; exit 2 ;;
  esac
done
if [ "$LIFECYCLE_OPERATION" = upgrade ] && [ -z "$ROLLBACK_BUNDLE" ]; then
  echo "ERROR: --upgrade 必须指定新的 --rollback-bundle" >&2
  exit 2
fi
GURU_WITH_GITNEXUS="${GURU_WITH_GITNEXUS:-0}"
GURU_ADVERSARIAL_ENABLED="${GURU_ADVERSARIAL_ENABLED:-}"

if [ -f "$TARGET/.codex/hooks.json" ]; then
  python3 - "$TARGET/.codex/hooks.json" <<'PYEOF'
import json
import sys

path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
except Exception as exc:
    print(f"ERROR: .codex/hooks.json 非法 JSON，跳过自动合并（请人工处理）：{exc}", file=sys.stderr)
    sys.exit(1)
if not isinstance(data, dict):
    print("ERROR: .codex/hooks.json 根节点必须是对象", file=sys.stderr)
    sys.exit(1)
hooks = data.get("hooks", {})
if not isinstance(hooks, dict):
    print("ERROR: .codex/hooks.json 的 hooks 必须是对象", file=sys.stderr)
    sys.exit(1)
for event, entries in hooks.items():
    if not isinstance(event, str) or not isinstance(entries, list):
        print(f"ERROR: .codex/hooks.json 的 hooks.{event} 必须是数组", file=sys.stderr)
        sys.exit(1)
    for entry_idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            print(f"ERROR: .codex/hooks.json 的 hooks.{event}[{entry_idx}] 必须是对象", file=sys.stderr)
            sys.exit(1)
        entry_hooks = entry.get("hooks", [])
        if not isinstance(entry_hooks, list):
            print(f"ERROR: .codex/hooks.json 的 hooks.{event}[{entry_idx}].hooks 必须是数组", file=sys.stderr)
            sys.exit(1)
        for hook_idx, hook in enumerate(entry_hooks):
            if not isinstance(hook, dict):
                print(f"ERROR: .codex/hooks.json 的 hooks.{event}[{entry_idx}].hooks[{hook_idx}] 必须是对象", file=sys.stderr)
                sys.exit(1)
PYEOF
fi

# 平台选择：决定 spec 包 / workflow / verify analyze 命令。
case "$PLATFORM" in
  flutter) SPEC_NAME="guru-flutter-client"; WF_NAME="guru-client"; ANALYZE_CMD="flutter analyze"; LAYERS="flutter service shared"; SKILL_GLOBS="client-* flutter-implementation-guru-*"; XTRA_HOOKS="block-l10n-sync.sh" ;;
  go)      SPEC_NAME="guru-go-backend";     WF_NAME="guru-go";     ANALYZE_CMD="go build ./... && go vet ./..."; LAYERS="backend shared"; SKILL_GLOBS="go-*"; XTRA_HOOKS="" ;;
  ios)     SPEC_NAME="guru-ios-native";     WF_NAME="guru-ios";    ANALYZE_CMD="xcodebuild build -quiet || swift build"; LAYERS="ios shared"; SKILL_GLOBS="ios-*"; XTRA_HOOKS="" ;;
  h5)      SPEC_NAME="guru-h5-web";         WF_NAME="guru-h5";     ANALYZE_CMD="pnpm exec tsc --noEmit"; LAYERS="frontend backend shared"; SKILL_GLOBS="h5-*"; XTRA_HOOKS="" ;;
  *) echo "ERROR: 未知平台 '$PLATFORM'（支持 flutter|go|ios|h5）"; exit 1 ;;
esac
[ -d "$ROOT/specs/$SPEC_NAME" ] || { echo "ERROR: spec 包不存在: specs/${SPEC_NAME}（先 pnpm -C packages/cli sync:guru 或确认 guru-template/specs/）"; exit 1; }
BOOTSTRAP_PRD="$HERE/bootstrap/${PLATFORM}-bootstrap-prd.md"

if [ "$LIFECYCLE_OPERATION" = plan ]; then
  PLANNED_BUNDLE="none"
  if [ -n "$ROLLBACK_BUNDLE" ]; then
    PLANNED_BUNDLE="$(validate_planned_rollback_bundle "$TARGET" "$ROLLBACK_BUNDLE")"
  fi
  echo "status=ready"
  echo "operation=apply"
  echo "target=$TARGET"
  echo "platform=$PLATFORM"
  echo "spec=$SPEC_NAME"
  echo "workflow=$WF_NAME"
  echo "rollback_bundle=$PLANNED_BUNDLE"
  echo "mutation=none"
  exit 0
fi

# guru-managed skill 全集（剪枝白名单：只删这些里的"非本平台"项，绝不碰用户自有/官方 trellis-* skill）
GURU_SKILLS="$(ls -d "$HERE"/agents-skills/*/ 2>/dev/null | xargs -n1 basename || true)"
# 阶段 C 收尾：旧 4 名 grill wrapper 已从模板删除，不再属于 GURU_SKILLS。
# 仅对这个显式 legacy 列表做存量清理；删除前先备份，避免误伤用户自建同名 skill 后不可恢复。
LEGACY_GRILL_SKILLS="client-grill go-design-grill h5-design-grill ios-design-grill"
# 平台无关 shared skill（每平台都装、不剪）：需求三件套被所有 workflow 的 Phase1(需求) 硬前置依赖。
SHARED_SKILLS="requirement-doc-standard requirement-writing requirement-review design-grill"
for s in $SHARED_SKILLS; do
  [ -d "$HERE/agents-skills/$s" ] || { echo "ERROR: shared skill 目录缺失: agents-skills/$s"; exit 1; }
done
# skill 名是否该装：shared 始终装；否则按当前平台 SKILL_GLOBS 任一 glob 匹配。
skill_in_scope() {
  local n="$1" g
  case " $SHARED_SKILLS " in *" $n "*) return 0 ;; esac
  for g in $SKILL_GLOBS; do
    # shellcheck disable=SC2254
    case "$n" in $g) return 0 ;; esac
  done
  return 1
}

# skill 目录安装：rm-then-cp 刷新 + 清理 macOS/py 脏文件（.DS_Store/__pycache__ 不随 cp -R 泄漏进目标）
install_skill_dir() {  # $1=源目录（内容到末尾）  $2=目标目录
  rm -rf "$2"; mkdir -p "$2"
  cp -R "$1/." "$2/"
  find "$2" \( -name .DS_Store -o -name __pycache__ \) -exec rm -rf {} + 2>/dev/null || true
}

ensure_local_runtime_gitignore() {
  local gitignore="$TARGET/.gitignore" added=0
  touch "$gitignore"
  add_ignore() {
    local pattern="$1"
    if ! grep -qxF "$pattern" "$gitignore"; then
      if [ "$added" = 0 ]; then
        if ! grep -qxF "# Local AI/Trellis runtime logs" "$gitignore"; then
          [ -s "$gitignore" ] && printf '\n' >> "$gitignore"
          printf '# Local AI/Trellis runtime logs\n' >> "$gitignore"
        fi
      fi
      printf '%s\n' "$pattern" >> "$gitignore"
      added=$((added + 1))
    fi
  }
  add_ignore ".claude/projects/"
  add_ignore ".codex/sessions/"
  add_ignore ".trellis/channels/"
  if [ "$added" = 0 ]; then
    echo "  gitignore: local AI/Trellis runtime logs already ignored"
  else
    echo "  gitignore: added local AI/Trellis runtime log ignores ×${added}"
  fi
}

gitnexus_requested() {
  case "$(printf '%s' "$GURU_WITH_GITNEXUS" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|on) return 0 ;;
    *) return 1 ;;
  esac
}

bootstrap_gitnexus() {
  command -v npx >/dev/null 2>&1 || { echo "ERROR: GURU_WITH_GITNEXUS=1 需要 npx（用于运行 gitnexus）"; exit 1; }

  echo ""
  echo "== GitNexus opt-in bootstrap =="
  (cd "$TARGET" && npx gitnexus analyze)
  (cd "$TARGET" && npx gitnexus status)
  [ -f "$TARGET/.gitnexus/meta.json" ] || { echo "ERROR: GitNexus analyze 未生成 .gitnexus/meta.json"; exit 1; }

  python3 - "$TARGET" <<'PYEOF'
import json
import os
import re
import shlex
import sys

root = sys.argv[1]
agents_path = os.path.join(root, "AGENTS.md")
meta_path = os.path.join(root, ".gitnexus", "meta.json")
with open(meta_path, encoding="utf-8") as fh:
    meta = json.load(fh)

stats = meta.get("stats") if isinstance(meta.get("stats"), dict) else {}
repo_name = os.path.basename(root.rstrip(os.sep)) or root
repo_arg = shlex.quote(root)
runner = "node .gitnexus/run.cjs analyze" if os.path.isfile(os.path.join(root, ".gitnexus", "run.cjs")) else "npx gitnexus analyze"
block = f"""<!-- gitnexus:start -->
# GitNexus - Code Intelligence

This project has a GitNexus index for **{repo_name}** ({stats.get("files", 0)} files, {stats.get("nodes", 0)} symbols, {stats.get("edges", 0)} relationships, {stats.get("processes", 0)} execution flows). The index was refreshed at `{meta.get("indexedAt", "unknown")}`.

> Index stale? Run `{runner}` from the project root, then `npx gitnexus status`.

## Agent Rules

- Use GitNexus MCP tools when available for unfamiliar code, impact analysis, and change detection.
- Before editing a function, class, or method, run impact analysis with `gitnexus_impact` or `npx gitnexus impact -r {repo_arg} <symbol>`.
- Before committing, run change detection with `gitnexus_detect_changes` or `npx gitnexus detect-changes --scope all -r {repo_arg}`.
- If MCP tools are missing, run `npx gitnexus setup`, restart the agent host, and use the GitNexus CLI meanwhile.

<!-- gitnexus:end -->
"""

content = ""
if os.path.isfile(agents_path):
    with open(agents_path, encoding="utf-8") as fh:
        content = fh.read()

content = re.sub(r"\n?<!-- gitnexus:start -->.*?<!-- gitnexus:end -->\n?", "\n", content, flags=re.S).rstrip()
new_content = f"{content}\n\n{block}" if content else block
with open(agents_path, "w", encoding="utf-8") as fh:
    fh.write(new_content.rstrip() + "\n")
PYEOF
  echo "  GitNexus: analyze/status 完成，AGENTS.md gitnexus 块已刷新"
  echo "  MCP: 如 agent 宿主未显示 gitnexus_* 工具，请运行 'npx gitnexus setup' 后重启宿主会话"
}

cleanup_legacy_grill_skills() {
  local ts backup_root touched_names="" side_name side_path skill_name skill_dir backup_skill_dir expected_agents expected_claude
  [ -n "${TARGET:-}" ] && [ "$TARGET" != "/" ] || { echo "ERROR: TARGET 非法，拒绝清理 legacy grill skill"; exit 1; }

  for skill_name in $LEGACY_GRILL_SKILLS; do
    for side_name in agents claude; do
      side_path="$TARGET/.$side_name/skills"
      skill_dir="$side_path/$skill_name"
      [ -d "$skill_dir" ] || continue
      expected_agents="$TARGET/.agents/skills/$skill_name"
      expected_claude="$TARGET/.claude/skills/$skill_name"
      if [ "$skill_dir" != "$expected_agents" ] && [ "$skill_dir" != "$expected_claude" ]; then
        echo "ERROR: legacy grill skill 路径非法，拒绝删除: $skill_dir"
        exit 1
      fi
      # 托管身份判断：只清理 guru 装的 grill（wrapper 的「兼容 wrapper」描述 / 旧 grill 的 grill-with-docs·Gate 前拷问）。
      # 特征用精确短语，绝不用裸 'design-grill'——那会匹配 skill 名自身（go-design-grill 等）误删用户同名 skill。
      # 无 guru grill 特征 = 疑似用户自建同名 skill，跳过不删、仅警告，避免误删用户数据。
      if ! grep -qE 'grill-with-docs|兼容 wrapper|Gate 前拷问' "$skill_dir/SKILL.md" 2>/dev/null; then
        echo "  ⚠ 跳过疑似用户自建同名 skill（无 guru grill 特征，未删，请自行确认）: .$side_name/skills/$skill_name"
        continue
      fi
      if [ -z "${backup_root:-}" ]; then
        ts="$(date +%Y%m%d%H%M%S)"
        backup_root="$TARGET/.trellis/backup/guru-legacy-skills/$ts"
        mkdir -p "$backup_root"
      fi
      backup_skill_dir="$backup_root/$skill_name/$side_name"
      mkdir -p "$(dirname "$backup_skill_dir")"
      cp -R "$skill_dir" "$backup_skill_dir"
      case " $touched_names " in *" $skill_name "*) ;; *) touched_names="${touched_names:+$touched_names }$skill_name" ;; esac
      rm -rf "$skill_dir"
    done
  done

  if [ -n "$touched_names" ]; then
    echo "  已备份并移除 legacy grill skill: $touched_names → ${backup_root#$TARGET/}；如系你自建的同名 skill，请从备份恢复"
  fi
}

# 平台-项目类型一致性兜底：漏传/传错第二位置参数会静默装错平台（默认 flutter）。
# 检测明显的项目标志文件，与 PLATFORM 矛盾时警告（不硬失败：monorepo/特殊布局可能合法）。
detect_hint=""
if [ -f "$TARGET/pubspec.yaml" ]; then detect_hint="${detect_hint:+$detect_hint,}flutter"; fi
if [ -f "$TARGET/go.mod" ]; then detect_hint="${detect_hint:+$detect_hint,}go"; fi
if [ -f "$TARGET/Package.swift" ] || ls "$TARGET"/*.xcodeproj >/dev/null 2>&1; then detect_hint="${detect_hint:+$detect_hint,}ios"; fi
if [ -f "$TARGET/package.json" ] && [ ! -f "$TARGET/pubspec.yaml" ]; then detect_hint="${detect_hint:+$detect_hint,}h5"; fi
case ",${detect_hint}," in
  ,,) ;;                          # 无可识别标志（空/特殊项目）：不校验
  *",${PLATFORM},"*) ;;           # 一致
  *) echo "  ⚠ 平台校验：传入平台 '${PLATFORM}' 与检测到的项目类型（${detect_hint}）不符——确认第二位置参数是否传错（apply.sh <目标> <flutter|go|ios|h5>）" ;;
esac

if [ -n "$ROLLBACK_BUNDLE" ]; then
  create_rollback_bundle "$TARGET" "$ROLLBACK_BUNDLE"
  APPLY_RECOVERY_BUNDLE="$(cd "$ROLLBACK_BUNDLE" && pwd)"
  APPLY_RECOVERY_EXPECTED_DIGEST="$(python3 - "$APPLY_RECOVERY_BUNDLE/manifest.json" <<'PYEOF'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    print(json.load(fh)["pre_apply_digest"])
PYEOF
)"
  APPLY_RECOVERY_ARMED=1
  trap handle_failed_apply_exit EXIT
  trap 'handle_failed_apply_signal 130 INT' INT
  trap 'handle_failed_apply_signal 143 TERM' TERM
  trap 'handle_failed_apply_signal 129 HUP' HUP
fi

if [ "$LIFECYCLE_OPERATION" = upgrade ]; then
  echo "== guru overlay 显式升级 → ${TARGET} （平台: ${PLATFORM} → spec=${SPEC_NAME} workflow=${WF_NAME}）=="
else
  echo "== guru overlay 装配 → ${TARGET} （平台: ${PLATFORM} → spec=${SPEC_NAME} workflow=${WF_NAME}）=="
fi
ensure_local_runtime_gitignore

# 1) skills → .agents/skills/（装本平台集合 + shared 需求三件套，剪枝他平台 guru skill）
mkdir -p "$TARGET/.agents/skills"
agent_skill_n=0
# 单遍历 guru-managed 全集：属本平台或 shared → rm-then-cp 刷新装；否则剪枝（不碰用户自有/官方 trellis-*）
for gs in $GURU_SKILLS; do
  if skill_in_scope "$gs"; then
    install_skill_dir "$HERE/agents-skills/$gs" "$TARGET/.agents/skills/$gs"
    agent_skill_n=$((agent_skill_n + 1))
  else
    rm -rf "$TARGET/.agents/skills/$gs"
  fi
done
echo "  skills ×${agent_skill_n} → .agents/skills/（${PLATFORM} 平台 + shared 需求三件套）"

# 2) delivery policy + guarded lifecycle + gates → project-local Custom runtime
mkdir -p "$TARGET/.trellis/scripts/guru" "$TARGET/.trellis/policy"
cp \
  "$HERE/verify/guru_gate.py" \
  "$HERE/verify/guru_risk.py" \
  "$HERE/verify/guru_contract.py" \
  "$HERE/verify/guru_delivery_policy.py" \
  "$HERE/verify/guru_review_record.py" \
  "$HERE/hooks/guru_after_create.py" \
  "$HERE/hooks/guru_after_start.py" \
  "$HERE/hooks/guru_task.py" \
  "$HERE/verify/guru_config_patch.py" \
  "$HERE/verify/guru_supervise.py" \
  "$TARGET/.trellis/scripts/guru/"
cp "$HERE/policy/delivery-policy.json" "$TARGET/.trellis/policy/delivery-policy.json"
chmod +x "$TARGET/.trellis/scripts/guru/"*.py
echo "  runtime: delivery policy + guarded lifecycle + gates → .trellis/scripts/guru/；policy → .trellis/policy/"

# 3) 平台 hooks（Claude）+ trellis-local：只装共享 + 本平台专属 + 平台化 grill-nudge
mkdir -p "$TARGET/.claude/hooks" "$TARGET/.claude/skills/trellis-local"
SHARED_HOOKS="block-legacy-dirs.sh block-sanctioned-tlds.sh block-unconfirmed-start.sh block-unstarted-commit.sh"
INSTALLED_HOOKS="$SHARED_HOOKS grill-nudge.sh $XTRA_HOOKS"
# 剪枝：删目标里 guru-managed 但不属当前平台的旧 hook（含历史 grill nudge 名、非 flutter 的 block-l10n-sync.sh）
LEGACY_GRILL_HOOK="client""-grill-nudge.sh"
GURU_HOOKS="$(ls "$HERE"/hooks/platform/*.sh 2>/dev/null | xargs -n1 basename || true) $LEGACY_GRILL_HOOK"
for gh in $GURU_HOOKS; do
  case " $INSTALLED_HOOKS " in *" $gh "*) ;; *) rm -f "$TARGET/.claude/hooks/$gh" ;; esac
done
# 装共享 + 平台专属 hook。block-legacy-dirs.sh 含用户按项目约定填写的 LEGACY_PATTERNS：
# cp 模板刷新脚本主体，但回填用户既有的非空值——否则二次 apply 用模板空值覆盖、老目录拦截静默失效。
for h in $SHARED_HOOKS $XTRA_HOOKS; do
  prev_legacy_patterns=""
  if [ "$h" = "block-legacy-dirs.sh" ] && [ -f "$TARGET/.claude/hooks/$h" ]; then
    prev_legacy_patterns="$(grep -m1 '^LEGACY_PATTERNS=' "$TARGET/.claude/hooks/$h" 2>/dev/null || true)"
  fi
  cp "$HERE/hooks/platform/$h" "$TARGET/.claude/hooks/$h"
  if [ -n "$prev_legacy_patterns" ] && [ "$prev_legacy_patterns" != "LEGACY_PATTERNS=''" ] && [ "$prev_legacy_patterns" != 'LEGACY_PATTERNS=""' ]; then
    python3 - "$TARGET/.claude/hooks/$h" "$prev_legacy_patterns" <<'PYEOF'
import sys
path, prev = sys.argv[1], sys.argv[2]
lines = open(path, encoding="utf-8").read().splitlines(keepends=True)
for i, ln in enumerate(lines):
    if ln.startswith("LEGACY_PATTERNS="):
        lines[i] = prev + "\n"
        break
open(path, "w", encoding="utf-8").write("".join(lines))
PYEOF
    echo "  hooks: 保留用户既有老目录拦截配置（block-legacy-dirs.sh 的 LEGACY_PATTERNS 未被模板空值覆盖）"
  fi
done
# grill-nudge 统一提示 design-grill；旧四名 skill 由下方 legacy 清理负责备份移除。
cp "$HERE/hooks/platform/grill-nudge.sh" "$TARGET/.claude/hooks/grill-nudge.sh"
chmod +x "$TARGET/.claude/hooks/"*.sh
cp "$HERE/trellis-local/SKILL.md" "$TARGET/.claude/skills/trellis-local/"
echo "  hooks(platform): ${INSTALLED_HOOKS} + trellis-local"

# 历史 `.grilled-*` 是旧 nudge 的"已提示"幂等标记，不再代表 design-grill 已完成。
# 阶段 B 起真正完成/跳过状态只认 task.json 的 guru_gates[gate].grill（由 guru_gate.py grill-done/skip 写入）。
old_grilled_n=0
if [ -d "$TARGET/.trellis/tasks" ]; then
  old_grilled_n="$(find "$TARGET/.trellis/tasks" -type f -name '.grilled-*' 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$old_grilled_n" != 0 ]; then
    find "$TARGET/.trellis/tasks" -type f -name '.grilled-*' -exec rm -f {} + 2>/dev/null || true
    echo "  grill markers: 已清理旧 .grilled-* 提示标记 ×${old_grilled_n}（不再表示完成）"
  fi
fi

# 4) 平台 skill 镜像（Claude Code 只读 .claude/skills；Codex 等读 .agents/skills）
MIRROR_SCRIPT="$TARGET/scripts/sync_platform_skills.py"
USED_PROJECT_MIRROR=0
if [ -f "$MIRROR_SCRIPT" ]; then
  # 项目自带镜像系统（如 himora）是该项目平台镜像的权威，交给它统一处理。
  # 契约：脚本的 --sync/--check 必须覆盖 SHARED_SKILLS（尤其 design-grill）在 .agents/.claude 两面存在。
  # 本脚本 §8 会显式校验 design-grill 两面存在，防止镜像脚本假绿。
  python3 "$MIRROR_SCRIPT" --sync --root "$TARGET"
  USED_PROJECT_MIRROR=1
  echo "  platform mirror: 项目镜像脚本 --sync 完成"
else
  # 单遍历 guru-managed 全集：属本平台或 shared → 镜像刷新；否则剪枝
  claude_skill_n=0
  for gs in $GURU_SKILLS; do
    if skill_in_scope "$gs"; then
      install_skill_dir "$HERE/agents-skills/$gs" "$TARGET/.claude/skills/$gs"
      claude_skill_n=$((claude_skill_n + 1))
    else
      rm -rf "$TARGET/.claude/skills/$gs"
    fi
  done
  echo "  platform mirror: skills ×${claude_skill_n} → .claude/skills/（${PLATFORM} 平台 + shared）"
fi

cleanup_legacy_grill_skills

# 4.5) 两个 skill 面双向对齐（修「换客户端就少一批 skill」）：
#   trellis init 只把引擎 skill（trellis-*）装进 --client 对应目录（如 --claude → .claude/skills），
#   但 Codex/本地 agent 客户端读 .agents/skills。§4 的镜像又只搬 guru skill。结果 trellis-* 只在
#   .claude/skills、读 .agents/skills 的客户端永远看不到它们。这里把两面对齐成同一并集（guru 平台 +
#   shared + 引擎 trellis-* + trellis-local + 用户自有），任意客户端读哪个目录都是完整集合。
#   guru 越界项已在 §1/§4 从两面同时剪掉、且并集只补「非 guru」项，故不会复活被裁剪的他平台 guru skill。
if [ "$USED_PROJECT_MIRROR" = 0 ]; then
  mkdir -p "$TARGET/.agents/skills" "$TARGET/.claude/skills"
  recon_n=0; drift_n=0
  put_skill() {  # $1=源 skill 目录  $2=目标 skill 目录：rm-then-cp + 清理脏文件
    rm -rf "$2"; mkdir -p "$2"; cp -R "$1." "$2/"
    find "$2" \( -name .DS_Store -o -name __pycache__ \) -exec rm -rf {} + 2>/dev/null || true
  }
  drift_dir() {  # $1=src skill 目录  $2=dst skill 目录 → 输出 src|dst|equal（按整棵子树最新文件 mtime，排除脏文件）
    python3 - "$1" "$2" <<'PY'
import os, sys
def newest(root):
    best = -1.0
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d != "__pycache__"]
        for n in fns:
            if n == ".DS_Store":
                continue
            try:
                best = max(best, os.stat(os.path.join(dp, n)).st_mtime)
            except OSError:
                pass
    return best
a, b = newest(sys.argv[1]), newest(sys.argv[2])
print("src" if a > b else "dst" if b > a else "equal")
PY
  }
  reconcile_skills() {  # $1=源 skills 目录  $2=目标 skills 目录
    # 把源里"非 guru"的 skill 对齐到目标：缺失→补；两面都有但内容漂移→以「整棵子树最新文件 mtime」
    # 较新一侧为权威覆盖较旧侧（不只看 SKILL.md/目录 mtime——多文件 skill 改内部文件不会 bump 二者，
    #   旧实现会漏同步且可能判反方向）。mtime 严格相等无法判向时按当前源侧优先同步并告警。
    #   diff 排除脏文件，避免"源带 .DS_Store / 目标已清理"造成的假漂移破坏幂等。反向调用处理另一方向。
    local sd nm dir
    [ -d "$1" ] || return 0
    for sd in "$1"/*/; do
      [ -d "$sd" ] || continue
      nm="$(basename "$sd")"
      case " $GURU_SKILLS " in *" $nm "*) continue ;; esac   # guru-managed 由 §1/§4 按平台权威管理，不在此并集
      if [ ! -d "$2/$nm" ]; then
        put_skill "$sd" "$2/$nm"; recon_n=$((recon_n + 1))
      elif ! diff -rq -x .DS_Store -x __pycache__ "$sd" "$2/$nm" >/dev/null 2>&1; then
        dir="$(drift_dir "$sd" "$2/$nm")"
        if [ "$dir" = src ]; then
          put_skill "$sd" "$2/$nm"; drift_n=$((drift_n + 1))
        elif [ "$dir" = equal ]; then
          put_skill "$sd" "$2/$nm"; drift_n=$((drift_n + 1))
          echo "  ⚠ skill 双面对齐: $nm 两面内容不同但最新 mtime 相等，按当前源侧优先同步——如方向有误请手动核对" >&2
        fi
        # dir=dst：目标侧更新，反向调用会处理（此处不动）
      fi
    done
  }
  reconcile_skills "$TARGET/.claude/skills" "$TARGET/.agents/skills"   # 引擎 trellis-* / trellis-local → .agents
  reconcile_skills "$TARGET/.agents/skills" "$TARGET/.claude/skills"   # .agents 侧用户自有 skill → .claude
  echo "  skill 双面对齐: 补齐 ×${recon_n} + 内容同步 ×${drift_n}（引擎 trellis-*/trellis-local/用户自有，两面一致）"
fi

# 5) Claude settings.json hooks 接线（自动幂等合并：按 matcher 定位、按 command 去重，保留用户既有内容）
python3 - "$TARGET" "$HERE/config-snippets/claude-settings.hooks.json" "$INSTALLED_HOOKS" "$GURU_HOOKS" <<'PYEOF'
import json, os, re, sys
target_root, snippet_path = sys.argv[1], sys.argv[2]
installed_hooks = set(sys.argv[3].split()) if len(sys.argv) > 3 else None
managed_hooks = set(sys.argv[4].split()) if len(sys.argv) > 4 else None
settings_path = os.path.join(target_root, ".claude", "settings.json")
snippet = json.load(open(snippet_path, encoding="utf-8"))
if os.path.isfile(settings_path):
    try:
        settings = json.load(open(settings_path, encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  ERROR: .claude/settings.json 非法 JSON，跳过自动合并（请人工处理）：{e}", file=sys.stderr)
        sys.exit(1)
else:
    settings = {}
if not isinstance(settings, dict):
    print("  ERROR: .claude/settings.json 根节点必须是对象", file=sys.stderr)
    sys.exit(1)
hooks = settings.setdefault("hooks", {})
if not isinstance(hooks, dict):
    print("  ERROR: .claude/settings.json 的 hooks 必须是对象", file=sys.stderr)
    sys.exit(1)
# 清理 guru-managed 但本平台未安装的悬空引用：切平台后 §3 已删该 hook 脚本，settings 不应再引用它
# （否则 PreToolUse 每次触发都跑一个不存在的脚本）。只动 guru-managed 集合内的引用，绝不碰用户自定义 hook。
removed = 0
if managed_hooks is not None and installed_hooks is not None:
    stale = managed_hooks - installed_hooks
    for event in list(hooks.keys()):
        entries = hooks.get(event)
        if not isinstance(entries, list):
            continue
        cleaned = []
        for entry in entries:
            if not isinstance(entry, dict):
                cleaned.append(entry)
                continue
            eh = entry.get("hooks")
            if isinstance(eh, list):
                kept = []
                dropped = 0
                for h in eh:
                    cmd = h.get("command", "") if isinstance(h, dict) else ""
                    # 锚定到 guru 项目命令形态 $CLAUDE_PROJECT_DIR/.claude/hooks/<name>：既避免误删 basename
                    # 同名但别处路径的用户 hook，也不误删指向 $HOME/.claude/hooks 的用户全局 hook
                    m = re.search(r'CLAUDE_PROJECT_DIR"?/\.claude/hooks/([A-Za-z0-9_.-]+\.sh)', cmd)
                    if m and m.group(1) in stale:
                        removed += 1
                        dropped += 1
                        continue   # 丢弃悬空 guru hook 引用
                    kept.append(h)
                # 仅当本轮确有 guru 悬空被剔除且导致该 entry 变空，才移除空壳；
                # 用户原本就空的 hooks 条目（占位）原样保留，不越界。
                if not kept and dropped > 0:
                    continue
                entry = {**entry, "hooks": kept}
            cleaned.append(entry)
        hooks[event] = cleaned
added = 0
for event, entries in snippet.get("hooks", {}).items():
    cur = hooks.setdefault(event, [])
    if not isinstance(cur, list):
        print(f"  ERROR: .claude/settings.json 的 hooks.{event} 必须是数组", file=sys.stderr)
        sys.exit(1)
    for entry in entries:
        # 只注册 command 指向"已安装" hook 脚本的条目；漏装的 hook 不注册（避免 settings 悬空引用、触发时跑不存在脚本）
        if installed_hooks is not None:
            kept = []
            for h in entry.get("hooks", []):
                m = re.search(r'CLAUDE_PROJECT_DIR"?/\.claude/hooks/([A-Za-z0-9_.-]+\.sh)', h.get("command", "") if isinstance(h, dict) else "")
                if m and m.group(1) not in installed_hooks:
                    continue
                kept.append(h)
            if not kept:
                continue
            entry = {**entry, "hooks": kept}
        existing = next((e for e in cur if isinstance(e, dict) and e.get("matcher") == entry.get("matcher")), None)
        if existing is None:
            cur.append(entry)
            added += len(entry.get("hooks", []))
        else:
            existing_hooks = existing.setdefault("hooks", [])
            if not isinstance(existing_hooks, list):
                print(f"  ERROR: .claude/settings.json matcher={entry.get('matcher')} 的 hooks 必须是数组", file=sys.stderr)
                sys.exit(1)
            for h in entry.get("hooks", []):
                cmd = h.get("command") if isinstance(h, dict) else None
                match_indices = [
                    i for i, existing_hook in enumerate(existing_hooks)
                    if isinstance(existing_hook, dict) and existing_hook.get("command") == cmd
                ]
                if not match_indices:
                    existing_hooks.append(h)
                    added += 1
                    continue
                first = match_indices[0]
                if existing_hooks[first] != h:
                    existing_hooks[first] = h
                for idx in reversed(match_indices[1:]):
                    del existing_hooks[idx]
os.makedirs(os.path.dirname(settings_path), exist_ok=True)
open(settings_path, "w", encoding="utf-8").write(json.dumps(settings, ensure_ascii=False, indent=2) + "\n")
print(f"  settings.json: hooks 接线完成（新增 {added} 条、清理悬空 {removed} 条，已有内容保留）")
PYEOF

# 5.5) Codex hooks 接线：Codex 通用模板只注入 workflow-state；Guru 专属 commit guard 由 overlay 追加。
# 不依赖目标预先存在 .codex/：安装顺序不能决定 commit guard 是否生效。
CODEX_HOOKS_TMP="$TARGET/.codex/hooks.json.tmp.$$"
rm -f "$CODEX_HOOKS_TMP"
python3 - "$TARGET" "$HERE/config-snippets/codex-hooks.hooks.json" "$CODEX_HOOKS_TMP" <<'PYEOF'
import json
import os
import shlex
import sys

target_root, snippet_path, tmp_path = sys.argv[1], sys.argv[2], sys.argv[3]
hooks_path = os.path.join(target_root, ".codex", "hooks.json")
snippet = json.load(open(snippet_path, encoding="utf-8"))
if os.path.isfile(hooks_path):
    try:
        config = json.load(open(hooks_path, encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  ERROR: .codex/hooks.json 非法 JSON，跳过自动合并（请人工处理）：{e}", file=sys.stderr)
        sys.exit(1)
else:
    config = {}
if not isinstance(config, dict):
    print("  ERROR: .codex/hooks.json 根节点必须是对象", file=sys.stderr)
    sys.exit(1)
hooks = config.setdefault("hooks", {})
if not isinstance(hooks, dict):
    print("  ERROR: .codex/hooks.json 的 hooks 必须是对象", file=sys.stderr)
    sys.exit(1)
added = 0
refreshed = 0
deduped = 0
legacy_commit_guard_cmd = "bash .codex/hooks/block-unstarted-commit.sh"
commit_guard_cmd = "bash " + shlex.quote(
    os.path.join(target_root, ".codex", "hooks", "block-unstarted-commit.sh")
)


def materialize_hook(hook):
    if not isinstance(hook, dict):
        return hook
    out = dict(hook)
    if out.get("command") == legacy_commit_guard_cmd:
        out["command"] = commit_guard_cmd
    return out


def command_matches(existing_hook, desired_command):
    if not isinstance(existing_hook, dict):
        return False
    existing_command = existing_hook.get("command")
    if existing_command == desired_command:
        return True
    if desired_command != commit_guard_cmd or not isinstance(existing_command, str):
        return False
    if existing_command == legacy_commit_guard_cmd:
        return True
    try:
        parts = shlex.split(existing_command)
    except ValueError:
        return False
    return (
        len(parts) == 2
        and parts[0] == "bash"
        and os.path.normpath(parts[1]).endswith(
            os.path.join(".codex", "hooks", "block-unstarted-commit.sh")
        )
    )


for event, entries in snippet.get("hooks", {}).items():
    cur = hooks.setdefault(event, [])
    if not isinstance(cur, list):
        print(f"  ERROR: .codex/hooks.json 的 hooks.{event} 必须是数组", file=sys.stderr)
        sys.exit(1)
    for entry in entries:
        desired_entry = dict(entry)
        desired_entry["hooks"] = [materialize_hook(h) for h in entry.get("hooks", [])]
        match_entries = [
            (i, e) for i, e in enumerate(cur)
            if isinstance(e, dict) and e.get("matcher") == entry.get("matcher")
        ]
        if not match_entries:
            cur.append(desired_entry)
            added += len(desired_entry.get("hooks", []))
            continue
        _first_idx, existing = match_entries[0]
        existing_hooks = existing.setdefault("hooks", [])
        if not isinstance(existing_hooks, list):
            print(f"  ERROR: .codex/hooks.json matcher={entry.get('matcher')} 的 hooks 必须是数组", file=sys.stderr)
            sys.exit(1)
        for idx, duplicate in reversed(match_entries[1:]):
            duplicate_hooks = duplicate.get("hooks")
            if not isinstance(duplicate_hooks, list):
                print(f"  ERROR: .codex/hooks.json matcher={entry.get('matcher')} 的重复 hooks 必须是数组", file=sys.stderr)
                sys.exit(1)
            existing_hooks.extend(duplicate_hooks)
            del cur[idx]
            deduped += 1
        for h in desired_entry.get("hooks", []):
            cmd = h.get("command") if isinstance(h, dict) else None
            match_indices = [
                i for i, existing_hook in enumerate(existing_hooks)
                if command_matches(existing_hook, cmd)
            ]
            if not match_indices:
                existing_hooks.append(h)
                added += 1
                continue
            first = match_indices[0]
            if existing_hooks[first] != h:
                existing_hooks[first] = h
                refreshed += 1
            for idx in reversed(match_indices[1:]):
                del existing_hooks[idx]
                deduped += 1
os.makedirs(os.path.dirname(hooks_path), exist_ok=True)
open(tmp_path, "w", encoding="utf-8").write(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
print(f"  codex hooks.json: block-unstarted-commit 接线完成（新增 {added} 条、刷新 {refreshed} 条、去重 {deduped} 条，已有内容保留）")
PYEOF
mkdir -p "$TARGET/.codex/hooks"
CODEX_GUARD="$TARGET/.codex/hooks/block-unstarted-commit.sh"
CODEX_GUARD_BACKUP=""
CODEX_GUARD_EXISTED=0
restore_codex_guard_on_error() {
  if [ "$CODEX_GUARD_EXISTED" = 1 ] && [ -n "$CODEX_GUARD_BACKUP" ] && [ -e "$CODEX_GUARD_BACKUP" ]; then
    mv "$CODEX_GUARD_BACKUP" "$CODEX_GUARD" >/dev/null 2>&1 || true
  else
    rm -f "$CODEX_GUARD"
  fi
}
if [ -e "$CODEX_GUARD" ] || [ -L "$CODEX_GUARD" ]; then
  CODEX_GUARD_EXISTED=1
  CODEX_GUARD_BACKUP="$TARGET/.codex/hooks/block-unstarted-commit.sh.bak.$$"
  if ! cp -p "$CODEX_GUARD" "$CODEX_GUARD_BACKUP"; then
    rm -f "$CODEX_HOOKS_TMP"
    echo "ERROR: Codex commit guard hook 备份失败" >&2
    exit 1
  fi
fi
if ! cp "$HERE/hooks/platform/block-unstarted-commit.sh" "$CODEX_GUARD"; then
  rm -f "$CODEX_HOOKS_TMP"
  restore_codex_guard_on_error
  echo "ERROR: Codex commit guard hook 复制失败" >&2
  exit 1
fi
if ! chmod +x "$CODEX_GUARD"; then
  rm -f "$CODEX_HOOKS_TMP"
  restore_codex_guard_on_error
  echo "ERROR: Codex commit guard hook chmod 失败" >&2
  exit 1
fi
if ! mv "$CODEX_HOOKS_TMP" "$TARGET/.codex/hooks.json"; then
  rm -f "$CODEX_HOOKS_TMP"
  restore_codex_guard_on_error
  echo "ERROR: Codex hooks.json 更新失败" >&2
  exit 1
fi
rm -f "$CODEX_GUARD_BACKUP"

# 6) workflow + SSOT 同步（升级通道：CLI update 不跟踪非 native workflow，spec/ 又是其保护路径）
# Source guru-template keeps <id>-workflow.md, while the packaged CLI bundle
# normalizes workflow files to <id>.md. Keep this resolver compatible with both
# layouts so the shipped overlay can install from dist/templates/guru/.
WORKFLOW_SRC="$ROOT/workflows/${WF_NAME}.md"
if [ ! -f "$WORKFLOW_SRC" ]; then
  WORKFLOW_SRC="$ROOT/workflows/${WF_NAME}-workflow.md"
fi
[ -f "$WORKFLOW_SRC" ] || { echo "ERROR: workflow 模板不存在: workflows/${WF_NAME}.md 或 workflows/${WF_NAME}-workflow.md"; exit 1; }
cp "$WORKFLOW_SRC" "$TARGET/.trellis/workflow.md"
echo "  workflow: $(basename "$WORKFLOW_SRC") → .trellis/workflow.md"
SPEC_SRC="$ROOT/specs/${SPEC_NAME}"
mkdir -p "$TARGET/.trellis/spec/guides" "$TARGET/.trellis/spec/conventions"
rm -rf "$TARGET/.trellis/spec/harness"
cp -R "$SPEC_SRC/harness" "$TARGET/.trellis/spec/harness"
cp "$SPEC_SRC/guides/"*.md "$TARGET/.trellis/spec/guides/"
cp "$SPEC_SRC/README.md" "$TARGET/.trellis/spec/"
# RECONCILE.md 平台特定（目前仅 flutter 提供）。切到不提供它的平台时清掉上一平台残留，
# 避免旧 reconcile 指引被 agent 继续消费。
if [ -f "$SPEC_SRC/RECONCILE.md" ]; then
  cp "$SPEC_SRC/RECONCILE.md" "$TARGET/.trellis/spec/"
else
  rm -f "$TARGET/.trellis/spec/RECONCILE.md"
fi
# 切平台残留治理：先清掉目标里他平台的样例 *.project-conventions.md（与 RECONCILE.md 同等对待，避免
# go 项目里躺着 flutter 的 calorie/seek 样例孤儿）。project-conventions.md 无前缀、不被该 glob 匹配，
# 且下方循环显式保护，用户权威取值绝不受损。
rm -f "$TARGET/.trellis/spec/conventions/"*.project-conventions.md 2>/dev/null || true
# conventions：项目取值（project-conventions.md）绝不覆盖；模板/样例/索引可刷新
for f in "$SPEC_SRC/conventions/"*.md; do
  base="$(basename "$f")"
  if [ "$base" = "project-conventions.md" ] && [ -f "$TARGET/.trellis/spec/conventions/project-conventions.md" ]; then
    continue
  fi
  cp "$f" "$TARGET/.trellis/spec/conventions/$base"
done
if [ -f "$TARGET/.trellis/spec/conventions/project-conventions.md" ]; then
  echo "  spec: harness/guides/README 已刷新；conventions/project-conventions.md 保留未动"
else
  echo "  spec: harness/guides/README 已刷新；⚠ conventions/project-conventions.md 缺失（按模板填写，见收尾）"
fi

# 7) Guru official supervision defaults (child-key merge, no user-value overwrite)
CONFIG_PATCH_ARGS=(ensure-supervision-defaults --root "$TARGET" --platform "$PLATFORM")
if [ -n "$GURU_ADVERSARIAL_ENABLED" ]; then
  CONFIG_PATCH_ARGS+=(--adversarial-enabled "$GURU_ADVERSARIAL_ENABLED")
fi
python3 "$TARGET/.trellis/scripts/guru/guru_config_patch.py" "${CONFIG_PATCH_ARGS[@]}"

# 7.1) config 合并（幂等：marker 检测）
python3 - "$TARGET" "$ANALYZE_CMD" <<'PYEOF'
import os, sys
t = sys.argv[1]
analyze = sys.argv[2] if len(sys.argv) > 2 else "flutter analyze"
MARK = "# >>> guru-overlay >>>"
END = "# <<< guru-overlay <<<"

def merge(path, block, create_header=""):
    cur = open(path, encoding="utf-8").read() if os.path.isfile(path) else create_header
    if MARK in cur:
        import re
        cur = re.sub(rf"{MARK}.*?{END}\n?", "", cur, flags=re.S)
    cur = cur.rstrip() + "\n\n" + MARK + "\n" + block.strip() + "\n" + END + "\n"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(cur)
    print(f"  merged: {os.path.relpath(path, t)}")

merge(os.path.join(t, ".trellis", "worktree.yaml"),
f'''verify:
  - "python3 .trellis/scripts/guru/guru_gate.py auto"
  - "{analyze}"''')

# config.yaml 若在 marker 块外已有未注释的顶层 hooks: 键，guru 块注入的 hooks: 会与之形成重复顶层键，
# YAML last-wins 会静默吞掉用户的 after_*/before_* → 警告（不自动解析合并用户 YAML，避免误判其结构）。
_cfg_path = os.path.join(t, ".trellis", "config.yaml")
if os.path.isfile(_cfg_path):
    import re as _re
    _outside = _re.sub(rf"{MARK}.*?{END}\n?", "", open(_cfg_path, encoding="utf-8").read(), flags=_re.S)
    if _re.search(r"(?m)^hooks\s*:", _outside):
        sys.stderr.write(
            "  ⚠ config.yaml 在 guru marker 块外已有顶层 hooks: 键：guru 注入的 hooks"
            "(after_create/before_start) 会形成重复顶层键，YAML last-wins 将静默覆盖你的 "
            "after_*/before_* hook。请把你的 hook 手动并入 guru-overlay marker 块内（或确认无冲突）。\n")

task_utils = os.path.join(t, ".trellis", "scripts", "common", "task_utils.py")
supports_blocking_start = os.path.isfile(task_utils) and "run_blocking_task_hooks" in open(
    task_utils, encoding="utf-8"
).read()
hook_lines = [
    "hooks:",
    "  after_create:",
    '    - "python3 .trellis/scripts/guru/guru_after_create.py"',
    "  after_start:",
    '    - "python3 .trellis/scripts/guru/guru_after_start.py"',
]
if supports_blocking_start:
    hook_lines.extend([
        "  # Blocking hook supported by this checkout-local Core.",
        "  before_start:",
        '    - "python3 .trellis/scripts/guru/guru_gate.py check-start"',
    ])
else:
    hook_lines.extend([
        "  # Official Core has no blocking before_start hook.",
        "  # Use guru_task.py start; after_start records direct official bypass as advisory evidence.",
    ])
merge(os.path.join(t, ".trellis", "config.yaml"), "\n".join(hook_lines))
PYEOF

# 7.5) by-layer 项目 spec 骨架 + bootstrap 任务接线
# 平台切换检测：.trellis/spec 下若有非当前平台、非方法学的层目录（前一平台残留），
# guru_after_create 会把它误注入后续任务基线（混入他平台上下文）→ 警告（不自动删，
# 用户可能有意保留多平台；如确属残留请手动归档/迁移）。
for D in "$TARGET/.trellis/spec"/*/; do
  [ -d "$D" ] || continue
  name="$(basename "$D")"
  case " $LAYERS harness conventions guides " in
    *" $name "*) ;;
    *) echo "  by-layer: ⚠ 检测到非当前平台层 spec/$name/（疑似前一平台残留，后续任务可能误加载，请确认是否归档/迁移）" ;;
  esac
done
# by-layer 空骨架随 spec 包由 `trellis init -t` 装入 .trellis/spec/<layer>/；此处兜底：
# 缺失则从 spec 包补装（不覆盖已被 bootstrap 填实的内容——目录已存在就跳过）。
mkdir -p "$TARGET/.trellis/spec"   # 非标准 target 可能有 .trellis 无 spec，先建父目录免 cp -R 失败
for L in $LAYERS; do
  # 缺失、或目录存在但为空（被外部清空 / 未填）都补装骨架；已被 bootstrap 填实(非空)的保留不覆盖。
  if [ -d "$SPEC_SRC/$L" ] && { [ ! -d "$TARGET/.trellis/spec/$L" ] || [ -z "$(ls -A "$TARGET/.trellis/spec/$L" 2>/dev/null)" ]; }; then
    rm -rf "$TARGET/.trellis/spec/$L"
    cp -R "$SPEC_SRC/$L" "$TARGET/.trellis/spec/$L"
    echo "  by-layer: 补装 spec/$L/（骨架）"
  fi
done
# bootstrap prd：init 生成的 native 版指向 guru 不安装的 backend/frontend（错配）；
# 覆盖成 guru 平台感知版（引导 agent 扫真实项目填 by-layer + conventions 槽位）。
BOOT_DIR="$TARGET/.trellis/tasks/00-bootstrap-guidelines"
# 写最小 task.json（对齐 init 的 24 字段）；新建任务、或目录已存在但缺 task.json 时复用。
write_boot_task_json() {
  # .developer 是多行 key=value（name=.. / initialized_at=..）：只取 name= 值（对齐官方 get_developer）。
  # cat 全文会把整文件塞进 task.json 的 creator/assignee（嵌字面换行 + name= 前缀），破坏 task.py --mine 过滤。
  # || true：.developer 缺失时 sed 经 pipefail 返回非 0，裸赋值在 set -e 下会中止脚本；缺失则 fallback guru。
  local dev
  dev="$(sed -n 's/^name=//p' "$TARGET/.trellis/.developer" 2>/dev/null | head -1)" || true
  [ -n "$dev" ] || dev=guru
  python3 - "$BOOT_DIR" "$dev" "$PLATFORM" "$LAYERS" "$(date +%F)" <<'PYEOF'
import json, os, sys
boot_dir, dev, platform, layers, today = sys.argv[1:6]
related = [f".trellis/spec/{l}/" for l in layers.split()] + [".trellis/spec/conventions/project-conventions.md"]
task = {
    "id": "00-bootstrap-guidelines", "name": "00-bootstrap-guidelines",
    "title": "Bootstrap Guidelines",
    "description": "Fill in project development guidelines for AI agents",
    "status": "in_progress", "dev_type": "docs", "scope": None, "package": None,
    "priority": "P1", "creator": dev, "assignee": dev,
    "createdAt": today, "completedAt": None, "branch": None, "base_branch": None,
    "worktree_path": None, "commit": None, "pr_url": None,
    "subtasks": [], "children": [], "parent": None,
    "relatedFiles": related,
    "notes": f"guru bootstrap task (overlay-created, {platform} project)",
    "meta": {},
}
with open(os.path.join(boot_dir, "task.json"), "w", encoding="utf-8") as fh:
    json.dump(task, fh, ensure_ascii=False, indent=2)
PYEOF
}
if [ -f "$BOOTSTRAP_PRD" ]; then
  if [ -d "$BOOT_DIR" ]; then
    # 部分 init 可能留下任务目录却缺 task.json → 补建，避免下游任务工具见到非法任务目录
    if [ ! -f "$BOOT_DIR/task.json" ]; then
      echo "  bootstrap: ⚠ task.json 缺失，补建任务元数据"
      write_boot_task_json
    fi
    if [ -f "$BOOT_DIR/prd.md" ] && cmp -s "$BOOTSTRAP_PRD" "$BOOT_DIR/prd.md"; then
      echo "  bootstrap: prd.md 已是 guru ${PLATFORM} 版（幂等跳过）"
    elif [ -f "$BOOT_DIR/prd.md" ] && grep -q guru "$BOOT_DIR/prd.md"; then
      # 已是 guru 版（用户可能已编辑 / 他平台 guru 版）：保留在制内容，不覆盖、不备份。
      # （此分支无覆盖动作，备份纯属多余且每次 apply 累积一份 → 破坏幂等；native 错配版无 "guru"
      #   标记，走下面 else 覆盖修正，那里才有真实覆盖、才需备份。）
      echo "  bootstrap: prd.md 已是 guru 版（保留在制内容，不覆盖）"
      echo "  bootstrap: 如需重置为 guru ${PLATFORM} 模板：cp $BOOTSTRAP_PRD ${BOOT_DIR#$TARGET/}/prd.md"
    else
      # native 错配版（无 "guru" 标记，指向 guru 不装的 backend/frontend）或无 prd：覆盖成 guru 版。
      # 有旧文件先 mktemp 备份（防同秒重复 apply 覆盖上一份备份）。
      if [ -f "$BOOT_DIR/prd.md" ]; then
        backup="$(mktemp "$BOOT_DIR/prd.md.pre-guru.$(date +%Y%m%d%H%M%S).XXXXXX")"
        cp "$BOOT_DIR/prd.md" "$backup"
        echo "  bootstrap: 备份 native prd.md → ${backup#$TARGET/}"
      fi
      cp "$BOOTSTRAP_PRD" "$BOOT_DIR/prd.md"
      echo "  bootstrap: prd.md → guru ${PLATFORM} 平台感知版（覆盖 native 错配）"
    fi
  else
    # init 未建该任务（非首次 init / 已 archive）。先查归档：已归档=用户做完过，绝不复活成 in_progress。
    archived="$(find "$TARGET/.trellis/tasks/archive" -mindepth 2 -maxdepth 2 -type d -name '00-bootstrap-guidelines' -print -quit 2>/dev/null || true)"
    if [ -n "$archived" ]; then
      echo "  bootstrap: 已归档（${archived#$TARGET/}），跳过重建（避免复活已完成任务）"
    else
      # 按需建最小骨架
      mkdir -p "$BOOT_DIR"
      cp "$BOOTSTRAP_PRD" "$BOOT_DIR/prd.md"
      write_boot_task_json
      echo "  bootstrap: init 未建任务 → 已创建 00-bootstrap-guidelines（guru ${PLATFORM}）"
    fi
  fi
else
  echo "  ⚠ bootstrap prd 缺失: $BOOTSTRAP_PRD（跳过 bootstrap 接线）"
fi

if gitnexus_requested; then
  bootstrap_gitnexus
fi

# All target mutations are complete. This exact digest is the only state an
# automatic failed-apply recovery may overwrite; later target drift fails closed.
if [ -n "$ROLLBACK_BUNDLE" ]; then
  checkpoint_rollback_bundle "$TARGET" "$APPLY_RECOVERY_BUNDLE"
fi

# 8) 装配自检（失败即非零退出；警告不阻塞）
echo ""
echo "== 装配自检 =="
FAIL=0

# 用 ast.parse 做语法检查：py_compile 会写 __pycache__ 副产物，破坏装配幂等性
if python3 -c "import ast,sys; [ast.parse(open(f,encoding='utf-8').read()) for f in sys.argv[1:]]" \
    "$TARGET/.trellis/scripts/guru/guru_gate.py" \
	    "$TARGET/.trellis/scripts/guru/guru_risk.py" \
	    "$TARGET/.trellis/scripts/guru/guru_contract.py" \
	    "$TARGET/.trellis/scripts/guru/guru_delivery_policy.py" \
	    "$TARGET/.trellis/scripts/guru/guru_review_record.py" \
	    "$TARGET/.trellis/scripts/guru/guru_after_create.py" \
	    "$TARGET/.trellis/scripts/guru/guru_after_start.py" \
	    "$TARGET/.trellis/scripts/guru/guru_task.py" \
	    "$TARGET/.trellis/scripts/guru/guru_config_patch.py" \
    "$TARGET/.trellis/scripts/guru/guru_supervise.py" 2>/dev/null; then
  echo "  ✓ guru 脚本语法"
else
  echo "  ✗ guru 脚本语法检查失败"; FAIL=1
fi

# 循环导入冒烟：ast.parse 抓不到 guru_risk↔guru_gate↔guru_supervise 的导入环；-B 不写 __pycache__ 保幂等
if PYTHONPATH="$TARGET/.trellis/scripts/guru" python3 -B -c "import guru_risk, guru_contract, guru_delivery_policy, guru_review_record, guru_gate, guru_supervise, guru_task" 2>/dev/null; then
  echo "  ✓ guru 脚本可导入（无循环依赖）"
else
  echo "  ✗ guru 脚本导入失败（循环依赖 / 缺失模块）"; FAIL=1
fi

if python3 - "$TARGET" <<'PYEOF'
import re, sys
content = open(f"{sys.argv[1]}/.trellis/workflow.md", encoding="utf-8").read()
TAG = re.compile(r"\[workflow-state:([A-Za-z0-9_-]+)\]\s*\n(.*?)\n\s*\[/workflow-state:\1\]", re.DOTALL)
blocks = TAG.findall(content)
oversize = [n for n, b in blocks if len(b.strip().encode("utf-8")) > 400]
sys.exit(0 if len(blocks) >= 6 and not oversize else 1)
PYEOF
then
  echo "  ✓ workflow breadcrumb（≥6 块且均 ≤400B）"
else
  echo "  ✗ workflow breadcrumb 解析/字节预算失败"; FAIL=1
fi

if grep -q "run_blocking_task_hooks" "$TARGET/.trellis/scripts/common/task_utils.py" 2>/dev/null; then
  if grep -q 'guru_gate.py check-start' "$TARGET/.trellis/config.yaml"; then
    echo "  ✓ core 支持 before_start 阻断钩子"
  else
    echo "  ✗ core 支持 before_start，但 Guru marker 未接线"; FAIL=1
  fi
else
  # Official Trellis exposes non-blocking after_* hooks. Do not install a
  # before_start key that Core would silently ignore; the guarded wrapper is
  # the writable high-risk entry, after_start records bypass truthfully, and
  # the Codex commit guard retains the irreversible boundary.
  if grep -q 'guru_gate.py check-start' "$TARGET/.trellis/config.yaml"; then
    echo "  ✗ official Core 不支持 before_start，但 config 仍宣称硬 Gate"; FAIL=1
  elif [ -x "$TARGET/.trellis/scripts/guru/guru_task.py" ] \
      && grep -q 'guru_after_start.py' "$TARGET/.trellis/config.yaml" \
      && [ -x "$TARGET/.codex/hooks/block-unstarted-commit.sh" ]; then
    echo "  ✓ official Core compensated：guarded wrapper + after_start evidence + Codex commit guard"
  else
    echo "  ✗ official Core compensated lifecycle 接线不完整"; FAIL=1
  fi
fi

if [ -f "$TARGET/scripts/check_workflow_compliance.py" ]; then
  if (cd "$TARGET" && python3 scripts/check_workflow_compliance.py >/dev/null 2>&1); then
    echo "  ✓ 项目 workflow 合规检查"
  else
    echo "  ✗ 项目 workflow 合规检查未通过（cd $TARGET && python3 scripts/check_workflow_compliance.py）"; FAIL=1
  fi
fi

if [ "$USED_PROJECT_MIRROR" = 1 ]; then
  if python3 "$MIRROR_SCRIPT" --check --root "$TARGET" >/dev/null 2>&1; then
    echo "  ✓ 平台 skill 镜像无漂移"
  else
    echo "  ✗ 平台 skill 镜像漂移（python3 scripts/sync_platform_skills.py --check）"; FAIL=1
  fi
  if [ -d "$TARGET/.agents/skills/design-grill" ] && [ -d "$TARGET/.claude/skills/design-grill" ]; then
    echo "  ✓ design-grill 两面存在（项目镜像模式）"
  else
    echo "  ✗ design-grill 两面缺失（项目镜像脚本必须同步 shared skill 到 .agents/.claude）"; FAIL=1
  fi
else
  # §4.5 双面对齐的不变量：.agents/skills 与 .claude/skills 必须内容一致（名字+内容，排除脏文件）。
  # 平台 configurator / trellis update 会向单面写 skill（如 Codex 的 trellis-start 只进 .agents），
  # 制造漂移；本检查在每次 apply 后做【内容级】断言（非仅目录名），兜底捕获 §4.5 自身的 bug（含
  # mtime 启发式在 equal-mtime / 多文件内部漂移下的盲区）。
  if diff -rq -x .DS_Store -x __pycache__ "$TARGET/.agents/skills" "$TARGET/.claude/skills" >/dev/null 2>&1; then
    echo "  ✓ skill 两面一致（.agents/skills == .claude/skills，含内容）"
  else
    echo "  ✗ skill 两面不一致（§4.5 对齐异常，见 diff）："
    diff -rq -x .DS_Store -x __pycache__ "$TARGET/.agents/skills" "$TARGET/.claude/skills" 2>&1 | sed 's/^/      /'
    FAIL=1
  fi
fi

echo ""
if [ "$FAIL" != 0 ]; then
  echo "== 装配完成但自检存在失败项（见上 ✗），请处理后重跑 =="
  exit 1
fi
echo "== 装配完成，自检通过。剩余人工事项 =="
echo "1) 项目约定：确认 $TARGET/.trellis/spec/conventions/project-conventions.md 已按模板填写（缺失时从 .template/样例取值建立）"
echo "2) 老目录拦截：如项目有禁止新建的老目录，填 $TARGET/.claude/hooks/block-legacy-dirs.sh 的 LEGACY_PATTERNS"
echo "3) Codex hooks：用户级 ~/.codex/config.toml 开 [features].hooks=true，并在 Codex /hooks 中 trust 本项目 hooks"
echo "4) 人工 Gate 通道：默认 strict（用户终端）；如需对话确认+agent 代跑，在 config.yaml 顶层加 guru.gate_mode: soft（见 workflow 机制节）"
echo ""
echo "维护规约：每次 trellis update / 平台 reconfigure 后补跑一次本脚本。"
echo "  原因：平台 configurator 会向单面写 skill（如 Codex 的 trellis-start 只进 .agents/skills），"
echo "  使 .agents/skills 与 .claude/skills 漂移；重跑 apply.sh 的 §4.5 双面对齐即拉平（幂等）。"
if [ -n "$ROLLBACK_BUNDLE" ]; then
  # Publish `applied` only after every other fallible apply step/output. Ignore
  # signals during the tiny publish/disarm window; finalize errors still reach
  # the EXIT recovery trap while the bundle remains prepared.
  trap '' INT TERM HUP
  finalize_rollback_bundle "$TARGET" "$APPLY_RECOVERY_BUNDLE" "$APPLY_RECOVERY_EXPECTED_DIGEST"
  APPLY_RECOVERY_ARMED=0
  trap - EXIT INT TERM HUP
  echo "  rollback: 已生成外部 preimage + post-apply CAS bundle（不包含 .git）" || true
fi
