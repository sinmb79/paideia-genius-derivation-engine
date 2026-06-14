# Promotion Gate

[English](promotion_gates.en.md)

`promotion` gate는 “최소 훈련 계약이 유효하다”는 수준을 넘어, 천재 후보로 승격할 만큼 반복 시험 성과와 전이 증거가 충분한지를 확인합니다.

## `genius_candidate_promoted` 조건

| 항목 | 필수 기준 | 이유 |
| --- | --- | --- |
| Base validation | `validation.passed is True` | 깨진 계약은 승격할 수 없습니다. |
| Scored reviewed trials | `scored_reviewed_trial_count >= 8` | 단일 고득점이나 리뷰 과제 수만으로 승격되는 shortcut을 막습니다. |
| Average score | `assessment_average_score >= 90` | 반복된 고성능이 있어야 합니다. |
| Varied transfer | 서로 다른 transfer evidence 2종 이상 | 한 문제 유형에만 과적합되는 것을 줄입니다. |
| Weakness guardrails | 약점 기록이 존재 | 천재성 주장이 약점 은폐로 이어지지 않게 합니다. |

## 관측값 위치

```python
promotion = profile["promotion"]

promotion["status"]                         # not_ready 또는 genius_candidate_promoted
promotion["observed"]["scored_reviewed_trials"]
promotion["observed"]["assessment_average_score"]
promotion["observed"]["varied_transfer_evidence_count"]
promotion["failed_checks"]
```

## 의도적으로 막는 shortcut

아래 조합은 reviewed evidence가 8개처럼 보여도 promotion을 통과하지 못합니다.

- 고득점 assessment 1개
- reviewed assignment 7개

이 경우 `reviewed_trials`는 8일 수 있지만 `scored_reviewed_trials`는 1입니다. `v0.2.0`은 천재 후보 승격에 scored reviewed trial 8개를 요구합니다.
