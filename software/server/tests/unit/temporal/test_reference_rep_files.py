from pathlib import Path

from bioliminal.temporal.reference_reps import ReferenceRep, load_reference_rep

_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config" / "reference_reps"


# Primary angles that rep_comparison will look up per movement, sourced
# from bioliminal.pipeline.stages.per_rep_metrics.PRIMARY_ANGLE and the
# push_up stage's analogous constant. If these drift, T11's stage fails
# at runtime with a cryptic KeyError — catch it here instead.
_PRIMARY_ANGLE_BY_MOVEMENT = {
    "overhead_squat": "left_knee_flexion",
    "single_leg_squat": "left_knee_flexion",
    "push_up": "left_knee_flexion",  # push_up shares the synthetic sweep
}


def test_committed_reference_reps_load_for_all_rep_based_movements():
    for movement in ("overhead_squat", "single_leg_squat", "push_up"):
        rep = load_reference_rep(movement, config_dir=_CONFIG_DIR)
        assert isinstance(rep, ReferenceRep)
        assert rep.movement == movement
        assert rep.frames_per_rep > 0
        # every angle trace has the same length as frames_per_rep
        for _name, series in rep.angles.items():
            assert len(series) == rep.frames_per_rep


def test_reference_reps_contain_primary_angle_per_movement():
    """Plumbing guard: the primary angle rep_comparison will look up at
    runtime must exist in the committed reference rep. Without this check
    a reference/runtime key mismatch only surfaces in T11's stage tests
    or worse in T17's dev-server smoke."""
    for movement, primary_angle in _PRIMARY_ANGLE_BY_MOVEMENT.items():
        rep = load_reference_rep(movement, config_dir=_CONFIG_DIR)
        assert primary_angle in rep.angles, (
            f"reference rep for {movement} missing primary_angle "
            f"{primary_angle!r}; has {sorted(rep.angles.keys())}"
        )
        assert len(rep.angles[primary_angle]) > 0
