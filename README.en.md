# Paideia Genius Derivation Engine

[한국어](README.md)

The Paideia Genius Derivation Engine treats narrow excellence as a training outcome, not a raw model-size claim. Within a bounded capacity, an agent can become unusually strong in a specific domain when its attention, chunks, timed practice, feedback, mistakes, and transfer work are repeatedly shaped by evidence.

This repository is a standalone extraction from Paideia-Agent. It does not perform network calls, store API keys, store OAuth tokens, or persist hidden chain-of-thought. It builds and validates a public-safe domain genius candidate profile from training curricula and reviewed evidence.

## Core Ideas

- Genius is a reviewable training contract, not a general superintelligence claim.
- Fixed-capacity efficiency can matter more than broad compute scaling for narrow expertise.
- External skills and other people's methods may be studied, but they are not promoted verbatim into the agent identity.
- Weaknesses and growth costs are preserved as résumé-like guardrails.
- A blueprint-only profile is a `needs_training_evidence` draft.

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

`validation.passed` means the training contract has enough minimum evidence to be valid; it does not prove genius. Longer-term criteria such as eight reviewed trials and an average score of 90 are recorded separately as `genius_candidate_promotion_target`.

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

profile = build_genius_derivation_profile(blueprint)
print(profile["validation"]["status"])
```

## Contract

See [docs/engine_contract.en.md](docs/engine_contract.en.md).

## Public-Safe Rules

- No network calls.
- No hidden chain-of-thought storage.
- Raw reasoning kibo entries are not exported; only the entry count is reflected.
- Obvious provider tokens are replaced with `[redacted-sensitive-value]` before export.
- Raw external skill text is not promoted into the agent.

## Verification

```powershell
py -3.12 -m py_compile src\paideia_genius_derivation\genius_derivation.py src\paideia_genius_derivation\cli.py
py -3.12 -m unittest discover -s tests -v
py -3.12 -m bandit -q -r src -c pyproject.toml -f json -o runs\bandit_report.json
```

## Research Basis

- Neural efficiency: <https://pubmed.ncbi.nlm.nih.gov/19580915/>
- Deliberate practice: <https://pubmed.ncbi.nlm.nih.gov/18778378/>
- Chunking expertise: <https://doi.org/10.1016/0010-0285(73)90004-2>
- Reflexion: <https://arxiv.org/abs/2303.11366>

## License

MIT License.
