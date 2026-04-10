from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.artifacts import PerRepMetrics, RepMetric
from auralink.pipeline.stages.base import StageContext
from auralink.pipeline.stages.within_movement_trend import run_within_movement_trend


def _ctx_with_reps(reps: list[RepMetric]) -> StageContext:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    session = Session(
        metadata=SessionMetadata(movement="overhead_squat", device="t", model="t", frame_rate=30.0),
        frames=[Frame(timestamp_ms=0, landmarks=[lm] * 33)],
    )
    ctx = StageContext(session=session)
    ctx.artifacts["per_rep_metrics"] = PerRepMetrics(primary_angle="left_knee_flexion", reps=reps)
    return ctx


def _rep(i: int, rom: float, vel: float, valgus: float, trunk: float) -> RepMetric:
    return RepMetric(
        rep_index=i,
        amplitude_deg=rom,
        peak_velocity_deg_per_s=vel,
        rom_deg=rom,
        mean_trunk_lean_deg=trunk,
        mean_knee_valgus_deg=valgus,
    )


def test_within_movement_trend_detects_decreasing_rom_as_fatigue():
    reps = [
        _rep(0, rom=90, vel=200, valgus=2, trunk=3),
        _rep(1, rom=85, vel=195, valgus=3, trunk=3),
        _rep(2, rom=78, vel=180, valgus=4, trunk=4),
        _rep(3, rom=72, vel=170, valgus=6, trunk=5),
    ]
    result = run_within_movement_trend(_ctx_with_reps(reps))
    assert result.rom_slope_deg_per_rep < -5.0
    assert result.fatigue_detected is True


def test_within_movement_trend_clean_session_no_fatigue():
    reps = [
        _rep(0, rom=90, vel=200, valgus=2, trunk=3),
        _rep(1, rom=91, vel=201, valgus=2, trunk=3),
        _rep(2, rom=90, vel=200, valgus=2, trunk=3),
        _rep(3, rom=91, vel=202, valgus=2, trunk=3),
    ]
    result = run_within_movement_trend(_ctx_with_reps(reps))
    assert result.fatigue_detected is False
    assert abs(result.rom_slope_deg_per_rep) < 1.0


def test_within_movement_trend_empty_reps_produces_zero_slopes():
    result = run_within_movement_trend(_ctx_with_reps([]))
    assert result.rom_slope_deg_per_rep == 0.0
    assert result.fatigue_detected is False
