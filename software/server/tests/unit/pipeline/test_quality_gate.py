import pytest

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.stages.base import StageContext
from auralink.pipeline.stages.quality_gate import run_quality_gate


def _lm(visibility: float = 1.0, presence: float = 1.0) -> Landmark:
    return Landmark(x=0.5, y=0.5, z=0.0, visibility=visibility, presence=presence)


def _frame(timestamp_ms: int, visibility: float = 1.0, presence: float = 1.0) -> Frame:
    return Frame(timestamp_ms=timestamp_ms, landmarks=[_lm(visibility, presence) for _ in range(33)])


def _session(frames: list[Frame], frame_rate: float = 30.0) -> Session:
    return Session(
        metadata=SessionMetadata(
            movement="overhead_squat",
            device="test",
            model="test",
            frame_rate=frame_rate,
        ),
        frames=frames,
    )


def _ctx(session: Session) -> StageContext:
    return StageContext(session=session)


def test_rejects_low_frame_rate():
    session = _session([_frame(i * 100) for i in range(30)], frame_rate=15.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is False
    assert any(issue.code == "low_frame_rate" for issue in report.issues)
    assert report.metrics["frame_rate"] == 15.0


def test_accepts_normal_frame_rate():
    session = _session([_frame(i * 33) for i in range(40)], frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is True
    assert report.issues == []


def test_rejects_low_average_visibility():
    frames = [_frame(i * 33, visibility=0.3) for i in range(40)]
    session = _session(frames, frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is False
    assert any(issue.code == "low_visibility" for issue in report.issues)
    assert report.metrics["avg_visibility"] == pytest.approx(0.3)


def test_accepts_good_visibility():
    frames = [_frame(i * 33, visibility=0.9) for i in range(40)]
    session = _session(frames, frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is True


def test_rejects_short_session():
    frames = [_frame(i * 33) for i in range(20)]
    session = _session(frames, frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is False
    assert any(issue.code == "short_duration" for issue in report.issues)


def test_accepts_session_with_sufficient_duration():
    frames = [_frame(i * 33) for i in range(40)]
    session = _session(frames, frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is True


def test_rejects_many_missing_landmarks():
    frames = []
    for i in range(40):
        landmarks = [_lm(visibility=1.0, presence=1.0) for _ in range(30)]
        landmarks.extend([_lm(visibility=1.0, presence=0.2) for _ in range(3)])
        frames.append(Frame(timestamp_ms=i * 33, landmarks=landmarks))
    session = _session(frames, frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is False
    assert any(issue.code == "missing_landmarks" for issue in report.issues)


def test_accepts_few_missing_landmarks():
    frames = [_frame(i * 33, presence=1.0) for i in range(40)]
    session = _session(frames, frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is True
