import pytest

from bioliminal.api.schemas import Frame, Landmark, Session, SessionMetadata
from bioliminal.ml.phase_segmenter import (
    Phase,
    PhaseBoundaries,
    PhaseSegmenter,
    SinglePhaseSegmenter,
)
from bioliminal.pipeline.stages.base import StageContext


def _session(frame_count: int) -> Session:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    frames = [
        Frame(timestamp_ms=i * 33, landmarks=[lm for _ in range(33)]) for i in range(frame_count)
    ]
    return Session(
        metadata=SessionMetadata(movement="rollup", device="t", model="t", frame_rate=30.0),
        frames=frames,
    )


def test_single_phase_segmenter_returns_one_phase_spanning_session():
    segmenter: PhaseSegmenter = SinglePhaseSegmenter()
    ctx = StageContext(session=_session(60))
    result = segmenter.segment(ctx)
    assert isinstance(result, PhaseBoundaries)
    assert len(result.phases) == 1
    phase = result.phases[0]
    assert phase.index == 0
    assert phase.start_timestamp_ms == 0
    assert phase.end_timestamp_ms == 59 * 33
    assert phase.label == "full_movement"


def test_single_phase_segmenter_empty_session_returns_no_phases():
    segmenter = SinglePhaseSegmenter()
    empty = Session(
        metadata=SessionMetadata(movement="rollup", device="t", model="t", frame_rate=30.0),
        frames=[],
    )
    ctx = StageContext(session=empty)
    result = segmenter.segment(ctx)
    assert result.phases == []


def test_phase_index_must_be_non_negative():
    with pytest.raises(ValueError):
        Phase(index=-1, start_timestamp_ms=0, end_timestamp_ms=100, label="full_movement")
