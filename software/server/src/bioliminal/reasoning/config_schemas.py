from typing import Literal

from pydantic import BaseModel, Field

from bioliminal.reasoning.chains import ChainName


EvidenceLevel = Literal[
    "rct",
    "prospective_cohort",
    "cross_sectional",
    "case_series",
    "expert_consensus",
    "mechanism_only",
]


class EvidenceBlock(BaseModel):
    """Per-rule evidence required by the MSI cherry-pick stance (ML#1, 2026-04-19).

    Every `RuleConfig` must declare what literature supports its kinematic claim.
    Rules with weak or absent supporting evidence are still allowed (level
    `expert_consensus` or `mechanism_only`) but must be honest about it; the
    report-narrative layer can use `level` to gate language strength.
    """

    level: EvidenceLevel
    citation: str = Field(min_length=1)
    mechanism: str = Field(min_length=1)
    correlation: str | None = None
    notes: str | None = None


class ThresholdSetConfig(BaseModel):
    knee_valgus_concern: float
    knee_valgus_flag: float
    hip_drop_concern: float
    hip_drop_flag: float
    trunk_lean_concern: float
    trunk_lean_flag: float


class BodyTypeAdjustment(BaseModel):
    applies_to_sex: list[str] = Field(default_factory=list)
    applies_to_hypermobile: bool | None = None
    applies_to_age_range: list[str] = Field(default_factory=list)
    threshold_overrides: dict[str, float] = Field(default_factory=dict)


class BodyTypeAdjustmentsConfig(BaseModel):
    adjustments: list[BodyTypeAdjustment] = Field(default_factory=list)


class RuleConfig(BaseModel):
    rule_id: str
    chain: ChainName
    applies_to_movements: list[str] = Field(min_length=1)
    metric_key: Literal[
        "mean_knee_valgus_deg",
        "mean_trunk_lean_deg",
        "rom_deg",
        "peak_velocity_deg_per_s",
    ]
    aggregation: Literal["max", "min", "mean"]
    threshold_concern_ref: str
    threshold_flag_ref: str
    involved_joints: list[str] = Field(default_factory=list)
    narrative_template: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    evidence: EvidenceBlock
