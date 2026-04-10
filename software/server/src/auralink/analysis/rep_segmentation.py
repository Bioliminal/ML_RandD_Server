"""Rep segmentation from a scalar joint-angle time series.

A rep is bounded by two local maxima (near the "top" of the movement)
with a local minimum (the "bottom") between them. We identify reps by:

1. Find all local maxima and local minima in the angle series.
2. For each adjacent (max, min, max) triple, compute amplitude (max - min).
3. Keep triples whose amplitude exceeds min_amplitude (filters noise).

This is sufficient for squats, lunges, push-ups — movements with a clear
flexion->extension cycle around a single joint angle. Continuous movements
like rollup use phase_segmentation instead (not in this scaffold).
"""

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class RepBoundary:
    start_index: int
    bottom_index: int
    end_index: int
    start_angle: float
    bottom_angle: float
    end_angle: float


def _find_local_extrema(
    series: Sequence[float],
) -> tuple[list[int], list[int]]:
    """Return (maxima_indices, minima_indices).

    Handles plateaus: each run of equal values is treated as a single
    extremum anchored at its leftmost index. Endpoints count as extrema
    based on the direction of the adjacent non-equal value.
    """
    maxima: list[int] = []
    minima: list[int] = []
    n = len(series)
    if n < 3:
        return maxima, minima

    i = 0
    while i < n:
        j = i
        while j + 1 < n and series[j + 1] == series[i]:
            j += 1

        prev_val = series[i - 1] if i > 0 else None
        next_val = series[j + 1] if j + 1 < n else None
        val = series[i]

        if prev_val is None and next_val is not None:
            if val >= next_val:
                maxima.append(i)
            else:
                minima.append(i)
        elif next_val is None and prev_val is not None:
            if val >= prev_val:
                maxima.append(i)
            else:
                minima.append(i)
        elif prev_val is not None and next_val is not None:
            if val > prev_val and val > next_val:
                maxima.append(i)
            elif val < prev_val and val < next_val:
                minima.append(i)

        i = j + 1

    return maxima, minima


def segment_reps(
    angle_series: Sequence[float],
    min_amplitude: float = 30.0,
) -> list[RepBoundary]:
    """Segment a scalar angle series into rep boundaries.

    Args:
        angle_series: Sequence of joint angles in degrees over time.
        min_amplitude: Minimum amplitude (max - min) to qualify as a rep.

    Returns:
        List of RepBoundary objects in temporal order.
    """
    maxima, minima = _find_local_extrema(angle_series)
    if not maxima or not minima:
        return []

    events = sorted(
        [(i, "max") for i in maxima] + [(i, "min") for i in minima]
    )

    reps: list[RepBoundary] = []
    for j in range(len(events) - 2):
        e1, e2, e3 = events[j], events[j + 1], events[j + 2]
        if e1[1] == "max" and e2[1] == "min" and e3[1] == "max":
            start, bottom, end = e1[0], e2[0], e3[0]
            amplitude = max(angle_series[start], angle_series[end]) - angle_series[bottom]
            if amplitude >= min_amplitude:
                reps.append(
                    RepBoundary(
                        start_index=start,
                        bottom_index=bottom,
                        end_index=end,
                        start_angle=angle_series[start],
                        bottom_angle=angle_series[bottom],
                        end_angle=angle_series[end],
                    )
                )
    return reps
