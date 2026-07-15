import dataclasses
import os
import sys
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock

VERIFY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if VERIFY_DIR not in sys.path:
    sys.path.insert(0, VERIFY_DIR)

import guru_contract
import guru_delivery_policy as policy
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

    def test_low_commit_enters_micro_with_scope(self):
        selection = self.select(
            description="fix typo in button label text",
            affected_paths=(PurePosixPath("lib/ui/title.dart"),),
            commit_requested=True,
        )
        self.assertEqual(selection.execution_route, guru_contract.ROUTE_MICRO_TASK)
        self.assertIn("gate_contract", selection.required_artifacts)
        self.assertEqual(selection.resolved_budget["model_cycles"], 8)

    def test_commit_without_concrete_low_risk_scope_routes_lite_not_micro(self):
        selection = self.select(description="fix typo", commit_requested=True)
        self.assertEqual(selection.execution_route, guru_contract.ROUTE_LITE_TASK)
        self.assertEqual(selection.required_gate_ids, ("deterministic_final",))

    def test_lite_enters_implementation_without_precode_gate_confirmation_or_worker(self):
        selection = self.select(description="change local button behavior", commit_requested=True)
        self.assertEqual(selection.execution_route, guru_contract.ROUTE_LITE_TASK)
        self.assertEqual(selection.required_gate_ids, ("deterministic_final",))
        self.assertEqual(selection.required_artifacts, ("scoped_diff", "deterministic_check"))
        self.assertLessEqual(selection.resolved_budget["first_value_deadline_seconds"], 300)
        self.assertEqual(selection.resolved_budget["confirmation_batches"], 0)
        self.assertEqual(selection.resolved_budget["live_workers"], 0)
        self.assertEqual(selection.resolved_budget["started_workers"], 0)
        self.assertEqual(selection.topology, "host_inline")
        self.assertEqual(selection.enforcement_mode, "advisory")
        self.assertIsNone(selection.capability_probe_digest)
        self.assertEqual(selection.route_acceptance["metrics_enforcement"], "advisory")

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
            description="fix typo in button label text",
            affected_paths=(PurePosixPath("lib/ui/title.dart"),),
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
            description="fix typo",
            affected_paths=(PurePosixPath("lib/a.dart"), PurePosixPath("lib/b.dart")),
            commit_requested=True,
            max_files=2,
        )
        self.assertEqual(selection.scope_max_files, 2)
        with self.assertRaisesRegex(policy.DeliveryPolicyError, "max_files"):
            self.select(
                description="fix typo",
                affected_paths=(PurePosixPath("lib/a.dart"), PurePosixPath("lib/b.dart")),
                commit_requested=True,
                max_files=1,
            )

    def test_contract_patch_carries_budget_and_generation_inputs(self):
        selection = self.select(
            description="fix typo in button label text",
            affected_paths=(PurePosixPath("lib/ui/title.dart"),),
            commit_requested=True,
        )
        patch = policy.selection_to_contract_patch(selection)
        self.assertEqual(patch["execution_policy"]["route"], guru_contract.ROUTE_MICRO_TASK)
        self.assertEqual(patch["execution_policy"]["budget"]["tool_calls"], 32)
        self.assertTrue(patch["execution_policy"]["scope_fingerprint"])

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
            commit_requested=True,
        )
        expanded = self.select(
            description="change workflow hook gate runtime",
            intent_hint="implementation",
            affected_paths=(PurePosixPath("lib/ui/button.dart"), PurePosixPath(".trellis/workflow.md")),
            commit_requested=True,
        )
        self.assertEqual(lite.execution_route, guru_contract.ROUTE_LITE_TASK)
        self.assertEqual(lite.resolved_budget["confirmation_batches"], 0)
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
