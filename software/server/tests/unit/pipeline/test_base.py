from bioliminal.api.schemas import Frame, Landmark, Session, SessionMetadata
from bioliminal.pipeline.stages.base import Stage, StageContext


def _minimal_session() -> Session:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    frame = Frame(timestamp_ms=0, landmarks=[lm for _ in range(33)])
    return Session(
        metadata=SessionMetadata(
            movement="overhead_squat",
            device="test",
            model="test",
            frame_rate=30.0,
        ),
        frames=[frame],
    )


def test_context_exposes_session_and_movement_type():
    session = _minimal_session()
    ctx = StageContext(session=session)
    assert ctx.session is session
    assert ctx.movement_type == "overhead_squat"
    assert ctx.artifacts == {}
    assert ctx.config == {}


def test_stage_runs_callable_on_context():
    session = _minimal_session()
    ctx = StageContext(session=session)
    stage = Stage(name="count_frames", run=lambda c: len(c.session.frames))
    assert stage.name == "count_frames"
    assert stage.run(ctx) == 1
