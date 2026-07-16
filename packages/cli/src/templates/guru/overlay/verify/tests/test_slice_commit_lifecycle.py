from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


VERIFY_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VERIFY_DIR))

import guru_contract  # noqa: E402
import guru_gate  # noqa: E402
import guru_review_record  # noqa: E402


class SliceCommitLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.task = self.root / ".trellis" / "tasks" / "task"
        self.task.mkdir(parents=True)
        (self.root / ".trellis" / "config.yaml").write_text(
            "guru:\n"
            "  supervision:\n"
            "    high_risk_review_provider_policy: codex\n",
            encoding="utf-8",
        )
        self._write("lib/a.txt", b"base\n")
        self._write("lib/b.txt", b"base-b\n")
        self._write(
            "packages/cli/src/templates/guru/overlay/verify/guru_supervise.py",
            b"# supervisor\n",
        )
        self._write(
            "packages/cli/src/templates/guru/overlay/verify/guru_gate.py",
            b"# gate\n",
        )
        self._write(
            ".trellis/scripts/guru/guru_supervise.py",
            b"# installed supervisor\n",
        )
        self._write(
            ".trellis/scripts/guru/guru_gate.py",
            b"# installed gate\n",
        )
        self._write_task_inputs()
        self._git("init")
        self._git("config", "user.name", "Slice Test")
        self._git("config", "user.email", "slice@example.test")
        self._git("add", "--", ".")
        self._git("commit", "-m", "baseline")
        self._write_contract(["lib/a.txt", "lib/b.txt"])
        self._write_packet("U1", ["lib/a.txt"])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write(self, rel: str, data: bytes) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {result.stderr or result.stdout}")
        return result.stdout.strip()

    def _write_task_inputs(self) -> None:
        (self.task / "task.json").write_text(
            json.dumps({"status": "in_progress", "route": "full_chain", "risk": "high"}),
            encoding="utf-8",
        )
        (self.task / "prd.md").write_bytes(
            b"# Requirements\r\n\r\n## BHV-001 First\r\n\r\nExact bytes.\r\n"
            b"\r\n## BHV-002 Second\r\n\r\nOther bytes.\r\n"
        )
        chapter = self.task / "design-package" / "chapters" / "receipt.md"
        chapter.parent.mkdir(parents=True)
        chapter.write_text(
            "# Receipt\n\n## Contract\n\nBind every byte.\n",
            encoding="utf-8",
        )

    def _write_contract(self, paths: list[str]) -> None:
        contract = guru_contract.default_contract(
            guru_contract.ROUTE_FULL_CHAIN,
            guru_contract.RISK_HIGH,
            created_by="test",
        )
        contract["scope"]["allowed_paths"] = paths
        contract["scope"]["max_files"] = None
        (self.task / "gate-contract.json").write_text(
            json.dumps(contract),
            encoding="utf-8",
        )

    def _packet(self, slice_id: str, targets: list[str], depends_on=None) -> dict:
        return {
            "schema_version": 1,
            "slice_id": slice_id,
            "owner_unit": "UNIT-receipt",
            "target_kind": "implementation",
            "target_paths": targets,
            "risk": "high",
            "risk_reasons": ["commit_gate"],
            "depends_on": list(depends_on or []),
            "requirements_design_inputs": [
                {"path": "prd.md", "heading": "BHV-001 First"},
                {
                    "path": "design-package/chapters/receipt.md",
                    "whole_file": True,
                },
            ],
            "deterministic_checks": ["true"],
            "semantic_review_provider": {
                "required": True,
                "provider": "codex",
                "ocr": "disabled",
            },
            "invariants": [
                {
                    "invariant_id": f"INV-{slice_id}",
                    "rule": "Exact reviewed bytes are committed.",
                    "source": "receipt.md",
                    "owner": "UNIT-receipt",
                    "positive_case": "Exact bytes pass.",
                    "negative_case": "Changed bytes fail.",
                    "route_if_missing": "IMPLEMENT_DEFECT",
                    "test_evidence": ["slice lifecycle test"],
                }
            ],
        }

    def _write_packet(
        self,
        slice_id: str,
        targets: list[str],
        depends_on=None,
    ) -> dict:
        packet = self._packet(slice_id, targets, depends_on)
        packet_dir = self.task / "slice-packets"
        packet_dir.mkdir(exist_ok=True)
        (packet_dir / f"{slice_id}.json").write_text(
            json.dumps(packet),
            encoding="utf-8",
        )
        return packet

    def _update_packet(self, slice_id: str, update) -> dict:
        path = self.task / "slice-packets" / f"{slice_id}.json"
        packet = json.loads(path.read_text(encoding="utf-8"))
        update(packet)
        path.write_text(json.dumps(packet), encoding="utf-8")
        return packet

    def _update_latest_review(self, update) -> dict:
        path = self.task / "review-records" / "implementation-reviews.jsonl"
        records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        update(records[-1])
        path.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )
        return records[-1]

    def _refresh_batch_id(self, batch: dict) -> None:
        batch["batch_id"] = guru_review_record.canonical_digest(
            "guru-slice-receipt-batch-v1",
            [
                {
                    field: receipt[field]
                    for field in guru_review_record.RECEIPT_REQUIRED_FIELDS
                }
                for receipt in batch["receipts"]
            ],
        )

    def _append_review(
        self,
        slice_id: str,
        targets: list[str],
        *,
        run_id: str | None = None,
        clean: bool = True,
        policy: str = "codex",
        runtime_dir: str = "packages/cli/src/templates/guru/overlay/verify",
    ) -> dict:
        run_id = run_id or f"review-{slice_id}"
        record = {
            "run_id": run_id,
            "slice_id": slice_id,
            "review_target": f"slice:{slice_id}",
            "target_paths": targets,
            "review_provider": "codex",
            "route_class": "none" if clean else "IMPLEMENT_DEFECT",
            "review_result": "clean" if clean else "findings",
            "deterministic_checks": "passed",
            "dirty_scope": "isolated",
            "invariant_coverage": "all_passed" if clean else "failed",
            "deterministic_results": [
                {
                    "command": "true",
                    "exit_code": 0,
                    "duration_ms": 1,
                    "stdout_summary": "",
                    "stderr_summary": "",
                }
            ],
            "supervisor_failure": "none",
            "required_satisfied": clean,
            "reviewed_target_digest": guru_review_record.target_snapshot_digest(
                str(self.root),
                targets,
                "index",
            ),
            "provider_override_source": "config_policy",
            "same_provider_user_quote": None,
            "high_risk_review_provider_policy": policy,
            "check_provider": "codex",
            "implement_provider": "codex",
            "review_target_kind": "slice",
        }
        review_record_path = (
            self.root
            / runtime_dir
            / "guru_review_record.py"
        )
        self._write(
            str(review_record_path.relative_to(self.root)),
            b"# review record\n",
        )
        with mock.patch.object(
            guru_review_record,
            "__file__",
            str(review_record_path),
        ):
            guru_review_record.append_record(str(self.task), record)
        return record

    @contextlib.contextmanager
    def _gate_root(
        self,
        runtime_dir: str = "packages/cli/src/templates/guru/overlay/verify",
    ):
        gate_path = (
            self.root
            / runtime_dir
            / "guru_gate.py"
        )
        with (
            mock.patch.object(guru_gate, "_repo_root", return_value=str(self.root)),
            mock.patch.object(guru_gate, "__file__", str(gate_path)),
        ):
            yield

    def _check_slice(
        self,
        slice_id: str,
        runtime_dir: str = "packages/cli/src/templates/guru/overlay/verify",
    ) -> tuple[int, str]:
        out = io.StringIO()
        err = io.StringIO()
        with self._gate_root(runtime_dir), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = guru_gate.cmd_check_slice_commit(str(self.task), slice_id)
        return rc, out.getvalue() + err.getvalue()

    def _record_slice(
        self,
        slice_id: str,
        run_id: str,
        runtime_dir: str = "packages/cli/src/templates/guru/overlay/verify",
    ) -> tuple[int, str]:
        out = io.StringIO()
        err = io.StringIO()
        with self._gate_root(runtime_dir), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = guru_gate.cmd_record_slice_commit(str(self.task), slice_id, run_id)
        return rc, out.getvalue() + err.getvalue()

    def test_requirements_design_digest_binds_raw_section_and_whole_file(self) -> None:
        u1 = self._packet("U1", ["lib/a.txt"])["requirements_design_inputs"]
        u2 = [
            {"path": "prd.md", "heading": "BHV-002 Second"},
            {"path": "design-package/chapters/receipt.md", "whole_file": True},
        ]
        before_u1 = guru_review_record.requirements_design_digest(str(self.task), u1)
        before_u2 = guru_review_record.requirements_design_digest(str(self.task), u2)
        prd = self.task / "prd.md"
        prd.write_bytes(prd.read_bytes().replace(b"Exact bytes.", b"Exact changed."))
        self.assertNotEqual(
            before_u1,
            guru_review_record.requirements_design_digest(str(self.task), u1),
        )
        self.assertEqual(
            before_u2,
            guru_review_record.requirements_design_digest(str(self.task), u2),
        )
        chapter = self.task / "design-package" / "chapters" / "receipt.md"
        chapter.write_bytes(chapter.read_bytes().replace(b"\n", b"\r\n"))
        self.assertNotEqual(
            before_u2,
            guru_review_record.requirements_design_digest(str(self.task), u2),
        )

    def test_requirements_design_digest_rejects_ambiguous_heading(self) -> None:
        prd = self.task / "prd.md"
        prd.write_bytes(prd.read_bytes() + b"\r\n## BHV-001 First\r\nDuplicate.\r\n")
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "ambiguous",
        ):
            guru_review_record.requirements_design_digest(
                str(self.task),
                [{"path": "prd.md", "heading": "BHV-001 First"}],
            )

    def test_commit_digest_matches_staged_digest_without_line_normalization(self) -> None:
        self._write("lib/a.txt", b"line-1\r\nline-2\n")
        self._git("add", "--", "lib/a.txt")
        staged = guru_review_record.target_snapshot_digest(
            str(self.root),
            ["lib/a.txt"],
            "index",
        )
        self._git("commit", "-m", "mixed line endings")
        commit = self._git("rev-parse", "HEAD")
        self.assertEqual(
            staged,
            guru_review_record.commit_target_digest(
                str(self.root),
                ["lib/a.txt"],
                commit,
            ),
        )

    def test_receipt_batch_round_trip_and_malformed_rejection(self) -> None:
        receipt = {
            "schema_version": 1,
            "slice_id": "U1",
            "commit_sha": "a" * 40,
            "parent_sha": "b" * 40,
            "review_run_id": "review-U1",
            "reviewed_target_digest": "0" * 64,
            "target_paths_digest": "1" * 64,
            "invariant_set_digest": "2" * 64,
            "requirements_design_digest": "3" * 64,
            "deterministic_commands_digest": "4" * 64,
            "deterministic_results_digest": "5" * 64,
            "review_policy_digest": "6" * 64,
            "supervisor_source_digest": "7" * 64,
            "committed_at": "2026-07-16T00:00:00Z",
        }
        guru_review_record.append_receipt_batch(str(self.task), [receipt])
        self.assertEqual(
            [receipt],
            guru_review_record.receipt_records(str(self.task)),
        )
        malformed = dict(receipt)
        del malformed["parent_sha"]
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "parent_sha",
        ):
            guru_review_record.append_receipt_batch(str(self.task), [malformed])
        receipt_path = Path(guru_review_record.receipts_path(str(self.task)))
        original = json.loads(receipt_path.read_text(encoding="utf-8"))
        wrong_kind = dict(original)
        wrong_kind["kind"] = "other"
        receipt_path.write_text(json.dumps(wrong_kind) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "invalid batch envelope",
        ):
            guru_review_record.receipt_records(str(self.task))
        wrong_batch = dict(original)
        wrong_batch["batch_id"] = "f" * 64
        receipt_path.write_text(json.dumps(wrong_batch) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "batch_id mismatch",
        ):
            guru_review_record.receipt_records(str(self.task))

    def test_evidence_key_excludes_volatile_deterministic_results(self) -> None:
        packet = guru_review_record.load_packet(str(self.task), "U1")
        first_record = {
            "deterministic_results": [
                {
                    "command": "true",
                    "exit_code": 0,
                    "duration_ms": 1,
                    "run_at": "2026-07-16T00:00:00Z",
                    "stdout_summary": "",
                    "stderr_summary": "",
                }
            ],
            "high_risk_review_provider_policy": "codex",
            "provider_override_source": "config_policy",
            "same_provider_user_quote": None,
            "review_target_kind": "slice",
            "implement_provider": "codex",
            "check_provider": "codex",
            "review_provider": "codex",
        }
        second_record = json.loads(json.dumps(first_record))
        second_record["deterministic_results"][0]["duration_ms"] = 999
        second_record["deterministic_results"][0]["run_at"] = (
            "2026-07-16T01:00:00Z"
        )
        first = guru_review_record.review_evidence_components(
            str(self.task),
            packet,
            first_record,
        )
        second = guru_review_record.review_evidence_components(
            str(self.task),
            packet,
            second_record,
        )
        reviewed_digest = "0" * 64
        self.assertNotEqual(
            first["deterministic_results_digest"],
            second["deterministic_results_digest"],
        )
        self.assertEqual(
            guru_review_record.review_evidence_key(reviewed_digest, first),
            guru_review_record.review_evidence_key(reviewed_digest, second),
        )

    def test_legacy_slice_review_without_packet_remains_appendable(self) -> None:
        packet = self.task / "slice-packets" / "U1.json"
        packet.unlink()
        self._write("lib/a.txt", b"legacy\n")
        self._git("add", "--", "lib/a.txt")
        record = self._append_review("U1", ["lib/a.txt"])
        reviews = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        ).read_text(encoding="utf-8")
        appended = json.loads(reviews.splitlines()[-1])
        self.assertEqual(record["run_id"], appended["run_id"])
        self.assertNotIn("evidence_key", appended)

    def test_clean_review_ready_commit_and_official_receipt(self) -> None:
        self._write("lib/a.txt", b"reviewed\r\nbytes\n")
        self._git("add", "--", "lib/a.txt")
        review = self._append_review("U1", ["lib/a.txt"])
        rc, output = self._check_slice("U1")
        self.assertEqual(0, rc, output)
        self.assertIn("SLICE_COMMIT_READY", output)
        self._git("commit", "-m", "slice U1")
        rc, output = self._record_slice("U1", review["run_id"])
        self.assertEqual(0, rc, output)
        self.assertIn("RECEIPT_RECORDED", output)
        receipt = guru_review_record.receipt_records(str(self.task))[-1]
        self.assertEqual(self._git("rev-parse", "HEAD"), receipt["commit_sha"])
        self.assertRegex(receipt["receipt_id"], r"^[0-9a-f]{64}$")
        with self._gate_root():
            self.assertEqual(
                "",
                guru_gate._validate_slice_receipt(
                    str(self.task),
                    str(self.root),
                receipt,
            ),
        )
        rc, output = self._record_slice("U1", review["run_id"])
        self.assertEqual(0, rc, output)
        self.assertIn("RECEIPT_EXISTS", output)
        self.assertEqual(
            1,
            len(guru_review_record.receipt_records(str(self.task))),
        )

    def test_findings_and_malformed_record_block_readiness(self) -> None:
        self._write("lib/a.txt", b"finding\n")
        self._git("add", "--", "lib/a.txt")
        self._append_review("U1", ["lib/a.txt"], clean=False)
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("not clean", output)
        reviews = self.task / "review-records" / "implementation-reviews.jsonl"
        reviews.write_text("{not-json}\n", encoding="utf-8")
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("invalid JSON", output)

    def test_post_review_byte_change_blocks_readiness(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        self._append_review("U1", ["lib/a.txt"])
        self._write("lib/a.txt", b"changed-after-review\n")
        self._git("add", "--", "lib/a.txt")
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("staged bytes changed", output)

    def test_post_review_invariant_change_blocks_readiness(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        self._append_review("U1", ["lib/a.txt"])
        self._update_packet(
            "U1",
            lambda packet: packet["invariants"][0].update(
                {"rule": "Changed invariant requires a new semantic review."}
            ),
        )
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("invariant_set_digest", output)

    def test_post_review_requirements_change_blocks_readiness(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        self._append_review("U1", ["lib/a.txt"])
        prd = self.task / "prd.md"
        prd.write_bytes(prd.read_bytes().replace(b"Exact bytes.", b"Changed input."))
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("requirements_design_digest", output)

    def test_post_review_deterministic_command_change_blocks_readiness(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        self._append_review("U1", ["lib/a.txt"])
        self._update_packet(
            "U1",
            lambda packet: packet.update({"deterministic_checks": ["true", "git status"]}),
        )
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("deterministic_commands_digest", output)

    def test_post_review_provider_policy_change_blocks_readiness(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        self._append_review("U1", ["lib/a.txt"])
        self._update_packet(
            "U1",
            lambda packet: packet.update(
                {
                    "semantic_review_provider": {
                        "required": True,
                        "provider": "opposite",
                        "ocr": "disabled",
                    }
                }
            ),
        )
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("review_policy_digest", output)

    def test_post_review_risk_change_blocks_readiness(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        self._append_review("U1", ["lib/a.txt"])
        self._update_packet(
            "U1",
            lambda packet: packet.update(
                {"risk": "low", "risk_reasons": ["reclassified"]}
            ),
        )
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("review_policy_digest", output)

    def test_explicit_empty_provider_policy_blocks_gate_and_producer(self) -> None:
        config = self.root / ".trellis" / "config.yaml"
        config.write_text(
            "guru:\n"
            "  supervision:\n"
            "    high_risk_review_provider_policy: current\n",
            encoding="utf-8",
        )
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        review = self._append_review(
            "U1",
            ["lib/a.txt"],
            policy="current",
        )
        config.write_text(
            "guru:\n"
            "  supervision:\n"
            "    high_risk_review_provider_policy:\n",
            encoding="utf-8",
        )
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("invalid high-risk review provider policy", output)
        self._git("commit", "-m", "slice with invalid current policy")
        rc, output = self._record_slice("U1", review["run_id"])
        self.assertEqual(2, rc)
        self.assertIn("invalid high-risk review provider policy", output)

    def test_post_review_supervisor_change_blocks_readiness(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        self._append_review("U1", ["lib/a.txt"])
        self._write(
            "packages/cli/src/templates/guru/overlay/verify/guru_supervise.py",
            b"# changed supervisor\n",
        )
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("supervisor_source_digest", output)

    def test_tampered_evidence_key_blocks_readiness(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        self._append_review("U1", ["lib/a.txt"])
        self._update_latest_review(
            lambda review: review.update({"evidence_key": "0" * 64})
        )
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("evidence_key", output)

    def test_out_of_scope_and_task_artifact_block_readiness(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        self._append_review("U1", ["lib/a.txt"])
        self._write("lib/out.txt", b"outside\n")
        self._git("add", "--", "lib/out.txt")
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("outside slice U1", output)
        self._git("reset", "HEAD", "--", "lib/out.txt")
        note = self.task / "note.txt"
        note.write_text("task artifact\n", encoding="utf-8")
        self._git("add", "-f", "--", str(note.relative_to(self.root)))
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("task artifacts", output)

    def test_missing_dependency_receipt_blocks_dependent_slice(self) -> None:
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._write("lib/b.txt", b"dependent\n")
        self._git("add", "--", "lib/b.txt")
        self._append_review("U2", ["lib/b.txt"])
        rc, output = self._check_slice("U2")
        self.assertEqual(2, rc)
        self.assertIn("has no valid commit receipt", output)

    def test_non_ancestor_receipt_blocks_dependency(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        review = self._append_review("U1", ["lib/a.txt"])
        self._git("commit", "-m", "slice U1")
        rc, output = self._record_slice("U1", review["run_id"])
        self.assertEqual(0, rc, output)
        receipt_path = Path(guru_review_record.receipts_path(str(self.task)))
        batch = json.loads(receipt_path.read_text(encoding="utf-8"))
        batch["receipts"][0]["commit_sha"] = "f" * 40
        self._refresh_batch_id(batch)
        receipt_path.write_text(json.dumps(batch) + "\n", encoding="utf-8")
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._write("lib/b.txt", b"dependent\n")
        self._git("add", "--", "lib/b.txt")
        self._append_review("U2", ["lib/b.txt"])
        rc, output = self._check_slice("U2")
        self.assertEqual(2, rc)
        self.assertIn("has no valid commit receipt", output)

    def test_receipt_requires_latest_review_run(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        first = self._append_review("U1", ["lib/a.txt"], run_id="review-U1-first")
        self._append_review("U1", ["lib/a.txt"], run_id="review-U1-latest")
        self._git("commit", "-m", "slice U1")
        rc, output = self._record_slice("U1", first["run_id"])
        self.assertEqual(2, rc)
        self.assertIn("requires the latest slice review run_id", output)

    def test_same_commit_conflicting_receipt_is_rejected(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        first = self._append_review("U1", ["lib/a.txt"], run_id="review-U1-first")
        self._git("commit", "-m", "slice U1")
        rc, output = self._record_slice("U1", first["run_id"])
        self.assertEqual(0, rc, output)
        second = self._append_review(
            "U1",
            ["lib/a.txt"],
            run_id="review-U1-second",
        )
        rc, output = self._record_slice("U1", second["run_id"])
        self.assertEqual(2, rc)
        self.assertIn("conflicting slice receipt already exists", output)

    def test_ordinary_dependent_receipt_requires_strict_ancestor(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        u1_review = self._append_review("U1", ["lib/a.txt"])
        self._git("commit", "-m", "slice U1")
        rc, output = self._record_slice("U1", u1_review["run_id"])
        self.assertEqual(0, rc, output)
        self._write_packet("U2", ["lib/a.txt"], depends_on=["U1"])
        u2_review = self._append_review("U2", ["lib/a.txt"])
        rc, output = self._record_slice("U2", u2_review["run_id"])
        self.assertEqual(2, rc)
        self.assertIn("has no valid commit receipt", output)
        self.assertEqual(
            ["U1"],
            [
                receipt["slice_id"]
                for receipt in guru_review_record.receipt_records(str(self.task))
            ],
        )

    def test_installed_layout_uses_runtime_supervisor_commit_path(self) -> None:
        runtime_dir = ".trellis/scripts/guru"
        self._write("lib/a.txt", b"installed-layout\n")
        self._git("add", "--", "lib/a.txt")
        review = self._append_review(
            "U1",
            ["lib/a.txt"],
            runtime_dir=runtime_dir,
        )
        rc, output = self._check_slice("U1", runtime_dir)
        self.assertEqual(0, rc, output)
        self._git("commit", "-m", "installed layout slice")
        rc, output = self._record_slice(
            "U1",
            review["run_id"],
            runtime_dir,
        )
        self.assertEqual(0, rc, output)
        receipt = guru_review_record.receipt_records(str(self.task))[-1]
        with self._gate_root(runtime_dir):
            self.assertEqual(
                "",
                guru_gate._validate_slice_receipt(
                    str(self.task),
                    str(self.root),
                    receipt,
                ),
            )

    def test_future_dependency_receipt_cannot_authorize_earlier_commit(self) -> None:
        self._write("lib/a.txt", b"dependency-v1\n")
        self._git("add", "--", "lib/a.txt")
        u1_v1_review = self._append_review(
            "U1",
            ["lib/a.txt"],
            run_id="review-U1-v1",
        )
        self._git("commit", "-m", "slice U1 v1")
        rc, output = self._record_slice("U1", u1_v1_review["run_id"])
        self.assertEqual(0, rc, output)
        u1_v1_receipt = guru_review_record.receipt_records(str(self.task))[-1]

        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._write("lib/b.txt", b"dependent\n")
        self._git("add", "--", "lib/b.txt")
        u2_review = self._append_review("U2", ["lib/b.txt"])
        self._git("commit", "-m", "slice U2")
        rc, output = self._record_slice("U2", u2_review["run_id"])
        self.assertEqual(0, rc, output)
        u2_receipt = guru_review_record.receipt_records(str(self.task))[-1]

        self._write("lib/a.txt", b"dependency-v2\n")
        self._git("add", "--", "lib/a.txt")
        u1_v2_review = self._append_review(
            "U1",
            ["lib/a.txt"],
            run_id="review-U1-v2",
        )
        self._git("commit", "-m", "slice U1 v2")
        rc, output = self._record_slice("U1", u1_v2_review["run_id"])
        self.assertEqual(0, rc, output)

        with self._gate_root():
            history = guru_gate._receipt_history_by_slice(str(self.task))
            dependency = guru_gate._dependency_receipt_for_commit(
                str(self.root),
                history,
                "U1",
                u2_receipt["commit_sha"],
                require_strict_ancestor=True,
            )
            self.assertEqual(u1_v1_receipt["commit_sha"], dependency["commit_sha"])
            self.assertEqual(
                "",
                guru_gate._validate_slice_receipt(
                    str(self.task),
                    str(self.root),
                    u2_receipt,
                ),
            )

        receipt_path = Path(guru_review_record.receipts_path(str(self.task)))
        batches = [
            json.loads(line)
            for line in receipt_path.read_text(encoding="utf-8").splitlines()
        ]
        for batch in batches:
            batch["receipts"] = [
                receipt
                for receipt in batch["receipts"]
                if not (
                    receipt["slice_id"] == "U1"
                    and receipt["commit_sha"] == u1_v1_receipt["commit_sha"]
                )
            ]
            if batch["receipts"]:
                self._refresh_batch_id(batch)
        receipt_path.write_text(
            "".join(
                json.dumps(batch) + "\n"
                for batch in batches
                if batch["receipts"]
            ),
            encoding="utf-8",
        )
        with self._gate_root():
            problem = guru_gate._validate_slice_receipt(
                str(self.task),
                str(self.root),
                u2_receipt,
            )
        self.assertIn("missing from dependent commit ancestry", problem)

    def test_committed_at_mutation_invalidates_receipt(self) -> None:
        self._write("lib/a.txt", b"reviewed\n")
        self._git("add", "--", "lib/a.txt")
        review = self._append_review("U1", ["lib/a.txt"])
        self._git("commit", "-m", "slice U1")
        rc, output = self._record_slice("U1", review["run_id"])
        self.assertEqual(0, rc, output)
        receipt_path = Path(guru_review_record.receipts_path(str(self.task)))
        batch = json.loads(receipt_path.read_text(encoding="utf-8"))
        batch["receipts"][0]["committed_at"] = "2099-01-01T00:00:00Z"
        self._refresh_batch_id(batch)
        receipt_path.write_text(json.dumps(batch) + "\n", encoding="utf-8")
        receipt = guru_review_record.receipt_records(str(self.task))[0]
        with self._gate_root():
            problem = guru_gate._validate_slice_receipt(
                str(self.task),
                str(self.root),
                receipt,
            )
        self.assertIn("committed_at mismatch", problem)

    def test_descendant_receipt_supersedes_changed_slice_contract(self) -> None:
        self._write("lib/a.txt", b"reviewed-v1\n")
        self._git("add", "--", "lib/a.txt")
        first = self._append_review("U1", ["lib/a.txt"], run_id="review-U1-v1")
        self._git("commit", "-m", "slice U1 v1")
        rc, output = self._record_slice("U1", first["run_id"])
        self.assertEqual(0, rc, output)
        self._update_packet(
            "U1",
            lambda packet: packet["invariants"][0].update(
                {"rule": "Changed shared path bytes require a fresh review."}
            ),
        )
        self._write("lib/a.txt", b"reviewed-v2\n")
        self._git("add", "--", "lib/a.txt")
        second = self._append_review("U1", ["lib/a.txt"], run_id="review-U1-v2")
        self._git("commit", "-m", "slice U1 v2")
        rc, output = self._record_slice("U1", second["run_id"])
        self.assertEqual(0, rc, output)
        receipts = guru_review_record.receipt_records(str(self.task))
        self.assertEqual(2, len(receipts))
        self.assertEqual(
            [first["run_id"], second["run_id"]],
            [receipt["review_run_id"] for receipt in receipts],
        )

    def test_check_commit_without_slice_keeps_legacy_dispatch(self) -> None:
        argv = ["guru_gate.py", "check-commit", str(self.task)]
        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(guru_gate, "cmd_check_commit", return_value=7) as legacy,
            mock.patch.object(guru_gate, "cmd_check_slice_commit") as sliced,
        ):
            self.assertEqual(7, guru_gate.main())
        legacy.assert_called_once_with(str(self.task))
        sliced.assert_not_called()


if __name__ == "__main__":
    unittest.main()
