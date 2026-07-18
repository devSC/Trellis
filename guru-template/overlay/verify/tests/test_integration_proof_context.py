#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


VERIFY_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VERIFY_DIR))
SPEC = importlib.util.spec_from_file_location(
    "guru_supervise_integration_proof_test",
    VERIFY_DIR / "guru_supervise.py",
)
assert SPEC is not None and SPEC.loader is not None
SUPERVISE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SUPERVISE
SPEC.loader.exec_module(SUPERVISE)


def _target(packet: dict, *, digest_source: str = "index"):
    return SUPERVISE.ReviewTarget(
        unit_id=packet.get("slice_id", "SL-INTEGRATION"),
        review_target=f"slice:{packet.get('slice_id', 'SL-INTEGRATION')}",
        packet=packet,
        slice_packet_path=None,
        digest_source=digest_source,
        active_brief="",
        reviewed_target_digest="a" * 64,
    )


def _packet(**overrides) -> dict:
    packet = {
        "schema_version": 1,
        "review_evidence_schema_version": 2,
        "slice_id": "SL-INTEGRATION",
        "integration_slice": True,
        "risk": "high",
        "target_paths": ["guru-template/overlay/a.py"],
        "depends_on": ["SL-A"],
        "requirements_design_inputs": [],
        "invariants": [{"invariant_id": "INV-1", "rule": "rule"}],
    }
    packet.update(overrides)
    return packet


def _config(root: Path):
    return SUPERVISE.SupervisionConfig(
        root=root,
        platform="cli",
        current_provider="codex",
        provider="codex",
        adversarial=False,
        adversarial_enabled=True,
        implement_timeout="1m",
        check_timeout="1m",
        warn_before="1m",
        idle_timeout=None,
        max_live_workers=None,
        trellis_bin="trellis",
        adversarial_model=None,
        adversarial_reasoning_effort=None,
    )


def _plan(task_dir: Path) -> SUPERVISE.RunPlan:
    return SUPERVISE.RunPlan(
        action="implementation-review",
        task_dir=task_dir,
        run_id="run",
        channel="channel",
        worker="worker",
        create_cmd=["trellis", "channel", "create"],
        spawn_cmd=[
            "trellis",
            "channel",
            "spawn",
            "--agent",
            "check",
            "--file",
            "skill.md",
            "--jsonl",
            "check.jsonl",
        ],
        send_cmd=["trellis", "channel", "send"],
        wait_cmd=["trellis", "channel", "wait"],
        messages_cmd=["trellis", "channel", "messages"],
        brief="old",
        files=[task_dir / "skill.md"],
        jsonls=[task_dir / "check.jsonl"],
    )


class IntegrationProofContextTests(unittest.TestCase):
    def test_review_brief_requires_schema_literal_for_clean_coverage(self) -> None:
        brief = SUPERVISE._active_review_brief(
            label="SL-PROOF",
            review_target="slice:SL-PROOF",
            target_paths=["guru-template/overlay/verify/guru_supervise.py"],
            semantic_provider={"provider": "codex", "required": True},
            digest_source="index",
        )
        self.assertIn(
            "invariant_coverage=all_passed",
            brief,
        )
        self.assertIn("不要写 complete", brief)

    def test_eligibility_is_exact_and_ordinary_packets_bypass(self) -> None:
        task_dir = Path("/tmp/task")
        contract = {"route": "full_chain", "risk": "high"}
        with (
            mock.patch.object(
                SUPERVISE.guru_contract,
                "load_contract",
                return_value=(contract, ""),
            ),
            mock.patch.object(
                SUPERVISE.guru_contract,
                "contract_route",
                return_value=SUPERVISE.guru_contract.ROUTE_FULL_CHAIN,
            ),
            mock.patch.object(
                SUPERVISE.guru_contract,
                "contract_risk",
                return_value=SUPERVISE.guru_contract.RISK_HIGH,
            ),
        ):
            self.assertTrue(
                SUPERVISE._integration_proof_eligible(
                    task_dir, _target(_packet())
                )
            )
        ordinary = _packet(integration_slice=False)
        with mock.patch.object(
            SUPERVISE.guru_contract, "load_contract"
        ) as load_contract:
            self.assertFalse(
                SUPERVISE._integration_proof_eligible(
                    task_dir, _target(ordinary)
                )
            )
            load_contract.assert_not_called()
        legacy = _packet()
        legacy.pop("review_evidence_schema_version")
        with mock.patch.object(
            SUPERVISE.guru_contract, "load_contract"
        ) as load_contract:
            self.assertFalse(
                SUPERVISE._integration_proof_eligible(
                    task_dir, _target(legacy)
                )
            )
            load_contract.assert_not_called()
        legacy_v1 = _packet(review_evidence_schema_version=1)
        with mock.patch.object(
            SUPERVISE.guru_contract, "load_contract"
        ) as load_contract:
            self.assertFalse(
                SUPERVISE._integration_proof_eligible(
                    task_dir, _target(legacy_v1)
                )
            )
            load_contract.assert_not_called()
        with self.assertRaisesRegex(
            SUPERVISE.GuruSupervisionError, "must be boolean"
        ):
            SUPERVISE._integration_proof_eligible(
                task_dir, _target(_packet(integration_slice="yes"))
            )

    def test_non_full_bypasses_and_eligible_non_staged_fails_closed(self) -> None:
        task_dir = Path("/tmp/task")
        with (
            mock.patch.object(
                SUPERVISE.guru_contract,
                "load_contract",
                return_value=({"route": "lite_task", "risk": "high"}, ""),
            ),
            mock.patch.object(
                SUPERVISE.guru_contract,
                "contract_route",
                return_value="lite_task",
            ),
            mock.patch.object(
                SUPERVISE.guru_contract,
                "contract_risk",
                return_value="high",
            ),
        ):
            self.assertFalse(
                SUPERVISE._integration_proof_eligible(
                    task_dir,
                    _target(_packet(), digest_source="worktree"),
                )
            )
        with (
            mock.patch.object(
                SUPERVISE.guru_contract,
                "load_contract",
                return_value=({"route": "full_chain", "risk": "high"}, ""),
            ),
            mock.patch.object(
                SUPERVISE.guru_contract,
                "contract_route",
                return_value=SUPERVISE.guru_contract.ROUTE_FULL_CHAIN,
            ),
            mock.patch.object(
                SUPERVISE.guru_contract,
                "contract_risk",
                return_value=SUPERVISE.guru_contract.RISK_HIGH,
            ),
        ):
            with self.assertRaisesRegex(
                SUPERVISE.GuruSupervisionError, "current staged"
            ):
                SUPERVISE._integration_proof_eligible(
                    task_dir,
                    _target(_packet(), digest_source="worktree"),
                )

    def test_budget_boundaries_use_complete_utf8_bytes(self) -> None:
        self.assertEqual(
            SUPERVISE._enforce_proof_prompt_budget("a" * 75000),
            {"payload_bytes": 75000, "estimated_tokens": 25000},
        )
        with self.assertRaisesRegex(
            SUPERVISE.GuruSupervisionError,
            "estimated_tokens>25000",
        ):
            SUPERVISE._enforce_proof_prompt_budget("a" * 75001)
        with self.assertRaisesRegex(
            SUPERVISE.GuruSupervisionError,
            "estimated_tokens>25000",
        ):
            SUPERVISE._enforce_proof_prompt_budget("a" * 98304)
        with self.assertRaisesRegex(
            SUPERVISE.GuruSupervisionError,
            "payload_bytes>98304,estimated_tokens>25000",
        ):
            SUPERVISE._enforce_proof_prompt_budget("a" * 98305)
        self.assertEqual(
            SUPERVISE._proof_prompt_metrics("\u4e2d"),
            {"payload_bytes": 3, "estimated_tokens": 1},
        )

    def test_retry_identity_uses_exact_frozen_fields(self) -> None:
        components = {
            name: name[0] * 64
            for name in (
                "reviewed_target_digest",
                "target_paths_digest",
                "invariant_set_digest",
                "requirements_design_digest",
                "deterministic_commands_digest",
                "deterministic_results_digest",
                "review_policy_digest",
                "supervisor_source_digest",
            )
        }
        captured = {}

        def build(value):
            captured.update(value)
            return dict(value)

        with mock.patch.object(
            SUPERVISE.guru_review_record,
            "build_retry_identity",
            side_effect=build,
            create=True,
        ):
            identity = SUPERVISE._proof_retry_identity(components, "f" * 64)
        self.assertEqual(identity, captured)
        self.assertEqual(
            set(identity),
            {
                "reviewed_target_digest",
                "target_paths_digest",
                "invariant_set_digest",
                "requirements_design_digest",
                "deterministic_commands_digest",
                "deterministic_results_digest",
                "review_policy_digest",
                "supervisor_source_digest",
                "proof_bundle_digest",
            },
        )

    def test_proof_plan_injects_zero_files_and_jsonls(self) -> None:
        plan = SUPERVISE._without_injected_context(
            _plan(Path("/tmp/task")),
            "proof",
            Path("/tmp/proof-isolated"),
        )
        self.assertEqual(plan.files, [])
        self.assertEqual(plan.jsonls, [])
        self.assertNotIn("--file", plan.spawn_cmd)
        self.assertNotIn("--jsonl", plan.spawn_cmd)
        self.assertNotIn("--agent", plan.spawn_cmd)
        self.assertEqual(
            plan.spawn_cmd[-2:],
            ["--cwd", "/tmp/proof-isolated"],
        )
        self.assertEqual(plan.brief, "proof")

    def test_undeclared_source_tool_event_is_counted_from_channel_trace(self) -> None:
        rows = [
            {"kind": "turn_started", "by": "worker", "seq": 1},
            {
                "kind": "progress",
                "by": "worker",
                "seq": 2,
                "detail": {
                    "tool": "shell",
                    "cmd": "sed -n 1,20p source.py",
                    "status": "inProgress",
                },
            },
            {"kind": "done", "by": "worker", "seq": 3},
        ]
        completed = subprocess.CompletedProcess(
            [],
            0,
            "\n".join(json.dumps(row) for row in rows),
            "",
        )
        with mock.patch.object(
            SUPERVISE.subprocess,
            "run",
            return_value=completed,
        ):
            trace = SUPERVISE._proof_worker_tool_trace(
                _config(Path("/tmp/root")),
                _plan(Path("/tmp/task")),
            )
        self.assertEqual(trace["duplicate_read_probe_count"], 1)
        self.assertEqual(trace["tool_events"][0]["event_kind"], "shell")

    def test_generated_peer_projection_omits_bodies_and_rejects_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            source = "guru-template/overlay/verify/a.py"
            peer = "packages/cli/src/templates/guru/overlay/verify/a.py"
            for rel in (source, peer):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("print('same')\n", encoding="utf-8")
            subprocess.run(["git", "add", source, peer], cwd=root, check=True)
            proofs, peers = SUPERVISE._generated_peer_proofs(
                root, [source, peer]
            )
            self.assertEqual(peers, {peer})
            self.assertEqual(proofs[0]["equal"], True)
            self.assertNotIn("content", proofs[0])
            (root / peer).write_text("different\n", encoding="utf-8")
            subprocess.run(["git", "add", peer], cwd=root, check=True)
            with self.assertRaisesRegex(
                SUPERVISE.GuruSupervisionError, "peer differs"
            ):
                SUPERVISE._generated_peer_proofs(root, [source, peer])

    def test_whole_file_requirement_selector_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            task_dir = Path(temp)
            (task_dir / "prd.md").write_text("# PRD\n", encoding="utf-8")
            with self.assertRaisesRegex(
                SUPERVISE.GuruSupervisionError, "whole-file"
            ):
                SUPERVISE._proof_requirements_design_context(
                    task_dir,
                    [{"path": "prd.md", "whole_file": True}],
                )

    def test_dependency_receipts_are_current_and_projected_without_bodies(self) -> None:
        receipt = {
            "slice_id": "SL-A",
            "commit_sha": "1" * 40,
            "receipt_id": "2" * 64,
            "review_run_id": "run-a",
            "reviewed_target_digest": "3" * 64,
            "invariant_verdicts_digest": "4" * 64,
            "target_paths_digest": "5" * 64,
            "requirements_design_digest": "6" * 64,
            "deterministic_commands_digest": "7" * 64,
            "deterministic_results_digest": "8" * 64,
            "review_policy_digest": "9" * 64,
        }
        packet = {"depends_on": ["SL-A"]}
        dependency_packet = {"target_paths": ["guru-template/overlay/a.py"]}
        completed = subprocess.CompletedProcess([], 0, "", "")
        with (
            mock.patch.object(
                SUPERVISE,
                "_guru_gate_receipt_history_by_slice",
                return_value={"SL-A": [receipt]},
            ),
            mock.patch.object(
                SUPERVISE,
                "_guru_gate_validate_slice_receipt",
                return_value="",
            ),
            mock.patch.object(
                SUPERVISE.guru_review_record,
                "load_packet",
                return_value=dependency_packet,
            ),
            mock.patch.object(
                SUPERVISE.subprocess,
                "run",
                return_value=completed,
            ),
        ):
            proofs, union = SUPERVISE._dependency_receipt_proofs(
                Path("/tmp/task"), Path("/tmp/root"), packet
            )
        self.assertEqual(union, ["guru-template/overlay/a.py"])
        self.assertEqual(proofs[0]["state"], "current")
        self.assertNotIn("target_body", proofs[0])

    def test_prompt_serialization_stabilizes_metrics(self) -> None:
        bundle = {
            "invariants": [{"invariant_id": "INV-1"}],
            "payload_metrics": {},
            "proof_bundle_digest": "",
        }
        identity = {
            "reviewed_target_digest": "a" * 64,
            "target_paths_digest": "b" * 64,
            "invariant_set_digest": "c" * 64,
            "requirements_design_digest": "d" * 64,
            "deterministic_commands_digest": "e" * 64,
            "deterministic_results_digest": "f" * 64,
            "review_policy_digest": "1" * 64,
            "supervisor_source_digest": "2" * 64,
        }
        with mock.patch.object(
            SUPERVISE.guru_review_record,
            "build_retry_identity",
            side_effect=lambda value: dict(value),
            create=True,
        ):
            prompt, projected, retry_identity = (
                SUPERVISE._serialize_integration_proof_prompt(
                    bundle,
                    {
                        "review_target": "slice:SL-INTEGRATION",
                        "review_provider": "codex",
                        "files": [],
                        "jsonls": [],
                    },
                    identity,
                )
            )
        self.assertEqual(
            projected["payload_metrics"],
            SUPERVISE._proof_prompt_metrics(prompt),
        )
        self.assertEqual(
            retry_identity["proof_bundle_digest"],
            projected["proof_bundle_digest"],
        )
        self.assertNotIn("--file", prompt)
        payload = json.loads(prompt.split("\n", 1)[1])
        metrics = payload["acceptance_metrics"]
        self.assertEqual(
            metrics["payload_bytes"],
            projected["payload_metrics"]["payload_bytes"],
        )
        self.assertEqual(
            metrics["estimated_tokens"],
            projected["payload_metrics"]["estimated_tokens"],
        )
        self.assertEqual(metrics["budget_verdict"], "passed")
        self.assertEqual(metrics["formatting_retry_identity"], retry_identity)
        contract = payload["verdict_contract"]
        self.assertEqual(
            contract["clean_header_values"]["invariant_coverage"],
            "all_passed",
        )
        self.assertEqual(
            contract["per_invariant_lines"]["status"],
            "invariant_status.<id>=pass|fail|not_applicable",
        )

    def test_acceptance_metrics_are_complete_and_require_one_regression(self) -> None:
        result = {"command": SUPERVISE.INTEGRATION_FULL_REGRESSION_COMMAND}
        metrics = SUPERVISE._integration_acceptance_metrics(
            receipt_proofs=[
                {"slice_id": "SL-A", "state": "current"},
                {"slice_id": "SL-B", "state": "current"},
            ],
            ordinary_targets=["a", "b", "c", "d"],
            peer_proofs=[{"equal": True}] * 7,
            integration_owned=["shell", "peer-a", "peer-b"],
            peer_paths={"peer-a", "peer-b"},
            requirements_design_proofs=[{}] * 10,
            deterministic_results=[{}, {}, {}, {}, result, {}],
        )
        self.assertEqual(metrics["semantic_reviewer_count"], 1)
        self.assertEqual(metrics["duplicate_read_probe_count"], 0)
        self.assertEqual(metrics["integration_full_regression_count"], 1)
        self.assertEqual(metrics["projection_counts"]["generated_peers"], 7)
        self.assertEqual(
            metrics["projection_counts"]["integration_owned_diff_paths"], 1
        )
        self.assertEqual(metrics["formatting_retry_count"], 0)
        self.assertEqual(metrics["receipt_invalidation_set"], [])
        self.assertEqual(
            metrics["provider_input_tokens"],
            {"available": False, "value": None},
        )
        with self.assertRaisesRegex(
            SUPERVISE.GuruSupervisionError,
            "exactly one full lifecycle regression:count=0",
        ):
            SUPERVISE._integration_acceptance_metrics(
                receipt_proofs=[],
                ordinary_targets=[],
                peer_proofs=[],
                integration_owned=[],
                peer_paths=set(),
                requirements_design_proofs=[],
                deterministic_results=[],
            )

    def test_semantic_prompt_contains_complete_frozen_verdict_contract(self) -> None:
        components = {
            "reviewed_target_digest": "a" * 64,
            "target_paths_digest": "b" * 64,
            "invariant_set_digest": "c" * 64,
            "requirements_design_digest": "d" * 64,
            "deterministic_commands_digest": "e" * 64,
            "deterministic_results_digest": "f" * 64,
            "review_policy_digest": "1" * 64,
            "supervisor_source_digest": "2" * 64,
        }
        invocation = {
            "review_target": "slice:SL-INTEGRATION",
            "review_provider": "codex",
            "files": [],
            "jsonls": [],
        }
        with mock.patch.object(
            SUPERVISE.guru_review_record,
            "build_retry_identity",
            side_effect=lambda value: dict(value),
            create=True,
        ):
            prompt, _projected, _identity = (
                SUPERVISE._serialize_integration_proof_prompt(
                    {"invariants": [{"invariant_id": "INV-1"}]},
                    invocation,
                    components,
                )
            )
        payload = json.loads(prompt.split("\n", 1)[1])
        contract = payload["verdict_contract"]
        self.assertEqual(
            contract["expected_invariant_ids"],
            ["INV-1"],
        )
        self.assertEqual(
            contract["required_headers"]["review_result"],
            ["blocked", "clean", "findings"],
        )
        self.assertEqual(
            contract["required_headers"]["review_target"],
            ["slice:SL-INTEGRATION"],
        )
        self.assertEqual(
            contract["clean_header_values"]["invariant_coverage"],
            "all_passed",
        )
        self.assertEqual(
            contract["per_invariant_lines"]["pass_evidence"],
            "invariant_evidence.<id>=<non-empty evidence>",
        )

    def test_admission_or_budget_failure_dispatches_zero_providers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task_dir = root / "task"
            task_dir.mkdir()
            config = _config(root)
            resolution = SUPERVISE.ReviewProviderResolution(
                check_config=config,
                reason="test",
                provider_override_source="config_policy",
                same_provider_user_quote=None,
                review_target_kind="slice",
            )
            args = argparse.Namespace(
                dry_run=False,
                platform="cli",
                provider="codex",
                trellis_bin="trellis",
            )
            execute = mock.Mock()
            with (
                mock.patch.object(
                    SUPERVISE,
                    "_integration_proof_bundle",
                    side_effect=SUPERVISE.GuruSupervisionError("stale receipt"),
                ),
                mock.patch.object(SUPERVISE, "_execute_plan", execute),
            ):
                with self.assertRaisesRegex(
                    SUPERVISE.GuruSupervisionError, "stale receipt"
                ):
                    SUPERVISE._run_integration_proof_review(
                        task_dir=task_dir,
                        root=root,
                        target=_target(_packet()),
                        config=config,
                        resolution=resolution,
                        review_run_id="run",
                        evidence_key="e" * 64,
                        evidence_components={},
                        det_status="passed",
                        det_results=[],
                        deterministic_reused=True,
                        args=args,
                    )
            execute.assert_not_called()

            with (
                mock.patch.object(
                    SUPERVISE,
                    "_integration_proof_bundle",
                    return_value={"invariants": [{"invariant_id": "INV-1"}]},
                ),
                mock.patch.object(
                    SUPERVISE,
                    "build_run_plan",
                    return_value=_plan(task_dir),
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_serialize_integration_proof_prompt",
                    side_effect=SUPERVISE.GuruSupervisionError("budget exceeded"),
                ),
                mock.patch.object(SUPERVISE, "_execute_plan", execute),
                mock.patch.object(
                    SUPERVISE.guru_review_record,
                    "deterministic_results_digest",
                    return_value="d" * 64,
                ),
            ):
                with self.assertRaisesRegex(
                    SUPERVISE.GuruSupervisionError, "budget exceeded"
                ):
                    SUPERVISE._run_integration_proof_review(
                        task_dir=task_dir,
                        root=root,
                        target=_target(_packet()),
                        config=config,
                        resolution=resolution,
                        review_run_id="run",
                        evidence_key="e" * 64,
                        evidence_components={},
                        det_status="passed",
                        det_results=[],
                        deterministic_reused=True,
                        args=args,
                    )
            execute.assert_not_called()

    def test_orchestration_uses_one_semantic_call_and_one_optional_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task_dir = root / "task"
            task_dir.mkdir()
            config = _config(root)
            resolution = SUPERVISE.ReviewProviderResolution(
                check_config=config,
                reason="test",
                provider_override_source="config_policy",
                same_provider_user_quote=None,
                review_target_kind="slice",
            )
            target = _target(_packet())
            args = argparse.Namespace(
                dry_run=False,
                platform="cli",
                provider="codex",
                trellis_bin="trellis",
            )
            bundle = {
                "invariants": [{"invariant_id": "INV-1"}],
                "proof_bundle_digest": "f" * 64,
            }
            identity = {"proof_bundle_digest": "f" * 64}
            record = {"review_result": "clean", "route_class": "none"}
            plans = []

            def execute(plan, _config_value):
                plans.append(plan)
                return (0, "done", "semantic" if len(plans) == 1 else "serialized")

            with (
                mock.patch.object(
                    SUPERVISE,
                    "_integration_proof_bundle",
                    return_value=bundle,
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_serialize_integration_proof_prompt",
                    return_value=("proof", bundle, identity),
                ),
                mock.patch.object(
                    SUPERVISE,
                    "build_run_plan",
                    side_effect=lambda *args, **kwargs: _plan(task_dir),
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_review_read_only_snapshot",
                    return_value="snapshot",
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_execute_plan",
                    side_effect=execute,
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_proof_worker_tool_trace",
                    side_effect=[
                        {
                            "status": "complete",
                            "duplicate_read_probe_count": 0,
                            "tool_events": [],
                        },
                        {
                            "status": "complete",
                            "duplicate_read_probe_count": 0,
                            "tool_events": [],
                        },
                    ],
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_proof_classification",
                    side_effect=["retryable_format", "valid"],
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_append_proof_retry_event",
                    return_value={"artifact": "raw.txt"},
                ) as append_event,
                mock.patch.object(
                    SUPERVISE,
                    "_require_current_slice_evidence",
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_append_proof_normalized_record",
                    return_value=(record, None),
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_enforce_proof_prompt_budget",
                    return_value={"payload_bytes": 1, "estimated_tokens": 1},
                ),
                mock.patch.object(
                    SUPERVISE.guru_review_record,
                    "deterministic_results_digest",
                    return_value="d" * 64,
                ),
            ):
                result = SUPERVISE._run_integration_proof_review(
                    task_dir=task_dir,
                    root=root,
                    target=target,
                    config=config,
                    resolution=resolution,
                    review_run_id="run",
                    evidence_key="e" * 64,
                    evidence_components={},
                    det_status="passed",
                    det_results=[],
                    deterministic_reused=True,
                    args=args,
                )
            self.assertEqual(result, 0)
            self.assertEqual(len(plans), 2)
            self.assertEqual(append_event.call_count, 2)
            self.assertEqual(
                append_event.call_args_list[0].args[3:],
                (0, "semantic", "retryable_format"),
            )
            self.assertEqual(
                append_event.call_args_list[1].args[3:],
                (1, "serialized", "valid"),
            )
            for plan in plans:
                self.assertEqual(plan.files, [])
                self.assertEqual(plan.jsonls, [])
                self.assertNotIn("--file", plan.spawn_cmd)
                self.assertNotIn("--jsonl", plan.spawn_cmd)
                self.assertIn("--cwd", plan.spawn_cmd)
            retry_payload = json.loads(plans[1].brief.split("\n", 1)[1])
            self.assertEqual(
                retry_payload["verdict_contract"]["clean_header_values"][
                    "invariant_coverage"
                ],
                "all_passed",
            )
            self.assertEqual(
                retry_payload["verdict_contract"]["expected_invariant_ids"],
                ["INV-1"],
            )

    def test_undeclared_tool_event_blocks_before_clean_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task_dir = root / "task"
            task_dir.mkdir()
            config = _config(root)
            resolution = SUPERVISE.ReviewProviderResolution(
                check_config=config,
                reason="test",
                provider_override_source="config_policy",
                same_provider_user_quote=None,
                review_target_kind="slice",
            )
            target = _target(_packet())
            args = argparse.Namespace(
                dry_run=False,
                platform="cli",
                provider="codex",
                trellis_bin="trellis",
            )
            bundle = {
                "invariants": [{"invariant_id": "INV-1"}],
                "proof_bundle_digest": "f" * 64,
            }
            trace = {
                "status": "complete",
                "duplicate_read_probe_count": 1,
                "tool_events": [{"event_kind": "shell", "seq": 2}],
            }
            normalize = mock.Mock()
            with (
                mock.patch.object(
                    SUPERVISE,
                    "_integration_proof_bundle",
                    return_value=bundle,
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_serialize_integration_proof_prompt",
                    return_value=("proof", bundle, {"proof_bundle_digest": "f" * 64}),
                ),
                mock.patch.object(
                    SUPERVISE,
                    "build_run_plan",
                    return_value=_plan(task_dir),
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_review_read_only_snapshot",
                    return_value="snapshot",
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_execute_plan",
                    return_value=(0, "done", "clean semantic output"),
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_proof_worker_tool_trace",
                    return_value=trace,
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_append_proof_normalized_record",
                    normalize,
                ),
                mock.patch.object(
                    SUPERVISE,
                    "_record_final_proof_blocked",
                ) as blocked,
                mock.patch.object(
                    SUPERVISE.guru_review_record,
                    "deterministic_results_digest",
                    return_value="d" * 64,
                ),
            ):
                result = SUPERVISE._run_integration_proof_review(
                    task_dir=task_dir,
                    root=root,
                    target=target,
                    config=config,
                    resolution=resolution,
                    review_run_id="run",
                    evidence_key="e" * 64,
                    evidence_components={},
                    det_status="passed",
                    det_results=[],
                    deterministic_reused=True,
                    args=args,
                )
            self.assertEqual(result, 2)
            normalize.assert_not_called()
            self.assertEqual(
                blocked.call_args.args[4]["semantic"][
                    "duplicate_read_probe_count"
                ],
                1,
            )

    def test_final_retry_failure_uses_normalized_blocked_producer_once(self) -> None:
        target = _target(_packet())
        appended = []
        with mock.patch.object(
            SUPERVISE.guru_review_record,
            "append_record",
            side_effect=lambda _task, record: appended.append(record),
        ):
            SUPERVISE._record_final_proof_blocked(
                Path("/tmp/task"),
                target,
                "run-serialization-1",
                {
                    "implement_provider": "codex",
                    "review_provider": "codex",
                    "deterministic_checks": "passed",
                    "deterministic_results": [],
                    "channel": "channel",
                    "worker": "worker",
                },
                {
                    "semantic": {
                        "status": "complete",
                        "duplicate_read_probe_count": 1,
                        "tool_events": [{"event_kind": "shell", "seq": 2}],
                    }
                },
            )
        self.assertEqual(len(appended), 1)
        self.assertEqual(appended[0]["review_result"], "blocked")
        self.assertEqual(
            appended[0]["supervisor_failure"],
            "MALFORMED_REVIEW_OUTPUT",
        )
        self.assertIn(
            '"duplicate_read_probe_count":1',
            appended[0]["message"],
        )


if __name__ == "__main__":
    unittest.main()
