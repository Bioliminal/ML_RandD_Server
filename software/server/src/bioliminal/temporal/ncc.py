"""Zero-mean normalized cross-correlation at zero lag.

After DTW has aligned two equal-length 1D signals, shape similarity collapses
to a single dot-product over de-meaned unit vectors. This is algebraically
identical to Pearson's r but is called NCC here for consistency with the
template-matching literature (OpenCV TM_CCOEFF_NORMED, scikit-image
match_template, Lewis 1995). Full rationale and edge-case handling in
docs/research/ncc-implementation-2026-04-14.md.
"""

import numpy as np


def ncc(x: np.ndarray | list[float], y: np.ndarray | list[float], eps: float = 1e-12) -> float:
    """Zero-mean normalized cross-correlation at zero lag.

    Inputs are 1D arrays of equal length (post-DTW alignment).
    Returns a score in [-1.0, 1.0]. 1.0 means identical shape (up to
    linear scale and offset); 0.0 means uncorrelated; -1.0 means inverted.

    Edge cases:
      - Raises ValueError on length mismatch or non-1D input.
      - Returns NaN if either signal has (near-)zero variance, since
        shape comparison is undefined for a constant signal.
      - NaNs in inputs propagate to a NaN output; callers must mask or
        interpolate upstream.
    """
    xa = np.asarray(x, dtype=np.float64)
    ya = np.asarray(y, dtype=np.float64)
    if xa.ndim != 1 or ya.ndim != 1:
        raise ValueError("ncc expects 1D arrays")
    if xa.shape != ya.shape:
        raise ValueError(f"length mismatch: {xa.shape} vs {ya.shape}")
    if not (np.all(np.isfinite(xa)) and np.all(np.isfinite(ya))):
        return float("nan")
    xc = xa - xa.mean()
    yc = ya - ya.mean()
    denom = float(np.sqrt(np.dot(xc, xc) * np.dot(yc, yc)))
    if denom < eps:
        return float("nan")
    return float(np.dot(xc, yc) / denom)
