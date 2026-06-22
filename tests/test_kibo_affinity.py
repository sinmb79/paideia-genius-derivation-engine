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


def test_pattern_affinity_allows_field_validated_pattern():
    result = evaluate_pattern_affinity(_profile(), _pattern(status="field_validated"), high_risk_task=True)

    assert result.allowed is True
