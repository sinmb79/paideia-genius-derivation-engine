from paideia_genius_derivation.kibo_affinity import evaluate_kibo_affinity, evaluate_pattern_affinity


def _profile(**evidence_overrides):
    evidence = {
        "training_evidence_unit_count": 2,
        "reviewed_transfer_evidence_count": 1,
        "scored_reviewed_trial_count": 1,
        "assessment_average_score": 88,
    }
    evidence.update(evidence_overrides)
    return {
        "schema": "paideia-genius-derivation-profile/v1",
        "domain_focus": {
            "primary_domain": "securities_research",
            "privileged_domains": ["valuation", "risk analysis"],
        },
        "evidence_summary": evidence,
        "unevenness_profile": {
            "weakness_guardrails": ["ask for missing evidence outside the trained domain"]
        },
    }


def _kibo(**overrides):
    data = {
        "kibo_id": "kibo-1",
        "domain": "investment_research",
        "task_type": "comparative_analysis",
        "problem_signature": "Valuation and risk analysis.",
        "required_inputs": ["valuation", "risk_analysis"],
        "reusable_logic": ["valuation", "risk_analysis"],
    }
    data.update(overrides)
    return data


def test_affinity_allows_domain_matched_reviewed_profile():
    result = evaluate_kibo_affinity(_profile(), _kibo())

    assert result.allowed is True
    assert result.affinity_score > 0.5
    assert result.blocked_reasons == ()


def test_affinity_blocks_when_evidence_is_missing():
    result = evaluate_kibo_affinity(
        _profile(training_evidence_unit_count=0, reviewed_transfer_evidence_count=0),
        _kibo(),
    )

    assert result.allowed is False
    assert "insufficient_training_evidence" in result.blocked_reasons
    assert "reviewed_transfer_work" in result.required_additional_evidence


def test_affinity_blocks_domain_mismatch():
    result = evaluate_kibo_affinity(_profile(), _kibo(domain="legal_research"))

    assert result.allowed is False
    assert "domain_mismatch" in result.blocked_reasons


def _pattern(**overrides):
    data = {
        "pattern_id": "pattern-1",
        "domain": "investment_research",
        "task_family": "comparative_analysis",
        "abstract_strategy": ["valuation", "risk_analysis"],
        "required_conditions": ["valuation", "risk_analysis"],
        "status": "exam_validated",
    }
    data.update(overrides)
    return data


def test_pattern_affinity_blocks_unvalidated_pattern():
    result = evaluate_pattern_affinity(_profile(), _pattern(status="draft"))

    assert result.allowed is False
    assert "pattern_not_exam_validated" in result.blocked_reasons


def test_pattern_affinity_requires_field_validation_for_high_risk():
    result = evaluate_pattern_affinity(_profile(), _pattern(status="exam_validated"), high_risk_task=True)

    assert result.allowed is False
    assert "high_risk_requires_field_validated_pattern" in result.blocked_reasons


def test_pattern_affinity_requires_critic_for_high_risk():
    result = evaluate_pattern_affinity(_profile(), _pattern(status="field_validated"), high_risk_task=True)

    assert result.allowed is False
    assert "high_risk_requires_critic_passed_pattern" in result.blocked_reasons


def test_pattern_affinity_allows_field_validated_pattern():
    result = evaluate_pattern_affinity(
        _profile(),
        _pattern(status="field_validated"),
        high_risk_task=True,
        critic_passed=True,
    )

    assert result.allowed is True


def test_pattern_affinity_serializes_pattern_schema():
    result = evaluate_pattern_affinity(_profile(), _pattern(status="field_validated"))

    assert result.to_dict()["schema"] == "paideia-pattern-affinity/v1"


def test_affinity_blocks_explicitly_failed_profile_validation():
    profile = _profile()
    profile["status"] = "training_contract_valid"
    profile["validation"] = {"passed": False}

    result = evaluate_kibo_affinity(profile, _kibo())

    assert result.allowed is False
    assert "genius_profile_validation_failed" in result.blocked_reasons


def test_pattern_affinity_blocks_active_curriculum_weakness():
    profile = _profile()
    profile["weakness_records"] = [
        {
            "schema": "paideia-weakness-record/v1",
            "weakness_id": "weakness-1",
            "owner": "Boss",
            "domain": "investment_research",
            "skill_id": "risk_analysis",
            "weakness_type": "risk_gap",
            "evidence_refs": ["failure-1"],
            "severity": 0.86,
            "recurrence_count": 2,
        }
    ]

    result = evaluate_pattern_affinity(_profile(**{}), _pattern(status="field_validated"))
    assert result.allowed is True

    blocked = evaluate_pattern_affinity(profile, _pattern(status="field_validated"))

    assert blocked.allowed is False
    assert "active_curriculum_weakness" in blocked.blocked_reasons
    assert "passed_adaptive_reexam" in blocked.required_additional_evidence


def test_pattern_affinity_blocks_repeated_weakness_with_backlog():
    profile = _profile()
    profile["curriculum_backlog"] = ["curriculum-risk-1"]
    profile["weakness_records"] = [
        {
            "weakness_id": "weakness-1",
            "owner": "Boss",
            "domain": "investment_research",
            "skill_id": "risk_analysis",
            "weakness_type": "risk_gap",
            "evidence_refs": ["failure-1", "failure-2", "failure-3"],
            "severity": 0.62,
            "recurrence_count": 3,
        }
    ]

    result = evaluate_pattern_affinity(profile, _pattern(status="field_validated"))

    assert result.allowed is False
    assert "curriculum_backlog_not_cleared" in result.blocked_reasons


def test_pattern_affinity_blocks_open_backlog_without_weakness_records():
    profile = _profile()
    profile["curriculum_backlog"] = [{"curriculum_id": "curriculum-risk-1", "skill_id": "risk_analysis"}]

    result = evaluate_pattern_affinity(profile, _pattern(status="field_validated"))

    assert result.allowed is False
    assert "curriculum_backlog_not_cleared" in result.blocked_reasons


def test_pattern_affinity_requires_reexam_after_remediation():
    profile = _profile()
    profile["weakness_records"] = [
        {
            "weakness_id": "weakness-1",
            "owner": "Boss",
            "domain": "investment_research",
            "skill_id": "risk_analysis",
            "weakness_type": "risk_gap",
            "evidence_refs": ["failure-1"],
            "severity": 0.75,
            "recurrence_count": 1,
            "remediation": {"status": "completed"},
        }
    ]

    result = evaluate_pattern_affinity(profile, _pattern(status="field_validated"))

    assert result.allowed is False
    assert "active_curriculum_weakness" in result.blocked_reasons


def test_pattern_affinity_recovers_after_remediation_and_reexam_pass():
    profile = _profile()
    profile["weakness_records"] = [
        {
            "weakness_id": "weakness-1",
            "owner": "Boss",
            "domain": "investment_research",
            "skill_id": "risk_analysis",
            "weakness_type": "risk_gap",
            "evidence_refs": ["failure-1"],
            "severity": 0.75,
            "recurrence_count": 1,
            "remediation": {"status": "completed"},
            "adaptive_reexam": {"passed": True, "score": 0.91, "target_score": 0.85},
        }
    ]

    result = evaluate_pattern_affinity(profile, _pattern(status="field_validated"))

    assert result.allowed is True
    assert "active_curriculum_weakness" not in result.blocked_reasons


def test_pattern_affinity_does_not_overblock_unrelated_same_domain_weakness():
    profile = _profile()
    profile["weakness_records"] = [
        {
            "weakness_id": "weakness-1",
            "owner": "Boss",
            "domain": "investment_research",
            "skill_id": "macro_regime_analysis",
            "weakness_type": "knowledge_gap",
            "evidence_refs": ["failure-1"],
            "severity": 0.95,
            "recurrence_count": 4,
        }
    ]

    result = evaluate_pattern_affinity(profile, _pattern(status="field_validated"))

    assert result.allowed is True
