import pytest

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.storage import SessionStorage


@pytest.fixture
def sample_session() -> Session:
    landmarks = [Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0, presence=1.0) for _ in range(33)]
    return Session(
        metadata=SessionMetadata(
            movement="overhead_squat",
            device="Pixel 8",
            model="mlkit_pose_detection",
            frame_rate=30.0,
        ),
        frames=[Frame(timestamp_ms=i * 33, landmarks=landmarks) for i in range(5)],
    )


def test_save_and_load_session(tmp_path, sample_session):
    storage = SessionStorage(base_dir=tmp_path)
    session_id = storage.save(sample_session)
    assert session_id
    loaded = storage.load(session_id)
    assert loaded.metadata.movement == "overhead_squat"
    assert len(loaded.frames) == 5


def test_load_missing_session_raises(tmp_path):
    storage = SessionStorage(base_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        storage.load("nonexistent-id")


def test_save_creates_unique_ids(tmp_path, sample_session):
    storage = SessionStorage(base_dir=tmp_path)
    id1 = storage.save(sample_session)
    id2 = storage.save(sample_session)
    assert id1 != id2
