from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GENIUS_DERIVATION_PROFILE_SCHEMA = "paideia-genius-derivation-profile/v1"
GENIUS_DERIVATION_VALIDATION_SCHEMA = "paideia-genius-derivation-profile-validation/v1"
GENIUS_DERIVATION_INPUT_VALIDATION_SCHEMA = "paideia-genius-derivation-input-validation/v1"
GENIUS_CANDIDATE_PROMOTION_SCHEMA = "paideia-genius-candidate-promotion/v1"
TRAINING_BLUEPRINT_SCHEMA = "ai-talent-training-blueprint/v1"

DRAFT_STATUS = "draft"
TRAINING_CONTRACT_VALID_STATUS = "training_contract_valid"
GENIUS_CANDIDATE_PROMOTED_STATUS = "genius_candidate_promoted"
FAILED_STATUS = "failed"

MINIMUM_ASSESSMENT_SCORE = 80
MINIMUM_RUBRIC_SCORE = 20

REQUIRED_PRACTICE_CYCLE = [
    "domain_problem_selection",
    "worked_example_compression",
    "timed_trial",
    "error_taxonomy",
    "counterexample_drill",
    "method_distillation",
    "varied_transfer",
]

REQUIRED_SCORECARD_METRICS = [
    "speed_under_constraint",
    "evidence_precision",
    "mistake_recovery",
    "method_stability",
    "varied_transfer_success",
    "originality_under_constraints",
]

_REDACTION_PLACEHOLDER = "[redacted-sensitive-value]"
_SENSITIVE_VALUE_PATTERNS = [
    re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"gh[opsu]_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"ya29\.[A-Za-z0-9._-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE),
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _has_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and any(_non_empty_text(item) for item in value)


def _redact_public_text(value: str) -> str:
    redacted = value
    for pattern in _SENSITIVE_VALUE_PATTERNS:
        redacted = pattern.sub(_REDACTION_PLACEHOLDER, redacted)
    return redacted


def _redact_public_value(value: Any) -> Any:
    if isinstance(value, str):
        return _redact_public_text(value)
    if isinstance(value, list):
        return [_redact_public_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _redact_public_value(item) for key, item in value.items()}
    return value


def _grade_records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [item for item in value.get("records", []) if isinstance(item, dict)]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _assessment_results(assessment_transcript: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(assessment_transcript, dict):
        return []
    return [item for item in assessment_transcript.get("results", []) if isinstance(item, dict)]


def _assessment_score_value(result: dict[str, Any]) -> float | None:
    direct_score = _numeric(result.get("score"))
    if direct_score is not None:
        return direct_score
    rubric_scores = [
        score
        for score in (_numeric(value) for value in _as_dict(result.get("rubric_scores")).values())
        if score is not None
    ]
    if not rubric_scores:
        return None
    return sum(rubric_scores) / len(rubric_scores)


def _assessment_meets_quality_floor(result: dict[str, Any]) -> bool:
    if result.get("passed") is not True:
        return False
    direct_score = _numeric(result.get("score"))
    if direct_score is not None and direct_score < MINIMUM_ASSESSMENT_SCORE:
        return False
    rubric_scores = [
        score
        for score in (_numeric(value) for value in _as_dict(result.get("rubric_scores")).values())
        if score is not None
    ]
    return not rubric_scores or min(rubric_scores) >= MINIMUM_RUBRIC_SCORE


def _reasoning_entry_count(reasoning_kibo: dict[str, Any] | None) -> int:
    kibo = _as_dict(reasoning_kibo)
    entry_count = kibo.get("entry_count")
    if isinstance(entry_count, int) and entry_count >= 0:
        return entry_count
    return len(_as_list(kibo.get("entries")))


def _track_from_blueprint(blueprint: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(blueprint.get("track"))


def _identity_from_blueprint(blueprint: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(blueprint.get("identity"))


def _curriculum_topics(curriculum_manifest: dict[str, Any] | None) -> list[str]:
    curriculum = _as_dict(curriculum_manifest)
    topics: list[str] = []
    for key in ["core_topics", "public_sources", "assessment_ladder"]:
        value = curriculum.get(key)
        if isinstance(value, list):
            topics.extend(str(item) for item in value[:12])
        elif isinstance(value, dict):
            for subvalue in value.values():
                if isinstance(subvalue, list):
                    topics.extend(str(item) for item in subvalue[:12])
                elif subvalue:
                    topics.append(str(subvalue))
    for year in _as_list(curriculum.get("yearly_ladder")):
        if isinstance(year, dict):
            topics.extend(str(item) for item in _as_list(year.get("learning_data"))[:4])
    return list(dict.fromkeys(item for item in topics if item))[:24]


def _weak_spots(
    assessment_transcript: dict[str, Any] | None,
    grade_learning_records: dict[str, Any] | list[dict[str, Any]] | None,
    growth_profile: dict[str, Any] | None,
) -> list[str]:
    weak: list[str] = []
    for result in _assessment_results(assessment_transcript):
        weak.extend(str(item) for item in _as_list(result.get("weak_spots")) if item)
        for key, score in _as_dict(result.get("rubric_scores")).items():
            if isinstance(score, (int, float)) and score < 20:
                weak.append(str(key))
    for record in _grade_records(grade_learning_records):
        loop = _as_dict(record.get("feedback_loop"))
        weak.extend(str(item) for item in _as_list(loop.get("observed_weak_spots")) if item)
    asymmetry = _as_dict(_as_dict(growth_profile).get("asymmetry_profile"))
    weak.extend(str(item) for item in _as_list(asymmetry.get("growth_costs")) if item)
    return list(dict.fromkeys(item for item in weak if item and item != "continue_current_learning_path"))[:12]


def _domain_focus(
    blueprint: dict[str, Any],
    curriculum_manifest: dict[str, Any] | None,
    growth_profile: dict[str, Any] | None,
) -> dict[str, Any]:
    track = _track_from_blueprint(blueprint)
    curriculum = _as_dict(curriculum_manifest)
    growth_asymmetry = _as_dict(_as_dict(growth_profile).get("asymmetry_profile"))
    domains: list[str] = []
    if curriculum.get("domain"):
        domains.append(str(curriculum["domain"]))
    domain_obsession = growth_asymmetry.get("domain_obsession")
    if domain_obsession:
        domains.append(str(domain_obsession))
    domains.extend(str(item) for item in _as_list(track.get("domains")) if item)
    domains = list(dict.fromkeys(domains))
    primary = str(track.get("name") or track.get("track_id") or (domains[0] if domains else "domain_specialty"))
    return {
        "primary_domain": primary,
        "track_id": track.get("track_id"),
        "target_role": track.get("target_role"),
        "major_goal": _identity_from_blueprint(blueprint).get("major_goal") or track.get("specialty"),
        "privileged_domains": domains[:8],
        "curriculum_id": curriculum.get("curriculum_id"),
    }


def _practice_ladder(
    grade_learning_records: dict[str, Any] | list[dict[str, Any]] | None,
    assessment_transcript: dict[str, Any] | None,
    curriculum_topics: list[str],
) -> list[dict[str, Any]]:
    ladder: list[dict[str, Any]] = []
    for record in _grade_records(grade_learning_records)[:12]:
        weak_spots = _as_dict(record.get("feedback_loop")).get("observed_weak_spots", [])
        ladder.append(
            {
                "stage_id": str(record.get("year_id") or record.get("education_stage") or "learning_stage"),
                "education_stage": record.get("education_stage"),
                "focus": _as_list(record.get("learning_data"))[:5],
                "linked_exams": _as_list(record.get("required_exams"))[:5],
                "timed_trial": True,
                "compression_task": "turn repeated worked examples into a named chunk and one reusable method rule",
                "weak_spots_to_retest": [str(item) for item in _as_list(weak_spots)[:5]],
            }
        )
    if ladder:
        return ladder

    for result in _assessment_results(assessment_transcript)[:8]:
        ladder.append(
            {
                "stage_id": str(result.get("gate_id") or "assessment_gate"),
                "education_stage": "assessment_gate",
                "focus": [str(result.get("gate_name") or result.get("gate_id") or "domain_exam")],
                "linked_exams": [str(result.get("gate_id") or "domain_exam")],
                "timed_trial": True,
                "compression_task": "compress the passed answer into a reusable method and retest the weak spot",
                "weak_spots_to_retest": _as_list(result.get("weak_spots"))[:5],
            }
        )
    if ladder:
        return ladder

    return [
        {
            "stage_id": "domain_foundation",
            "education_stage": "foundation",
            "focus": curriculum_topics[:5] or ["domain_problem_solving"],
            "linked_exams": ["domain_foundation_exam"],
            "timed_trial": True,
            "compression_task": "build first chunks from sourced examples before broad search",
            "weak_spots_to_retest": [],
        }
    ]


def _pattern_chunks(curriculum_topics: list[str], domain_focus: dict[str, Any]) -> list[dict[str, Any]]:
    seeds = curriculum_topics or _as_list(domain_focus.get("privileged_domains")) or [domain_focus.get("primary_domain")]
    chunks: list[dict[str, Any]] = []
    for index, topic in enumerate(seeds[:10], start=1):
        chunks.append(
            {
                "chunk_id": _stable_id("chunk", topic, index),
                "label": str(topic),
                "purpose": "recognize this pattern quickly and choose a practiced method before exhaustive search",
                "training_method": "worked_example_to_timed_recall_to_counterexample",
            }
        )
    return chunks


def validate_genius_derivation_inputs(
    blueprint: dict[str, Any],
    *,
    curriculum_manifest: dict[str, Any] | None = None,
    assessment_transcript: dict[str, Any] | None = None,
    growth_profile: dict[str, Any] | None = None,
    grade_learning_records: dict[str, Any] | list[dict[str, Any]] | None = None,
    reasoning_kibo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the public input contract before profile construction."""

    failed: list[str] = []
    issues: list[dict[str, Any]] = []

    def add_issue(check_id: str, message: str, *, path: str) -> None:
        failed.append(check_id)
        issues.append({"check_id": check_id, "path": path, "message": message})

    if not isinstance(blueprint, dict):
        add_issue("blueprint_object_required", "blueprint must be a JSON object", path="blueprint")
        blueprint = {}

    identity = _as_dict(blueprint.get("identity"))
    track = _as_dict(blueprint.get("track"))
    checks = {
        "blueprint_schema": blueprint.get("schema") == TRAINING_BLUEPRINT_SCHEMA,
        "identity_object": isinstance(blueprint.get("identity"), dict),
        "identity_name": _non_empty_text(identity.get("name")),
        "track_object": isinstance(blueprint.get("track"), dict),
        "track_id": _non_empty_text(track.get("track_id")),
        "track_domains": _has_non_empty_string_list(track.get("domains")),
    }
    if not checks["blueprint_schema"]:
        add_issue("blueprint_schema", f"blueprint.schema must be {TRAINING_BLUEPRINT_SCHEMA}", path="blueprint.schema")
    if not checks["identity_object"]:
        add_issue("identity_object", "blueprint.identity must be an object", path="blueprint.identity")
    if not checks["identity_name"]:
        add_issue("identity_name", "blueprint.identity.name is required", path="blueprint.identity.name")
    if not checks["track_object"]:
        add_issue("track_object", "blueprint.track must be an object", path="blueprint.track")
    if not checks["track_id"]:
        add_issue("track_id", "blueprint.track.track_id is required", path="blueprint.track.track_id")
    if not checks["track_domains"]:
        add_issue("track_domains", "blueprint.track.domains must contain at least one domain", path="blueprint.track.domains")

    if curriculum_manifest is not None and not isinstance(curriculum_manifest, dict):
        add_issue("curriculum_manifest_object", "curriculum manifest must be an object", path="curriculum_manifest")

    if assessment_transcript is not None:
        if not isinstance(assessment_transcript, dict):
            add_issue("assessment_transcript_object", "assessment transcript must be an object", path="assessment_transcript")
        else:
            results = assessment_transcript.get("results")
            if not isinstance(results, list):
                add_issue("assessment_results_list", "assessment_transcript.results must be a list", path="assessment_transcript.results")
            else:
                for index, result in enumerate(results):
                    path = f"assessment_transcript.results[{index}]"
                    if not isinstance(result, dict):
                        add_issue("assessment_result_object", "each assessment result must be an object", path=path)
                        continue
                    if "passed" not in result or not isinstance(result.get("passed"), bool):
                        add_issue("assessment_result_passed_bool", "assessment result passed must be a boolean", path=f"{path}.passed")
                    if "rubric_scores" in result and not isinstance(result.get("rubric_scores"), dict):
                        add_issue("assessment_rubric_scores_object", "rubric_scores must be an object when present", path=f"{path}.rubric_scores")
                    if "score" in result and _numeric(result.get("score")) is None:
                        add_issue("assessment_score_number", "score must be numeric when present", path=f"{path}.score")

    if growth_profile is not None:
        if not isinstance(growth_profile, dict):
            add_issue("growth_profile_object", "growth profile must be an object", path="growth_profile")
        elif "asymmetry_profile" in growth_profile and not isinstance(growth_profile.get("asymmetry_profile"), dict):
            add_issue(
                "growth_asymmetry_profile_object",
                "growth_profile.asymmetry_profile must be an object when present",
                path="growth_profile.asymmetry_profile",
            )

    if grade_learning_records is not None:
        if not isinstance(grade_learning_records, (dict, list)):
            add_issue("grade_learning_records_object_or_list", "grade learning records must be an object or list", path="grade_learning_records")
        else:
            if isinstance(grade_learning_records, dict) and "records" in grade_learning_records and not isinstance(grade_learning_records.get("records"), list):
                add_issue("grade_learning_records_records_list", "grade_learning_records.records must be a list", path="grade_learning_records.records")
            raw_records = grade_learning_records.get("records", []) if isinstance(grade_learning_records, dict) else grade_learning_records
            for record_index, record in enumerate(_as_list(raw_records)):
                record_path = f"grade_learning_records.records[{record_index}]" if isinstance(grade_learning_records, dict) else f"grade_learning_records[{record_index}]"
                if not isinstance(record, dict):
                    add_issue("grade_record_object", "each grade learning record must be an object", path=record_path)
                    continue
                assignments = record.get("assignments")
                if assignments is not None and not isinstance(assignments, list):
                    add_issue("grade_assignments_list", "record.assignments must be a list when present", path=f"{record_path}.assignments")
                    continue
                for assignment_index, assignment in enumerate(_as_list(assignments)):
                    path = f"{record_path}.assignments[{assignment_index}].status"
                    if not isinstance(assignment, dict):
                        add_issue("grade_assignment_object", "each assignment must be an object", path=path)
                    elif not _non_empty_text(assignment.get("status")):
                        add_issue("grade_assignment_status", "assignment.status is required", path=path)

    if reasoning_kibo is not None:
        if not isinstance(reasoning_kibo, dict):
            add_issue("reasoning_kibo_object", "reasoning_kibo must be an object", path="reasoning_kibo")
        else:
            entry_count = reasoning_kibo.get("entry_count")
            if entry_count is not None and (not isinstance(entry_count, int) or entry_count < 0):
                add_issue("reasoning_kibo_entry_count", "reasoning_kibo.entry_count must be a non-negative integer", path="reasoning_kibo.entry_count")
            if "entries" in reasoning_kibo and not isinstance(reasoning_kibo.get("entries"), list):
                add_issue("reasoning_kibo_entries_list", "reasoning_kibo.entries must be a list when present", path="reasoning_kibo.entries")

    failed = list(dict.fromkeys(failed))
    checks.update(
        {
            "curriculum_manifest_shape": not any(item["check_id"] == "curriculum_manifest_object" for item in issues),
            "assessment_transcript_shape": not any(item["check_id"].startswith("assessment_") for item in issues),
            "growth_profile_shape": not any(item["check_id"].startswith("growth_") for item in issues),
            "grade_learning_records_shape": not any(item["check_id"].startswith("grade_") for item in issues),
            "reasoning_kibo_shape": not any(item["check_id"].startswith("reasoning_") for item in issues),
        }
    )
    return {
        "schema": GENIUS_DERIVATION_INPUT_VALIDATION_SCHEMA,
        "passed": not failed,
        "status": "passed" if not failed else "failed",
        "checks": checks,
        "failed_checks": failed,
        "issues": issues,
    }


def _evidence_counts(
    assessment_transcript: dict[str, Any] | None,
    grade_learning_records: dict[str, Any] | list[dict[str, Any]] | None,
    growth_profile: dict[str, Any] | None,
    *,
    curriculum_topic_count: int,
    practice_ladder_stage_count: int,
) -> dict[str, Any]:
    assessments = _assessment_results(assessment_transcript)
    records = _grade_records(grade_learning_records)
    passed = sum(1 for item in assessments if item.get("passed") is True)
    qualified_assessments = [item for item in assessments if _assessment_meets_quality_floor(item)]
    qualified_scores = [
        score
        for score in (_assessment_score_value(item) for item in qualified_assessments)
        if score is not None
    ]
    reviewed_assignments = sum(
        1
        for record in records
        for assignment in _as_list(record.get("assignments"))
        if isinstance(assignment, dict) and assignment.get("status") == "completed_and_reviewed"
    )
    unreviewed_assignments = sum(
        1
        for record in records
        for assignment in _as_list(record.get("assignments"))
        if isinstance(assignment, dict) and assignment.get("status") != "completed_and_reviewed"
    )
    domains = Counter(str(record.get("education_stage") or "unknown") for record in records)
    varied_transfer_signals = {
        str(item.get("gate_id") or item.get("gate_name") or "assessment_gate")
        for item in qualified_assessments
    }
    varied_transfer_signals.update(
        str(record.get("education_stage") or record.get("year_id") or "learning_stage")
        for record in records
        if any(
            isinstance(assignment, dict) and assignment.get("status") == "completed_and_reviewed"
            for assignment in _as_list(record.get("assignments"))
        )
    )
    return {
        "assessment_result_count": len(assessments),
        "passed_assessment_count": passed,
        "qualified_passed_assessment_count": len(qualified_assessments),
        "disqualified_passed_assessment_count": max(0, passed - len(qualified_assessments)),
        "scored_reviewed_trial_count": len(qualified_scores),
        "assessment_average_score": round(sum(qualified_scores) / len(qualified_scores), 2) if qualified_scores else 0,
        "grade_learning_record_count": len(records),
        "reviewed_assignment_count": reviewed_assignments,
        "unreviewed_assignment_count": unreviewed_assignments,
        "reviewed_transfer_evidence_count": len(qualified_assessments) + reviewed_assignments,
        "training_evidence_unit_count": len(qualified_assessments) + reviewed_assignments + len(records),
        "varied_transfer_evidence_count": len([item for item in varied_transfer_signals if item]),
        "curriculum_topic_count": curriculum_topic_count,
        "practice_ladder_stage_count": practice_ladder_stage_count,
        "growth_profile_schema": _as_dict(growth_profile).get("schema"),
        "growth_profile_present": bool(_as_dict(growth_profile).get("schema")),
        "grade_stage_distribution": [
            {"id": key, "count": count}
            for key, count in domains.most_common(8)
        ],
    }


def build_genius_derivation_profile(
    blueprint: dict[str, Any],
    *,
    curriculum_manifest: dict[str, Any] | None = None,
    assessment_transcript: dict[str, Any] | None = None,
    growth_profile: dict[str, Any] | None = None,
    grade_learning_records: dict[str, Any] | list[dict[str, Any]] | None = None,
    reasoning_kibo: dict[str, Any] | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Build a public-safe domain genius derivation profile.

    The profile is not a claim that an agent is generally superior. It is a
    training contract for uneven, domain-specific excellence under bounded
    context, timed exams, feedback, and reviewed transfer work.
    """

    if not isinstance(blueprint, dict):
        raise ValueError("Invalid input contract: blueprint must be a JSON object")
    if blueprint.get("schema") != TRAINING_BLUEPRINT_SCHEMA:
        raise ValueError("Unsupported training blueprint schema")
    input_validation = validate_genius_derivation_inputs(
        blueprint,
        curriculum_manifest=curriculum_manifest,
        assessment_transcript=assessment_transcript,
        growth_profile=growth_profile,
        grade_learning_records=grade_learning_records,
        reasoning_kibo=reasoning_kibo,
    )
    if not input_validation["passed"]:
        raise ValueError("Invalid input contract: " + ", ".join(input_validation["failed_checks"]))

    identity = _identity_from_blueprint(blueprint)
    domain_focus = _domain_focus(blueprint, curriculum_manifest, growth_profile)
    topics = _curriculum_topics(curriculum_manifest)
    weak = _weak_spots(assessment_transcript, grade_learning_records, growth_profile)
    practice_ladder = _practice_ladder(grade_learning_records, assessment_transcript, topics)
    chunks = _pattern_chunks(topics, domain_focus)
    reasoning_entry_count = _reasoning_entry_count(reasoning_kibo)

    profile = {
        "schema": GENIUS_DERIVATION_PROFILE_SCHEMA,
        "created_at_utc": _now(),
        "profile_id": _stable_id(
            "genius-profile",
            identity.get("name"),
            domain_focus.get("track_id"),
            domain_focus.get("curriculum_id"),
        ),
        "status": "candidate_ready_for_training",
        "input_contract_validation": input_validation,
        "talent": {
            "name": identity.get("name"),
            "gender": identity.get("gender"),
            "primary_language": identity.get("language", "ko"),
        },
        "domain_focus": domain_focus,
        "design_claim": {
            "genius_definition": (
                "reviewable domain-specific performance produced by training, compression, "
                "timed trials, error correction, and transfer work"
            ),
            "not_general_superintelligence": True,
            "not_model_size_claim": True,
            "not_personality_injection": True,
            "human_capacity_analogy": (
                "same bounded brain-like capacity can behave differently when attention, chunks, "
                "practice pressure, and feedback loops are specialized"
            ),
        },
        "capacity_budget": {
            "strategy": "fixed_capacity_efficiency_over_raw_compute_scaling",
            "attention_allocation": {
                "primary_domain": 0.62,
                "adjacent_support_domains": 0.23,
                "general_life_and_communication": 0.10,
                "novelty_and_external_reference_quarantine": 0.05,
            },
            "search_policy": "practiced_chunks_and_minimal_needed_research_before_broad_search",
            "context_policy": "bounded_hot_context_with_reviewed_memory_only",
        },
        "deliberate_practice_program": {
            "cycle": REQUIRED_PRACTICE_CYCLE,
            "ladder": practice_ladder,
            "daily_training_rule": (
                "one focused domain problem, one timed attempt, one error note, "
                "one counterexample, one method revision"
            ),
            "promotion_rule": "only reviewed exams or verified work outcomes can harden a method",
        },
        "cognitive_kibo_targets": {
            "pattern_chunks": chunks,
            "compression_rules": [
                "name repeated evidence patterns as reusable chunks",
                "prefer a narrow practiced method when it fits the task",
                "record the condition where the method fails",
                "turn every serious error into a retest item",
            ],
            "quality_controls": [
                "source_before_claim",
                "counterexample_before_confidence",
                "time_box_before_broad_search",
                "reviewed_work_before_memory_promotion",
            ],
            "reasoning_entry_count": reasoning_entry_count,
        },
        "unevenness_profile": {
            "specialization_is_allowed_to_create_asymmetry": True,
            "expected_strength_biases": _as_list(_as_dict(_as_dict(growth_profile).get("asymmetry_profile")).get("strength_biases")),
            "accepted_tradeoffs": [
                "less breadth-first curiosity during high-pressure domain work",
                "slower response in unrelated domains when safety or evidence is thin",
                "stronger skepticism toward methods outside the trained major",
            ],
            "weakness_guardrails": weak
            or [
                "do not mistake narrow excellence for universal judgment",
                "ask for missing evidence outside the trained domain",
            ],
            "minimum_general_floor": [
                "safety boundaries",
                "honest uncertainty",
                "owner instruction priority",
                "basic communication clarity",
            ],
        },
        "scorecard": {
            "metrics": [
                {
                    "id": metric,
                    "target": "reviewed_improvement_over_repeated_trials",
                    "promotion_source": "exam_feedback_or_verified_work",
                }
                for metric in REQUIRED_SCORECARD_METRICS
            ],
            "profile_validation_threshold": {
                "purpose": "minimum evidence required to validate this training contract, not to prove genius",
                "minimum_training_evidence_units": 1,
                "minimum_reviewed_transfer_evidence_count": 1,
                "requires_growth_or_grade_learning_evidence": True,
                "requires_domain_scope_or_curriculum_evidence": True,
            },
            "genius_candidate_promotion_target": {
                "purpose": "long-term promotion target after repeated scored reviewed trials; not the base profile validation gate",
                "minimum_scored_reviewed_trials": 8,
                "minimum_average_score": 90,
                "requires_varied_transfer": True,
                "requires_documented_weaknesses": True,
            },
        },
        "evidence_summary": _evidence_counts(
            assessment_transcript,
            grade_learning_records,
            growth_profile,
            curriculum_topic_count=len(topics),
            practice_ladder_stage_count=len(practice_ladder),
        ),
        "research_basis": [
            {
                "id": "neural_efficiency",
                "use": "same capacity can differ by efficiency and task-focused activation",
                "source": "https://pubmed.ncbi.nlm.nih.gov/19580915/",
            },
            {
                "id": "deliberate_practice",
                "use": "expert performance requires structured practice, feedback, and increasing challenge",
                "source": "https://pubmed.ncbi.nlm.nih.gov/18778378/",
            },
            {
                "id": "chunking_expertise",
                "use": "experts compress familiar patterns into retrievable chunks",
                "source": "https://doi.org/10.1016/0010-0285(73)90004-2",
            },
            {
                "id": "reflexion_language_agents",
                "use": "verbal feedback can improve future agent decisions without weight updates",
                "source": "https://arxiv.org/abs/2303.11366",
            },
        ],
        "public_safe": {
            "network_call_performed": False,
            "private_reasoning_trace": "not_stored",
            "hidden_chain_of_thought": "forbidden",
            "raw_external_skill_text_promoted": False,
            "sensitive_values_exported": False,
            "sensitive_value_redaction_policy": "obvious_provider_sensitive_values_are_replaced_before_export",
        },
    }
    profile = _redact_public_value(profile)
    profile["validation"] = validate_genius_derivation_profile(profile)
    profile["promotion"] = evaluate_genius_candidate_promotion(profile)
    profile["status"] = _profile_status(profile["validation"], profile["promotion"])
    if output_path is not None:
        write_genius_derivation_profile(output_path, profile)
    return profile


def validate_genius_derivation_profile(profile: dict[str, Any]) -> dict[str, Any]:
    cycle = _as_list(_as_dict(profile.get("deliberate_practice_program")).get("cycle"))
    scorecard = _as_dict(profile.get("scorecard"))
    metric_ids = {
        str(item.get("id"))
        for item in _as_list(scorecard.get("metrics"))
        if isinstance(item, dict) and item.get("id")
    }
    public_safe = _as_dict(profile.get("public_safe"))
    design_claim = _as_dict(profile.get("design_claim"))
    capacity = _as_dict(profile.get("capacity_budget"))
    unevenness = _as_dict(profile.get("unevenness_profile"))
    evidence = _as_dict(profile.get("evidence_summary"))
    domain_focus = _as_dict(profile.get("domain_focus"))
    profile_validation_threshold = _as_dict(scorecard.get("profile_validation_threshold"))
    genius_candidate_target = _as_dict(scorecard.get("genius_candidate_promotion_target"))
    evidence_check_ids = {
        "training_evidence_present",
        "reviewed_transfer_or_assessment_present",
        "growth_or_grade_learning_evidence_present",
        "domain_scope_or_curriculum_evidence_present",
    }
    checks = {
        "schema": profile.get("schema") == GENIUS_DERIVATION_PROFILE_SCHEMA,
        "domain_focus_present": bool(domain_focus.get("primary_domain")),
        "genius_not_general_superintelligence": design_claim.get("not_general_superintelligence") is True,
        "genius_not_model_size_claim": design_claim.get("not_model_size_claim") is True,
        "fixed_capacity_strategy": capacity.get("strategy") == "fixed_capacity_efficiency_over_raw_compute_scaling",
        "training_evidence_present": int(evidence.get("training_evidence_unit_count") or 0) > 0,
        "reviewed_transfer_or_assessment_present": int(evidence.get("reviewed_transfer_evidence_count") or 0) > 0,
        "growth_or_grade_learning_evidence_present": (
            bool(evidence.get("growth_profile_present"))
            or int(evidence.get("grade_learning_record_count") or 0) > 0
        ),
        "domain_scope_or_curriculum_evidence_present": (
            bool(domain_focus.get("privileged_domains"))
            or int(evidence.get("curriculum_topic_count") or 0) > 0
        ),
        "practice_cycle_complete": cycle == REQUIRED_PRACTICE_CYCLE,
        "timed_trials_required": "timed_trial" in cycle,
        "method_distillation_required": "method_distillation" in cycle,
        "varied_transfer_required": "varied_transfer" in cycle,
        "scorecard_complete": set(REQUIRED_SCORECARD_METRICS) <= metric_ids,
        "profile_validation_threshold_explicit": (
            profile_validation_threshold.get("minimum_training_evidence_units") == 1
            and profile_validation_threshold.get("minimum_reviewed_transfer_evidence_count") == 1
            and profile_validation_threshold.get("requires_growth_or_grade_learning_evidence") is True
            and profile_validation_threshold.get("requires_domain_scope_or_curriculum_evidence") is True
        ),
        "genius_promotion_target_not_base_validation_gate": (
            genius_candidate_target.get("purpose")
            == "long-term promotion target after repeated scored reviewed trials; not the base profile validation gate"
        ),
        "asymmetry_explicit": unevenness.get("specialization_is_allowed_to_create_asymmetry") is True,
        "weakness_guardrails_present": bool(_as_list(unevenness.get("weakness_guardrails"))),
        "no_network_call": public_safe.get("network_call_performed") is False,
        "no_private_reasoning_trace": public_safe.get("private_reasoning_trace") == "not_stored",
        "no_external_skill_raw_promotion": public_safe.get("raw_external_skill_text_promoted") is False,
    }
    failed = [check_id for check_id, passed in checks.items() if not passed]
    status = "passed"
    if failed:
        status = "needs_training_evidence" if any(item in evidence_check_ids for item in failed) else "failed"
    contract_status = "minimum_evidence_contract_passed" if not failed else status
    return {
        "schema": GENIUS_DERIVATION_VALIDATION_SCHEMA,
        "status": status,
        "contract_status": contract_status,
        "passed": not failed,
        "checks": checks,
        "failed_checks": failed,
    }


def evaluate_genius_candidate_promotion(profile: dict[str, Any]) -> dict[str, Any]:
    """Evaluate the stricter long-term genius candidate promotion gate."""

    validation = _as_dict(profile.get("validation"))
    scorecard = _as_dict(profile.get("scorecard"))
    target = _as_dict(scorecard.get("genius_candidate_promotion_target"))
    evidence = _as_dict(profile.get("evidence_summary"))
    unevenness = _as_dict(profile.get("unevenness_profile"))

    minimum_trials = int(target.get("minimum_scored_reviewed_trials") or target.get("minimum_reviewed_trials") or 8)
    minimum_average = float(target.get("minimum_average_score") or 90)
    requires_varied_transfer = target.get("requires_varied_transfer") is True
    requires_documented_weaknesses = target.get("requires_documented_weaknesses") is True
    reviewed_trials = int(evidence.get("reviewed_transfer_evidence_count") or 0)
    scored_reviewed_trials = int(evidence.get("scored_reviewed_trial_count") or 0)
    average_score = float(evidence.get("assessment_average_score") or 0)
    varied_transfer_count = int(evidence.get("varied_transfer_evidence_count") or 0)
    weakness_guardrails = _as_list(unevenness.get("weakness_guardrails"))

    checks = {
        "training_contract_valid": validation.get("passed") is True,
        "minimum_scored_reviewed_trials_met": scored_reviewed_trials >= minimum_trials,
        "minimum_average_score_met": average_score >= minimum_average,
        "varied_transfer_met": (not requires_varied_transfer) or varied_transfer_count >= 2,
        "documented_weaknesses_present": (not requires_documented_weaknesses) or bool(weakness_guardrails),
    }
    failed = [check_id for check_id, passed in checks.items() if not passed]
    promoted = not failed
    return {
        "schema": GENIUS_CANDIDATE_PROMOTION_SCHEMA,
        "status": GENIUS_CANDIDATE_PROMOTED_STATUS if promoted else "not_ready",
        "promoted": promoted,
        "checks": checks,
        "failed_checks": failed,
        "observed": {
            "reviewed_trials": reviewed_trials,
            "scored_reviewed_trials": scored_reviewed_trials,
            "assessment_average_score": average_score,
            "varied_transfer_evidence_count": varied_transfer_count,
            "weakness_guardrail_count": len(weakness_guardrails),
        },
        "required": {
            "minimum_scored_reviewed_trials": minimum_trials,
            "minimum_average_score": minimum_average,
            "requires_varied_transfer": requires_varied_transfer,
            "requires_documented_weaknesses": requires_documented_weaknesses,
        },
    }


def _profile_status(validation: dict[str, Any], promotion: dict[str, Any]) -> str:
    if promotion.get("promoted") is True:
        return GENIUS_CANDIDATE_PROMOTED_STATUS
    if validation.get("passed") is True:
        return TRAINING_CONTRACT_VALID_STATUS
    if validation.get("status") == "needs_training_evidence":
        return DRAFT_STATUS
    return FAILED_STATUS


def write_genius_derivation_profile(path: Path, profile: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def read_genius_derivation_profile(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
