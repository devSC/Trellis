#!/usr/bin/env python3
"""Core-free Guru delivery policy resolver.

This module is intentionally template/overlay owned.  It turns an intake request
into an immutable execution selection/envelope without importing Trellis Core.
"""
from __future__ import annotations

import argparse
import dataclasses
import glob
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guru_contract  # noqa: E402
import guru_risk  # noqa: E402
import guru_review_record  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_POLICY_RELS = (
    os.path.join("..", "policy", "delivery-policy.json"),
    os.path.join("..", "..", "policy", "delivery-policy.json"),
)
INSTALLED_CONSISTENCY_PATHS = (
    ".trellis/policy/delivery-policy.json",
    ".trellis/workflow.md",
    ".trellis/scripts/guru/guru_contract.py",
    ".trellis/scripts/guru/guru_delivery_policy.py",
    ".trellis/scripts/guru/guru_gate.py",
    ".trellis/scripts/guru/guru_risk.py",
)
SOURCE_CONSISTENCY_PATHS = (
    "guru-template/overlay/README.md",
    "guru-template/overlay/policy/delivery-policy.json",
    "guru-template/overlay/verify/guru_contract.py",
    "guru-template/overlay/verify/guru_delivery_policy.py",
    "guru-template/overlay/verify/guru_gate.py",
    "guru-template/overlay/verify/guru_risk.py",
    "guru-template/overlay/tests/apply_test.sh",
    "guru-template/overlay/verify/tests/test_delivery_policy.py",
)

INTENTS = {"implementation", "review", "research", "debug", "docs", "config", "ops"}
READ_ONLY_INTENTS = {"review", "research"}
REQUIRED_BUDGET_KEYS = {
    "planning_deadline_seconds",
    "first_value_deadline_seconds",
    "terminal_deadline_seconds",
    "model_cycles",
    "tool_calls",
    "wait_calls",
    "planned_context_bytes",
    "observed_context_bytes",
    "duplicate_reads",
    "repairs",
    "live_workers",
    "started_workers",
    "idle_seconds",
    "no_progress_cycles",
    "confirmation_batches",
}
MANAGED_BASE_PROBES = {"lifecycle_control", "structured_events"}
MANAGED_BUDGET_PROBES = {
    "active_monotonic_time",
    "model_cycles",
    "tool_calls",
    "wait_calls",
    "observed_context_bytes",
    "duplicate_reads",
    "repairs",
    "worker_leases",
    "idle_seconds",
    "semantic_progress",
    "confirmation_batches",
}
HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")
DELIVERY_METRICS = (
    "time_to_first_code",
    "user_confirmation_count",
    "review_worker_count",
    "full_suite_run_count",
    "digest_invalidation_count",
    "finding_to_fix_cycles",
    "wall_time_per_route",
    "token_cost_per_completed_slice",
    "gate_rework_count",
)


class DeliveryPolicyError(ValueError):
    """Raised when policy input or selection is invalid."""


@dataclass(frozen=True)
class IntakeRequest:
    description: str = ""
    intent_hint: str | None = None
    affected_paths: tuple[PurePosixPath, ...] = ()
    commit_requested: bool = False
    read_only_requested: bool = False
    preferred_route: str | None = None
    max_files: int | None = None
    requirements_clear: bool | None = None
    coupling: str = "unknown"
    reversible: bool | None = None
    verification_scope: str = "unknown"
    prior_route: str | None = None
    prior_selection_generation: int | None = None
    first_write_started: bool = False


@dataclass(frozen=True)
class DeliverySelection:
    intent: str
    execution_route: str
    risk: str
    first_value_metric: str
    first_value_kind: str
    write_capability: str
    required_artifacts: tuple[str, ...]
    required_gate_ids: tuple[str, ...]
    terminal_conditions: tuple[str, ...]
    resolved_budget: dict[str, int]
    scope_fingerprint: str
    policy_version: str
    promotion_reasons: tuple[str, ...]
    topology: str
    enforcement_mode: str
    scope_max_files: int | None
    capability_probe_digest: str | None
    evidence_cache_key: str | None
    evidence_reused: bool
    planning_cost_ratio_percent: int
    route_acceptance: dict[str, Any]
    delivery_metrics: tuple[str, ...]
    recommended_route: str
    selected_route: str
    selection_source: str
    selection_generation: int
    brainstorm_required: bool


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _repo_rel(path: PurePosixPath | str) -> str:
    text = str(path)
    if (
        not text
        or "\x00" in text
        or "\\" in text
        or text.startswith("/")
        or text.startswith("./")
        or text.startswith("~")
        or text.startswith("file:")
        or "//" in text
        or text.endswith("/")
    ):
        raise DeliveryPolicyError(f"ScopeUnbounded: unsafe scope path: {text!r}")
    parts = text.split("/")
    if any(part in {"", ".", ".."} for part in parts) or re.match(r"^[A-Za-z]:", parts[0]):
        raise DeliveryPolicyError(f"ScopeUnbounded: unsafe scope path: {text!r}")
    return text


def project_docs_code_test_digest(project_root: str) -> str | None:
    """Bind evidence reuse to the installed or source Custom contract snapshot."""
    root = os.path.abspath(project_root)
    for candidates in (INSTALLED_CONSISTENCY_PATHS, SOURCE_CONSISTENCY_PATHS):
        if all(os.path.isfile(os.path.join(root, rel)) for rel in candidates):
            try:
                return guru_review_record.target_snapshot_digest(root, list(candidates), "worktree")
            except guru_review_record.ReviewRecordError:
                return None
    return None


def delivery_evidence_cache_key(
    *,
    policy_version: str,
    intent: str,
    execution_route: str,
    scope_fingerprint: str,
    target_digest: str,
    docs_code_test_digest: str,
) -> str:
    return _digest({
        "policy_version": policy_version,
        "intent": intent,
        "execution_route": execution_route,
        "scope_fingerprint": scope_fingerprint,
        "target_digest": target_digest,
        "docs_code_test_digest": docs_code_test_digest,
    })


def _project_evidence_inputs(project_root: str, paths: tuple[str, ...]) -> dict[str, Any]:
    if not paths:
        return {}
    try:
        target_digest = guru_review_record.target_snapshot_digest(
            os.path.abspath(project_root),
            list(paths),
            "worktree",
        )
    except guru_review_record.ReviewRecordError:
        return {}
    consistency_digest = project_docs_code_test_digest(project_root)
    if not HEX_DIGEST.fullmatch(str(consistency_digest or "")):
        return {}
    return {
        "target_digest": target_digest,
        "docs_code_test_digest": consistency_digest,
    }


def _find_project_reuse_candidate(
    project_root: str,
    *,
    evidence_cache_key: str,
    target_digest: str,
    docs_code_test_digest: str,
) -> dict | None:
    root = os.path.abspath(project_root)
    patterns = (
        os.path.join(root, ".trellis", "tasks", "*", "verification-evidence.jsonl"),
        os.path.join(root, ".trellis", "tasks", "archive", "*", "*", "verification-evidence.jsonl"),
    )
    for path in reversed(sorted({item for pattern in patterns for item in glob.glob(pattern)})):
        try:
            with open(path, encoding="utf-8") as fh:
                rows = [json.loads(line) for line in fh if line.strip()]
        except (OSError, json.JSONDecodeError):
            continue
        for row in reversed(rows):
            if not isinstance(row, dict) or row.get("kind") != "delivery_evidence_cache":
                continue
            if (
                row.get("evidence_cache_key") == evidence_cache_key
                and row.get("target_digest") == target_digest
                and row.get("docs_code_test_digest") == docs_code_test_digest
                and row.get("outcome") == "passed"
            ):
                return row
    return None


def load_policy(path: str | None = None) -> dict:
    if path is None:
        base = os.path.dirname(os.path.abspath(__file__))
        candidates = [os.path.join(base, rel) for rel in DEFAULT_POLICY_RELS]
        path = next((candidate for candidate in candidates if os.path.isfile(candidate)), candidates[0])
    with open(path, encoding="utf-8") as fh:
        policy = json.load(fh)
    validate_policy(policy)
    return policy


def validate_policy(policy: dict) -> None:
    if not isinstance(policy, dict):
        raise DeliveryPolicyError("PolicySchemaInvalid: policy root must be object")
    if policy.get("schema_version") != SCHEMA_VERSION:
        raise DeliveryPolicyError(f"PolicySchemaInvalid: schema_version must be {SCHEMA_VERSION}")
    if not isinstance(policy.get("policy_version"), str) or not policy["policy_version"].strip():
        raise DeliveryPolicyError("PolicySchemaInvalid: policy_version missing")
    intent_profiles = policy.get("intent_profiles")
    route_profiles = policy.get("route_profiles")
    if not isinstance(intent_profiles, dict) or not INTENTS.issubset(intent_profiles):
        raise DeliveryPolicyError("PolicySchemaInvalid: intent_profiles incomplete")
    if not isinstance(route_profiles, dict):
        raise DeliveryPolicyError("PolicySchemaInvalid: route_profiles missing")
    for route in (*guru_contract.ROUTES, "read_only_cap"):
        profile = route_profiles.get(route)
        if not isinstance(profile, dict):
            raise DeliveryPolicyError(f"PolicySchemaInvalid: route profile missing: {route}")
        missing = REQUIRED_BUDGET_KEYS - set(profile)
        if missing:
            raise DeliveryPolicyError(f"PolicySchemaInvalid: route {route} missing budgets: {sorted(missing)}")
        for key in REQUIRED_BUDGET_KEYS:
            value = profile.get(key)
            if not isinstance(value, int) or value < 0:
                raise DeliveryPolicyError(f"PolicySchemaInvalid: {route}.{key} must be non-negative integer")
            if key not in {"wait_calls", "live_workers", "started_workers", "confirmation_batches"} and value == 0:
                raise DeliveryPolicyError(f"PolicySchemaInvalid: {route}.{key} must be positive")
    gates = policy.get("route_gates")
    if not isinstance(gates, dict) or not guru_contract.ROUTES.issubset(gates):
        raise DeliveryPolicyError("PolicySchemaInvalid: route_gates incomplete")
    read_only_gates = policy.get("read_only_route_gates")
    if not isinstance(read_only_gates, dict) or not guru_contract.ROUTES.issubset(read_only_gates):
        raise DeliveryPolicyError("PolicySchemaInvalid: read_only_route_gates incomplete")
    risk_rules = policy.get("risk_rules")
    if not isinstance(risk_rules, dict):
        raise DeliveryPolicyError("PolicySchemaInvalid: risk_rules missing")
    if {"low_commit_route", "low_no_commit_route"}.intersection(risk_rules):
        raise DeliveryPolicyError("PolicySchemaInvalid: risk_rules cannot classify complexity from commit intent")
    required_risk_rules = {
        "high_or_unknown_high_signal_route",
        "unknown_default_route",
        "medium_default_route",
        "mechanical_change_route",
        "bounded_local_change_route",
        "ambiguous_requirements_route",
    }
    if not required_risk_rules.issubset(risk_rules):
        raise DeliveryPolicyError("PolicySchemaInvalid: risk_rules difficulty evidence table incomplete")
    topology_rules = policy.get("topology_rules")
    if not isinstance(topology_rules, dict) or not guru_contract.ROUTES.issubset(topology_rules):
        raise DeliveryPolicyError("PolicySchemaInvalid: topology_rules incomplete")
    for inline_route in (
        guru_contract.ROUTE_SMALL_INLINE,
        guru_contract.ROUTE_MICRO_TASK,
        guru_contract.ROUTE_LITE_TASK,
    ):
        if topology_rules.get(inline_route) != ["host_inline"]:
            raise DeliveryPolicyError(
                f"PolicySchemaInvalid: {inline_route} topology must be host_inline only"
            )
    if topology_rules.get(guru_contract.ROUTE_FULL_CHAIN) != ["managed_single", "managed_parallel"]:
        raise DeliveryPolicyError(
            "PolicySchemaInvalid: full_chain topology must allow managed_single and managed_parallel"
        )


def _infer_intent(request: IntakeRequest) -> str:
    hint = str(request.intent_hint or "").strip().lower().replace("-", "_")
    if hint in INTENTS:
        return hint
    text = request.description.lower()
    if request.read_only_requested or "review" in text or "审查" in text or "只读" in text:
        return "review"
    if "research" in text or "调研" in text:
        return "research"
    if "debug" in text or "bug" in text or "报错" in text:
        return "debug"
    if "doc" in text or "文档" in text:
        return "docs"
    if "config" in text or "配置" in text or "workflow" in text or "hook" in text:
        return "config"
    return "implementation"


def _min_budget(left: dict, right: dict) -> dict[str, int]:
    return {key: min(int(left[key]), int(right[key])) for key in REQUIRED_BUDGET_KEYS}


def _route_rank(route: str) -> int:
    return guru_contract.ROUTE_RANK.get(guru_contract.normalize_route(route), -1)


def _route_eligible(route: str, request: IntakeRequest, assessment: dict) -> bool:
    route = guru_contract.normalize_route(route)
    if route == guru_contract.ROUTE_FULL_CHAIN:
        return True
    if guru_contract.normalize_risk(assessment.get("risk")) == guru_contract.RISK_HIGH:
        return False
    if route == guru_contract.ROUTE_LITE_TASK:
        return True
    if route == guru_contract.ROUTE_MICRO_TASK:
        return (
            request.requirements_clear is True
            and str(request.coupling).strip().lower().replace("-", "_") == "local"
            and request.reversible is True
            and str(request.verification_scope).strip().lower().replace("-", "_") == "focused"
            and 0 < len(request.affected_paths) <= 3
        )
    if route == guru_contract.ROUTE_SMALL_INLINE:
        return "mechanical_change" in set(assessment.get("risk_flags") or [])
    return False


def _resolve_route_transition(
    request: IntakeRequest,
    assessment: dict,
    recommended: str,
    *,
    force_full: bool,
) -> tuple[str, str, int, tuple[str, ...]]:
    prior = guru_contract.normalize_route(request.prior_route)
    preferred = guru_contract.normalize_route(request.preferred_route)
    prior_generation = request.prior_selection_generation
    if prior and (
        not isinstance(prior_generation, int)
        or isinstance(prior_generation, bool)
        or prior_generation <= 0
    ):
        raise DeliveryPolicyError("RouteTransitionInvalid: prior route requires a positive selection generation")

    reasons: list[str] = []
    source = "recommended"
    if preferred:
        selected = preferred
        source = "user_override"
        if force_full:
            reasons.append("high_or_unknown_high_signal_recommends_full_chain")
    elif force_full:
        selected = guru_contract.ROUTE_FULL_CHAIN
        source = "risk_promotion"
        reasons.append("high_or_unknown_high_signal_recommends_full_chain")
    else:
        selected = recommended

    if prior and selected != prior:
        generation = int(prior_generation) + 1
        if _route_rank(selected) > _route_rank(prior):
            source = "risk_promotion" if force_full else "scope_reassessment"
            reasons.append(f"route_promoted_{prior}_to_{selected}")
        elif source != "user_override":
            source = "prewrite_reassessment"
    elif prior:
        generation = int(prior_generation)
    else:
        generation = 1
    return selected, source, generation, tuple(reasons)


def _resolve_topology(route: str, capability_report: dict | None) -> tuple[str, str, str | None]:
    capability_report = capability_report if isinstance(capability_report, dict) else {}
    active_probes_raw = capability_report.get("active_probes")
    active_probes = {
        str(item) for item in (active_probes_raw if isinstance(active_probes_raw, list) else [])
        if isinstance(item, str) and item
    }
    generation = capability_report.get("probe_generation")
    generation_valid = isinstance(generation, str) and bool(generation.strip())
    managed = capability_report.get("managed_runner") is True and generation_valid
    all_hard_probes = MANAGED_BASE_PROBES | MANAGED_BUDGET_PROBES
    enforced = managed and all_hard_probes.issubset(active_probes)
    parallel = (
        capability_report.get("managed_parallel") is True
        and capability_report.get("parallel_eligible") is True
        and "parallel_leases" in active_probes
    )
    probe_digest = _digest({"generation": generation, "active_probes": sorted(active_probes)}) if managed else None
    route = guru_contract.normalize_route(route)
    if route in {
        guru_contract.ROUTE_SMALL_INLINE,
        guru_contract.ROUTE_MICRO_TASK,
        guru_contract.ROUTE_LITE_TASK,
    }:
        return "host_inline", "advisory", None
    if route == guru_contract.ROUTE_FULL_CHAIN and not enforced:
        missing = sorted(all_hard_probes - active_probes)
        raise DeliveryPolicyError(
            "CapabilityUnavailable: full_chain requires actively probed managed runner counters: "
            + ", ".join(missing)
        )
    if route == guru_contract.ROUTE_FULL_CHAIN and parallel:
        return "managed_parallel", "enforced", probe_digest
    if route == guru_contract.ROUTE_FULL_CHAIN:
        return "managed_single", "enforced", probe_digest
    raise DeliveryPolicyError("TopologyIllegal: unknown execution route")


def _required_artifacts(intent: str, route: str) -> tuple[str, ...]:
    if intent in READ_ONLY_INTENTS:
        return ("evidence_package", "verified_evidence") if route == guru_contract.ROUTE_FULL_CHAIN else ("verified_evidence",)
    if route == guru_contract.ROUTE_SMALL_INLINE:
        return ("scoped_diff", "deterministic_check")
    if route == guru_contract.ROUTE_MICRO_TASK:
        return ("gate_contract", "scoped_diff", "deterministic_check")
    if route == guru_contract.ROUTE_LITE_TASK:
        return (
            "task_json", "prd", "implement_context", "check_context", "gate_contract",
            "task_evidence", "scoped_diff", "deterministic_check",
        )
    return ("requirements", "overview", "detail", "slice_packet", "risk_packet", "guarded_start", "implementation_review")


def _required_gates(policy: dict, intent: str, route: str) -> tuple[str, ...]:
    if intent in READ_ONLY_INTENTS:
        read_only_gates = policy.get("read_only_route_gates")
        if not isinstance(read_only_gates, dict) or route not in read_only_gates:
            raise DeliveryPolicyError("PolicySchemaInvalid: read_only_route_gates incomplete")
        return tuple(read_only_gates[route])
    return tuple(policy["route_gates"][route])


def managed_capability_report(*, parallel: bool = False) -> dict:
    """Return an explicit local probe fixture; callers must actively verify it."""
    probes = sorted(MANAGED_BASE_PROBES | MANAGED_BUDGET_PROBES | ({"parallel_leases"} if parallel else set()))
    return {
        "managed_runner": True,
        "managed_parallel": parallel,
        "parallel_eligible": parallel,
        "probe_generation": "local-active-probe-v1",
        "active_probes": probes,
    }


def resolve_delivery_selection(
    request: IntakeRequest,
    policy: dict | None = None,
    evidence: dict | None = None,
    capability_report: dict | None = None,
) -> DeliverySelection:
    policy = policy or load_policy()
    validate_policy(policy)
    evidence = evidence if isinstance(evidence, dict) else {}
    intent = _infer_intent(request)
    paths = tuple(_repo_rel(path) for path in request.affected_paths)
    if len(set(paths)) != len(paths):
        raise DeliveryPolicyError("ScopeUnbounded: duplicate affected paths are not a concrete scope")
    symlink_paths = {str(item) for item in evidence.get("symlink_paths", []) if isinstance(item, str)}
    if symlink_paths.intersection(paths):
        raise DeliveryPolicyError("ScopeUnbounded: scope contains a symlink path")
    assessment = guru_risk.assess_intake(
        request.description,
        paths,
        commit_requested=request.commit_requested,
        requirements_clear=request.requirements_clear,
        coupling=request.coupling,
        reversible=request.reversible,
        verification_scope=request.verification_scope,
    )
    risk = guru_contract.normalize_risk(evidence.get("risk") or assessment.get("risk"))
    recommended = guru_contract.normalize_route(assessment.get("route")) or guru_contract.recommended_route_for_risk(risk)
    high_signals = set(assessment.get("risk_flags") or [])
    high_signals.update(str(flag) for flag in evidence.get("high_signals", []) if flag)
    unknown_high_signal = "unknown-high-signal" in high_signals or "unknown_high_signal" in high_signals
    if risk == guru_contract.RISK_HIGH or unknown_high_signal:
        recommended = guru_contract.ROUTE_FULL_CHAIN
    route, selection_source, selection_generation, promotion_reasons = _resolve_route_transition(
        request,
        assessment,
        recommended,
        force_full=risk == guru_contract.RISK_HIGH or unknown_high_signal,
    )
    if intent in READ_ONLY_INTENTS:
        write_capability = "none"
    else:
        write_capability = policy["intent_profiles"][intent]["write_capability"]
    if intent in READ_ONLY_INTENTS and write_capability != "none":
        raise DeliveryPolicyError("RouteIllegalForIntent: read-only intent cannot write")
    scope_max_files: int | None = None
    if route == guru_contract.ROUTE_MICRO_TASK:
        if not paths:
            raise DeliveryPolicyError("ScopeUnbounded: micro_task requires explicit affected paths")
        scope_max_files = request.max_files if request.max_files is not None else len(paths)
        if not isinstance(scope_max_files, int) or isinstance(scope_max_files, bool) or scope_max_files <= 0:
            raise DeliveryPolicyError("ScopeUnbounded: micro_task max_files must be a positive integer")
        if scope_max_files < len(paths):
            raise DeliveryPolicyError("ScopeUnbounded: micro_task max_files is smaller than concrete scope")
    scope_payload = {
        "paths": sorted(paths),
        "intent": intent,
        "requested_max_files": request.max_files,
        "requirements_clear": request.requirements_clear,
        "coupling": str(request.coupling).strip().lower().replace("-", "_"),
        "reversible": request.reversible,
        "verification_scope": str(request.verification_scope).strip().lower().replace("-", "_"),
        "layers": sorted(str(item) for item in evidence.get("layers", []) if item),
        "contracts": sorted(str(item) for item in evidence.get("contracts", []) if item),
    }
    scope_fingerprint = _digest(scope_payload)
    target_digest = evidence.get("target_digest")
    consistency_digest = evidence.get("docs_code_test_digest")
    evidence_cache_key = None
    if HEX_DIGEST.fullmatch(str(target_digest or "")) and HEX_DIGEST.fullmatch(str(consistency_digest or "")):
        evidence_cache_key = _digest({
            "policy_version": policy["policy_version"],
            "intent": intent,
            "execution_route": route,
            "scope_fingerprint": scope_fingerprint,
            "target_digest": target_digest,
            "docs_code_test_digest": consistency_digest,
        })
    reuse = policy.get("evidence_reuse") if isinstance(policy.get("evidence_reuse"), dict) else {}
    candidate = evidence.get("reuse_candidate") if isinstance(evidence.get("reuse_candidate"), dict) else {}
    evidence_reused = bool(
        evidence_cache_key
        and candidate.get("evidence_cache_key") == evidence_cache_key
        and candidate.get("target_digest") == target_digest
        and candidate.get("docs_code_test_digest") == consistency_digest
        and candidate.get("outcome") == reuse.get("required_outcome", "passed")
    )
    ratio = int(reuse.get("max_planning_cost_ratio_percent", 70)) if evidence_reused else 100
    budget = dict(policy["route_profiles"][route])
    if write_capability == "none":
        budget = _min_budget(budget, policy["route_profiles"]["read_only_cap"])
    if evidence_reused:
        for key in reuse.get("cost_budget_keys", []):
            if key in budget:
                budget[key] = max(1, budget[key] * ratio // 100)
    topology, enforcement, capability_probe_digest = _resolve_topology(route, capability_report)
    first_kind = policy["intent_profiles"][intent]["first_value_kind"]
    first_metric = "first_code" if first_kind == "first_scoped_code_diff" else (
        "first_accepted_artifact" if first_kind == "first_accepted_artifact" else "first_verified_evidence"
    )
    required_gates = _required_gates(policy, intent, route)
    route_acceptance = {
        "ttfc_seconds": budget["first_value_deadline_seconds"],
        "pre_risk_required": risk == guru_contract.RISK_HIGH,
        "confirmation_limit": budget["confirmation_batches"],
        "autonomous_close": budget["confirmation_batches"] <= 1,
        "evidence_reuse": True,
        "docs_code_test_consistency": "deterministic_final" in required_gates,
        "gate_rework": "bounded",
        "metrics_enforcement": "advisory" if route == guru_contract.ROUTE_LITE_TASK else "enforced",
        "provider": "codex",
        "claude_forbidden": True,
        "brainstorm_mode": "conditional" if route == guru_contract.ROUTE_LITE_TASK else "not_required",
        "brainstorm_required": bool(assessment.get("brainstorm_required")) if route == guru_contract.ROUTE_LITE_TASK else False,
    }
    return DeliverySelection(
        intent=intent,
        execution_route=route,
        risk=risk,
        first_value_metric=first_metric,
        first_value_kind=first_kind,
        write_capability=write_capability,
        required_artifacts=_required_artifacts(intent, route),
        required_gate_ids=required_gates,
        terminal_conditions=("first_value_deadline", "terminal_deadline", "budget_exceeded", "required_gate_failed"),
        resolved_budget=budget,
        scope_fingerprint=scope_fingerprint,
        policy_version=policy["policy_version"],
        promotion_reasons=tuple(promotion_reasons),
        topology=topology,
        enforcement_mode=enforcement,
        scope_max_files=scope_max_files,
        capability_probe_digest=capability_probe_digest,
        evidence_cache_key=evidence_cache_key,
        evidence_reused=evidence_reused,
        planning_cost_ratio_percent=ratio,
        route_acceptance=route_acceptance,
        delivery_metrics=DELIVERY_METRICS,
        recommended_route=recommended,
        selected_route=route,
        selection_source=selection_source,
        selection_generation=selection_generation,
        brainstorm_required=route_acceptance["brainstorm_required"],
    )


def resolve_project_delivery_selection(
    request: IntakeRequest,
    project_root: str,
    policy: dict | None = None,
    *,
    capability_report: dict | None = None,
) -> DeliverySelection:
    """Resolve through the official project entrypoint and reuse exact passed evidence."""
    policy = policy or load_policy()
    report = capability_report if capability_report is not None else managed_capability_report()
    paths = tuple(_repo_rel(path) for path in request.affected_paths)
    evidence = _project_evidence_inputs(project_root, paths)
    cold = resolve_delivery_selection(
        request,
        policy,
        evidence=evidence,
        capability_report=report,
    )
    if not cold.evidence_cache_key:
        return cold
    candidate = _find_project_reuse_candidate(
        project_root,
        evidence_cache_key=cold.evidence_cache_key,
        target_digest=evidence["target_digest"],
        docs_code_test_digest=evidence["docs_code_test_digest"],
    )
    if candidate is None:
        return cold
    return resolve_delivery_selection(
        request,
        policy,
        evidence={**evidence, "reuse_candidate": candidate},
        capability_report=report,
    )


def policy_snapshot_digest(selection: DeliverySelection) -> str:
    return _digest({
        "policy_version": selection.policy_version,
        "required_gate_ids": selection.required_gate_ids,
        "budget": selection.resolved_budget,
        "topology": selection.topology,
        "enforcement_mode": selection.enforcement_mode,
        "capability_probe_digest": selection.capability_probe_digest,
    })


def _require_digest(name: str, value: str) -> None:
    if not isinstance(value, str) or not HEX_DIGEST.fullmatch(value):
        raise DeliveryPolicyError(f"RiskPacketIncomplete: {name} must be a sha256 digest")


def canonical_decision_universe(
    decisions: tuple[dict, ...],
    invariant_ids: tuple[str, ...],
) -> tuple[dict, ...]:
    """Validate the complete detail-bound critical/high decision inventory."""
    try:
        return guru_contract.canonical_decision_universe(decisions, invariant_ids)
    except guru_contract.ContractError as exc:
        message = str(exc).replace("RISK_DECISION_INVENTORY_INVALID", "RiskPacketIncomplete")
        raise DeliveryPolicyError(message) from exc


def build_risk_packet(
    selection: DeliverySelection,
    decisions: tuple[dict, ...] = (),
    artifact_digest: str = "",
    *,
    detail_artifact_digest: str = "",
    task_id: str = "",
    slice_id: str = "",
    slice_packet_digest: str = "",
    invariant_ids: tuple[str, ...] = (),
) -> dict:
    if selection.execution_route != guru_contract.ROUTE_FULL_CHAIN:
        raise DeliveryPolicyError("RouteIllegalForRisk: risk packets are Full-only")
    for name, value in {
        "artifact_digest": artifact_digest,
        "detail_artifact_digest": detail_artifact_digest,
        "slice_packet_digest": slice_packet_digest,
    }.items():
        _require_digest(name, value)
    if not task_id.strip() or not slice_id.strip() or not invariant_ids:
        raise DeliveryPolicyError("RiskPacketIncomplete: task, slice and invariant bindings are required")
    universe = canonical_decision_universe(decisions, invariant_ids)
    blocking = [item for item in universe if item["status"] == "unresolved"]
    return {
        "schema_version": SCHEMA_VERSION,
        "packet_id": f"risk-{selection.scope_fingerprint[:16]}",
        "task_id": task_id,
        "slice_id": slice_id,
        "slice_packet_digest": slice_packet_digest,
        "owner_unit": "UNIT-delivery-policy",
        "intent": selection.intent,
        "route": selection.execution_route,
        "risk": selection.risk,
        "scope_fingerprint": selection.scope_fingerprint,
        "artifact_digest": artifact_digest,
        "detail_artifact_digest": detail_artifact_digest,
        "policy_version": selection.policy_version,
        "policy_snapshot_digest": policy_snapshot_digest(selection),
        "decision_universe_digest": _digest(universe),
        "decision_items": blocking,
        "decision_set_digest": _digest(blocking),
        "confirmation_required": selection.risk == guru_contract.RISK_HIGH,
        "pre_write_required": True,
        "invariant_ids": sorted(set(invariant_ids)),
    }


def build_execution_envelope(
    selection: DeliverySelection,
    *,
    task_id: str | None = None,
    slice_id: str | None = None,
    slice_packet_digest: str | None = None,
    risk_packet_digest: str | None = None,
    confirmation_attestation_digest: str | None = None,
    requirements_digest: str | None = None,
    confirmation_required: bool = False,
    selection_generation: int | None = None,
) -> dict:
    route = selection.execution_route
    writable = selection.write_capability != "none"
    confirmation_required = confirmation_required or (
        writable
        and (
            route == guru_contract.ROUTE_LITE_TASK
            or (route == guru_contract.ROUTE_FULL_CHAIN and selection.risk == guru_contract.RISK_HIGH)
        )
    )
    if selection_generation is None:
        selection_generation = selection.selection_generation
    if not isinstance(selection_generation, int) or isinstance(selection_generation, bool) or selection_generation <= 0:
        raise DeliveryPolicyError("EnvelopeFieldIllegal: selection_generation must be positive")
    if route == guru_contract.ROUTE_SMALL_INLINE and any([task_id, slice_id, slice_packet_digest, risk_packet_digest, confirmation_attestation_digest, requirements_digest]):
        raise DeliveryPolicyError("EnvelopeFieldIllegal: small_inline cannot carry task or Full bindings")
    if route == guru_contract.ROUTE_MICRO_TASK and any([slice_id, slice_packet_digest, risk_packet_digest, confirmation_attestation_digest, requirements_digest]):
        raise DeliveryPolicyError("EnvelopeFieldIllegal: micro_task cannot carry slice/packet/risk/confirmation bindings")
    if route == guru_contract.ROUTE_LITE_TASK:
        if writable and not task_id:
            raise DeliveryPolicyError("EnvelopeFieldIllegal: writable lite_task requires task_id")
        if writable and not HEX_DIGEST.fullmatch(str(requirements_digest or "")):
            raise DeliveryPolicyError("EnvelopeFieldIllegal: writable lite_task requires a sha256 requirements_digest")
        if slice_packet_digest or risk_packet_digest:
            raise DeliveryPolicyError("EnvelopeFieldIllegal: lite_task cannot carry Full packet/risk bindings")
    if route == guru_contract.ROUTE_FULL_CHAIN:
        missing = ["task_id"] if not task_id else []
        if writable:
            missing.extend(name for name, value in {
                "slice_id": slice_id,
                "slice_packet_digest": slice_packet_digest,
                "risk_packet_digest": risk_packet_digest,
            }.items() if not value)
        elif slice_packet_digest:
            raise DeliveryPolicyError("EnvelopeFieldIllegal: read-only Full cannot carry a writable slice packet")
        if missing:
            raise DeliveryPolicyError("EnvelopeFieldIllegal: full_chain missing " + ", ".join(missing))
        for name, value in {
            "slice_packet_digest": slice_packet_digest,
            "risk_packet_digest": risk_packet_digest,
        }.items():
            if writable and not HEX_DIGEST.fullmatch(str(value or "")):
                raise DeliveryPolicyError(f"EnvelopeFieldIllegal: {name} must be a sha256 digest")
    if confirmation_required and not confirmation_attestation_digest:
        raise DeliveryPolicyError("EnvelopeFieldIllegal: current confirmation attestation is required")
    if confirmation_required and not HEX_DIGEST.fullmatch(str(confirmation_attestation_digest or "")):
        raise DeliveryPolicyError("EnvelopeFieldIllegal: confirmation attestation must be a sha256 digest")
    if not confirmation_required and confirmation_attestation_digest and route != guru_contract.ROUTE_LITE_TASK:
        raise DeliveryPolicyError("EnvelopeFieldIllegal: unexpected confirmation attestation")
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "envelope_id": f"env-{selection.scope_fingerprint[:16]}-{selection_generation}",
        "selection_generation": selection_generation,
        "recommended_route": selection.recommended_route,
        "selected_route": selection.selected_route,
        "selection_source": selection.selection_source,
        "intent": selection.intent,
        "execution_route": route,
        "topology": selection.topology,
        "enforcement_mode": selection.enforcement_mode,
        "write_capability": selection.write_capability,
        "scope_fingerprint": selection.scope_fingerprint,
        "scope_max_files": selection.scope_max_files,
        "policy_snapshot_digest": policy_snapshot_digest(selection),
        "required_gate_ids": list(selection.required_gate_ids),
        "budget": selection.resolved_budget,
        "first_value_kind": selection.first_value_kind,
        "terminal_conditions": list(selection.terminal_conditions),
        "confirmation_required": confirmation_required,
        "evidence_cache_key": selection.evidence_cache_key,
        "evidence_reused": selection.evidence_reused,
        "planning_cost_ratio_percent": selection.planning_cost_ratio_percent,
        "route_acceptance": selection.route_acceptance,
        "delivery_metrics": list(selection.delivery_metrics),
    }
    for name, value in {
        "task_id": task_id,
        "slice_id": slice_id,
        "slice_packet_digest": slice_packet_digest,
        "risk_packet_digest": risk_packet_digest,
        "confirmation_attestation_digest": confirmation_attestation_digest,
        "requirements_digest": requirements_digest,
    }.items():
        if value is not None:
            envelope[name] = value
    return envelope


def selection_to_contract_patch(selection: DeliverySelection) -> dict:
    return {
        "execution_policy": {
            "schema_version": SCHEMA_VERSION,
            "policy_version": selection.policy_version,
            "intent": selection.intent,
            "route": selection.execution_route,
            "recommended_route": selection.recommended_route,
            "selected_route": selection.selected_route,
            "selection_source": selection.selection_source,
            "selection_generation": selection.selection_generation,
            "risk": selection.risk,
            "first_value_metric": selection.first_value_metric,
            "required_gate_ids": list(selection.required_gate_ids),
            "budget": selection.resolved_budget,
            "scope_fingerprint": selection.scope_fingerprint,
            "scope_max_files": selection.scope_max_files,
            "topology": selection.topology,
            "enforcement_mode": selection.enforcement_mode,
            "promotion_reasons": list(selection.promotion_reasons),
            "capability_probe_digest": selection.capability_probe_digest,
            "evidence_cache_key": selection.evidence_cache_key,
            "evidence_reused": selection.evidence_reused,
            "planning_cost_ratio_percent": selection.planning_cost_ratio_percent,
            "route_acceptance": selection.route_acceptance,
            "delivery_metrics": list(selection.delivery_metrics),
            "brainstorm_required": selection.brainstorm_required,
        },
        "commit_policy": {
            "require_in_progress": selection.execution_route in {
                guru_contract.ROUTE_LITE_TASK,
                guru_contract.ROUTE_FULL_CHAIN,
            },
            "require_clean_implementation_review": selection.execution_route == guru_contract.ROUTE_FULL_CHAIN,
            "allow_task_artifacts_only": False,
        },
    }


def _request_from_args(args: argparse.Namespace) -> IntakeRequest:
    return IntakeRequest(
        description=args.description or "",
        intent_hint=args.intent,
        affected_paths=tuple(args.path),
        commit_requested=args.commit_requested,
        read_only_requested=args.read_only,
        preferred_route=args.preferred_route,
        max_files=args.max_files,
        requirements_clear=args.requirements_clear,
        coupling=args.coupling,
        reversible=args.reversible,
        verification_scope=args.verification_scope,
        prior_route=args.prior_route,
        prior_selection_generation=args.prior_selection_generation,
        first_write_started=args.first_write_started,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve Guru delivery policy")
    parser.add_argument("--description", default="")
    parser.add_argument("--intent", default=None)
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--commit-requested", action="store_true")
    parser.add_argument("--read-only", action="store_true")
    parser.add_argument("--preferred-route", default=None)
    parser.add_argument("--max-files", type=int, default=None)
    parser.add_argument("--requirements-clear", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--coupling", choices=("local", "cross_layer", "unknown"), default="unknown")
    parser.add_argument("--reversible", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--verification-scope", choices=("focused", "broad", "unknown"), default="unknown")
    parser.add_argument("--prior-route", default=None)
    parser.add_argument("--prior-selection-generation", type=int, default=None)
    parser.add_argument("--first-write-started", action="store_true")
    parser.add_argument("--policy", default=None)
    args = parser.parse_args(argv)
    try:
        policy = load_policy(args.policy)
        selection = resolve_project_delivery_selection(
            _request_from_args(args),
            os.getcwd(),
            policy,
            capability_report=managed_capability_report(parallel=True),
        )
        print(_canonical_json(dataclasses.asdict(selection)))
        return 0
    except DeliveryPolicyError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
