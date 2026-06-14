from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from .genius_derivation import build_genius_derivation_profile


def _read_json(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_reasoning_kibo_jsonl(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    entries: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            item = json.loads(stripped)
            if isinstance(item, dict):
                entries.append(item)
    return {"entries": entries}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paideia-genius-profile",
        description="Build and validate a public-safe Paideia domain genius derivation profile.",
    )
    subparsers = parser.add_subparsers(dest="command")

    build_profile = subparsers.add_parser(
        "build-profile",
        help="Build a genius derivation profile from a training blueprint and optional evidence files.",
    )
    build_profile.add_argument("--blueprint", required=True, help="Training blueprint JSON path.")
    build_profile.add_argument("--curriculum", help="Curriculum manifest JSON path.")
    build_profile.add_argument("--assessment-transcript", help="Assessment transcript JSON path.")
    build_profile.add_argument("--growth-profile", help="Growth profile JSON path.")
    build_profile.add_argument("--grade-learning-records", help="Grade learning records JSON path.")
    build_profile.add_argument("--reasoning-kibo", help="Reasoning kibo JSONL path.")
    build_profile.add_argument(
        "--allow-draft",
        action="store_true",
        help="Return success for a blueprint-only draft that still needs training evidence.",
    )
    build_profile.add_argument("--output", required=True, help="Output profile JSON path.")
    return parser


def _write_failure_profile(output_path: Path, error: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "schema": "paideia-genius-derivation-profile/v1",
                "status": "failed",
                "validation": {
                    "schema": "paideia-genius-derivation-profile-validation/v1",
                    "status": "failed",
                    "passed": False,
                    "failed_checks": ["unsupported_training_blueprint_schema"],
                },
                "error": error,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "build-profile":
        output_path = Path(args.output)
        try:
            blueprint = _read_json(args.blueprint)
            if blueprint is None:
                raise ValueError("Missing training blueprint")
            profile = build_genius_derivation_profile(
                blueprint,
                curriculum_manifest=_read_json(args.curriculum),
                assessment_transcript=_read_json(args.assessment_transcript),
                growth_profile=_read_json(args.growth_profile),
                grade_learning_records=_read_json(args.grade_learning_records),
                reasoning_kibo=_read_reasoning_kibo_jsonl(args.reasoning_kibo),
                output_path=output_path,
            )
        except ValueError as exc:
            _write_failure_profile(output_path, str(exc))
            print(str(output_path))
            return 2

        print(str(output_path))
        if profile["validation"]["status"] == "needs_training_evidence" and args.allow_draft:
            return 0
        return 0 if profile["validation"]["passed"] else 2

    parser.print_help()
    return 2
