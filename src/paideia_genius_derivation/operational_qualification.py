from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


OPERATIONAL_QUALIFICATION_SCHEMA = "paideia-operational-qualification/v1"
QUALIFICATION_STATUSES = {
    "unqualified",
    "simulation_qualified",
    "shadow_qualified",
    "limited_field_qualified",
    "operationally_qualified",
    "suspended",
}


def _tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),)


def _int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class OperationalQualification:
    profile_id: str
    capability_ids: tuple[str, ...]
    permitted_risk_classes: tuple[str, ...]
    simulation_exam_count: int
    shadow_exam_count: int
    field_trial_count: int
    unresolved_weakness_ids: tuple[str, ...]
    status: str
    schema: str = OPERATIONAL_QUALIFICATION_SCHEMA

    def __post_init__(self) -> None:
        if not self.profile_id:
            raise ValueError("profile_id is required")
        if self.status not in QUALIFICATION_STATUSES:
            raise ValueError(f"Unsupported operational qualification status: {self.status}")
        for key in ("simulation_exam_count", "shadow_exam_count", "field_trial_count"):
            object.__setattr__(self, key, max(0, int(getattr(self, key))))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["capability_ids"] = list(self.capability_ids)
        data["permitted_risk_classes"] = list(self.permitted_risk_classes)
        data["unresolved_weakness_ids"] = list(self.unresolved_weakness_ids)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperationalQualification":
        return cls(
            profile_id=str(data.get("profile_id") or ""),
            capability_ids=_tuple(data.get("capability_ids")),
            permitted_risk_classes=_tuple(data.get("permitted_risk_classes")),
            simulation_exam_count=_int(data.get("simulation_exam_count")),
            shadow_exam_count=_int(data.get("shadow_exam_count")),
            field_trial_count=_int(data.get("field_trial_count")),
            unresolved_weakness_ids=_tuple(data.get("unresolved_weakness_ids")),
            status=str(data.get("status") or "unqualified"),
            schema=str(data.get("schema") or OPERATIONAL_QUALIFICATION_SCHEMA),
        )
