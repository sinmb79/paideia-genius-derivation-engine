# Changelog

All notable changes to the Paideia Genius Derivation Engine are tracked here.

## v0.2.0 - Validation Gates Hardening

Released: 2026-06-14

### Breaking Changes

- Profile status is now split into `draft`, `training_contract_valid`, and `genius_candidate_promoted`.
- Code that treated `validation.passed` as genius promotion should now check the separate `promotion` object.
- Genius candidate promotion now requires `scored_reviewed_trial_count >= 8`; reviewed assignments alone do not satisfy the scored trial gate.

### Changed

- Added `validation.contract_status = minimum_evidence_contract_passed`.
- Added long-term `promotion` gate with explicit observed and required values.
- Blocked shortcut promotion through one high-score assessment plus reviewed assignments.
- Strengthened required blueprint field validation for `identity.name`, `track.track_id`, and `track.domains`.
- Strengthened assessment transcript and grade learning record input validation.
- Excluded low-quality passed assessments from reviewed evidence.
- Streamed Reasoning Kibo JSONL counting without exporting raw entries.
- Added Python 3.10, 3.11, and 3.12 CI.

### Validation

- `py_compile` passed.
- `unittest`: 16 passed.
- `bandit`: 0 findings.
- CLI smoke test passed.
- GitHub Actions matrix passed.

## v0.1.0 - Initial Standalone Extraction

- Extracted the genius derivation engine from Paideia-Agent into a standalone package.
- Added CLI profile generation from synthetic fixtures.
- Added public-safe redaction and no-network runtime boundary.
