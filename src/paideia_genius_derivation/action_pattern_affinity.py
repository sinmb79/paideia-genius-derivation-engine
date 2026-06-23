from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any, Iterable, Mapping


ACTION_PATTERN_AFFINITY_SCHEMA = "paideia-action-pattern-affinity/v1"
HIGH_WEAKNESS_THRESHOLD = 0.75
REPEATED_WEAKNESS_THRESHOLD = 3
DEPLOYMENT_CEILINGS = {
    "not_compiled",
    "compiled",
    "simulation_validated",
    "shadow_validated",
    "limited_field",
    "operational",
    "suspended",
    "revoked",
}


def _tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _bool(value: Any) -> bool:
    return value is True


def _int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(numeric):
        return default
    try:
        return max(0, int(numeric))
    except (OverflowError, ValueError):
        return default


def _score(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(numeric):
        return default
    return max(0.0, min(1.0, numeric))


def _tokens(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        text = json.dumps(dict(value), ensure_ascii=False, sort_keys=True)
    elif isinstance(value, (list, tuple, set)):
        text = " ".join(str(item) for item in value)
    else:
        text = str(value or "")
    return {token.casefold() for token in re.findall(r"[0-9A-Za-z_]+", text)}


def _parse_date(value: Any) -> date | None:
    if value in {None, ""}:
        return None
    if not isinstance(value, str):
        raise ValueError("evidence_fresh_until must be an ISO date string")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError as exc:
            raise ValueError("evidence_fresh_until must be an ISO date string") from exc


def _profile_domains(genius_profile: Mapping[str, Any]) -> set[str]:
    focus = _as_mapping(genius_profile.get("domain_focus"))
    domains = {
        str(focus.get("primary_domain") or "").casefold(),
        *(str(item).casefold() for item in _as_list(focus.get("privileged_domains"))),
    }
    explicit_domains = _as_list(genius_profile.get("domains") or genius_profile.get("qualified_domains"))
    domains.update(str(item).casefold() for item in explicit_domains)
    return {domain for domain in domains if domain}


def _domain_matches(genius_profile: Mapping[str, Any], action_pattern: Mapping[str, Any]) -> bool:
    domains = _profile_domains(genius_profile)
    if not domains:
        return True
    pattern_domain = str(action_pattern.get("domain") or "").casefold()
    if pattern_domain in domains:
        return True
    compatible = {"investment_research", "securities_research", "valuation", "finance"}
    return pattern_domain in compatible and bool(domains & compatible)


def _pattern_tokens(action_pattern: Mapping[str, Any]) -> set[str]:
    return _tokens(
        [
            action_pattern.get("domain"),
            action_pattern.get("task_family"),
            action_pattern.get("required_capabilities"),
            action_pattern.get("goal_template"),
            action_pattern.get("steps"),
        ]
    )


def _weakness_resolved(weakness: Mapping[str, Any]) -> bool:
    status = str(weakness.get("status") or "").casefold()
    remediation = _as_mapping(weakness.get("remediation"))
    reexam = _as_mapping(weakness.get("adaptive_reexam") or weakness.get("reexam"))
    remediation_done = remediation.get("completed") is True or str(remediation.get("status") or "").casefold() in {
        "completed",
        "passed",
        "remediated",
    }
    if not remediation_done or not reexam:
        return False
    target = _score(reexam.get("target_score"), 0.75)
    return reexam.get("passed") is True and _score(reexam.get("score")) >= target


def _weakness_matches_pattern(weakness: Mapping[str, Any], action_pattern: Mapping[str, Any]) -> bool:
    pattern_domain = str(action_pattern.get("domain") or "").casefold()
    domain = str(weakness.get("domain") or "").casefold()
    if domain and domain not in {"general", pattern_domain}:
        return False
    tokens = _pattern_tokens(action_pattern)
    weakness_tokens = _tokens(
        [
            weakness.get("skill_id"),
            weakness.get("capability_id"),
            weakness.get("capability_ids"),
            weakness.get("weakness_type"),
            weakness.get("scope"),
        ]
    )
    meaningful = {token for token in weakness_tokens if len(token) >= 3}
    if meaningful:
        return bool(meaningful & tokens)
    return str(weakness.get("scope") or "").casefold() == "domain" and domain == pattern_domain


def _blocking_weakness_ids(
    active_weaknesses: Iterable[Mapping[str, Any]],
    action_pattern: Mapping[str, Any],
) -> tuple[str, ...]:
    ids: list[str] = []
    for weakness in active_weaknesses:
        if not isinstance(weakness, Mapping):
            continue
        if _weakness_resolved(weakness):
            continue
        if not _weakness_matches_pattern(weakness, action_pattern):
            continue
        if _score(weakness.get("severity")) >= HIGH_WEAKNESS_THRESHOLD or _int(weakness.get("recurrence_count")) >= REPEATED_WEAKNESS_THRESHOLD:
            ids.append(str(weakness.get("weakness_id") or weakness.get("id") or "unknown_weakness"))
    return tuple(dict.fromkeys(ids))


def _base_deployment_ceiling(action_pattern: Mapping[str, Any], validation_profile: Mapping[str, Any]) -> str:
    lifecycle = str(action_pattern.get("lifecycle_status") or action_pattern.get("status") or "draft").casefold()
    if lifecycle == "revoked":
        return "revoked"
    if lifecycle in {"suspended", "review_quarantine"}:
        return "suspended"
    if lifecycle == "draft":
        return "not_compiled"
    if _strong_validation_profile(validation_profile):
        return "operational" if lifecycle == "promoted" else "limited_field"
    if _bool(validation_profile.get("shadow_validation_passed")):
        return "shadow_validated"
    if _bool(validation_profile.get("behavioral_exam_passed")):
        return "simulation_validated"
    return "compiled" if _bool(validation_profile.get("structural_exam_passed")) or lifecycle == "structural_validated" else "not_compiled"


def _strong_validation_profile(validation_profile: Mapping[str, Any]) -> bool:
    return all(
        _bool(validation_profile.get(field))
        for field in (
            "behavioral_exam_passed",
            "near_transfer_passed",
            "far_transfer_passed",
            "adversarial_exam_passed",
            "shadow_validation_passed",
            "field_validation_passed",
            "critic_clearance_passed",
        )
    )


def _blocked_ceiling(blocked: list[str], base_ceiling: str) -> str:
    if "revoked_pattern" in blocked:
        return "revoked"
    if "suspended_pattern" in blocked or "quarantined_pattern" in blocked:
        return "suspended"
    if blocked:
        return "not_compiled"
    return base_ceiling


@dataclass(frozen=True)
class ActionPatternAffinity:
    allowed: bool
    affinity_score: float
    blocked_reasons: tuple[str, ...]
    required_additional_evidence: tuple[str, ...]
    allowed_deployment_ceiling: str
    schema: str = ACTION_PATTERN_AFFINITY_SCHEMA

    def __post_init__(self) -> None:
        if self.allowed_deployment_ceiling not in DEPLOYMENT_CEILINGS:
            raise ValueError(f"Unsupported allowed_deployment_ceiling: {self.allowed_deployment_ceiling}")
        object.__setattr__(self, "affinity_score", _score(self.affinity_score))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["affinity_score"] = round(float(self.affinity_score), 4)
        data["blocked_reasons"] = list(self.blocked_reasons)
        data["required_additional_evidence"] = list(self.required_additional_evidence)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionPatternAffinity":
        return cls(
            allowed=bool(data.get("allowed", False)),
            affinity_score=_score(data.get("affinity_score")),
            blocked_reasons=_tuple(data.get("blocked_reasons")),
            required_additional_evidence=_tuple(data.get("required_additional_evidence")),
            allowed_deployment_ceiling=str(data.get("allowed_deployment_ceiling") or "not_compiled"),
            schema=str(data.get("schema") or ACTION_PATTERN_AFFINITY_SCHEMA),
        )


PatternAffinityV2 = ActionPatternAffinity


def evaluate_pattern_affinity_v2(
    genius_profile: Mapping[str, Any],
    action_pattern: Mapping[str, Any],
    validation_profile: Mapping[str, Any],
    evidence_summary: Mapping[str, Any],
    active_weaknesses: Iterable[Mapping[str, Any]],
    *,
    risk_level: str,
) -> PatternAffinityV2:
    """Evaluate whether a genius profile may use a canonical ActionPattern."""
    genius_profile = _as_mapping(genius_profile)
    action_pattern = _as_mapping(action_pattern)
    validation_profile = _as_mapping(validation_profile)
    evidence_summary = _as_mapping(evidence_summary)
    risk = str(risk_level or "low").casefold()

    blocked: list[str] = []
    required: list[str] = []

    pattern_id = action_pattern.get("pattern_id")
    pattern_version = action_pattern.get("pattern_version")
    if not pattern_id:
        blocked.append("invalid_action_pattern")
        required.append("canonical_action_pattern")
    profile_id = validation_profile.get("profile_id")
    if not validation_profile:
        blocked.append("missing_validation_profile")
        required.append("canonical_validation_profile")
    elif not profile_id:
        blocked.append("invalid_validation_profile")
        required.append("canonical_validation_profile")
    expected_profile_id = action_pattern.get("validation_profile_id")
    if expected_profile_id and profile_id != expected_profile_id:
        blocked.append("validation_profile_id_mismatch")
        required.append("matching_validation_profile")
    if validation_profile.get("pattern_id") != pattern_id:
        blocked.append("validation_profile_pattern_mismatch")
        required.append("matching_validation_profile")
    if validation_profile.get("pattern_version") != pattern_version:
        blocked.append("validation_profile_version_mismatch")
        required.append("matching_validation_profile")

    lifecycle = str(action_pattern.get("lifecycle_status") or action_pattern.get("status") or "draft").casefold()
    if lifecycle == "revoked":
        blocked.append("revoked_pattern")
        required.append("new_pattern_version")
    if lifecycle == "suspended":
        blocked.append("suspended_pattern")
        required.append("pattern_governance_clearance")
    if lifecycle == "review_quarantine":
        blocked.append("quarantined_pattern")
        required.append("pattern_governance_clearance")

    try:
        fresh_until = _parse_date(validation_profile.get("evidence_fresh_until"))
    except ValueError:
        fresh_until = None
        blocked.append("invalid_evidence_fresh_until")
        required.append("fresh_pattern_validation_evidence")
    if fresh_until is not None and fresh_until < date.today():
        blocked.append("expired_evidence")
        required.append("fresh_pattern_validation_evidence")
    if risk == "high" and fresh_until is None and "invalid_evidence_fresh_until" not in blocked:
        blocked.append("missing_evidence_fresh_until")
        required.append("fresh_pattern_validation_evidence")

    evidence_statuses = {
        str(evidence_summary.get("evidence_status") or "").casefold(),
        str(validation_profile.get("evidence_status") or "").casefold(),
    }
    if "stale" in evidence_statuses or _int(evidence_summary.get("stale_evidence_count")) > 0:
        blocked.append("stale_evidence")
        required.append("fresh_pattern_validation_evidence")
    if "expired" in evidence_statuses or _int(evidence_summary.get("expired_evidence_count")) > 0:
        blocked.append("expired_evidence")
        required.append("fresh_pattern_validation_evidence")
    if (
        "invalid" in evidence_statuses
        or validation_profile.get("evidence_valid") is False
        or _int(evidence_summary.get("invalid_evidence_count")) > 0
    ):
        blocked.append("invalid_evidence")
        required.append("valid_pattern_evidence")

    if not _bool(validation_profile.get("behavioral_exam_passed")):
        blocked.append("behavioral_exam_required")
        required.append("passed_behavioral_exam")
    if _bool(validation_profile.get("high_risk_eligible")) and not _strong_validation_profile(validation_profile):
        blocked.append("high_risk_profile_inconsistent")
        required.append("complete_high_risk_validation_profile")
    if risk == "high":
        if not _bool(validation_profile.get("near_transfer_passed")):
            blocked.append("near_transfer_required")
            required.append("near_transfer_evidence")
        if not _bool(validation_profile.get("far_transfer_passed")):
            blocked.append("far_transfer_required")
            required.append("far_transfer_evidence")
        if not _bool(validation_profile.get("adversarial_exam_passed")):
            blocked.append("adversarial_exam_required")
            required.append("adversarial_exam_evidence")
        if not _bool(validation_profile.get("shadow_validation_passed")):
            blocked.append("shadow_validation_required")
            required.append("shadow_validation_evidence")
        if not _bool(validation_profile.get("field_validation_passed")):
            blocked.append("field_validation_required")
            required.append("field_validation_evidence")
        if not _bool(validation_profile.get("critic_clearance_passed")):
            blocked.append("critic_clearance_required")
            required.append("critic_clearance_evidence")
        if not _bool(validation_profile.get("high_risk_eligible")):
            blocked.append("high_risk_not_eligible")
            required.append("high_risk_eligibility_clearance")
        if _int(evidence_summary.get("verified_outcome_count")) < 1:
            blocked.append("verified_field_outcome_required")
            required.append("verified_field_outcome_evidence")

    if _int(evidence_summary.get("active_weakness_count")) > 0:
        blocked.append("active_weakness_summary_blocker")
        required.append("cleared_active_weakness_summary")

    weakness_ids = _blocking_weakness_ids(active_weaknesses, action_pattern)
    if weakness_ids:
        blocked.append("active_curriculum_weakness")
        required.append("completed_curriculum_remediation")
        required.append("passed_adaptive_reexam")

    if not _domain_matches(genius_profile, action_pattern):
        blocked.append("domain_mismatch")
        required.append("domain_matched_training_evidence")

    base_ceiling = _base_deployment_ceiling(action_pattern, validation_profile)
    allowed_ceiling = _blocked_ceiling(blocked, base_ceiling)
    score = 0.25
    if _domain_matches(genius_profile, action_pattern):
        score += 0.20
    if _bool(validation_profile.get("behavioral_exam_passed")):
        score += 0.20
    if _bool(validation_profile.get("shadow_validation_passed")):
        score += 0.15
    if _bool(validation_profile.get("field_validation_passed")):
        score += 0.15
    score += min(0.05, 0.01 * _int(evidence_summary.get("verified_outcome_count")))
    if blocked:
        score = min(score, 0.49)

    return ActionPatternAffinity(
        allowed=not blocked,
        affinity_score=score,
        blocked_reasons=tuple(dict.fromkeys(blocked)),
        required_additional_evidence=tuple(dict.fromkeys(required)),
        allowed_deployment_ceiling=allowed_ceiling,
    )
