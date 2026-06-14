from __future__ import annotations

from copy import deepcopy

from paideia_genius_derivation import build_genius_derivation_profile


BLUEPRINT = {
    "schema": "ai-talent-training-blueprint/v1",
    "identity": {"name": "Mira", "language": "ko"},
    "track": {
        "track_id": "securities_research_phd",
        "name": "Securities Research PhD Track",
        "domains": ["valuation", "risk analysis", "public filings research"],
    },
}

CURRICULUM = {
    "curriculum_id": "securities-genius-track",
    "domain": "securities_research",
    "core_topics": ["valuation", "risk", "filings", "counterexample"],
}

GROWTH_PROFILE = {
    "schema": "paideia-growth-profile/v1",
    "asymmetry_profile": {
        "strength_biases": ["valuation patience"],
        "growth_costs": ["overconfidence after repeated wins"],
        "domain_obsession": "securities_research",
    },
}


def scored_trials(count: int, score: int) -> dict[str, object]:
    return {
        "results": [
            {
                "gate_id": f"transfer_gate_{index}",
                "passed": True,
                "score": score,
                "rubric_scores": {
                    "evidence_precision": 24,
                    "counterexample_depth": 24,
                },
                "weak_spots": ["overconfidence"],
            }
            for index in range(count)
        ]
    }


def reviewed_assignments(count: int) -> dict[str, object]:
    return {
        "records": [
            {
                "year_id": f"reviewed_assignment_{index}",
                "education_stage": f"transfer_stage_{index}",
                "learning_data": ["transfer work"],
                "assignments": [{"status": "completed_and_reviewed"}],
            }
            for index in range(count)
        ]
    }


def summarize(label: str, profile: dict[str, object]) -> None:
    promotion = profile["promotion"]
    assert isinstance(promotion, dict)
    print(f"\n{label}")
    print("status:", profile["status"])
    print("promotion:", promotion["status"])
    print("observed:", promotion["observed"])
    print("failed_checks:", promotion["failed_checks"])


def main() -> None:
    shortcut_case = build_genius_derivation_profile(
        deepcopy(BLUEPRINT),
        curriculum_manifest=CURRICULUM,
        assessment_transcript=scored_trials(1, 95),
        growth_profile=GROWTH_PROFILE,
        grade_learning_records=reviewed_assignments(7),
    )
    summarize("Shortcut blocked: 1 high-score trial + 7 reviewed assignments", shortcut_case)

    promoted_case = build_genius_derivation_profile(
        deepcopy(BLUEPRINT),
        curriculum_manifest=CURRICULUM,
        assessment_transcript=scored_trials(8, 95),
        growth_profile=GROWTH_PROFILE,
    )
    summarize("Promoted: 8 scored reviewed trials", promoted_case)


if __name__ == "__main__":
    main()
