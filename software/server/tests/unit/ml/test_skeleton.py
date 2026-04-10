from auralink.ml.lifter import LiftedAngleTimeSeries
from auralink.ml.skeleton import NoOpSkeletonFitter, SkeletonBundle, SkeletonFitter


def _sample_lifted() -> LiftedAngleTimeSeries:
    return LiftedAngleTimeSeries(
        angles={"left_knee_flexion": [180.0, 150.0]},
        timestamps_ms=[0, 33],
        scale_factor=0.3,
        is_3d=False,
    )


def test_noop_skeleton_fitter_returns_empty_unfitted_bundle():
    fitter: SkeletonFitter = NoOpSkeletonFitter()
    bundle = fitter.fit(_sample_lifted())
    assert isinstance(bundle, SkeletonBundle)
    assert bundle.params == {}
    assert bundle.fitted is False


def test_noop_skeleton_fitter_is_idempotent():
    fitter = NoOpSkeletonFitter()
    first = fitter.fit(_sample_lifted())
    second = fitter.fit(_sample_lifted())
    assert first.params == second.params
    assert first.fitted == second.fitted
