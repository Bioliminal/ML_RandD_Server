from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from auralink.api.schemas import MovementType, Session


@dataclass
class StageContext:
    session: Session
    artifacts: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)

    @property
    def movement_type(self) -> MovementType:
        return self.session.metadata.movement


@dataclass(frozen=True)
class Stage:
    name: str
    run: Callable[[StageContext], Any]


STAGE_NAME_QUALITY_GATE = "quality_gate"
STAGE_NAME_ANGLE_SERIES = "angle_series"
STAGE_NAME_NORMALIZE = "normalize"
STAGE_NAME_REP_SEGMENT = "rep_segment"
STAGE_NAME_PER_REP_METRICS = "per_rep_metrics"
STAGE_NAME_WITHIN_MOVEMENT_TREND = "within_movement_trend"
STAGE_NAME_LIFT = "lift"
STAGE_NAME_SKELETON = "skeleton"
