from typing import Protocol

from bioliminal.pipeline.artifacts import LiftedAngleTimeSeries, NormalizedAngleTimeSeries

__all__ = ["IdentityLifter", "Lifter", "LiftedAngleTimeSeries"]


class Lifter(Protocol):
    def lift(self, angles: NormalizedAngleTimeSeries) -> LiftedAngleTimeSeries: ...


class IdentityLifter:
    def lift(self, angles: NormalizedAngleTimeSeries) -> LiftedAngleTimeSeries:
        return LiftedAngleTimeSeries(
            angles=dict(angles.angles),
            timestamps_ms=list(angles.timestamps_ms),
            scale_factor=angles.scale_factor,
            is_3d=False,
        )
