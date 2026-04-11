from typing import Protocol

from auralink.ml.lifter import LiftedAngleTimeSeries
from auralink.pipeline.artifacts import SkeletonBundle

__all__ = ["NoOpSkeletonFitter", "SkeletonBundle", "SkeletonFitter"]


class SkeletonFitter(Protocol):
    def fit(self, lifted: LiftedAngleTimeSeries) -> SkeletonBundle: ...


class NoOpSkeletonFitter:
    def fit(self, lifted: LiftedAngleTimeSeries) -> SkeletonBundle:
        return SkeletonBundle(params={}, fitted=False)
