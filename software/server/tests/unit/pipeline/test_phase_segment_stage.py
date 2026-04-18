from bioliminal.api.schemas import Frame, Landmark, Session, SessionMetadata
from bioliminal.ml.phase_segmenter import PhaseBoundaries, SinglePhaseSegmenter
from bioliminal.pipeline.stages.base import STAGE_NAME_PHASE_SEGMENT, StageContext
from bioliminal.pipeline.stages.phase_segment import run_phase_segment


def _rollup_session(frame_count: int) -> Session:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    frames = [
        Frame(timestamp_ms=i * 33, landmarks=[lm for _ in range(33)]) for i in range(frame_count)
    ]
    return Session(
        metadata=SessionMetadata(movement="rollup", device="t", model="t", frame_rate=30.0),
        frames=frames,
    )


def test_stage_name_phase_segment_constant_exists():
    assert STAGE_NAME_PHASE_SEGMENT == "phase_segment"


def test_run_phase_segment_produces_single_full_movement_phase():
    ctx = StageContext(session=_rollup_session(60))
    result = run_phase_segment(ctx)
    assert isinstance(result, PhaseBoundaries)
    assert len(result.phases) == 1
    assert result.phases[0].label == "full_movement"
    assert result.phases[0].start_timestamp_ms == 0
    assert result.phases[0].end_timestamp_ms == 59 * 33


def test_run_phase_segment_accepts_injected_segmenter():
    ctx = StageContext(session=_rollup_session(10))
    segmenter = SinglePhaseSegmenter()
    result = run_phase_segment(ctx, segmenter=segmenter)
    assert len(result.phases) == 1
