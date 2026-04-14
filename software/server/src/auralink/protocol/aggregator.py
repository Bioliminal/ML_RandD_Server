"""Cross-session protocol aggregator.

Consumes per-session Reports, reads their movement_temporal_summary fields,
and produces a ProtocolReport with cross-movement metrics and a fatigue
carryover flag. Endpoint-only — never runs as a pipeline stage.

Fatigue carryover is a joint condition: the cross-session mean NCC must
trend downward AND the cross-session mean ROM deviation must grow in
magnitude across >= 3 sessions. Fewer than 3 sessions cannot trigger
carryover (insufficient trend signal).
"""

from __future__ import annotations

import numpy as np

from auralink.protocol.schemas import CrossMovementMetric, ProtocolReport
from auralink.report.schemas import Report

_MIN_SESSIONS_FOR_CARRYOVER = 3


def _slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    xs = np.arange(len(values), dtype=np.float64)
    ys = np.asarray(values, dtype=np.float64)
    slope, _intercept = np.polyfit(xs, ys, 1)
    return float(slope)


def _trend(values: list[float], higher_is_better: bool) -> str:
    if len(values) < 2:
        return "stable"
    s = _slope(values)
    eps = 1e-9
    if higher_is_better:
        if s > eps:
            return "improving"
        if s < -eps:
            return "declining"
        return "stable"
    if s < -eps:
        return "improving"
    if s > eps:
        return "declining"
    return "stable"


def aggregate_protocol(reports: list[Report], session_ids: list[str]) -> ProtocolReport:
    """Aggregate per-session reports into a ProtocolReport.

    session_ids must be in the same order as reports. Sessions whose reports
    have no movement_temporal_summary (e.g., push_up) are skipped in the
    metric computation but still recorded in per_session_movements.
    """
    if len(reports) != len(session_ids):
        raise ValueError(
            f"reports/session_ids length mismatch: {len(reports)} vs {len(session_ids)}"
        )

    per_session_movements: dict[str, str] = {}
    # Keyed by session_id (preserving order) so same-movement repeated sessions
    # don't overwrite each other. The time-series order is session_ids order.
    mean_ncc_by_session: dict[str, float] = {}
    mean_rom_dev_by_session: dict[str, float] = {}

    for session_id, report in zip(session_ids, reports, strict=True):
        per_session_movements[session_id] = report.movement_section.movement
        summary = report.movement_section.movement_temporal_summary
        if summary is None:
            continue
        mean_ncc_by_session[session_id] = summary.mean_ncc
        mean_rom_dev_by_session[session_id] = summary.mean_rom_deviation_pct

    metrics: list[CrossMovementMetric] = []
    if mean_ncc_by_session:
        metrics.append(
            CrossMovementMetric(
                metric_name="mean_ncc",
                values_by_movement=dict(mean_ncc_by_session),
                trend=_trend(list(mean_ncc_by_session.values()), higher_is_better=True),
            )
        )
    if mean_rom_dev_by_session:
        metrics.append(
            CrossMovementMetric(
                metric_name="mean_rom_deviation_pct",
                values_by_movement=dict(mean_rom_dev_by_session),
                trend=_trend(
                    [abs(v) for v in mean_rom_dev_by_session.values()],
                    higher_is_better=False,
                ),
            )
        )

    carryover = False
    if len(mean_ncc_by_session) >= _MIN_SESSIONS_FOR_CARRYOVER:
        ncc_values = list(mean_ncc_by_session.values())
        rom_abs_values = [abs(v) for v in mean_rom_dev_by_session.values()]
        ncc_slope = _slope(ncc_values)
        rom_slope = _slope(rom_abs_values)
        # Belt-and-braces: with only 3-4 sessions a polyfit slope is very
        # sensitive to a single outlier. Require BOTH a negative NCC slope
        # AND an endpoint drop (last session NCC meaningfully below first)
        # to reduce false-positive carryover claims. Same for ROM growth.
        ncc_endpoint_drop = ncc_values[-1] < ncc_values[0] - 1e-6
        rom_endpoint_growth = rom_abs_values[-1] > rom_abs_values[0] + 1e-6
        carryover = (
            ncc_slope < 0.0 and rom_slope > 0.0 and ncc_endpoint_drop and rom_endpoint_growth
        )

    if carryover:
        narrative = (
            "Your movement shows a cumulative pattern across the protocol — "
            "shape similarity trended down and range of motion varied more over time. "
            "This is a good opportunity to explore pacing and recovery between sets."
        )
    elif metrics:
        narrative = (
            "Your movement shows a stable pattern across the protocol — "
            "no notable cross-movement drift detected."
        )
    else:
        narrative = (
            "Not enough temporal data across these sessions to summarize a cross-movement pattern."
        )

    return ProtocolReport(
        session_ids=list(session_ids),
        per_session_movements=per_session_movements,
        cross_movement_metrics=metrics,
        fatigue_carryover_detected=carryover,
        summary_narrative=narrative,
    )
