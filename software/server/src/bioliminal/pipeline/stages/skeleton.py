from bioliminal.ml.lifter import LiftedAngleTimeSeries
from bioliminal.ml.skeleton import NoOpSkeletonFitter, SkeletonBundle, SkeletonFitter
from bioliminal.pipeline.stages.base import STAGE_NAME_LIFT, StageContext

_default_fitter: SkeletonFitter = NoOpSkeletonFitter()


def run_skeleton(ctx: StageContext, fitter: SkeletonFitter | None = None) -> SkeletonBundle:
    """Fit a parametric skeleton to the lifted angle time series.

    Default implementation is `NoOpSkeletonFitter` — returns an empty bundle
    with `fitted=False`. Accepts an injected `SkeletonFitter` for tests and
    future HSMR wiring.
    """
    impl = fitter if fitter is not None else _default_fitter
    lifted: LiftedAngleTimeSeries = ctx.artifacts[STAGE_NAME_LIFT]
    return impl.fit(lifted)
