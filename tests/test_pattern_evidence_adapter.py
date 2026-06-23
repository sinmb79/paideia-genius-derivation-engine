import pytest
import json
from pathlib import Path

from paideia_genius_derivation.pattern_evidence_adapter import build_pattern_evidence_packet


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def _manifest():
    return {
        "schema": "paideia-cross-repo-compatibility/v1",
        "contracts_release": "2.0.0",
        "paideia_agent": ">=0.x,<1.0",
        "paideia_engines": ">=0.x,<1.0",
        "genius_derivation": ">=0.x,<1.0",
        "contract_hashes": {
            "action_pattern": "a" * 64,
            "validation_profile": "b" * 64,
        },
    }


def _action_pattern(**overrides):
    data = {
        "schema": "paideia-kibo-v2-action-pattern/v2",
        "schema_version": "2.0.0",
        "contract_hash": "a" * 64,
        "pattern_id": "pattern-1",
        "pattern_version": "1.0.0",
        "parent_pattern_version": None,
        "owner": "Boss",
        "domain": "investment_research",
        "task_family": "comparative_analysis",
        "goal_template": "Analyze {company}.",
        "input_slots": [],
        "preconditions": [],
        "required_observations": [],
        "steps": [],
        "transitions": [],
        "invariants": [],
        "abort_conditions": [],
        "recovery_actions": [],
        "success_conditions": [],
        "forbidden_contexts": [],
        "required_capabilities": ["valuation", "risk_analysis"],
        "source_case_ids": ["case-1"],
        "validation_profile_id": "validation-1",
        "lifecycle_status": "draft",
    }
    data.update(overrides)
    return data


def _valid_action_node():
    return {
        "node_id": "inspect",
        "action_type": "inspect",
        "capability": "code_inspection",
        "input_bindings": {"repo": "context.repo"},
        "expected_effects": [{"predicate_id": "effect-1", "op": "exists", "field": "plan", "value": True}],
        "timeout_ms": 1000,
        "retry_policy": {"max_attempts": 1, "backoff_ms": 0},
        "on_success": "test",
        "on_failure": None,
        "on_uncertain": None,
        "human_review_required": False,
    }


def _validation_profile(**overrides):
    data = {
        "schema": "paideia-kibo-v2-validation-profile/v2",
        "schema_version": "2.0.0",
        "contract_hash": "b" * 64,
        "profile_id": "validation-1",
        "pattern_id": "pattern-1",
        "pattern_version": "1.0.0",
        "structural_exam_passed": True,
        "behavioral_exam_passed": True,
        "near_transfer_passed": True,
        "far_transfer_passed": False,
        "adversarial_exam_passed": False,
        "shadow_validation_passed": False,
        "field_validation_passed": False,
        "critic_clearance_passed": True,
        "high_risk_eligible": False,
        "evidence_fresh_until": None,
        "evidence_refs": ["exam-1"],
    }
    data.update(overrides)
    return data


def test_pattern_evidence_adapter_builds_v2_packet_without_engine_dependency():
    packet = build_pattern_evidence_packet(
        action_pattern=_action_pattern(),
        validation_profile=_validation_profile(),
        evidence_summary={
            "verified_outcome_count": 2,
            "active_weakness_count": 0,
            "stale_evidence_count": 1,
            "expired_evidence_count": 2,
            "invalid_evidence_count": 3,
            "evidence_status": "stale",
        },
        manifest=_manifest(),
    )

    assert packet["schema"] == "paideia-genius-pattern-evidence-packet/v1"
    assert packet["pattern_id"] == "pattern-1"
    assert packet["profile_id"] == "validation-1"
    assert packet["validation_profile_id"] == "validation-1"
    assert packet["evidence_refs"] == ["exam-1"]
    assert packet["behavioral_exam_passed"] is True
    assert packet["near_transfer_passed"] is True
    assert packet["far_transfer_passed"] is False
    assert packet["critic_clearance_passed"] is True
    assert packet["verified_outcome_count"] == 2
    assert packet["stale_evidence_count"] == 1
    assert packet["expired_evidence_count"] == 2
    assert packet["invalid_evidence_count"] == 3
    assert packet["evidence_status"] == "stale"


def test_pattern_evidence_adapter_consumes_engine_generated_manifest_when_available():
    manifest_path = WORKSPACE_ROOT / "22b-paideia-engines" / "docs" / "cross_repo_compatibility_manifest.json"
    if not manifest_path.exists():
        pytest.skip("Engine manifest fixture is available only in the multi-repo workspace")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    action_pattern = _action_pattern(contract_hash=manifest["contract_hashes"]["action_pattern"])
    validation_profile = _validation_profile(contract_hash=manifest["contract_hashes"]["validation_profile"])

    packet = build_pattern_evidence_packet(
        action_pattern=action_pattern,
        validation_profile=validation_profile,
        evidence_summary={"verified_outcome_count": 1},
        manifest=manifest,
    )

    assert packet["pattern_id"] == "pattern-1"


def test_pattern_evidence_adapter_does_not_trust_non_finite_summary_counts():
    packet = build_pattern_evidence_packet(
        action_pattern=_action_pattern(),
        validation_profile=_validation_profile(),
        evidence_summary={"verified_outcome_count": float("nan")},
        manifest=_manifest(),
    )

    assert packet["verified_outcome_count"] == 0


def test_pattern_evidence_adapter_fails_closed_on_hash_mismatch():
    action_pattern = _action_pattern(contract_hash="0" * 64)

    with pytest.raises(ValueError, match="Contract hash mismatch"):
        build_pattern_evidence_packet(
            action_pattern=action_pattern,
            validation_profile=_validation_profile(),
            evidence_summary={},
            manifest=_manifest(),
        )


def test_pattern_evidence_adapter_fails_closed_on_missing_manifest_hash():
    manifest = _manifest()
    manifest["contract_hashes"] = {}
    action_pattern = _action_pattern()
    del action_pattern["contract_hash"]

    with pytest.raises(ValueError, match="Compatibility manifest requires contract_hashes"):
        build_pattern_evidence_packet(
            action_pattern=action_pattern,
            validation_profile=_validation_profile(),
            evidence_summary={},
            manifest=manifest,
        )


def test_pattern_evidence_adapter_rejects_missing_required_payload():
    action_pattern = _action_pattern()
    del action_pattern["pattern_id"]

    with pytest.raises(ValueError, match="missing required fields"):
        build_pattern_evidence_packet(
            action_pattern=action_pattern,
            validation_profile=_validation_profile(),
            evidence_summary={},
            manifest=_manifest(),
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("pattern_id", None),
        ("pattern_version", {}),
        ("input_slots", "not-list"),
        ("required_capabilities", "abc"),
    ],
)
def test_pattern_evidence_adapter_rejects_malformed_action_pattern_payload(field_name, bad_value):
    action_pattern = _action_pattern()
    action_pattern[field_name] = bad_value

    with pytest.raises(ValueError, match="invalid field types"):
        build_pattern_evidence_packet(
            action_pattern=action_pattern,
            validation_profile=_validation_profile(),
            evidence_summary={},
            manifest=_manifest(),
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("steps", [{"junk": True}]),
        ("input_slots", [{"slot_id": "ticker"}]),
        ("preconditions", [{"predicate_id": "pre-1", "op": "exists", "field": "repo", "value": True, "junk": True}]),
    ],
)
def test_pattern_evidence_adapter_rejects_malformed_nested_action_pattern_payload(field_name, bad_value):
    action_pattern = _action_pattern()
    action_pattern[field_name] = bad_value

    with pytest.raises(ValueError, match="invalid nested payload"):
        build_pattern_evidence_packet(
            action_pattern=action_pattern,
            validation_profile=_validation_profile(),
            evidence_summary={},
            manifest=_manifest(),
        )


def test_pattern_evidence_adapter_rejects_nullable_retry_backoff():
    action_pattern = _action_pattern()
    node = _valid_action_node()
    node["retry_policy"]["backoff_ms"] = None
    action_pattern["steps"] = [node]

    with pytest.raises(ValueError, match="invalid nested payload"):
        build_pattern_evidence_packet(
            action_pattern=action_pattern,
            validation_profile=_validation_profile(),
            evidence_summary={},
            manifest=_manifest(),
        )


def test_pattern_evidence_adapter_rejects_unknown_lifecycle_status():
    action_pattern = _action_pattern(lifecycle_status="not-a-valid-status")

    with pytest.raises(ValueError, match="Unsupported lifecycle_status"):
        build_pattern_evidence_packet(
            action_pattern=action_pattern,
            validation_profile=_validation_profile(),
            evidence_summary={},
            manifest=_manifest(),
        )


def test_pattern_evidence_adapter_rejects_extra_top_level_action_pattern_field():
    action_pattern = _action_pattern(extra=True)

    with pytest.raises(ValueError, match="unexpected fields"):
        build_pattern_evidence_packet(
            action_pattern=action_pattern,
            validation_profile=_validation_profile(),
            evidence_summary={},
            manifest=_manifest(),
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    [
        ("behavioral_exam_passed", "yes"),
        ("evidence_refs", "exam-1"),
        ("pattern_version", {}),
    ],
)
def test_pattern_evidence_adapter_rejects_malformed_validation_profile_payload(field_name, bad_value):
    validation_profile = _validation_profile()
    validation_profile[field_name] = bad_value

    with pytest.raises(ValueError, match="invalid field types"):
        build_pattern_evidence_packet(
            action_pattern=_action_pattern(),
            validation_profile=validation_profile,
            evidence_summary={},
            manifest=_manifest(),
        )


def test_pattern_evidence_adapter_rejects_extra_top_level_validation_profile_field():
    validation_profile = _validation_profile(extra=True)

    with pytest.raises(ValueError, match="unexpected fields"):
        build_pattern_evidence_packet(
            action_pattern=_action_pattern(),
            validation_profile=validation_profile,
            evidence_summary={},
            manifest=_manifest(),
        )


def test_pattern_evidence_adapter_rejects_pattern_version_mismatch():
    with pytest.raises(ValueError, match="Pattern version mismatch"):
        build_pattern_evidence_packet(
            action_pattern=_action_pattern(pattern_version="1.0.0"),
            validation_profile=_validation_profile(pattern_version="1.0.1"),
            evidence_summary={},
            manifest=_manifest(),
        )


def test_pattern_evidence_adapter_rejects_major_version_mismatch():
    with pytest.raises(ValueError, match="Unsupported schema_version"):
        build_pattern_evidence_packet(
            action_pattern=_action_pattern(schema_version="3.0.0"),
            validation_profile=_validation_profile(),
            evidence_summary={},
            manifest=_manifest(),
        )


def test_pattern_evidence_adapter_rejects_non_string_schema_version():
    with pytest.raises(ValueError, match="Unsupported schema_version"):
        build_pattern_evidence_packet(
            action_pattern=_action_pattern(schema_version=2.0),
            validation_profile=_validation_profile(),
            evidence_summary={},
            manifest=_manifest(),
        )


def test_pattern_evidence_adapter_rejects_non_string_manifest_hash():
    manifest = _manifest()
    manifest["contract_hashes"]["action_pattern"] = 123
    action_pattern = _action_pattern(contract_hash=123)

    with pytest.raises(ValueError, match="invalid contract hashes"):
        build_pattern_evidence_packet(
            action_pattern=action_pattern,
            validation_profile=_validation_profile(),
            evidence_summary={},
            manifest=manifest,
        )
