from pydantic import BaseModel, Field

from auralink.pipeline.artifacts import (
    AngleTimeSeries,
    LiftedAngleTimeSeries,
    MovementTemporalSummary,
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    PhaseBoundaries,
    RepBoundaries,
    SessionQualityReport,
    SkeletonBundle,
    WithinMovementTrend,
)
from auralink.reasoning.observations import ChainObservation
from auralink.protocol.schemas import CrossMovementMetric


class TemporalSection(BaseModel):
    """Plan 3 temporal analysis slot. Populated for rep-based movements."""

    movement_temporal_summary: MovementTemporalSummary | None = None


class CrossMovementSection(BaseModel):
    """Plan 3 cross-movement slot. Populated only by the protocol aggregator."""

    cross_movement_metrics: list[CrossMovementMetric] = Field(default_factory=list)


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
    movement_temporal_summary: MovementTemporalSummary | None = None


class Report(BaseModel):
    metadata: ReportMetadata
    movement_section: MovementSection
    overall_narrative: str
    temporal_section: TemporalSection | None = None
    cross_movement_section: CrossMovementSection | None = None
