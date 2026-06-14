from __future__ import annotations

from paideia_genius_derivation import build_genius_derivation_profile


BLUEPRINT = {
    "schema": "ai-talent-training-blueprint/v1",
    "identity": {
        "name": "Mira",
        "language": "ko",
        "major_goal": "securities research specialist",
    },
    "track": {
        "track_id": "securities_research_phd",
        "name": "Securities Research PhD Track",
        "target_role": "securities research agent",
        "domains": ["valuation", "risk analysis"],
    },
}

ASSESSMENT_TRANSCRIPT = {
    "results": [
        {
            "gate_id": "valuation_case_report",
            "passed": True,
            "score": 92,
            "rubric_scores": {
                "evidence_precision": 24,
                "counterexample_depth": 23,
            },
            "weak_spots": ["overfocus_on_downside"],
        }
    ]
}

GROWTH_PROFILE = {
    "schema": "paideia-growth-profile/v1",
    "asymmetry_profile": {
        "strength_biases": ["slow valuation patience"],
        "growth_costs": ["can overfocus on downside"],
        "domain_obsession": "securities_research",
    },
}

GRADE_LEARNING_RECORDS = {
    "records": [
        {
            "year_id": "doctoral_year_1",
            "education_stage": "doctoral_research",
            "learning_data": ["valuation memo", "risk checklist"],
            "assignments": [{"status": "completed_and_reviewed"}],
        }
    ]
}


def main() -> None:
    profile = build_genius_derivation_profile(
        BLUEPRINT,
        assessment_transcript=ASSESSMENT_TRANSCRIPT,
        growth_profile=GROWTH_PROFILE,
        grade_learning_records=GRADE_LEARNING_RECORDS,
    )

    print("status:", profile["status"])
    print("contract_status:", profile["validation"]["contract_status"])
    print("promotion_status:", profile["promotion"]["status"])
    print("scored_reviewed_trials:", profile["promotion"]["observed"]["scored_reviewed_trials"])


if __name__ == "__main__":
    main()
