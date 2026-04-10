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

    all_vis: list[float] = []
    for frame in ctx.session.frames:
        for lm in frame.landmarks:
            all_vis.append(lm.visibility)
    avg_vis = sum(all_vis) / len(all_vis) if all_vis else 0.0
    metrics["avg_visibility"] = avg_vis
    if avg_vis < MIN_AVG_VISIBILITY:
        issues.append(
            QualityIssue(
                code="low_visibility",
                detail=f"avg visibility {avg_vis:.2f} < {MIN_AVG_VISIBILITY:.2f}",
            )
        )

    return SessionQualityReport(passed=not issues, issues=issues, metrics=metrics)
