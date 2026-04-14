"""Shared pytest fixtures for BioLiminal server tests."""

import pytest

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata


@pytest.fixture
def neutral_landmark() -> Landmark:
    return Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)


@pytest.fixture
def neutral_frame(neutral_landmark: Landmark) -> Frame:
    return Frame(
        timestamp_ms=0,
        landmarks=[neutral_landmark for _ in range(33)],
    )


@pytest.fixture
def minimal_session(neutral_frame: Frame) -> Session:
    return Session(
        metadata=SessionMetadata(
            movement="overhead_squat",
            device="test-device",
            model="test-model",
            frame_rate=30.0,
        ),
        frames=[neutral_frame],
    )
