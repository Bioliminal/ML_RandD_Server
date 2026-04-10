import pytest

from auralink.pipeline.artifacts import QualityIssue, SessionQualityReport
from auralink.pipeline.errors import (
    PipelineError,
    QualityGateError,
    StageError,
)


def test_pipeline_error_is_base():
    err = PipelineError("oops")
    assert isinstance(err, Exception)
    assert str(err) == "oops"


def test_stage_error_carries_stage_name_and_detail():
    err = StageError(stage_name="angle_series", detail="NaN in input")
    assert err.stage_name == "angle_series"
    assert err.detail == "NaN in input"
    assert "angle_series" in str(err)
    assert isinstance(err, PipelineError)


def test_quality_gate_error_carries_report():
    report = SessionQualityReport(
        passed=False,
        issues=[QualityIssue(code="low_visibility", detail="avg 0.3 < 0.5")],
        metrics={"avg_visibility": 0.3},
    )
    err = QualityGateError(report=report)
    assert err.report is report
    assert err.report.issues[0].code == "low_visibility"
    assert isinstance(err, PipelineError)


def test_stage_error_raises_and_catches():
    with pytest.raises(PipelineError):
        raise StageError(stage_name="foo", detail="bar")
