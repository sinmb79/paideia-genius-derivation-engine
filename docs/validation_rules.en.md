# Validation Rules

[한국어](validation_rules.ko.md)

This document defines what `validation` checks and what it does not claim.

## Input Contract

Required blueprint fields:

| Field | Requirement |
| --- | --- |
| `schema` | `ai-talent-training-blueprint/v1` |
| `identity.name` | Non-empty string |
| `track.track_id` | Non-empty string |
| `track.domains` | Array containing at least one string |

Optional inputs are shape-checked as well.

- `assessment_transcript.results` must be a list.
- Each assessment result needs boolean `passed`.
- `grade_learning_records.records[]` must contain objects.
- Assignments need `status` when present.
- Each Reasoning Kibo JSONL line must be a JSON object.

## Evidence Quality Floor

An assessment does not become reviewed evidence merely by setting `passed: true`.

| Item | Requirement |
| --- | --- |
| When `score` is present | `score >= 80` |
| When `rubric_scores` are present | Every numeric score is at least 20 |
| Quality floor failure | May contribute weakness records, but not reviewed evidence |

## CLI Exit Codes

| Exit code | Meaning |
| --- | --- |
| `0` | Profile generated successfully. With `--allow-draft`, a draft is also accepted. |
| `2` | Input error, schema error, or insufficient evidence without `--allow-draft`. A failure artifact is written to the output path. |

## Public-Safe Rules

- No network calls
- No API key or OAuth token storage
- No hidden chain-of-thought storage
- Reasoning Kibo raw entries are not stored; only entry count is reflected
- Obvious provider tokens are masked as `[redacted-sensitive-value]`
