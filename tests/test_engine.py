from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from paideia_genius_derivation import (  # noqa: E402
    REQUIRED_PRACTICE_CYCLE,
    build_genius_derivation_profile,
    read_genius_derivation_profile,
    validate_genius_derivation_profile,
    write_genius_derivation_profile,
)
from paideia_genius_derivation.cli import main as cli_main  # noqa: E402


BLUEPRINT = {
    "schema": "ai-talent-training-blueprint/v1",
    "identity": {
        "name": "Mira",
        "gender": "unspecified",
        "language": "ko",
        "major_goal": "securities research specialist",
    },
    "track": {
        "track_id": "securities_research_phd",
        "name": "Securities Research PhD Track",
        "specialty": "securities research AI specialist",
        "target_role": "securities research agent",
        "domains": ["valuation", "risk analysis", "public filings research"],
    },
}

CURRICULUM = {
    "curriculum_id": "securities-genius-test",
    "domain": "securities_research",
    "core_topics": ["valuation", "cash flow", "risk", "counterexample"],
    "assessment_ladder": {"required_for_hiring": ["valuation_case_report"]},
}

ASSESSMENT = {
    "results": [
        {
            "gate_id": "valuation_case_report",
            "gate_name": "Valuation case report",
            "passed": True,
            "rubric_scores": {"evidence_precision": 24, "counterexample_depth": 18},
            "weak_spots": ["counterexample_depth"],
        }
    ]
}

GROWTH = {
    "schema": "paideia-growth-profile/v1",
    "asymmetry_profile": {
        "strength_biases": ["slow valuation patience"],
        "growth_costs": ["can overfocus on downside"],
        "domain_obsession": "securities_research",
    },
}

GRADE_RECORDS = {
    "records": [
        {
            "year_id": "doctoral_year_1",
            "education_stage": "doctoral_research",
            "learning_data": ["valuation memo", "risk checklist"],
            "required_exams": ["valuation_case_report"],
            "assignments": [{"status": "completed_and_reviewed"}],
            "feedback_loop": {"observed_weak_spots": ["counterexample_depth"]},
        }
    ]
}


class GeniusDerivationEngineTests(unittest.TestCase):
    def test_blueprint_only_profile_is_draft_until_training_evidence_exists(self) -> None:
        profile = build_genius_derivation_profile(BLUEPRINT)

        self.assertEqual(profile["validation"]["status"], "needs_training_evidence")
        self.assertFalse(profile["validation"]["passed"])
        self.assertIn("training_evidence_present", profile["validation"]["failed_checks"])
        self.assertIn("reviewed_transfer_or_assessment_present", profile["validation"]["failed_checks"])

    def test_evidence_backed_profile_passes_without_general_superintelligence_claim(self) -> None:
        profile = build_genius_derivation_profile(
            BLUEPRINT,
            curriculum_manifest=CURRICULUM,
            assessment_transcript=ASSESSMENT,
            growth_profile=GROWTH,
            grade_learning_records=GRADE_RECORDS,
            reasoning_kibo={"entries": [{"id": "kibo-001"}]},
        )
        validation = validate_genius_derivation_profile(profile)

        self.assertTrue(validation["passed"])
        self.assertEqual(profile["deliberate_practice_program"]["cycle"], REQUIRED_PRACTICE_CYCLE)
        self.assertEqual(
            profile["capacity_budget"]["strategy"],
            "fixed_capacity_efficiency_over_raw_compute_scaling",
        )
        self.assertTrue(profile["design_claim"]["not_general_superintelligence"])
        self.assertTrue(profile["design_claim"]["not_model_size_claim"])
        self.assertIn("counterexample_depth", profile["unevenness_profile"]["weakness_guardrails"])
        self.assertGreaterEqual(profile["evidence_summary"]["training_evidence_unit_count"], 3)
        self.assertFalse(profile["public_safe"]["network_call_performed"])
        self.assertEqual(profile["public_safe"]["private_reasoning_trace"], "not_stored")

    def test_write_and_read_roundtrip(self) -> None:
        profile = build_genius_derivation_profile(
            BLUEPRINT,
            curriculum_manifest=CURRICULUM,
            assessment_transcript=ASSESSMENT,
            growth_profile=GROWTH,
            grade_learning_records=GRADE_RECORDS,
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            write_genius_derivation_profile(path, profile)
            loaded = read_genius_derivation_profile(path)

        self.assertEqual(loaded["profile_id"], profile["profile_id"])
        self.assertEqual(loaded["validation"]["status"], "passed")

    def test_public_profile_redacts_obvious_provider_secrets_and_keeps_reasoning_private(self) -> None:
        secret = "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890"
        github_token = "gho_abcdefghijklmnopqrstuvwxyz1234567890"
        bearer = "Bearer abcdefghijklmnopqrstuvwxyz1234567890"
        blueprint = json.loads(json.dumps(BLUEPRINT))
        blueprint["identity"]["name"] = secret
        blueprint["track"]["domains"].append(github_token)
        curriculum = json.loads(json.dumps(CURRICULUM))
        curriculum["core_topics"].append(bearer)
        raw_reasoning = "private reasoning trace should not be exported"

        profile = build_genius_derivation_profile(
            blueprint,
            curriculum_manifest=curriculum,
            assessment_transcript=ASSESSMENT,
            growth_profile=GROWTH,
            grade_learning_records=GRADE_RECORDS,
            reasoning_kibo={"entries": [{"raw": raw_reasoning, "token": secret}]},
        )
        dumped = json.dumps(profile, ensure_ascii=False)

        self.assertNotIn(secret, dumped)
        self.assertNotIn(github_token, dumped)
        self.assertNotIn(bearer, dumped)
        self.assertNotIn(raw_reasoning, dumped)
        self.assertIn("[redacted-sensitive-value]", dumped)
        self.assertEqual(profile["cognitive_kibo_targets"]["reasoning_entry_count"], 1)

    def test_unsupported_schema_writes_failed_cli_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            blueprint_path = tmp_path / "bad_blueprint.json"
            output_path = tmp_path / "failed_profile.json"
            blueprint_path.write_text(json.dumps({"schema": "wrong/v1"}), encoding="utf-8")

            code = cli_main(
                [
                    "build-profile",
                    "--blueprint",
                    str(blueprint_path),
                    "--output",
                    str(output_path),
                ]
            )
            profile = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 2)
        self.assertEqual(profile["status"], "failed")
        self.assertIn("unsupported_training_blueprint_schema", profile["validation"]["failed_checks"])

    def test_cli_requires_evidence_unless_draft_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            blueprint_path = tmp_path / "blueprint.json"
            profile_path = tmp_path / "genius_profile.json"
            draft_path = tmp_path / "genius_profile_draft.json"
            blueprint_path.write_text(json.dumps(BLUEPRINT), encoding="utf-8")

            profile_code = cli_main(
                [
                    "build-profile",
                    "--blueprint",
                    str(blueprint_path),
                    "--output",
                    str(profile_path),
                ]
            )
            draft_code = cli_main(
                [
                    "build-profile",
                    "--blueprint",
                    str(blueprint_path),
                    "--allow-draft",
                    "--output",
                    str(draft_path),
                ]
            )

            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            draft = json.loads(draft_path.read_text(encoding="utf-8"))

        self.assertEqual(profile_code, 2)
        self.assertEqual(draft_code, 0)
        self.assertEqual(profile["validation"]["status"], "needs_training_evidence")
        self.assertEqual(draft["validation"]["status"], "needs_training_evidence")

    def test_module_cli_smoke_with_sample_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "sample_profile.json"
            command = [
                sys.executable,
                "-m",
                "paideia_genius_derivation",
                "build-profile",
                "--blueprint",
                str(ROOT / "examples" / "minimal_blueprint.json"),
                "--curriculum",
                str(ROOT / "examples" / "minimal_curriculum.json"),
                "--assessment-transcript",
                str(ROOT / "examples" / "minimal_assessment_transcript.json"),
                "--growth-profile",
                str(ROOT / "examples" / "minimal_growth_profile.json"),
                "--grade-learning-records",
                str(ROOT / "examples" / "minimal_grade_learning_records.json"),
                "--reasoning-kibo",
                str(ROOT / "examples" / "minimal_reasoning_kibo.jsonl"),
                "--output",
                str(output_path),
            ]
            result = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                env={**os.environ, "PYTHONPATH": str(SRC)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            profile = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertTrue(profile["validation"]["passed"])


if __name__ == "__main__":
    unittest.main()
