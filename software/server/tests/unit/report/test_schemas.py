from auralink.pipeline.artifacts import SessionQualityReport
from auralink.report.schemas import (
    CrossMovementSection,
    MovementSection,
    Report,
    ReportMetadata,
    TemporalSection,
)


def _minimal_quality_report() -> SessionQualityReport:
    return SessionQualityReport(passed=True)


def test_temporal_section_instantiable():
    t = TemporalSection()
    assert t is not None


def test_cross_movement_section_instantiable():
    c = CrossMovementSection()
    assert c is not None


def test_report_round_trips():
    report = Report(
        metadata=ReportMetadata(session_id="s1", movement="overhead_squat"),
        movement_section=MovementSection(
            movement="overhead_squat",
            quality_report=_minimal_quality_report(),
        ),
        overall_narrative="Your movement shows a clean overall pattern.",
    )
    data = report.model_dump()
    restored = Report.model_validate(data)
    assert restored.metadata.session_id == "s1"
    assert restored.movement_section.movement == "overhead_squat"
