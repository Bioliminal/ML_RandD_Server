import pytest
from pydantic import ValidationError

from bioliminal.protocol.schemas import CrossMovementMetric, ProtocolReport, ProtocolRequest


def test_protocol_request_min_and_max_length():
    assert ProtocolRequest(session_ids=["a"]).session_ids == ["a"]
    with pytest.raises(ValidationError):
        ProtocolRequest(session_ids=[])
    with pytest.raises(ValidationError):
        ProtocolRequest(session_ids=[f"s{i}" for i in range(11)])


def test_protocol_report_and_cross_movement_metric_round_trip():
    metric = CrossMovementMetric(
        metric_name="mean_ncc",
        values_by_session={"s1": 0.93, "s2": 0.90},
        trend="declining",
    )
    report = ProtocolReport(
        session_ids=["s1", "s2"],
        per_session_movements={"s1": "overhead_squat", "s2": "single_leg_squat"},
        cross_movement_metrics=[metric],
        fatigue_carryover_detected=True,
        summary_narrative="Your movement shows a cumulative pattern across the session.",
    )
    data = report.model_dump(mode="json")
    restored = ProtocolReport.model_validate(data)
    assert restored.fatigue_carryover_detected is True
    assert restored.cross_movement_metrics[0].metric_name == "mean_ncc"
    assert restored.cross_movement_metrics[0].trend == "declining"
