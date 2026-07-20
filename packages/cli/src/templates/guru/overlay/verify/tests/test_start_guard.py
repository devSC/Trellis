import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock

HOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "hooks"))


def load_hook_module(name):
    path = os.path.join(HOOKS_DIR, f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


guru_task = load_hook_module("guru_task")
guru_after_start = load_hook_module("guru_after_start")
import guru_delivery_policy
import guru_gate


class Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class StartGuardTests(unittest.TestCase):
    def write_inventory(self, task_dir, decision_items):
        for item in decision_items:
            item.setdefault("source_refs", [{
                "artifact_key": "start-guard.md",
                "anchor": f"GURU-DECISION:{item['decision_id']}",
            }])
        inventory = {
            "schema_version": 1,
            "task_id": "task-1",
            "scope": {
                "selected_slice_id": "delivery-control",
                "official_start_authority": "selected_slice_only",
                "later_slice_authority": "supervisor_fail_closed",
            },
            "slices": {"delivery-control": decision_items},
        }
        (task_dir / "implement.md").write_text(
            "# Plan\n\n"
            f"{guru_task.DECISION_INVENTORY_START}\n"
            "```json\n"
            f"{json.dumps(inventory, indent=2, sort_keys=True)}\n"
            "```\n"
            f"{guru_task.DECISION_INVENTORY_END}\n",
            encoding="utf-8",
        )

    def make_task(self, *, session=True, current_run=None, decisions=False, decision_status="unresolved"):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        task_dir = root / ".trellis" / "tasks" / "task-1"
        (root / ".git").mkdir()
        (root / ".trellis" / "scripts" / "guru").mkdir(parents=True)
        (root / ".trellis" / "scripts" / "task.py").write_text("# fake\n", encoding="utf-8")
        (root / ".trellis" / "scripts" / "guru" / "guru_gate.py").write_text("# fake\n", encoding="utf-8")
        common_dir = root / ".trellis" / "scripts" / "common"
        common_dir.mkdir(parents=True)
        active_task_sources = (
            parent / relative
            for parent in Path(__file__).resolve().parents
            for relative in (
                Path("trellis/scripts/common/active_task.py"),
                Path(".trellis/scripts/common/active_task.py"),
            )
        )
        active_task_source = next((path for path in active_task_sources if path.is_file()), None)
        self.assertIsNotNone(active_task_source, "active_task.py fixture source not found")
        shutil.copyfile(active_task_source, common_dir / "active_task.py")
        for name in ("slice-packets", "risk-packets", "execution-envelopes", "confirmation-attestations"):
            (task_dir / name).mkdir(parents=True, exist_ok=True)
        design_package = task_dir / "design-package"
        (design_package / "chapters").mkdir(parents=True)
        (design_package / "README.md").write_text("# Fixture design package\n", encoding="utf-8")
        (design_package / "design-main.md").write_text("# Fixture overview\n", encoding="utf-8")
        (design_package / "chapters" / "start-guard.md").write_text(
            "# Fixture detail\n\nGURU-DECISION:DEC-START-001\n",
            encoding="utf-8",
        )
        task = {
            "id": "task-1", "status": "planning", "guru_chain": "full", "require_req_uc": True,
            "design_package": ".trellis/tasks/task-1/design-package",
            "guru_gates": {
                "requirements": {"artifact_digest": "req"},
                "detail": {"artifact_digest": "e" * 64},
            },
        }
        self.write_json(task_dir / "task.json", task)
        self.write_json(task_dir / "gate-contract.json", {
            "schema_version": 1,
            "route": "full_chain",
            "risk": "high",
            "policy_version": "guru-risk-contract-v2",
            "risk_decision_inventory": {
                "schema_version": 1,
                "required": True,
                "source": "implement.md",
            },
        })
        packet = {
            "schema_version": 1,
            "slice_id": "delivery-control",
            "depends_on": [],
            "invariants": [{"invariant_id": "INV-START-001"}, {"invariant_id": "INV-START-002"}],
        }
        packet_path = task_dir / "slice-packets" / "delivery-control.json"
        self.write_json(packet_path, packet)
        gate_digest = guru_task._gate_digest(task, task_dir)
        packet_digest = guru_task._sha256_file(packet_path)
        decision_universe = []
        if decisions:
            decision = {
                "decision_id": "DEC-START-001", "required": True, "severity": "high", "status": decision_status,
                "irreversible": True, "recommendation": "guard", "alternatives": ["stop"],
                "impact": "unsafe", "invariant_ids": ["INV-START-001"],
            }
            if decision_status == "resolved":
                decision["resolution"] = {
                    "choice": "guard",
                    "evidence": "resolved in the confirmed detail contract",
                }
            decision_universe = [decision]
        self.write_inventory(task_dir, decision_universe)
        decision_items = [item for item in decision_universe if item["status"] == "unresolved"]
        risk = {
            "schema_version": 1, "task_id": "task-1", "slice_id": "delivery-control",
            "route": "full_chain", "risk": "high", "slice_packet_digest": packet_digest,
            "artifact_digest": gate_digest, "scope_fingerprint": "d" * 64,
            "detail_artifact_digest": "e" * 64,
            "policy_snapshot_digest": "c" * 64, "decision_items": decision_items,
            "decision_universe_digest": guru_task._digest(tuple(decision_universe)),
            "decision_set_digest": guru_task._digest(decision_items),
            "confirmation_required": True,
            "invariant_ids": ["INV-START-001", "INV-START-002"],
        }
        risk_path = task_dir / "risk-packets" / "delivery-control.json"
        self.write_json(risk_path, risk)
        risk_digest = guru_task._sha256_file(risk_path)
        attestation = {
            "schema_version": 1,
            "task_id": "task-1",
            "slice_id": "delivery-control",
            "risk_packet_digest": risk_digest,
            "scope_fingerprint": "d" * 64,
            "decision_set_digest": risk["decision_set_digest"],
            "decision_ids": sorted(item["decision_id"] for item in decision_items),
            "outcome": "confirmed",
            "confirmation_batch": 1,
            "provider": "codex",
            "user_quote": "confirmed",
        }
        attestation_path = task_dir / "confirmation-attestations" / "delivery-control.json"
        self.write_json(attestation_path, attestation)
        attestation_digest = guru_task._sha256_file(attestation_path)
        envelope = {
            "schema_version": 1, "task_id": "task-1", "slice_id": "delivery-control",
            "execution_route": "full_chain", "slice_packet_digest": packet_digest,
            "risk_packet_digest": risk_digest, "scope_fingerprint": "d" * 64,
            "policy_snapshot_digest": "c" * 64,
            "confirmation_required": True,
            "confirmation_attestation_digest": attestation_digest,
        }
        envelope_path = task_dir / "execution-envelopes" / "delivery-control.json"
        self.write_json(envelope_path, envelope)
        context_key = "ctx" if session else None
        active_task = "old-task" if session else None
        if session:
            session_path = root / ".trellis" / ".runtime" / "sessions" / "ctx.json"
            self.write_json(session_path, {"current_task": active_task, "current_run": current_run, "custom": "keep"})
        request = guru_task.StartRequest(
            task_dir=task_dir,
            selected_slice_id="delivery-control",
            official_task_py=root / ".trellis" / "scripts" / "task.py",
            expected_gate_digest=gate_digest,
            expected_slice_packet_digest=packet_digest,
            expected_risk_packet_digest=risk_digest,
            expected_envelope_digest=guru_task._sha256_file(envelope_path),
            expected_attestation_digest=attestation_digest,
            expected_context_key=context_key,
            expected_active_task=active_task,
        )
        return tmp, root, task_dir, request

    def write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def fake_run(
        self,
        root,
        task_dir,
        *,
        official_rc=0,
        call_hook=True,
        gate_fails=False,
        post_gate_fails=False,
        replace_lock=False,
    ):
        gate_calls = 0

        def run(cmd, **kwargs):
            nonlocal gate_calls
            if "guru_gate.py" in str(cmd[1]):
                gate_calls += 1
                if gate_fails:
                    return Result(2, "", "detail confirmation stale")
                if post_gate_fails and gate_calls >= 3:
                    return Result(2, "", "post gate failed")
                return Result(0, "START_READY\n", "")
            task_path = task_dir / "task.json"
            task = json.loads(task_path.read_text(encoding="utf-8"))
            task["status"] = "in_progress"
            self.write_json(task_path, task)
            env = kwargs["env"]
            sessions_dir = root / ".trellis" / ".runtime" / "sessions"
            session_files = list(sessions_dir.glob("*.json")) if sessions_dir.is_dir() else []
            if len(session_files) == 1 and any(
                env.get(key) for key in ("TRELLIS_CONTEXT_ID", "CODEX_THREAD_ID", "CODEX_SESSION_ID")
            ):
                session_path = session_files[0]
                session = json.loads(session_path.read_text(encoding="utf-8")) if session_path.is_file() else {}
                session["current_task"] = ".trellis/tasks/task-1"
                session.setdefault("current_run", None)
                self.write_json(session_path, session)
            if call_hook:
                old = os.environ.copy()
                try:
                    os.environ.clear()
                    os.environ.update(env)
                    os.environ["TASK_JSON_PATH"] = str(task_path)
                    guru_after_start.main()
                finally:
                    os.environ.clear()
                    os.environ.update(old)
            if replace_lock:
                (task_dir / ".guru-start.lock").write_text('{"token":"replacement-owner"}\n', encoding="utf-8")
            return Result(official_rc, "started\n", "boom" if official_rc else "")

        return run

    def run_guard(self, root, task_dir, request, run, env=None):
        if env is None:
            env = {"TRELLIS_CONTEXT_ID": request.expected_context_key} if request.expected_context_key else {}
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch.object(guru_task, "_repo_root", return_value=root), \
             mock.patch.object(guru_task.subprocess, "run", side_effect=run):
            return guru_task.start_with_guard(request)

    def test_v2_gate_digest_excludes_confirmation_records_and_binds_planning_state(self):
        tmp, _root, task_dir, _request = self.make_task()
        self.addCleanup(tmp.cleanup)
        task_path = task_dir / "task.json"
        task = json.loads(task_path.read_text(encoding="utf-8"))
        stable_digest = guru_task._gate_digest(task, task_dir)

        task["guru_gates"]["requirements"] = {
            "confirmed_by": "operator",
            "confirmed_at": "2026-07-16T12:00:00Z",
            "artifact_digest": "a" * 64,
            "confirmation_batch_digest": "b" * 64,
        }
        task["guru_gates"]["detail"] = {
            "confirmed_by": "operator",
            "confirmed_at": "2026-07-16T12:00:00Z",
            "artifact_digest": "e" * 64,
            "confirmation_batch_digest": "b" * 64,
        }
        self.write_json(task_path, task)
        self.assertEqual(guru_task._gate_digest(task, task_dir), stable_digest)

        task["guru_gates"]["review_runs"] = {
            "detail": [{"run_id": "review-1", "result": "clean"}],
        }
        self.write_json(task_path, task)
        review_digest = guru_task._gate_digest(task, task_dir)
        self.assertNotEqual(review_digest, stable_digest)

        contract_path = task_dir / "gate-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["contract_probe"] = "changed"
        self.write_json(contract_path, contract)
        self.assertNotEqual(guru_task._gate_digest(task, task_dir), review_digest)

    def test_v1_gate_digest_retains_legacy_confirmation_binding(self):
        tmp, _root, task_dir, _request = self.make_task()
        self.addCleanup(tmp.cleanup)
        contract_path = task_dir / "gate-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["policy_version"] = guru_task.guru_contract.POLICY_VERSION_V1
        self.write_json(contract_path, contract)
        task_path = task_dir / "task.json"
        task = json.loads(task_path.read_text(encoding="utf-8"))
        legacy_digest = guru_task._gate_digest(task, task_dir)

        task["guru_gates"]["requirements"] = {
            **task["guru_gates"]["requirements"],
            "confirmed_at": "2026-07-16T12:01:00Z",
        }
        self.write_json(task_path, task)
        self.assertNotEqual(guru_task._gate_digest(task, task_dir), legacy_digest)

    def test_v2_non_full_route_uses_legacy_confirmation_binding(self):
        tmp, _root, task_dir, _request = self.make_task()
        self.addCleanup(tmp.cleanup)
        contract_path = task_dir / "gate-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["route"] = guru_task.guru_contract.ROUTE_LITE_TASK
        self.write_json(contract_path, contract)
        task_path = task_dir / "task.json"
        task = json.loads(task_path.read_text(encoding="utf-8"))
        legacy_digest = guru_task._gate_digest(task, task_dir)
        task["guru_gates"]["detail"]["confirmed_at"] = "2026-07-16T12:02:00Z"
        self.write_json(task_path, task)
        self.assertNotEqual(guru_task._gate_digest(task, task_dir), legacy_digest)

    def test_full_v2_chronology_builds_risk_then_confirms_checks_and_binds(self):
        tmp, root, task_dir, _request = self.make_task(session=False)
        self.addCleanup(tmp.cleanup)
        previous_allow_abs = os.environ.get("GURU_GATE_ALLOW_ABS")
        os.environ["GURU_GATE_ALLOW_ABS"] = "1"

        def restore_allow_abs():
            if previous_allow_abs is None:
                os.environ.pop("GURU_GATE_ALLOW_ABS", None)
            else:
                os.environ["GURU_GATE_ALLOW_ABS"] = previous_allow_abs

        self.addCleanup(restore_allow_abs)
        task_path = task_dir / "task.json"
        task = json.loads(task_path.read_text(encoding="utf-8"))
        task["design_package"] = str(task_dir / "design-package")
        task["guru_gates"] = {"review_runs": {"overview": [], "detail": []}}
        self.write_json(task_path, task)
        for relative_path in (
            "risk-packets/delivery-control.json",
            "confirmation-attestations/delivery-control.json",
            "execution-envelopes/delivery-control.json",
        ):
            (task_dir / relative_path).unlink()
        (task_dir / "prd.md").write_text(
            "# Requirements\n\nChronological Full v2 fixture.\n",
            encoding="utf-8",
        )
        (task_dir / "design.md").write_text(
            "# Design\n\nChronological Full v2 fixture.\n",
            encoding="utf-8",
        )

        stable_before = guru_task._gate_digest(task, task_dir)
        self.assertNotIn("requirements", task["guru_gates"])
        self.assertNotIn("detail", task["guru_gates"])
        packet_path = task_dir / "slice-packets/delivery-control.json"
        packet_digest = guru_task._sha256_file(packet_path)
        detail_digest = guru_gate._gate_digest(str(task_dir), "detail")
        policy_data = guru_delivery_policy.load_policy()
        selection = guru_delivery_policy.resolve_delivery_selection(
            guru_delivery_policy.IntakeRequest(
                description="change workflow hook gate runtime",
                intent_hint="implementation",
                affected_paths=(PurePosixPath(".trellis/workflow.md"),),
                commit_requested=True,
            ),
            policy_data,
            capability_report=guru_delivery_policy.managed_capability_report(parallel=True),
        )
        risk = guru_delivery_policy.build_risk_packet(
            selection,
            (),
            stable_before,
            detail_artifact_digest=detail_digest,
            task_id="task-1",
            slice_id="delivery-control",
            slice_packet_digest=packet_digest,
            invariant_ids=("INV-START-001", "INV-START-002"),
        )
        risk_path = task_dir / "risk-packets/delivery-control.json"
        self.write_json(risk_path, risk)

        with mock.patch.object(guru_gate, "_turn_ref", return_value="turn-chronology"):
            self.assertEqual(
                guru_gate._record_full_confirmation_batch(
                    str(task_dir),
                    "agent",
                    user_quote="确认 Full 单批次",
                ),
                guru_gate.PASS,
            )
        confirmed_task = json.loads(task_path.read_text(encoding="utf-8"))
        self.assertEqual(
            guru_task._gate_digest(confirmed_task, task_dir),
            stable_before,
        )
        self.assertEqual(guru_gate._full_confirmation_batch_problem(str(task_dir)), "")
        with (
            mock.patch.object(guru_gate, "check_requirements", return_value=guru_gate.PASS),
            mock.patch.object(guru_gate, "check_overview", return_value=guru_gate.PASS),
            mock.patch.object(guru_gate, "check_detail", return_value=guru_gate.PASS),
            mock.patch.object(guru_gate, "_block_requirements_review", return_value=guru_gate.PASS),
            mock.patch.object(guru_gate, "_review_state", return_value={"ready": True}),
        ):
            self.assertEqual(guru_gate.cmd_check_start(str(task_dir)), guru_gate.PASS)

        risk_digest = guru_task._sha256_file(risk_path)
        attestation = {
            "schema_version": 1,
            "task_id": "task-1",
            "slice_id": "delivery-control",
            "risk_packet_digest": risk_digest,
            "scope_fingerprint": risk["scope_fingerprint"],
            "decision_set_digest": risk["decision_set_digest"],
            "decision_ids": [],
            "outcome": "confirmed",
            "confirmation_batch": 1,
            "provider": "codex",
            "user_quote": "确认 Full 单批次",
        }
        attestation_path = task_dir / "confirmation-attestations/delivery-control.json"
        self.write_json(attestation_path, attestation)
        attestation_digest = guru_task._sha256_file(attestation_path)
        envelope = guru_delivery_policy.build_execution_envelope(
            selection,
            task_id="task-1",
            slice_id="delivery-control",
            slice_packet_digest=packet_digest,
            risk_packet_digest=risk_digest,
            confirmation_attestation_digest=attestation_digest,
            confirmation_required=True,
        )
        envelope_path = task_dir / "execution-envelopes/delivery-control.json"
        self.write_json(envelope_path, envelope)
        request = guru_task.StartRequest(
            task_dir=task_dir,
            selected_slice_id="delivery-control",
            official_task_py=root / ".trellis/scripts/task.py",
            expected_gate_digest=stable_before,
            expected_slice_packet_digest=packet_digest,
            expected_risk_packet_digest=risk_digest,
            expected_envelope_digest=guru_task._sha256_file(envelope_path),
            expected_attestation_digest=attestation_digest,
        )
        binding = guru_task._artifact_binding(request, root)
        self.assertEqual(binding["gate_digest"], stable_before)
        self.assertEqual(binding["risk_packet_digest"], risk_digest)
        self.assertEqual(binding["attestation_digest"], attestation_digest)

    def test_guarded_start_requires_real_hook_and_exact_session_postcondition(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        rc = self.run_guard(root, task_dir, request, self.fake_run(root, task_dir))
        self.assertEqual(rc, 0)
        attempt = json.loads(next((task_dir / "start-attempts").glob("*.json")).read_text(encoding="utf-8"))
        self.assertEqual(attempt["state"], "verified")
        self.assertEqual(attempt["hook_outcome"]["status"], "observed")
        self.assertEqual(attempt["capability"], {
            "entry_scope": "guarded_entry",
            "guarded_lifecycle_bindings": "enforced",
            "guarded_structural_bindings": "enforced",
            "confirmation_identity_provenance": "not_claimed",
            "high_risk_confirmation_evidence": "digest_bound_single_batch",
            "unresolved_required_high_risk": "blocked_without_current_confirmation",
            "direct_official_bypass": "advisory",
        })
        session = json.loads((root / ".trellis/.runtime/sessions/ctx.json").read_text(encoding="utf-8"))
        self.assertEqual(session["current_task"], ".trellis/tasks/task-1")
        self.assertIsNone(session["current_run"])

    def test_no_session_start_is_supported_and_pointer_remains_absent(self):
        tmp, root, task_dir, request = self.make_task(session=False)
        self.addCleanup(tmp.cleanup)
        rc = self.run_guard(root, task_dir, request, self.fake_run(root, task_dir))
        self.assertEqual(rc, 0)
        self.assertFalse((root / ".trellis/.runtime/sessions").exists())

    def test_real_resolver_uses_codex_thread_id(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        old_path = root / ".trellis/.runtime/sessions/ctx.json"
        session = json.loads(old_path.read_text())
        old_path.unlink()
        resolved_key = "codex_019f-context-probe"
        self.write_json(root / ".trellis/.runtime/sessions" / f"{resolved_key}.json", session)
        request = guru_task.StartRequest(**{
            **request.__dict__, "expected_context_key": resolved_key,
        })
        rc = self.run_guard(
            root, task_dir, request, self.fake_run(root, task_dir),
            env={"CODEX_THREAD_ID": "019f-context-probe"},
        )
        self.assertEqual(rc, 0)

    def test_real_resolver_sanitizes_unsafe_explicit_override_and_fences_path(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        old_path = root / ".trellis/.runtime/sessions/ctx.json"
        session = json.loads(old_path.read_text())
        old_path.unlink()
        self.write_json(root / ".trellis/.runtime/sessions/escape-key.json", session)
        normalized = guru_task.StartRequest(**{**request.__dict__, "expected_context_key": "escape-key"})
        rc = self.run_guard(
            root, task_dir, normalized, self.fake_run(root, task_dir),
            env={"TRELLIS_CONTEXT_ID": "../escape-key"},
        )
        self.assertEqual(rc, 0)
        self.assertFalse((root / ".trellis/.runtime/escape-key.json").exists())

    def test_expected_context_key_must_match_official_normalization(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        mismatched = guru_task.StartRequest(**{**request.__dict__, "expected_context_key": "../escape-key"})
        rc = self.run_guard(
            root, task_dir, mismatched, self.fake_run(root, task_dir),
            env={"TRELLIS_CONTEXT_ID": "../escape-key"},
        )
        self.assertEqual(rc, 2)
        self.assertFalse((task_dir / "start-attempts").exists())

    def test_missing_stale_or_mismatched_bindings_never_call_official(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        bad = guru_task.StartRequest(**{**request.__dict__, "expected_risk_packet_digest": "0" * 64})
        run = mock.Mock(side_effect=self.fake_run(root, task_dir))
        rc = self.run_guard(root, task_dir, bad, run)
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads((task_dir / "task.json").read_text())["status"], "planning")
        self.assertFalse((task_dir / "start-attempts").exists())

    def test_selected_risk_attestation_and_envelope_drift_each_block_official_start(self):
        cases = (
            ("risk-packets/delivery-control.json", "risk"),
            ("confirmation-attestations/delivery-control.json", "attestation"),
            ("execution-envelopes/delivery-control.json", "envelope"),
        )
        for relative_path, drift_kind in cases:
            with self.subTest(drift_kind=drift_kind):
                tmp, root, task_dir, request = self.make_task()
                try:
                    artifact_path = task_dir / relative_path
                    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
                    artifact["drift_probe"] = drift_kind
                    self.write_json(artifact_path, artifact)
                    run = mock.Mock(side_effect=self.fake_run(root, task_dir))
                    rc = self.run_guard(root, task_dir, request, run)
                    self.assertEqual(rc, 2)
                    run.assert_not_called()
                    self.assertFalse((task_dir / "start-attempts").exists())
                finally:
                    tmp.cleanup()

    def test_high_risk_start_without_current_confirmation_evidence_fails_closed(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        (task_dir / "confirmation-attestations" / "delivery-control.json").unlink()
        run = mock.Mock(side_effect=self.fake_run(root, task_dir))
        rc = self.run_guard(root, task_dir, request, run)
        self.assertEqual(rc, 2)
        run.assert_not_called()
        self.assertFalse((task_dir / "start-attempts").exists())

    def test_supervisor_current_run_conflict_blocks_before_attempt(self):
        tmp, root, task_dir, request = self.make_task(current_run="run-1")
        self.addCleanup(tmp.cleanup)
        rc = self.run_guard(root, task_dir, request, self.fake_run(root, task_dir))
        self.assertEqual(rc, 2)
        self.assertFalse((task_dir / "start-attempts").exists())

    def test_start_lock_conflict_blocks(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        self.write_json(task_dir / ".guru-start.lock", {"pid": 1})
        rc = self.run_guard(root, task_dir, request, self.fake_run(root, task_dir))
        self.assertEqual(rc, 2)
        self.assertFalse((task_dir / "start-attempts").exists())

    def test_post_lock_toctou_is_detected_without_official_call(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        original = guru_task._StartLock.__enter__

        def mutate(lock):
            result = original(lock)
            task = json.loads((task_dir / "task.json").read_text())
            task["status"] = "in_progress"
            self.write_json(task_dir / "task.json", task)
            return result

        run = mock.Mock(side_effect=self.fake_run(root, task_dir))
        with mock.patch.object(guru_task._StartLock, "__enter__", mutate):
            rc = self.run_guard(root, task_dir, request, run)
        self.assertEqual(rc, 2)
        self.assertFalse((task_dir / "start-attempts").exists())

    def test_hook_not_observed_compensates_exact_task_and_session_preimages(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        task_before = (task_dir / "task.json").read_bytes()
        session_path = root / ".trellis/.runtime/sessions/ctx.json"
        session_before = session_path.read_bytes()
        rc = self.run_guard(root, task_dir, request, self.fake_run(root, task_dir, call_hook=False))
        self.assertEqual(rc, 2)
        self.assertEqual((task_dir / "task.json").read_bytes(), task_before)
        self.assertEqual(session_path.read_bytes(), session_before)
        attempt = json.loads(next((task_dir / "start-attempts").glob("*.json")).read_text())
        self.assertEqual(attempt["state"], "compensated")

    def test_post_gate_failure_compensates_even_when_official_returns_zero(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        rc = self.run_guard(root, task_dir, request, self.fake_run(root, task_dir, post_gate_fails=True))
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads((task_dir / "task.json").read_text())["status"], "planning")

    def test_post_artifact_recheck_exception_always_compensates(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        task_before = (task_dir / "task.json").read_bytes()
        session_path = root / ".trellis/.runtime/sessions/ctx.json"
        session_before = session_path.read_bytes()
        original = guru_task._artifact_binding
        calls = 0

        def fail_after_official(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls >= 3:
                raise ValueError("forced post-artifact failure")
            return original(*args, **kwargs)

        with mock.patch.object(guru_task, "_artifact_binding", side_effect=fail_after_official):
            rc = self.run_guard(root, task_dir, request, self.fake_run(root, task_dir))
        self.assertEqual(rc, 2)
        self.assertEqual((task_dir / "task.json").read_bytes(), task_before)
        self.assertEqual(session_path.read_bytes(), session_before)
        attempt = json.loads(next((task_dir / "start-attempts").glob("*.json")).read_text())
        self.assertEqual(attempt["state"], "compensated")

    def test_replacement_lock_is_never_unlinked_and_forces_compensation(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        rc = self.run_guard(
            root, task_dir, request,
            self.fake_run(root, task_dir, replace_lock=True),
        )
        self.assertEqual(rc, 2)
        lock_path = task_dir / ".guru-start.lock"
        self.assertTrue(lock_path.is_file())
        self.assertIn("replacement-owner", lock_path.read_text())
        self.assertEqual(json.loads((task_dir / "task.json").read_text())["status"], "planning")

    def test_self_asserted_human_attestation_is_not_trusted(self):
        tmp, root, task_dir, request = self.make_task(decisions=True)
        self.addCleanup(tmp.cleanup)
        task_path = task_dir / "task.json"
        task = json.loads(task_path.read_text())
        task["guru_gates"]["risk_confirmation"] = {
            "via": "guru_gate", "mode": "strict_tty", "confirmed_by": "operator",
            "confirmed_at": "2026-07-14T00:00:00Z",
            "risk_packet_digest": request.expected_risk_packet_digest,
            "scope_fingerprint": "d" * 64, "decision_ids": ["DEC-START-001"],
            "detail_artifact_digest": "e" * 64,
        }
        self.write_json(task_path, task)
        attestation_path = task_dir / "confirmation-attestations/delivery-control.json"
        attestation = {
            "schema_version": 1, "task_id": "task-1", "slice_id": "delivery-control",
            "risk_packet_digest": request.expected_risk_packet_digest,
            "gate_digest": request.expected_gate_digest,
            "scope_fingerprint": "d" * 64, "decision_ids": ["DEC-START-001"],
            "confirmation_record_digest": guru_task._digest(task["guru_gates"]["risk_confirmation"]),
            "trust_source": {
                "kind": "platform_user_confirmation", "actor_type": "human", "context_id": "self-asserted",
            },
        }
        self.write_json(attestation_path, attestation)
        attestation_digest = guru_task._sha256_file(attestation_path)
        envelope_path = task_dir / "execution-envelopes/delivery-control.json"
        envelope = json.loads(envelope_path.read_text())
        envelope["confirmation_attestation_digest"] = attestation_digest
        self.write_json(envelope_path, envelope)
        request = guru_task.StartRequest(**{
            **request.__dict__,
            "expected_attestation_digest": attestation_digest,
            "expected_envelope_digest": guru_task._sha256_file(envelope_path),
        })
        run = mock.Mock(side_effect=self.fake_run(root, task_dir))
        rc = self.run_guard(root, task_dir, request, run)
        self.assertEqual(rc, 2)
        run.assert_not_called()
        self.assertFalse((task_dir / "start-attempts").exists())

    def test_resolved_status_forgery_cannot_empty_a_bound_blocking_packet(self):
        tmp, root, task_dir, request = self.make_task(decisions=True)
        self.addCleanup(tmp.cleanup)
        risk_path = task_dir / "risk-packets/delivery-control.json"
        risk = json.loads(risk_path.read_text())
        risk["decision_items"][0]["status"] = "resolved"
        risk["decision_set_digest"] = guru_task._digest(risk["decision_items"])
        risk["confirmation_required"] = False
        self.write_json(risk_path, risk)
        risk_digest = guru_task._sha256_file(risk_path)
        envelope_path = task_dir / "execution-envelopes/delivery-control.json"
        envelope = json.loads(envelope_path.read_text())
        envelope["risk_packet_digest"] = risk_digest
        self.write_json(envelope_path, envelope)
        request = guru_task.StartRequest(**{
            **request.__dict__,
            "expected_risk_packet_digest": risk_digest,
            "expected_envelope_digest": guru_task._sha256_file(envelope_path),
        })
        run = mock.Mock(side_effect=self.fake_run(root, task_dir))
        rc = self.run_guard(root, task_dir, request, run)
        self.assertEqual(rc, 2)
        run.assert_not_called()
        self.assertFalse((task_dir / "start-attempts").exists())

    def test_deleting_decision_and_rehashing_every_mutable_binding_still_blocks(self):
        tmp, root, task_dir, request = self.make_task(decisions=True)
        self.addCleanup(tmp.cleanup)
        risk_path = task_dir / "risk-packets/delivery-control.json"
        risk = json.loads(risk_path.read_text())
        risk["decision_items"] = []
        risk["decision_set_digest"] = guru_task._digest([])
        risk["confirmation_required"] = False
        self.write_json(risk_path, risk)
        risk_digest = guru_task._sha256_file(risk_path)
        envelope_path = task_dir / "execution-envelopes/delivery-control.json"
        envelope = json.loads(envelope_path.read_text())
        envelope["risk_packet_digest"] = risk_digest
        self.write_json(envelope_path, envelope)
        request = guru_task.StartRequest(**{
            **request.__dict__,
            "expected_risk_packet_digest": risk_digest,
            "expected_envelope_digest": guru_task._sha256_file(envelope_path),
        })
        run = mock.Mock(side_effect=self.fake_run(root, task_dir))
        rc = self.run_guard(root, task_dir, request, run)
        self.assertEqual(rc, 2)
        run.assert_not_called()
        self.assertFalse((task_dir / "start-attempts").exists())

    def test_explicit_resolved_inventory_in_confirmed_detail_can_start(self):
        tmp, root, task_dir, request = self.make_task(decisions=True, decision_status="resolved")
        self.addCleanup(tmp.cleanup)
        rc = self.run_guard(root, task_dir, request, self.fake_run(root, task_dir))
        self.assertEqual(rc, 0)
        attempt = json.loads(next((task_dir / "start-attempts").glob("*.json")).read_text())
        self.assertEqual(attempt["state"], "verified")

    def test_missing_confirmed_detail_inventory_fails_before_any_subprocess(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        (task_dir / "implement.md").unlink()
        run = mock.Mock(side_effect=self.fake_run(root, task_dir))
        rc = self.run_guard(root, task_dir, request, run)
        self.assertEqual(rc, 2)
        run.assert_not_called()
        self.assertFalse((task_dir / "start-attempts").exists())

    def test_rewriting_inventory_and_packet_cannot_bypass_stale_detail_gate(self):
        tmp, root, task_dir, request = self.make_task(decisions=True)
        self.addCleanup(tmp.cleanup)
        self.write_inventory(task_dir, [])
        risk_path = task_dir / "risk-packets/delivery-control.json"
        risk = json.loads(risk_path.read_text())
        risk["decision_universe_digest"] = guru_task._digest(())
        risk["decision_items"] = []
        risk["decision_set_digest"] = guru_task._digest([])
        risk["confirmation_required"] = False
        self.write_json(risk_path, risk)
        risk_digest = guru_task._sha256_file(risk_path)
        envelope_path = task_dir / "execution-envelopes/delivery-control.json"
        envelope = json.loads(envelope_path.read_text())
        envelope["risk_packet_digest"] = risk_digest
        self.write_json(envelope_path, envelope)
        request = guru_task.StartRequest(**{
            **request.__dict__,
            "expected_risk_packet_digest": risk_digest,
            "expected_envelope_digest": guru_task._sha256_file(envelope_path),
        })
        run = mock.Mock(side_effect=self.fake_run(root, task_dir, gate_fails=True))
        rc = self.run_guard(root, task_dir, request, run)
        self.assertEqual(rc, 2)
        run.assert_not_called()
        self.assertFalse((task_dir / "start-attempts").exists())

    def test_compensation_conflict_preserves_observed_state(self):
        tmp, root, task_dir, request = self.make_task()
        self.addCleanup(tmp.cleanup)
        with mock.patch.dict(os.environ, {"TRELLIS_CONTEXT_ID": "ctx"}, clear=True):
            binding = guru_task._artifact_binding(request, root)
            pre = guru_task._snapshot(request, root, binding)
            attempt_id, attempt_path, _identity = guru_task._prepare_attempt(request, root, pre)
        task = json.loads((task_dir / "task.json").read_text())
        task["status"] = "in_progress"
        self.write_json(task_dir / "task.json", task)
        with mock.patch.dict(os.environ, {"TRELLIS_CONTEXT_ID": "ctx"}, clear=True):
            observed = guru_task._snapshot(request, root, binding)
        guru_task._mark_attempt(attempt_path, "official_returned", {"official_post_snapshot": observed})
        task["external"] = True
        self.write_json(task_dir / "task.json", task)
        result = guru_task.compensate_after_start(attempt_id, task_dir)
        self.assertFalse(result["ok"])
        self.assertTrue(json.loads((task_dir / "task.json").read_text())["external"])
        self.assertEqual(json.loads(attempt_path.read_text())["state"], "manual_recovery_required")

    def test_direct_official_bypass_is_advisory_and_never_restores(self):
        tmp, root, task_dir, _request = self.make_task()
        self.addCleanup(tmp.cleanup)
        task = json.loads((task_dir / "task.json").read_text())
        task["status"] = "in_progress"
        self.write_json(task_dir / "task.json", task)
        with mock.patch.dict(os.environ, {"TASK_JSON_PATH": str(task_dir / "task.json")}, clear=True):
            self.assertEqual(guru_after_start.main(), 0)
        row = json.loads((task_dir / "start-violations.jsonl").read_text().strip())
        self.assertEqual(row["capability"], "advisory")
        self.assertEqual(json.loads((task_dir / "task.json").read_text())["status"], "in_progress")


if __name__ == "__main__":
    unittest.main()
