from pydantic import BaseModel, Field


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


class PerRepMetrics(BaseModel):
    primary_angle: str
    reps: list[RepMetric] = Field(default_factory=list)


class WithinMovementTrend(BaseModel):
    rom_slope_deg_per_rep: float
    velocity_slope_deg_per_s_per_rep: float
    valgus_slope_deg_per_rep: float
    trunk_lean_slope_deg_per_rep: float
    fatigue_detected: bool


class PipelineArtifacts(BaseModel):
    quality_report: SessionQualityReport
    angle_series: AngleTimeSeries | None = None
    normalized_angle_series: NormalizedAngleTimeSeries | None = None
    rep_boundaries: RepBoundaries | None = None
    per_rep_metrics: PerRepMetrics | None = None
    within_movement_trend: WithinMovementTrend | None = None
