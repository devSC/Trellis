from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock


VERIFY_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VERIFY_DIR))

import guru_contract  # noqa: E402
import guru_gate  # noqa: E402
import guru_review_record  # noqa: E402
import guru_supervise  # noqa: E402


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
            "review_evidence_schema_version": 2,
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
        for receipt in batch["receipts"]:
            if "receipt_id" in receipt:
                receipt["receipt_id"] = guru_review_record.canonical_digest(
                    "guru-slice-commit-receipt-v1",
                    guru_review_record.receipt_digest_payload(receipt),
                )
        batch["batch_id"] = guru_review_record.canonical_digest(
            "guru-slice-receipt-batch-v1",
            [
                guru_review_record.receipt_digest_payload(receipt)
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
                    "cwd": str(self.root),
                    "exit_code": 0,
                    "timed_out": False,
                    "duration_ms": 1,
                    "stdout_summary": "",
                    "stderr_summary": "",
                    "run_at": "2026-07-17T00:00:00Z",
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
            packet_path = (
                self.task / "slice-packets" / f"{slice_id}.json"
            )
            if packet_path.is_file():
                packet = guru_review_record.load_packet(
                    str(self.task),
                    slice_id,
                )
                lifecycle_v2 = (
                    packet.get(
                        guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD,
                        1,
                    )
                    == guru_review_record.REVIEW_EVIDENCE_SCHEMA_VERSION
                )
                if lifecycle_v2:
                    statuses = {}
                    for index, invariant in enumerate(packet["invariants"]):
                        status = "pass" if clean or index else "fail"
                        statuses[invariant["invariant_id"]] = {
                            "status": status,
                            "evidence": (
                                "reviewed exact bytes"
                                if status == "pass"
                                else "semantic finding"
                            ),
                        }
                    record["invariant_verdicts"] = (
                        guru_review_record.canonical_invariant_verdicts(
                            packet["invariants"],
                            statuses,
                            require_all_pass=clean,
                        )
                    )
                components = guru_review_record.review_evidence_components(
                    str(self.task),
                    packet,
                    record,
                )
                evidence_key = guru_review_record.review_evidence_key(
                    record["reviewed_target_digest"],
                    components,
                )
                record["evidence_key"] = evidence_key
                record["deterministic_evidence_key"] = evidence_key
                record[
                    guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD
                ] = (
                    guru_review_record.REVIEW_EVIDENCE_SCHEMA_VERSION
                    if lifecycle_v2
                    else 1
                )
                guru_review_record.append_deterministic_evidence(
                    str(self.task),
                    guru_review_record.deterministic_evidence_record(
                        evidence_key,
                        packet["deterministic_checks"],
                        "passed",
                        record["deterministic_results"],
                    ),
                )
                if lifecycle_v2:
                    fields = {
                        "review_result": record["review_result"],
                        "route_class": record["route_class"],
                        "review_target": record["review_target"],
                        "review_provider": record["review_provider"],
                        "deterministic_checks": record[
                            "deterministic_checks"
                        ],
                        "dirty_scope": record["dirty_scope"],
                        "invariant_coverage": record[
                            "invariant_coverage"
                        ],
                        "_invariants": statuses,
                        "_reviewer_probe_commands": [],
                    }
                    record, failure = (
                        guru_review_record.normalize_review_record(
                            fields,
                            {
                                "mode": "supervisor",
                                "packet": packet,
                                "implement_provider": "codex",
                                "supervisor_deterministic_status": "passed",
                                "deterministic_results": record[
                                    "deterministic_results"
                                ],
                                "run_id": run_id,
                                "slice_id": slice_id,
                                "review_target": f"slice:{slice_id}",
                                "target_paths": targets,
                                "channel": "official-test-review",
                                "worker": "official-test-worker",
                                "check_provider": "codex",
                                "provider_override_source": "config_policy",
                                "same_provider_user_quote": None,
                                "high_risk_review_provider_policy": policy,
                                "review_target_kind": "slice",
                                "reviewed_target_digest": record[
                                    "reviewed_target_digest"
                                ],
                                "evidence_key": evidence_key,
                                "deterministic_evidence_key": evidence_key,
                                guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD: (
                                    guru_review_record.REVIEW_EVIDENCE_SCHEMA_VERSION
                                ),
                                "supervisor_successful_commands": ["true"],
                            },
                        )
                    )
                    self.assertIsNone(failure)
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

    def _supervisor_args(self, run_id: str = "u2") -> object:
        return type(
            "Args",
            (),
            {
                "task_dir": str(self.task),
                "root": str(self.root),
                "run_id": run_id,
                "platform": "cli",
                "provider": "codex",
                "trellis_bin": "trellis",
                "slice": "U1",
                "staged": True,
                "contract": False,
                "same_provider": False,
                "user_quote": None,
                "dry_run": False,
            },
        )()

    def _aggregate_args(self, run_id: str = "aggregate") -> object:
        args = self._supervisor_args(run_id)
        args.slice = ["U1", "U2"]
        args.aggregate = True
        return args

    def _aggregate_worker_verdict(self) -> str:
        return (
            "review_result=clean\n"
            "route_class=none\n"
            "review_target=aggregate:U1,U2\n"
            "review_provider=codex\n"
            "deterministic_checks=passed\n"
            "dirty_scope=isolated\n"
            "invariant_coverage=all_passed\n"
            "invariant_status.INV-U1=pass\n"
            "invariant_evidence.INV-U1=reviewed aggregate U1 bytes\n"
            "invariant_status.INV-U2=pass\n"
            "invariant_evidence.INV-U2=reviewed aggregate U2 bytes\n"
        )

    @contextlib.contextmanager
    def _aggregate_runtime(self):
        runtime = (
            self.root
            / "packages/cli/src/templates/guru/overlay/verify"
        )
        record_path = runtime / "guru_review_record.py"
        self._write(
            str(record_path.relative_to(self.root)),
            b"# review record\n",
        )
        with (
            mock.patch.object(
                guru_supervise,
                "__file__",
                str(runtime / "guru_supervise.py"),
            ),
            mock.patch.object(
                guru_review_record,
                "__file__",
                str(record_path),
            ),
        ):
            yield

    def _supervision_config(self) -> guru_supervise.SupervisionConfig:
        return guru_supervise.SupervisionConfig(
            root=self.root,
            platform="cli",
            current_provider="codex",
            provider="codex",
            adversarial=False,
            adversarial_enabled=False,
            implement_timeout="1m",
            check_timeout="1m",
            warn_before="10s",
            idle_timeout=None,
            max_live_workers=None,
            trellis_bin="trellis",
            adversarial_model=None,
            adversarial_reasoning_effort=None,
            high_risk_review_provider_policy="codex",
        )

    def _clean_worker_verdict(self) -> str:
        return (
            "review_result=clean\n"
            "route_class=none\n"
            "review_target=slice:U1\n"
            "review_provider=codex\n"
            "deterministic_checks=passed\n"
            "dirty_scope=isolated\n"
            "invariant_coverage=all_passed\n"
            "invariant_status.INV-U1=pass\n"
            "invariant_evidence.INV-U1=reviewed exact staged bytes\n"
        )

    def _staged_worker_verdict(self) -> str:
        return (
            "review_result=clean\n"
            "route_class=none\n"
            "review_target=staged:index\n"
            "review_provider=codex\n"
            "deterministic_checks=passed\n"
            "dirty_scope=isolated\n"
            "invariant_coverage=all_passed\n"
            "invariant_status.staged_scope_reviewed=pass\n"
            "invariant_evidence.staged_scope_reviewed=reviewed staged bytes\n"
        )

    def _seed_clean_lifecycle_evidence(self) -> None:
        self._write("lib/a.txt", b"u2 seeded clean\n")
        self._git("add", "--", "lib/a.txt")
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._clean_worker_verdict()),
            ),
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("seed-clean")
                ),
            )

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

    def test_aggregate_packet_unions_contract_and_rejects_conflicts(self) -> None:
        u2 = self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._update_packet(
            "U1",
            lambda packet: packet["deterministic_checks"].append("shared-check"),
        )
        self._update_packet(
            "U2",
            lambda packet: packet["deterministic_checks"].insert(0, "shared-check"),
        )
        packet = guru_review_record.build_aggregate_packet(
            str(self.task),
            ["U2", "U1"],
            ["lib/a.txt", "lib/b.txt"],
        )
        self.assertEqual(["U1", "U2"], packet["aggregate_slice_ids"])
        self.assertEqual(["lib/a.txt", "lib/b.txt"], packet["target_paths"])
        self.assertEqual(
            ["true", "shared-check"],
            packet["deterministic_checks"],
        )
        self.assertEqual(
            {"INV-U1", "INV-U2"},
            {item["invariant_id"] for item in packet["invariants"]},
        )
        self.assertNotIn("staged_scope_reviewed", json.dumps(packet))
        self.assertEqual(
            {"U1", "U2"},
            set(packet["per_slice_requirements_design_digests"]),
        )

        self._write_packet("U3", ["lib/a.txt"])
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "omits covering slices",
        ):
            guru_review_record.build_aggregate_packet(
                str(self.task),
                ["U1", "U2"],
                ["lib/a.txt", "lib/b.txt"],
        )
        (self.task / "slice-packets" / "U3.json").unlink()

        self._write_packet("U3", ["lib/unstaged.txt"])
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "selected slices do not cover staged paths: U3",
        ):
            guru_review_record.build_aggregate_packet(
                str(self.task),
                ["U1", "U2", "U3"],
                ["lib/a.txt", "lib/b.txt"],
            )
        (self.task / "slice-packets" / "U3.json").unlink()

        self._update_packet(
            "U2",
            lambda candidate: candidate["invariants"].__setitem__(
                0,
                dict(
                    u2["invariants"][0],
                    invariant_id="INV-U1",
                    rule="Conflicting aggregate rule.",
                ),
            ),
        )
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "invariant conflict",
        ):
            guru_review_record.build_aggregate_packet(
                str(self.task),
                ["U1", "U2"],
                ["lib/a.txt", "lib/b.txt"],
            )
        self._update_packet(
            "U2",
            lambda candidate: candidate.__setitem__("invariants", u2["invariants"]),
        )
        self._update_packet(
            "U2",
            lambda candidate: candidate.__setitem__(
                "semantic_review_provider",
                {"required": True, "provider": "claude", "ocr": "disabled"},
            ),
        )
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "provider policy is ambiguous",
        ):
            guru_review_record.build_aggregate_packet(
                str(self.task),
                ["U1", "U2"],
                ["lib/a.txt", "lib/b.txt"],
            )
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "not covered",
        ):
            guru_review_record.build_aggregate_packet(
                str(self.task),
                ["U1", "U2"],
                ["lib/a.txt", "lib/c.txt"],
            )

    def test_aggregate_unknown_and_low_risk_uses_effective_task_risk(self) -> None:
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._update_packet(
            "U1",
            lambda packet: packet.__setitem__("risk", "unknown"),
        )
        self._update_packet(
            "U2",
            lambda packet: packet.__setitem__("risk", "low"),
        )
        packet = guru_review_record.build_aggregate_packet(
            str(self.task),
            ["U1", "U2"],
            ["lib/a.txt", "lib/b.txt"],
        )
        self.assertEqual("high", packet["risk"])
        self.assertTrue(
            guru_supervise._slice_uses_high_risk_review_policy(
                packet,
                self.task,
            )
        )
        policy = guru_review_record.review_policy_payload(packet, {})
        self.assertEqual("high", policy["packet_risk"])

        (self.task / "task.json").write_text(
            json.dumps(
                {
                    "status": "in_progress",
                    "route": "full_chain",
                    "risk": "unknown",
                }
            ),
            encoding="utf-8",
        )
        unknown_task_packet = guru_review_record.build_aggregate_packet(
            str(self.task),
            ["U1", "U2"],
            ["lib/a.txt", "lib/b.txt"],
        )
        self.assertIsNone(unknown_task_packet["risk"])
        self.assertFalse(
            guru_supervise._slice_uses_high_risk_review_policy(
                unknown_task_packet,
                self.task,
            )
        )

    def test_aggregate_review_runs_unique_commands_and_one_worker(self) -> None:
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._update_packet(
            "U2",
            lambda packet: packet["deterministic_checks"].append("true"),
        )
        self._write("lib/a.txt", b"aggregate-a\n")
        self._write("lib/b.txt", b"aggregate-b\n")
        self._git("add", "--", "lib/a.txt", "lib/b.txt")
        calls = []

        with (
            self._aggregate_runtime(),
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._aggregate_worker_verdict()),
            ) as worker,
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
                wraps=lambda commands, cwd: (
                    calls.append(list(commands))
                    or ("passed", [
                        {
                            "command": command,
                            "cwd": cwd,
                            "exit_code": 0,
                            "timed_out": False,
                            "duration_ms": 1,
                            "stdout_summary": "",
                            "stderr_summary": "",
                            "run_at": "2026-07-17T00:00:00Z",
                        }
                        for command in commands
                    ])
                ),
            ),
        ):
            rc = guru_supervise.run_implementation_review(
                self._aggregate_args("aggregate-one")
            )
        self.assertEqual(0, rc)
        self.assertEqual(1, worker.call_count)
        self.assertEqual([["true"]], calls)
        record_path = self.task / "review-records" / "implementation-reviews.jsonl"
        record = json.loads(record_path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(["U1", "U2"], record["aggregate_slice_ids"])
        self.assertEqual({"U1", "U2"}, set(record["per_slice_component_digests"]))
        self.assertEqual(
            {"U1", "U2"},
            set(record["per_slice_requirements_design_digests"]),
        )

    def test_aggregate_key_binds_per_slice_inputs_hidden_by_union(self) -> None:
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._update_packet(
            "U2",
            lambda packet: packet.__setitem__(
                "requirements_design_inputs",
                [
                    {"path": "prd.md", "whole_file": True},
                    {
                        "path": "design-package/chapters/receipt.md",
                        "whole_file": True,
                    },
                ],
            ),
        )
        policy_record = {
            "deterministic_results": [],
            "provider_override_source": "config_policy",
            "same_provider_user_quote": None,
            "high_risk_review_provider_policy": "codex",
            "review_target_kind": "aggregate",
            "implement_provider": "codex",
            "check_provider": "codex",
            "review_provider": "codex",
        }
        before_packet = guru_review_record.build_aggregate_packet(
            str(self.task), ["U1", "U2"], ["lib/a.txt", "lib/b.txt"]
        )
        before = guru_review_record.review_evidence_components(
            str(self.task),
            before_packet,
            policy_record,
            supervisor_path=str(
                self.root
                / "packages/cli/src/templates/guru/overlay/verify/guru_supervise.py"
            ),
        )
        self._update_packet(
            "U1",
            lambda packet: packet["requirements_design_inputs"].__setitem__(
                0,
                {"path": "prd.md", "heading": "BHV-002 Second"},
            ),
        )
        after_packet = guru_review_record.build_aggregate_packet(
            str(self.task), ["U1", "U2"], ["lib/a.txt", "lib/b.txt"]
        )
        after = guru_review_record.review_evidence_components(
            str(self.task),
            after_packet,
            policy_record,
            supervisor_path=str(
                self.root
                / "packages/cli/src/templates/guru/overlay/verify/guru_supervise.py"
            ),
        )
        self.assertEqual(
            before_packet["requirements_design_inputs"],
            after_packet["requirements_design_inputs"],
        )
        self.assertNotEqual(
            before["requirements_design_digest"],
            after["requirements_design_digest"],
        )

    def test_partial_receipt_blocks_aggregate_before_checks_or_worker(self) -> None:
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        receipt = {
            "schema_version": 1,
            "slice_id": "U1",
            "commit_sha": "a" * 40,
            "parent_sha": "b" * 40,
            "review_run_id": "existing",
            "reviewed_target_digest": "0" * 64,
            "target_paths_digest": "1" * 64,
            "invariant_set_digest": "2" * 64,
            "requirements_design_digest": "3" * 64,
            "deterministic_commands_digest": "4" * 64,
            "deterministic_results_digest": "5" * 64,
            "review_policy_digest": "6" * 64,
            "supervisor_source_digest": "7" * 64,
            "committed_at": "2026-07-17T00:00:00Z",
        }
        guru_review_record.append_receipt_batch(str(self.task), [receipt])
        self._write("lib/a.txt", b"partial-a\n")
        self._write("lib/b.txt", b"partial-b\n")
        self._git("add", "--", "lib/a.txt", "lib/b.txt")
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
            ) as checks,
            mock.patch.object(guru_supervise, "_execute_plan") as worker,
        ):
            rc = guru_supervise.run_implementation_review(
                self._aggregate_args("partial")
            )
        self.assertEqual(2, rc)
        checks.assert_not_called()
        worker.assert_not_called()

    def test_v2_staged_fallback_requires_explicit_aggregate(self) -> None:
        self._write("lib/a.txt", b"weak fallback blocked\n")
        self._git("add", "--", "lib/a.txt")
        args = self._supervisor_args("weak-fallback")
        args.slice = None
        args.aggregate = False
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
            ) as checks,
            mock.patch.object(guru_supervise, "_execute_plan") as worker,
        ):
            self.assertEqual(2, guru_supervise.run_implementation_review(args))
        checks.assert_not_called()
        worker.assert_not_called()

    def test_full_unknown_v2_staged_fallback_requires_explicit_aggregate(
        self,
    ) -> None:
        contract = guru_contract.default_contract(
            guru_contract.ROUTE_FULL_CHAIN,
            guru_contract.RISK_UNKNOWN,
            created_by="test",
        )
        contract["scope"]["allowed_paths"] = ["lib/a.txt"]
        contract["scope"]["max_files"] = None
        (self.task / "gate-contract.json").write_text(
            json.dumps(contract),
            encoding="utf-8",
        )
        self._write("lib/a.txt", b"unknown risk weak fallback blocked\n")
        self._git("add", "--", "lib/a.txt")
        args = self._supervisor_args("unknown-risk-weak-fallback")
        args.slice = None
        args.aggregate = False
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
            ) as checks,
            mock.patch.object(guru_supervise, "_execute_plan") as worker,
        ):
            self.assertEqual(2, guru_supervise.run_implementation_review(args))
        checks.assert_not_called()
        worker.assert_not_called()

    def test_full_high_missing_or_malformed_contract_never_uses_weak_staged_review(
        self,
    ) -> None:
        self._write("lib/a.txt", b"contract fail closed\n")
        self._git("add", "--", "lib/a.txt")
        args = self._supervisor_args("contract-fail-closed")
        args.slice = None
        args.aggregate = False
        contract_path = self.task / "gate-contract.json"
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
            ) as checks,
            mock.patch.object(guru_supervise, "_execute_plan") as worker,
        ):
            for label, contract_bytes in (
                ("missing", None),
                ("malformed", b"{not-json\n"),
            ):
                with self.subTest(label=label):
                    if contract_bytes is None:
                        contract_path.unlink(missing_ok=True)
                    else:
                        contract_path.write_bytes(contract_bytes)
                    args.run_id = f"contract-{label}"
                    self.assertEqual(
                        2,
                        guru_supervise.run_implementation_review(args),
                    )
        checks.assert_not_called()
        worker.assert_not_called()

    def test_aggregate_cli_accepts_repeated_explicit_slices(self) -> None:
        parsed = guru_supervise.build_parser().parse_args(
            [
                "implementation-review",
                str(self.task),
                "--aggregate",
                "--staged",
                "--slice",
                "U2",
                "--slice",
                "U1",
            ]
        )
        self.assertTrue(parsed.aggregate)
        self.assertEqual(["U2", "U1"], parsed.slice)
        with (
            mock.patch.object(
                sys,
                "argv",
                [
                    "guru_gate.py",
                    "check-commit",
                    str(self.task),
                    "--aggregate",
                    "--slice",
                    "U2",
                    "--slice",
                    "U1",
                ],
            ),
            mock.patch.object(
                guru_gate,
                "cmd_check_aggregate_slice_commit",
                return_value=0,
            ) as aggregate_gate,
        ):
            self.assertEqual(0, guru_gate.main())
        aggregate_gate.assert_called_once_with(str(self.task), ["U2", "U1"])

    def test_non_full_v2_staged_review_keeps_legacy_behavior(self) -> None:
        contract = guru_contract.default_contract(
            guru_contract.ROUTE_LITE_TASK,
            guru_contract.RISK_LOW,
            created_by="test",
        )
        contract["scope"]["allowed_paths"] = ["lib/a.txt"]
        contract["scope"]["max_files"] = None
        contract_path = self.task / "gate-contract.json"
        contract_path.write_text(json.dumps(contract), encoding="utf-8")
        self._write("lib/a.txt", b"non-full legacy staged\n")
        self._git("add", "--", "lib/a.txt")
        args = self._supervisor_args("non-full-v2")
        args.slice = None
        args.aggregate = False
        legacy_config = guru_supervise.replace(
            self._supervision_config(),
            current_provider="claude",
            provider="claude",
        )
        with (
            mock.patch.object(guru_supervise, "_guru_gate_check_implementation", return_value=0),
            mock.patch.object(guru_supervise, "_load_config", return_value=legacy_config),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._staged_worker_verdict()),
            ) as worker,
        ):
            self.assertEqual(0, guru_supervise.run_implementation_review(args))
        worker.assert_called_once()

    def test_focused_context_v2_slice_omits_full_task_manifests(self) -> None:
        (self.task / "design.md").write_text(
            "FULL DESIGN MUST NOT BE INJECTED\n", encoding="utf-8"
        )
        (self.task / "implement.md").write_text(
            "FULL IMPLEMENT MUST NOT BE INJECTED\n", encoding="utf-8"
        )
        (self.task / "check.jsonl").write_text(
            '{"secret":"FULL CHECK MUST NOT BE INJECTED"}\n',
            encoding="utf-8",
        )
        self._write("lib/a.txt", b"focused slice bytes\n")
        self._git("add", "--", "lib/a.txt")
        captured = []

        def capture_plan(plan, _config):
            captured.append(plan)
            return 0, "done", self._clean_worker_verdict()

        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                side_effect=capture_plan,
            ),
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("focused-context-slice")
                ),
            )
        self.assertEqual(1, len(captured))
        plan = captured[0]
        self.assertEqual([], plan.jsonls)
        self.assertIn(
            (self.task / "slice-packets" / "U1.json").resolve(),
            [path.resolve() for path in plan.files],
        )
        self.assertNotIn(self.task / "prd.md", plan.files)
        self.assertNotIn(self.task / "design.md", plan.files)
        self.assertNotIn(self.task / "implement.md", plan.files)
        self.assertIn("focused_review_context=", plan.brief)
        self.assertIn("focused slice bytes", plan.brief)
        self.assertIn("Exact bytes.", plan.brief)
        self.assertIn("Bind every byte.", plan.brief)
        self.assertNotIn("Other bytes.", plan.brief)
        self.assertNotIn("FULL DESIGN MUST NOT BE INJECTED", plan.brief)
        self.assertNotIn("FULL IMPLEMENT MUST NOT BE INJECTED", plan.brief)
        self.assertNotIn("FULL CHECK MUST NOT BE INJECTED", plan.brief)

    def test_focused_staged_diff_uses_literal_target_paths(self) -> None:
        literal_path = "lib/literal*.txt"
        pattern_match = "lib/literal-match.txt"
        self._write(literal_path, b"literal metachar target\n")
        self._write(pattern_match, b"pattern-only decoy\n")
        self._git(
            "--literal-pathspecs",
            "add",
            "--",
            literal_path,
            pattern_match,
        )
        focused = guru_supervise._focused_staged_diff(
            self.root,
            [literal_path],
        )
        self.assertIn("literal metachar target", focused)
        self.assertNotIn("pattern-only decoy", focused)

    def test_focused_context_v2_aggregate_omits_full_task_manifests(self) -> None:
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        (self.task / "design.md").write_text(
            "FULL AGGREGATE DESIGN MUST NOT BE INJECTED\n", encoding="utf-8"
        )
        (self.task / "implement.md").write_text(
            "FULL AGGREGATE IMPLEMENT MUST NOT BE INJECTED\n", encoding="utf-8"
        )
        (self.task / "check.jsonl").write_text(
            '{"secret":"FULL AGGREGATE CHECK MUST NOT BE INJECTED"}\n',
            encoding="utf-8",
        )
        self._write("lib/a.txt", b"focused aggregate a\n")
        self._write("lib/b.txt", b"focused aggregate b\n")
        self._git("add", "--", "lib/a.txt", "lib/b.txt")
        captured = []

        def capture_plan(plan, _config):
            captured.append(plan)
            return 0, "done", self._aggregate_worker_verdict()

        with (
            self._aggregate_runtime(),
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                side_effect=capture_plan,
            ),
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._aggregate_args("focused-context-aggregate")
                ),
            )
        self.assertEqual(1, len(captured))
        plan = captured[0]
        self.assertEqual([], plan.jsonls)
        self.assertNotIn(self.task / "prd.md", plan.files)
        self.assertNotIn(self.task / "design.md", plan.files)
        self.assertNotIn(self.task / "implement.md", plan.files)
        self.assertIn("focused_review_context=", plan.brief)
        self.assertIn("focused aggregate a", plan.brief)
        self.assertIn("focused aggregate b", plan.brief)
        self.assertIn('"state":"same_aggregate_pending"', plan.brief)
        self.assertIn("INV-U1", plan.brief)
        self.assertIn("INV-U2", plan.brief)
        self.assertNotIn("FULL AGGREGATE DESIGN MUST NOT BE INJECTED", plan.brief)
        self.assertNotIn("FULL AGGREGATE IMPLEMENT MUST NOT BE INJECTED", plan.brief)
        self.assertNotIn("FULL AGGREGATE CHECK MUST NOT BE INJECTED", plan.brief)

    def test_focused_context_legacy_v1_keeps_full_task_manifests(self) -> None:
        (self.task / "design.md").write_text(
            "legacy design context\n", encoding="utf-8"
        )
        (self.task / "implement.md").write_text(
            "legacy implementation context\n", encoding="utf-8"
        )
        (self.task / "check.jsonl").write_text(
            '{"legacy":"check context"}\n', encoding="utf-8"
        )
        plan = guru_supervise.build_run_plan(
            "implementation-review",
            self.task,
            self._supervision_config(),
            "legacy-context",
        )
        resolved_files = {path.resolve() for path in plan.files}
        self.assertIn((self.task / "prd.md").resolve(), resolved_files)
        self.assertIn((self.task / "design.md").resolve(), resolved_files)
        self.assertIn((self.task / "implement.md").resolve(), resolved_files)
        self.assertEqual(
            [(self.task / "check.jsonl").resolve()],
            [path.resolve() for path in plan.jsonls],
        )
        self.assertNotIn("focused_review_context=", plan.brief)

    def test_aggregate_gate_and_atomic_topological_receipts(self) -> None:
        contract = guru_contract.default_contract(
            guru_contract.ROUTE_FULL_CHAIN,
            guru_contract.RISK_UNKNOWN,
            created_by="test",
        )
        contract["scope"]["allowed_paths"] = ["lib/a.txt", "lib/b.txt"]
        contract["scope"]["max_files"] = None
        (self.task / "gate-contract.json").write_text(
            json.dumps(contract),
            encoding="utf-8",
        )
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._write("lib/a.txt", b"aggregate receipt a\n")
        self._write("lib/b.txt", b"aggregate receipt b\n")
        self._git("add", "--", "lib/a.txt", "lib/b.txt")
        with (
            self._aggregate_runtime(),
            mock.patch.object(guru_supervise, "_guru_gate_check_implementation", return_value=0),
            mock.patch.object(guru_supervise, "_load_config", return_value=self._supervision_config()),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._aggregate_worker_verdict()),
            ),
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._aggregate_args("aggregate-receipt")
                ),
            )
        output = io.StringIO()
        errors = io.StringIO()
        with self._gate_root(), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            self.assertEqual(
                0,
                guru_gate.cmd_check_aggregate_slice_commit(
                    str(self.task), ["U2", "U1"]
                ),
            )
        self.assertIn("SLICE_COMMIT_READY aggregate=U1,U2", output.getvalue())
        self._git("commit", "-m", "aggregate implementation")
        with self._gate_root(), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            self.assertEqual(
                0,
                guru_gate.cmd_record_aggregate_slice_commit(
                    str(self.task),
                    ["U2", "U1"],
                    "aggregate-receipt-review-1",
                ),
                errors.getvalue(),
            )
        batches = guru_review_record.load_receipt_batches(str(self.task))
        self.assertEqual(1, len(batches))
        self.assertEqual(
            ["U1", "U2"],
            [receipt["slice_id"] for receipt in batches[0]["receipts"]],
        )
        self.assertEqual(
            batches[0]["receipts"][0]["commit_sha"],
            batches[0]["receipts"][1]["commit_sha"],
        )
        history = guru_gate._receipt_history_by_slice(str(self.task))
        with self._gate_root():
            self.assertEqual(
                "",
                guru_gate._validate_slice_receipt(
                    str(self.task),
                    str(self.root),
                    history["U2"][-1],
                receipt_history=history,
            ),
        )
        receipt_path = Path(guru_review_record.receipts_path(str(self.task)))
        before_replay = receipt_path.read_bytes()
        replay = io.StringIO()
        with self._gate_root(), contextlib.redirect_stdout(replay):
            self.assertEqual(
                0,
                guru_gate.cmd_record_aggregate_slice_commit(
                    str(self.task),
                    ["U2", "U1"],
                    "aggregate-receipt-review-1",
                ),
            )
        self.assertIn("RECEIPTS_EXIST", replay.getvalue())
        self.assertEqual(before_replay, receipt_path.read_bytes())

    def test_aggregate_receipt_replay_rejects_partial_batch(self) -> None:
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._write("lib/a.txt", b"aggregate partial a\n")
        self._write("lib/b.txt", b"aggregate partial b\n")
        self._git("add", "--", "lib/a.txt", "lib/b.txt")
        with (
            self._aggregate_runtime(),
            mock.patch.object(guru_supervise, "_guru_gate_check_implementation", return_value=0),
            mock.patch.object(guru_supervise, "_load_config", return_value=self._supervision_config()),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._aggregate_worker_verdict()),
            ),
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._aggregate_args("aggregate-partial")
                ),
            )
        self._git("commit", "-m", "aggregate partial")
        with self._gate_root():
            self.assertEqual(
                0,
                guru_gate.cmd_record_aggregate_slice_commit(
                    str(self.task),
                    ["U1", "U2"],
                    "aggregate-partial-review-1",
                ),
            )
        receipt_path = Path(guru_review_record.receipts_path(str(self.task)))
        receipts = guru_review_record.receipt_records(str(self.task))
        receipt_path.unlink()
        guru_review_record.append_receipt_batch(str(self.task), receipts[:1])
        before_replay = receipt_path.read_bytes()
        output = io.StringIO()
        with self._gate_root(), contextlib.redirect_stderr(output):
            self.assertEqual(
                2,
                guru_gate.cmd_record_aggregate_slice_commit(
                    str(self.task),
                    ["U1", "U2"],
                    "aggregate-partial-review-1",
                ),
            )
        self.assertIn("replay is partial", output.getvalue())
        self.assertEqual(before_replay, receipt_path.read_bytes())

    def test_aggregate_receipt_replay_rejects_conflicting_batch(self) -> None:
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._write("lib/a.txt", b"aggregate conflict a\n")
        self._write("lib/b.txt", b"aggregate conflict b\n")
        self._git("add", "--", "lib/a.txt", "lib/b.txt")
        with (
            self._aggregate_runtime(),
            mock.patch.object(guru_supervise, "_guru_gate_check_implementation", return_value=0),
            mock.patch.object(guru_supervise, "_load_config", return_value=self._supervision_config()),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._aggregate_worker_verdict()),
            ),
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._aggregate_args("aggregate-conflict")
                ),
            )
        self._git("commit", "-m", "aggregate conflict")
        with self._gate_root():
            self.assertEqual(
                0,
                guru_gate.cmd_record_aggregate_slice_commit(
                    str(self.task),
                    ["U1", "U2"],
                    "aggregate-conflict-review-1",
                ),
            )
        receipt_path = Path(guru_review_record.receipts_path(str(self.task)))
        receipts = guru_review_record.receipt_records(str(self.task))
        receipt_path.unlink()
        receipts[1]["review_run_id"] = "conflicting-aggregate-run"
        receipts[1]["receipt_id"] = guru_review_record.canonical_digest(
            "guru-slice-commit-receipt-v1",
            guru_review_record.receipt_digest_payload(receipts[1]),
        )
        guru_review_record.append_receipt_batch(str(self.task), receipts)
        before_replay = receipt_path.read_bytes()
        output = io.StringIO()
        with self._gate_root(), contextlib.redirect_stderr(output):
            self.assertEqual(
                2,
                guru_gate.cmd_record_aggregate_slice_commit(
                    str(self.task),
                    ["U1", "U2"],
                    "aggregate-conflict-review-1",
                ),
            )
        self.assertIn("replay conflicts", output.getvalue())
        self.assertEqual(before_replay, receipt_path.read_bytes())
        receipt_path.unlink()
        split_receipts = [dict(receipt) for receipt in receipts]
        split_receipts[1]["review_run_id"] = "aggregate-conflict-review-1"
        split_receipts[1]["receipt_id"] = guru_review_record.canonical_digest(
            "guru-slice-commit-receipt-v1",
            guru_review_record.receipt_digest_payload(split_receipts[1]),
        )
        guru_review_record.append_receipt_batch(
            str(self.task), split_receipts[:1]
        )
        guru_review_record.append_receipt_batch(
            str(self.task), split_receipts[1:]
        )
        before_split_replay = receipt_path.read_bytes()
        split_output = io.StringIO()
        with self._gate_root(), contextlib.redirect_stderr(split_output):
            self.assertEqual(
                2,
                guru_gate.cmd_record_aggregate_slice_commit(
                    str(self.task),
                    ["U1", "U2"],
                    "aggregate-conflict-review-1",
                ),
            )
        self.assertIn("across receipt batches", split_output.getvalue())
        self.assertEqual(before_split_replay, receipt_path.read_bytes())
        split_history = guru_gate._receipt_history_by_slice(str(self.task))
        with self._gate_root():
            split_problem = guru_gate._validate_slice_receipt(
                str(self.task),
                str(self.root),
                split_history["U2"][-1],
                receipt_history=split_history,
            )
        self.assertIn("does not match official review", split_problem)

    def test_aggregate_receipt_validation_rejects_split_or_duplicate_batch(
        self,
    ) -> None:
        self._write_packet("U2", ["lib/b.txt"])
        self._write("lib/a.txt", b"independent aggregate a\n")
        self._write("lib/b.txt", b"independent aggregate b\n")
        self._git("add", "--", "lib/a.txt", "lib/b.txt")
        with (
            self._aggregate_runtime(),
            mock.patch.object(guru_supervise, "_guru_gate_check_implementation", return_value=0),
            mock.patch.object(guru_supervise, "_load_config", return_value=self._supervision_config()),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._aggregate_worker_verdict()),
            ),
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._aggregate_args("aggregate-independent")
                ),
            )
        self._git("commit", "-m", "independent aggregate")
        with self._gate_root():
            self.assertEqual(
                0,
                guru_gate.cmd_record_aggregate_slice_commit(
                    str(self.task),
                    ["U1", "U2"],
                    "aggregate-independent-review-1",
                ),
            )
        receipt_path = Path(guru_review_record.receipts_path(str(self.task)))
        receipts = guru_review_record.receipt_records(str(self.task))
        receipt_path.unlink()
        guru_review_record.append_receipt_batch(str(self.task), receipts[:1])
        guru_review_record.append_receipt_batch(str(self.task), receipts[1:])
        split_history = guru_gate._receipt_history_by_slice(str(self.task))
        with self._gate_root():
            for slice_id in ("U1", "U2"):
                problem = guru_gate._validate_slice_receipt(
                    str(self.task),
                    str(self.root),
                    split_history[slice_id][-1],
                    receipt_history=split_history,
                )
                self.assertIn("does not match official review", problem)
        receipt_path.unlink()
        guru_review_record.append_receipt_batch(str(self.task), receipts)
        guru_review_record.append_receipt_batch(str(self.task), receipts)
        duplicate_history = guru_gate._receipt_history_by_slice(str(self.task))
        with self._gate_root():
            for slice_id in ("U1", "U2"):
                problem = guru_gate._validate_slice_receipt(
                    str(self.task),
                    str(self.root),
                    duplicate_history[slice_id][-1],
                    receipt_history=duplicate_history,
                )
                self.assertIn("exactly one atomic receipt batch", problem)

    def test_historical_aggregate_receipt_binds_commit_supervisor(self) -> None:
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._write("lib/a.txt", b"aggregate historical a\n")
        self._write("lib/b.txt", b"aggregate historical b\n")
        self._git("add", "--", "lib/a.txt", "lib/b.txt")
        with (
            self._aggregate_runtime(),
            mock.patch.object(guru_supervise, "_guru_gate_check_implementation", return_value=0),
            mock.patch.object(guru_supervise, "_load_config", return_value=self._supervision_config()),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._aggregate_worker_verdict()),
            ),
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._aggregate_args("aggregate-historical")
                ),
            )
        self._git("commit", "-m", "aggregate historical")
        aggregate_commit = self._git("rev-parse", "HEAD")
        with self._gate_root():
            self.assertEqual(
                0,
                guru_gate.cmd_record_aggregate_slice_commit(
                    str(self.task),
                    ["U1", "U2"],
                    "aggregate-historical-review-1",
                ),
            )
        supervisor_path = (
            "packages/cli/src/templates/guru/overlay/verify/guru_supervise.py"
        )
        self._write(supervisor_path, b"# later supervisor revision\n")
        self._git("add", "--", supervisor_path)
        self._git("commit", "-m", "later supervisor revision")
        later_commit = self._git("rev-parse", "HEAD")
        history = guru_gate._receipt_history_by_slice(str(self.task))
        with self._gate_root():
            self.assertEqual(
                "",
                guru_gate._validate_slice_receipt(
                    str(self.task),
                    str(self.root),
                    history["U2"][-1],
                    receipt_history=history,
                ),
            )
        receipt_path = Path(guru_review_record.receipts_path(str(self.task)))
        batch = json.loads(receipt_path.read_text(encoding="utf-8"))
        committed_at = self._git("show", "-s", "--format=%cI", later_commit)
        for receipt in batch["receipts"]:
            receipt["commit_sha"] = later_commit
            receipt["parent_sha"] = aggregate_commit
            receipt["committed_at"] = committed_at
        self._refresh_batch_id(batch)
        receipt_path.write_text(json.dumps(batch) + "\n", encoding="utf-8")
        tampered_history = guru_gate._receipt_history_by_slice(str(self.task))
        with self._gate_root():
            problem = guru_gate._validate_slice_receipt(
                str(self.task),
                str(self.root),
                tampered_history["U2"][-1],
                receipt_history=tampered_history,
            )
        self.assertIn("supervisor", problem)

    def test_aggregate_receipt_rejects_ambiguous_review_run_ownership(self) -> None:
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._write("lib/a.txt", b"aggregate collision a\n")
        self._write("lib/b.txt", b"aggregate collision b\n")
        self._git("add", "--", "lib/a.txt", "lib/b.txt")
        with (
            self._aggregate_runtime(),
            mock.patch.object(guru_supervise, "_guru_gate_check_implementation", return_value=0),
            mock.patch.object(guru_supervise, "_load_config", return_value=self._supervision_config()),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._aggregate_worker_verdict()),
            ),
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._aggregate_args("aggregate-collision")
                ),
            )
        run_id = "aggregate-collision-review-1"
        self._append_review("U1", ["lib/a.txt"], run_id=run_id)
        review, error, aggregate = guru_gate._receipt_review_record(
            str(self.task),
            "U1",
            run_id,
        )
        self.assertIsNone(review)
        self.assertFalse(aggregate)
        self.assertIn("ownership ambiguous", error)
        self._git("commit", "-m", "aggregate collision")
        output = io.StringIO()
        with self._gate_root(), contextlib.redirect_stderr(output):
            self.assertEqual(
                2,
                guru_gate.cmd_record_aggregate_slice_commit(
                    str(self.task),
                    ["U1", "U2"],
                    run_id,
                ),
            )
        self.assertIn("ownership ambiguous", output.getvalue())
        self.assertFalse(
            Path(guru_review_record.receipts_path(str(self.task))).exists()
        )

    def test_ordinary_receipt_rejects_ambiguous_review_run_ownership(self) -> None:
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._write("lib/a.txt", b"ordinary collision a\n")
        self._write("lib/b.txt", b"ordinary collision b\n")
        self._git("add", "--", "lib/a.txt", "lib/b.txt")
        with (
            self._aggregate_runtime(),
            mock.patch.object(guru_supervise, "_guru_gate_check_implementation", return_value=0),
            mock.patch.object(guru_supervise, "_load_config", return_value=self._supervision_config()),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._aggregate_worker_verdict()),
            ),
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._aggregate_args("ordinary-collision")
                ),
            )
        run_id = "ordinary-collision-review-1"
        self._append_review("U1", ["lib/a.txt"], run_id=run_id)
        self._git("commit", "-m", "ordinary collision", "--", "lib/a.txt")
        rc, output = self._record_slice("U1", run_id)
        self.assertEqual(2, rc)
        self.assertIn("ownership ambiguous", output)
        self.assertFalse(
            Path(guru_review_record.receipts_path(str(self.task))).exists()
        )

    def test_aggregate_gate_rejects_byte_drift_and_component_map_tamper(self) -> None:
        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._write("lib/a.txt", b"aggregate stable a\n")
        self._write("lib/b.txt", b"aggregate stable b\n")
        self._git("add", "--", "lib/a.txt", "lib/b.txt")
        with (
            self._aggregate_runtime(),
            mock.patch.object(guru_supervise, "_guru_gate_check_implementation", return_value=0),
            mock.patch.object(guru_supervise, "_load_config", return_value=self._supervision_config()),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._aggregate_worker_verdict()),
            ),
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._aggregate_args("aggregate-drift")
                ),
            )
        self._write("lib/a.txt", b"aggregate changed after review\n")
        self._git("add", "--", "lib/a.txt")
        with self._gate_root():
            self.assertEqual(
                2,
                guru_gate.cmd_check_aggregate_slice_commit(
                    str(self.task), ["U1", "U2"]
                ),
            )
        self._write("lib/a.txt", b"aggregate stable a\n")
        self._git("add", "--", "lib/a.txt")
        self._update_latest_review(
            lambda record: record["per_slice_component_digests"]["U2"].__setitem__(
                "invariant_set_digest", "f" * 64
            )
        )
        with self._gate_root():
            self.assertEqual(
                2,
                guru_gate.cmd_check_aggregate_slice_commit(
                    str(self.task), ["U1", "U2"]
                ),
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

    def test_v2_invariant_verdicts_require_exact_canonical_coverage(
        self,
    ) -> None:
        invariants = self._packet("U1", ["lib/a.txt"])["invariants"]
        canonical = guru_review_record.canonical_invariant_verdicts(
            invariants,
            {
                "INV-U1": {
                    "status": "pass",
                    "evidence": "exact reviewed bytes",
                }
            },
            require_all_pass=True,
        )
        self.assertEqual(
            {
                "INV-U1": {
                    "status": "pass",
                    "evidence": "exact reviewed bytes",
                    "reason": "",
                }
            },
            canonical,
        )
        invalid_maps = [
            {},
            {
                "INV-U1": {
                    "status": "pass",
                    "evidence": "",
                }
            },
            {
                "INV-U1": {
                    "status": "fail",
                }
            },
            {
                "INV-U1": {
                    "status": "not_applicable",
                    "reason": "not applicable",
                }
            },
            {
                "INV-U1": {
                    "status": "pass",
                    "evidence": "ok",
                },
                "INV-UNKNOWN": {
                    "status": "pass",
                    "evidence": "unknown",
                },
            },
        ]
        for verdicts in invalid_maps:
            with self.subTest(verdicts=verdicts), self.assertRaises(
                guru_review_record.ReviewRecordError
            ):
                guru_review_record.canonical_invariant_verdicts(
                    invariants,
                    verdicts,
                    require_all_pass=True,
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

    def test_lifecycle_writer_requires_both_caller_supplied_keys(self) -> None:
        self._write("lib/a.txt", b"strict writer keys\n")
        self._git("add", "--", "lib/a.txt")
        record = self._append_review("U1", ["lib/a.txt"])
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        before = review_path.read_bytes()
        runtime_record = (
            self.root
            / "packages/cli/src/templates/guru/overlay/verify"
            / "guru_review_record.py"
        )
        candidates = []
        missing = type(record)(record)
        missing.pop("evidence_key")
        candidates.append(missing)
        missing_deterministic = type(record)(record)
        missing_deterministic.pop("deterministic_evidence_key")
        candidates.append(missing_deterministic)
        missing_schema = type(record)(record)
        missing_schema.pop(
            guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD
        )
        candidates.append(missing_schema)
        candidates.append(type(record)(record, evidence_key="0" * 64))
        candidates.append(
            type(record)(record, deterministic_evidence_key="0" * 64)
        )
        with mock.patch.object(
            guru_review_record,
            "__file__",
            str(runtime_record),
        ):
            for candidate in candidates:
                with self.subTest(candidate=candidate), self.assertRaisesRegex(
                    guru_review_record.ReviewRecordError,
                    "must match current evidence|schema_version missing",
                ):
                    guru_review_record.append_record(
                        str(self.task),
                        candidate,
                    )
                self.assertEqual(before, review_path.read_bytes())

    def test_v2_writer_missing_requirements_manifest_never_downgrades_to_v1(
        self,
    ) -> None:
        self._write("lib/a.txt", b"missing v2 manifest\n")
        self._git("add", "--", "lib/a.txt")
        self._update_packet(
            "U1",
            lambda packet: packet.pop("requirements_design_inputs"),
        )
        record = {
            "run_id": "v2-missing-manifest",
            "slice_id": "U1",
            "review_target": "slice:U1",
            "target_paths": ["lib/a.txt"],
            "review_provider": "codex",
            "route_class": "none",
            "review_result": "clean",
            "deterministic_checks": "passed",
            "dirty_scope": "isolated",
            "invariant_coverage": "all_passed",
            "supervisor_failure": "none",
            "required_satisfied": True,
            "reviewed_target_digest": (
                guru_review_record.target_snapshot_digest(
                    str(self.root),
                    ["lib/a.txt"],
                    "index",
                )
            ),
        }
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "requirements_design_inputs",
        ):
            guru_review_record.append_record(str(self.task), record)

        self._update_packet(
            "U1",
            lambda packet: packet.pop(
                guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD
            ),
        )
        v1_record = dict(record, run_id="v1-missing-manifest")
        guru_review_record.append_record(str(self.task), v1_record)
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        appended = json.loads(
            review_path.read_text(encoding="utf-8").splitlines()[-1]
        )
        self.assertEqual("v1-missing-manifest", appended["run_id"])
        self.assertNotIn("evidence_key", appended)

    def test_v2_aggregate_only_clean_cannot_append_or_pass_gate(self) -> None:
        self._write("lib/a.txt", b"aggregate only clean\n")
        self._git("add", "--", "lib/a.txt")
        clean = self._append_review("U1", ["lib/a.txt"])
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        before = review_path.read_bytes()
        handwritten_clone = dict(
            clean,
            run_id="handwritten-aggregate-only-clean",
        )
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "official normalized producer",
        ):
            guru_review_record.append_record(
                str(self.task),
                handwritten_clone,
            )
        self.assertEqual(before, review_path.read_bytes())

        aggregate_only = type(clean)(
            clean,
            run_id="official-shape-without-invariants",
        )
        aggregate_only.pop("invariant_verdicts")
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "invariant_verdicts",
        ):
            guru_review_record.append_record(
                str(self.task),
                aggregate_only,
            )
        self.assertEqual(before, review_path.read_bytes())

        rows = [
            json.loads(line)
            for line in before.decode("utf-8").splitlines()
            if line.strip()
        ]
        rows[-1].pop("invariant_verdicts")
        review_path.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("invariant_verdicts", output)
        self.assertNotIn("SLICE_COMMIT_READY", output)

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

    def test_historical_receipt_validates_recorded_deterministic_evidence(
        self,
    ) -> None:
        self._write("lib/a.txt", b"historical deterministic receipt\n")
        self._git("add", "--", "lib/a.txt")
        review = self._append_review("U1", ["lib/a.txt"])
        self._git("commit", "-m", "historical deterministic receipt")
        rc, output = self._record_slice("U1", review["run_id"])
        self.assertEqual(0, rc, output)
        receipt = guru_review_record.receipt_records(str(self.task))[-1]

        def historical_problem() -> str:
            with self._gate_root():
                return guru_gate._validate_historical_slice_receipt(
                    str(self.task),
                    str(self.root),
                    receipt,
                )

        self.assertEqual("", historical_problem())
        self._update_packet(
            "U1",
            lambda packet: packet["invariants"][0].update(
                {"rule": "Current packet drift is not historical evidence."}
            ),
        )
        self.assertEqual("", historical_problem())

        evidence_path = Path(
            guru_review_record.deterministic_evidence_path(str(self.task))
        )
        original_evidence = evidence_path.read_text(encoding="utf-8")
        evidence_path.unlink()
        self.assertIn("deterministic evidence missing", historical_problem())

        evidence_path.write_text("{malformed}\n", encoding="utf-8")
        self.assertIn("invalid JSON", historical_problem())

        failed_result = dict(
            review["deterministic_results"][0],
            exit_code=1,
            stderr_summary="failed",
        )
        failed = guru_review_record.deterministic_evidence_record(
            review["deterministic_evidence_key"],
            ["true"],
            "failed",
            [failed_result],
        )
        evidence_path.write_text(json.dumps(failed) + "\n", encoding="utf-8")
        self.assertIn("not passed", historical_problem())

        changed_result = dict(
            review["deterministic_results"][0],
            command="printf changed",
        )
        changed = guru_review_record.deterministic_evidence_record(
            review["deterministic_evidence_key"],
            ["printf changed"],
            "passed",
            [changed_result],
        )
        evidence_path.write_text(json.dumps(changed) + "\n", encoding="utf-8")
        self.assertIn("binding mismatch", historical_problem())

        changed_result = dict(
            review["deterministic_results"][0],
            duration_ms=2,
        )
        changed = guru_review_record.deterministic_evidence_record(
            review["deterministic_evidence_key"],
            ["true"],
            "passed",
            [changed_result],
        )
        evidence_path.write_text(json.dumps(changed) + "\n", encoding="utf-8")
        self.assertIn("binding mismatch", historical_problem())

        evidence_path.write_text(original_evidence, encoding="utf-8")
        reviews_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        original_reviews = reviews_path.read_text(encoding="utf-8")
        self._update_latest_review(
            lambda row: row.pop("deterministic_evidence_key")
        )
        self.assertIn(
            "deterministic_evidence_key mismatch",
            historical_problem(),
        )
        reviews_path.write_text(original_reviews, encoding="utf-8")
        self._update_latest_review(
            lambda row: row.pop(
                guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD
            )
        )
        self.assertIn("evidence schema mismatch", historical_problem())
        reviews_path.write_text(original_reviews, encoding="utf-8")

    def test_v2_receipt_binds_multi_invariant_verdict_digest(self) -> None:
        self._update_packet(
            "U1",
            lambda packet: packet["invariants"].append(
                {
                    **packet["invariants"][0],
                    "invariant_id": "INV-U1-SECOND",
                    "rule": "Second invariant is independently covered.",
                }
            ),
        )
        self._write("lib/a.txt", b"multi invariant receipt\n")
        self._git("add", "--", "lib/a.txt")
        review = self._append_review("U1", ["lib/a.txt"])
        self._git("commit", "-m", "multi invariant receipt")
        rc, output = self._record_slice("U1", review["run_id"])
        self.assertEqual(0, rc, output)
        receipt = guru_review_record.receipt_records(str(self.task))[-1]

        def historical_problem() -> str:
            with self._gate_root():
                return guru_gate._validate_historical_slice_receipt(
                    str(self.task),
                    str(self.root),
                    receipt,
                )

        self.assertEqual("", historical_problem())
        reviews_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        original_reviews = reviews_path.read_text(encoding="utf-8")
        rows = [
            json.loads(line)
            for line in original_reviews.splitlines()
            if line.strip()
        ]
        rows[-1]["invariant_verdicts"].pop("INV-U1-SECOND")
        reviews_path.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )
        self.assertIn("invariant_verdicts_digest mismatch", historical_problem())

        reviews_path.write_text(original_reviews, encoding="utf-8")
        rows = [
            json.loads(line)
            for line in original_reviews.splitlines()
            if line.strip()
        ]
        replaced = rows[-1]["invariant_verdicts"].pop("INV-U1-SECOND")
        rows[-1]["invariant_verdicts"]["INV-REPLACED"] = replaced
        rows[-1]["invariant_verdicts_digest"] = (
            guru_review_record.invariant_verdicts_digest(
                rows[-1]["invariant_verdicts"]
            )
        )
        reviews_path.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )
        self.assertIn("invariant_verdicts_digest mismatch", historical_problem())
        reviews_path.write_text(original_reviews, encoding="utf-8")

        receipt_path = Path(
            guru_review_record.receipts_path(str(self.task))
        )
        original_batch = receipt_path.read_text(encoding="utf-8")
        batch = json.loads(original_batch)
        batch["receipts"][-1].pop(
            guru_review_record.RECEIPT_INVARIANT_VERDICTS_DIGEST_FIELD
        )
        receipt_path.write_text(json.dumps(batch) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "invariant_verdicts_digest",
        ):
            guru_review_record.receipt_records(str(self.task))

        batch = json.loads(original_batch)
        batch["receipts"][-1][
            guru_review_record.RECEIPT_INVARIANT_VERDICTS_DIGEST_FIELD
        ] = "0" * 64
        receipt_path.write_text(json.dumps(batch) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "receipt_id mismatch",
        ):
            guru_review_record.receipt_records(str(self.task))
        receipt_path.write_text(original_batch, encoding="utf-8")

    def test_pre_u2_receipt_authorizes_u2_dependency(self) -> None:
        self._write("lib/a.txt", b"pre-u2 reviewed slice\n")
        self._git("add", "--", "lib/a.txt")
        review = self._append_review("U1", ["lib/a.txt"])
        self._git("commit", "-m", "pre-u2 slice")
        rc, output = self._record_slice("U1", review["run_id"])
        self.assertEqual(0, rc, output)

        reviews_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        reviews = [
            json.loads(line)
            for line in reviews_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        reviews[-1].pop(
            guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD
        )
        reviews[-1].pop("deterministic_evidence_key")
        reviews[-1].pop("invariant_verdicts")
        reviews[-1].pop("invariant_verdicts_digest")
        reviews_path.write_text(
            "".join(json.dumps(row) + "\n" for row in reviews),
            encoding="utf-8",
        )

        receipt_path = Path(
            guru_review_record.receipts_path(str(self.task))
        )
        batch = json.loads(receipt_path.read_text(encoding="utf-8"))
        legacy_receipt = batch["receipts"][-1]
        legacy_receipt.pop(
            guru_review_record.RECEIPT_REVIEW_EVIDENCE_SCHEMA_FIELD
        )
        legacy_receipt.pop(
            guru_review_record.RECEIPT_DETERMINISTIC_EVIDENCE_KEY_FIELD
        )
        legacy_receipt.pop(
            guru_review_record.RECEIPT_INVARIANT_VERDICTS_DIGEST_FIELD
        )
        self._refresh_batch_id(batch)
        receipt_path.write_text(
            json.dumps(batch) + "\n",
            encoding="utf-8",
        )
        self._update_packet(
            "U1",
            lambda packet: packet.pop(
                guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD
            ),
        )
        deterministic_path = Path(
            guru_review_record.deterministic_evidence_path(str(self.task))
        )
        deterministic_path.unlink()
        self.assertEqual(
            1,
            len(guru_review_record.receipt_records(str(self.task))),
        )

        self._write_packet("U2", ["lib/b.txt"], depends_on=["U1"])
        self._write("lib/b.txt", b"u2 depends on pre-u2 receipt\n")
        self._git("add", "--", "lib/b.txt")
        self._append_review("U2", ["lib/b.txt"])
        rc, output = self._check_slice("U2")
        self.assertEqual(0, rc, output)
        self.assertIn("SLICE_COMMIT_READY", output)

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

    def test_slice_gate_validates_referenced_deterministic_evidence(self) -> None:
        self._write("lib/a.txt", b"reviewed deterministic evidence\n")
        self._git("add", "--", "lib/a.txt")
        review = self._append_review("U1", ["lib/a.txt"])
        evidence_path = Path(
            guru_review_record.deterministic_evidence_path(str(self.task))
        )
        original = evidence_path.read_text(encoding="utf-8")

        evidence_path.unlink()
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("deterministic evidence missing", output)

        evidence_path.write_text("{malformed}\n", encoding="utf-8")
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("invalid JSON", output)

        failed_result = dict(
            review["deterministic_results"][0],
            exit_code=1,
            stderr_summary="failed",
        )
        failed = guru_review_record.deterministic_evidence_record(
            review["deterministic_evidence_key"],
            ["true"],
            "failed",
            [failed_result],
        )
        evidence_path.write_text(json.dumps(failed) + "\n", encoding="utf-8")
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("not passed", output)

        changed_result = dict(
            review["deterministic_results"][0],
            duration_ms=2,
        )
        changed = guru_review_record.deterministic_evidence_record(
            review["deterministic_evidence_key"],
            ["true"],
            "passed",
            [changed_result],
        )
        evidence_path.write_text(json.dumps(changed) + "\n", encoding="utf-8")
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("binding mismatch", output)

        evidence_path.write_text(original, encoding="utf-8")
        self._update_latest_review(
            lambda row: row.update(
                {"deterministic_evidence_key": "0" * 64}
            )
        )
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertIn("deterministic_evidence_key", output)

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

    def test_final_gate_uses_current_integration_receipt_without_reviewer(
        self,
    ) -> None:
        self._update_packet(
            "U1",
            lambda packet: packet.update(
                {
                    "integration_slice": False,
                    guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD: 1,
                }
            ),
        )
        self._write("lib/a.txt", b"final-u1\n")
        self._git("add", "--", "lib/a.txt")
        u1_review = self._append_review(
            "U1",
            ["lib/a.txt"],
            run_id="final-U1-review-1",
        )
        self._git("commit", "-m", "final U1")
        rc, output = self._record_slice("U1", u1_review["run_id"])
        self.assertEqual(0, rc, output)

        self._write_packet(
            "U2",
            ["."],
            depends_on=["U1"],
        )
        self._update_packet(
            "U2",
            lambda packet: packet.__setitem__("integration_slice", True),
        )
        missing_output = io.StringIO()
        with (
            self._gate_root(),
            contextlib.redirect_stderr(missing_output),
            mock.patch.object(
                guru_gate,
                "_commit_plan_payload",
                side_effect=AssertionError("final Gate spawned generic review path"),
            ),
        ):
            self.assertEqual(
                2,
                guru_gate.cmd_check_commit(str(self.task)),
            )
        self.assertIn("required slice receipt missing", missing_output.getvalue())
        self.assertIn("reviewers_spawned=0", missing_output.getvalue())

        self._write("lib/a.txt", b"final-combined-a\n")
        self._write("lib/b.txt", b"final-combined-b\n")
        contract_path = self.task / "gate-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["scope"]["allowed_paths"].append(
            "packages/cli/src/templates/guru/overlay/verify/guru_review_record.py"
        )
        contract_path.write_text(json.dumps(contract), encoding="utf-8")
        self._write(
            "packages/cli/src/templates/guru/overlay/verify/guru_review_record.py",
            b"# review record\n",
        )
        self._git(
            "add",
            "--",
            "lib/a.txt",
            "lib/b.txt",
            "packages/cli/src/templates/guru/overlay/verify/guru_review_record.py",
        )
        integration_review = self._append_review(
            "U2",
            ["."],
            run_id="final-U2-review-1",
        )
        self._git("commit", "-m", "final integration")
        rc, output = self._record_slice("U2", integration_review["run_id"])
        self.assertEqual(0, rc, output)
        final_output = io.StringIO()
        with (
            self._gate_root(),
            contextlib.redirect_stdout(final_output),
            mock.patch.object(
                guru_gate,
                "_commit_plan_payload",
                side_effect=AssertionError("final Gate spawned generic review path"),
            ),
        ):
            started = time.monotonic()
            self.assertEqual(
                0,
                guru_gate.cmd_check_commit(str(self.task)),
            )
            self.assertLess(time.monotonic() - started, 10)
        self.assertIn("FINAL_COMMIT_READY", final_output.getvalue())
        self.assertIn("reviewers_spawned=0", final_output.getvalue())
        self.assertIn("commit_shas=U1:", final_output.getvalue())

        self._write("lib/a.txt", b"drift after integration\n")
        drift_output = io.StringIO()
        with self._gate_root(), contextlib.redirect_stderr(drift_output):
            self.assertEqual(
                2,
                guru_gate.cmd_check_commit(str(self.task)),
            )
        self.assertIn("final worktree bytes", drift_output.getvalue())
        self.assertIn("recovery_command=", drift_output.getvalue())

    def test_final_gate_recovery_targets_stale_integration_slice(self) -> None:
        packets = [
            {
                "slice_id": "U1",
                "target_paths": ["lib/a.txt"],
                "depends_on": [],
                "integration_slice": False,
            },
            {
                "slice_id": "U4",
                "target_paths": ["lib/a.txt"],
                "depends_on": ["U1"],
                "integration_slice": True,
            },
        ]
        cases = [
            ("newer", "older", "not newer than current slice receipt"),
            ("shared", "shared", "shares a commit outside one validated aggregate batch"),
        ]
        for ordinary_commit, integration_commit, expected_error in cases:
            with self.subTest(expected_error=expected_error):
                receipts = {
                    "U1": {
                        "slice_id": "U1",
                        "receipt_id": "r1",
                        "commit_sha": ordinary_commit,
                    },
                    "U4": {
                        "slice_id": "U4",
                        "receipt_id": "r4",
                        "commit_sha": integration_commit,
                        "reviewed_target_digest": "digest",
                        "supervisor_source_digest": "current-supervisor",
                    },
                }
                output = io.StringIO()
                with (
                    mock.patch.object(guru_gate, "_repo_root", return_value="/repo"),
                    mock.patch.object(
                        guru_gate,
                        "_receipt_history_by_slice",
                        return_value=guru_gate._ReceiptHistory(),
                    ),
                    mock.patch.object(
                        guru_gate,
                        "_dependency_receipt_for_commit",
                        side_effect=lambda _root, _history, slice_id, _head,
                        require_strict_ancestor: receipts[slice_id],
                    ),
                    mock.patch.object(
                        guru_gate,
                        "_validate_slice_receipt",
                        return_value="",
                    ),
                    mock.patch.object(
                        guru_gate.guru_review_record,
                        "supervisor_source_digest",
                        return_value="current-supervisor",
                    ),
                    mock.patch.object(
                        guru_gate,
                        "_git_is_ancestor",
                        return_value=False,
                    ),
                    mock.patch.object(
                        guru_gate,
                        "_display_task_dir",
                        return_value="TASK",
                    ),
                    contextlib.redirect_stderr(output),
                ):
                    self.assertEqual(
                        2,
                        guru_gate.cmd_check_final_receipts("TASK", packets),
                    )
                message = output.getvalue()
                self.assertIn(expected_error, message)
                self.assertIn("--slice U4 --staged", message)
                self.assertIn("check-commit TASK --slice U4", message)
                self.assertNotIn("--slice U1 --staged", message)

    def test_final_gate_requires_current_integration_supervisor_digest(
        self,
    ) -> None:
        packets = [
            {
                "slice_id": "U1",
                "target_paths": ["lib/a.txt"],
                "depends_on": [],
                "integration_slice": False,
            },
            {
                "slice_id": "U4",
                "target_paths": ["lib/a.txt"],
                "depends_on": ["U1"],
                "integration_slice": True,
            },
        ]
        receipts = {
            "U1": {
                "slice_id": "U1",
                "receipt_id": "r1",
                "commit_sha": "ordinary",
                "supervisor_source_digest": "historical",
            },
            "U4": {
                "slice_id": "U4",
                "receipt_id": "r4",
                "commit_sha": "integration",
                "reviewed_target_digest": "unchanged-target",
                "supervisor_source_digest": "old-supervisor",
            },
        }
        output = io.StringIO()
        with (
            mock.patch.object(guru_gate, "_repo_root", return_value="/repo"),
            mock.patch.object(
                guru_gate,
                "_receipt_history_by_slice",
                return_value=guru_gate._ReceiptHistory(),
            ),
            mock.patch.object(
                guru_gate,
                "_dependency_receipt_for_commit",
                side_effect=lambda _root, _history, slice_id, _head,
                require_strict_ancestor: receipts[slice_id],
            ),
            mock.patch.object(
                guru_gate,
                "_validate_slice_receipt",
                return_value="",
            ),
            mock.patch.object(
                guru_gate.guru_review_record,
                "supervisor_source_digest",
                return_value="current-supervisor",
            ),
            mock.patch.object(
                guru_gate,
                "_display_task_dir",
                return_value="TASK",
            ),
            contextlib.redirect_stderr(output),
        ):
            self.assertEqual(
                2,
                guru_gate.cmd_check_final_receipts("TASK", packets),
            )
        message = output.getvalue()
        self.assertIn(
            "integration receipt is stale against current supervisor source",
            message,
        )
        self.assertIn("--slice U4 --staged", message)
        self.assertNotIn("--slice U1 --staged", message)

    def test_final_gate_accepts_one_atomic_aggregate_integration_batch(
        self,
    ) -> None:
        self._write_packet(
            "U2",
            ["lib/a.txt", "lib/b.txt"],
            depends_on=["U1"],
        )
        self._update_packet(
            "U2",
            lambda packet: packet.__setitem__("integration_slice", True),
        )
        self._write("lib/a.txt", b"aggregate-final-a\n")
        self._write("lib/b.txt", b"aggregate-final-b\n")
        self._git("add", "--", "lib/a.txt", "lib/b.txt")
        with (
            self._aggregate_runtime(),
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._aggregate_worker_verdict()),
            ),
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._aggregate_args("aggregate-final")
                ),
            )
        self._git("commit", "-m", "aggregate final")
        with self._gate_root():
            self.assertEqual(
                0,
                guru_gate.cmd_record_aggregate_slice_commit(
                    str(self.task),
                    ["U1", "U2"],
                    "aggregate-final-review-1",
                ),
            )
        output = io.StringIO()
        with (
            self._gate_root(),
            contextlib.redirect_stdout(output),
            mock.patch.object(
                guru_gate,
                "_commit_plan_payload",
                side_effect=AssertionError("final Gate spawned generic review path"),
            ),
        ):
            self.assertEqual(
                0,
                guru_gate.cmd_check_commit(str(self.task)),
            )
        self.assertIn("FINAL_COMMIT_READY", output.getvalue())
        self.assertIn("commit_shas=U1:", output.getvalue())
        self.assertIn(",U2:", output.getvalue())

    def test_final_lifecycle_activation_is_fail_closed_and_route_compatible(
        self,
    ) -> None:
        missing_output = io.StringIO()
        with self._gate_root(), contextlib.redirect_stderr(missing_output):
            self.assertEqual(
                2,
                guru_gate.cmd_check_commit(str(self.task)),
            )
        self.assertIn("exactly one integration slice", missing_output.getvalue())

        self._update_packet(
            "U1",
            lambda packet: packet.__setitem__("integration_slice", "true"),
        )
        _, malformed_packets, malformed_error = (
            guru_gate._final_lifecycle_context(str(self.task))
        )
        self.assertEqual([], malformed_packets)
        self.assertIn("must be boolean", malformed_error)
        self._update_packet(
            "U1",
            lambda packet: packet.__setitem__("integration_slice", 1),
        )
        _, malformed_packets, malformed_error = (
            guru_gate._final_lifecycle_context(str(self.task))
        )
        self.assertEqual([], malformed_packets)
        self.assertIn("must be boolean", malformed_error)

        self._update_packet(
            "U1",
            lambda packet: packet.__setitem__("integration_slice", True),
        )
        self._write_packet("U2", ["lib/b.txt"])
        self._update_packet(
            "U2",
            lambda packet: packet.__setitem__("integration_slice", True),
        )
        duplicate_output = io.StringIO()
        with self._gate_root(), contextlib.redirect_stderr(duplicate_output):
            self.assertEqual(
                2,
                guru_gate.cmd_check_commit(str(self.task)),
            )
        self.assertIn("exactly one integration slice", duplicate_output.getvalue())

        lite_contract = guru_contract.default_contract(
            guru_contract.ROUTE_LITE_TASK,
            guru_contract.RISK_LOW,
            created_by="test",
        )
        lite_contract["scope"]["allowed_paths"] = ["lib/a.txt", "lib/b.txt"]
        lite_contract["scope"]["max_files"] = None
        (self.task / "gate-contract.json").write_text(
            json.dumps(lite_contract),
            encoding="utf-8",
        )
        _, lifecycle_packets, lifecycle_error = guru_gate._final_lifecycle_context(
            str(self.task)
        )
        self.assertIsNone(lifecycle_packets)
        self.assertEqual("", lifecycle_error)

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

    def test_deterministic_commands_are_exact_string_stably_deduplicated(self) -> None:
        completed = subprocess.CompletedProcess([], 0, "ok", "")
        with mock.patch.object(
            guru_review_record.subprocess,
            "run",
            return_value=completed,
        ) as run:
            status, results = guru_review_record.run_deterministic_checks(
                ["true", "true", " true"],
                str(self.root),
            )
        self.assertEqual("passed", status)
        self.assertEqual(["true", " true"], [row["command"] for row in results])
        self.assertEqual(2, run.call_count)

    def test_deterministic_evidence_round_trip_and_tamper_fail_closed(self) -> None:
        results = [
            {
                "command": "true",
                "cwd": str(self.root),
                "exit_code": 0,
                "timed_out": False,
                "stdout_summary": "",
                "stderr_summary": "",
                "duration_ms": 1,
                "run_at": "2026-07-17T00:00:00Z",
            }
        ]
        key = "a" * 64
        record = guru_review_record.deterministic_evidence_record(
            key,
            ["true", "true"],
            "passed",
            results,
        )
        guru_review_record.append_deterministic_evidence(
            str(self.task),
            record,
        )
        self.assertEqual(
            record,
            guru_review_record.load_deterministic_evidence(
                str(self.task),
                key,
            ),
        )
        path = Path(
            guru_review_record.deterministic_evidence_path(str(self.task))
        )
        tampered = json.loads(path.read_text(encoding="utf-8"))
        tampered["results"][0]["exit_code"] = 1
        path.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "digest mismatch|status/results mismatch",
        ):
            guru_review_record.load_deterministic_evidence(
                str(self.task),
                key,
            )

    def test_deterministic_evidence_requires_complete_result_schema(self) -> None:
        result = {
            "command": "true",
            "cwd": str(self.root),
            "exit_code": 0,
            "timed_out": False,
            "stdout_summary": "",
            "stderr_summary": "",
            "duration_ms": 0,
            "run_at": "2026-07-17T00:00:00Z",
        }
        record = guru_review_record.deterministic_evidence_record(
            "a" * 64,
            ["true"],
            "passed",
            [result],
        )
        for field in (
            "command",
            "cwd",
            "exit_code",
            "timed_out",
            "stdout_summary",
            "stderr_summary",
            "duration_ms",
            "run_at",
        ):
            with self.subTest(omitted=field):
                candidate = json.loads(json.dumps(record))
                del candidate["results"][0][field]
                with self.assertRaises(guru_review_record.ReviewRecordError):
                    guru_review_record.validate_deterministic_evidence(
                        candidate
                    )
        invalid_values = (
            ("command", 7),
            ("command", ""),
            ("cwd", 7),
            ("cwd", " "),
            ("exit_code", "0"),
            ("exit_code", True),
            ("timed_out", 0),
            ("stdout_summary", []),
            ("stderr_summary", {}),
            ("duration_ms", True),
            ("duration_ms", "0"),
            ("run_at", 7),
            ("run_at", "2026-07-17T00:00:00"),
        )
        for field, value in invalid_values:
            with self.subTest(invalid_type_or_value=field):
                candidate = json.loads(json.dumps(record))
                candidate["results"][0][field] = value
                with self.assertRaises(guru_review_record.ReviewRecordError):
                    guru_review_record.validate_deterministic_evidence(
                        candidate
                    )
        missing_recorded_at = json.loads(json.dumps(record))
        del missing_recorded_at["recorded_at"]
        with self.assertRaises(guru_review_record.ReviewRecordError):
            guru_review_record.validate_deterministic_evidence(
                missing_recorded_at
            )
        for recorded_at in (
            None,
            "",
            "not-a-time",
            "2026-07-17T00:00:00",
        ):
            with self.subTest(recorded_at=recorded_at):
                candidate = json.loads(json.dumps(record))
                candidate["recorded_at"] = recorded_at
                with self.assertRaises(guru_review_record.ReviewRecordError):
                    guru_review_record.validate_deterministic_evidence(
                        candidate
                    )

    def test_deterministic_evidence_result_boundaries_and_consistency(self) -> None:
        boundary = {
            "command": "true",
            "cwd": str(self.root),
            "exit_code": 0,
            "timed_out": False,
            "stdout_summary": "x" * 500,
            "stderr_summary": "y" * 500,
            "duration_ms": 0,
            "run_at": "2026-07-17T00:00:00+08:00",
        }
        record = guru_review_record.deterministic_evidence_record(
            "b" * 64,
            ["true"],
            "passed",
            [boundary],
        )
        self.assertEqual(
            record,
            guru_review_record.validate_deterministic_evidence(record),
        )
        for field in ("stdout_summary", "stderr_summary"):
            with self.subTest(over_bound=field):
                candidate_result = dict(boundary)
                candidate_result[field] = "x" * 501
                with self.assertRaisesRegex(
                    guru_review_record.ReviewRecordError,
                    field,
                ):
                    guru_review_record.deterministic_evidence_record(
                        "b" * 64,
                        ["true"],
                        "passed",
                        [candidate_result],
                    )
        negative = dict(boundary, duration_ms=-1)
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "duration_ms",
        ):
            guru_review_record.deterministic_evidence_record(
                "b" * 64,
                ["true"],
                "passed",
                [negative],
            )
        timeout = dict(
            boundary,
            exit_code=None,
            timed_out=True,
            stderr_summary="timeout",
        )
        timed_out_record = guru_review_record.deterministic_evidence_record(
            "b" * 64,
            ["true"],
            "failed",
            [timeout],
        )
        self.assertEqual("failed", timed_out_record["status"])
        inconsistent_timeout = dict(timeout, exit_code=1)
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "timeout",
        ):
            guru_review_record.deterministic_evidence_record(
                "b" * 64,
                ["true"],
                "failed",
                [inconsistent_timeout],
            )
        unexplained_none = dict(
            boundary,
            exit_code=None,
            timed_out=False,
            stderr_summary="",
        )
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "exit_code=null",
        ):
            guru_review_record.deterministic_evidence_record(
                "b" * 64,
                ["true"],
                "failed",
                [unexplained_none],
            )
        exec_error = dict(unexplained_none, stderr_summary="exec error")
        self.assertEqual(
            "failed",
            guru_review_record.deterministic_evidence_record(
                "b" * 64,
                ["true"],
                "failed",
                [exec_error],
            )["status"],
        )

    def test_clean_normalization_rejects_repeated_supervisor_command_probe(self) -> None:
        packet = guru_review_record.load_packet(str(self.task), "U1")
        fields = guru_review_record.parse_verdict_block(
            self._clean_worker_verdict()
            + "reviewer_probe_command.1=true\n"
        )
        context = {
            "mode": "supervisor",
            "packet": packet,
            "implement_provider": "codex",
            "supervisor_deterministic_status": "passed",
            "deterministic_results": [],
            "run_id": "repeat",
            "slice_id": "U1",
            "review_target": "slice:U1",
            "target_paths": ["lib/a.txt"],
            "channel": "c",
            "worker": "w",
            "check_provider": "codex",
            "provider_override_source": "config_policy",
            "same_provider_user_quote": None,
            "high_risk_review_provider_policy": "codex",
            "review_target_kind": "slice",
            "reviewed_target_digest": "0" * 64,
            "supervisor_successful_commands": ["true"],
        }
        record, failure = guru_review_record.normalize_review_record(
            fields,
            context,
        )
        self.assertEqual("MALFORMED_REVIEW_OUTPUT", failure)
        self.assertEqual("blocked", record["review_result"])
        fields = guru_review_record.parse_verdict_block(
            self._clean_worker_verdict()
            + "reviewer_probe_command.1=git status --short\n"
        )
        record, failure = guru_review_record.normalize_review_record(
            fields,
            context,
        )
        self.assertIsNone(failure)
        self.assertEqual("clean", record["review_result"])

    def test_deterministic_failure_is_cached_before_worker_plan(self) -> None:
        self._write("lib/a.txt", b"u2 failure\n")
        self._git("add", "--", "lib/a.txt")
        failed_results = [
            {
                "command": "true",
                "cwd": str(self.root),
                "exit_code": 1,
                "timed_out": False,
                "stdout_summary": "",
                "stderr_summary": "failed",
                "duration_ms": 1,
                "run_at": "2026-07-17T00:00:00Z",
            }
        ]
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
                return_value=("failed", failed_results),
            ) as deterministic,
            mock.patch.object(guru_supervise, "build_run_plan") as build,
            mock.patch.object(guru_supervise, "_execute_plan") as execute,
        ):
            self.assertEqual(
                2,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("failure-first")
                ),
            )
            self.assertEqual(
                2,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("failure-second")
                ),
            )
        self.assertEqual(1, deterministic.call_count)
        build.assert_not_called()
        execute.assert_not_called()

    def test_v2_slice_review_requires_staged_before_deterministic_or_worker(
        self,
    ) -> None:
        self._write("lib/a.txt", b"u2 unstaged whitespace error  \n")
        args = self._supervisor_args("unstaged-v2")
        args.staged = False
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
            ) as deterministic,
            mock.patch.object(guru_supervise, "build_run_plan") as build,
            mock.patch.object(guru_supervise, "_execute_plan") as execute,
        ):
            self.assertEqual(2, guru_supervise.run_implementation_review(args))
        deterministic.assert_not_called()
        build.assert_not_called()
        execute.assert_not_called()

        self._git("add", "--", "lib/a.txt")
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertNotIn("SLICE_COMMIT_READY", output)
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        reviews = [
            json.loads(line)
            for line in review_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual("SCOPE_INVALID", reviews[-1]["supervisor_failure"])
        self.assertFalse(
            any(review.get("review_result") == "clean" for review in reviews)
        )

    def test_v1_slice_review_keeps_legacy_worktree_path(self) -> None:
        self._update_packet(
            "U1",
            lambda packet: packet.pop(
                guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD
            ),
        )
        self._write("lib/a.txt", b"v1 worktree review\n")
        args = self._supervisor_args("v1-worktree")
        args.staged = False
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._clean_worker_verdict()),
            ) as execute,
        ):
            self.assertEqual(0, guru_supervise.run_implementation_review(args))
        execute.assert_called_once()
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        review = json.loads(review_path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual("clean", review["review_result"])
        self.assertEqual("slice:U1", review["review_target"])
        self.assertNotIn(
            guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD,
            review,
        )

    def test_semantic_input_drift_after_checks_blocks_worker_dispatch(self) -> None:
        self._write("lib/a.txt", b"u2 semantic drift before worker\n")
        self._git("add", "--", "lib/a.txt")
        real_run = guru_review_record.run_deterministic_checks

        def run_then_mutate(commands, repo_root):
            result = real_run(commands, repo_root)
            self._update_packet(
                "U1",
                lambda packet: packet["invariants"][0].update(
                    {"rule": "Changed after deterministic checks."}
                ),
            )
            return result

        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
                side_effect=run_then_mutate,
            ),
            mock.patch.object(guru_supervise, "build_run_plan") as build,
            mock.patch.object(guru_supervise, "_execute_plan") as execute,
        ):
            self.assertEqual(
                2,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("drift-before-worker")
                ),
            )
        build.assert_not_called()
        execute.assert_not_called()
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        self.assertFalse(review_path.exists())

    def test_semantic_input_drift_at_append_writes_no_clean_record(self) -> None:
        self._write("lib/a.txt", b"u2 semantic drift at append\n")
        self._git("add", "--", "lib/a.txt")
        real_normalize = guru_review_record.normalize_review_record

        def mutate_then_normalize(fields, context):
            prd = self.task / "prd.md"
            prd.write_bytes(
                prd.read_bytes().replace(
                    b"Exact bytes.",
                    b"Changed immediately before append.",
                )
            )
            return real_normalize(fields, context)

        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._clean_worker_verdict()),
            ),
            mock.patch.object(
                guru_review_record,
                "normalize_review_record",
                side_effect=mutate_then_normalize,
            ),
        ):
            self.assertEqual(
                2,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("drift-at-append")
                ),
            )
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        if review_path.exists():
            reviews = [
                json.loads(line)
                for line in review_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertFalse(
                any(
                    row.get("run_id") == "drift-at-append-review-1"
                    and row.get("review_result") == "clean"
                    for row in reviews
                )
            )
        rc, output = self._check_slice("U1")
        self.assertEqual(2, rc)
        self.assertNotIn("SLICE_COMMIT_READY", output)

    def test_clean_evidence_reuse_runs_zero_checks_and_zero_worker(self) -> None:
        self._write("lib/a.txt", b"u2 clean\n")
        self._git("add", "--", "lib/a.txt")
        config = self._supervision_config()
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=config,
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._clean_worker_verdict()),
            ) as execute,
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
                wraps=guru_review_record.run_deterministic_checks,
            ) as deterministic,
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("clean-first")
                ),
            )
            first_det_calls = deterministic.call_count
            first_worker_calls = execute.call_count
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("clean-second")
                ),
            )
        self.assertEqual(1, first_det_calls)
        self.assertEqual(1, first_worker_calls)
        self.assertEqual(first_det_calls, deterministic.call_count)
        self.assertEqual(first_worker_calls, execute.call_count)
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        latest = json.loads(review_path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual("clean-second-review-1", latest["run_id"])
        self.assertEqual("evidence-cache", latest["channel"])
        self.assertEqual("semantic-review-reuse", latest["worker"])
        self.assertIn("reused_from_run_id=clean-first-review-1", latest["message"])

    def test_later_findings_supersede_same_key_clean_reuse(self) -> None:
        self._seed_clean_lifecycle_evidence()
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        clean = json.loads(
            review_path.read_text(encoding="utf-8").splitlines()[-1]
        )
        findings = json.loads(json.dumps(clean))
        first_invariant = next(iter(findings["invariant_verdicts"]))
        findings["invariant_verdicts"][first_invariant] = {
            "status": "fail",
            "evidence": "concurrent semantic finding",
            "reason": "",
        }
        findings["invariant_verdicts_digest"] = (
            guru_review_record.invariant_verdicts_digest(
                findings["invariant_verdicts"]
            )
        )
        findings.update(
            {
                "run_id": "concurrent-findings-after-clean",
                "review_result": "findings",
                "route_class": "IMPLEMENT_DEFECT",
                "invariant_coverage": "failed",
                "required_satisfied": False,
            }
        )
        guru_review_record.append_record(str(self.task), findings)
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
                wraps=guru_review_record.run_deterministic_checks,
            ) as deterministic,
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._clean_worker_verdict()),
            ) as execute,
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("review-after-late-findings")
                ),
            )
        deterministic.assert_not_called()
        self.assertEqual(1, execute.call_count)

    def test_latest_clean_after_findings_is_reusable(self) -> None:
        self._seed_clean_lifecycle_evidence()
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        clean = json.loads(
            review_path.read_text(encoding="utf-8").splitlines()[-1]
        )
        findings = json.loads(json.dumps(clean))
        first_invariant = next(iter(findings["invariant_verdicts"]))
        findings["invariant_verdicts"][first_invariant] = {
            "status": "fail",
            "evidence": "semantic finding before latest clean",
            "reason": "",
        }
        findings["invariant_verdicts_digest"] = (
            guru_review_record.invariant_verdicts_digest(
                findings["invariant_verdicts"]
            )
        )
        findings.update(
            {
                "run_id": "findings-after-seed",
                "review_result": "findings",
                "route_class": "IMPLEMENT_DEFECT",
                "invariant_coverage": "failed",
                "required_satisfied": False,
            }
        )
        guru_review_record.append_record(str(self.task), findings)
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
            ) as deterministic,
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._clean_worker_verdict()),
            ) as execute,
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("produce-latest-clean")
                ),
            )
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("reuse-latest-clean")
                ),
            )
        deterministic.assert_not_called()
        self.assertEqual(1, execute.call_count)

    def test_later_malformed_attempt_blocks_same_key_clean_reuse(self) -> None:
        self._seed_clean_lifecycle_evidence()
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        clean = json.loads(
            review_path.read_text(encoding="utf-8").splitlines()[-1]
        )
        malformed = dict(clean)
        malformed.update(
            {
                "run_id": "malformed-after-clean",
                "review_result": "blocked",
                "route_class": "none",
                "supervisor_failure": "MALFORMED_REVIEW_OUTPUT",
                "required_satisfied": False,
                "repairable": False,
            }
        )
        guru_review_record.append_record(str(self.task), malformed)
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
                wraps=guru_review_record.run_deterministic_checks,
            ) as deterministic,
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._clean_worker_verdict()),
            ) as execute,
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("review-after-malformed")
                ),
            )
        deterministic.assert_not_called()
        self.assertEqual(1, execute.call_count)

    def test_clean_reuse_refreshes_latest_row_and_slice_gate(self) -> None:
        config = self._supervision_config()

        def run_clean(content: bytes, run_id: str) -> None:
            self._write("lib/a.txt", content)
            self._git("add", "--", "lib/a.txt")
            with (
                mock.patch.object(
                    guru_supervise,
                    "_guru_gate_check_implementation",
                    return_value=0,
                ),
                mock.patch.object(
                    guru_supervise,
                    "_load_config",
                    return_value=config,
                ),
                mock.patch.object(
                    guru_supervise,
                    "_execute_plan",
                    return_value=(0, "done", self._clean_worker_verdict()),
                ),
            ):
                self.assertEqual(
                    0,
                    guru_supervise.run_implementation_review(
                        self._supervisor_args(run_id)
                    ),
                )

        run_clean(b"snapshot-k\n", "snapshot-k")
        run_clean(b"snapshot-k2\n", "snapshot-k2")
        self._write("lib/a.txt", b"snapshot-k\n")
        self._git("add", "--", "lib/a.txt")
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=config,
            ),
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
            ) as deterministic,
            mock.patch.object(guru_supervise, "build_run_plan") as build,
            mock.patch.object(guru_supervise, "_execute_plan") as execute,
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("snapshot-k-restored")
                ),
            )
        deterministic.assert_not_called()
        build.assert_not_called()
        execute.assert_not_called()
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        latest = json.loads(review_path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual("snapshot-k-restored-review-1", latest["run_id"])
        self.assertIn("reused_from_run_id=snapshot-k-review-1", latest["message"])
        out = io.StringIO()
        err = io.StringIO()
        with (
            mock.patch.object(
                guru_gate,
                "_repo_root",
                return_value=str(self.root),
            ),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            rc = guru_gate.cmd_check_slice_commit(str(self.task), "U1")
        output = out.getvalue() + err.getvalue()
        self.assertEqual(0, rc, output)
        self.assertIn("SLICE_COMMIT_READY", output)
        self.assertIn("snapshot-k-restored-review-1", output)

    def test_findings_reuse_passed_deterministic_evidence(self) -> None:
        self._write("lib/a.txt", b"u2 findings then clean\n")
        self._git("add", "--", "lib/a.txt")
        finding = (
            self._clean_worker_verdict()
            .replace("review_result=clean", "review_result=findings")
            .replace("route_class=none", "route_class=IMPLEMENT_DEFECT")
            .replace(
                "invariant_coverage=all_passed",
                "invariant_coverage=failed",
            )
            .replace(
                "invariant_status.INV-U1=pass",
                "invariant_status.INV-U1=fail",
            )
        )
        outputs = [
            (0, "done", finding),
            (0, "done", self._clean_worker_verdict()),
        ]
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                side_effect=outputs,
            ) as execute,
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
                wraps=guru_review_record.run_deterministic_checks,
            ) as deterministic,
        ):
            self.assertEqual(
                2,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("finding")
                ),
            )
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("repair")
                ),
            )
        self.assertEqual(1, deterministic.call_count)
        self.assertEqual(2, execute.call_count)

    def test_interrupted_worker_reuses_passed_deterministic_evidence(self) -> None:
        self._write("lib/a.txt", b"u2 interrupted then clean\n")
        self._git("add", "--", "lib/a.txt")
        outputs = [
            (1, "error", ""),
            (0, "done", self._clean_worker_verdict()),
        ]
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                side_effect=outputs,
            ) as execute,
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
                wraps=guru_review_record.run_deterministic_checks,
            ) as deterministic,
        ):
            self.assertEqual(
                1,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("interrupted")
                ),
            )
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("retry")
                ),
            )
        self.assertEqual(1, deterministic.call_count)
        self.assertEqual(2, execute.call_count)
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        reviews = [
            json.loads(line)
            for line in review_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(
            ["MALFORMED_REVIEW_OUTPUT", "none"],
            [row["supervisor_failure"] for row in reviews],
        )

    def test_concurrent_invocations_execute_each_unique_command_once(self) -> None:
        self._write("lib/a.txt", b"u2 concurrent\n")
        self._git("add", "--", "lib/a.txt")
        self._update_packet(
            "U1",
            lambda packet: packet.update(
                {"deterministic_checks": ["true", "true"]}
            ),
        )
        counter = 0
        counter_lock = threading.Lock()

        def deterministic_once(commands, repo_root):
            nonlocal counter
            self.assertEqual(["true"], commands)
            with counter_lock:
                counter += 1
            time.sleep(0.15)
            return (
                "passed",
                [
                    {
                        "command": commands[0],
                        "cwd": repo_root,
                        "exit_code": 0,
                        "timed_out": False,
                        "stdout_summary": "",
                        "stderr_summary": "",
                        "duration_ms": 1,
                        "run_at": "2026-07-17T00:00:00Z",
                    }
                ],
            )

        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
                side_effect=deterministic_once,
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._clean_worker_verdict()),
            ),
            mock.patch.object(
                guru_supervise,
                "_review_read_only_snapshot",
                return_value="stable",
            ),
        ):
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [
                    pool.submit(
                        guru_supervise.run_implementation_review,
                        self._supervisor_args(f"concurrent-{index}"),
                    )
                    for index in range(2)
                ]
                results = [future.result(timeout=10) for future in futures]
        self.assertEqual([0, 0], results)
        self.assertEqual(1, counter)
        cache_path = Path(
            guru_review_record.deterministic_evidence_path(str(self.task))
        )
        cache_rows = [
            json.loads(line)
            for line in cache_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(1, len(cache_rows))
        validated_cache = guru_review_record.validate_deterministic_evidence(
            cache_rows[0]
        )
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        reviews = [
            json.loads(line)
            for line in review_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(2, len(reviews))
        self.assertTrue(
            all(
                review["deterministic_evidence_key"]
                == validated_cache["evidence_key"]
                and review["deterministic_results_digest"]
                == validated_cache["deterministic_results_digest"]
                for review in reviews
            )
        )
        lock_dir = cache_path.parent / "deterministic-locks"
        self.assertEqual(1, len(list(lock_dir.glob("*.lock"))))

    def test_deterministic_evidence_lock_releases_on_exception(self) -> None:
        lock = guru_review_record.DeterministicEvidenceLock(
            str(self.task),
            "c" * 64,
            timeout_seconds=1,
            poll_seconds=0.01,
        )
        with self.assertRaisesRegex(RuntimeError, "inside lock"):
            with lock:
                self.assertTrue(Path(lock.path).is_file())
                raise RuntimeError("inside lock")
        with lock:
            self.assertTrue(Path(lock.path).is_file())

    def test_deterministic_evidence_lock_recovers_after_hard_exit(self) -> None:
        key = "d" * 64
        script = (
            "import os,sys;"
            f"sys.path.insert(0,{str(VERIFY_DIR)!r});"
            "import guru_review_record as record;"
            f"lock=record.DeterministicEvidenceLock({str(self.task)!r},{key!r});"
            "lock.__enter__();"
            "os._exit(0)"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=self.root,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        lock = guru_review_record.DeterministicEvidenceLock(
            str(self.task),
            key,
            timeout_seconds=2,
            poll_seconds=0.01,
        )
        self.assertTrue(Path(lock.path).is_file())
        with lock:
            self.assertTrue(Path(lock.path).is_file())
        with lock:
            self.assertTrue(Path(lock.path).is_file())
        self.assertFalse(Path(lock.reclaim_path).exists())

    def test_deterministic_evidence_lock_never_steals_live_owner(self) -> None:
        owner = guru_review_record.DeterministicEvidenceLock(
            str(self.task),
            "e" * 64,
            timeout_seconds=1,
            poll_seconds=0.01,
        )
        with owner:
            before = Path(owner.path).read_bytes()
            waiter = guru_review_record.DeterministicEvidenceLock(
                str(self.task),
                "e" * 64,
                timeout_seconds=0.12,
                poll_seconds=0.01,
            )
            started = time.monotonic()
            with self.assertRaisesRegex(
                guru_review_record.ReviewRecordError,
                "timed out",
            ):
                waiter.__enter__()
            self.assertLess(time.monotonic() - started, 1.0)
            self.assertEqual(before, Path(owner.path).read_bytes())
        with owner:
            self.assertTrue(Path(owner.path).is_file())

    def test_deterministic_evidence_lock_replaces_unlocked_stale_owner(self) -> None:
        lock = guru_review_record.DeterministicEvidenceLock(
            str(self.task),
            "f" * 64,
            timeout_seconds=0.2,
            poll_seconds=0.01,
        )
        path = Path(lock.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"pid":"unknown"}\n', encoding="utf-8")
        with lock:
            self.assertEqual(lock.owner_bytes, path.read_bytes())

    def test_deterministic_evidence_lock_ownership_change_fails_closed(self) -> None:
        lock = guru_review_record.DeterministicEvidenceLock(
            str(self.task),
            "1" * 64,
        )
        replacement = b'{"replacement":"live-owner"}\n'
        with self.assertRaisesRegex(
            guru_review_record.ReviewRecordError,
            "ownership changed",
        ):
            with lock:
                Path(lock.path).write_bytes(replacement)
        self.assertEqual(replacement, Path(lock.path).read_bytes())

    def test_deterministic_evidence_lock_cleanup_failure_fails_closed(self) -> None:
        lock = guru_review_record.DeterministicEvidenceLock(
            str(self.task),
            "2" * 64,
        )
        with (
            mock.patch.object(
                lock,
                "_unlock_file",
                side_effect=PermissionError("cleanup denied"),
            ),
            self.assertRaisesRegex(
                guru_review_record.ReviewRecordError,
                "cannot release",
            ),
        ):
            with lock:
                pass
        self.assertTrue(Path(lock.path).exists())
        with lock:
            self.assertTrue(Path(lock.path).is_file())

    def test_reviewer_brief_injects_bounded_results_and_no_repeat_rule(self) -> None:
        results = [
            {
                "command": "true",
                "exit_code": 0,
                "timed_out": False,
                "stdout_summary": "x" * 500,
                "stderr_summary": "",
                "duration_ms": 1,
                "run_at": "2026-07-17T00:00:00Z",
            }
        ]
        brief = guru_supervise._deterministic_reviewer_brief(
            "a" * 64,
            results,
            reused=True,
        )
        self.assertIn("Do not rerun any exact command", brief)
        self.assertIn("reviewer_probe_command.N", brief)
        self.assertIn('"command":"true"', brief)
        self.assertIn('"reused":true', brief)
        self.assertIn(
            "supervisor_deterministic_evidence_truncated=false",
            brief,
        )

    def test_reviewer_brief_has_total_bound_and_truncation_marker(self) -> None:
        results = [
            {
                "command": f"probe-{index}-" + ("x" * 1000),
                "exit_code": 0,
                "timed_out": False,
                "stdout_summary": "y" * 500,
                "stderr_summary": "z" * 500,
                "duration_ms": 1,
                "run_at": "2026-07-17T00:00:00Z",
            }
            for index in range(40)
        ]
        brief = guru_supervise._deterministic_reviewer_brief(
            "a" * 64,
            results,
            reused=False,
        )
        self.assertLessEqual(
            len(brief),
            guru_supervise.DETERMINISTIC_REVIEW_BRIEF_MAX_CHARS,
        )
        self.assertIn(
            "supervisor_deterministic_evidence_truncated=true",
            brief,
        )

    def test_reviewer_write_attempt_blocks_clean_normalization(self) -> None:
        self._write("lib/a.txt", b"u2 reviewer write\n")
        self._git("add", "--", "lib/a.txt")
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._clean_worker_verdict()),
            ),
            mock.patch.object(
                guru_supervise,
                "_review_read_only_snapshot",
                side_effect=["before", "after"],
            ),
        ):
            self.assertEqual(
                2,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("write-attempt")
                ),
            )
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        latest = json.loads(review_path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual("SCOPE_INVALID", latest["supervisor_failure"])

    def test_host_turn_diff_ref_does_not_mask_reviewer_findings(self) -> None:
        self._write("lib/a.txt", b"u2 host observation ref\n")
        self._git("add", "--", "lib/a.txt")

        def create_host_ref(_plan, _config):
            tree = self._git("write-tree")
            self._git(
                "update-ref",
                "refs/codex/turn-diffs/captures/123/worker/base",
                tree,
            )
            return (
                0,
                "done",
                "review_result=findings\n"
                "route_class=IMPLEMENT_DEFECT\n"
                "review_target=slice:U1\n"
                "review_provider=codex\n"
                "deterministic_checks=passed\n"
                "dirty_scope=isolated\n"
                "invariant_coverage=failed\n"
                "invariant_status.INV-U1=fail\n"
                "invariant_evidence.INV-U1=independent semantic blocker\n",
            )

        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                side_effect=create_host_ref,
            ),
        ):
            self.assertEqual(
                2,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("host-observation-ref")
                ),
            )
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        latest = json.loads(
            review_path.read_text(encoding="utf-8").splitlines()[-1]
        )
        self.assertEqual("host-observation-ref-review-1", latest["run_id"])
        self.assertEqual("findings", latest["review_result"])
        self.assertEqual("IMPLEMENT_DEFECT", latest["route_class"])
        self.assertEqual("none", latest["supervisor_failure"])

    def test_reviewer_ref_mutation_blocks_clean_normalization(self) -> None:
        self._write("lib/a.txt", b"u2 reviewer ref mutation\n")
        self._git("add", "--", "lib/a.txt")

        def create_refs(_plan, _config):
            head = self._git("rev-parse", "HEAD")
            self._git("branch", "review-worker-branch")
            self._git("tag", "review-worker-tag")
            self._git("update-ref", "refs/heads/review-worker-update", head)
            return 0, "done", self._clean_worker_verdict()

        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                side_effect=create_refs,
            ),
        ):
            self.assertEqual(
                2,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("ref-mutation")
                ),
            )
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        reviews = [
            json.loads(line)
            for line in review_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual("SCOPE_INVALID", reviews[-1]["supervisor_failure"])
        self.assertFalse(
            any(
                review.get("run_id") == "ref-mutation-review-1"
                and review.get("review_result") == "clean"
                for review in reviews
            )
        )

    def test_reviewer_broken_non_head_refs_block_clean_normalization(self) -> None:
        self._write("lib/a.txt", b"u2 reviewer broken refs\n")
        self._git("add", "--", "lib/a.txt")

        def create_broken_refs(_plan, _config):
            git_dir = Path(self._git("rev-parse", "--git-dir"))
            if not git_dir.is_absolute():
                git_dir = self.root / git_dir
            refs_dir = git_dir / "refs" / "heads"
            refs_dir.mkdir(parents=True, exist_ok=True)
            (refs_dir / "review-worker-empty").write_bytes(b"")
            (refs_dir / "review-worker-malformed").write_bytes(b"xyz\n")
            return 0, "done", self._clean_worker_verdict()

        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                side_effect=create_broken_refs,
            ),
        ):
            self.assertEqual(
                2,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("broken-ref-mutation")
                ),
            )
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        reviews = [
            json.loads(line)
            for line in review_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual("SCOPE_INVALID", reviews[-1]["supervisor_failure"])
        self.assertFalse(
            any(
                review.get("run_id") == "broken-ref-mutation-review-1"
                and review.get("review_result") == "clean"
                for review in reviews
            )
        )

    def test_reviewer_snapshot_supports_unborn_head_without_weakening_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            tracked = root / "tracked.txt"
            tracked.write_bytes(b"staged\n")
            subprocess.run(
                ["git", "add", "--", "tracked.txt"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            before = guru_supervise._review_read_only_snapshot(root)
            self.assertEqual(before, guru_supervise._review_read_only_snapshot(root))

            tracked.write_bytes(b"worktree changed\n")
            self.assertNotEqual(
                before,
                guru_supervise._review_read_only_snapshot(root),
            )

    def test_reviewer_snapshot_binds_symbolic_and_detached_head_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.name", "Snapshot Test"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "snapshot@example.test"],
                cwd=root,
                check=True,
            )
            (root / "tracked.txt").write_bytes(b"tracked\n")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                ["git", "commit", "-m", "baseline"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "branch", "same-commit"],
                cwd=root,
                check=True,
            )
            symbolic = guru_supervise._review_read_only_snapshot(root)
            subprocess.run(
                ["git", "switch", "same-commit"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            other_symbolic = guru_supervise._review_read_only_snapshot(root)
            subprocess.run(
                ["git", "checkout", "--detach"],
                cwd=root,
                check=True,
                capture_output=True,
            )
            detached = guru_supervise._review_read_only_snapshot(root)

            self.assertNotEqual(symbolic, other_symbolic)
            self.assertNotEqual(other_symbolic, detached)

    def test_reviewer_snapshot_rejects_existing_invalid_branch_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            head_ref = subprocess.run(
                ["git", "symbolic-ref", "-q", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            ref_path = root / ".git" / head_ref
            ref_path.parent.mkdir(parents=True, exist_ok=True)
            ref_path.write_text("1".zfill(40) + "\n", encoding="ascii")

            with self.assertRaises(guru_supervise.GuruSupervisionError):
                guru_supervise._review_read_only_snapshot(root)

    def test_reviewer_snapshot_hard_stops_unborn_to_invalid_ref_mutation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
            before = guru_supervise._review_read_only_snapshot(root)
            head_ref = subprocess.run(
                ["git", "symbolic-ref", "-q", "HEAD"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            ref_path = root / ".git" / head_ref
            ref_path.parent.mkdir(parents=True, exist_ok=True)

            self.assertIsInstance(before, str)
            for malformed in (b"", b"xyz\n"):
                with self.subTest(malformed=malformed):
                    ref_path.write_bytes(malformed)
                    with self.assertRaises(guru_supervise.GuruSupervisionError):
                        guru_supervise._review_read_only_snapshot(root)

    def test_reviewer_snapshot_rejects_non_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(guru_supervise.GuruSupervisionError):
                guru_supervise._review_read_only_snapshot(Path(temp))

    def test_non_slice_staged_review_keeps_legacy_execution_path(self) -> None:
        self._update_packet(
            "U1",
            lambda packet: packet.pop(
                guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD
            ),
        )
        self._write("lib/a.txt", b"legacy staged review\n")
        self._git("add", "--", "lib/a.txt")
        legacy_config = guru_supervise.replace(
            self._supervision_config(),
            current_provider="claude",
            provider="claude",
        )
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=legacy_config,
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._staged_worker_verdict()),
            ) as execute,
        ):
            for run_id, staged, contract in (
                ("legacy-staged", True, False),
                ("legacy-contract", False, True),
            ):
                with self.subTest(run_id=run_id):
                    args = self._supervisor_args(run_id)
                    args.slice = None
                    args.staged = staged
                    args.contract = contract
                    self.assertEqual(
                        0,
                        guru_supervise.run_implementation_review(args),
                    )
        self.assertEqual(2, execute.call_count)
        self.assertFalse(
            Path(
                guru_review_record.deterministic_evidence_path(
                    str(self.task)
                )
            ).exists()
        )
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        review = json.loads(review_path.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual("staged:index", review["review_target"])
        self.assertNotIn("evidence_key", review)

    def test_packet_backed_legacy_implement_check_appends_structured_review(
        self,
    ) -> None:
        self._update_packet(
            "U1",
            lambda packet: packet.pop(
                guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD
            ),
        )
        self._write("lib/a.txt", b"legacy implement check\n")
        args = self._supervisor_args("legacy-implement-check")
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_scope_preflight",
                return_value=None,
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                side_effect=[
                    (0, "done", ""),
                    (0, "done", self._clean_worker_verdict()),
                ],
            ),
        ):
            self.assertEqual(0, guru_supervise.run_implement_check(args))
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        review = json.loads(
            review_path.read_text(encoding="utf-8").splitlines()[-1]
        )
        self.assertEqual("clean", review["review_result"])
        self.assertEqual("legacy-implement-check-check-1", review["run_id"])
        self.assertNotIn(
            guru_review_record.REVIEW_EVIDENCE_SCHEMA_FIELD,
            review,
        )

    def test_append_supervisor_review_call_contract_ast_probe(self) -> None:
        tree = ast.parse(
            Path(guru_supervise.__file__).read_text(encoding="utf-8")
        )
        function = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "_append_supervisor_review_record"
        )
        required = {
            argument.arg
            for argument, default in zip(
                function.args.kwonlyargs,
                function.args.kw_defaults,
            )
            if default is None
        }
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_append_supervisor_review_record"
        ]
        self.assertGreaterEqual(len(calls), 3)
        for call in calls:
            supplied = {
                keyword.arg
                for keyword in call.keywords
                if keyword.arg is not None
            }
            self.assertEqual(set(), required - supplied, ast.unparse(call))

    def test_clean_reuse_rejects_tampered_deterministic_results_binding(self) -> None:
        self._seed_clean_lifecycle_evidence()
        self._update_latest_review(
            lambda review: review["deterministic_results"][0].update(
                {"duration_ms": 999}
            )
        )
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._clean_worker_verdict()),
            ) as execute,
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
            ) as deterministic,
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("tampered-results")
                ),
            )
        deterministic.assert_not_called()
        execute.assert_called_once()
        latest = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        ).read_text(encoding="utf-8").splitlines()[-1]
        self.assertNotIn("validated clean semantic evidence reused", latest)

    def test_clean_reuse_rejects_wrong_deterministic_evidence_key(self) -> None:
        self._seed_clean_lifecycle_evidence()
        self._update_latest_review(
            lambda review: review.update(
                {"deterministic_evidence_key": "f" * 64}
            )
        )
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._clean_worker_verdict()),
            ) as execute,
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("wrong-key")
                ),
            )
        execute.assert_called_once()
        latest = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        ).read_text(encoding="utf-8").splitlines()[-1]
        self.assertNotIn("validated clean semantic evidence reused", latest)

    def test_clean_reuse_missing_cache_reruns_deterministic_checks(self) -> None:
        self._seed_clean_lifecycle_evidence()
        Path(
            guru_review_record.deterministic_evidence_path(str(self.task))
        ).unlink()
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(
                guru_supervise,
                "_execute_plan",
                return_value=(0, "done", self._clean_worker_verdict()),
            ) as execute,
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
                wraps=guru_review_record.run_deterministic_checks,
            ) as deterministic,
        ):
            self.assertEqual(
                0,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("missing-cache")
                ),
            )
        self.assertEqual(1, deterministic.call_count)
        execute.assert_called_once()
        latest = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        ).read_text(encoding="utf-8").splitlines()[-1]
        self.assertNotIn("validated clean semantic evidence reused", latest)

    def test_clean_reuse_malformed_cache_fails_closed(self) -> None:
        self._seed_clean_lifecycle_evidence()
        review_path = (
            self.task
            / "review-records"
            / "implementation-reviews.jsonl"
        )
        before = len(review_path.read_text(encoding="utf-8").splitlines())
        path = Path(
            guru_review_record.deterministic_evidence_path(str(self.task))
        )
        path.write_text("{malformed}\n", encoding="utf-8")
        with (
            mock.patch.object(
                guru_supervise,
                "_guru_gate_check_implementation",
                return_value=0,
            ),
            mock.patch.object(
                guru_supervise,
                "_load_config",
                return_value=self._supervision_config(),
            ),
            mock.patch.object(guru_supervise, "_execute_plan") as execute,
            mock.patch.object(
                guru_review_record,
                "run_deterministic_checks",
            ) as deterministic,
        ):
            self.assertEqual(
                2,
                guru_supervise.run_implementation_review(
                    self._supervisor_args("malformed-cache")
                ),
            )
        deterministic.assert_not_called()
        execute.assert_not_called()
        self.assertEqual(
            before,
            len(review_path.read_text(encoding="utf-8").splitlines()),
        )


if __name__ == "__main__":
    unittest.main()
