# Engine Contract

[한국어](engine_contract.ko.md)

This document defines the input and output contract for the Paideia Genius Derivation Engine.

## Inputs

### Blueprint

Required.

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

If `schema` does not match, the library raises `ValueError`; the CLI writes a failed artifact and returns exit code `2`.

### Curriculum Manifest

Provides the domain scope, core topics, and assessment ladder. Without it, the engine can still create a draft, but it will not validate as `passed`.

### Assessment Transcript

Provides exam results, weak spots, and rubric scores. Passed assessments count as evidence.

### Growth Profile

Provides strength biases, growth costs, and domain obsession. It preserves asymmetric growth rather than presenting genius as universal competence.

### Grade Learning Records

Provides stage-by-stage learning records, assignments, and feedback loops. Assignments marked `completed_and_reviewed` count as evidence.

### Reasoning Kibo JSONL

Each line is a JSON object. Raw entries are not exported; only the entry count is reflected.

## Output

The output schema is `paideia-genius-derivation-profile/v1`.

Key sections:

- `domain_focus`: major, role, and privileged domains
- `design_claim`: explicitly rejects general superintelligence and model-size claims
- `capacity_budget`: fixed-capacity efficiency strategy
- `deliberate_practice_program`: repeated practice cycle and ladder
- `cognitive_kibo_targets`: pattern chunks and compression rules
- `unevenness_profile`: strengths, weaknesses, and growth costs
- `scorecard`: evaluation metrics, minimum training-contract validation threshold, and long-term genius candidate promotion target
- `evidence_summary`: counted validation evidence
- `public_safe`: public-safety flags
- `validation`: profile validation result

`scorecard.profile_validation_threshold` defines the minimum evidence gate for a valid training contract. `scorecard.genius_candidate_promotion_target` is a long-term goal for later repeated trials and transfer work, not the direct base `validation.passed` condition.

## Validation Status

- `passed`: structure and minimum training-contract evidence passed. It does not prove genius.
- `needs_training_evidence`: the profile was built, but evidence is insufficient.
- `failed`: schema or core structure is invalid.

## Security Boundary

This engine is not a full DLP system. It does redact common provider token patterns before export.

- `sk-proj-*`
- `sk-*`
- `gho_*`, `ghp_*`, `ghs_*`, `ghu_*`
- Slack `xoxb-*` style tokens
- `ya29.*`
- `Bearer ...`

Do not publish real personal training records as examples. Repository examples should remain synthetic fixtures.
