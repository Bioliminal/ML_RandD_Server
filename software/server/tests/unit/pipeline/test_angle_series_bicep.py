import pytest

from bioliminal.api.schemas import Frame, PoseLandmark, Session, SessionMetadata
from bioliminal.pipeline.stages.angle_series import run_angle_series
from bioliminal.pipeline.stages.base import StageContext


def _upright_frame(ts_ms: int) -> Frame:
    landmarks = [PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0) for _ in range(33)]
    landmarks[11] = PoseLandmark(x=0.0, y=0.0, z=0.0, visibility=1.0, presence=1.0)
    landmarks[13] = PoseLandmark(x=1.0, y=0.0, z=0.0, visibility=1.0, presence=1.0)
    landmarks[15] = PoseLandmark(x=2.0, y=0.0, z=0.0, visibility=1.0, presence=1.0)
    landmarks[12] = PoseLandmark(x=0.0, y=0.1, z=0.0, visibility=1.0, presence=1.0)
    landmarks[14] = PoseLandmark(x=1.0, y=0.1, z=0.0, visibility=1.0, presence=1.0)
    landmarks[16] = PoseLandmark(x=2.0, y=0.1, z=0.0, visibility=1.0, presence=1.0)
    return Frame(timestamp_ms=ts_ms, landmarks=landmarks)


def _session(movement: str) -> Session:
    return Session(
        metadata=SessionMetadata(
            movement=movement,
            device="test",
            model="mediapipe_blazepose_full",
            frame_rate=30.0,
        ),
        frames=[_upright_frame(i * 33) for i in range(3)],
    )


def test_bicep_curl_produces_elbow_flexion_series():
    session = _session("bicep_curl")
    ctx = StageContext(session=session, artifacts={})
    result = run_angle_series(ctx)
    assert "left_elbow_flexion" in result.angles
    assert "right_elbow_flexion" in result.angles
    assert len(result.angles["left_elbow_flexion"]) == 3
    for angle in result.angles["left_elbow_flexion"]:
        assert angle == pytest.approx(180.0, abs=1.0)


def test_bicep_curl_does_not_emit_squat_angles():
    session = _session("bicep_curl")
    ctx = StageContext(session=session, artifacts={})
    result = run_angle_series(ctx)
    assert "left_elbow_flexion" in result.angles


def test_squat_movement_still_emits_knee_angles_not_elbow():
    session = _session("overhead_squat")
    ctx = StageContext(session=session, artifacts={})
    result = run_angle_series(ctx)
    assert "left_knee_flexion" in result.angles
    assert "left_elbow_flexion" not in result.angles
