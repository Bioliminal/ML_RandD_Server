from auralink.ml.lifter import IdentityLifter, Lifter, LiftedAngleTimeSeries
from auralink.pipeline.artifacts import NormalizedAngleTimeSeries
from auralink.pipeline.stages.base import STAGE_NAME_NORMALIZE, StageContext

_default_lifter: Lifter = IdentityLifter()


def run_lift(ctx: StageContext, lifter: Lifter | None = None) -> LiftedAngleTimeSeries:
    """Lift 2D normalized angles to 3D-aware angles.

    Default implementation uses `IdentityLifter` — a 2D passthrough.
    Accepts an injected `Lifter` for tests and future MotionBERT wiring.
    """
    impl = lifter if lifter is not None else _default_lifter
    normalized: NormalizedAngleTimeSeries = ctx.artifacts[STAGE_NAME_NORMALIZE]
    return impl.lift(normalized)
