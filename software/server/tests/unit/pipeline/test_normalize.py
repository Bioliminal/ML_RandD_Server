import pytest

from bioliminal.api.schemas import Frame, Landmark, Session, SessionMetadata
from bioliminal.pipeline.artifacts import AngleTimeSeries
from bioliminal.pipeline.stages.base import StageContext
from bioliminal.pipeline.stages.normalize import run_normalize


def _frame(shoulder_y: float, hip_y: float) -> Frame:
    base = [Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0, presence=1.0) for _ in range(33)]
    base[11] = Landmark(x=0.5, y=shoulder_y, z=0.0, visibility=1.0, presence=1.0)
    base[12] = Landmark(x=0.5, y=shoulder_y, z=0.0, visibility=1.0, presence=1.0)
    base[23] = Landmark(x=0.5, y=hip_y, z=0.0, visibility=1.0, presence=1.0)
    base[24] = Landmark(x=0.5, y=hip_y, z=0.0, visibility=1.0, presence=1.0)
    return Frame(timestamp_ms=0, landmarks=base)


def _session() -> Session:
    return Session(
        metadata=SessionMetadata(movement="overhead_squat", device="t", model="t", frame_rate=30.0),
        frames=[_frame(0.3, 0.6)],
    )


def test_normalize_emits_scale_factor_from_hip_shoulder_distance():
    ctx = StageContext(session=_session())
    ctx.artifacts["angle_series"] = AngleTimeSeries(
        angles={"trunk_lean": [5.0]},
        timestamps_ms=[0],
    )
    result = run_normalize(ctx)
    assert result.scale_factor == pytest.approx(0.3, abs=1e-6)
    assert result.angles == {"trunk_lean": [5.0]}
    assert result.timestamps_ms == [0]


def test_normalize_zero_distance_falls_back_to_small_positive():
    session = Session(
        metadata=SessionMetadata(movement="overhead_squat", device="t", model="t", frame_rate=30.0),
        frames=[_frame(0.5, 0.5)],
    )
    ctx = StageContext(session=session)
    ctx.artifacts["angle_series"] = AngleTimeSeries(angles={}, timestamps_ms=[0])
    result = run_normalize(ctx)
    assert result.scale_factor > 0.0
