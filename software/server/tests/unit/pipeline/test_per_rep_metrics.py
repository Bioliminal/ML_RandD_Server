import numpy as np

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.artifacts import (
    NormalizedAngleTimeSeries,
    RepBoundaries,
    RepBoundaryModel,
)
from auralink.pipeline.stages.base import StageContext
from auralink.pipeline.stages.per_rep_metrics import run_per_rep_metrics


def _ctx(knee_flex: list[float], trunk: list[float], valgus_l: list[float], valgus_r: list[float]):
    n = len(knee_flex)
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    frames = [Frame(timestamp_ms=i * 33, landmarks=[lm] * 33) for i in range(n)]
    session = Session(
        metadata=SessionMetadata(movement="overhead_squat", device="t", model="t", frame_rate=30.0),
        frames=frames,
    )
    ctx = StageContext(session=session)
    ctx.artifacts["normalize"] = NormalizedAngleTimeSeries(
        angles={
            "left_knee_flexion": knee_flex,
            "right_knee_flexion": knee_flex,
            "trunk_lean": trunk,
            "left_knee_valgus": valgus_l,
            "right_knee_valgus": valgus_r,
        },
        timestamps_ms=[f.timestamp_ms for f in frames],
        scale_factor=0.3,
    )
    ctx.artifacts["rep_segment"] = RepBoundaries(
        by_angle={
            "left_knee_flexion": [
                RepBoundaryModel(
                    start_index=0,
                    bottom_index=n // 2,
                    end_index=n - 1,
                    start_angle=knee_flex[0],
                    bottom_angle=knee_flex[n // 2],
                    end_angle=knee_flex[n - 1],
                )
            ]
        }
    )
    return ctx


def test_per_rep_metrics_computes_amplitude_rom_and_velocity():
    descent = np.linspace(180, 90, 15).tolist()
    ascent = np.linspace(90, 180, 15).tolist()
    knee = descent + ascent
    trunk = [5.0] * len(knee)
    valgus_l = [3.0] * len(knee)
    valgus_r = [1.0] * len(knee)
    ctx = _ctx(knee, trunk, valgus_l, valgus_r)

    result = run_per_rep_metrics(ctx)
    assert result.primary_angle == "left_knee_flexion"
    assert len(result.reps) == 1
    rep = result.reps[0]
    assert rep.rep_index == 0
    assert rep.amplitude_deg == 90.0
    assert rep.rom_deg == 90.0
    assert 150 < rep.peak_velocity_deg_per_s < 250
    assert rep.mean_trunk_lean_deg == 5.0
    assert rep.mean_knee_valgus_deg == 3.0


def test_per_rep_metrics_empty_when_no_reps():
    n = 30
    ctx = _ctx([180.0] * n, [0.0] * n, [0.0] * n, [0.0] * n)
    ctx.artifacts["rep_segment"] = RepBoundaries(by_angle={"left_knee_flexion": []})
    result = run_per_rep_metrics(ctx)
    assert result.reps == []
