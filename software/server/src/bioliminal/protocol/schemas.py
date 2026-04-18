"""Protocol-level schemas — cross-session aggregation surface.

A protocol is a sequence of sessions (typically one per movement in the
four-movement screening). Aggregation is triggered by POST /protocols, which
loads per-session artifacts and calls protocol.aggregator.aggregate_protocol
to produce a ProtocolReport. Cross-session analysis is never a pipeline
stage; stages run per-session.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ProtocolRequest(BaseModel):
    """POST /protocols request body: a list of session IDs to aggregate."""

    session_ids: list[str] = Field(min_length=1, max_length=10)


class CrossMovementMetric(BaseModel):
    """One metric aggregated across the sessions in a protocol.

    values_by_session is keyed by session_id (preserving insertion order, which
    mirrors the session_ids order from the request). Session-keyed (not
    movement-keyed) so repeated same-movement sessions in a protocol don't
    overwrite each other.
    trend classifies the sequence: "improving" when lower-is-better metrics
    decrease across sessions or higher-is-better metrics increase; "declining"
    is the opposite; "stable" when neither.
    """

    metric_name: str
    values_by_session: dict[str, float]
    trend: Literal["improving", "stable", "declining"]


class ProtocolReport(BaseModel):
    """POST /protocols response body.

    per_session_movements maps session_id to movement string for easy
    presentation without re-reading session artifacts. fatigue_carryover_detected
    fires when cross-session mean NCC declines AND mean ROM deviation grows
    across >= 3 sessions.
    """

    session_ids: list[str]
    per_session_movements: dict[str, str]
    cross_movement_metrics: list[CrossMovementMetric] = Field(default_factory=list)
    fatigue_carryover_detected: bool
    summary_narrative: str
