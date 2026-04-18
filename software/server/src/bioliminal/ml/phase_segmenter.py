from typing import Protocol

from bioliminal.pipeline.artifacts import Phase, PhaseBoundaries
from bioliminal.pipeline.stages.base import StageContext

__all__ = ["Phase", "PhaseBoundaries", "PhaseSegmenter", "SinglePhaseSegmenter"]


class PhaseSegmenter(Protocol):
    def segment(self, ctx: StageContext) -> PhaseBoundaries: ...


class SinglePhaseSegmenter:
    def segment(self, ctx: StageContext) -> PhaseBoundaries:
        frames = ctx.session.frames
        if not frames:
            return PhaseBoundaries(phases=[])
        first_ts = frames[0].timestamp_ms
        last_ts = frames[-1].timestamp_ms
        return PhaseBoundaries(
            phases=[
                Phase(
                    index=0,
                    start_timestamp_ms=first_ts,
                    end_timestamp_ms=last_ts,
                    label="full_movement",
                )
            ]
        )
