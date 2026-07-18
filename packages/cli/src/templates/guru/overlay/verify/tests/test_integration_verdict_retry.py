from __future__ import annotations

import errno
import hashlib
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

import guru_review_record as review_record  # noqa: E402


class IntegrationVerdictRetryTests(unittest.TestCase):
    invariant_ids = ["INV-RT-006", "INV-RT-007", "INV-RT-008"]

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.task = Path(self.temp.name) / "task"
        self.task.mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _digest(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _identity(self, **updates: str) -> dict:
        identity = {
            field: self._digest(field)
            for field in review_record.RETRY_IDENTITY_FIELDS
        }
        identity.update(updates)
        return review_record.build_retry_identity(identity)

    def _metadata(self, run_id: str = "20260718090000-123-review-1") -> dict:
        return {
            "run_id": run_id,
            "review_target": "slice:SL-VERDICT-EVIDENCE",
            "provider": "codex",
            "timestamp": "2026-07-18T09:00:00+08:00",
        }

    def _verdict(
        self,
        *,
        result: str = "clean",
        route: str = "none",
        include_result: bool = True,
        include_evidence: bool = True,
        failing_invariant: str | None = None,
    ) -> str:
        lines = []
        if include_result:
            lines.append(f"review_result={result}")
        lines.extend(
            [
                f"route_class={route}",
                "review_target=slice:SL-VERDICT-EVIDENCE",
                "review_provider=codex",
                "deterministic_checks=passed",
                "dirty_scope=isolated",
                "invariant_coverage="
                + ("failed" if failing_invariant else "all_passed"),
            ]
        )
        for invariant_id in self.invariant_ids:
            status = "fail" if invariant_id == failing_invariant else "pass"
            lines.append(f"invariant_status.{invariant_id}={status}")
            if include_evidence or status == "fail":
                lines.append(
                    f"invariant_evidence.{invariant_id}="
                    + ("semantic defect" if status == "fail" else "focused test")
                )
        return "\n".join(lines) + "\n"

    def _packet(self, *, schema_version: int = 2, risk: str = "high") -> dict:
        packet = {
            "risk": risk,
            "semantic_review_provider": {
                "required": True,
                "provider": "codex",
                "ocr": "disabled",
            },
            "invariants": [
                {"invariant_id": invariant_id}
                for invariant_id in self.invariant_ids
            ],
        }
        if schema_version == 2:
            packet[review_record.REVIEW_EVIDENCE_SCHEMA_FIELD] = 2
        return packet

    def _context(self, identity: dict, *, schema_version: int = 2) -> dict:
        context = {
            "mode": "supervisor",
            "packet": self._packet(schema_version=schema_version),
            "run_id": "20260718090000-123-review-1",
            "slice_id": "SL-VERDICT-EVIDENCE",
            "review_target": "slice:SL-VERDICT-EVIDENCE",
            "target_paths": ["guru-template/overlay/verify/guru_review_record.py"],
            "channel": "review-channel",
            "worker": "semantic-reviewer",
            "timestamp": "2026-07-18T09:00:00+08:00",
            "deterministic_results": [],
            "supervisor_deterministic_status": "passed",
            "supervisor_successful_commands": [],
            "provider_override_source": "config_policy",
            "same_provider_user_quote": None,
            "high_risk_review_provider_policy": "codex",
            "check_provider": "codex",
            "implement_provider": "codex",
            "review_target_kind": "slice",
            "reviewed_target_digest": identity["reviewed_target_digest"],
            "retry_identity": identity,
        }
        if schema_version == 2:
            context[review_record.REVIEW_EVIDENCE_SCHEMA_FIELD] = 2
        return context

    def _compact_proof_context(self, identity: dict) -> dict:
        return {
            "run_id": "20260718090000-123-review-1",
            "slice_id": "SL-VERDICT-EVIDENCE",
            "review_target": "slice:SL-VERDICT-EVIDENCE",
            "target_paths": ["guru-template/overlay/verify/guru_review_record.py"],
            "channel": "review-channel",
            "worker": "semantic-reviewer",
            "deterministic_checks": "passed",
            "deterministic_results": [],
            "reviewed_target_digest": identity["reviewed_target_digest"],
            "expected_invariants": self._packet()["invariants"],
            "evidence_components": {
                field: identity[field]
                for field in review_record.RETRY_IDENTITY_FIELDS[:-1]
            },
            "evidence_key": self._digest("evidence-key"),
            "implementation_review_policy": {
                "provider_override_source": "config_policy",
                "same_provider_user_quote": None,
                "high_risk_review_provider_policy": "codex",
                "review_target_kind": "slice",
                "implement_provider": "codex",
                "check_provider": "codex",
                "review_provider": "codex",
            },
        }

    def _official_rows(self) -> list[dict]:
        path = self.task / "review-records" / "implementation-reviews.jsonl"
        if not path.exists():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_retry_identity_is_exact_stable_and_tamper_evident(self) -> None:
        identity = self._identity()
        reverse_order = {
            field: identity[field]
            for field in reversed(review_record.RETRY_IDENTITY_FIELDS)
        }
        self.assertEqual(identity, review_record.build_retry_identity(reverse_order))
        self.assertEqual(set(identity), set(review_record.RETRY_IDENTITY_FIELDS))

        for field in review_record.RETRY_IDENTITY_FIELDS:
            tampered = dict(identity)
            tampered[field] = self._digest(f"changed-{field}")
            self.assertNotEqual(identity, review_record.build_retry_identity(tampered))

        for invalid in (
            {key: value for key, value in identity.items() if key != "proof_bundle_digest"},
            {**identity, "extra": self._digest("extra")},
            {**identity, "proof_bundle_digest": 1},
            {**identity, "proof_bundle_digest": "A" * 64},
        ):
            with self.assertRaises(review_record.ReviewRecordError):
                review_record.build_retry_identity(invalid)

    def test_classification_matrix_is_fail_closed(self) -> None:
        identity = self._identity()
        self.assertEqual(
            "valid",
            review_record.classify_retryable_format_failure(
                self._verdict(), self.invariant_ids, identity
            ),
        )
        self.assertEqual(
            "retryable_format",
            review_record.classify_retryable_format_failure(
                self._verdict(include_result=False), self.invariant_ids, identity
            ),
        )
        self.assertEqual(
            "semantic_finding",
            review_record.classify_retryable_format_failure(
                self._verdict(
                    result="findings",
                    route="IMPLEMENT_DEFECT",
                    failing_invariant="INV-RT-007",
                ),
                self.invariant_ids,
                identity,
            ),
        )
        self.assertEqual(
            "non_retryable",
            review_record.classify_retryable_format_failure(
                self._verdict(result="blocked", route="PROCESS_DEFECT"),
                self.invariant_ids,
                identity,
            ),
        )
        self.assertEqual(
            "non_retryable",
            review_record.classify_retryable_format_failure(
                self._verdict(include_evidence=False), self.invariant_ids, identity
            ),
        )
        self.assertEqual(
            "non_retryable",
            review_record.classify_retryable_format_failure(
                "provider failed", self.invariant_ids, identity
            ),
        )

    def test_append_replays_immutable_artifacts_and_domain_digest(self) -> None:
        identity = self._identity()
        metadata = self._metadata()
        semantic = self._verdict(include_result=False)
        serialized = self._verdict()
        first = review_record.append_format_retry_evidence(
            str(self.task), metadata, identity, 0, semantic, "retryable_format"
        )
        stream = (
            self.task
            / "review-records"
            / "implementation-review-format-retries.jsonl"
        )
        first_stream = stream.read_bytes()
        first_stat = stream.stat()
        retry_metadata = self._metadata("20260718090000-123-review-1-serialization-1")
        second = review_record.append_format_retry_evidence(
            str(self.task), retry_metadata, identity, 1, serialized, "valid"
        )

        events = review_record.load_format_retry_evidence(str(self.task))
        self.assertEqual([first, second], events)
        self.assertTrue(stream.read_bytes().startswith(first_stream))
        self.assertTrue(os.path.samestat(first_stat, stream.stat()))
        self.assertNotEqual(
            first["retry_identity_digest"],
            hashlib.sha256(
                json.dumps(identity, sort_keys=True).encode("utf-8")
            ).hexdigest(),
        )
        self.assertEqual(
            semantic,
            (self.task / first["artifact_path"]).read_text(encoding="utf-8"),
        )
        self.assertEqual(
            serialized,
            (self.task / second["artifact_path"]).read_text(encoding="utf-8"),
        )

    def test_stream_open_failure_leaves_no_final_artifact_and_can_retry(self) -> None:
        identity = self._identity()
        metadata = self._metadata()
        raw_output = self._verdict(include_result=False)
        records = self.task / "review-records"
        artifact = (
            records
            / "implementation-review-format-retries"
            / f"{metadata['run_id']}-semantic.txt"
        )
        real_open = review_record.os.open

        def fail_stream_pending_open(path, flags, mode=0o777):
            value = os.fspath(path)
            if (
                "implementation-review-format-retries.jsonl." in value
                and value.endswith(".tmp")
            ):
                raise OSError(errno.ENOSPC, "injected stream open failure")
            return real_open(path, flags, mode)

        with mock.patch.object(
            review_record.os,
            "open",
            side_effect=fail_stream_pending_open,
        ):
            with self.assertRaises(review_record.ReviewRecordError):
                review_record.append_format_retry_evidence(
                    str(self.task),
                    metadata,
                    identity,
                    0,
                    raw_output,
                    "retryable_format",
                )

        self.assertFalse(artifact.exists())
        self.assertEqual([], review_record.load_format_retry_evidence(str(self.task)))
        event = review_record.append_format_retry_evidence(
            str(self.task),
            metadata,
            identity,
            0,
            raw_output,
            "retryable_format",
        )
        self.assertEqual([event], review_record.load_format_retry_evidence(str(self.task)))

    def test_partial_writes_complete_one_exact_event_and_artifact(self) -> None:
        identity = self._identity()
        metadata = self._metadata()
        raw_output = self._verdict(include_result=False)
        real_write = review_record.os.write
        partial_write_count = 0

        def partial_write(fd, data):
            nonlocal partial_write_count
            if b'"owner_identity"' in data:
                return real_write(fd, data)
            if len(data) > 1:
                partial_write_count += 1
                data = data[: max(1, len(data) // 2)]
            return real_write(fd, data)

        with mock.patch.object(review_record.os, "write", side_effect=partial_write):
            event = review_record.append_format_retry_evidence(
                str(self.task),
                metadata,
                identity,
                0,
                raw_output,
                "retryable_format",
            )

        stream = (
            self.task
            / "review-records"
            / "implementation-review-format-retries.jsonl"
        )
        self.assertGreater(partial_write_count, 1)
        self.assertEqual(1, len(stream.read_text(encoding="utf-8").splitlines()))
        self.assertEqual([event], review_record.load_format_retry_evidence(str(self.task)))
        self.assertEqual(
            raw_output,
            (self.task / event["artifact_path"]).read_text(encoding="utf-8"),
        )

    def test_stream_fsync_failure_is_retryable_without_orphan_final(self) -> None:
        identity = self._identity()
        metadata = self._metadata()
        raw_output = self._verdict(include_result=False)
        records = self.task / "review-records"
        artifact = (
            records
            / "implementation-review-format-retries"
            / f"{metadata['run_id']}-semantic.txt"
        )
        real_fsync = review_record._fsync_retry_file

        def fail_stream_fsync(fd, label):
            if label == "format retry event pending":
                raise review_record.ReviewRecordError("injected stream fsync failure")
            return real_fsync(fd, label)

        with mock.patch.object(
            review_record,
            "_fsync_retry_file",
            side_effect=fail_stream_fsync,
        ):
            with self.assertRaises(review_record.ReviewRecordError):
                review_record.append_format_retry_evidence(
                    str(self.task),
                    metadata,
                    identity,
                    0,
                    raw_output,
                    "retryable_format",
                )

        self.assertFalse(artifact.exists())
        self.assertEqual([], review_record.load_format_retry_evidence(str(self.task)))
        self.assertEqual([], list(records.glob("*.tmp")))
        event = review_record.append_format_retry_evidence(
            str(self.task),
            metadata,
            identity,
            0,
            raw_output,
            "retryable_format",
        )
        self.assertEqual([event], review_record.load_format_retry_evidence(str(self.task)))

    def test_replay_recovers_stream_commit_before_artifact_promotion(self) -> None:
        identity = self._identity()
        metadata = dict(self._metadata())
        metadata.pop("timestamp")
        raw_output = self._verdict(include_result=False)
        records = self.task / "review-records"
        artifact = (
            records
            / "implementation-review-format-retries"
            / f"{metadata['run_id']}-semantic.txt"
        )
        pending_artifact = Path(str(artifact) + ".pending")

        with mock.patch.object(
            review_record,
            "_recover_pending_retry_artifact",
            side_effect=review_record.ReviewRecordError("injected promotion crash"),
        ):
            with self.assertRaises(review_record.ReviewRecordError):
                review_record.append_format_retry_evidence(
                    str(self.task),
                    metadata,
                    identity,
                    0,
                    raw_output,
                    "retryable_format",
                )

        self.assertFalse(artifact.exists())
        self.assertTrue(pending_artifact.is_file())
        events = review_record.load_format_retry_evidence(str(self.task))
        self.assertEqual(1, len(events))
        self.assertTrue(artifact.is_file())
        self.assertFalse(pending_artifact.exists())
        self.assertEqual(
            events[0],
            review_record.append_format_retry_evidence(
                str(self.task),
                metadata,
                identity,
                0,
                raw_output,
                "retryable_format",
            ),
        )

    def test_replay_completes_interrupted_append_tail(self) -> None:
        identity = self._identity()
        metadata = self._metadata()
        raw_output = self._verdict(include_result=False)

        def append_prefix_then_crash(stream_path, encoded):
            fd = os.open(stream_path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
            try:
                os.write(fd, encoded[: len(encoded) // 2])
                os.fsync(fd)
            finally:
                os.close(fd)
            raise review_record.ReviewRecordError("injected append crash")

        with mock.patch.object(
            review_record,
            "_append_retry_event_bytes",
            side_effect=append_prefix_then_crash,
        ):
            with self.assertRaises(review_record.ReviewRecordError):
                review_record.append_format_retry_evidence(
                    str(self.task),
                    metadata,
                    identity,
                    0,
                    raw_output,
                    "retryable_format",
                )

        events = review_record.load_format_retry_evidence(str(self.task))
        self.assertEqual(1, len(events))
        self.assertEqual(
            raw_output,
            (self.task / events[0]["artifact_path"]).read_text(encoding="utf-8"),
        )

    def test_append_lock_recovers_after_owner_hard_exit(self) -> None:
        script = (
            "import os,sys;"
            f"sys.path.insert(0,{str(VERIFY_DIR)!r});"
            "import guru_review_record as record;"
            f"lock=record._FormatRetryAppendLock({str(self.task)!r});"
            "lock.__enter__();"
            "os._exit(0)"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=VERIFY_DIR,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)

        event = review_record.append_format_retry_evidence(
            str(self.task),
            self._metadata(),
            self._identity(),
            0,
            "semantic",
            "retryable_format",
        )
        self.assertEqual([event], review_record.load_format_retry_evidence(str(self.task)))

    def test_append_lock_rejects_symlink_without_touching_target(self) -> None:
        records = self.task / "review-records"
        records.mkdir()
        outside = self.task.parent / "outside-lock.txt"
        outside.write_text("KEEP", encoding="utf-8")
        try:
            os.symlink(
                outside,
                records / ".implementation-review-format-retries.lock",
            )
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable")

        with self.assertRaises(review_record.ReviewRecordError):
            review_record.append_format_retry_evidence(
                str(self.task),
                self._metadata(),
                self._identity(),
                0,
                "semantic",
                "retryable_format",
            )
        self.assertEqual("KEEP", outside.read_text(encoding="utf-8"))

    def test_directory_fsync_unsupported_still_replays_two_events(self) -> None:
        identity = self._identity()
        real_open = review_record.os.open

        def reject_directory_open(path, flags, mode=0o777):
            if os.path.isdir(os.fspath(path)):
                raise AssertionError("directory open must be skipped")
            return real_open(path, flags, mode)

        with (
            mock.patch.object(
                review_record,
                "_retry_directory_fsync_supported",
                return_value=False,
            ),
            mock.patch.object(
                review_record.os,
                "open",
                side_effect=reject_directory_open,
            ),
        ):
            first = review_record.append_format_retry_evidence(
                str(self.task),
                self._metadata(),
                identity,
                0,
                "semantic",
                "retryable_format",
            )
            second = review_record.append_format_retry_evidence(
                str(self.task),
                self._metadata("20260718090000-123-review-1-serialization-1"),
                identity,
                1,
                "serialized",
                "valid",
            )
            events = review_record.load_format_retry_evidence(str(self.task))

        self.assertEqual([first, second], events)

    def test_replay_does_not_replace_symlinked_final_artifact(self) -> None:
        identity = self._identity()
        metadata = self._metadata()
        raw_output = self._verdict(include_result=False)
        records = self.task / "review-records"
        artifact = (
            records
            / "implementation-review-format-retries"
            / f"{metadata['run_id']}-semantic.txt"
        )
        outside = self.task.parent / "outside-artifact.txt"
        outside.write_text("outside", encoding="utf-8")

        with mock.patch.object(
            review_record,
            "_recover_pending_retry_artifact",
            side_effect=review_record.ReviewRecordError("injected promotion crash"),
        ):
            with self.assertRaises(review_record.ReviewRecordError):
                review_record.append_format_retry_evidence(
                    str(self.task),
                    metadata,
                    identity,
                    0,
                    raw_output,
                    "retryable_format",
                )
        try:
            os.symlink(outside, artifact)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable")

        with self.assertRaises(review_record.ReviewRecordError):
            review_record.load_format_retry_evidence(str(self.task))
        self.assertTrue(artifact.is_symlink())
        self.assertEqual("outside", outside.read_text(encoding="utf-8"))

    def test_path_escape_overwrite_and_invalid_attempt_are_rejected(self) -> None:
        identity = self._identity()
        with self.assertRaises(review_record.ReviewRecordError):
            review_record.append_format_retry_evidence(
                str(self.task),
                self._metadata("../escape"),
                identity,
                0,
                "raw",
                "retryable_format",
            )
        for invalid_attempt in (2, True, [], {}):
            with self.assertRaises(review_record.ReviewRecordError):
                review_record.append_format_retry_evidence(
                    str(self.task),
                    self._metadata(),
                    identity,
                    invalid_attempt,
                    "raw",
                    "retryable_format",
                )
        with self.assertRaises(review_record.ReviewRecordError):
            review_record.append_format_retry_evidence(
                str(self.task),
                self._metadata(),
                identity,
                0,
                "raw",
                [],
            )

        artifact = (
            self.task
            / "review-records"
            / "implementation-review-format-retries"
            / f"{self._metadata()['run_id']}-semantic.txt"
        )
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("existing", encoding="utf-8")
        with self.assertRaises(review_record.ReviewRecordError):
            review_record.append_format_retry_evidence(
                str(self.task),
                self._metadata(),
                identity,
                0,
                "replacement",
                "retryable_format",
            )
        self.assertEqual("existing", artifact.read_text(encoding="utf-8"))

    def test_symlinked_evidence_root_cannot_escape_task(self) -> None:
        outside = self.task.parent / "outside"
        outside.mkdir()
        try:
            os.symlink(outside, self.task / "review-records")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable")
        with self.assertRaises(review_record.ReviewRecordError):
            review_record.append_format_retry_evidence(
                str(self.task),
                self._metadata(),
                self._identity(),
                0,
                "raw",
                "retryable_format",
            )
        self.assertEqual([], list(outside.iterdir()))

    def test_retry_identity_mismatch_and_second_retry_are_rejected(self) -> None:
        identity = self._identity()
        changed = self._identity(proof_bundle_digest=self._digest("changed"))
        first_metadata = self._metadata()
        review_record.append_format_retry_evidence(
            str(self.task), first_metadata, identity, 0, "semantic", "retryable_format"
        )
        with self.assertRaises(review_record.ReviewRecordError):
            review_record.append_format_retry_evidence(
                str(self.task), first_metadata, changed, 1, "retry", "valid"
            )
        review_record.append_format_retry_evidence(
            str(self.task),
            self._metadata("20260718090000-123-review-1-serialization-1"),
            identity,
            1,
            "retry",
            "valid",
        )

        second_metadata = self._metadata("20260718090100-124-review-1")
        review_record.append_format_retry_evidence(
            str(self.task), second_metadata, identity, 0, "semantic-2", "retryable_format"
        )
        with self.assertRaises(review_record.ReviewRecordError):
            review_record.append_format_retry_evidence(
                str(self.task), second_metadata, identity, 1, "retry-2", "valid"
            )

    def test_consumed_identity_survives_deleted_serialization_tail(self) -> None:
        identity = self._identity()
        first = review_record.append_format_retry_evidence(
            str(self.task),
            self._metadata("semantic-run"),
            identity,
            0,
            "semantic",
            "retryable_format",
        )
        second = review_record.append_format_retry_evidence(
            str(self.task),
            self._metadata("serialization-run-1"),
            identity,
            1,
            "serialized-1",
            "valid",
        )
        stream = (
            self.task
            / "review-records"
            / "implementation-review-format-retries.jsonl"
        )
        (self.task / second["artifact_path"]).unlink()
        stream.write_text(
            json.dumps(
                first,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            review_record.ReviewRecordError,
            "consumption marker history mismatch",
        ):
            review_record.append_format_retry_evidence(
                str(self.task),
                self._metadata("serialization-run-2"),
                identity,
                1,
                "serialized-2",
                "valid",
            )

    def test_replay_rejects_artifact_and_event_tampering(self) -> None:
        identity = self._identity()
        event = review_record.append_format_retry_evidence(
            str(self.task),
            self._metadata(),
            identity,
            0,
            "semantic",
            "retryable_format",
        )
        artifact = self.task / event["artifact_path"]
        artifact.write_text("tampered", encoding="utf-8")
        with self.assertRaises(review_record.ReviewRecordError):
            review_record.load_format_retry_evidence(str(self.task))

        artifact.write_text("semantic", encoding="utf-8")
        stream = (
            self.task
            / "review-records"
            / "implementation-review-format-retries.jsonl"
        )
        stored = json.loads(stream.read_text(encoding="utf-8"))
        stored["attempt"] = 2
        stream.write_text(json.dumps(stored) + "\n", encoding="utf-8")
        with self.assertRaises(review_record.ReviewRecordError):
            review_record.load_format_retry_evidence(str(self.task))

    def test_success_publishes_only_one_final_official_row(self) -> None:
        identity = self._identity()
        metadata = self._metadata()
        review_record.append_format_retry_evidence(
            str(self.task),
            metadata,
            identity,
            0,
            self._verdict(include_result=False),
            "retryable_format",
        )
        self.assertEqual([], self._official_rows())
        retry_output = self._verdict()
        review_record.append_format_retry_evidence(
            str(self.task), metadata, identity, 1, retry_output, "valid"
        )
        record = review_record.normalize_retry_verdict(
            retry_output,
            self._compact_proof_context(identity),
            identity,
            identity["proof_bundle_digest"],
        )
        review_record.append_record(str(self.task), record)

        rows = self._official_rows()
        self.assertEqual(1, len(rows))
        self.assertEqual("clean", rows[0]["review_result"])
        self.assertEqual("none", rows[0]["supervisor_failure"])

    def test_failed_retry_publishes_one_final_blocked_row(self) -> None:
        identity = self._identity()
        metadata = self._metadata()
        review_record.append_format_retry_evidence(
            str(self.task), metadata, identity, 0, "semantic", "retryable_format"
        )
        review_record.append_format_retry_evidence(
            str(self.task), metadata, identity, 1, "still malformed", "non_retryable"
        )
        record = review_record.normalize_retry_verdict(
            "still malformed",
            self._context(identity),
            identity,
            identity["proof_bundle_digest"],
        )
        review_record.append_record(str(self.task), record)

        rows = self._official_rows()
        self.assertEqual(1, len(rows))
        self.assertEqual("blocked", rows[0]["review_result"])
        self.assertEqual("MALFORMED_REVIEW_OUTPUT", rows[0]["supervisor_failure"])

    def test_normalization_rejects_snapshot_and_proof_drift(self) -> None:
        identity = self._identity()
        context = self._context(identity)
        context["reviewed_target_digest"] = self._digest("drift")
        with self.assertRaises(review_record.ReviewRecordError):
            review_record.normalize_retry_verdict(
                self._verdict(),
                context,
                identity,
                identity["proof_bundle_digest"],
            )
        with self.assertRaises(review_record.ReviewRecordError):
            review_record.normalize_retry_verdict(
                self._verdict(),
                self._context(identity),
                identity,
                self._digest("other-proof"),
            )
        compact = self._compact_proof_context(identity)
        compact["evidence_components"]["review_policy_digest"] = self._digest(
            "drift"
        )
        with self.assertRaises(review_record.ReviewRecordError):
            review_record.normalize_retry_verdict(
                self._verdict(),
                compact,
                identity,
                identity["proof_bundle_digest"],
            )

    def test_legacy_normalization_remains_unchanged(self) -> None:
        identity = self._identity()
        context = self._context(identity, schema_version=1)
        context["packet"] = self._packet(schema_version=1, risk="low")
        context["provider_override_source"] = "staged_packet"
        record, failure = review_record.normalize_review_record(
            review_record.parse_verdict_block(self._verdict()),
            context,
        )
        self.assertIsNone(failure)
        self.assertEqual("clean", record["review_result"])
        self.assertNotIn("invariant_verdicts", record)


if __name__ == "__main__":
    unittest.main()
