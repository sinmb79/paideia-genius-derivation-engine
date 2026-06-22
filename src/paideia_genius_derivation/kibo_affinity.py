from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any


KIBO_AFFINITY_SCHEMA = "paideia-kibo-affinity/v1"
PATTERN_AFFINITY_SCHEMA = "paideia-pattern-affinity/v1"


def _tokens(value: Any) -> set[str]:
    if isinstance(value, dict):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    elif isinstance(value, (list, tuple, set)):
        text = " ".join(str(item) for item in value)
    else:
        text = str(value or "")
    return {token.casefold() for token in re.findall(r"[0-9A-Za-z가-힣_]+", text)}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


@dataclass(frozen=True)
class KiboAffinity:
    allowed: bool
    affinity_score: float
    blocked_reasons: tuple[str, ...]
    required_additional_evidence: tuple[str, ...]
    schema: str = KIBO_AFFINITY_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["blocked_reasons"] = list(self.blocked_reasons)
        data["required_additional_evidence"] = list(self.required_additional_evidence)
        data["affinity_score"] = round(self.affinity_score, 4)
        return data


def _domain_match(profile: dict[str, Any], kibo: dict[str, Any]) -> bool:
    focus = _as_dict(profile.get("domain_focus"))
    kibo_domain = str(kibo.get("domain") or "").casefold()
    domains = {
        str(focus.get("primary_domain") or "").casefold(),
        *(str(item).casefold() for item in _as_list(focus.get("privileged_domains"))),
    }
    if kibo_domain in domains:
        return True
    compatible = {"investment_research", "securities_research", "valuation", "finance"}
    return kibo_domain in compatible and bool(domains & compatible)


def _weakness_conflict(profile: dict[str, Any], kibo: dict[str, Any]) -> bool:
    weakness_tokens = _tokens(_as_dict(profile.get("unevenness_profile")).get("weakness_guardrails"))
    if not weakness_tokens:
        return False
    kibo_tokens = _tokens(
        [
            kibo.get("domain"),
            kibo.get("task_type"),
            kibo.get("required_inputs"),
            kibo.get("reusable_logic"),
            kibo.get("problem_signature"),
        ]
    )
    meaningful = {token for token in weakness_tokens if len(token) >= 5}
    return bool(meaningful & kibo_tokens)


def evaluate_kibo_affinity(
    genius_profile: dict[str, Any],
    kibo_record: dict[str, Any],
    *,
    minimum_training_evidence: int = 1,
    minimum_reviewed_transfer: int = 1,
) -> KiboAffinity:
    evidence = _as_dict(genius_profile.get("evidence_summary"))
    training_count = int(evidence.get("training_evidence_unit_count") or 0)
    transfer_count = int(evidence.get("reviewed_transfer_evidence_count") or 0)
    scored_trials = int(evidence.get("scored_reviewed_trial_count") or 0)
    average_score = float(evidence.get("assessment_average_score") or 0)

    blocked: list[str] = []
    required: list[str] = []
    profile_status = str(genius_profile.get("status") or "").casefold()
    validation = _as_dict(genius_profile.get("validation"))
    if profile_status and profile_status not in {"training_contract_valid", "genius_candidate_promoted"}:
        blocked.append("genius_profile_not_validated")
        required.append("validated_genius_profile")
    if validation and validation.get("passed") is False:
        blocked.append("genius_profile_validation_failed")
        required.append("passed_genius_profile_validation")
    if not _domain_match(genius_profile, kibo_record):
        blocked.append("domain_mismatch")
        required.append("domain_matched_training_evidence")
    if training_count < minimum_training_evidence:
        blocked.append("insufficient_training_evidence")
        required.append("reviewed_training_evidence")
    if transfer_count < minimum_reviewed_transfer:
        blocked.append("insufficient_reviewed_transfer_evidence")
        required.append("reviewed_transfer_work")
    if scored_trials and average_score < 80:
        blocked.append("reviewed_trial_score_below_floor")
        required.append("higher_scored_reviewed_trials")
    if _weakness_conflict(genius_profile, kibo_record):
        blocked.append("weakness_guardrail_conflict")
        required.append("guardrail_specific_review")

    domain_score = 0.35 if "domain_mismatch" not in blocked else 0.0
    evidence_score = min(0.30, 0.10 * training_count)
    transfer_score = min(0.20, 0.10 * transfer_count)
    trial_score = 0.15 if not scored_trials or average_score >= 80 else 0.0
    score = max(0.0, min(1.0, domain_score + evidence_score + transfer_score + trial_score))
    return KiboAffinity(
        allowed=not blocked,
        affinity_score=score,
        blocked_reasons=tuple(dict.fromkeys(blocked)),
        required_additional_evidence=tuple(dict.fromkeys(required)),
    )


def evaluate_pattern_affinity(
    genius_profile: dict[str, Any],
    pattern_candidate: dict[str, Any],
    *,
    minimum_training_evidence: int = 1,
    minimum_reviewed_transfer: int = 1,
    high_risk_task: bool = False,
    critic_passed: bool = False,
) -> KiboAffinity:
    affinity = evaluate_kibo_affinity(
        genius_profile,
        {
            "domain": pattern_candidate.get("domain"),
            "task_type": pattern_candidate.get("task_family"),
            "required_inputs": pattern_candidate.get("required_conditions"),
            "reusable_logic": pattern_candidate.get("abstract_strategy"),
            "problem_signature": " ".join(str(item) for item in pattern_candidate.get("abstract_strategy", [])),
        },
        minimum_training_evidence=minimum_training_evidence,
        minimum_reviewed_transfer=minimum_reviewed_transfer,
    )
    blocked = list(affinity.blocked_reasons)
    required = list(affinity.required_additional_evidence)
    status = str(pattern_candidate.get("status") or "draft")
    if status in {"draft", "weakened"}:
        blocked.append("pattern_not_exam_validated")
        required.append("passed_pattern_exam")
    if status == "quarantined":
        blocked.append("quarantined_pattern")
        required.append("pattern_governance_review")
    if high_risk_task and status not in {"field_validated", "reinforced"}:
        blocked.append("high_risk_requires_field_validated_pattern")
        required.append("real_world_outcome_evidence")
    if high_risk_task and not critic_passed:
        blocked.append("high_risk_requires_critic_passed_pattern")
        required.append("critic_report_pass_gate")
    score = affinity.affinity_score
    if blocked:
        score = min(score, 0.49)
    return KiboAffinity(
        allowed=not blocked,
        affinity_score=max(0.0, min(1.0, score)),
        blocked_reasons=tuple(dict.fromkeys(blocked)),
        required_additional_evidence=tuple(dict.fromkeys(required)),
        schema=PATTERN_AFFINITY_SCHEMA,
    )
