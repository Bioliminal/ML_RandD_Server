import numpy as np

from bioliminal.api.schemas import Frame
from bioliminal.pipeline.artifacts import AngleTimeSeries, NormalizedAngleTimeSeries
from bioliminal.pipeline.stages.base import StageContext
from bioliminal.pose.keypoints import LandmarkIndex

_FALLBACK_SCALE = 1e-6


def _hip_shoulder_distance(frame: Frame) -> float:
    l_sh = frame.landmarks[LandmarkIndex.LEFT_SHOULDER]
    r_sh = frame.landmarks[LandmarkIndex.RIGHT_SHOULDER]
    l_hip = frame.landmarks[LandmarkIndex.LEFT_HIP]
    r_hip = frame.landmarks[LandmarkIndex.RIGHT_HIP]
    sh_mid = np.array([(l_sh.x + r_sh.x) / 2, (l_sh.y + r_sh.y) / 2])
    hip_mid = np.array([(l_hip.x + r_hip.x) / 2, (l_hip.y + r_hip.y) / 2])
    return float(np.linalg.norm(sh_mid - hip_mid))


def run_normalize(ctx: StageContext) -> NormalizedAngleTimeSeries:
    raw: AngleTimeSeries = ctx.artifacts["angle_series"]
    distances = [_hip_shoulder_distance(f) for f in ctx.session.frames]
    scale = float(np.median(distances)) if distances else _FALLBACK_SCALE
    if scale <= 0.0:
        scale = _FALLBACK_SCALE
    return NormalizedAngleTimeSeries(
        angles=raw.angles,
        timestamps_ms=raw.timestamps_ms,
        scale_factor=scale,
    )
