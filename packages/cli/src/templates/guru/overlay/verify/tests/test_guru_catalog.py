import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock

VERIFY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if VERIFY_DIR not in sys.path:
    sys.path.insert(0, VERIFY_DIR)

import guru_catalog as catalog


SPEC_IDS = (
    "guru-flutter-client",
    "guru-go-backend",
    "guru-h5-web",
    "guru-ios-native",
)
WORKFLOW_PATHS = {
    "guru-client": "guru-client-workflow.md",
    "guru-go": "guru-go-workflow.md",
    "guru-h5": "guru-h5-workflow.md",
    "guru-ios": "guru-ios-workflow.md",
}


class CatalogResolverTests(unittest.TestCase):
    def make_registry(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "guru-template"
        (root / "specs").mkdir(parents=True)
        (root / "workflows").mkdir()
        templates = []
        for template_id in SPEC_IDS:
            spec_root = root / "specs" / template_id
            (spec_root / "nested").mkdir(parents=True)
            (spec_root / "README.md").write_text(f"# {template_id}\n", encoding="utf-8")
            (spec_root / "nested" / "rules.md").write_text("rules\n", encoding="utf-8")
            templates.append(self.entry(template_id, "spec", f"specs/{template_id}"))
        for template_id, filename in WORKFLOW_PATHS.items():
            (root / "workflows" / filename).write_text(f"# {template_id}\n", encoding="utf-8")
            templates.append(self.entry(template_id, "workflow", f"workflows/{filename}"))
        self.write_index(root, templates)
        return root

    @staticmethod
    def entry(template_id, kind, relative_path):
        return {
            "id": template_id,
            "type": kind,
            "name": template_id,
            "description": f"{template_id} fixture",
            "path": relative_path,
            "tags": ["guru"],
        }

    @staticmethod
    def write_index(root, templates, **overrides):
        data = {"version": 1, "templates": templates}
        data.update(overrides)
        (root / "index.json").write_text(
            json.dumps(data, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_load_requires_stable_complete_registry(self):
        root = self.make_registry()
        loaded = catalog.CatalogResolver().load(root)
        self.assertEqual(tuple(entry.template_id for entry in loaded.entries), catalog.EXPECTED_TEMPLATE_IDS)
        self.assertEqual(len(loaded.source_digest), 64)
        self.assertEqual(loaded.registry_root, root.resolve())

    def test_workflow_is_one_file_and_spec_is_ordered_tree(self):
        root = self.make_registry()
        resolver = catalog.CatalogResolver()
        loaded = resolver.load(root)
        workflow = resolver.resolve(loaded, "guru-client", "release-123")
        spec = resolver.resolve(loaded, "guru-flutter-client", "release-123")
        self.assertEqual(workflow.entry.kind, catalog.TemplateKind.WORKFLOW)
        self.assertEqual(workflow.files, (PurePosixPath("workflows/guru-client-workflow.md"),))
        self.assertEqual(spec.entry.kind, catalog.TemplateKind.SPEC)
        self.assertEqual(
            spec.files,
            (
                PurePosixPath("specs/guru-flutter-client/README.md"),
                PurePosixPath("specs/guru-flutter-client/nested/rules.md"),
            ),
        )

    def test_content_digest_is_deterministic_and_binds_ref_path_and_bytes(self):
        root = self.make_registry()
        resolver = catalog.CatalogResolver()
        loaded = resolver.load(root)
        first = resolver.resolve(loaded, "guru-flutter-client", "release-a")
        repeated = resolver.resolve(resolver.load(root), "guru-flutter-client", "release-a")
        other_ref = resolver.resolve(loaded, "guru-flutter-client", "release-b")
        self.assertEqual(first.content_digest, repeated.content_digest)
        self.assertNotEqual(first.content_digest, other_ref.content_digest)
        (root / "specs" / "guru-flutter-client" / "README.md").write_text("changed\n", encoding="utf-8")
        changed = resolver.resolve(resolver.load(root), "guru-flutter-client", "release-a")
        self.assertNotEqual(first.content_digest, changed.content_digest)

    def test_duplicate_ids_fail_closed_with_all_conflicts(self):
        root = self.make_registry()
        raw = json.loads((root / "index.json").read_text(encoding="utf-8"))
        raw["templates"].append(dict(raw["templates"][0]))
        self.write_index(root, raw["templates"])
        with self.assertRaisesRegex(catalog.TemplateIdDuplicate, "guru-flutter-client"):
            catalog.CatalogResolver().load(root)

    def test_schema_and_stable_id_failures_are_rejected(self):
        cases = (
            ("version", lambda raw: raw.update(version=2), catalog.CatalogSchemaInvalid),
            ("unknown field", lambda raw: raw.update(extra=True), catalog.CatalogSchemaInvalid),
            ("bad type", lambda raw: raw["templates"][0].update(type="asset"), catalog.CatalogSchemaInvalid),
            ("bad id", lambda raw: raw["templates"][0].update(id="Guru Bad"), catalog.CatalogSchemaInvalid),
            ("missing stable id", lambda raw: raw["templates"].pop(), catalog.CatalogSchemaInvalid),
        )
        for label, mutate, error_type in cases:
            with self.subTest(label=label):
                root = self.make_registry()
                raw = json.loads((root / "index.json").read_text(encoding="utf-8"))
                mutate(raw)
                (root / "index.json").write_text(json.dumps(raw), encoding="utf-8")
                with self.assertRaises(error_type):
                    catalog.CatalogResolver().load(root)

    def test_kind_specific_path_type_mismatch_fails_closed(self):
        root = self.make_registry()
        raw = json.loads((root / "index.json").read_text(encoding="utf-8"))
        next(item for item in raw["templates"] if item["id"] == "guru-client")["path"] = "specs/guru-flutter-client"
        self.write_index(root, raw["templates"])
        with self.assertRaises(catalog.TemplatePathInvalid):
            catalog.CatalogResolver().load(root)

    def test_missing_paths_fail_closed(self):
        root = self.make_registry()
        raw = json.loads((root / "index.json").read_text(encoding="utf-8"))
        next(item for item in raw["templates"] if item["id"] == "guru-client")["path"] = "workflows/missing.md"
        self.write_index(root, raw["templates"])
        with self.assertRaises(catalog.TemplateMissing):
            catalog.CatalogResolver().load(root)

    def test_absolute_parent_and_backslash_paths_are_rejected(self):
        for invalid_path in ("/tmp/workflow.md", "../workflow.md", "workflows/../workflow.md", "workflows\\workflow.md"):
            with self.subTest(path=invalid_path):
                root = self.make_registry()
                raw = json.loads((root / "index.json").read_text(encoding="utf-8"))
                next(item for item in raw["templates"] if item["id"] == "guru-client")["path"] = invalid_path
                self.write_index(root, raw["templates"])
                with self.assertRaises(catalog.TemplatePathInvalid):
                    catalog.CatalogResolver().load(root)

    def test_workflow_symlink_escape_is_rejected(self):
        root = self.make_registry()
        outside = root.parent / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        workflow = root / "workflows" / "guru-client-workflow.md"
        workflow.unlink()
        workflow.symlink_to(outside)
        with self.assertRaises(catalog.TemplatePathInvalid):
            catalog.CatalogResolver().load(root)

    def test_spec_tree_rejects_nested_symlinks(self):
        root = self.make_registry()
        outside = root.parent / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        (root / "specs" / "guru-flutter-client" / "linked.md").symlink_to(outside)
        with self.assertRaises(catalog.TemplatePathInvalid):
            catalog.CatalogResolver().load(root)

    def test_workflow_swap_to_symlink_before_open_fails_closed(self):
        root = self.make_registry()
        resolver = catalog.CatalogResolver()
        loaded = resolver.load(root)
        outside = root.parent / "outside.md"
        outside.write_bytes(b"outside bytes must never be accepted\n")
        workflow = root / "workflows" / "guru-client-workflow.md"
        original_open_leaf = catalog._open_leaf_fd
        swap_observed = False

        def swap_before_open(parent_fd, leaf, label, missing_error):
            nonlocal swap_observed
            if label == "guru-client" and not swap_observed:
                workflow.unlink()
                workflow.symlink_to(outside)
                swap_observed = True
            return original_open_leaf(parent_fd, leaf, label, missing_error)

        with mock.patch.object(catalog, "_open_leaf_fd", side_effect=swap_before_open):
            with self.assertRaises(catalog.TemplatePathInvalid):
                resolver.resolve(loaded, "guru-client", "release-123")
        self.assertTrue(swap_observed)

    def test_root_replacement_after_load_requires_reload(self):
        root = self.make_registry()
        resolver = catalog.CatalogResolver()
        loaded = resolver.load(root)
        old_root = root.with_name("guru-template-old")
        root.rename(old_root)
        shutil.copytree(old_root, root)

        with self.assertRaisesRegex(catalog.CatalogRootInvalid, "identity changed"):
            resolver.resolve(loaded, "guru-client", "release-123")

    def test_ancestor_symlink_replacement_is_rejected_even_for_same_root_inode(self):
        root = self.make_registry()
        resolver = catalog.CatalogResolver()
        loaded = resolver.load(root)
        ancestor = root.parent
        moved = ancestor.with_name(f"{ancestor.name}-moved")
        ancestor.rename(moved)
        try:
            ancestor.symlink_to(moved, target_is_directory=True)
            with self.assertRaisesRegex(catalog.CatalogRootInvalid, "without following any path component"):
                resolver.resolve(loaded, "guru-client", "release-123")
        finally:
            if ancestor.is_symlink():
                ancestor.unlink()
            if moved.exists():
                moved.rename(ancestor)

    def test_multi_file_update_during_resolve_never_returns_a_mixed_digest(self):
        root = self.make_registry()
        resolver = catalog.CatalogResolver()
        loaded = resolver.load(root)
        mutate_target = root / "specs/guru-flutter-client/nested/rules.md"
        original_read = catalog._read_open_file
        mutated = False

        def mutate_between_files(file_descriptor, relative_path, *, expected_identity):
            nonlocal mutated
            snapshot = original_read(
                file_descriptor,
                relative_path,
                expected_identity=expected_identity,
            )
            if relative_path.as_posix().endswith("README.md") and not mutated:
                mutate_target.write_text("new generation\n", encoding="utf-8")
                mutated = True
            return snapshot

        with mock.patch.object(catalog, "_read_open_file", side_effect=mutate_between_files):
            with self.assertRaisesRegex(catalog.TemplatePathInvalid, "changed while pinned snapshot"):
                resolver.resolve(loaded, "guru-flutter-client", "release-123")
        self.assertTrue(mutated)

    def test_directory_digest_rejects_root_replacement_during_read(self):
        root = self.make_registry()
        old_root = root.with_name("guru-template-digest-old")
        original_collect = catalog._collect_regular_tree
        replaced = False

        def replace_after_snapshot(root_fd, relative_root):
            nonlocal replaced
            snapshots = original_collect(root_fd, relative_root)
            if not replaced:
                root.rename(old_root)
                shutil.copytree(old_root, root)
                replaced = True
            return snapshots

        with mock.patch.object(catalog, "_collect_regular_tree", side_effect=replace_after_snapshot):
            with self.assertRaisesRegex(catalog.CatalogRootInvalid, "changed during pinned read"):
                catalog.directory_digest(root)
        self.assertTrue(replaced)

    def test_official_source_failure_is_explicit_and_never_reads_bundled(self):
        class FailingOfficialSource:
            def __init__(self):
                self.official_reads = 0
                self.bundled_reads = 0

            def materialize(self, source_ref):
                self.official_reads += 1
                raise OSError(f"source unavailable: {source_ref}")

        source = FailingOfficialSource()
        with self.assertRaisesRegex(catalog.SourceUnavailable, "release-123"):
            catalog.CatalogResolver().resolve_official(source, "guru-client", "release-123")
        self.assertEqual(source.official_reads, 1)
        self.assertEqual(source.bundled_reads, 0)

    def test_raw_rc_zero_blank_fallback_is_preserved_as_failure(self):
        root = self.make_registry()
        observation = catalog.observe_official_install(
            returncode=0,
            stdout="Template missing\nFalling back to blank templates...\n",
            stderr="",
            staging_root=root.parent,
        )
        self.assertEqual(observation.raw_returncode, 0)
        self.assertTrue(observation.blank_fallback_observed)
        self.assertFalse(observation.succeeded)
        self.assertEqual(observation.failure_kind, "OfficialBlankFallback")

    def test_nonzero_official_result_stays_failed_with_raw_output(self):
        root = self.make_registry()
        observation = catalog.observe_official_install(
            returncode=17,
            stdout="partial stdout\n",
            stderr="network failure\n",
            staging_root=root.parent,
        )
        self.assertEqual(observation.raw_returncode, 17)
        self.assertEqual(observation.raw_stderr, "network failure\n")
        self.assertFalse(observation.succeeded)
        self.assertEqual(observation.failure_kind, "OfficialCommandFailed")


if __name__ == "__main__":
    unittest.main()
