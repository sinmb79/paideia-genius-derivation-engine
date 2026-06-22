# Closed-Loop Curriculum Feedback Loop

Release target: 2026-Q3  
Codename: Adaptive Curriculum Feedback Loop

The Genius Derivation Engine now recognizes curriculum remediation state in pattern affinity checks.

## Added

- `curriculum_backlog` and `weakness_records` fields on generated profiles.
- Pattern affinity blocking for active high-severity or repeated weaknesses.
- Backlog-aware affinity reduction until curriculum remediation and adaptive re-exam evidence are complete.

## Safety

- Weakness records are optional, reviewable artifacts.
- Existing Kibo affinity behavior remains backward compatible when no curriculum data is supplied.
- High-risk pattern use still requires field validation and critic pass evidence.

## Validation

- Full test suite: `27 passed`
