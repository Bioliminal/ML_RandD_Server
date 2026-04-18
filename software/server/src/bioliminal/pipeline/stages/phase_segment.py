from bioliminal.ml.phase_segmenter import PhaseBoundaries, PhaseSegmenter, SinglePhaseSegmenter
from bioliminal.pipeline.stages.base import StageContext

_default_segmenter: PhaseSegmenter = SinglePhaseSegmenter()


def run_phase_segment(
    ctx: StageContext,
    segmenter: PhaseSegmenter | None = None,
) -> PhaseBoundaries:
    """Segment a continuous movement into phases.

    Default implementation is `SinglePhaseSegmenter` — one phase spanning the
    entire session, labeled `full_movement`. Used for `rollup` movements that
    do not have rep cycles.
    """
    impl = segmenter if segmenter is not None else _default_segmenter
    return impl.segment(ctx)
