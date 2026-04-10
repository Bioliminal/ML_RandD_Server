from typing import Protocol

from pydantic import BaseModel, Field

from auralink.pipeline.stages.base import StageContext


class Phase(BaseModel):
    index: int = Field(ge=0)
    start_timestamp_ms: int = Field(ge=0)
    end_timestamp_ms: int = Field(ge=0)
    label: str


class PhaseBoundaries(BaseModel):
    phases: list[Phase] = Field(default_factory=list)


class PhaseSegmenter(Protocol):
    def segment(self, ctx: StageContext) -> PhaseBoundaries: ...


class SinglePhaseSegmenter:
    """Emits one phase spanning the entire session.

    This is the rollup stub — real rollup analysis requires phase detection
    that research gap section 7.3 has not closed. Keeps the pipeline runnable
    end-to-end for the rollup movement type.
    """

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
