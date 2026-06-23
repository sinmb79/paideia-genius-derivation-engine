from __future__ import annotations

import math
from typing import Any


COMPATIBILITY_MANIFEST_SCHEMA = "paideia-cross-repo-compatibility/v1"
V2_SCHEMA_PREFIX = "paideia-kibo-v2-"
V2_SCHEMA_SUFFIX = "/v2"
REQUIRED_REPO_COMPATIBILITY_RANGES = {
    "paideia_agent": ">=0.x,<1.0",
    "paideia_engines": ">=0.x,<1.0",
    "genius_derivation": ">=0.x,<1.0",
}
ACTION_PATTERN_LIFECYCLE_STATUSES = {
    "draft",
    "review_quarantine",
    "structural_validated",
    "behavioral_validated",
    "shadow_validated",
    "field_validated",
    "promoted",
    "suspended",
    "revoked",
}

ACTION_PATTERN_REQUIRED_FIELDS = (
    "pattern_id",
    "pattern_version",
    "parent_pattern_version",
    "owner",
    "domain",
    "task_family",
    "goal_template",
    "input_slots",
    "preconditions",
    "required_observations",
    "steps",
    "transitions",
    "invariants",
    "abort_conditions",
    "recovery_actions",
    "success_conditions",
    "forbidden_contexts",
    "required_capabilities",
    "source_case_ids",
    "validation_profile_id",
    "lifecycle_status",
)

VALIDATION_PROFILE_REQUIRED_FIELDS = (
    "profile_id",
    "pattern_id",
    "pattern_version",
    "structural_exam_passed",
    "behavioral_exam_passed",
    "near_transfer_passed",
    "far_transfer_passed",
    "adversarial_exam_passed",
    "shadow_validation_passed",
    "field_validation_passed",
    "critic_clearance_passed",
    "evidence_fresh_until",
    "high_risk_eligible",
    "evidence_refs",
)

CONTRACT_HEADER_FIELDS = ("schema", "schema_version", "contract_hash")
ACTION_PATTERN_ALLOWED_FIELDS = (*CONTRACT_HEADER_FIELDS, *ACTION_PATTERN_REQUIRED_FIELDS)
VALIDATION_PROFILE_ALLOWED_FIELDS = (*CONTRACT_HEADER_FIELDS, *VALIDATION_PROFILE_REQUIRED_FIELDS)

ACTION_PATTERN_FIELD_RULES = {
    "pattern_id": "non_empty_string",
    "pattern_version": "non_empty_string",
    "parent_pattern_version": "optional_string",
    "owner": "non_empty_string",
    "domain": "non_empty_string",
    "task_family": "non_empty_string",
    "goal_template": "string",
    "input_slots": "list",
    "preconditions": "list",
    "required_observations": "list",
    "steps": "list",
    "transitions": "list",
    "invariants": "list",
    "abort_conditions": "list",
    "recovery_actions": "list",
    "success_conditions": "list",
    "forbidden_contexts": "list",
    "required_capabilities": "string_list",
    "source_case_ids": "string_list",
    "validation_profile_id": "optional_string",
    "lifecycle_status": "non_empty_string",
}

VALIDATION_PROFILE_FIELD_RULES = {
    "profile_id": "non_empty_string",
    "pattern_id": "non_empty_string",
    "pattern_version": "non_empty_string",
    "structural_exam_passed": "boolean",
    "behavioral_exam_passed": "boolean",
    "near_transfer_passed": "boolean",
    "far_transfer_passed": "boolean",
    "adversarial_exam_passed": "boolean",
    "shadow_validation_passed": "boolean",
    "field_validation_passed": "boolean",
    "critic_clearance_passed": "boolean",
    "evidence_fresh_until": "optional_string",
    "high_risk_eligible": "boolean",
    "evidence_refs": "string_list",
}


def contract_name_from_schema(schema: str) -> str:
    if not schema.startswith(V2_SCHEMA_PREFIX) or not schema.endswith(V2_SCHEMA_SUFFIX):
        raise ValueError(f"Unsupported v2 schema id: {schema}")
    return schema[len(V2_SCHEMA_PREFIX) : -len(V2_SCHEMA_SUFFIX)].replace("-", "_")


def validate_v2_header(artifact: dict[str, Any], manifest: dict[str, Any]) -> str:
    if manifest.get("schema") != COMPATIBILITY_MANIFEST_SCHEMA:
        raise ValueError("Unsupported compatibility manifest schema")
    release = manifest.get("contracts_release")
    if not isinstance(release, str) or not release.startswith("2."):
        raise ValueError("Unsupported contracts release")
    for repo_name, expected_range in REQUIRED_REPO_COMPATIBILITY_RANGES.items():
        if manifest.get(repo_name) != expected_range:
            raise ValueError(f"Compatibility manifest range mismatch for {repo_name}")
    hashes = manifest.get("contract_hashes")
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("Compatibility manifest requires contract_hashes")
    invalid_hashes = [
        name
        for name, value in hashes.items()
        if not isinstance(name, str) or not isinstance(value, str) or len(value) != 64
    ]
    if invalid_hashes:
        raise ValueError(f"Compatibility manifest has invalid contract hashes: {', '.join(map(str, invalid_hashes))}")
    schema_id = artifact.get("schema")
    if not isinstance(schema_id, str):
        raise ValueError("Artifact schema must be a string")
    contract_name = contract_name_from_schema(schema_id)
    schema_version = artifact.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version.startswith("2."):
        raise ValueError("Unsupported schema_version")
    expected_hash = hashes.get(contract_name)
    if not expected_hash:
        raise ValueError(f"Compatibility manifest has no hash for {contract_name}")
    artifact_hash = artifact.get("contract_hash")
    if not isinstance(artifact_hash, str) or len(artifact_hash) != 64:
        raise ValueError(f"Artifact contract_hash for {contract_name} must be a 64-character string")
    if artifact_hash != expected_hash:
        raise ValueError(f"Contract hash mismatch for {contract_name}")
    return contract_name


def _require_fields(artifact: dict[str, Any], fields: tuple[str, ...], contract_name: str) -> None:
    missing = [field for field in fields if field not in artifact]
    blank = [field for field in fields if artifact.get(field) == ""]
    if missing or blank:
        raise ValueError(f"{contract_name} is missing required fields: {', '.join(missing + blank)}")


def _require_top_level_no_extra(artifact: dict[str, Any], fields: tuple[str, ...], contract_name: str) -> None:
    extra = sorted(set(artifact) - set(fields))
    if extra:
        raise ValueError(f"{contract_name} has unexpected fields: {', '.join(extra)}")


def _matches_rule(value: Any, rule: str) -> bool:
    if rule == "non_empty_string":
        return isinstance(value, str) and bool(value)
    if rule == "string":
        return isinstance(value, str)
    if rule == "optional_string":
        return value is None or isinstance(value, str)
    if rule == "boolean":
        return isinstance(value, bool)
    if rule == "list":
        return isinstance(value, list)
    if rule == "string_list":
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    return True


def _require_field_types(artifact: dict[str, Any], rules: dict[str, str], contract_name: str) -> None:
    invalid = [field for field, rule in rules.items() if not _matches_rule(artifact.get(field), rule)]
    if invalid:
        raise ValueError(f"{contract_name} has invalid field types: {', '.join(invalid)}")


def _nested_error(path: str, message: str) -> None:
    raise ValueError(f"invalid nested payload: {path} {message}")


def _require_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _nested_error(path, "must be an object")
    return value


def _require_no_extra(value: dict[str, Any], allowed: tuple[str, ...], path: str) -> None:
    extra = sorted(set(value) - set(allowed))
    if extra:
        _nested_error(path, f"has unexpected fields: {', '.join(extra)}")


def _require_nested_fields(value: dict[str, Any], fields: tuple[str, ...], path: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        _nested_error(path, f"is missing fields: {', '.join(missing)}")


def _require_nested_rule(value: dict[str, Any], field_name: str, rule: str, path: str) -> None:
    if not _matches_rule(value.get(field_name), rule):
        _nested_error(f"{path}.{field_name}", f"must match {rule}")


def _require_optional_int(value: Any, path: str) -> None:
    if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
        _nested_error(path, "must be a non-negative integer or null")


def _require_non_negative_int(value: Any, path: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        _nested_error(path, "must be a non-negative integer")


def _validate_predicate(value: Any, path: str) -> None:
    item = _require_object(value, path)
    fields = ("predicate_id", "op", "field", "value")
    _require_no_extra(item, fields, path)
    _require_nested_fields(item, fields, path)
    _require_nested_rule(item, "predicate_id", "non_empty_string", path)
    _require_nested_rule(item, "op", "non_empty_string", path)
    _require_nested_rule(item, "field", "non_empty_string", path)


def _validate_typed_slot(value: Any, path: str) -> None:
    item = _require_object(value, path)
    fields = ("slot_id", "value_type", "required")
    _require_no_extra(item, fields, path)
    _require_nested_fields(item, fields, path)
    _require_nested_rule(item, "slot_id", "non_empty_string", path)
    _require_nested_rule(item, "value_type", "non_empty_string", path)
    _require_nested_rule(item, "required", "boolean", path)


def _validate_observation_requirement(value: Any, path: str) -> None:
    item = _require_object(value, path)
    fields = ("observation_id", "value_type", "freshness_ms")
    _require_no_extra(item, fields, path)
    _require_nested_fields(item, fields, path)
    _require_nested_rule(item, "observation_id", "non_empty_string", path)
    _require_nested_rule(item, "value_type", "non_empty_string", path)
    _require_optional_int(item.get("freshness_ms"), f"{path}.freshness_ms")


def _validate_retry_policy(value: Any, path: str) -> None:
    item = _require_object(value, path)
    fields = ("max_attempts", "backoff_ms")
    _require_no_extra(item, fields, path)
    _require_nested_fields(item, fields, path)
    if not isinstance(item.get("max_attempts"), int) or isinstance(item.get("max_attempts"), bool) or item["max_attempts"] < 1:
        _nested_error(f"{path}.max_attempts", "must be a positive integer")
    _require_non_negative_int(item.get("backoff_ms"), f"{path}.backoff_ms")


def _validate_action_node(value: Any, path: str) -> None:
    item = _require_object(value, path)
    fields = (
        "node_id",
        "action_type",
        "capability",
        "input_bindings",
        "expected_effects",
        "timeout_ms",
        "retry_policy",
        "on_success",
        "on_failure",
        "on_uncertain",
        "human_review_required",
    )
    _require_no_extra(item, fields, path)
    _require_nested_fields(item, fields, path)
    _require_nested_rule(item, "node_id", "non_empty_string", path)
    _require_nested_rule(item, "action_type", "non_empty_string", path)
    _require_nested_rule(item, "capability", "non_empty_string", path)
    if not isinstance(item.get("input_bindings"), dict) or not all(isinstance(key, str) and isinstance(val, str) for key, val in item["input_bindings"].items()):
        _nested_error(f"{path}.input_bindings", "must be an object of string values")
    if not isinstance(item.get("expected_effects"), list):
        _nested_error(f"{path}.expected_effects", "must be a list")
    for index, predicate in enumerate(item["expected_effects"]):
        _validate_predicate(predicate, f"{path}.expected_effects[{index}]")
    _require_optional_int(item.get("timeout_ms"), f"{path}.timeout_ms")
    _validate_retry_policy(item.get("retry_policy"), f"{path}.retry_policy")
    _require_nested_rule(item, "on_success", "optional_string", path)
    _require_nested_rule(item, "on_failure", "optional_string", path)
    _require_nested_rule(item, "on_uncertain", "optional_string", path)
    _require_nested_rule(item, "human_review_required", "boolean", path)


def _validate_transition(value: Any, path: str) -> None:
    item = _require_object(value, path)
    fields = ("from_node_id", "to_node_id", "condition")
    _require_no_extra(item, fields, path)
    _require_nested_fields(item, fields, path)
    _require_nested_rule(item, "from_node_id", "non_empty_string", path)
    _require_nested_rule(item, "to_node_id", "non_empty_string", path)
    if item.get("condition") is not None:
        _validate_predicate(item["condition"], f"{path}.condition")


def _validate_recovery_action(value: Any, path: str) -> None:
    item = _require_object(value, path)
    fields = ("recovery_id", "trigger", "action_node_id")
    _require_no_extra(item, fields, path)
    _require_nested_fields(item, fields, path)
    _require_nested_rule(item, "recovery_id", "non_empty_string", path)
    _validate_predicate(item.get("trigger"), f"{path}.trigger")
    _require_nested_rule(item, "action_node_id", "non_empty_string", path)


def _validate_object_list(artifact: dict[str, Any], field_name: str, validator, contract_name: str) -> None:
    values = artifact.get(field_name)
    if not isinstance(values, list):
        raise ValueError(f"{contract_name} has invalid field types: {field_name}")
    for index, item in enumerate(values):
        validator(item, f"{field_name}[{index}]")


def _validate_action_pattern_nested_payload(artifact: dict[str, Any], contract_name: str) -> None:
    _validate_object_list(artifact, "input_slots", _validate_typed_slot, contract_name)
    _validate_object_list(artifact, "preconditions", _validate_predicate, contract_name)
    _validate_object_list(artifact, "required_observations", _validate_observation_requirement, contract_name)
    _validate_object_list(artifact, "steps", _validate_action_node, contract_name)
    _validate_object_list(artifact, "transitions", _validate_transition, contract_name)
    _validate_object_list(artifact, "invariants", _validate_predicate, contract_name)
    _validate_object_list(artifact, "abort_conditions", _validate_predicate, contract_name)
    _validate_object_list(artifact, "recovery_actions", _validate_recovery_action, contract_name)
    _validate_object_list(artifact, "success_conditions", _validate_predicate, contract_name)
    _validate_object_list(artifact, "forbidden_contexts", _validate_predicate, contract_name)


def build_pattern_evidence_packet(
    *,
    action_pattern: dict[str, Any],
    validation_profile: dict[str, Any],
    evidence_summary: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    action_contract = validate_v2_header(action_pattern, manifest)
    validation_contract = validate_v2_header(validation_profile, manifest)
    if action_contract != "action_pattern":
        raise ValueError(f"Expected action_pattern, got {action_contract}")
    if validation_contract != "validation_profile":
        raise ValueError(f"Expected validation_profile, got {validation_contract}")
    _require_fields(action_pattern, ACTION_PATTERN_REQUIRED_FIELDS, action_contract)
    _require_fields(validation_profile, VALIDATION_PROFILE_REQUIRED_FIELDS, validation_contract)
    _require_top_level_no_extra(action_pattern, ACTION_PATTERN_ALLOWED_FIELDS, action_contract)
    _require_top_level_no_extra(validation_profile, VALIDATION_PROFILE_ALLOWED_FIELDS, validation_contract)
    _require_field_types(action_pattern, ACTION_PATTERN_FIELD_RULES, action_contract)
    _require_field_types(validation_profile, VALIDATION_PROFILE_FIELD_RULES, validation_contract)
    if action_pattern["lifecycle_status"] not in ACTION_PATTERN_LIFECYCLE_STATUSES:
        raise ValueError(f"Unsupported lifecycle_status: {action_pattern['lifecycle_status']}")
    _validate_action_pattern_nested_payload(action_pattern, action_contract)
    if action_pattern.get("pattern_id") != validation_profile.get("pattern_id"):
        raise ValueError("Pattern id mismatch between action pattern and validation profile")
    if action_pattern.get("pattern_version") != validation_profile.get("pattern_version"):
        raise ValueError("Pattern version mismatch between action pattern and validation profile")
    return {
        "schema": "paideia-genius-pattern-evidence-packet/v1",
        "pattern_id": action_pattern.get("pattern_id"),
        "pattern_version": action_pattern.get("pattern_version"),
        "validation_profile_id": action_pattern.get("validation_profile_id"),
        "profile_id": validation_profile.get("profile_id"),
        "domain": action_pattern.get("domain"),
        "task_family": action_pattern.get("task_family"),
        "required_capabilities": list(action_pattern.get("required_capabilities") or []),
        "structural_exam_passed": bool(validation_profile.get("structural_exam_passed")),
        "behavioral_exam_passed": bool(validation_profile.get("behavioral_exam_passed")),
        "near_transfer_passed": bool(validation_profile.get("near_transfer_passed")),
        "far_transfer_passed": bool(validation_profile.get("far_transfer_passed")),
        "adversarial_exam_passed": bool(validation_profile.get("adversarial_exam_passed")),
        "shadow_validation_passed": bool(validation_profile.get("shadow_validation_passed")),
        "field_validation_passed": bool(validation_profile.get("field_validation_passed")),
        "critic_clearance_passed": bool(validation_profile.get("critic_clearance_passed")),
        "high_risk_eligible": bool(validation_profile.get("high_risk_eligible")),
        "evidence_fresh_until": validation_profile.get("evidence_fresh_until"),
        "evidence_refs": list(validation_profile.get("evidence_refs") or []),
        "verified_outcome_count": _non_negative_int(evidence_summary.get("verified_outcome_count")),
        "active_weakness_count": _non_negative_int(evidence_summary.get("active_weakness_count")),
        "stale_evidence_count": _non_negative_int(evidence_summary.get("stale_evidence_count")),
        "expired_evidence_count": _non_negative_int(evidence_summary.get("expired_evidence_count")),
        "invalid_evidence_count": _non_negative_int(evidence_summary.get("invalid_evidence_count")),
        "evidence_status": evidence_summary.get("evidence_status"),
    }


def _non_negative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0
    if not math.isfinite(numeric) or numeric < 0:
        return 0
    return int(numeric)
