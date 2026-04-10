"""Single-purpose synthetic fixture for overhead_squat integration tests.

Plan 4 will absorb this into the shared `tests/fixtures/synthetic/generator.py`.
Until then, callers in Plan 1's integration tests use build_overhead_squat_payload().
"""

import math


def _landmark(x: float, y: float) -> dict:
    return {"x": x, "y": y, "z": 0.0, "visibility": 1.0, "presence": 1.0}


def _frame_for_knee_angle(
    timestamp_ms: int,
    knee_flexion_deg: float,
    knee_valgus_deg: float = 0.0,
    trunk_lean_deg: float = 4.0,
) -> dict:
    """Stylized pose: hip at (0.5, 0.5), knee and ankle positioned so
    knee_flexion_angle() returns the requested value, with a small constant
    knee valgus and a small constant trunk lean.
    """
    hip = (0.5, 0.5)
    knee = (0.5, 0.7)
    r = 0.2
    angle_from_down_rad = math.radians(180.0 - knee_flexion_deg)
    # Apply valgus as a small horizontal offset on the ankle position.
    valgus_offset = math.radians(knee_valgus_deg) * 0.1
    ankle_x = knee[0] + r * math.sin(angle_from_down_rad) + valgus_offset
    ankle_y = knee[1] + r * math.cos(angle_from_down_rad)

    trunk_rad = math.radians(trunk_lean_deg)
    shoulder_x = hip[0] + 0.2 * math.sin(trunk_rad)
    shoulder_y = hip[1] - 0.2 * math.cos(trunk_rad)

    landmarks: list[dict] = [_landmark(0.0, 0.0) for _ in range(33)]
    landmarks[11] = _landmark(shoulder_x - 0.05, shoulder_y)  # LEFT_SHOULDER
    landmarks[12] = _landmark(shoulder_x + 0.05, shoulder_y)  # RIGHT_SHOULDER
    landmarks[23] = _landmark(hip[0] - 0.05, hip[1])          # LEFT_HIP
    landmarks[24] = _landmark(hip[0] + 0.05, hip[1])          # RIGHT_HIP
    landmarks[25] = _landmark(knee[0] - 0.05, knee[1])        # LEFT_KNEE
    landmarks[26] = _landmark(knee[0] + 0.05, knee[1])        # RIGHT_KNEE
    landmarks[27] = _landmark(ankle_x - 0.05, ankle_y)        # LEFT_ANKLE
    landmarks[28] = _landmark(ankle_x + 0.05, ankle_y)        # RIGHT_ANKLE

    for i in range(33):
        if landmarks[i]["x"] == 0.0 and landmarks[i]["y"] == 0.0:
            landmarks[i] = _landmark(0.5, 0.5)

    return {"timestamp_ms": timestamp_ms, "landmarks": landmarks}


def build_overhead_squat_payload(
    rep_count: int = 2,
    frames_per_rep: int = 30,
    frame_rate: float = 30.0,
    knee_valgus_deg: float = 2.0,
    trunk_lean_deg: float = 4.0,
) -> dict:
    """Build a POST /sessions payload representing `rep_count` overhead squats."""
    frames: list[dict] = []
    frame_interval_ms = int(round(1000.0 / frame_rate))
    for rep in range(rep_count):
        for i in range(frames_per_rep):
            theta = (i / frames_per_rep) * 2.0 * math.pi
            knee_flex = 135.0 + 45.0 * math.cos(theta)  # 90..180..90
            frames.append(
                _frame_for_knee_angle(
                    timestamp_ms=(rep * frames_per_rep + i) * frame_interval_ms,
                    knee_flexion_deg=knee_flex,
                    knee_valgus_deg=knee_valgus_deg,
                    trunk_lean_deg=trunk_lean_deg,
                )
            )
    return {
        "metadata": {
            "movement": "overhead_squat",
            "device": "synthetic",
            "model": "synthetic_v1",
            "frame_rate": frame_rate,
        },
        "frames": frames,
    }
