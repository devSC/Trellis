#!/usr/bin/env python3
"""Guru task-local gate contract and degradation helpers.

This module owns the JSON contract boundary for `gate-contract.json`,
`gate-degradations.jsonl`, and `gate-evidence/`.  It intentionally does not
import guru_gate to avoid cycles; callers pass staged paths and risk helpers in.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

SCHEMA_VERSION = 1
CONTRACT_FILE = "gate-contract.json"
DEGRADATIONS_FILE = "gate-degradations.jsonl"
EVIDENCE_DIR = "gate-evidence"
POLICY_VERSION_V1 = "guru-risk-contract-v1"
POLICY_VERSION_V2 = "guru-risk-contract-v2"
DECISION_INVENTORY_START = "<!-- GURU:RISK_DECISION_INVENTORY:START -->"
DECISION_INVENTORY_END = "<!-- GURU:RISK_DECISION_INVENTORY:END -->"

ROUTE_SMALL_INLINE = "small_inline"
ROUTE_MICRO_TASK = "micro_task"
ROUTE_LITE_TASK = "lite_task"
ROUTE_FULL_CHAIN = "full_chain"
ROUTES = {ROUTE_SMALL_INLINE, ROUTE_MICRO_TASK, ROUTE_LITE_TASK, ROUTE_FULL_CHAIN}
ROUTE_RANK = {
    ROUTE_SMALL_INLINE: 0,
    ROUTE_MICRO_TASK: 1,
    ROUTE_LITE_TASK: 2,
    ROUTE_FULL_CHAIN: 3,
}

RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_UNKNOWN = "unknown"
RISKS = {RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_UNKNOWN}

HIGH_RISK_ALIASES = {"high", "critical", "p0"}
LOW_RISK_ALIASES = {"low", "minor", "trivial"}
MEDIUM_RISK_ALIASES = {"medium", "moderate", "normal", "p1", "p2"}
RISK_ALIASES = HIGH_RISK_ALIASES | MEDIUM_RISK_ALIASES | LOW_RISK_ALIASES | {RISK_UNKNOWN}

OPTIONAL_DEGRADABLE_GATES = {
    "gitnexus_impact": {"micro_task", "lite_task"},
    "gitnexus_detect_changes": {"micro_task", "lite_task"},
    "semantic_review_optional": {"lite_task"},
}

REQUIRED_NON_DEGRADABLE_GATES = {
    "requirements_review",
    "overview_review",
    "detail_review",
    "implementation_review",
    "check_commit",
}

HIGH_RISK_PATH_KEYWORDS = (
    ".trellis/workflow.md",
    ".trellis/config.yaml",
    ".codex/",
    ".claude/",
    "hooks/",
    "/hooks/",
    "workflow",
    "guru_gate.py",
    "guru_risk.py",
    "guru_contract.py",
    "guru_supervise.py",
    "schema",
    "migration",
    "payment",
    "ads",
    "permission",
    "privacy",
)


class ContractError(Exception):
    """Raised for unrecoverable contract read/write errors."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_risk(value) -> str:
    if not isinstance(value, str):
        return RISK_UNKNOWN
    risk = value.strip().lower().replace("_", "-")
    if risk in HIGH_RISK_ALIASES:
        return RISK_HIGH
    if risk in MEDIUM_RISK_ALIASES:
        return RISK_MEDIUM
    if risk in LOW_RISK_ALIASES:
        return RISK_LOW
    if risk == RISK_UNKNOWN:
        return RISK_UNKNOWN
    return RISK_UNKNOWN


def raw_risk_problem(value) -> str:
    if not isinstance(value, str) or not value.strip():
        return "risk must be low|medium|high|unknown"
    risk = value.strip().lower().replace("_", "-")
    if risk not in RISK_ALIASES:
        return f"risk has unknown value: {value}"
    return ""


def normalize_route(value) -> str:
    if not isinstance(value, str):
        return ""
    route = value.strip().lower().replace("-", "_")
    return route if route in ROUTES else ""


def recommended_route_for_risk(risk: str) -> str:
    risk = normalize_risk(risk)
    if risk == RISK_HIGH:
        return ROUTE_FULL_CHAIN
    if risk == RISK_MEDIUM:
        return ROUTE_LITE_TASK
    if risk == RISK_LOW:
        return ROUTE_MICRO_TASK
    return ROUTE_FULL_CHAIN


def contract_recommended_route(contract: dict | None) -> str:
    if not isinstance(contract, dict):
        return ""
    selection = contract.get("route_selection")
    if isinstance(selection, dict):
        route = normalize_route(selection.get("recommended_route") or selection.get("from_route"))
        if route:
            return route
    assessment = contract.get("assessment")
    if isinstance(assessment, dict):
        route = normalize_route(assessment.get("recommended_route") or assessment.get("recommended_contract"))
        if route:
            return route
    return normalize_route(contract.get("recommended_route"))


def contract_path(task_dir: str) -> str:
    return os.path.join(task_dir, CONTRACT_FILE)


def degradations_path(task_dir: str) -> str:
    return os.path.join(task_dir, DEGRADATIONS_FILE)


def load_contract(task_dir: str) -> tuple[dict | None, str]:
    path = contract_path(task_dir)
    if not os.path.isfile(path):
        return None, ""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        return None, f"cannot read {CONTRACT_FILE}: {exc}"
    if not isinstance(data, dict):
        return None, f"{CONTRACT_FILE} root must be object"
    return data, ""


def write_contract(task_dir: str, contract: dict) -> None:
    os.makedirs(task_dir, exist_ok=True)
    path = contract_path(task_dir)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(contract, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def default_contract(route: str, risk: str, *, created_by: str = "intake") -> dict:
    route = normalize_route(route)
    risk = normalize_risk(risk)
    recommended_route = recommended_route_for_risk(risk)
    if route == ROUTE_FULL_CHAIN:
        require_in_progress = True
        require_clean_review = True
    elif route == ROUTE_LITE_TASK:
        require_in_progress = True
        require_clean_review = True
    elif route == ROUTE_MICRO_TASK:
        require_in_progress = False
        require_clean_review = False
    else:
        require_in_progress = False
        require_clean_review = False
    return {
        "schema_version": SCHEMA_VERSION,
        "risk": risk,
        "route": route,
        "assessment": {
            "confidence": None,
            "reasons": [],
            "risk_flags": [],
            "recommended_route": recommended_route,
        },
        "route_selection": {
            "selected_route": route,
            "source": "recommended",
            "recommended_route": recommended_route,
            "risk_acknowledged": False,
            "user_quote": "",
            "selected_by": "system",
            "selected_at": _now_iso(),
        },
        "scope": {
            "allowed_paths": [],
            "forbidden_path_patterns": [],
            "max_files": None,
        },
        "required_gates": [],
        "optional_gates": [],
        "allowed_degradations": [],
        "commit_policy": {
            "require_in_progress": require_in_progress,
            "require_clean_implementation_review": require_clean_review,
            "allow_task_artifacts_only": False,
        },
        "risk_decision_inventory": {
            "schema_version": 1,
            "required": route == ROUTE_FULL_CHAIN and risk in {RISK_HIGH, RISK_UNKNOWN},
            "source": "implement.md",
        },
        "created_by": created_by,
        "created_at": _now_iso(),
        "policy_version": POLICY_VERSION_V2,
    }


def contract_route(contract: dict | None) -> str:
    if not isinstance(contract, dict):
        return ""
    return normalize_route(contract.get("route"))


def contract_risk(contract: dict | None) -> str:
    if not isinstance(contract, dict):
        return RISK_UNKNOWN
    return normalize_risk(contract.get("risk"))


def decision_inventory_policy_problem(contract: dict | None) -> str:
    """Return a v2 inventory policy error without changing legacy v1 behavior."""
    if not isinstance(contract, dict) or contract.get("policy_version") != POLICY_VERSION_V2:
        return ""
    policy = contract.get("risk_decision_inventory")
    if not isinstance(policy, dict):
        return "RISK_DECISION_INVENTORY_POLICY_INVALID: v2 contract requires risk_decision_inventory"
    if policy.get("schema_version") != 1 or policy.get("source") != "implement.md":
        return "RISK_DECISION_INVENTORY_POLICY_INVALID: expected schema_version=1 and source=implement.md"
    should_require = (
        contract_route(contract) == ROUTE_FULL_CHAIN
        and contract_risk(contract) in {RISK_HIGH, RISK_UNKNOWN}
    )
    if policy.get("required") is not should_require:
        return "RISK_DECISION_INVENTORY_POLICY_INVALID: required flag disagrees with route/risk"
    return ""


def decision_inventory_required(contract: dict | None) -> bool:
    return (
        decision_inventory_policy_problem(contract) == ""
        and isinstance(contract, dict)
        and contract.get("policy_version") == POLICY_VERSION_V2
        and isinstance(contract.get("risk_decision_inventory"), dict)
        and contract["risk_decision_inventory"].get("required") is True
    )


def canonical_decision_universe(
    raw_items,
    invariant_ids,
    *,
    artifact_text_by_key: dict | None = None,
) -> tuple[dict, ...]:
    """Validate and canonicalize one slice's required critical/high decisions."""
    if not isinstance(raw_items, (list, tuple)):
        raise ContractError("RISK_DECISION_INVENTORY_INVALID: slice decisions must be an array")
    allowed_invariants = set(invariant_ids)
    universe = []
    seen_ids = set()
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: decision entries must be objects")
        item = dict(raw)
        fields = (
            "decision_id",
            "severity",
            "status",
            "recommendation",
            "alternatives",
            "impact",
            "irreversible",
            "invariant_ids",
            "required",
        )
        if any(field not in item for field in fields):
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: decision shape is incomplete")
        decision_id = item["decision_id"]
        if (
            not isinstance(decision_id, str)
            or not decision_id.strip()
            or decision_id in seen_ids
        ):
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: decision ids must be unique non-empty strings")
        seen_ids.add(decision_id)
        if item["required"] is not True or item["severity"] not in {"critical", "high"}:
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: only required critical/high decisions are allowed")
        if item["status"] not in {"unresolved", "resolved"}:
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: decision status must be unresolved or resolved")
        if not isinstance(item["irreversible"], bool):
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: irreversible must be boolean")
        if not all(
            isinstance(item[field], str) and item[field].strip()
            for field in ("recommendation", "impact")
        ):
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: decision text fields must be non-empty")
        alternatives = item["alternatives"]
        if (
            not isinstance(alternatives, list)
            or not alternatives
            or not all(isinstance(value, str) and value.strip() for value in alternatives)
        ):
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: alternatives must be non-empty strings")
        item_invariants = item["invariant_ids"]
        if (
            not isinstance(item_invariants, list)
            or not item_invariants
            or not all(isinstance(value, str) and value.strip() for value in item_invariants)
            or not set(item_invariants).issubset(allowed_invariants)
        ):
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: invariant bindings are invalid")
        resolution = item.get("resolution")
        if item["status"] == "resolved":
            if not isinstance(resolution, dict) or not all(
                isinstance(resolution.get(field), str) and resolution[field].strip()
                for field in ("choice", "evidence")
            ):
                raise ContractError("RISK_DECISION_INVENTORY_INVALID: resolved decisions need choice/evidence")
        elif resolution not in (None, {}):
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: unresolved decisions cannot carry resolution")

        if artifact_text_by_key is not None:
            source_refs = item.get("source_refs")
            if not isinstance(source_refs, list) or not source_refs:
                raise ContractError("RISK_DECISION_INVENTORY_INVALID: every decision needs source_refs")
            canonical_refs = []
            seen_refs = set()
            for ref in source_refs:
                if not isinstance(ref, dict) or set(ref) != {"artifact_key", "anchor"}:
                    raise ContractError("RISK_DECISION_INVENTORY_INVALID: source_refs need artifact_key/anchor")
                artifact_key = ref.get("artifact_key")
                anchor = ref.get("anchor")
                if (
                    not isinstance(artifact_key, str)
                    or artifact_key not in artifact_text_by_key
                    or not isinstance(anchor, str)
                    or decision_id not in anchor
                ):
                    raise ContractError("RISK_DECISION_INVENTORY_INVALID: source_ref is not detail-bound")
                pair = (artifact_key, anchor)
                if pair in seen_refs or artifact_text_by_key[artifact_key].count(anchor) != 1:
                    raise ContractError("RISK_DECISION_INVENTORY_INVALID: source_ref anchor must exist exactly once")
                seen_refs.add(pair)
                canonical_refs.append({"artifact_key": artifact_key, "anchor": anchor})
            item["source_refs"] = sorted(canonical_refs, key=lambda row: (row["artifact_key"], row["anchor"]))
        universe.append(item)
    universe.sort(key=lambda item: item["decision_id"])
    return tuple(universe)


def load_detail_decision_inventory(
    task_dir: str,
    task_id: str,
    artifacts: list,
    *,
    expected_slice_id: str | None = None,
) -> dict:
    """Load the unique detail-bound inventory and validate every declared slice."""
    artifact_path_by_key = {}
    for entry in artifacts:
        if not isinstance(entry, dict):
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: detail artifact row is malformed")
        key = entry.get("key")
        path = entry.get("path")
        if not isinstance(key, str) or not isinstance(path, str) or key in artifact_path_by_key:
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: detail artifact keys are invalid")
        artifact_path_by_key[key] = path
    implement_path = artifact_path_by_key.get("task:implement.md") or artifact_path_by_key.get("implement.md")
    if implement_path is None:
        raise ContractError("RISK_DECISION_INVENTORY_MISSING: implement.md is not in detail artifacts")
    try:
        with open(implement_path, encoding="utf-8") as fh:
            implement = fh.read()
    except OSError as exc:
        raise ContractError("RISK_DECISION_INVENTORY_MISSING: cannot read task:implement.md") from exc
    artifact_text_by_key = {}
    for key, path in artifact_path_by_key.items():
        if key in {
            "prd.md",
            "design.md",
            "implement.md",
            "task:prd.md",
            "task:design.md",
            "task:implement.md",
        }:
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                artifact_text_by_key[key] = fh.read()
        except OSError as exc:
            raise ContractError(f"RISK_DECISION_INVENTORY_INVALID: cannot read detail artifact {key}") from exc
    if implement.count(DECISION_INVENTORY_START) != 1 or implement.count(DECISION_INVENTORY_END) != 1:
        raise ContractError("RISK_DECISION_INVENTORY_MISSING: markers must appear exactly once")
    start = implement.index(DECISION_INVENTORY_START) + len(DECISION_INVENTORY_START)
    end = implement.index(DECISION_INVENTORY_END, start)
    lines = [line.rstrip() for line in implement[start:end].strip().splitlines()]
    if (
        len(lines) < 3
        or lines[0].strip() != "```json"
        or lines[-1].strip() != "```"
        or any(line.strip().startswith("```") for line in lines[1:-1])
    ):
        raise ContractError("RISK_DECISION_INVENTORY_INVALID: expected one JSON fence")
    try:
        inventory = json.loads("\n".join(lines[1:-1]))
    except json.JSONDecodeError as exc:
        raise ContractError("RISK_DECISION_INVENTORY_INVALID: JSON cannot be parsed") from exc
    if not isinstance(inventory, dict) or set(inventory) != {"schema_version", "task_id", "scope", "slices"}:
        raise ContractError("RISK_DECISION_INVENTORY_INVALID: root shape is invalid")
    if inventory.get("schema_version") != 1 or inventory.get("task_id") != task_id:
        raise ContractError("RISK_DECISION_INVENTORY_INVALID: schema/task binding is invalid")
    scope = inventory.get("scope")
    expected_scope_keys = {
        "selected_slice_id",
        "official_start_authority",
        "later_slice_authority",
    }
    if not isinstance(scope, dict) or set(scope) != expected_scope_keys:
        raise ContractError("RISK_DECISION_INVENTORY_INVALID: scope shape is invalid")
    selected_slice_id = scope.get("selected_slice_id")
    if (
        not isinstance(selected_slice_id, str)
        or not selected_slice_id
        or scope.get("official_start_authority") != "selected_slice_only"
        or scope.get("later_slice_authority") != "supervisor_fail_closed"
        or (expected_slice_id is not None and selected_slice_id != expected_slice_id)
    ):
        raise ContractError("RISK_DECISION_INVENTORY_INVALID: selected-slice authority is invalid")
    slices = inventory.get("slices")
    if not isinstance(slices, dict) or selected_slice_id not in slices:
        raise ContractError("RISK_DECISION_INVENTORY_INVALID: selected slice is absent")

    universes = {}
    all_decision_ids = set()
    for slice_id, raw_items in slices.items():
        if not isinstance(slice_id, str) or not slice_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for ch in slice_id):
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: slice id is invalid")
        packet_path = os.path.join(task_dir, "slice-packets", f"{slice_id}.json")
        try:
            with open(packet_path, encoding="utf-8") as fh:
                packet = json.load(fh)
        except (OSError, ValueError) as exc:
            raise ContractError(f"RISK_DECISION_INVENTORY_INVALID: slice packet missing/invalid: {slice_id}") from exc
        if not isinstance(packet, dict) or packet.get("slice_id") != slice_id:
            raise ContractError(f"RISK_DECISION_INVENTORY_INVALID: slice packet binding mismatch: {slice_id}")
        invariant_ids = [
            row.get("invariant_id")
            for row in packet.get("invariants", [])
            if isinstance(row, dict) and isinstance(row.get("invariant_id"), str) and row.get("invariant_id")
        ]
        if len(invariant_ids) != len(packet.get("invariants", [])) or len(invariant_ids) != len(set(invariant_ids)):
            raise ContractError(f"RISK_DECISION_INVENTORY_INVALID: packet invariants invalid: {slice_id}")
        universe = canonical_decision_universe(
            raw_items,
            invariant_ids,
            artifact_text_by_key=artifact_text_by_key,
        )
        decision_ids = {item["decision_id"] for item in universe}
        if all_decision_ids & decision_ids:
            raise ContractError("RISK_DECISION_INVENTORY_INVALID: decision ids must be unique across slices")
        all_decision_ids.update(decision_ids)
        universes[slice_id] = universe
    return {
        "inventory": inventory,
        "selected_slice_id": selected_slice_id,
        "decision_universe": universes[selected_slice_id],
        "universes": universes,
    }


def _route_rank(route: str) -> int:
    return ROUTE_RANK.get(normalize_route(route), -1)


def _route_override_required(contract: dict) -> bool:
    route = contract_route(contract)
    risk = contract_risk(contract)
    recommended = contract_recommended_route(contract)
    if recommended and _route_rank(route) < _route_rank(recommended):
        return True
    if risk == RISK_HIGH and route != ROUTE_FULL_CHAIN:
        return True
    if risk == RISK_MEDIUM and route in {ROUTE_SMALL_INLINE, ROUTE_MICRO_TASK}:
        return True
    return False


def user_route_override_problems(contract: dict | None) -> list:
    if not isinstance(contract, dict):
        return ["gate contract missing or malformed"]
    route = contract_route(contract)
    selection = contract.get("route_selection")
    if not isinstance(selection, dict):
        return ["route_selection user override audit is required for lower-than-recommended route"]
    problems = []
    selected_route = normalize_route(selection.get("selected_route"))
    if selected_route != route:
        problems.append("route_selection.selected_route must match route")
    source = str(selection.get("source") or "").strip().lower()
    if source != "user_override":
        problems.append("route_selection.source must be user_override")
    selected_by = str(selection.get("selected_by") or selection.get("by") or "").strip().lower()
    if selected_by != "user":
        problems.append("route_selection.selected_by must be user")
    if selection.get("risk_acknowledged") is not True:
        problems.append("route_selection.risk_acknowledged must be true")
    user_quote = selection.get("user_quote")
    if not isinstance(user_quote, str) or not user_quote.strip():
        problems.append("route_selection.user_quote must be non-empty")
    selected_at = selection.get("selected_at")
    if not isinstance(selected_at, str) or not selected_at.strip():
        problems.append("route_selection.selected_at must be non-empty")
    recommended = normalize_route(selection.get("recommended_route") or selection.get("from_route"))
    if not recommended:
        problems.append("route_selection.recommended_route must be valid")
    elif _route_rank(route) >= _route_rank(recommended):
        problems.append("route_selection must record a stricter recommended_route than route")
    return problems


def has_user_route_override(contract: dict | None) -> bool:
    return not user_route_override_problems(contract)


def _list_of_strings(value, field: str, problems: list) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        problems.append(f"{field} must be an array")
        return []
    out = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            problems.append(f"{field} must contain non-empty strings")
            continue
        out.append(item.strip())
    return out


def _allowed_degradation_map(contract: dict, problems: list) -> dict:
    route = contract_route(contract)
    rows = contract.get("allowed_degradations", [])
    if rows is None:
        rows = []
    if not isinstance(rows, list):
        problems.append("allowed_degradations must be an array")
        return {}
    allowed = {}
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            problems.append(f"allowed_degradations[{idx}] must be object")
            continue
        gate = row.get("gate")
        if not isinstance(gate, str) or not gate.strip():
            problems.append(f"allowed_degradations[{idx}].gate missing")
            continue
        gate = gate.strip()
        if gate in REQUIRED_NON_DEGRADABLE_GATES:
            problems.append(f"{gate} is a required gate and cannot be degraded")
            continue
        if route not in OPTIONAL_DEGRADABLE_GATES.get(gate, set()):
            problems.append(f"{gate} degradation is not globally allowed for route={route}")
            continue
        fallbacks = _list_of_strings(row.get("fallback_checks"), f"allowed_degradations[{idx}].fallback_checks", problems)
        if not fallbacks:
            problems.append(f"allowed_degradations[{idx}].fallback_checks must contain at least one check")
        allowed[gate] = {"row": row, "fallback_checks": fallbacks}
    return allowed


def validate_contract(contract: dict | None) -> list:
    problems = []
    if not isinstance(contract, dict):
        return ["gate contract missing or malformed"]
    if contract.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version must be {SCHEMA_VERSION}")
    route = contract_route(contract)
    risk = contract_risk(contract)
    risk_problem = raw_risk_problem(contract.get("risk"))
    if risk_problem:
        problems.append(risk_problem)
    if not route:
        problems.append("route must be small_inline|micro_task|lite_task|full_chain")
    if risk not in RISKS:
        problems.append("risk must be low|medium|high|unknown")
    if route == ROUTE_SMALL_INLINE:
        problems.append("small_inline cannot be used as a commit contract; use micro_task when committing")
    selection = contract.get("route_selection")
    if selection is not None and not isinstance(selection, dict):
        problems.append("route_selection must be object")
    if route and _route_override_required(contract):
        problems.extend(user_route_override_problems(contract))
    scope = contract.get("scope", {})
    if scope is not None and not isinstance(scope, dict):
        problems.append("scope must be object")
        scope = {}
    _list_of_strings(scope.get("allowed_paths"), "scope.allowed_paths", problems)
    _list_of_strings(scope.get("forbidden_path_patterns"), "scope.forbidden_path_patterns", problems)
    max_files = scope.get("max_files")
    if max_files is not None and (not isinstance(max_files, int) or max_files <= 0):
        problems.append("scope.max_files must be a positive integer or null")
    if route == ROUTE_MICRO_TASK:
        allowed_paths = _list_of_strings(scope.get("allowed_paths"), "scope.allowed_paths", problems)
        normalized_allowed = [_normalize_path(path) for path in allowed_paths]
        if not normalized_allowed:
            problems.append("micro_task contract requires explicit non-empty scope.allowed_paths")
        if "." in normalized_allowed or "" in normalized_allowed:
            problems.append("micro_task scope.allowed_paths cannot include repo root")
        if not isinstance(max_files, int) or max_files <= 0:
            problems.append("micro_task contract requires positive scope.max_files")
    policy = contract.get("commit_policy", {})
    if policy is not None and not isinstance(policy, dict):
        problems.append("commit_policy must be object")
    _allowed_degradation_map(contract, problems)
    return problems


def read_degradations(task_dir: str) -> tuple[list, str]:
    path = degradations_path(task_dir)
    if not os.path.isfile(path):
        return [], ""
    rows = []
    try:
        with open(path, encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, 1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    return [], f"{DEGRADATIONS_FILE} line {lineno} invalid JSON: {exc}"
                if not isinstance(row, dict):
                    return [], f"{DEGRADATIONS_FILE} line {lineno} must be object"
                rows.append(row)
    except OSError as exc:
        return [], f"cannot read {DEGRADATIONS_FILE}: {exc}"
    return rows, ""


def append_degradation(task_dir: str, row: dict) -> None:
    if not isinstance(row, dict):
        raise ContractError("degradation row must be object")
    row = dict(row)
    row.setdefault("schema_version", SCHEMA_VERSION)
    row.setdefault("created_at", _now_iso())
    path = degradations_path(task_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    need_nl = False
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as fh:
            fh.seek(-1, os.SEEK_END)
            need_nl = fh.read(1) != b"\n"
    with open(path, "a", encoding="utf-8") as fh:
        if need_nl:
            fh.write("\n")
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _passed_compensating_checks(row: dict) -> set:
    checks = row.get("compensating_checks", [])
    if not isinstance(checks, list):
        return set()
    passed = set()
    for check in checks:
        if not isinstance(check, dict):
            continue
        name = check.get("name")
        status = str(check.get("status", "")).strip().lower()
        if isinstance(name, str) and name.strip() and status == "passed":
            passed.add(name.strip())
    return passed


def validate_degradations(contract: dict, rows: list) -> list:
    problems = []
    if not isinstance(contract, dict):
        return ["gate contract missing or malformed"]
    allowed = _allowed_degradation_map(contract, problems)
    route = contract_route(contract)
    risk = contract_risk(contract)
    for idx, row in enumerate(rows):
        if row.get("schema_version") != SCHEMA_VERSION:
            problems.append(f"degradation[{idx}] schema_version must be {SCHEMA_VERSION}")
        gate = row.get("gate")
        if not isinstance(gate, str) or not gate.strip():
            problems.append(f"degradation[{idx}] gate missing")
            continue
        gate = gate.strip()
        if gate not in allowed:
            problems.append(f"degradation[{idx}] gate={gate} is not allowed by contract/global policy")
            continue
        if risk == RISK_HIGH or route == ROUTE_FULL_CHAIN:
            problems.append(f"degradation[{idx}] gate={gate} cannot degrade high/full_chain gates")
            continue
        required = set(allowed[gate].get("fallback_checks", []))
        passed = _passed_compensating_checks(row)
        missing = sorted(required - passed)
        if missing:
            problems.append(f"degradation[{idx}] missing passed compensating checks: {', '.join(missing)}")
    return problems


def _normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.strip("/")


def path_in_scope(path: str, allowed_paths: list) -> bool:
    normalized = _normalize_path(path)
    if not allowed_paths:
        return True
    for raw in allowed_paths:
        target = _normalize_path(raw)
        if not target:
            continue
        if target == "." or normalized == target or normalized.startswith(target + "/"):
            return True
    return False


def is_task_artifact_path(path: str, task_dir: str, root: str) -> bool:
    normalized = _normalize_path(path)
    if normalized == ".trellis/tasks" or normalized.startswith(".trellis/tasks/"):
        return True
    if normalized == ".trellis/workspace" or normalized.startswith(".trellis/workspace/"):
        return True
    try:
        task_prefix = os.path.relpath(os.path.realpath(task_dir), os.path.realpath(root)).replace(os.sep, "/").rstrip("/")
    except ValueError:
        task_prefix = ""
    return bool(task_prefix and (normalized == task_prefix or normalized.startswith(task_prefix + "/")))


def high_risk_path_signals(paths: list) -> list:
    signals = []
    for path in paths:
        normalized = _normalize_path(path).lower()
        for keyword in HIGH_RISK_PATH_KEYWORDS:
            if keyword.lower() in normalized:
                signals.append(path)
                break
    return sorted(set(signals))


def validate_commit_contract(contract: dict, staged_paths: list, task_dir: str, root: str) -> list:
    problems = validate_contract(contract)
    if not isinstance(contract, dict):
        return problems
    rows, read_error = read_degradations(task_dir)
    if read_error:
        problems.append(read_error)
        rows = []
    problems.extend(validate_degradations(contract, rows))
    scope = contract.get("scope", {}) if isinstance(contract, dict) else {}
    if not isinstance(scope, dict):
        scope = {}
    allowed_paths = _list_of_strings(scope.get("allowed_paths"), "scope.allowed_paths", problems)
    forbidden_patterns = _list_of_strings(scope.get("forbidden_path_patterns"), "scope.forbidden_path_patterns", problems)
    max_files = scope.get("max_files")
    if isinstance(max_files, int) and max_files > 0 and len(staged_paths) > max_files:
        problems.append(f"staged file count {len(staged_paths)} exceeds contract max_files={max_files}")
    artifact_paths = [p for p in staged_paths if is_task_artifact_path(p, task_dir, root)]
    policy = contract.get("commit_policy", {})
    if not isinstance(policy, dict):
        policy = {}
    allow_task_artifacts_only = bool(policy.get("allow_task_artifacts_only"))
    if artifact_paths:
        problems.append("staged task artifacts are not allowed by this gate contract: " + ", ".join(artifact_paths[:5]))
    code_paths = [p for p in staged_paths if p not in artifact_paths]
    if not code_paths and not allow_task_artifacts_only:
        problems.append("staged changes contain only task/workspace artifacts")
    out_of_scope = [p for p in code_paths if not path_in_scope(p, allowed_paths)]
    if out_of_scope:
        problems.append("staged paths outside gate contract scope: " + ", ".join(out_of_scope[:5]))
    forbidden = []
    for path in code_paths:
        normalized = _normalize_path(path)
        if any(pattern and pattern in normalized for pattern in forbidden_patterns):
            forbidden.append(path)
    if forbidden:
        problems.append("staged paths match forbidden contract patterns: " + ", ".join(forbidden[:5]))
    return problems
