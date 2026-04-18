# Normalized Cross-Correlation (NCC) Implementation

**Status:** current
**Created:** 2026-04-14
**Updated:** 2026-04-14
**Owner:** AaronCarney

**Date:** 2026-04-14
**Context:** BioLiminal capstone — similarity scoring of DTW-aligned 1D joint-angle rep pairs (30–150 samples) to feed a trend-detection module.

## 1. Canonical Formula

The version used in computer vision template matching and signal processing is the **zero-mean (zero-normalized) cross-correlation coefficient**, often called NCC or ZNCC. For two equal-length sequences `x` and `y` of length `N`:

```
           Σ (x_i - x̄)(y_i - ȳ)
NCC = ───────────────────────────────────────
      sqrt( Σ(x_i - x̄)² · Σ(y_i - ȳ)² )
```

Properties:
- Bounded in **[-1, 1]** (1 = identical shape, 0 = uncorrelated, -1 = inverted)
- Invariant to linear scaling and additive offset of either signal (only *shape* matters)
- Equivalent to the Pearson correlation coefficient at lag zero when both signals have the same length

This is the form used by OpenCV's `TM_CCOEFF_NORMED`, scikit-image's `match_template`, and the PLOS One FFT-NCC paper (Lewis 1995 / Subramaniam 2018). It is the right default for post-DTW rep comparison because the alignment step has already removed timing differences, so only zero-lag shape matters.

## 2. NumPy Reference Implementation

Since DTW has already aligned the two reps to equal length, we only need the zero-lag case — which is a one-liner over de-meaned, unit-variance vectors.

```python
import numpy as np

def ncc(x: np.ndarray, y: np.ndarray, eps: float = 1e-12) -> float:
    """
    Zero-mean normalized cross-correlation at zero lag.

    Inputs are 1D arrays of equal length (post-DTW alignment).
    Returns a score in [-1.0, 1.0]. 1.0 means identical shape (up to
    linear scale and offset); 0.0 means uncorrelated.

    Edge cases:
      - Raises ValueError on length mismatch or non-1D input.
      - Returns NaN if either signal has (near-)zero variance, since
        the shape comparison is undefined for a constant signal.
      - NaNs in inputs propagate to a NaN output; callers should mask
        or interpolate upstream.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if x.ndim != 1 or y.ndim != 1:
        raise ValueError("ncc expects 1D arrays")
    if x.shape != y.shape:
        raise ValueError(f"length mismatch: {x.shape} vs {y.shape}")
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return float("nan")
    xc = x - x.mean()
    yc = y - y.mean()
    denom = np.sqrt(np.dot(xc, xc) * np.dot(yc, yc))
    if denom < eps:
        return float("nan")
    return float(np.dot(xc, yc) / denom)
```

Notes on the edge cases:
- **Length mismatch:** raised as `ValueError` — should never happen post-DTW, so treat as a bug signal rather than silently padding.
- **Zero variance:** a flat signal has no shape; returning `NaN` forces the caller to handle it (usually: drop the rep, or flag as "no movement detected" upstream). Returning 0 would be misleading.
- **NaN inputs:** propagate rather than silently fill — upstream sensor dropouts should be caught before scoring.
- `float64` cast guards against integer input and reduces catastrophic cancellation on near-flat signals.

## 3. scipy Alternative — Not Worth the Dep

`scipy.signal.correlate(x, y, mode='same', method='auto')` computes the **unnormalized** cross-correlation function across all lags, using direct sums for small inputs and FFT for large ones. To get an NCC score from it you still have to:

1. De-mean both signals
2. Divide by `sqrt(Σxc² · Σyc²)` manually
3. Pick the zero-lag entry (or argmax, but DTW already handled lag)

So scipy gives you nothing numpy can't do in one line for the zero-lag case. The FFT speedup only matters for full lag-sweep correlations on signals ≳ 500–1000 samples; our reps are 30–150 samples where direct sums win regardless. scipy.signal's own `method='auto'` heuristic would pick `'direct'` at our scale.

**Recommendation:** stick with numpy. The only reason to add scipy would be if we later need full-lag NCC for pre-DTW rough alignment or template search, at which point `scipy.signal.correlate` with manual normalization is the right call.

Docs: [scipy.signal.correlate](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.correlate.html), [numpy.correlate](https://numpy.org/doc/stable/reference/generated/numpy.correlate.html).

## 4. Threshold Guidance from the Literature

Direct NCC thresholds for joint-angle rep comparison are sparse — the biomechanics community mostly reports **Coefficient of Multiple Correlation (CMC)** and **Pearson r** on gait waveforms, which are mathematically equivalent to NCC at zero lag for equal-length signals. Translated to our setting:

| Source / context | Metric | "Good" band | Notes |
|---|---|---|---|
| Kavanagh et al., gait EMG cross-correlation | XCC | 0.85–0.95 intra-subject, comfortable walking | Cross-trial repeatability in the same subject |
| Ferrari et al., CMC for gait kinematics | CMC | >0.90 excellent, 0.75–0.90 good, <0.75 poor | Widely cited in gait labs |
| IMU vs photogrammetry validation (Frontiers Bioeng 2024) | Pearson r | r > 0.75 = sufficient agreement | Sagittal hip/knee/ankle |
| Gait waveform similarity review (Iosa 2014) | Pearson / CMC | 0.8–0.9 = acceptable, >0.9 = strong | Clinical gait |

Same-subject, same-exercise NCCs typically cluster in the **0.85–0.95** range; dropping under **0.75** is a reliable signal that the movement has meaningfully changed (form breakdown, substitution, wrong exercise). Our proposed bands are consistent with this literature:

- **≥ 0.95** clean rep (matches best intra-subject repeatability)
- **0.75–0.95** concern — flag for trend watch
- **< 0.75** flag — likely different movement or significant form change

Two caveats for tuning:
1. **Axis matters.** Sagittal joints correlate higher than frontal/transverse. Expect thresholds to need per-joint calibration.
2. **NCC ignores amplitude.** A rep with half the range of motion but the same shape still scores near 1.0. We need a separate amplitude/ROM check alongside NCC — don't rely on NCC alone for "same movement."

## 5. NCC vs Pearson — Same Thing At Zero Lag

For two signals of equal length compared at zero lag (our case, after DTW), **NCC and Pearson's r are algebraically identical**. Both:
- Subtract the mean from each signal
- Divide by each signal's standard deviation (equivalently, the L2 norm of the de-meaned vector)
- Take the dot product

Where they diverge is intent:
- **Pearson's r** is a single scalar — "how linearly related are these two samples?"
- **Cross-correlation** is a *function* of lag — `xcorr(x, y)[k]` measures linear relation when `y` is shifted by `k`. NCC is cross-correlation normalized so each lag value is bounded in [-1, 1]; Pearson's r is the special case `k=0`.

When to pick which:
- **Pearson / zero-lag NCC:** signals already time-aligned (our case post-DTW). Use it; simpler, faster, identical answer.
- **Full-lag NCC:** signals not aligned, or you want to *find* the best lag (pre-DTW template search, event detection). Report `max(ncc(lag))` and the lag that achieved it.

For BioLiminal's rep scoring: call it NCC in the code for consistency with the vision literature and template-matching pipelines, but know that what we're computing is mathematically Pearson r on the de-meaned vectors. The implementation above reflects that — it's the zero-lag form, one dot product and two norms, and nothing more is needed.

## Sources

- [Cross-correlation — Wikipedia](https://en.wikipedia.org/wiki/Cross-correlation)
- [Pearson correlation coefficient — Wikipedia](https://en.wikipedia.org/wiki/Pearson_correlation_coefficient)
- [Computation of the normalized cross-correlation by FFT — PLOS One 2018](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0203434)
- [scipy.signal.correlate docs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.correlate.html)
- [numpy.correlate docs](https://numpy.org/doc/stable/reference/generated/numpy.correlate.html)
- [Assessment of Waveform Similarity in Clinical Gait Data — Iosa 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4122015/)
- [Evaluating CMC for kinematic gait data — Ferrari et al.](https://pubmed.ncbi.nlm.nih.gov/22673759/)
- [IMU vs photogrammetry gait validation — Frontiers Bioeng 2024](https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2024.1449698/full)
- [How to choose similarity indices for gait kinematics — Tandfonline](https://www.tandfonline.com/doi/full/10.1080/23335432.2018.1426496)
