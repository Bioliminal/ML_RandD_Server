"""Synthetic 10-rep bicep curl Session factory for deterministic integration tests."""
import math

from bioliminal.api.schemas import Frame, PoseLandmark, Session, SessionMetadata


def synthetic_bicep_session(
    *,
    n_reps: int = 10,
    samples_per_rep: int = 90,
    peak_flexion_deg: float = 30.0,
    full_extension_deg: float = 170.0,
    frame_rate: float = 30.0,
    visibility: float = 0.9,
) -> Session:
    """Clean cosine-shaped curl. Shoulder at (0,0), extended-wrist at (2,0),
    folded-wrist at (cos(flex), sin(flex)). Elbow always at (1,0)."""
    frames: list[Frame] = []
    total = n_reps * samples_per_rep
    for i in range(total):
        t = 2 * math.pi * (i % samples_per_rep) / samples_per_rep
        angle_deg = (peak_flexion_deg + full_extension_deg) / 2.0 + \
                    (full_extension_deg - peak_flexion_deg) / 2.0 * math.cos(t)
        angle_rad = math.radians(angle_deg)
        wrist_x = 1.0 + math.cos(math.pi - angle_rad)
        wrist_y = math.sin(math.pi - angle_rad)

        landmarks = [
            PoseLandmark(x=0.5, y=0.5, z=0.0, visibility=visibility, presence=1.0)
            for _ in range(33)
        ]
        landmarks[11] = PoseLandmark(x=0.0, y=0.0, z=0.0, visibility=visibility, presence=1.0)
        landmarks[13] = PoseLandmark(x=1.0, y=0.0, z=0.0, visibility=visibility, presence=1.0)
        landmarks[15] = PoseLandmark(x=wrist_x, y=wrist_y, z=0.0, visibility=visibility, presence=1.0)
        landmarks[12] = PoseLandmark(x=0.0, y=0.1, z=0.0, visibility=visibility, presence=1.0)
        landmarks[14] = PoseLandmark(x=1.0, y=0.1, z=0.0, visibility=visibility, presence=1.0)
        landmarks[16] = PoseLandmark(x=wrist_x, y=wrist_y + 0.1, z=0.0, visibility=visibility, presence=1.0)
        landmarks[23] = PoseLandmark(x=0.0, y=1.0, z=0.0, visibility=visibility, presence=1.0)
        landmarks[24] = PoseLandmark(x=0.1, y=1.0, z=0.0, visibility=visibility, presence=1.0)

        frames.append(Frame(timestamp_ms=int(i * 1000 / frame_rate), landmarks=landmarks))

    return Session(
        metadata=SessionMetadata(
            movement="bicep_curl",
            device="test-device",
            model="mediapipe_blazepose_full",
            frame_rate=frame_rate,
        ),
        frames=frames,
    )
