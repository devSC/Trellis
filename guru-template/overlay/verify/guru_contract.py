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
        "created_by": created_by,
        "created_at": _now_iso(),
        "policy_version": "guru-risk-contract-v1",
    }


def contract_route(contract: dict | None) -> str:
    if not isinstance(contract, dict):
        return ""
    return normalize_route(contract.get("route"))


def contract_risk(contract: dict | None) -> str:
    if not isinstance(contract, dict):
        return RISK_UNKNOWN
    return normalize_risk(contract.get("risk"))


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
    route = contract_route(contract)
    if route and route != ROUTE_FULL_CHAIN and not has_user_route_override(contract):
        risky_paths = high_risk_path_signals(code_paths)
        if risky_paths:
            problems.append(
                f"{route} staged paths contain high-risk signals: " + ", ".join(risky_paths[:5])
            )
    return problems
