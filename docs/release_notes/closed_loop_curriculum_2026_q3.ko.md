# 폐쇄형 보완 교육과정 피드백 루프

릴리즈 목표: 2026-Q3  
코드명: Adaptive Curriculum Feedback Loop

Genius Derivation Engine은 이제 pattern affinity 판단에서 보완 교육 상태를 인식합니다.

## 추가 내용

- 생성되는 profile에 `curriculum_backlog`, `weakness_records` 필드 추가
- 고심각도 또는 반복 weakness가 있는 경우 pattern affinity 차단
- curriculum remediation과 adaptive re-exam 증거가 완료되기 전까지 affinity 감소

## 안전 경계

- WeaknessRecord는 선택적이고 검토 가능한 산출물입니다.
- curriculum 데이터가 없으면 기존 Kibo affinity 동작과 하위 호환됩니다.
- high-risk pattern 사용은 계속 field validation과 critic pass 증거를 요구합니다.

## 검증

- 전체 테스트: `27 passed`
