from bioliminal.ml.lifter import IdentityLifter, LiftedAngleTimeSeries, Lifter
from bioliminal.pipeline.artifacts import NormalizedAngleTimeSeries


def _sample_normalized() -> NormalizedAngleTimeSeries:
    return NormalizedAngleTimeSeries(
        angles={"left_knee_flexion": [180.0, 150.0, 120.0]},
        timestamps_ms=[0, 33, 66],
        scale_factor=0.3,
    )


def test_identity_lifter_passes_angles_through_unchanged():
    lifter = IdentityLifter()
    result = lifter.lift(_sample_normalized())
    assert result.angles == {"left_knee_flexion": [180.0, 150.0, 120.0]}
    assert result.timestamps_ms == [0, 33, 66]
    assert result.scale_factor == 0.3
    assert result.is_3d is False


def test_identity_lifter_returns_lifted_angle_time_series_type():
    lifter: Lifter = IdentityLifter()
    result = lifter.lift(_sample_normalized())
    assert isinstance(result, LiftedAngleTimeSeries)
