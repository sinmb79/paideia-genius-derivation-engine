from paideia_genius_derivation import evaluate_pattern_affinity_v2


def _profile(**overrides):
    data = {
        "profile_id": "profile-1",
        "domain_focus": {
            "primary_domain": "software_agent_engineering",
            "privileged_domains": ["code_inspection"],
        },
    }
    data.update(overrides)
    return data


def _action_pattern(**overrides):
    data = {
        "pattern_id": "pattern-1",
        "pattern_version": "1.0.0",
        "domain": "software_agent_engineering",
        "task_family": "code_review",
        "goal_template": "Inspect a repository change.",
        "required_capabilities": ["code_inspection", "risk_analysis"],
        "steps": [
            {
                "node_id": "inspect",
                "capability": "code_inspection",
                "action_type": "inspect",
            }
        ],
        "lifecycle_status": "field_validated",
        "validation_profile_id": "validation-1",
    }
    data.update(overrides)
    return data


def _validation_profile(**overrides):
    data = {
        "profile_id": "validation-1",
        "pattern_id": "pattern-1",
        "pattern_version": "1.0.0",
        "structural_exam_passed": True,
        "behavioral_exam_passed": True,
        "near_transfer_passed": True,
        "far_transfer_passed": True,
        "adversarial_exam_passed": True,
        "shadow_validation_passed": True,
        "field_validation_passed": True,
        "critic_clearance_passed": True,
        "high_risk_eligible": True,
        "evidence_fresh_until": "2999-01-01",
    }
    data.update(overrides)
    return data


def test_pattern_affinity_v2_allows_fresh_high_risk_field_validated_pattern():
    result = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(),
        validation_profile=_validation_profile(),
        evidence_summary={"verified_outcome_count": 2, "active_weakness_count": 0},
        active_weaknesses=[],
        risk_level="high",
    )

    assert result.allowed is True
    assert result.allowed_deployment_ceiling == "limited_field"
    assert result.blocked_reasons == ()


def test_pattern_affinity_v2_blocks_high_risk_without_behavioral_and_field_evidence():
    result = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(lifecycle_status="behavioral_validated"),
        validation_profile=_validation_profile(
            behavioral_exam_passed=False,
            field_validation_passed=False,
            high_risk_eligible=False,
        ),
        evidence_summary={"verified_outcome_count": 0},
        active_weaknesses=[],
        risk_level="high",
    )

    assert result.allowed is False
    assert result.allowed_deployment_ceiling == "not_compiled"
    assert "behavioral_exam_required" in result.blocked_reasons
    assert "field_validation_required" in result.blocked_reasons
    assert "verified_field_outcome_required" in result.blocked_reasons


def test_pattern_affinity_v2_blocks_missing_or_unbound_validation_profile():
    missing = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(),
        validation_profile={},
        evidence_summary={"verified_outcome_count": 2},
        active_weaknesses=[],
        risk_level="low",
    )
    mismatch = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(validation_profile_id="validation-expected"),
        validation_profile=_validation_profile(profile_id="validation-other"),
        evidence_summary={"verified_outcome_count": 2},
        active_weaknesses=[],
        risk_level="low",
    )

    assert missing.allowed is False
    assert "missing_validation_profile" in missing.blocked_reasons
    assert "behavioral_exam_required" in missing.blocked_reasons
    assert mismatch.allowed is False
    assert "validation_profile_id_mismatch" in mismatch.blocked_reasons


def test_pattern_affinity_v2_blocks_inconsistent_high_risk_profile_claim():
    result = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(),
        validation_profile=_validation_profile(near_transfer_passed=False, high_risk_eligible=True),
        evidence_summary={"verified_outcome_count": 2},
        active_weaknesses=[],
        risk_level="high",
    )

    assert result.allowed is False
    assert "high_risk_profile_inconsistent" in result.blocked_reasons
    assert "near_transfer_required" in result.blocked_reasons


def test_pattern_affinity_v2_blocks_expired_or_invalid_evidence():
    expired = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(),
        validation_profile=_validation_profile(evidence_fresh_until="2000-01-01"),
        evidence_summary={"verified_outcome_count": 2},
        active_weaknesses=[],
        risk_level="high",
    )

    invalid = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(),
        validation_profile=_validation_profile(evidence_fresh_until="not-a-date"),
        evidence_summary={"verified_outcome_count": 2},
        active_weaknesses=[],
        risk_level="high",
    )

    assert expired.allowed is False
    assert "expired_evidence" in expired.blocked_reasons
    assert "fresh_pattern_validation_evidence" in expired.required_additional_evidence
    assert invalid.allowed is False
    assert "invalid_evidence_fresh_until" in invalid.blocked_reasons


def test_pattern_affinity_v2_blocks_stale_or_invalid_evidence_summary():
    result = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(),
        validation_profile=_validation_profile(),
        evidence_summary={"verified_outcome_count": 2, "stale_evidence_count": 1, "invalid_evidence_count": 1},
        active_weaknesses=[],
        risk_level="high",
    )

    assert result.allowed is False
    assert "stale_evidence" in result.blocked_reasons
    assert "invalid_evidence" in result.blocked_reasons


def test_pattern_affinity_v2_blocks_mismatched_validation_profile():
    result = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(pattern_version="1.0.0"),
        validation_profile=_validation_profile(pattern_version="2.0.0"),
        evidence_summary={"verified_outcome_count": 2},
        active_weaknesses=[],
        risk_level="low",
    )

    assert result.allowed is False
    assert "validation_profile_version_mismatch" in result.blocked_reasons
    assert "matching_validation_profile" in result.required_additional_evidence


def test_pattern_affinity_v2_blocks_high_severity_or_repeated_active_weaknesses():
    result = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(),
        validation_profile=_validation_profile(),
        evidence_summary={"verified_outcome_count": 2},
        active_weaknesses=[
            {
                "weakness_id": "weakness-high",
                "domain": "software_agent_engineering",
                "skill_id": "code_inspection",
                "severity": 0.9,
                "recurrence_count": 1,
            },
            {
                "weakness_id": "weakness-repeat",
                "domain": "software_agent_engineering",
                "capability_id": "risk_analysis",
                "severity": 0.4,
                "recurrence_count": 3,
            },
        ],
        risk_level="high",
    )

    assert result.allowed is False
    assert "active_curriculum_weakness" in result.blocked_reasons
    assert "passed_adaptive_reexam" in result.required_additional_evidence


def test_pattern_affinity_v2_requires_reexam_for_remediated_high_severity_weakness():
    result = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(),
        validation_profile=_validation_profile(),
        evidence_summary={"verified_outcome_count": 2},
        active_weaknesses=[
            {
                "weakness_id": "weakness-remediated-without-reexam",
                "domain": "software_agent_engineering",
                "skill_id": "code_inspection",
                "severity": 0.9,
                "recurrence_count": 3,
                "status": "remediated",
            }
        ],
        risk_level="high",
    )

    assert result.allowed is False
    assert "active_curriculum_weakness" in result.blocked_reasons


def test_pattern_affinity_v2_allows_remediated_weakness_after_passed_reexam():
    result = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(),
        validation_profile=_validation_profile(),
        evidence_summary={"verified_outcome_count": 2},
        active_weaknesses=[
            {
                "weakness_id": "weakness-remediated",
                "domain": "software_agent_engineering",
                "skill_id": "code_inspection",
                "severity": 0.9,
                "recurrence_count": 3,
                "status": "remediated",
                "remediation": {"status": "completed"},
                "adaptive_reexam": {"passed": True, "score": 0.91, "target_score": 0.85},
            }
        ],
        risk_level="high",
    )

    assert result.allowed is True
    assert result.blocked_reasons == ()


def test_pattern_affinity_v2_ignores_unrelated_or_resolved_weaknesses():
    result = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(),
        validation_profile=_validation_profile(),
        evidence_summary={"verified_outcome_count": 2},
        active_weaknesses=[
            {
                "weakness_id": "unrelated",
                "domain": "software_agent_engineering",
                "skill_id": "documentation",
                "severity": 0.95,
                "recurrence_count": 4,
            },
            {
                "weakness_id": "resolved",
                "domain": "software_agent_engineering",
                "skill_id": "code_inspection",
                "severity": 0.95,
                "recurrence_count": 4,
                "status": "resolved",
                "remediation": {"status": "completed"},
                "adaptive_reexam": {"passed": True, "score": 0.91, "target_score": 0.85},
            },
        ],
        risk_level="high",
    )

    assert result.allowed is True
    assert result.blocked_reasons == ()


def test_pattern_affinity_v2_blocks_bare_resolved_status_without_reexam():
    result = evaluate_pattern_affinity_v2(
        genius_profile=_profile(),
        action_pattern=_action_pattern(),
        validation_profile=_validation_profile(),
        evidence_summary={"verified_outcome_count": 2},
        active_weaknesses=[
            {
                "weakness_id": "bare-resolved",
                "domain": "software_agent_engineering",
                "skill_id": "code_inspection",
                "severity": 0.95,
                "recurrence_count": 4,
                "status": "resolved",
            },
        ],
        risk_level="high",
    )

    assert result.allowed is False
    assert "active_curriculum_weakness" in result.blocked_reasons
