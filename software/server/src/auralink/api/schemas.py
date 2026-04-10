from pydantic import BaseModel, Field, field_validator


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
