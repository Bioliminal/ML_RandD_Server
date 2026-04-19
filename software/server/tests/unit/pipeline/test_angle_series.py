from bioliminal.api.schemas import Frame, Landmark, Session, SessionMetadata
from bioliminal.pipeline.stages.angle_series import _SQUAT_TRACKED, run_angle_series
from bioliminal.pipeline.stages.base import StageContext


def _frame(timestamp_ms: int) -> Frame:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    return Frame(timestamp_ms=timestamp_ms, landmarks=[lm for _ in range(33)])


def _session(frame_count: int) -> Session:
    return Session(
        metadata=SessionMetadata(movement="overhead_squat", device="t", model="t", frame_rate=30.0),
        frames=[_frame(i * 33) for i in range(frame_count)],
    )


def test_angle_series_produces_one_entry_per_tracked_angle():
    ctx = StageContext(session=_session(10))
    result = run_angle_series(ctx)
    assert set(result.angles.keys()) == set(_SQUAT_TRACKED)
    assert result.timestamps_ms == [i * 33 for i in range(10)]


def test_angle_series_values_match_frame_count():
    ctx = StageContext(session=_session(12))
    result = run_angle_series(ctx)
    for name in _SQUAT_TRACKED:
        assert len(result.angles[name]) == 12


def test_tracked_angle_names_are_canonical():
    assert "left_knee_flexion" in _SQUAT_TRACKED
    assert "right_knee_flexion" in _SQUAT_TRACKED
    assert "left_knee_valgus" in _SQUAT_TRACKED
    assert "right_knee_valgus" in _SQUAT_TRACKED
    assert "left_hip_flexion" in _SQUAT_TRACKED
    assert "right_hip_flexion" in _SQUAT_TRACKED
    assert "trunk_lean" in _SQUAT_TRACKED
