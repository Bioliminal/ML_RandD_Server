"""Dynamic Time Warping wrapper over dtaidistance.

Provides a single call-site for aligning two 1D joint-angle sequences with a
Sakoe-Chiba band constraint. Returns both the DTW distance and the explicit
warping path so downstream callers can re-index either sequence onto the
alignment before scoring shape similarity with NCC.

dtaidistance is Apache-2.0, C-backed, numpy-only; see
docs/research/dtw-library-comparison-2026-04-14.md.
"""

from dtaidistance import dtw as _dtai_dtw
from pydantic import BaseModel, Field


class DTWResult(BaseModel):
    """Thin pydantic wrapper so callers can round-trip DTW output through JSON."""

    distance: float = Field(ge=0.0)
    path: list[tuple[int, int]]
    window: int | None = None


def _sakoe_chiba_window(len_a: int, len_b: int, radius_fraction: float = 0.1) -> int:
    """Return the Sakoe-Chiba radius as an integer number of frames.

    Scales with the longer of the two sequences. Floor of 1 so the constraint
    is never degenerate. Paper omitted this entirely; we restore it because
    unconstrained DTW is known to produce pathological paths.
    """
    # window=1 in dtaidistance means |i-j|<1, i.e. diagonal-only (Euclidean).
    # Minimum of 2 ensures the band actually allows warping.
    return max(2, int(radius_fraction * max(len_a, len_b)))


def run_dtw(
    a: list[float],
    b: list[float],
    radius_fraction: float = 0.1,
) -> DTWResult:
    """Align two 1D sequences via DTW under a Sakoe-Chiba band.

    Parameters
    ----------
    a, b : list[float]
        Sequences to align. May be of different length; DTW handles this.
    radius_fraction : float
        Sakoe-Chiba band radius as a fraction of the longer sequence length.
        Default 0.1 matches the biomechanics literature (Ferrari et al.,
        Keogh et al.). Must be in (0, 1].

    Returns
    -------
    DTWResult
        distance : float   -- DTW alignment cost
        path : list[(i,j)] -- (index_in_a, index_in_b) pairs forming the
                              optimal warping path
        window : int       -- the concrete Sakoe-Chiba radius applied
    """
    if not a or not b:
        raise ValueError("run_dtw requires non-empty sequences")
    if not (0.0 < radius_fraction <= 1.0):
        raise ValueError(f"radius_fraction must be in (0, 1]; got {radius_fraction}")

    window = _sakoe_chiba_window(len(a), len(b), radius_fraction)
    distance = float(_dtai_dtw.distance(a, b, window=window))
    raw_path = _dtai_dtw.warping_path(a, b, window=window)
    path = [(int(i), int(j)) for i, j in raw_path]
    return DTWResult(distance=distance, path=path, window=window)
