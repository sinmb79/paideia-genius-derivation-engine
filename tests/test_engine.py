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
    evaluate_genius_candidate_promotion,
    read_genius_derivation_profile,
    validate_genius_derivation_inputs,
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

        self.assertEqual(profile["status"], "draft")
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
        self.assertEqual(profile["status"], "training_contract_valid")
        self.assertEqual(profile["validation"]["contract_status"], "minimum_evidence_contract_passed")
        self.assertEqual(profile["promotion"]["status"], "not_ready")
        self.assertEqual(profile["deliberate_practice_program"]["cycle"], REQUIRED_PRACTICE_CYCLE)
        self.assertEqual(
            profile["capacity_budget"]["strategy"],
            "fixed_capacity_efficiency_over_raw_compute_scaling",
        )
        self.assertTrue(profile["design_claim"]["not_general_superintelligence"])
        self.assertTrue(profile["design_claim"]["not_model_size_claim"])
        self.assertIn("counterexample_depth", profile["unevenness_profile"]["weakness_guardrails"])
        self.assertEqual(profile["curriculum_backlog"], [])
        self.assertEqual(profile["weakness_records"], [])
        self.assertEqual(profile["evidence_summary"]["qualified_passed_assessment_count"], 0)
        self.assertEqual(profile["evidence_summary"]["disqualified_passed_assessment_count"], 1)
        self.assertEqual(profile["evidence_summary"]["reviewed_assignment_count"], 1)
        self.assertGreaterEqual(profile["evidence_summary"]["training_evidence_unit_count"], 2)
        self.assertEqual(
            profile["scorecard"]["profile_validation_threshold"]["purpose"],
            "minimum evidence required to validate this training contract, not to prove genius",
        )
        self.assertEqual(
            profile["scorecard"]["genius_candidate_promotion_target"]["purpose"],
            "long-term promotion target after repeated scored reviewed trials; not the base profile validation gate",
        )
        self.assertFalse(profile["public_safe"]["network_call_performed"])
        self.assertEqual(profile["public_safe"]["private_reasoning_trace"], "not_stored")

    def test_profile_builder_accepts_curriculum_backlog_and_weakness_records(self) -> None:
        weakness = {
            "schema": "paideia-weakness-record/v1",
            "weakness_id": "weakness-risk",
            "owner": "Boss",
            "domain": "investment_research",
            "skill_id": "risk_analysis",
            "weakness_type": "risk_gap",
            "evidence_refs": ["failure-1"],
            "severity": 0.75,
            "recurrence_count": 1,
        }
        profile = build_genius_derivation_profile(
            BLUEPRINT,
            curriculum_manifest=CURRICULUM,
            assessment_transcript=ASSESSMENT,
            growth_profile=GROWTH,
            grade_learning_records=GRADE_RECORDS,
            curriculum_backlog=[{"curriculum_id": "curriculum-risk", "skill_id": "risk_analysis"}],
            weakness_records=[weakness],
        )

        self.assertEqual(profile["curriculum_backlog"][0]["curriculum_id"], "curriculum-risk")
        self.assertEqual(profile["weakness_records"][0]["weakness_id"], "weakness-risk")

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
        self.assertEqual(loaded["status"], "training_contract_valid")

    def test_input_contract_requires_identity_track_and_domains(self) -> None:
        invalid = json.loads(json.dumps(BLUEPRINT))
        invalid["identity"]["name"] = ""
        invalid["track"]["domains"] = []

        validation = validate_genius_derivation_inputs(invalid)

        self.assertFalse(validation["passed"])
        self.assertIn("identity_name", validation["failed_checks"])
        self.assertIn("track_domains", validation["failed_checks"])
        with self.assertRaisesRegex(ValueError, "identity_name"):
            build_genius_derivation_profile(invalid)

    def test_invalid_optional_input_shape_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "assessment_results_list"):
            build_genius_derivation_profile(
                BLUEPRINT,
                curriculum_manifest=CURRICULUM,
                assessment_transcript={"results": "not-a-list"},
            )

    def test_grade_records_require_record_objects(self) -> None:
        with self.assertRaisesRegex(ValueError, "grade_record_object"):
            build_genius_derivation_profile(
                BLUEPRINT,
                curriculum_manifest=CURRICULUM,
                grade_learning_records={"records": ["bad-record"]},
            )

    def test_low_score_assessment_does_not_count_as_reviewed_evidence(self) -> None:
        profile = build_genius_derivation_profile(
            BLUEPRINT,
            curriculum_manifest=CURRICULUM,
            assessment_transcript=ASSESSMENT,
            growth_profile=GROWTH,
        )

        self.assertEqual(profile["status"], "draft")
        self.assertEqual(profile["evidence_summary"]["qualified_passed_assessment_count"], 0)
        self.assertEqual(profile["evidence_summary"]["reviewed_transfer_evidence_count"], 0)
        self.assertIn("reviewed_transfer_or_assessment_present", profile["validation"]["failed_checks"])

    def test_unreviewed_assignment_does_not_count_as_reviewed_transfer(self) -> None:
        unreviewed_records = {
            "records": [
                {
                    "year_id": "doctoral_year_1",
                    "education_stage": "doctoral_research",
                    "learning_data": ["valuation memo"],
                    "assignments": [{"status": "submitted"}],
                }
            ]
        }

        profile = build_genius_derivation_profile(
            BLUEPRINT,
            curriculum_manifest=CURRICULUM,
            growth_profile=GROWTH,
            grade_learning_records=unreviewed_records,
        )

        self.assertEqual(profile["status"], "draft")
        self.assertEqual(profile["evidence_summary"]["unreviewed_assignment_count"], 1)
        self.assertEqual(profile["evidence_summary"]["reviewed_transfer_evidence_count"], 0)
        self.assertIn("reviewed_transfer_or_assessment_present", profile["validation"]["failed_checks"])

    def test_genius_candidate_promotion_requires_stricter_long_term_gate(self) -> None:
        transcript = {
            "results": [
                {
                    "gate_id": f"transfer_gate_{index}",
                    "passed": True,
                    "score": 95,
                    "rubric_scores": {"evidence_precision": 24, "counterexample_depth": 24},
                    "weak_spots": ["overconfidence"],
                }
                for index in range(8)
            ]
        }

        profile = build_genius_derivation_profile(
            BLUEPRINT,
            curriculum_manifest=CURRICULUM,
            assessment_transcript=transcript,
            growth_profile=GROWTH,
        )
        promotion = evaluate_genius_candidate_promotion(profile)

        self.assertEqual(profile["status"], "genius_candidate_promoted")
        self.assertTrue(promotion["promoted"])
        self.assertEqual(promotion["observed"]["reviewed_trials"], 8)
        self.assertEqual(promotion["observed"]["scored_reviewed_trials"], 8)
        self.assertEqual(promotion["observed"]["assessment_average_score"], 95.0)

    def test_genius_candidate_promotion_requires_eight_scored_reviewed_trials(self) -> None:
        transcript = {
            "results": [
                {
                    "gate_id": "one_high_score_gate",
                    "passed": True,
                    "score": 95,
                    "rubric_scores": {"evidence_precision": 24, "counterexample_depth": 24},
                    "weak_spots": ["overconfidence"],
                }
            ]
        }
        records = {
            "records": [
                {
                    "year_id": f"reviewed_assignment_{index}",
                    "education_stage": f"transfer_stage_{index}",
                    "learning_data": ["transfer work"],
                    "assignments": [{"status": "completed_and_reviewed"}],
                }
                for index in range(7)
            ]
        }

        profile = build_genius_derivation_profile(
            BLUEPRINT,
            curriculum_manifest=CURRICULUM,
            assessment_transcript=transcript,
            growth_profile=GROWTH,
            grade_learning_records=records,
        )

        self.assertEqual(profile["status"], "training_contract_valid")
        self.assertEqual(profile["promotion"]["observed"]["reviewed_trials"], 8)
        self.assertEqual(profile["promotion"]["observed"]["scored_reviewed_trials"], 1)
        self.assertIn("minimum_scored_reviewed_trials_met", profile["promotion"]["failed_checks"])

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

    def test_cli_counts_reasoning_kibo_jsonl_without_exporting_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            blueprint_path = tmp_path / "blueprint.json"
            kibo_path = tmp_path / "large_reasoning_kibo.jsonl"
            output_path = tmp_path / "draft_profile.json"
            blueprint_path.write_text(json.dumps(BLUEPRINT), encoding="utf-8")
            kibo_path.write_text(
                "\n".join(json.dumps({"id": f"kibo-{index}", "raw": "do-not-export-raw-kibo"}) for index in range(1000)),
                encoding="utf-8",
            )

            code = cli_main(
                [
                    "build-profile",
                    "--blueprint",
                    str(blueprint_path),
                    "--reasoning-kibo",
                    str(kibo_path),
                    "--allow-draft",
                    "--output",
                    str(output_path),
                ]
            )
            profile = json.loads(output_path.read_text(encoding="utf-8"))
            dumped = json.dumps(profile)

        self.assertEqual(code, 0)
        self.assertEqual(profile["cognitive_kibo_targets"]["reasoning_entry_count"], 1000)
        self.assertNotIn("do-not-export-raw-kibo", dumped)
        self.assertNotIn('"entries"', dumped)

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

    def test_cli_writes_controlled_failure_for_missing_file_and_bad_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            missing_output = tmp_path / "missing_profile.json"
            bad_shape_path = tmp_path / "bad_shape.json"
            bad_shape_output = tmp_path / "bad_shape_profile.json"
            bad_shape_path.write_text(json.dumps([BLUEPRINT]), encoding="utf-8")

            missing_code = cli_main(
                [
                    "build-profile",
                    "--blueprint",
                    str(tmp_path / "missing_blueprint.json"),
                    "--output",
                    str(missing_output),
                ]
            )
            bad_shape_code = cli_main(
                [
                    "build-profile",
                    "--blueprint",
                    str(bad_shape_path),
                    "--output",
                    str(bad_shape_output),
                ]
            )
            missing_profile = json.loads(missing_output.read_text(encoding="utf-8"))
            bad_shape_profile = json.loads(bad_shape_output.read_text(encoding="utf-8"))

        self.assertEqual(missing_code, 2)
        self.assertEqual(bad_shape_code, 2)
        self.assertEqual(missing_profile["validation"]["failed_checks"], ["input_file_not_found"])
        self.assertEqual(bad_shape_profile["validation"]["failed_checks"], ["invalid_input_shape"])

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

    def test_cli_accepts_curriculum_backlog_and_weakness_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            blueprint_path = tmp_path / "blueprint.json"
            curriculum_path = tmp_path / "curriculum.json"
            assessment_path = tmp_path / "assessment.json"
            growth_path = tmp_path / "growth.json"
            records_path = tmp_path / "records.json"
            backlog_path = tmp_path / "backlog.json"
            weakness_path = tmp_path / "weakness.jsonl"
            output_path = tmp_path / "profile.json"
            blueprint_path.write_text(json.dumps(BLUEPRINT), encoding="utf-8")
            curriculum_path.write_text(json.dumps(CURRICULUM), encoding="utf-8")
            assessment_path.write_text(json.dumps(ASSESSMENT), encoding="utf-8")
            growth_path.write_text(json.dumps(GROWTH), encoding="utf-8")
            records_path.write_text(json.dumps(GRADE_RECORDS), encoding="utf-8")
            backlog_path.write_text(
                json.dumps([{"curriculum_id": "curriculum-risk", "skill_id": "risk_analysis"}]),
                encoding="utf-8",
            )
            weakness_path.write_text(
                json.dumps(
                    {
                        "schema": "paideia-weakness-record/v1",
                        "weakness_id": "weakness-risk",
                        "owner": "Boss",
                        "domain": "investment_research",
                        "skill_id": "risk_analysis",
                        "weakness_type": "risk_gap",
                        "evidence_refs": ["failure-1"],
                        "severity": 0.75,
                        "recurrence_count": 1,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            code = cli_main(
                [
                    "build-profile",
                    "--blueprint",
                    str(blueprint_path),
                    "--curriculum",
                    str(curriculum_path),
                    "--assessment-transcript",
                    str(assessment_path),
                    "--growth-profile",
                    str(growth_path),
                    "--grade-learning-records",
                    str(records_path),
                    "--curriculum-backlog",
                    str(backlog_path),
                    "--weakness-records",
                    str(weakness_path),
                    "--output",
                    str(output_path),
                ]
            )
            profile = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(profile["curriculum_backlog"][0]["curriculum_id"], "curriculum-risk")
        self.assertEqual(profile["weakness_records"][0]["weakness_id"], "weakness-risk")

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
