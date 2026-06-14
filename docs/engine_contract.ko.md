# 엔진 계약

[English](engine_contract.en.md)

이 문서는 Paideia 천재 도출 엔진의 입력과 출력 계약을 설명합니다.

## 입력

### Blueprint

필수 입력입니다.

```json
{
  "schema": "ai-talent-training-blueprint/v1",
  "identity": {
    "name": "Mira",
    "gender": "unspecified",
    "language": "ko",
    "major_goal": "securities research specialist"
  },
  "track": {
    "track_id": "securities_research_phd",
    "name": "Securities Research PhD Track",
    "target_role": "securities research agent",
    "domains": ["valuation", "risk analysis"]
  }
}
```

`schema`가 다르면 엔진 함수는 `ValueError`를 발생시키고, CLI는 실패 artifact를 쓴 뒤 종료 코드 `2`를 반환합니다.

### Curriculum Manifest

전공 범위, core topic, 평가 ladder를 제공합니다. 없으면 blueprint만으로 초안을 만들 수 있지만 `passed`가 되지는 않습니다.

### Assessment Transcript

시험 결과와 약점, rubric score를 제공합니다. `passed: true`인 시험은 검증 증거로 계산됩니다.

### Growth Profile

강점 편향, 성장 비용, 집착 전공을 제공합니다. 천재성을 균형 잡힌 만능성으로 포장하지 않고 비대칭 성장으로 기록하기 위한 입력입니다.

### Grade Learning Records

연도/단계별 학습 기록, 과제, 피드백 loop를 제공합니다. `completed_and_reviewed` 과제는 검증 증거로 계산됩니다.

### Reasoning Kibo JSONL

각 줄은 JSON object입니다. 엔진은 원문을 출력하지 않고 entry 개수만 반영합니다.

## 출력

출력 schema는 `paideia-genius-derivation-profile/v1`입니다.

핵심 섹션:

- `domain_focus`: 전공, 역할, privileged domain
- `design_claim`: 일반 초지능/모델 크기 주장이 아님을 명시
- `capacity_budget`: 고정 용량 효율 전략
- `deliberate_practice_program`: 반복 훈련 cycle과 ladder
- `cognitive_kibo_targets`: pattern chunk와 압축 규칙
- `unevenness_profile`: 강점, 약점, 성장 비용
- `scorecard`: 평가 metric, 최소 훈련 계약 검증 기준, 장기 천재 후보 승격 목표
- `evidence_summary`: 검증 증거 수
- `public_safe`: 공개 안전 플래그
- `validation`: profile 검증 결과

`scorecard.profile_validation_threshold`는 이 profile이 훈련 계약으로 유효한지 판단하는 최소 기준입니다. `scorecard.genius_candidate_promotion_target`는 이후 반복 시험과 전이 과제로 달성해야 하는 장기 목표이며, base `validation.passed`의 직접 조건이 아닙니다.

## 검증 상태

- `passed`: 최소 훈련 증거와 구조 검증을 통과한 훈련 계약입니다. 천재성이 입증됐다는 뜻은 아닙니다.
- `needs_training_evidence`: 구조는 만들었지만 증거가 부족합니다.
- `failed`: schema 또는 핵심 구조가 맞지 않습니다.

## 보안 경계

이 엔진은 active DLP 시스템이 아닙니다. 다만 공개 artifact에 자주 섞이는 provider token 패턴은 출력 전 마스킹합니다.

- `sk-proj-*`
- `sk-*`
- `gho_*`, `ghp_*`, `ghs_*`, `ghu_*`
- `xoxb-*` 등 Slack token
- `ya29.*`
- `Bearer ...`

개인 데이터나 실제 훈련 기록을 공개 레포 예제로 넣지 마세요. 예제는 synthetic fixture만 사용해야 합니다.
