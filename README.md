# Paideia 천재 도출 엔진

[English](README.en.md)

Paideia 천재 도출 엔진은 AI를 “더 큰 모델이면 더 똑똑해진다”는 방향으로만 보지 않습니다. 같은 한정된 용량 안에서도 무엇을 오래 훈련했고, 어떤 문제를 빨리 알아보고, 어떤 실패를 반복해서 고쳤는지에 따라 특정 분야에서 비대칭적인 전문성이 생긴다는 전제를 코드로 만든 독립 엔진입니다.

이 저장소는 Paideia-Agent 본체에서 분리한 standalone 패키지입니다. 네트워크 호출, API key 저장, OAuth 토큰 저장, hidden chain-of-thought 저장 없이, 교육과정과 시험/과제 증거를 바탕으로 “특정 전공 천재 후보 프로필”을 생성하고 검증합니다.

## 핵심 철학

- 천재성은 일반 초지능 선언이 아니라 검증 가능한 훈련 계약입니다.
- 모델 크기보다 중요한 것은 제한된 용량 안의 주의 배분, 패턴 chunking, 시간 제한 시험, 오류 수정, 전이 과제입니다.
- 외부 스킬이나 타인의 방법은 참고 자료일 뿐, 그대로 복사해 에이전트 정체성으로 승격하지 않습니다.
- 약점과 성장 비용은 숨기지 않고 이력서처럼 남겨야 합니다.
- 증거 없는 blueprint-only 결과물은 `needs_training_evidence` 초안입니다.

## 시스템 흐름

```mermaid
flowchart TD
    A["훈련 blueprint"] --> B["전공 범위와 curriculum"]
    B --> C["시험 transcript"]
    B --> D["학년별 학습 기록"]
    C --> E["오류와 약점 분류"]
    D --> E
    E --> F["패턴 chunk와 압축 규칙"]
    F --> G["시간 제한 시험과 전이 과제"]
    G --> H["천재 도출 profile"]
    H --> I["검증 가능한 이력서와 runtime 계약"]
```

## 설치

```powershell
py -3.12 -m pip install -e .
```

런타임 의존성은 표준 라이브러리뿐입니다. 개발 검증에는 `pytest`, `bandit`를 선택적으로 씁니다.

```powershell
py -3.12 -m pip install -e ".[dev]"
```

## CLI 사용

증거 없는 초안을 만들 때:

```powershell
paideia-genius-profile build-profile `
  --blueprint .\examples\minimal_blueprint.json `
  --allow-draft `
  --output .\runs\draft_profile.json
```

검증 가능한 프로필을 만들 때:

```powershell
paideia-genius-profile build-profile `
  --blueprint .\examples\minimal_blueprint.json `
  --curriculum .\examples\minimal_curriculum.json `
  --assessment-transcript .\examples\minimal_assessment_transcript.json `
  --growth-profile .\examples\minimal_growth_profile.json `
  --grade-learning-records .\examples\minimal_grade_learning_records.json `
  --reasoning-kibo .\examples\minimal_reasoning_kibo.jsonl `
  --output .\runs\sample_profile.json
```

`--allow-draft`가 없고 훈련 증거가 부족하면 파일은 생성되지만 종료 코드는 `2`입니다. 이는 “실패”라기보다, 증거가 부족한 프로필을 자동으로 합격 처리하지 않기 위한 안전장치입니다.

`validation.passed`는 “천재 입증”이 아니라 최소 증거를 갖춘 훈련 계약 검증입니다. 반복 시험 8회, 평균 90점 같은 장기 기준은 `genius_candidate_promotion_target`으로 별도 기록되며, 실제 후보 승격은 이후 반복된 검토 시험과 전이 과제로 판단해야 합니다.

## Python 사용

```python
from paideia_genius_derivation import build_genius_derivation_profile

blueprint = {
    "schema": "ai-talent-training-blueprint/v1",
    "identity": {"name": "Mira", "language": "ko"},
    "track": {
        "track_id": "securities_research_phd",
        "name": "Securities Research PhD Track",
        "domains": ["valuation", "risk analysis"],
    },
}

profile = build_genius_derivation_profile(blueprint)
print(profile["validation"]["status"])
```

## 입력 계약

상세 입력/출력 계약은 [docs/engine_contract.ko.md](docs/engine_contract.ko.md)를 보시면 됩니다.

최소 필수 입력은 `ai-talent-training-blueprint/v1` schema를 가진 blueprint입니다. `passed` 검증을 받으려면 다음 중 충분한 훈련 증거가 필요합니다.

- curriculum manifest
- assessment transcript
- growth profile
- grade learning records
- reviewed assignment 또는 passed assessment
- reasoning kibo JSONL의 entry count

## 공개 안전 규칙

- 네트워크 호출을 수행하지 않습니다.
- hidden chain-of-thought와 raw private reasoning trace를 저장하지 않습니다.
- reasoning kibo 입력은 원문을 저장하지 않고 entry 개수만 반영합니다.
- OpenAI/GitHub/Slack/Google 계열의 명백한 provider token 문자열은 출력 전 `[redacted-sensitive-value]`로 대체합니다.
- 외부 스킬 원문을 그대로 승격하지 않습니다.

## 검증

```powershell
py -3.12 -m py_compile src\paideia_genius_derivation\genius_derivation.py src\paideia_genius_derivation\cli.py
py -3.12 -m unittest discover -s tests -v
py -3.12 -m bandit -q -r src -c pyproject.toml -f json -o runs\bandit_report.json
```

## 연구 근거

- Neural efficiency: 같은 용량에서도 효율적이고 과제 중심적인 활성화가 중요할 수 있습니다. <https://pubmed.ncbi.nlm.nih.gov/19580915/>
- Deliberate practice: 구조화된 훈련, 피드백, 난이도 상승이 전문성 형성에 중요합니다. <https://pubmed.ncbi.nlm.nih.gov/18778378/>
- Chunking expertise: 전문가는 익숙한 패턴을 더 큰 검색 단위로 압축합니다. <https://doi.org/10.1016/0010-0285(73)90004-2>
- Reflexion: 언어적 피드백 기록은 weight update 없이도 다음 행동을 개선할 수 있습니다. <https://arxiv.org/abs/2303.11366>

## 라이선스

MIT License. Paideia-Agent에서 분리한 독립 공개 패키지입니다.
