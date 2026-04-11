"""Shared synthetic fixture generator for all four movement types.

Owns `generate_session()` (produces full POST /sessions payloads) and
`generate_reference_rep()` (single-rep frame list consumed by Plan 3).
This module is the single source of synthetic data; Plans 2 and 3 import
from here rather than building their own generators.
"""

import math
from typing import Any, Literal

MovementType = Literal["overhead_squat", "single_leg_squat", "push_up", "rollup"]


def _landmark(x: float, y: float) -> dict:
    return {"x": x, "y": y, "z": 0.0, "visibility": 1.0, "presence": 1.0}


def _frame_for_knee_angle(
    timestamp_ms: int,
    knee_flexion_deg: float,
    knee_valgus_deg: float = 0.0,
    trunk_lean_deg: float = 4.0,
) -> dict:
    """Stylized pose: hip at (0.5, 0.5), knee at (0.5, 0.7), ankle placed so
    `knee_flexion_angle()` returns the requested value. Applies a horizontal
    valgus offset on the ankle and a trunk-lean offset on the shoulder mid.
    """
    hip = (0.5, 0.5)
    knee = (0.5, 0.7)
    r = 0.2
    angle_from_down_rad = math.radians(180.0 - knee_flexion_deg)
    valgus_offset = math.radians(knee_valgus_deg) * 0.1
    ankle_x = knee[0] + r * math.sin(angle_from_down_rad) + valgus_offset
    ankle_y = knee[1] + r * math.cos(angle_from_down_rad)

    trunk_rad = math.radians(trunk_lean_deg)
    shoulder_x = hip[0] + 0.2 * math.sin(trunk_rad)
    shoulder_y = hip[1] - 0.2 * math.cos(trunk_rad)

    landmarks: list[dict] = [_landmark(0.0, 0.0) for _ in range(33)]
    landmarks[11] = _landmark(shoulder_x - 0.05, shoulder_y)  # LEFT_SHOULDER
    landmarks[12] = _landmark(shoulder_x + 0.05, shoulder_y)  # RIGHT_SHOULDER
    landmarks[23] = _landmark(hip[0] - 0.05, hip[1])  # LEFT_HIP
    landmarks[24] = _landmark(hip[0] + 0.05, hip[1])  # RIGHT_HIP
    landmarks[25] = _landmark(knee[0] - 0.05, knee[1])  # LEFT_KNEE
    landmarks[26] = _landmark(knee[0] + 0.05, knee[1])  # RIGHT_KNEE
    landmarks[27] = _landmark(ankle_x - 0.05, ankle_y)  # LEFT_ANKLE
    landmarks[28] = _landmark(ankle_x + 0.05, ankle_y)  # RIGHT_ANKLE

    for i in range(33):
        if landmarks[i]["x"] == 0.0 and landmarks[i]["y"] == 0.0:
            landmarks[i] = _landmark(0.5, 0.5)

    return {"timestamp_ms": timestamp_ms, "landmarks": landmarks}


def _rep_cycling_frames(
    rep_count: int,
    frames_per_rep: int,
    frame_interval_ms: int,
    knee_valgus_deg: float,
    trunk_lean_deg: float,
) -> list[dict]:
    frames: list[dict] = []
    for rep in range(rep_count):
        for i in range(frames_per_rep):
            theta = (i / frames_per_rep) * 2.0 * math.pi
            knee_flex = 135.0 + 45.0 * math.cos(theta)  # 90..180..90 sweep
            frames.append(
                _frame_for_knee_angle(
                    timestamp_ms=(rep * frames_per_rep + i) * frame_interval_ms,
                    knee_flexion_deg=knee_flex,
                    knee_valgus_deg=knee_valgus_deg,
                    trunk_lean_deg=trunk_lean_deg,
                )
            )
    return frames


def _continuous_rollup_frames(
    frame_count: int,
    frame_interval_ms: int,
    trunk_lean_deg: float,
) -> list[dict]:
    """Single-phase continuous motion — half-cosine knee sweep, no rep cycling."""
    frames: list[dict] = []
    for i in range(frame_count):
        theta = (i / frame_count) * math.pi  # 0..pi single arc
        knee_flex = 135.0 + 45.0 * math.cos(theta)
        frames.append(
            _frame_for_knee_angle(
                timestamp_ms=i * frame_interval_ms,
                knee_flexion_deg=knee_flex,
                knee_valgus_deg=0.0,
                trunk_lean_deg=trunk_lean_deg,
            )
        )
    return frames


def generate_session(
    movement: MovementType,
    rep_count: int = 2,
    frames_per_rep: int = 30,
    frame_rate: float = 30.0,
    injected_compensations: dict[str, Any] | None = None,
) -> dict:
    """Produce a valid POST /sessions payload for any movement type.

    For rep-based movements (overhead_squat, single_leg_squat, push_up) the
    payload contains `rep_count * frames_per_rep` frames cycling through a
    90°..180° knee flexion sweep. For rollup, the payload contains a single
    continuous half-cosine motion with no rep cycling.

    Plan 4 stub: all rep-cycling movements share a knee-flexion sweep, so a
    push_up fixture is biomechanically nonsense (it has squat landmarks
    labeled as push_up). This is tolerable because push_up's pipeline stops
    at the skeleton stage and never inspects the frames for push-up-specific
    angles. Realism is deferred to a follow-on epoch that adds real pose
    templates per movement.

    `injected_compensations` accepts:
    - `knee_valgus_deg: float` — horizontal ankle offset driver
    - `trunk_lean_deg: float` — shoulder lean offset driver
    """
    comps = injected_compensations or {}
    knee_valgus_deg = float(comps.get("knee_valgus_deg", 2.0))
    trunk_lean_deg = float(comps.get("trunk_lean_deg", 4.0))
    frame_interval_ms = int(round(1000.0 / frame_rate))

    if movement == "rollup":
        frames = _continuous_rollup_frames(
            frame_count=rep_count * frames_per_rep,
            frame_interval_ms=frame_interval_ms,
            trunk_lean_deg=trunk_lean_deg,
        )
    else:
        frames = _rep_cycling_frames(
            rep_count=rep_count,
            frames_per_rep=frames_per_rep,
            frame_interval_ms=frame_interval_ms,
            knee_valgus_deg=knee_valgus_deg,
            trunk_lean_deg=trunk_lean_deg,
        )

    return {
        "metadata": {
            "movement": movement,
            "device": "synthetic",
            "model": "synthetic_v1",
            "frame_rate": frame_rate,
        },
        "frames": frames,
    }


def generate_reference_rep(
    movement: MovementType,
    frames_per_rep: int = 30,
    frame_rate: float = 30.0,
) -> dict:
    """Return a single-rep fixture payload. Used by Plan 3 as the reference
    template for DTW alignment. Shares the same underlying rep synthesis.
    """
    return generate_session(
        movement=movement,
        rep_count=1,
        frames_per_rep=frames_per_rep,
        frame_rate=frame_rate,
    )


def build_overhead_squat_payload(
    rep_count: int = 2,
    frames_per_rep: int = 30,
    frame_rate: float = 30.0,
    knee_valgus_deg: float = 2.0,
    trunk_lean_deg: float = 4.0,
) -> dict:
    """Backward-compat alias for Plan 1 callers. Delegates to generate_session."""
    return generate_session(
        "overhead_squat",
        rep_count=rep_count,
        frames_per_rep=frames_per_rep,
        frame_rate=frame_rate,
        injected_compensations={
            "knee_valgus_deg": knee_valgus_deg,
            "trunk_lean_deg": trunk_lean_deg,
        },
    )
