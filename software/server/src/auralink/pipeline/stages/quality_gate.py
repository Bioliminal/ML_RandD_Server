from auralink.pipeline.artifacts import QualityIssue, SessionQualityReport
from auralink.pipeline.stages.base import StageContext

MIN_FRAME_RATE = 20.0
MIN_AVG_VISIBILITY = 0.5
MIN_DURATION_S = 1.0
MAX_MISSING_LANDMARK_FRACTION = 0.05


def run_quality_gate(ctx: StageContext) -> SessionQualityReport:
    issues: list[QualityIssue] = []
    metrics: dict[str, float] = {}

    frame_rate = ctx.session.metadata.frame_rate
    metrics["frame_rate"] = frame_rate
    if frame_rate < MIN_FRAME_RATE:
        issues.append(
            QualityIssue(
                code="low_frame_rate",
                detail=f"{frame_rate:.1f} fps < {MIN_FRAME_RATE:.0f} fps minimum",
            )
        )

    return SessionQualityReport(passed=not issues, issues=issues, metrics=metrics)
