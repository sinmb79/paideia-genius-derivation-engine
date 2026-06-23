from paideia_genius_derivation import evaluate_pattern_affinity_v2


def test_pattern_affinity_v2_requires_behavioral_validation_evidence():
    result = evaluate_pattern_affinity_v2(
        genius_profile={"profile_id": "profile-1"},
        action_pattern={
            "pattern_id": "pattern-1",
            "pattern_version": "1.0.0",
            "domain": "software_agent_engineering",
            "required_capabilities": ["code_inspection"],
            "lifecycle_status": "behavioral_validated",
        },
        validation_profile={
            "pattern_id": "pattern-1",
            "pattern_version": "1.0.0",
            "behavioral_exam_passed": False,
            "field_validation_passed": False,
            "high_risk_eligible": False,
            "evidence_fresh_until": "2999-01-01",
        },
        evidence_summary={"verified_outcome_count": 0},
        active_weaknesses=[],
        risk_level="high",
    )

    assert result.allowed is False
    assert "behavioral_exam_required" in result.blocked_reasons
