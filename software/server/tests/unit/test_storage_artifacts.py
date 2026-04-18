import pytest

from bioliminal.api.schemas import Frame, Landmark, Session, SessionMetadata
from bioliminal.pipeline.artifacts import PipelineArtifacts, QualityIssue, SessionQualityReport
from bioliminal.pipeline.storage import SessionStorage


def _session() -> Session:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    frame = Frame(timestamp_ms=0, landmarks=[lm for _ in range(33)])
    return Session(
        metadata=SessionMetadata(movement="overhead_squat", device="t", model="t", frame_rate=30.0),
        frames=[frame],
    )


def _artifacts() -> PipelineArtifacts:
    return PipelineArtifacts(
        quality_report=SessionQualityReport(
            passed=True,
            issues=[QualityIssue(code="ok", detail="all checks passed")],
            metrics={"frame_rate": 30.0},
        ),
    )


def test_save_and_load_artifacts_round_trip(tmp_path):
    storage = SessionStorage(base_dir=tmp_path)
    session_id = storage.save(_session())
    storage.save_artifacts(session_id, _artifacts())
    loaded = storage.load_artifacts(session_id)
    assert loaded.quality_report.passed is True
    assert loaded.quality_report.issues[0].code == "ok"


def test_load_artifacts_missing_raises_file_not_found(tmp_path):
    storage = SessionStorage(base_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        storage.load_artifacts("nonexistent-id")
