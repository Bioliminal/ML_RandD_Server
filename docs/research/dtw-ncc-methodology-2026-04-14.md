# DTW + NCC Methodology — Source Paper Analysis

**Date:** 2026-04-14
**Target paper:** Scientific Reports 2025, DOI `10.1038/s41598-025-29062-7`
**Status:** Paper found

## Citation

> "A real time action scoring system for movement analysis and feedback in physical therapy using human pose estimation"
> *Scientific Reports*, 2025. DOI: 10.1038/s41598-025-29062-7
> Authors affiliated with Augmented Vision Ltd.
> Open access: https://www.nature.com/articles/s41598-025-29062-7
> PMC mirror: https://pmc.ncbi.nlm.nih.gov/articles/PMC12749503/

---

## 1. Signals

- **Backbone:** MediaPipe pose, **2D only** (normalized `x,y` relative to frame dimensions). **No 3D, no depth.**
- **Primary signal:** **joint-angle time-series** computed from three-point keypoint triplets (e.g., shoulder–elbow–wrist for elbow flexion) using the **cosine rule** (Eq. 5). They do *not* feed raw landmarks into DTW/NCC.
- **Joints tracked:** shoulders, elbows, hips (sagittal + frontal), knees — roughly 10 joint channels. Analysis is explicitly focused on **sagittal-plane flexion/extension**.
- **Derived features:** ROM, angular velocity (deg/s), peak/trough positions on the angle trace. They use the peak/trough detection to segment reps.
- A "fixed bounding-box" stabilization step is added to combat MediaPipe tracking jitter before angle computation.

## 2. DTW Setup

- **What is compared:** each user repetition's joint-angle trajectory is aligned to a **reference repetition** (clinician demo), after rep-segmentation via peak/trough detection.
- **Implementation:** `dtaidistance` Python library.
- **Cost function:** standard DTW with **Euclidean** pointwise distance on scalar joint-angle samples (Eq. 13): `DTW(Q,C) = sqrt(sum distance(Q[i], C[j]))` where `Q` = patient sequence, `C` = clinician demonstration.
- **Warping window:** **none specified.** No Sakoe-Chiba band, Itakura parallelogram, or other constraint reported. This is a notable omission for real-time use.
- **Scope:** per-joint, per-rep. No joint-wise weighting documented.

## 3. NCC Setup

Formulas (Eq. 14–16):

```
r(tau) = sum_t [ (X[t] - mu_X) * (Y[t+tau] - mu_Y) ] / (sigma_X * sigma_Y)
S      = (1/N) * sum_i  max_tau r_i(tau)
```

- **Applied to DTW-warped signals**, not raw signals and not the DTW cost matrix. The DTW alignment first puts the two sequences in phase; NCC then measures shape similarity on the aligned traces.
- **Reported "good match" region:** average NCC **> 0.85** is called "a high level of correlation." They do **not** publish a hard pass/fail threshold — NCC is reported as a continuous quality score.
- Range interpretation is standard: −1 (anti-correlated) to +1 (identical shape), 0 = no relationship.

## 4. Within-Movement Fatigue / Compensation Drift

**Not modeled.** The paper reports per-rep ROM and velocity with standard deviations (Table 8) and characterizes these as "intra-trial fluctuations," but:

- No monotonic drift test across reps.
- No explicit fatigue model.
- No compensation-pattern detection (e.g., trunk lean creep on squats).

This is a gap we will have to design ourselves — the paper does not give us a prior art methodology to copy.

## 5. Cross-Movement Analysis

**Not supported.** Each exercise has its own reference demo and is scored independently. There is no carry-over analysis from e.g. overhead squat → single-leg squat → push-up. The system is exercise-specific by construction.

Again: another gap we own.

## 6. Reference Rep Construction

- **Source:** "professionally filmed demonstrations by the research team" — physiotherapists and rehab specialists performed each exercise as the reference.
- **Aggregation method:** **unclear.** The paper does not specify whether they use a single best-quality demo rep, average multiple clinician reps, or build a DBA (DTW-barycenter-averaged) template. They describe it as "a clinically validated reference rather than an independent ground truth."
- Practical read: treat it as a **single expert demonstration per exercise**, with aggregation strategy unspecified and therefore open to us.

## 7. Validation

- **Subjects:** N = **6 healthy adults**, 20–35 yr, all members of the Augmented Vision Ltd research team. Small, non-blinded, non-clinical population.
- **Ground truth labels:**
  - **Keypoint accuracy:** ~1000 manually annotated keypoints, ~8–9% deviation (Table 2).
  - **Joint angles:** clinicians frame-by-frame with goniometric anatomical landmarks.
  - **Rep counts:** manual count by research team; error formula `Error(%) = 100 * |detected - actual| / actual` (Eq. 17).
- **Reported metrics:**
  - ROM deviation from clinicians: **1.6–3.2%** (Table 10).
  - Angular velocity error: ~**0.1 deg/s** average.
  - Joint-angle MAE reported per joint.
- **Framing:** the paper is explicit that the benchmark is "clinically validated reference" alignment, not an independent ground-truth biomechanical model. There is **no gold-standard mocap (Vicon/OptiTrack) comparison**, no IMU cross-validation, and no physiotherapist blind-rating study.

---

## Implications for our L2 Plan 3

1. **Signals — adopt their choice, upgrade where cheap.** Computing DTW/NCC on joint-angle traces (not raw landmarks) is the right move: it's rotation/translation/scale invariant and dimensionally compact. But we should work in **3D** where our backbone permits (MediaPipe World Landmarks, MoveNet MultiPose + lift, or BlazePose GHUM) — the 2D limitation is a MediaPipe-era legacy, not a methodological requirement.

2. **DTW cost function — add a Sakoe-Chiba band.** The paper omits warping constraints. For real-time rep scoring at 30 Hz we should cap warping at a physiologically plausible window (e.g., r = 10–15% of rep length) to prevent pathological alignments where the user "warps into" the reference during a compensation, and also to cut `O(n^2)` to `O(n*w)`. Euclidean pointwise cost is fine to start; we can revisit with angle-wrap-aware or per-joint-weighted costs later.

3. **NCC threshold calibration.** The paper's 0.85 anchor is a descriptive observation on N=6 healthy subjects, not a validated clinical cutoff. We should treat NCC as a continuous score and **calibrate threshold(s) from our own eval set** across user skill levels — "good rep" vs "compensated rep" vs "different-exercise-entirely" as three-class labeling.

4. **Fatigue / drift detection — we own this.** The paper gives us no methodology. Design options to explore:
   - Monotone regression of NCC(rep_i, reference) across reps in a set → slope < 0 indicates drift.
   - Rolling per-joint ROM delta vs. rep 1 baseline.
   - DTW cost trend across reps (rising cost = increasing deviation).
   - Dedicated compensation features (e.g., hip-shift asymmetry on squats, lumbar flexion on deadlifts) as side-channel signals complementing the global NCC score.

5. **Cross-movement analysis — we own this too.** The paper's exercise-siloed architecture doesn't carry over. For our use case (overhead squat → single-leg squat → push-up session), we need a **session-level** layer: per-exercise scores feed an aggregate movement-quality vector, and we look for patterns (e.g., shoulder mobility deficit manifesting in both overhead squat and push-up lockout).

6. **Reference rep construction — specify explicitly.** The paper is vague; we should pick one and document it in the decision doc. Recommendation: **DBA (DTW Barycenter Averaging)** of 3–5 expert demonstrations per exercise rather than a single demo rep. This gives us a smoother template and an expected-variance envelope we can use for tolerance bands.

7. **Validation — we need more rigor than the paper.** N=6 healthy research-team members is a weak validation. We should plan for:
   - Independent physiotherapist blind rating of a held-out set (pass/fail + compensation type).
   - Cohen's kappa between system labels and clinician labels.
   - A **negative set** (deliberately wrong reps) so we can report separation, not just agreement.
   - Optional: IMU cross-check on a subset if hardware permits.

8. **Fixed bounding-box trick is cheap and worth adopting** — they specifically cite it as a tracking-stability improvement for MediaPipe. If we use MediaPipe, we should replicate.

### TL;DR for L2 Plan 3

The paper validates our **core pipeline shape** (2D/3D pose → joint angles → DTW align → NCC score against expert reference), provides concrete formulas (Eq. 13–16), and supplies a starting similarity anchor (NCC ≈ 0.85 = "good"). It does **not** give us fatigue detection, cross-movement analysis, rigorous validation methodology, or reference-rep aggregation strategy — those are our design responsibility. Plan 3 should cite this paper for the DTW+NCC math and explicitly scope the four gaps above as novel contributions.
