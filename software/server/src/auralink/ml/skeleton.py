from typing import Protocol

from pydantic import BaseModel, Field

from auralink.ml.lifter import LiftedAngleTimeSeries


class SkeletonBundle(BaseModel):
    """Parametric skeleton fit output.

    A real HSMR/SKEL fitter will populate `params` with the 46-DOF shape
    coefficients. NoOpSkeletonFitter returns an empty bundle with
    `fitted=False`. Task 9 re-homes this schema in `pipeline/artifacts.py`.
    """

    params: dict[str, float] = Field(default_factory=dict)
    fitted: bool


class SkeletonFitter(Protocol):
    def fit(self, lifted: LiftedAngleTimeSeries) -> SkeletonBundle: ...


class NoOpSkeletonFitter:
    """No-op skeleton fitter used as the Plan 4 default."""

    def fit(self, lifted: LiftedAngleTimeSeries) -> SkeletonBundle:
        return SkeletonBundle(params={}, fitted=False)
