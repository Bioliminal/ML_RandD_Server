from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Landmark(BaseModel):
    """Single BlazePose landmark.

    Coordinates in normalized [0, 1] space (x, y) or input-relative (z).
    Visibility and presence are sigmoid'd values in [0, 1].
    """

    x: float
    y: float
    z: float
    visibility: float = Field(ge=0.0, le=1.0)
    presence: float = Field(ge=0.0, le=1.0)


# Alias for cross-repo and test compatibility.
PoseLandmark = Landmark


class Frame(BaseModel):
    """A single captured frame with 33 BlazePose landmarks in canonical order."""

    timestamp_ms: int = Field(ge=0)
    landmarks: list[Landmark]

    @field_validator("landmarks")
    @classmethod
    def require_33_landmarks(cls, v: list[Landmark]) -> list[Landmark]:
        if len(v) != 33:
            raise ValueError(f"expected 33 BlazePose landmarks, got {len(v)}")
        return v


MovementType = Literal[
    "overhead_squat",
    "single_leg_squat",
    "push_up",
    "rollup",
    "bicep_curl",
]


# sEMG encoding rationale (see research/synthesis/deep-read-semg-privacy-regulation-2026-04-15.md):
# raw sEMG is 90-97% re-identifiable from 0.8s of 4-channel data — functionally a biometric
# identifier. Feature extraction (RMS, MDF) on-device is the de-identification strategy of
# record. The encoding field lets the phone signal which representation it is sending; the
# server can reject raw uploads for jurisdictions or tiers that don't permit them.
sEMGEncoding = Literal["raw_mv", "normalized_0_1", "feature_rms", "feature_mdf"]


class sEMGSample(BaseModel):
    """Single sEMG reading. Schema is intentionally minimal pending gitlab
    ML_RandD_Server#13 (sEMG in SessionPayload decision); extra fields permitted
    via extra='allow' for forward compatibility with channel metadata, windowing,
    and feature-extraction parameters."""

    model_config = ConfigDict(extra="allow")

    channel: int = Field(ge=0)  # 0=biceps belly, 1=brachioradialis for demo
    timestamp_ms: int = Field(ge=0)  # MCU-clock timestamp
    value: float
    encoding: sEMGEncoding = "normalized_0_1"


# Consent metadata is LOAD-BEARING for any session that includes sEMG. Rationale
# (same research synthesis doc): Washington MHMDA requires opt-in collection consent
# with purpose; GDPR Article 9 requires explicit consent with no wellness exception;
# FTC HBNR covers unauthorized disclosures. Persisting jurisdiction + policy version
# + opt-in timestamp is the audit trail regulators will ask for. For sessions without
# sEMG, consent is not required at this layer (pose data is not consumer health data
# under MHMDA's definition).
ConsentJurisdiction = Literal["US-WA", "US-other", "EU", "other"]


class ConsentMetadata(BaseModel):
    """Session-level consent fingerprint. Required when emg is present; see
    Session.validate_consent_for_emg."""

    model_config = ConfigDict(extra="allow")

    consent_version: str  # policy hash or semver tag
    consent_jurisdiction: ConsentJurisdiction
    consent_timestamp: datetime
    data_retention_days: int | None = None  # None = retain per default policy


class SessionMetadata(BaseModel):
    movement: MovementType
    device: str
    model: str  # e.g. "mediapipe_blazepose_full"
    frame_rate: float = Field(gt=0)
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Session(BaseModel):
    metadata: SessionMetadata
    frames: list[Frame]
    emg: list[sEMGSample] | None = None  # optional pending ML_RandD_Server#13
    consent: ConsentMetadata | None = None

    @model_validator(mode="after")
    def validate_consent_for_emg(self) -> "Session":
        if self.emg and self.consent is None:
            raise ValueError(
                "consent metadata is required for any session that carries sEMG "
                "(MHMDA / GDPR Art 9 / FTC HBNR). See "
                "research/synthesis/deep-read-semg-privacy-regulation-2026-04-15.md"
            )
        return self


class SessionCreateResponse(BaseModel):
    session_id: str
    frames_received: int


# Report response schema. Fields below are the matrix §8.3 starting shape; they
# are NOT Aaron-approved as final. extra='allow' so #12 (bicep curl rule YAML +
# report narrative) can extend without a schema migration. The report endpoint
# itself is tracked separately in mobile-handover §1.
class RepScore(BaseModel):
    model_config = ConfigDict(extra="allow")

    rep_index: int = Field(ge=0)
    activation_delta: float | None = None  # sEMG pre/post-cue delta; None if no emg
    cue_fired: bool = False
    cue_verified: bool = False  # verify-delta ≥ 15% within 500 ms per cue spec
    elbow_angle_range: tuple[float, float] | None = None  # (min_deg, max_deg)


class SessionReport(BaseModel):
    model_config = ConfigDict(extra="allow")

    session_id: str
    reps: list[RepScore] = Field(default_factory=list)
    total_reps: int = 0
    chain_observations: list[str] = Field(default_factory=list)  # rule-engine output
    narrative: str = ""  # human-readable summary
