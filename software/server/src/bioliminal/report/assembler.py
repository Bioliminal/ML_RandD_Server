from bioliminal.api.schemas import RepScore
from bioliminal.pipeline.artifacts import (
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    PipelineArtifacts,
    RepBoundaries,
)
from bioliminal.report.schemas import (
    MovementSection,
    Report,
    ReportMetadata,
    TemporalSection,
)


def assemble_rep_scores(
    *,
    per_rep: PerRepMetrics,
    normalized: NormalizedAngleTimeSeries,
    boundaries: RepBoundaries,
    movement_type: str,
) -> list[RepScore]:
    elbow_series = (
        normalized.angles.get("left_elbow_flexion", [])
        if movement_type == "bicep_curl"
        else []
    )
    primary_boundaries = boundaries.by_angle.get(per_rep.primary_angle, [])
    out: list[RepScore] = []
    for idx, rm in enumerate(per_rep.reps):
        elbow_range: tuple[float, float] | None = None
        if movement_type == "bicep_curl" and idx < len(primary_boundaries) and elbow_series:
            rep = primary_boundaries[idx]
            window = elbow_series[rep.start_index : rep.end_index + 1]
            if window:
                elbow_range = (float(min(window)), float(max(window)))
        out.append(RepScore(rep_index=rm.rep_index, elbow_angle_range=elbow_range))
    return out


def _build_overall_narrative(section: MovementSection) -> str:
    if not section.quality_report.passed:
        return (
            "We could not generate a complete movement read from this session. "
            "See the quality report for details on what to adjust for the next capture."
        )
    obs = section.chain_observations
    if not obs:
        return "Your movement shows a clean overall pattern — no notable compensations detected."
    flagged = [o for o in obs if o.severity.value == "flag"]
    concern = [o for o in obs if o.severity.value == "concern"]
    parts: list[str] = []
    if flagged:
        parts.append(
            f"Your movement shows {len(flagged)} notable pattern(s) worth exploring further."
        )
    if concern:
        parts.append(
            f"There are {len(concern)} area(s) of early-stage variation in your body connections."
        )
    return " ".join(parts)


def assemble_report(
    artifacts: PipelineArtifacts,
    session_id: str,
    movement: str,
    captured_at_ms: int | None = None,
) -> Report:
    movement_section = MovementSection(
        movement=movement,
        quality_report=artifacts.quality_report,
        angle_series=artifacts.angle_series,
        normalized_angle_series=artifacts.normalized_angle_series,
        rep_boundaries=artifacts.rep_boundaries,
        per_rep_metrics=artifacts.per_rep_metrics,
        within_movement_trend=artifacts.within_movement_trend,
        lift_result=artifacts.lift_result,
        skeleton_result=artifacts.skeleton_result,
        phase_boundaries=artifacts.phase_boundaries,
        chain_observations=artifacts.chain_observations or [],
        movement_temporal_summary=artifacts.movement_temporal_summary,
    )
    temporal_section: TemporalSection | None = None
    if artifacts.movement_temporal_summary is not None:
        temporal_section = TemporalSection(
            movement_temporal_summary=artifacts.movement_temporal_summary,
        )
    return Report(
        metadata=ReportMetadata(
            session_id=session_id,
            movement=movement,
            captured_at_ms=captured_at_ms,
        ),
        movement_section=movement_section,
        overall_narrative=_build_overall_narrative(movement_section),
        temporal_section=temporal_section,
        cross_movement_section=None,
    )
