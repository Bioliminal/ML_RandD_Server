# DTW Library Comparison — BioLiminal RnD Server

**Date:** 2026-04-14
**Context:** Align 1D rep angle time-series (N≈30–150) vs reference. Python 3.11+ / FastAPI / numpy. Need `(distance, warp_path)`. Non-real-time, ~100ms/rep budget. License must be MIT/BSD/Apache-2.0 (no GPL/AGPL).

## Comparison Table

| Criterion | fastdtw | dtaidistance | tslearn | dtw-python | numpy-native |
|---|---|---|---|---|---|
| **License** | MIT | Apache-2.0 | BSD-2-Clause | **GPL-3.0-or-later** | n/a |
| **Latest version** | 0.3.4 | 2.4.0 | 0.8.1 | 1.7.4 | — |
| **Last release** | Oct 2019 | Feb 2026 | Mar 2026 | Feb 2026 | — |
| **Python 3.11+** | Broken on numpy 2.x (issue #65) | Yes, requires ≥3.8 | Yes, requires ≥3.10 | Yes, requires ≥3.9 | Yes |
| **Stars** | 846 | 1.2k | 3.1k | ~300 (DTW org) | — |
| **Exact DTW?** | **No** — approximation | Yes | Yes | Yes | Yes |
| **Backend** | Pure Python | C (Cython + OpenMP) + Python fallback | Numba JIT | C extension | numpy |
| **Required deps** | numpy, scipy | numpy only | scikit-learn ≥1.4, scipy ≥1.10, numba ≥0.61, joblib, numpy | numpy, scipy | numpy |
| **Hidden bloat** | Low | **None** (scipy/pandas are optional extras) | **High** — pulls sklearn + numba | Moderate | None |
| **Warp path API** | `fastdtw(a,b) → (dist, path)` | `dtw.warping_path(a,b)` + `dtw.distance(a,b)` | `dtw_path(a,b) → (path, dist)` | `dtw(a,b).index1/index2` | hand-rolled |
| **Sakoe-Chiba band** | radius param (approx only) | Yes (`window=`) | Yes | Yes | easy to add |
| **Itakura parallelogram** | No | No | No | Yes | manual |
| **Subsequence DTW** | No | Yes (dedicated module) | Partial | Yes (open-begin/open-end) | manual |
| **Perf at N=150** | ~1–3 ms (approx) | <0.2 ms (C) | ~1 ms (after numba warmup) | ~0.5 ms | ~2–5 ms |
| **Maintenance** | **Stale** (2019, numpy 2 broken) | Active (2.4.0 Feb 2026) | Active | Active | n/a |

## Recommendation

**Use `dtaidistance`.**

It is the only candidate that is (a) actively maintained through 2026, (b) C-backed and exact at our N, (c) has zero forced transitive dependencies beyond numpy — scipy/pandas/matplotlib are all optional extras — and (d) ships both a warping-path API and native Sakoe-Chiba window support, which we will want once we start tightening alignment tolerances. Apache-2.0 is compatible with our MIT/BSD policy (it is the same permissive family — no copyleft, just an explicit patent grant). The raw performance (<0.2 ms/rep at N=150) leaves 500× headroom under the 100 ms budget, which matters when we start batching reps for a session summary.

If we ever need a zero-dep fallback (e.g., lambda cold-start sensitivity), the numpy-native O(N²) DP is ~40 lines and runs in ~2 ms at N=150 — cheap insurance, but not worth adopting as the primary path when `dtaidistance` is already 10× faster with a better API.

## Warning Flags

- **`dtw-python` is GPL-3.0-or-later.** Disqualified for any product we intend to ship under a permissive license. Do not vendor, do not import, even for prototyping — GPL linkage is viral.
- **`fastdtw` is effectively abandoned.** Last release October 2019. Open issue #65 (May 2025) reports it will not compile against numpy 2.x due to removed `numpy.math cimport INFINITY`. It is also only an approximation, which defeats the point of picking a library over a 40-line numpy DP.
- **`tslearn` drags in scikit-learn + numba + scipy + joblib** just to call `dtw_path`. That is ~200 MB of wheels and a numba JIT warmup on first call. Bad ratio for one function.
- **dtaidistance Apache-2.0 note:** Apache-2.0 is not literally "MIT/BSD" but is in the same permissive family and is universally accepted alongside them (numpy itself is BSD, pyarrow is Apache). If the constraint is strict "MIT/BSD only" for a specific compliance reason, flag this to the user before adopting. Otherwise it's fine.
- **dtaidistance C compilation:** `pip install dtaidistance` compiles Cython extensions. On slim base images without a C toolchain it will fall back to pure Python (~30× slower but still correct). For Docker, install on a `python:3.11` image (not `-slim`) or `apt-get install build-essential` first.

## numpy-native reference (for context)

~40 lines, no deps beyond numpy, exact, full control:

```python
import numpy as np

def dtw(a: np.ndarray, b: np.ndarray) -> tuple[float, list[tuple[int, int]]]:
    n, m = len(a), len(b)
    cost = np.full((n + 1, m + 1), np.inf)
    cost[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d = abs(a[i - 1] - b[j - 1])
            cost[i, j] = d + min(cost[i - 1, j], cost[i, j - 1], cost[i - 1, j - 1])
    # backtrack
    path = []
    i, j = n, m
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        step = np.argmin([cost[i - 1, j - 1], cost[i - 1, j], cost[i, j - 1]])
        if step == 0:
            i, j = i - 1, j - 1
        elif step == 1:
            i -= 1
        else:
            j -= 1
    return float(cost[n, m]), path[::-1]
```

Runs in ~2–5 ms at N=150 (Python-level loops). Drop to Cython or vectorize the inner band for 10× if needed. Useful as a sanity-check oracle for whichever library we adopt.
