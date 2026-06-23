import pytest

from paideia_genius_derivation import (
    ACTION_PATTERN_AFFINITY_SCHEMA,
    OPERATIONAL_QUALIFICATION_SCHEMA,
    ActionPatternAffinity,
    OperationalQualification,
)


def test_action_pattern_affinity_round_trip():
    affinity = ActionPatternAffinity(
        allowed=False,
        affinity_score=0.42,
        blocked_reasons=("active_curriculum_weakness",),
        required_additional_evidence=("passed_adaptive_reexam",),
        allowed_deployment_ceiling="shadow_validated",
    )

    payload = affinity.to_dict()

    assert payload["schema"] == ACTION_PATTERN_AFFINITY_SCHEMA
    assert ActionPatternAffinity.from_dict(payload).to_dict() == payload


def test_action_pattern_affinity_rejects_unknown_deployment_ceiling():
    with pytest.raises(ValueError, match="Unsupported allowed_deployment_ceiling"):
        ActionPatternAffinity(
            allowed=True,
            affinity_score=0.9,
            blocked_reasons=(),
            required_additional_evidence=(),
            allowed_deployment_ceiling="direct_actuator",
        )


def test_operational_qualification_round_trip():
    qualification = OperationalQualification(
        profile_id="profile-1",
        capability_ids=("cap.inspect",),
        permitted_risk_classes=("low", "medium"),
        simulation_exam_count=3,
        shadow_exam_count=2,
        field_trial_count=0,
        unresolved_weakness_ids=("weakness-1",),
        status="shadow_qualified",
    )

    payload = qualification.to_dict()

    assert payload["schema"] == OPERATIONAL_QUALIFICATION_SCHEMA
    assert OperationalQualification.from_dict(payload).to_dict() == payload


def test_operational_qualification_rejects_unknown_status():
    with pytest.raises(ValueError, match="Unsupported operational qualification status"):
        OperationalQualification(
            profile_id="profile-1",
            capability_ids=(),
            permitted_risk_classes=(),
            simulation_exam_count=0,
            shadow_exam_count=0,
            field_trial_count=0,
            unresolved_weakness_ids=(),
            status="weaponized",
        )
