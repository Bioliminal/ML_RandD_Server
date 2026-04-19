import pytest

from bioliminal.api.schemas import Frame, PoseLandmark, Session, SessionMetadata
from bioliminal.pipeline.stages.base import StageContext
from bioliminal.pipeline.stages.quality_gate import run_quality_gate


def _frame_with_upper_limb_vis(vis: float) -> Frame:
    lms = []
    for idx in range(33):
        if idx in (11, 12, 13, 14, 15, 16):
            v = vis
        else:
            v = 0.9
        lms.append(PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=v, presence=1.0))
    return Frame(timestamp_ms=0, landmarks=lms)


def _session(movement: str, upper_limb_vis: float, n_frames: int = 60) -> Session:
    return Session(
        metadata=SessionMetadata(movement=movement, device="t", model="m", frame_rate=30.0),
        frames=[_frame_with_upper_limb_vis(upper_limb_vis) for _ in range(n_frames)],
    )


def test_bicep_curl_flags_low_upper_limb_visibility():
    session = _session("bicep_curl", upper_limb_vis=0.3)
    ctx = StageContext(session=session, artifacts={})
    report = run_quality_gate(ctx)
    codes = [issue.code for issue in report.issues]
    assert "low_upper_limb_visibility" in codes


def test_bicep_curl_no_flag_when_upper_limb_visible():
    session = _session("bicep_curl", upper_limb_vis=0.8)
    ctx = StageContext(session=session, artifacts={})
    report = run_quality_gate(ctx)
    codes = [issue.code for issue in report.issues]
    assert "low_upper_limb_visibility" not in codes


def test_squat_does_not_emit_upper_limb_flag():
    session = _session("overhead_squat", upper_limb_vis=0.1)
    ctx = StageContext(session=session, artifacts={})
    report = run_quality_gate(ctx)
    codes = [issue.code for issue in report.issues]
    assert "low_upper_limb_visibility" not in codes


def test_upper_limb_metric_always_reported_for_bicep():
    session = _session("bicep_curl", upper_limb_vis=0.9)
    ctx = StageContext(session=session, artifacts={})
    report = run_quality_gate(ctx)
    assert "upper_limb_visibility" in report.metrics
    assert report.metrics["upper_limb_visibility"] == pytest.approx(0.9, abs=0.01)
