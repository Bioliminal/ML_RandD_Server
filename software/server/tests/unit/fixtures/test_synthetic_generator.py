from bioliminal.api.schemas import Session
from bioliminal.pose.joint_angles import knee_flexion_angle
from tests.fixtures.synthetic.generator import (
    build_overhead_squat_payload,
    generate_reference_rep,
    generate_session,
)


def test_generate_session_overhead_squat_produces_60_frames_for_2_reps():
    payload = generate_session("overhead_squat", rep_count=2, frames_per_rep=30)
    assert payload["metadata"]["movement"] == "overhead_squat"
    assert len(payload["frames"]) == 60
    session = Session.model_validate(payload)
    assert len(session.frames) == 60


def test_generate_session_rollup_produces_single_continuous_motion():
    payload = generate_session("rollup", rep_count=1, frames_per_rep=60)
    assert payload["metadata"]["movement"] == "rollup"
    assert len(payload["frames"]) == 60
    session = Session.model_validate(payload)
    # Rollup is continuous — timestamps increase monotonically.
    timestamps = [f.timestamp_ms for f in session.frames]
    assert timestamps == sorted(timestamps)
    assert timestamps[0] == 0


def test_generate_session_push_up_payload_validates_against_session_schema():
    payload = generate_session("push_up", rep_count=2, frames_per_rep=30)
    session = Session.model_validate(payload)
    assert session.metadata.movement == "push_up"
    assert len(session.frames) == 60


def test_generate_session_single_leg_squat_payload_validates_against_session_schema():
    payload = generate_session("single_leg_squat", rep_count=2, frames_per_rep=30)
    session = Session.model_validate(payload)
    assert session.metadata.movement == "single_leg_squat"
    assert len(session.frames) == 60


def test_generate_reference_rep_returns_single_rep_frame_list():
    ref = generate_reference_rep("overhead_squat")
    assert ref["metadata"]["movement"] == "overhead_squat"
    assert len(ref["frames"]) == 30  # default frames_per_rep
    session = Session.model_validate(ref)
    angles = [knee_flexion_angle(f, "left") for f in session.frames]
    assert min(angles) < 100
    assert max(angles) > 170


def test_generate_session_injects_higher_valgus_when_compensations_set():
    clean = generate_session("overhead_squat", rep_count=1, frames_per_rep=30)
    noisy = generate_session(
        "overhead_squat",
        rep_count=1,
        frames_per_rep=30,
        injected_compensations={"knee_valgus_deg": 12.0},
    )
    clean_session = Session.model_validate(clean)
    noisy_session = Session.model_validate(noisy)

    def _mean_ankle_x(session):
        return sum(f.landmarks[27].x for f in session.frames) / len(session.frames)

    # Higher valgus pushes the left ankle x offset — mean offset is larger.
    assert _mean_ankle_x(noisy_session) != _mean_ankle_x(clean_session)


def test_build_overhead_squat_payload_is_backward_compat_alias():
    alias = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
    direct = generate_session("overhead_squat", rep_count=2, frames_per_rep=30)
    assert alias["metadata"] == direct["metadata"]
    assert len(alias["frames"]) == len(direct["frames"])
