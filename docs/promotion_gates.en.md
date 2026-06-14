# Promotion Gate

[한국어](promotion_gates.ko.md)

The `promotion` gate goes beyond the minimum valid training contract. It checks whether repeated scored performance and transfer evidence are strong enough to promote a profile to genius candidate status.

## `genius_candidate_promoted` Requirements

| Item | Requirement | Why |
| --- | --- | --- |
| Base validation | `validation.passed is True` | Broken contracts cannot be promoted. |
| Scored reviewed trials | `scored_reviewed_trial_count >= 8` | Blocks shortcut promotion through a single high score or assignment-only evidence. |
| Average score | `assessment_average_score >= 90` | Promotion needs repeated high performance. |
| Varied transfer | At least two distinct transfer evidence signals | Reduces overfitting to one problem type. |
| Weakness guardrails | Weakness records exist | A genius claim must not hide known weaknesses. |

## Where to Inspect Values

```python
promotion = profile["promotion"]

promotion["status"]                         # not_ready or genius_candidate_promoted
promotion["observed"]["scored_reviewed_trials"]
promotion["observed"]["assessment_average_score"]
promotion["observed"]["varied_transfer_evidence_count"]
promotion["failed_checks"]
```

## Shortcut Blocked on Purpose

This combination does not pass promotion even if it looks like eight reviewed evidence items:

- one high-score assessment
- seven reviewed assignments

In that case `reviewed_trials` may be 8, but `scored_reviewed_trials` is 1. `v0.2.0` requires eight scored reviewed trials for genius candidate promotion.
