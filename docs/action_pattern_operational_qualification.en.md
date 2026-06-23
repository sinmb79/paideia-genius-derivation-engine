# Action Pattern Operational Qualification

This PR-1 foundation adds two contract objects for later curriculum-aware
action pattern evaluation:

- `ActionPatternAffinity`: whether a genius profile is allowed to support an
  action pattern, why it is blocked, and the highest deployment status allowed.
- `OperationalQualification`: the reviewed capability, risk, exam, field trial,
  and unresolved weakness evidence for a profile.

No deployment promotion logic is added here. The existing Kibo and pattern
affinity functions remain backward compatible.
