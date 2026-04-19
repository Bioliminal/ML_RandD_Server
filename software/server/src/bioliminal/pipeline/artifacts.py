from typing import Literal

from pydantic import BaseModel, Field

from bioliminal.reasoning.observations import ChainObservation


class QualityIssue(BaseModel):
    code: str
    detail: str


class SessionQualityReport(BaseModel):
    passed: bool
    issues: list[QualityIssue] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)


class AngleTimeSeries(BaseModel):
    angles: dict[str, list[float]]
    timestamps_ms: list[int]


class NormalizedAngleTimeSeries(BaseModel):
    angles: dict[str, list[float]]
    timestamps_ms: list[int]
    scale_factor: float = Field(gt=0)


class RepBoundaryModel(BaseModel):
    start_index: int = Field(ge=0)
    bottom_index: int = Field(ge=0)
    end_index: int = Field(ge=0)
    start_angle: float
    bottom_angle: float
    end_angle: float


class RepBoundaries(BaseModel):
    by_angle: dict[str, list[RepBoundaryModel]] = Field(default_factory=dict)


class RepMetric(BaseModel):
    rep_index: int = Field(ge=0)
    amplitude_deg: float
    peak_velocity_deg_per_s: float
    rom_deg: float
    mean_trunk_lean_deg: float
    mean_knee_valgus_deg: float
    # Bicep-only fields. Default None so squat/other movement pipelines are unaffected.
    concentric_s: float | None = None
    eccentric_s: float | None = None
    # Session-scalar CV + decline metrics. Same value repeated on every rep
    # so the rule engine's per-rep aggregator enum (max/min/mean) can
    # "aggregate" them correctly via max.
    velocity_decline_pct: float | None = None
    amplitude_cv_pct: float | None = None
    tempo_cv_pct: float | None = None


class PerRepMetrics(BaseModel):
    primary_angle: str
    reps: list[RepMetric] = Field(default_factory=list)


class WithinMovementTrend(BaseModel):
    rom_slope_deg_per_rep: float
    velocity_slope_deg_per_s_per_rep: float
    valgus_slope_deg_per_rep: float
    trunk_lean_slope_deg_per_rep: float
    fatigue_detected: bool


class RepComparison(BaseModel):
    """One rep scored against the movement's reference rep.

    ncc_score may be NaN when the user rep is a flat signal (zero variance);
    callers must handle NaN before arithmetic. rom_deviation_pct is a signed
    percentage: positive means the user's range of motion exceeds the
    reference, negative means it falls short. status is the combined
    classification from NCC and ROM thresholds (NCC amplitude-guard rule —
    see plan architectural decision 5).
    """

    rep_index: int = Field(ge=0)
    angle: str
    ncc_score: float
    dtw_distance: float = Field(ge=0.0)
    rom_user_deg: float = Field(ge=0.0)
    rom_reference_deg: float = Field(ge=0.0)
    rom_deviation_pct: float
    status: Literal["clean", "concern", "flag"]


class MovementTemporalSummary(BaseModel):
    """Within-movement temporal aggregation over a list of RepComparisons.

    ncc_slope_per_rep is fit with numpy.polyfit over the NCC scores treating
    rep index as x; a negative slope means shape is drifting away from the
    reference across the set. mean_rom_deviation_pct is a plain mean of the
    rom_deviation_pct field. form_drift_detected is a joint condition — both
    a sufficiently negative NCC slope AND a large mean ROM deviation must be
    present — to avoid false positives from a single noisy rep.
    """

    primary_angle: str
    rep_comparisons: list[RepComparison] = Field(default_factory=list)
    mean_ncc: float
    ncc_slope_per_rep: float
    mean_rom_deviation_pct: float
    form_drift_detected: bool


class LiftedAngleTimeSeries(BaseModel):
    angles: dict[str, list[float]]
    timestamps_ms: list[int]
    scale_factor: float = Field(gt=0)
    is_3d: bool


class SkeletonBundle(BaseModel):
    params: dict[str, float] = Field(default_factory=dict)
    fitted: bool


class Phase(BaseModel):
    index: int = Field(ge=0)
    start_timestamp_ms: int = Field(ge=0)
    end_timestamp_ms: int = Field(ge=0)
    label: str


class PhaseBoundaries(BaseModel):
    phases: list[Phase] = Field(default_factory=list)


class PipelineArtifacts(BaseModel):
    quality_report: SessionQualityReport
    angle_series: AngleTimeSeries | None = None
    normalized_angle_series: NormalizedAngleTimeSeries | None = None
    rep_boundaries: RepBoundaries | None = None
    per_rep_metrics: PerRepMetrics | None = None
    within_movement_trend: WithinMovementTrend | None = None
    lift_result: LiftedAngleTimeSeries | None = None
    skeleton_result: SkeletonBundle | None = None
    phase_boundaries: PhaseBoundaries | None = None
    chain_observations: list[ChainObservation] | None = None
    movement_temporal_summary: MovementTemporalSummary | None = None
