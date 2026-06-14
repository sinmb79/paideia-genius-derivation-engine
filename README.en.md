# Paideia Genius Derivation Engine

[![CI](https://github.com/sinmb79/paideia-genius-derivation-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/sinmb79/paideia-genius-derivation-engine/actions/workflows/ci.yml)

[한국어](README.md)

The Paideia Genius Derivation Engine treats narrow excellence as a training outcome, not a raw model-size claim. Within a bounded capacity, an agent can become unusually strong in a specific domain when its attention, chunks, timed practice, feedback, mistakes, and transfer work are repeatedly shaped by evidence.

This repository is a standalone extraction from Paideia-Agent. It does not perform network calls, store API keys, store OAuth tokens, or persist hidden chain-of-thought. It builds and validates a public-safe domain genius candidate profile from training curricula and reviewed evidence.

## v0.2.0 Release Summary

`v0.2.0` is a validation hardening release. It separates a minimum-evidence training contract from the stricter long-term promotion gate, so a profile does not become a genius candidate merely because it has some evidence.

### Main Changes

| Change | Why it matters |
| --- | --- |
| Split profile status into `draft`, `training_contract_valid`, and `genius_candidate_promoted` | Drafts, valid training contracts, and promoted candidates should not be conflated. |
| Added `validation.contract_status = minimum_evidence_contract_passed` | Makes clear that `validation.passed` is a minimum contract gate, not proof of genius. |
| Added a separate `promotion` gate | Long-term repeated trials and transfer evidence are checked independently. |
| Required `scored_reviewed_trial_count >= 8` | Blocks shortcut promotion through one high-score assessment plus reviewed assignments. |
| Hardened assessment and grade learning record validation | Prevents malformed inputs from silently becoming evidence. |
| Streamed Reasoning Kibo JSONL counts | Keeps raw reasoning private while still reflecting evidence volume. |

### Breaking Changes

Code that directly compares `profile["status"]` may need to account for the new status values.

| Previous assumption | v0.2.0 migration |
| --- | --- |
| Evidence-backed profile means candidate status | Distinguish `training_contract_valid` from `genius_candidate_promoted`. |
| Reviewed assignments can satisfy promotion trial count | Check `promotion["observed"]["scored_reviewed_trials"]`. |
| `validation.passed` proves genius | Treat `validation` as the minimum contract gate and `promotion` as the long-term candidate gate. |

```python
status = profile["status"]
if status == "genius_candidate_promoted":
    run_promoted_agent_path(profile)
elif status == "training_contract_valid":
    keep_training(profile)
else:
    request_more_evidence(profile)
```

## Core Ideas

- Genius is a reviewable training contract, not a general superintelligence claim.
- Fixed-capacity efficiency can matter more than broad compute scaling for narrow expertise.
- External skills and other people's methods may be studied, but they are not promoted verbatim into the agent identity.
- Weaknesses and growth costs are preserved as resume-like guardrails.
- A blueprint-only profile has top-level status `draft`.

## Flow

```mermaid
flowchart TD
    A["Training blueprint"] --> B["Major scope and curriculum"]
    B --> C["Assessment transcript"]
    B --> D["Grade learning records"]
    C --> E["Error and weakness taxonomy"]
    D --> E
    E --> F["Pattern chunks and compression rules"]
    F --> G["Timed trials and transfer work"]
    G --> H["Genius derivation profile"]
    H --> I["Reviewable dossier and runtime contract"]
```

## Install

```powershell
py -3.12 -m pip install -e .
```

Runtime dependencies are standard-library only. For development checks:

```powershell
py -3.12 -m pip install -e ".[dev]"
```

## CLI

Create a draft:

```powershell
paideia-genius-profile build-profile `
  --blueprint .\examples\minimal_blueprint.json `
  --allow-draft `
  --output .\runs\draft_profile.json
```

Create an evidence-backed profile:

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

Without `--allow-draft`, insufficient evidence produces an artifact but returns exit code `2`.

`validation.passed` means the training contract has enough minimum evidence to be valid; it does not prove genius. Longer-term criteria such as eight scored reviewed trials and an average score of 90 are checked by a separate `promotion` gate.

## Status Model

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> training_contract_valid: minimum evidence contract passed
    training_contract_valid --> genius_candidate_promoted: long-term promotion gate passed
    draft --> failed: input contract failed
    training_contract_valid --> failed: output structure failed
```

| Status | Meaning |
| --- | --- |
| `draft` | The blueprint is valid, but minimum training evidence is missing. |
| `training_contract_valid` | The profile is a minimum-evidence training contract, not proof of genius. |
| `genius_candidate_promoted` | The stricter long-term promotion gate passed: at least 8 scored reviewed trials, average score 90+, varied transfer, and documented weaknesses. |

`validation.contract_status` describes the minimum contract gate, such as `minimum_evidence_contract_passed`. `promotion.status` describes long-term genius candidate promotion.

### Minimum `genius_candidate_promoted` Conditions

| Condition | Requirement |
| --- | --- |
| Base validation | `validation.passed is True` |
| Scored reviewed trials | `scored_reviewed_trial_count >= 8` |
| Average score | `assessment_average_score >= 90` |
| Varied transfer | At least two distinct transfer evidence signals |
| Weakness guardrail | Weakness or error guardrails are documented |

## Python

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

assessment_transcript = {
    "results": [
        {
            "gate_id": "valuation_case_report",
            "passed": True,
            "score": 92,
            "rubric_scores": {"evidence_precision": 24, "counterexample_depth": 23},
            "weak_spots": ["overfocus_on_downside"],
        }
    ]
}

growth_profile = {
    "schema": "paideia-growth-profile/v1",
    "asymmetry_profile": {
        "strength_biases": ["slow valuation patience"],
        "growth_costs": ["can overfocus on downside"],
    },
}

grade_learning_records = {
    "records": [
        {
            "education_stage": "doctoral_research",
            "assignments": [{"status": "completed_and_reviewed"}],
        }
    ]
}

profile = build_genius_derivation_profile(
    blueprint,
    assessment_transcript=assessment_transcript,
    growth_profile=growth_profile,
    grade_learning_records=grade_learning_records,
)

print(profile["status"])                         # training_contract_valid
print(profile["validation"]["contract_status"])  # minimum_evidence_contract_passed
print(profile["promotion"]["status"])            # not_ready
```

Longer runnable examples are available in `examples/basic_profile.py` and `examples/promotion_gate_examples.py`.

## Contract

See [docs/engine_contract.en.md](docs/engine_contract.en.md). The lifecycle is documented in [docs/profile_lifecycle.en.md](docs/profile_lifecycle.en.md), promotion gates in [docs/promotion_gates.en.md](docs/promotion_gates.en.md), and validation rules in [docs/validation_rules.en.md](docs/validation_rules.en.md).

The library validates `identity.name`, `track.track_id`, and `track.domains` before profile construction. Passed assessments only count as reviewed evidence if they meet the assessment quality floor: `score >= 80` when a score is present, and all numeric `rubric_scores` are at least 20 when rubric scores are present.

## Public-Safe Rules

- No network calls.
- No hidden chain-of-thought storage.
- Raw reasoning kibo entries are not exported; only the entry count is reflected.
- Obvious provider tokens are replaced with `[redacted-sensitive-value]` before export.
- Raw external skill text is not promoted into the agent.

See [SECURITY.md](SECURITY.md) for the security boundary and [CHANGELOG.md](CHANGELOG.md) for release history.

## Verification

```powershell
py -3.12 -m py_compile src\paideia_genius_derivation\genius_derivation.py src\paideia_genius_derivation\cli.py
py -3.12 -m unittest discover -s tests -v
py -3.12 -m bandit -q -r src -c pyproject.toml -f json -o runs\bandit_report.json
```

GitHub Actions runs compile, unittest, and Bandit scan on Python 3.10, 3.11, and 3.12.

## Research Basis

- Neural efficiency: <https://pubmed.ncbi.nlm.nih.gov/19580915/>
- Deliberate practice: <https://pubmed.ncbi.nlm.nih.gov/18778378/>
- Chunking expertise: <https://doi.org/10.1016/0010-0285(73)90004-2>
- Reflexion: <https://arxiv.org/abs/2303.11366>

## License

MIT License.
