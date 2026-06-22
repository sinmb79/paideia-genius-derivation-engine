# Pattern Affinity for Genius Derivation

Release date: 2026-06-22

This release connects Paideia's genius derivation engine to the new Kibo Pattern Layer. Genius profiles can now be evaluated against Pattern Candidates, not only individual Kibo records.

## Highlights

- Added `evaluate_pattern_affinity`.
- Blocks draft, weakened, and quarantined patterns from specialist use.
- Requires field-validated or reinforced patterns for high-risk tasks.
- Reuses the existing evidence-based affinity model: domain match, training evidence, reviewed transfer evidence, reviewed trial scores, and weakness guardrail conflicts.
- Preserves the existing `evaluate_kibo_affinity` behavior.

## Validation

- `paideia-genius-derivation-engine`: 25 tests passed.
- Kibo/pattern affinity targeted tests: 9 tests passed.

## Post-Review Hardening

- Pattern affinity now serializes as `paideia-pattern-affinity/v1`.
- High-risk pattern affinity requires critic pass evidence.
- Explicitly failed genius profile validation blocks affinity approval.

<details>
<summary>한국어 설명 보기</summary>

# Pattern Affinity for Genius Derivation

릴리즈 일자: 2026-06-22

이번 릴리즈는 Paideia genius derivation engine을 새 Kibo Pattern Layer와 연결합니다. 이제 genius profile은 개별 Kibo record뿐 아니라 Pattern Candidate에 대해서도 사용 자격을 평가할 수 있습니다.

## 주요 변경

- `evaluate_pattern_affinity` 추가
- draft, weakened, quarantined pattern의 specialist 사용 차단
- high-risk task에서는 field-validated 또는 reinforced pattern 요구
- 기존 evidence-based affinity 모델 재사용: domain match, training evidence, reviewed transfer evidence, reviewed trial score, weakness guardrail conflict
- 기존 `evaluate_kibo_affinity` 동작 유지

## 검증

- `paideia-genius-derivation-engine`: 전체 25개 테스트 통과
- Kibo/pattern affinity targeted test: 9개 통과

## 리뷰 후 보강

- Pattern affinity 직렬화 schema가 `paideia-pattern-affinity/v1`로 나가도록 보강했습니다.
- high-risk pattern affinity에는 critic pass evidence가 필요합니다.
- genius profile validation이 명시적으로 실패한 경우 affinity approval을 차단합니다.

</details>
