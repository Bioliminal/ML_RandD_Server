from enum import StrEnum

from pydantic import BaseModel, Field

from bioliminal.reasoning.chains import ChainName


class ObservationSeverity(StrEnum):
    INFO = "info"
    CONCERN = "concern"
    FLAG = "flag"


class ChainObservation(BaseModel):
    chain: ChainName
    severity: ObservationSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    trigger_rule: str
    involved_joints: list[str] = Field(default_factory=list)
    evidence: dict[str, float] = Field(default_factory=dict)
    narrative: str
