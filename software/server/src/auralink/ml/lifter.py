from typing import Protocol

from pydantic import BaseModel, Field

from auralink.pipeline.artifacts import NormalizedAngleTimeSeries


class LiftedAngleTimeSeries(BaseModel):
    """2D-or-3D angle time series after lifting.

    IdentityLifter copies the 2D input verbatim with `is_3d=False`. A future
    MotionBERT lifter will populate 3D-aware angles and set `is_3d=True`.
    Task 9 re-homes this schema in `pipeline/artifacts.py` and re-exports it
    here for import stability.
    """

    angles: dict[str, list[float]]
    timestamps_ms: list[int]
    scale_factor: float = Field(gt=0)
    is_3d: bool


class Lifter(Protocol):
    def lift(self, angles: NormalizedAngleTimeSeries) -> LiftedAngleTimeSeries: ...


class IdentityLifter:
    """2D passthrough lifter. Used as the Plan 4 default."""

    def lift(self, angles: NormalizedAngleTimeSeries) -> LiftedAngleTimeSeries:
        return LiftedAngleTimeSeries(
            angles=dict(angles.angles),
            timestamps_ms=list(angles.timestamps_ms),
            scale_factor=angles.scale_factor,
            is_3d=False,
        )
