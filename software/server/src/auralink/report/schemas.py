from pydantic import BaseModel, Field

from auralink.pipeline.artifacts import (
    AngleTimeSeries,
    LiftedAngleTimeSeries,
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    PhaseBoundaries,
    RepBoundaries,
    SessionQualityReport,
    SkeletonBundle,
    WithinMovementTrend,
)
from auralink.reasoning.observations import ChainObservation


class TemporalSection(BaseModel):
    """Placeholder slot — Plan 3 populates with DTW/temporal analysis."""


class CrossMovementSection(BaseModel):
    """Placeholder slot — Plan 3 populates with cross-movement aggregation."""


class ReportMetadata(BaseModel):
    session_id: str
    movement: str
    captured_at_ms: int | None = None


class MovementSection(BaseModel):
    movement: str
    quality_report: SessionQualityReport
    angle_series: AngleTimeSeries | None = None
    normalized_angle_series: NormalizedAngleTimeSeries | None = None
    rep_boundaries: RepBoundaries | None = None
    per_rep_metrics: PerRepMetrics | None = None
    within_movement_trend: WithinMovementTrend | None = None
    lift_result: LiftedAngleTimeSeries | None = None
    skeleton_result: SkeletonBundle | None = None
    phase_boundaries: PhaseBoundaries | None = None
    chain_observations: list[ChainObservation] = Field(default_factory=list)


class Report(BaseModel):
    metadata: ReportMetadata
    movement_section: MovementSection
    overall_narrative: str
    temporal_section: TemporalSection | None = None
    cross_movement_section: CrossMovementSection | None = None
