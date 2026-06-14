# Validation Rules

[English](validation_rules.en.md)

이 문서는 `validation`이 무엇을 보고, 무엇을 보지 않는지 정리합니다.

## 입력 계약

필수 blueprint 조건:

| 필드 | 기준 |
| --- | --- |
| `schema` | `ai-talent-training-blueprint/v1` |
| `identity.name` | 비어 있지 않은 문자열 |
| `track.track_id` | 비어 있지 않은 문자열 |
| `track.domains` | 하나 이상의 문자열을 가진 배열 |

선택 입력도 shape를 검증합니다.

- `assessment_transcript.results`는 list여야 합니다.
- 각 assessment result의 `passed`는 boolean이어야 합니다.
- `grade_learning_records.records[]`는 object여야 합니다.
- assignment가 있으면 `status`가 필요합니다.
- Reasoning Kibo JSONL은 각 줄이 JSON object여야 합니다.

## Evidence quality floor

Assessment는 `passed: true`만으로 reviewed evidence가 되지 않습니다.

| 항목 | 기준 |
| --- | --- |
| `score`가 있는 경우 | `score >= 80` |
| `rubric_scores`가 있는 경우 | 모든 numeric score가 20 이상 |
| quality floor 실패 | 약점 기록에는 반영될 수 있지만 reviewed evidence에는 미포함 |

## CLI 종료 코드

| 종료 코드 | 의미 |
| --- | --- |
| `0` | profile 생성 성공. `--allow-draft`가 있으면 draft도 성공으로 봅니다. |
| `2` | 입력 오류, schema 오류, 또는 `--allow-draft` 없는 evidence 부족입니다. 실패 artifact는 output 경로에 기록됩니다. |

## 공개 안전 규칙

- 네트워크 호출 없음
- API key/OAuth token 저장 없음
- hidden chain-of-thought 저장 없음
- Reasoning Kibo 원문 미저장, entry count만 반영
- 명백한 provider token 문자열은 `[redacted-sensitive-value]`로 마스킹
