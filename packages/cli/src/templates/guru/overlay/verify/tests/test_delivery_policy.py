import copy
import dataclasses
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock

VERIFY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if VERIFY_DIR not in sys.path:
    sys.path.insert(0, VERIFY_DIR)

import guru_contract
import guru_delivery_policy as policy
import guru_gate
import guru_supervise


class DeliveryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = policy.load_policy()

    def select(self, **kwargs):
        request = policy.IntakeRequest(**kwargs)
        return policy.resolve_delivery_selection(
            request,
            self.policy,
            capability_report=policy.managed_capability_report(parallel=True),
        )

    def make_lite_task(
        self,
        root: Path,
        *,
        status: str = "planning",
        brainstorm_required: bool = False,
    ) -> Path:
        task_dir = root / "07-15-lite-runtime"
        task_dir.mkdir()
        contract = guru_contract.default_contract(
            guru_contract.ROUTE_LITE_TASK,
            guru_contract.RISK_MEDIUM,
            created_by="test",
        )
        contract.update({
            "execution_policy": {
                "scope_fingerprint": "d" * 64,
                "selection_generation": 1,
                "brainstorm_required": brainstorm_required,
            },
            "commit_policy": {
                "require_in_progress": True,
                "require_clean_implementation_review": False,
                "allow_task_artifacts_only": False,
            },
        })
        contract["scope"]["allowed_paths"] = ["lib/ui/button.dart"]
        contract["scope"]["max_files"] = 1
        (task_dir / "prd.md").write_text("# Requirement\n\nAccepted local behavior.\n", encoding="utf-8")
        (task_dir / "implement.jsonl").write_text("", encoding="utf-8")
        (task_dir / "check.jsonl").write_text("", encoding="utf-8")
        (task_dir / "gate-contract.json").write_text(json.dumps(contract), encoding="utf-8")
        task_data = {"id": "lite-runtime", "status": status, "guru_chain": "light"}
        (task_dir / "task.json").write_text(json.dumps(task_data), encoding="utf-8")
        task_data["guru_gates"] = {
            "requirements": {
                "confirmed_by": "user",
                "artifact_digest": guru_gate.requirements_confirmation_digest(str(task_dir)),
            }
        }
        (task_dir / "task.json").write_text(json.dumps(task_data), encoding="utf-8")
        return task_dir

    def make_full_task(self, root: Path) -> Path:
        task_dir = root / "07-15-full-runtime"
        task_dir.mkdir()
        contract = guru_contract.default_contract(
            guru_contract.ROUTE_FULL_CHAIN,
            guru_contract.RISK_HIGH,
            created_by="test",
        )
        (task_dir / "gate-contract.json").write_text(json.dumps(contract), encoding="utf-8")
        (task_dir / "prd.md").write_text("# Requirements\n\nConfirmed behavior.\n", encoding="utf-8")
        (task_dir / "design.md").write_text("# Overview\n\n# Detail\n\nIrreversible decisions.\n", encoding="utf-8")
        (task_dir / "implement.md").write_text("# Plan\n\nImplementation and tests.\n", encoding="utf-8")
        (task_dir / "task.json").write_text(json.dumps({
            "id": "full-runtime",
            "status": "planning",
            "guru_chain": "light",
        }), encoding="utf-8")
        risk_dir = task_dir / "risk-packets"
        risk_dir.mkdir()
        (risk_dir / "delivery-control.json").write_text(
            json.dumps({"risk": "high", "decisions": ["D1"]}),
            encoding="utf-8",
        )
        return task_dir

    def test_low_copy_change_without_commit_enters_small_inline(self):
        selection = self.select(
            description="fix typo in button label text",
            affected_paths=(PurePosixPath("lib/ui/title.dart"),),
            commit_requested=False,
        )
        self.assertEqual(selection.execution_route, guru_contract.ROUTE_SMALL_INLINE)
        self.assertEqual(selection.first_value_metric, "first_code")
        self.assertEqual(selection.required_gate_ids, ("deterministic_final",))
        self.assertEqual(selection.topology, "host_inline")

    def test_low_mechanical_change_stays_small_when_commit_is_requested(self):
        without_commit = self.select(
            description="fix typo in button label text",
            affected_paths=(PurePosixPath("lib/ui/title.dart"),),
            commit_requested=False,
        )
        with_commit = self.select(
            description="fix typo in button label text",
            affected_paths=(PurePosixPath("lib/ui/title.dart"),),
            commit_requested=True,
        )
        self.assertEqual(without_commit.execution_route, guru_contract.ROUTE_SMALL_INLINE)
        self.assertEqual(with_commit.execution_route, guru_contract.ROUTE_SMALL_INLINE)
        self.assertEqual(with_commit.scope_fingerprint, without_commit.scope_fingerprint)

    def test_clear_local_reversible_focused_behavior_change_enters_micro(self):
        selection = self.select(
            description="change local button behavior",
            affected_paths=(PurePosixPath("lib/ui/button.dart"),),
            requirements_clear=True,
            coupling="local",
            reversible=True,
            verification_scope="focused",
            commit_requested=True,
        )
        self.assertEqual(selection.execution_route, guru_contract.ROUTE_MICRO_TASK)
        self.assertIn("gate_contract", selection.required_artifacts)
        self.assertEqual(selection.resolved_budget["confirmation_batches"], 0)
        self.assertEqual(selection.resolved_budget["live_workers"], 0)
        self.assertEqual(selection.resolved_budget["started_workers"], 0)
        self.assertEqual(selection.topology, "host_inline")
        self.assertEqual(selection.enforcement_mode, "advisory")
        self.assertIsNone(selection.capability_probe_digest)
        self.assertEqual(self.policy["topology_rules"]["micro_task"], ["host_inline"])

    def test_commit_without_concrete_low_risk_scope_routes_lite_not_micro(self):
        selection = self.select(description="fix typo", commit_requested=True)
        self.assertEqual(selection.execution_route, guru_contract.ROUTE_LITE_TASK)
        self.assertEqual(selection.required_gate_ids, ("requirements_confirmed", "deterministic_final"))

    def test_lite_requires_one_prewrite_requirements_confirmation_and_zero_workers(self):
        selection = self.select(
            description="change local button behavior",
            requirements_clear=False,
            commit_requested=True,
        )
        self.assertEqual(selection.execution_route, guru_contract.ROUTE_LITE_TASK)
        self.assertEqual(selection.required_gate_ids, ("requirements_confirmed", "deterministic_final"))
        self.assertEqual(selection.required_artifacts, (
            "task_json", "prd", "implement_context", "check_context", "gate_contract",
            "task_evidence", "scoped_diff", "deterministic_check",
        ))
        self.assertLessEqual(selection.resolved_budget["first_value_deadline_seconds"], 300)
        self.assertEqual(selection.resolved_budget["confirmation_batches"], 1)
        self.assertEqual(selection.resolved_budget["live_workers"], 0)
        self.assertEqual(selection.resolved_budget["started_workers"], 0)
        self.assertEqual(selection.topology, "host_inline")
        self.assertEqual(selection.enforcement_mode, "advisory")
        self.assertIsNone(selection.capability_probe_digest)
        self.assertEqual(selection.route_acceptance["metrics_enforcement"], "advisory")
        self.assertTrue(selection.route_acceptance["brainstorm_required"])

    def test_explicitly_ambiguous_text_requires_lite_brainstorm_across_risk_keywords(self):
        for description, paths in (
            ("fix unclear behavior", ()),
            ("fix unclear typo text", (PurePosixPath("lib/ui/title.dart"),)),
            ("修复需求不明确的行为", ()),
        ):
            with self.subTest(description=description):
                selection = self.select(description=description, affected_paths=paths)
                self.assertEqual(selection.execution_route, guru_contract.ROUTE_LITE_TASK)
                self.assertTrue(selection.route_acceptance["brainstorm_required"])
                self.assertEqual(selection.route_acceptance["confirmation_limit"], 1)
                self.assertEqual(selection.resolved_budget["started_workers"], 0)

        high = self.select(description="fix unclear workflow behavior")
        self.assertEqual(high.execution_route, guru_contract.ROUTE_FULL_CHAIN)
        self.assertEqual(high.risk, guru_contract.RISK_HIGH)

    def test_keyword_boundaries_and_mixed_risk_never_hide_behavior_changes_as_small(self):
        context_behavior = self.select(
            description="fix context behavior",
            affected_paths=(PurePosixPath("lib/ui/context.dart"),),
        )
        mixed = self.select(
            description="update text behavior contract",
            affected_paths=(PurePosixPath("lib/ui/title.dart"),),
        )
        self.assertEqual(context_behavior.execution_route, guru_contract.ROUTE_LITE_TASK)
        self.assertEqual(mixed.execution_route, guru_contract.ROUTE_LITE_TASK)
        self.assertFalse(context_behavior.brainstorm_required)

    def test_official_project_resolver_reuses_exact_cache_and_invalidates_target_drift(self):
        request = policy.IntakeRequest(
            description="change local button behavior",
            affected_paths=(PurePosixPath("lib/ui/button.dart"),),
        )
        with (
            tempfile.TemporaryDirectory() as tmp,
            mock.patch.object(
                policy.guru_review_record,
                "target_snapshot_digest",
                return_value="a" * 64,
            ),
            mock.patch.object(
                policy,
                "project_docs_code_test_digest",
                return_value="b" * 64,
            ),
        ):
            root = Path(tmp)
            cold = policy.resolve_project_delivery_selection(
                request,
                str(root),
                self.policy,
                capability_report=policy.managed_capability_report(),
            )
            self.assertFalse(cold.evidence_reused)
            cache_dir = root / ".trellis" / "tasks" / "prior"
            cache_dir.mkdir(parents=True)
            (cache_dir / "verification-evidence.jsonl").write_text(json.dumps({
                "kind": "delivery_evidence_cache",
                "outcome": "passed",
                "evidence_cache_key": cold.evidence_cache_key,
                "target_digest": "a" * 64,
                "docs_code_test_digest": "b" * 64,
            }) + "\n", encoding="utf-8")
            warm = policy.resolve_project_delivery_selection(
                request,
                str(root),
                self.policy,
                capability_report=policy.managed_capability_report(),
            )
            self.assertTrue(warm.evidence_reused)
            self.assertEqual(warm.planning_cost_ratio_percent, 70)

            with mock.patch.object(
                policy.guru_review_record,
                "target_snapshot_digest",
                return_value="c" * 64,
            ):
                drift = policy.resolve_project_delivery_selection(
                    request,
                    str(root),
                    self.policy,
                    capability_report=policy.managed_capability_report(),
                )
            self.assertFalse(drift.evidence_reused)
            self.assertEqual(drift.planning_cost_ratio_percent, 100)

    def test_writable_lite_envelope_requires_task_requirements_and_confirmation_bindings(self):
        selection = self.select(
            description="change local button behavior",
            requirements_clear=False,
        )
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "task_id"):
            policy.build_execution_envelope(selection)
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "requirements_digest"):
            policy.build_execution_envelope(selection, task_id="task-1")
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "confirmation attestation"):
            policy.build_execution_envelope(
                selection,
                task_id="task-1",
                requirements_digest="a" * 64,
            )
        envelope = policy.build_execution_envelope(
            selection,
            task_id="task-1",
            requirements_digest="a" * 64,
            confirmation_attestation_digest="b" * 64,
        )
        self.assertTrue(envelope["confirmation_required"])
        self.assertEqual(envelope["requirements_digest"], "a" * 64)
        self.assertEqual(envelope["confirmation_attestation_digest"], "b" * 64)

    def test_route_override_and_generation_transition_rules(self):
        heavier = self.select(
            description="fix typo in label",
            affected_paths=(PurePosixPath("lib/ui/title.dart"),),
            preferred_route="lite_task",
        )
        self.assertEqual(heavier.recommended_route, guru_contract.ROUTE_SMALL_INLINE)
        self.assertEqual(heavier.selected_route, guru_contract.ROUTE_LITE_TASK)
        self.assertEqual(heavier.selection_source, "user_override")

        eligible_prewrite = self.select(
            description="change local button behavior",
            affected_paths=(PurePosixPath("lib/ui/button.dart"),),
            requirements_clear=True,
            coupling="local",
            reversible=True,
            verification_scope="focused",
            prior_route="lite_task",
            prior_selection_generation=3,
            first_write_started=False,
        )
        self.assertEqual(eligible_prewrite.selected_route, guru_contract.ROUTE_MICRO_TASK)
        self.assertEqual(eligible_prewrite.selection_generation, 4)

        unchanged = self.select(
            description="change local button behavior",
            requirements_clear=False,
            prior_route="lite_task",
            prior_selection_generation=3,
        )
        self.assertEqual(unchanged.selected_route, guru_contract.ROUTE_LITE_TASK)
        self.assertEqual(unchanged.selection_generation, 3)

        with self.assertRaisesRegex(policy.DeliveryPolicyError, "RouteDowngradeUnproven"):
            self.select(
                description="change local button behavior",
                requirements_clear=False,
                preferred_route="micro_task",
            )

    def test_lite_start_requires_standard_task_and_current_confirmation_without_full_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = self.make_lite_task(Path(tmp))
            self.assertEqual(guru_gate._lite_standard_task_problems(str(task_dir)), [])
            with (
                mock.patch.object(guru_gate, "check_requirements", return_value=guru_gate.PASS),
                mock.patch.object(guru_gate, "check_overview", return_value=guru_gate.BLOCK) as overview,
                mock.patch.object(guru_gate, "check_detail", return_value=guru_gate.BLOCK) as detail,
            ):
                self.assertEqual(guru_gate.cmd_check_start(str(task_dir)), guru_gate.PASS)
            overview.assert_not_called()
            detail.assert_not_called()

            (task_dir / "check.jsonl").unlink()
            self.assertIn("check.jsonl", " ".join(guru_gate._lite_standard_task_problems(str(task_dir))))

    def test_lite_brainstorm_evidence_is_required_only_when_intake_marks_it_necessary(self):
        prd = """# Requirement

## P0 capabilities

### BHV-001 Update local behavior

Given a valid local state
When the bounded change is applied
Then the expected behavior is visible

## Failure path

Invalid input leaves state unchanged.

## Acceptance

The focused deterministic check passes.

## Open questions

None.
"""
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = self.make_lite_task(Path(tmp), brainstorm_required=False)
            (task_dir / "prd.md").write_text(prd, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(guru_gate.check_requirements(str(task_dir)), guru_gate.PASS)

            contract = json.loads((task_dir / "gate-contract.json").read_text(encoding="utf-8"))
            contract["execution_policy"]["brainstorm_required"] = True
            (task_dir / "gate-contract.json").write_text(json.dumps(contract), encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(guru_gate.check_requirements(str(task_dir)), guru_gate.BLOCK)
            self.assertIn("Brainstorm Evidence missing", stderr.getvalue())

    def test_lite_confirmation_stales_when_prd_route_risk_or_scope_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = self.make_lite_task(Path(tmp))
            task_data = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
            original = task_data["guru_gates"]["requirements"]["artifact_digest"]
            self.assertEqual(original, guru_gate.requirements_confirmation_digest(str(task_dir)))

            contract = json.loads((task_dir / "gate-contract.json").read_text(encoding="utf-8"))
            contract["execution_policy"]["scope_fingerprint"] = "e" * 64
            (task_dir / "gate-contract.json").write_text(json.dumps(contract), encoding="utf-8")
            self.assertNotEqual(original, guru_gate.requirements_confirmation_digest(str(task_dir)))

    def test_in_progress_lite_auto_skips_check_implementation_worker_and_full_packet_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = self.make_lite_task(Path(tmp), status="in_progress")
            with (
                mock.patch.object(guru_gate, "check_requirements", return_value=guru_gate.PASS),
                mock.patch.object(guru_gate, "cmd_check_implementation") as implementation_check,
                mock.patch.object(guru_gate, "_implementation_packet_preflight_problem") as packet_preflight,
            ):
                self.assertEqual(guru_gate.auto(str(task_dir)), guru_gate.PASS)
            implementation_check.assert_not_called()
            packet_preflight.assert_not_called()
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "RouteDowngradeAfterWrite"):
            self.select(
                description="change local button behavior",
                affected_paths=(PurePosixPath("lib/ui/button.dart"),),
                requirements_clear=True,
                coupling="local",
                reversible=True,
                verification_scope="focused",
                prior_route="lite_task",
                prior_selection_generation=3,
                first_write_started=True,
            )

    def test_intake_exposes_recommended_selected_and_user_override_routes(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = guru_gate.cmd_intake(None, {
                "description": "fix typo in label",
                "paths": ["lib/ui/title.dart"],
                "commit_requested": True,
                "preferred_route": "lite_task",
            })
        self.assertEqual(rc, guru_gate.PASS)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["recommended_route"], guru_contract.ROUTE_SMALL_INLINE)
        self.assertEqual(payload["selected_route"], guru_contract.ROUTE_LITE_TASK)
        self.assertEqual(payload["selection_source"], "user_override")
        self.assertEqual(payload["selection_generation"], 1)

    def test_reintake_loads_existing_route_generation_and_write_boundary(self):
        options = {
            "description": "change local button behavior",
            "paths": ["lib/ui/button.dart"],
            "requirements_clear": True,
            "coupling": "local",
            "reversible": True,
            "verification_scope": "focused",
        }
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = self.make_lite_task(Path(tmp), status="planning")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(guru_gate.cmd_intake(str(task_dir), options), guru_gate.PASS)
            payload = json.loads(output.getvalue())
            self.assertEqual(payload["selected_route"], guru_contract.ROUTE_MICRO_TASK)
            self.assertEqual(payload["selection_generation"], 2)

            task_data = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
            task_data["status"] = "in_progress"
            (task_dir / "task.json").write_text(json.dumps(task_data), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(guru_gate.cmd_intake(str(task_dir), options), guru_gate.BLOCK)
            payload = json.loads(output.getvalue())
            self.assertIn("RouteDowngradeAfterWrite", " ".join(payload["blocking_reasons"]))

            stale = {**options, "prior_route": "micro_task"}
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(guru_gate.cmd_intake(str(task_dir), stale), guru_gate.BLOCK)
            self.assertIn("conflicts with existing contract route", output.getvalue())

    def test_direct_small_commit_plan_does_not_upgrade_or_ask_again(self):
        with (
            mock.patch.object(guru_gate, "_repo_root", return_value="/repo"),
            mock.patch.object(
                guru_gate,
                "_git_staged_paths",
                return_value=(["lib/ui/title.dart"], ""),
            ),
            mock.patch.object(guru_gate, "resolve_task_dir", return_value=None),
            mock.patch.object(guru_gate.guru_risk, "has_cross_layer_or_storage", return_value=False),
        ):
            plan = guru_gate._commit_plan_payload(None)
        self.assertEqual(plan["route"], "direct_small_inline")
        self.assertTrue(plan["can_commit_now"])
        self.assertEqual(plan["blocking_reasons"], [])
        self.assertEqual(plan["required_user_confirmations"], [])

    def test_lite_commit_plan_uses_current_confirmation_and_scope_without_full_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = self.make_lite_task(Path(tmp), status="in_progress")
            with (
                mock.patch.object(guru_gate, "_repo_root", return_value="/repo"),
                mock.patch.object(
                    guru_gate,
                    "_git_staged_paths",
                    return_value=(["lib/ui/button.dart"], ""),
                ),
                mock.patch.object(guru_gate, "resolve_task_dir", return_value=str(task_dir)),
                mock.patch.object(guru_gate.guru_risk, "has_cross_layer_or_storage", return_value=False),
                mock.patch.object(guru_gate, "_captured_gate_problem") as captured_gate,
                mock.patch.object(guru_gate, "_implementation_review_coverage") as review_coverage,
            ):
                plan = guru_gate._commit_plan_payload(str(task_dir))
            captured_gate.assert_not_called()
            review_coverage.assert_not_called()
            self.assertFalse(plan["can_commit_now"])
            self.assertIn("verification evidence missing", " ".join(plan["blocking_reasons"]))
            self.assertEqual(plan["required_user_confirmations"], [])

            (task_dir / "verification-evidence.jsonl").write_text(json.dumps({
                "kind": "deterministic_final",
                "status": "passed",
                "selection_generation": 1,
                "scope_fingerprint": "d" * 64,
                "target_paths": ["lib/ui/button.dart"],
                "target_digest": "a" * 64,
                "docs_code_test_consistency": "passed",
                "spec_sync": "not_required",
            }) + "\n", encoding="utf-8")
            with (
                mock.patch.object(guru_gate, "_repo_root", return_value="/repo"),
                mock.patch.object(
                    guru_gate,
                    "_git_staged_paths",
                    return_value=(["lib/ui/button.dart"], ""),
                ),
                mock.patch.object(guru_gate, "resolve_task_dir", return_value=str(task_dir)),
                mock.patch.object(guru_gate.guru_risk, "has_cross_layer_or_storage", return_value=False),
                mock.patch.object(guru_gate, "_captured_gate_problem") as captured_gate,
                mock.patch.object(guru_gate, "_implementation_review_coverage") as review_coverage,
                mock.patch.object(
                    guru_gate.guru_review_record,
                    "target_snapshot_digest",
                    return_value="a" * 64,
                ),
            ):
                plan = guru_gate._commit_plan_payload(str(task_dir))
            captured_gate.assert_not_called()
            review_coverage.assert_not_called()
            self.assertTrue(plan["can_commit_now"])
            self.assertEqual(plan["blocking_reasons"], [])
            self.assertEqual(plan["required_user_confirmations"], [])
            self.assertEqual(plan["allowed_stage_paths"], ["lib/ui/button.dart"])
            self.assertEqual(plan["review_coverage"]["source"], "not-required-for-lite_task")
            self.assertEqual(plan["review_coverage"]["missing_review_commands"], [])

            with (
                mock.patch.object(guru_gate, "_repo_root", return_value="/repo"),
                mock.patch.object(
                    guru_gate,
                    "_git_staged_paths",
                    return_value=(["lib/ui/other.dart"], ""),
                ),
                mock.patch.object(guru_gate, "resolve_task_dir", return_value=str(task_dir)),
                mock.patch.object(guru_gate.guru_risk, "has_cross_layer_or_storage", return_value=False),
                mock.patch.object(guru_gate, "_captured_gate_problem") as captured_gate,
                mock.patch.object(guru_gate, "_implementation_review_coverage") as review_coverage,
            ):
                blocked = guru_gate._commit_plan_payload(str(task_dir))
            captured_gate.assert_not_called()
            review_coverage.assert_not_called()
            self.assertFalse(blocked["can_commit_now"])
            self.assertIn("outside gate contract scope", " ".join(blocked["blocking_reasons"]))

    def test_lite_commit_success_records_reusable_exact_evidence_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = self.make_lite_task(Path(tmp), status="in_progress")
            contract_path = task_dir / "gate-contract.json"
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["execution_policy"].update({
                "policy_version": self.policy["policy_version"],
                "intent": "implementation",
                "route": guru_contract.ROUTE_LITE_TASK,
            })
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            (task_dir / "verification-evidence.jsonl").write_text(json.dumps({
                "kind": "deterministic_final",
                "status": "passed",
                "selection_generation": 1,
                "scope_fingerprint": "d" * 64,
                "target_paths": ["lib/ui/button.dart"],
                "target_digest": "a" * 64,
                "docs_code_test_consistency": "passed",
                "spec_sync": "not_required",
            }) + "\n", encoding="utf-8")
            with (
                mock.patch.object(guru_gate, "resolve_task_dir", return_value=str(task_dir)),
                mock.patch.object(
                    guru_gate.guru_delivery_policy,
                    "project_docs_code_test_digest",
                    return_value="b" * 64,
                ),
            ):
                cache_key, error = guru_gate._record_lite_delivery_evidence_cache(
                    str(task_dir),
                    str(Path(tmp)),
                )
            self.assertEqual(error, "")
            self.assertRegex(cache_key, r"^[0-9a-f]{64}$")
            rows = [
                json.loads(line)
                for line in (task_dir / "verification-evidence.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(rows[-1]["kind"], "delivery_evidence_cache")
            self.assertEqual(rows[-1]["target_digest"], "a" * 64)
            self.assertEqual(rows[-1]["docs_code_test_digest"], "b" * 64)

    def test_full_commit_plan_still_requires_implementation_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = self.make_full_task(Path(tmp))
            task_data = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
            task_data["status"] = "in_progress"
            (task_dir / "task.json").write_text(json.dumps(task_data), encoding="utf-8")
            coverage = guru_gate._empty_review_coverage()
            with (
                mock.patch.object(guru_gate, "_repo_root", return_value="/repo"),
                mock.patch.object(
                    guru_gate,
                    "_git_staged_paths",
                    return_value=(["lib/ui/button.dart"], ""),
                ),
                mock.patch.object(guru_gate, "resolve_task_dir", return_value=str(task_dir)),
                mock.patch.object(guru_gate, "_captured_gate_problem", return_value=""),
                mock.patch.object(
                    guru_gate,
                    "_implementation_review_coverage",
                    return_value=(coverage, "implementation review record missing", True),
                ) as review_coverage,
            ):
                plan = guru_gate._commit_plan_payload(str(task_dir))
            review_coverage.assert_called_once()
            self.assertFalse(plan["can_commit_now"])
            self.assertIn("implementation review record missing", plan["blocking_reasons"])

    def test_auto_uses_lite_route_instead_of_full_planning_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = self.make_lite_task(Path(tmp))
            with (
                mock.patch.object(guru_gate, "check_requirements", return_value=guru_gate.PASS),
                mock.patch.object(guru_gate, "check_overview", return_value=guru_gate.BLOCK) as overview,
                mock.patch.object(guru_gate, "check_detail", return_value=guru_gate.BLOCK) as detail,
                mock.patch.object(guru_gate, "check_implement", return_value=guru_gate.BLOCK) as implement,
            ):
                self.assertEqual(guru_gate.auto(str(task_dir)), guru_gate.PASS)
            overview.assert_not_called()
            detail.assert_not_called()
            implement.assert_not_called()

    def test_lite_status_reports_one_confirmation_and_no_full_reviews(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = self.make_lite_task(Path(tmp))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(guru_gate.cmd_status(str(task_dir)), guru_gate.PASS)
            rendered = output.getvalue()
            self.assertIn("Brainstorm Evidence — not required", rendered)
            self.assertIn("Lite requirements confirmation", rendered)
            self.assertIn("Overview/Detail reviews — not required", rendered)
            self.assertNotIn("confirm detail", rendered)

    def test_gate_usage_is_route_aware_for_lite_and_full_confirmation_and_review(self):
        usage = guru_gate.__doc__ or ""
        self.assertIn("Lite 只确认 requirements 一次", usage)
        self.assertIn("Full v2 一次批量确认", usage)
        self.assertIn("Lite 不需要 Worker", usage)
        self.assertIn("Lite 校验标准任务/当前确认/in_progress/合同 scope", usage)
        self.assertNotIn("提交前置：check-implementation + staged scope + implementation review clean", usage)

    def test_full_v2_records_one_current_batch_for_requirements_risk_and_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = self.make_full_task(Path(tmp))
            with mock.patch.object(guru_gate, "_turn_ref", return_value="turn-1"):
                self.assertEqual(
                    guru_gate._record_full_confirmation_batch(
                        str(task_dir),
                        "agent",
                        user_quote="已确认",
                    ),
                    guru_gate.PASS,
                )
            task_data = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
            requirements = task_data["guru_gates"]["requirements"]
            detail = task_data["guru_gates"]["detail"]
            self.assertEqual(requirements["confirmation_batch_digest"], detail["confirmation_batch_digest"])
            self.assertEqual(requirements["confirmation_batch_id"], detail["confirmation_batch_id"])
            self.assertEqual(
                requirements["confirmation_projection_digest"],
                detail["confirmation_projection_digest"],
            )
            self.assertEqual(requirements["schema_version"], 2)
            self.assertEqual(requirements["mode"], "soft")
            self.assertEqual(requirements["via"], "agent")
            self.assertEqual(requirements["turn_ref"], "turn-1")
            self.assertEqual(requirements["user_quote"], "已确认")
            self.assertEqual(guru_gate._full_confirmation_batch_problem(str(task_dir)), "")
            with (
                mock.patch.object(guru_gate, "check_requirements", return_value=guru_gate.PASS),
                mock.patch.object(guru_gate, "check_overview", return_value=guru_gate.PASS),
                mock.patch.object(guru_gate, "check_detail", return_value=guru_gate.PASS),
                mock.patch.object(guru_gate, "_block_requirements_review", return_value=guru_gate.PASS),
                mock.patch.object(guru_gate, "_review_state", return_value={"ready": True}),
            ):
                self.assertEqual(guru_gate.cmd_check_start(str(task_dir)), guru_gate.PASS)

            risk_path = task_dir / "risk-packets" / "delivery-control.json"
            original_risk = risk_path.read_text(encoding="utf-8")
            risk_path.write_text(
                json.dumps({"risk": "high", "decisions": ["D1", "D2"]}),
                encoding="utf-8",
            )
            self.assertIn("stale", guru_gate._full_confirmation_batch_problem(str(task_dir)).lower())
            risk_path.write_text(original_risk, encoding="utf-8")
            added_risk = task_dir / "risk-packets" / "added.json"
            added_risk.write_text(json.dumps({"risk": "high"}), encoding="utf-8")
            self.assertIn("stale", guru_gate._full_confirmation_batch_problem(str(task_dir)).lower())
            added_risk.unlink()
            risk_path.unlink()
            self.assertIn(
                "at least one",
                guru_gate._full_confirmation_batch_problem(str(task_dir)).lower(),
            )
            risk_path.write_text(original_risk, encoding="utf-8")

            requirements_path = task_dir / "prd.md"
            original_requirements = requirements_path.read_text(encoding="utf-8")
            requirements_path.write_text(
                original_requirements + "\nChanged requirements.\n",
                encoding="utf-8",
            )
            self.assertIn("stale", guru_gate._full_confirmation_batch_problem(str(task_dir)).lower())
            requirements_path.write_text(original_requirements, encoding="utf-8")

            design_path = task_dir / "design.md"
            original_design = design_path.read_text(encoding="utf-8")
            design_path.write_text(
                original_design + "\nChanged design.\n",
                encoding="utf-8",
            )
            self.assertIn("stale", guru_gate._full_confirmation_batch_problem(str(task_dir)).lower())

    def test_full_v2_confirmation_projection_rejects_every_metadata_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = self.make_full_task(Path(tmp))
            task_path = task_dir / "task.json"
            with mock.patch.object(guru_gate, "_turn_ref", return_value="turn-1"):
                self.assertEqual(
                    guru_gate._record_full_confirmation_batch(
                        str(task_dir),
                        "agent",
                        user_quote="已确认",
                    ),
                    guru_gate.PASS,
                )
            baseline = json.loads(task_path.read_text(encoding="utf-8"))
            fields = (
                "schema_version",
                "confirmed_by",
                "confirmed_at",
                "confirmation_scope",
                "allowed_next_action",
                "prompt_summary",
                "confirmation_batch_id",
                "confirmation_batch_digest",
                "requirements_digest",
                "detail_artifact_digest",
                "risk_packet_set_digest",
                "mode",
                "via",
                "turn_ref",
                "user_quote",
                "confirmation_projection_digest",
            )
            for field in fields:
                with self.subTest(field=field):
                    mutated = copy.deepcopy(baseline)
                    value = mutated["guru_gates"]["requirements"][field]
                    mutated["guru_gates"]["requirements"][field] = (
                        value + "-mutated" if isinstance(value, str) else value + 1
                    )
                    task_path.write_text(json.dumps(mutated), encoding="utf-8")
                    self.assertNotEqual(
                        guru_gate._full_confirmation_batch_problem(str(task_dir)),
                        "",
                    )
            missing = copy.deepcopy(baseline)
            del missing["guru_gates"]["requirements"]["confirmation_projection_digest"]
            task_path.write_text(json.dumps(missing), encoding="utf-8")
            self.assertIn(
                "diverge",
                guru_gate._full_confirmation_batch_problem(str(task_dir)).lower(),
            )
            unknown = copy.deepcopy(baseline)
            unknown["guru_gates"]["requirements"]["unexpected"] = True
            unknown["guru_gates"]["detail"]["unexpected"] = True
            task_path.write_text(json.dumps(unknown), encoding="utf-8")
            self.assertIn(
                "unknown",
                guru_gate._full_confirmation_batch_problem(str(task_dir)).lower(),
            )

    def test_full_v2_projection_rejects_self_rehashed_invalid_constants_and_shapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = self.make_full_task(Path(tmp))
            task_path = task_dir / "task.json"
            with mock.patch.object(guru_gate, "_turn_ref", return_value="turn-1"):
                self.assertEqual(
                    guru_gate._record_full_confirmation_batch(
                        str(task_dir),
                        "agent",
                        user_quote="已确认",
                    ),
                    guru_gate.PASS,
                )
            baseline = json.loads(task_path.read_text(encoding="utf-8"))

            def assert_rehashed_blocked(mutator):
                mutated = copy.deepcopy(baseline)
                for gate in ("requirements", "detail"):
                    record = mutated["guru_gates"][gate]
                    mutator(record)
                    record["confirmation_projection_digest"] = (
                        guru_gate._full_confirmation_projection_digest(record)
                    )
                task_path.write_text(json.dumps(mutated), encoding="utf-8")
                self.assertNotEqual(
                    guru_gate._full_confirmation_batch_problem(str(task_dir)),
                    "",
                )

            for field in (
                "confirmation_scope",
                "allowed_next_action",
                "prompt_summary",
                "confirmation_batch_id",
                "confirmation_batch_digest",
                "requirements_digest",
                "detail_artifact_digest",
                "risk_packet_set_digest",
            ):
                with self.subTest(field=field):
                    assert_rehashed_blocked(
                        lambda record, field=field: record.__setitem__(
                            field,
                            record[field] + "-mutated",
                        )
                    )

            assert_rehashed_blocked(lambda record: record.pop("via"))
            assert_rehashed_blocked(lambda record: record.pop("mode"))

            def tty_with_quote(record):
                record.pop("mode")
                record.pop("via")

            assert_rehashed_blocked(tty_with_quote)
            assert_rehashed_blocked(
                lambda record: record.__setitem__("turn_ref", "")
            )

    def test_init_contract_persists_lite_selection_runtime_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = Path(tmp) / "07-15-init-lite"
            task_dir.mkdir()
            (task_dir / "task.json").write_text(
                json.dumps({"id": "init-lite", "status": "planning"}),
                encoding="utf-8",
            )
            self.assertEqual(guru_gate.cmd_init_contract(str(task_dir), {
                "route": "lite_task",
                "risk": "medium",
                "allowed_paths": ["lib/ui/button.dart"],
            }), guru_gate.PASS)
            contract = json.loads((task_dir / "gate-contract.json").read_text(encoding="utf-8"))
            execution = contract["execution_policy"]
            self.assertEqual(execution["recommended_route"], guru_contract.ROUTE_LITE_TASK)
            self.assertEqual(execution["selected_route"], guru_contract.ROUTE_LITE_TASK)
            self.assertEqual(execution["selection_generation"], 1)
            self.assertRegex(execution["scope_fingerprint"], r"^[0-9a-f]{64}$")
            self.assertFalse(contract["commit_policy"]["require_clean_implementation_review"])

    def test_high_risk_preference_cannot_downgrade(self):
        selection = self.select(
            description="change workflow hook gate runtime",
            preferred_route="lite_task",
            affected_paths=(PurePosixPath(".trellis/workflow.md"),),
            commit_requested=True,
        )
        self.assertEqual(selection.risk, guru_contract.RISK_HIGH)
        self.assertEqual(selection.execution_route, guru_contract.ROUTE_FULL_CHAIN)
        self.assertIn("high_or_unknown_high_signal_requires_full_chain", selection.promotion_reasons)
        self.assertIn("risk_packet", selection.required_gate_ids)

    def test_unknown_high_signal_promotes_full_even_if_risk_not_high(self):
        selection = policy.resolve_delivery_selection(
            policy.IntakeRequest(
                description="small change",
                affected_paths=(PurePosixPath("lib/ui/title.dart"),),
                preferred_route="micro_task",
                commit_requested=True,
            ),
            self.policy,
            evidence={"risk": "medium", "high_signals": ["unknown-high-signal"]},
            capability_report=policy.managed_capability_report(parallel=False),
        )
        self.assertEqual(selection.execution_route, guru_contract.ROUTE_FULL_CHAIN)
        self.assertEqual(selection.topology, "managed_single")

    def test_review_intent_is_read_only_and_budget_capped(self):
        selection = self.select(
            description="review current implementation only",
            intent_hint="review",
            read_only_requested=True,
            affected_paths=(PurePosixPath("lib/ui/title.dart"),),
        )
        self.assertEqual(selection.write_capability, "none")
        self.assertEqual(selection.first_value_metric, "first_verified_evidence")
        self.assertLessEqual(selection.resolved_budget["model_cycles"], self.policy["route_profiles"]["read_only_cap"]["model_cycles"])
        self.assertEqual(selection.required_gate_ids, ("evidence_package", "implementation_review"))
        self.assertNotIn("start_guard", selection.required_gate_ids)

    def test_full_review_uses_read_only_gates_and_never_start_guard(self):
        selection = self.select(
            description="review workflow hook gate runtime without edits",
            intent_hint="review",
            read_only_requested=True,
            affected_paths=(PurePosixPath(".trellis/workflow.md"),),
        )
        self.assertEqual(selection.execution_route, guru_contract.ROUTE_FULL_CHAIN)
        self.assertEqual(selection.write_capability, "none")
        self.assertEqual(selection.required_gate_ids, (
            "requirements_confirmed", "overview_review_clean", "detail_review_clean", "evidence_package",
        ))
        self.assertNotIn("start_guard", selection.required_gate_ids)

    def test_full_envelope_requires_packet_and_risk_digest(self):
        selection = self.select(
            description="change workflow hook gate runtime",
            affected_paths=(PurePosixPath(".trellis/workflow.md"),),
            commit_requested=True,
        )
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "EnvelopeFieldIllegal"):
            policy.build_execution_envelope(selection, task_id="task-1")
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "confirmation attestation"):
            policy.build_execution_envelope(
                selection,
                task_id="task-1",
                slice_id="delivery-control",
                slice_packet_digest="a" * 64,
                risk_packet_digest="b" * 64,
            )
        envelope = policy.build_execution_envelope(
            selection,
            task_id="task-1",
            slice_id="delivery-control",
            slice_packet_digest="a" * 64,
            risk_packet_digest="b" * 64,
            confirmation_attestation_digest="c" * 64,
            confirmation_required=True,
        )
        self.assertEqual(envelope["execution_route"], guru_contract.ROUTE_FULL_CHAIN)
        self.assertEqual(envelope["slice_id"], "delivery-control")
        self.assertIn("start_guard", envelope["required_gate_ids"])
        self.assertTrue(envelope["confirmation_required"])
        self.assertEqual(envelope["budget"]["confirmation_batches"], 1)

    def test_lower_route_rejects_full_only_envelope_fields(self):
        selection = self.select(
            description="change local button behavior",
            affected_paths=(PurePosixPath("lib/ui/button.dart"),),
            requirements_clear=True,
            coupling="local",
            reversible=True,
            verification_scope="focused",
            commit_requested=True,
        )
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "micro_task"):
            policy.build_execution_envelope(selection, slice_id="x")

    def test_policy_schema_rejects_missing_budget(self):
        broken = dataclasses.asdict(dataclasses.make_dataclass("Box", [("x", dict)])({}).x) if False else dict(self.policy)
        broken["route_profiles"] = dict(self.policy["route_profiles"])
        broken["route_profiles"]["lite_task"] = dict(broken["route_profiles"]["lite_task"])
        del broken["route_profiles"]["lite_task"]["tool_calls"]
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "missing budgets"):
            policy.validate_policy(broken)

    def test_policy_schema_rejects_worker_topology_for_zero_worker_routes(self):
        self.assertEqual(self.policy["topology_rules"]["micro_task"], ["host_inline"])
        self.assertEqual(self.policy["topology_rules"]["lite_task"], ["host_inline"])
        broken = json.loads(json.dumps(self.policy))
        broken["topology_rules"]["micro_task"].append("managed_single")
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "micro_task topology"):
            policy.validate_policy(broken)

    def test_risk_rules_use_difficulty_evidence_not_commit_intent(self):
        rules = self.policy["risk_rules"]
        self.assertNotIn("low_commit_route", rules)
        self.assertNotIn("low_no_commit_route", rules)
        self.assertEqual(rules["mechanical_change_route"], guru_contract.ROUTE_SMALL_INLINE)
        self.assertEqual(rules["bounded_local_change_route"], guru_contract.ROUTE_MICRO_TASK)
        broken = json.loads(json.dumps(self.policy))
        broken["risk_rules"] = {
            "low_commit_route": guru_contract.ROUTE_MICRO_TASK,
            "low_no_commit_route": guru_contract.ROUTE_SMALL_INLINE,
        }
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "commit intent"):
            policy.validate_policy(broken)

    def test_capability_never_overclaims_full_without_runner(self):
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "CapabilityUnavailable"):
            policy.resolve_delivery_selection(
                policy.IntakeRequest(
                    description="change workflow hook gate runtime",
                    affected_paths=(PurePosixPath(".trellis/workflow.md"),),
                    commit_requested=True,
                ),
                self.policy,
                capability_report={"managed_runner": False},
            )

    def test_loose_capability_booleans_do_not_claim_enforcement(self):
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "CapabilityUnavailable"):
            policy.resolve_delivery_selection(
                policy.IntakeRequest(
                    description="change workflow hook gate runtime",
                    affected_paths=(PurePosixPath(".trellis/workflow.md"),),
                ),
                self.policy,
                capability_report={"managed_runner": True, "managed_parallel": True, "hard_counters": True},
            )

    def test_scope_fence_rejects_parent_backslash_absolute_and_symlink(self):
        for value in ("../secret", "lib\\secret.dart", "/tmp/secret"):
            with self.subTest(value=value), self.assertRaisesRegex(policy.DeliveryPolicyError, "ScopeUnbounded"):
                self.select(description="fix typo", affected_paths=(value,), commit_requested=True)
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "symlink"):
            policy.resolve_delivery_selection(
                policy.IntakeRequest(description="fix typo", affected_paths=("lib/link",), commit_requested=True),
                self.policy,
                evidence={"symlink_paths": ["lib/link"]},
                capability_report=policy.managed_capability_report(),
            )

    def test_micro_scope_binds_positive_max_files(self):
        selection = self.select(
            description="change local button behavior",
            affected_paths=(PurePosixPath("lib/a.dart"), PurePosixPath("lib/b.dart")),
            requirements_clear=True,
            coupling="local",
            reversible=True,
            verification_scope="focused",
            commit_requested=True,
            max_files=2,
        )
        self.assertEqual(selection.scope_max_files, 2)
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "max_files"):
            self.select(
                description="change local button behavior",
                affected_paths=(PurePosixPath("lib/a.dart"), PurePosixPath("lib/b.dart")),
                requirements_clear=True,
                coupling="local",
                reversible=True,
                verification_scope="focused",
                commit_requested=True,
                max_files=1,
            )

    def test_contract_patch_carries_budget_and_generation_inputs(self):
        selection = self.select(
            description="change local button behavior",
            affected_paths=(PurePosixPath("lib/ui/button.dart"),),
            requirements_clear=True,
            coupling="local",
            reversible=True,
            verification_scope="focused",
            commit_requested=True,
        )
        patch = policy.selection_to_contract_patch(selection)
        self.assertEqual(patch["execution_policy"]["route"], guru_contract.ROUTE_MICRO_TASK)
        self.assertEqual(patch["execution_policy"]["budget"]["tool_calls"], 32)
        self.assertTrue(patch["execution_policy"]["scope_fingerprint"])
        self.assertEqual(patch["execution_policy"]["recommended_route"], guru_contract.ROUTE_MICRO_TASK)
        self.assertEqual(patch["execution_policy"]["selected_route"], guru_contract.ROUTE_MICRO_TASK)
        self.assertEqual(patch["execution_policy"]["selection_source"], "recommended")
        self.assertEqual(patch["execution_policy"]["selection_generation"], 1)

    def test_exact_digest_evidence_reuse_reduces_cost_and_drift_invalidates(self):
        request = policy.IntakeRequest(description="change local button behavior", commit_requested=True)
        current = {"target_digest": "a" * 64, "docs_code_test_digest": "b" * 64}
        first = policy.resolve_delivery_selection(
            request,
            self.policy,
            evidence=current,
            capability_report=policy.managed_capability_report(),
        )
        candidate = {
            "evidence_cache_key": first.evidence_cache_key,
            "target_digest": current["target_digest"],
            "docs_code_test_digest": current["docs_code_test_digest"],
            "outcome": "passed",
        }
        hit = policy.resolve_delivery_selection(
            request,
            self.policy,
            evidence={**current, "reuse_candidate": candidate},
            capability_report=policy.managed_capability_report(),
        )
        self.assertTrue(hit.evidence_reused)
        self.assertEqual(hit.planning_cost_ratio_percent, 70)
        self.assertLessEqual(hit.resolved_budget["model_cycles"], first.resolved_budget["model_cycles"] * 70 // 100)
        self.assertEqual(hit.required_gate_ids, first.required_gate_ids)
        miss = policy.resolve_delivery_selection(
            request,
            self.policy,
            evidence={**current, "target_digest": "c" * 64, "reuse_candidate": candidate},
            capability_report=policy.managed_capability_report(),
        )
        self.assertFalse(miss.evidence_reused)
        self.assertEqual(miss.planning_cost_ratio_percent, 100)

    def test_all_intents_have_bounded_first_value_terminal_and_write_contracts(self):
        cases = (
            ("implementation", "change local button behavior", "lib/ui/button.dart", True, False, "first_code", "scoped_repository"),
            ("review", "review current button implementation only", "lib/ui/button.dart", False, True, "first_verified_evidence", "none"),
            ("research", "research parser behavior only", "lib/parser.py", False, True, "first_verified_evidence", "none"),
            ("docs", "update local usage document", "docs/usage.md", True, False, "first_accepted_artifact", "scoped_repository"),
            ("config", "update local formatter config", "config/formatter.json", True, False, "first_code", "scoped_repository"),
            ("ops", "inspect local status output", "scripts/status.py", False, False, "first_verified_evidence", "task_artifacts"),
            ("debug", "fix parser bug", "lib/parser.py", True, False, "first_code", "scoped_repository"),
        )
        for intent, description, path, commit, read_only, first_metric, write_capability in cases:
            with self.subTest(intent=intent):
                selection = self.select(
                    description=description,
                    intent_hint=intent,
                    affected_paths=(PurePosixPath(path),),
                    commit_requested=commit,
                    read_only_requested=read_only,
                )
                self.assertEqual(selection.intent, intent)
                self.assertEqual(selection.first_value_metric, first_metric)
                self.assertEqual(selection.write_capability, write_capability)
                self.assertEqual(
                    selection.terminal_conditions,
                    ("first_value_deadline", "terminal_deadline", "budget_exceeded", "required_gate_failed"),
                )
                self.assertLessEqual(selection.resolved_budget["confirmation_batches"], 1)
                self.assertTrue(selection.route_acceptance["autonomous_close"])
                self.assertEqual(selection.route_acceptance["provider"], "codex")
                self.assertTrue(selection.route_acceptance["claude_forbidden"])

    def test_all_intents_compound_on_exact_evidence_and_invalidate_on_either_digest(self):
        cases = (
            ("implementation", "change local button behavior", "lib/ui/button.dart", True, False),
            ("review", "review current button implementation only", "lib/ui/button.dart", False, True),
            ("research", "research parser behavior only", "lib/parser.py", False, True),
            ("docs", "update local usage document", "docs/usage.md", True, False),
            ("config", "update local formatter config", "config/formatter.json", True, False),
            ("ops", "inspect local status output", "scripts/status.py", False, False),
            ("debug", "fix parser bug", "lib/parser.py", True, False),
        )
        current = {"target_digest": "a" * 64, "docs_code_test_digest": "b" * 64}
        cost_keys = tuple(self.policy["evidence_reuse"]["cost_budget_keys"])
        for intent, description, path, commit, read_only in cases:
            request = policy.IntakeRequest(
                description=description,
                intent_hint=intent,
                affected_paths=(PurePosixPath(path),),
                commit_requested=commit,
                read_only_requested=read_only,
            )
            with self.subTest(intent=intent, state="warm"):
                cold = policy.resolve_delivery_selection(
                    request,
                    self.policy,
                    evidence=current,
                    capability_report=policy.managed_capability_report(parallel=True),
                )
                candidate = {
                    "evidence_cache_key": cold.evidence_cache_key,
                    **current,
                    "outcome": "passed",
                }
                warm = policy.resolve_delivery_selection(
                    request,
                    self.policy,
                    evidence={**current, "reuse_candidate": candidate},
                    capability_report=policy.managed_capability_report(parallel=True),
                )
                self.assertTrue(warm.evidence_reused)
                self.assertLessEqual(warm.planning_cost_ratio_percent, 70)
                self.assertEqual(warm.required_gate_ids, cold.required_gate_ids)
                for key in cost_keys:
                    self.assertLessEqual(warm.resolved_budget[key], max(1, cold.resolved_budget[key] * 70 // 100))
            for drift_name, drift in (
                ("target", {"target_digest": "c" * 64}),
                ("consistency", {"docs_code_test_digest": "d" * 64}),
            ):
                with self.subTest(intent=intent, state=f"{drift_name}_drift"):
                    miss = policy.resolve_delivery_selection(
                        request,
                        self.policy,
                        evidence={**current, **drift, "reuse_candidate": candidate},
                        capability_report=policy.managed_capability_report(parallel=True),
                    )
                    self.assertFalse(miss.evidence_reused)
                    self.assertEqual(miss.planning_cost_ratio_percent, 100)

    def test_scope_expansion_promotes_before_next_write_and_confirmation_is_single_batch(self):
        lite = self.select(
            description="change local button behavior",
            intent_hint="implementation",
            affected_paths=(PurePosixPath("lib/ui/button.dart"),),
            requirements_clear=False,
            commit_requested=True,
        )
        expanded = self.select(
            description="change workflow hook gate runtime",
            intent_hint="implementation",
            affected_paths=(PurePosixPath("lib/ui/button.dart"), PurePosixPath(".trellis/workflow.md")),
            commit_requested=True,
        )
        self.assertEqual(lite.execution_route, guru_contract.ROUTE_LITE_TASK)
        self.assertEqual(lite.resolved_budget["confirmation_batches"], 1)
        self.assertEqual(expanded.execution_route, guru_contract.ROUTE_FULL_CHAIN)
        self.assertEqual(expanded.risk, guru_contract.RISK_HIGH)
        self.assertIn("risk_packet", expanded.required_gate_ids)
        self.assertIn("start_guard", expanded.required_gate_ids)
        self.assertEqual(expanded.resolved_budget["confirmation_batches"], 1)

        envelope_args = {
            "task_id": "task-1",
            "slice_id": "delivery-control",
            "slice_packet_digest": "a" * 64,
            "risk_packet_digest": "b" * 64,
            "confirmation_attestation_digest": "c" * 64,
            "confirmation_required": True,
        }
        first = policy.build_execution_envelope(expanded, **envelope_args)
        unchanged_retry = policy.build_execution_envelope(expanded, **envelope_args)
        self.assertEqual(unchanged_retry, first)
        self.assertEqual(first["confirmation_attestation_digest"], "c" * 64)
        self.assertEqual(first["budget"]["confirmation_batches"], 1)

    def test_risk_packet_binds_complete_detail_decision_universe(self):
        selection = self.select(
            description="change workflow hook gate runtime",
            affected_paths=(PurePosixPath(".trellis/workflow.md"),),
            commit_requested=True,
        )
        packet = policy.build_risk_packet(selection, (
            {
                "decision_id": "D1", "required": True, "severity": "high", "status": "unresolved",
                "irreversible": True, "recommendation": "keep Full", "alternatives": ["stop"],
                "impact": "unsafe start", "invariant_ids": ["INV-POLICY-001"],
            },
            {
                "decision_id": "D2", "required": True, "severity": "critical", "status": "resolved",
                "irreversible": False, "recommendation": "preserve rollback", "alternatives": ["stop"],
                "impact": "rollback safety", "invariant_ids": ["INV-POLICY-002"],
                "resolution": {"choice": "preserve rollback", "evidence": "confirmed detail contract"},
            },
        ), artifact_digest="a" * 64, detail_artifact_digest="c" * 64,
            task_id="task-1", slice_id="delivery-control",
            slice_packet_digest="b" * 64, invariant_ids=("INV-POLICY-001", "INV-POLICY-002"))
        self.assertEqual([d["decision_id"] for d in packet["decision_items"]], ["D1"])
        self.assertEqual(packet["detail_artifact_digest"], "c" * 64)
        self.assertEqual(
            packet["decision_universe_digest"],
            policy._digest(policy.canonical_decision_universe((
                {
                    "decision_id": "D1", "required": True, "severity": "high", "status": "unresolved",
                    "irreversible": True, "recommendation": "keep Full", "alternatives": ["stop"],
                    "impact": "unsafe start", "invariant_ids": ["INV-POLICY-001"],
                },
                {
                    "decision_id": "D2", "required": True, "severity": "critical", "status": "resolved",
                    "irreversible": False, "recommendation": "preserve rollback", "alternatives": ["stop"],
                    "impact": "rollback safety", "invariant_ids": ["INV-POLICY-002"],
                    "resolution": {"choice": "preserve rollback", "evidence": "confirmed detail contract"},
                },
            ), ("INV-POLICY-001", "INV-POLICY-002"))),
        )
        self.assertEqual(packet["invariant_ids"], ["INV-POLICY-001", "INV-POLICY-002"])
        self.assertTrue(packet["confirmation_required"])
        self.assertTrue(packet["pre_write_required"])

    def test_risk_packet_rejects_incomplete_or_non_high_required_decision(self):
        selection = self.select(
            description="change workflow hook gate runtime",
            affected_paths=(PurePosixPath(".trellis/workflow.md"),),
        )
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "RiskPacketIncomplete"):
            policy.build_risk_packet(
                selection,
                ({"decision_id": "D1", "required": True, "severity": "medium"},),
                artifact_digest="a" * 64,
                detail_artifact_digest="c" * 64,
                task_id="task-1",
                slice_id="delivery-control",
                slice_packet_digest="b" * 64,
                invariant_ids=("INV-POLICY-001",),
            )

    def test_launch_boundary_rejects_non_codex_and_claude_events(self):
        plan = guru_supervise.RunPlan(
            action="check",
            task_dir=Path("task"),
            run_id="run",
            channel="channel",
            worker="worker",
            create_cmd=["create"],
            spawn_cmd=["spawn"],
            send_cmd=["send"],
            wait_cmd=["wait"],
            messages_cmd=["messages"],
            brief="brief",
            files=[],
            jsonls=[],
        )
        base = dict(
            root=Path("."), platform="cli", adversarial=False, adversarial_enabled=False,
            implement_timeout="1m", check_timeout="1m", warn_before="1m",
            idle_timeout=None, max_live_workers=None, trellis_bin="trellis",
            adversarial_model=None, adversarial_reasoning_effort=None,
        )
        non_codex = guru_supervise.SupervisionConfig(
            current_provider="claude", provider="claude", **base
        )
        with mock.patch.object(guru_supervise, "_run") as run:
            self.assertEqual(guru_supervise._execute_plan(plan, non_codex)[0], 2)
            run.assert_not_called()

        codex = guru_supervise.SupervisionConfig(
            current_provider="codex", provider="codex", **base
        )
        results = [
            mock.Mock(returncode=0, stdout="", stderr=""),
            mock.Mock(returncode=0, stdout="", stderr=""),
            mock.Mock(returncode=0, stdout="", stderr=""),
            mock.Mock(returncode=0, stdout='{"kind":"done"}\n', stderr=""),
            mock.Mock(returncode=0, stdout='{"kind":"message","provider":"claude"}\n', stderr=""),
        ]
        with mock.patch.object(guru_supervise, "_run", side_effect=results):
            self.assertEqual(guru_supervise._execute_plan(plan, codex)[0], 2)


if __name__ == "__main__":
    unittest.main()
