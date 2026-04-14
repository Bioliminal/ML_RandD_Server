# Research Integration Report — Technical Context Document

**Project:** BioLiminal (UT Austin capstone, 5-person team)
**Date:** 2026-04-09
**Status:** Research synthesis — pre-implementation
**Purpose:** Technical context document for team members and their AI agents. Captures the state of sensing/ML research, product architecture changes based on new findings, and open research directions. Companion to the plain-English PDF at `docs/operations/comms/research-integration-report.pdf`.

> **⚠️ 2026-04-10 revision pointer.** After deep-reading 16 newly added papers (OpenCap / OpenCap Monocular / WHAM / Miller hybrid ML+MSK / Sahrmann MSI series / Van Dillen 2016 RCT / Harris-Hayes 2016 & 2018 / Joyce 2023 / Rajagopal 2016 / Uhlrich coordination retraining / TCPFormer / ViTPose / Sabo Beighton), several architectural decisions in §2.4, §5, §6, §10 are **superseded** by `docs/research/model-framework-recommendations-2026-04-10.md`. Key changes: premium pipeline switches from `MediaPipe → MotionBERT → HSMR` to `MediaPipe → WHAM → OpenCap Monocular` (HSMR retained as parallel branch for rollup spine sequencing only); intake questionnaire removed per team decision; MSI framework cherry-picked (kinematic rules yes, diagnostic labels no) per Van Dillen 2016 RCT negative result. Read that file before acting on this one. Per-paper extractions live in `docs/research/deep-read-sensing-2026-04-10.md` and `docs/research/deep-read-biomech-2026-04-10.md`.

---

## 0. Document Scope & Conventions

This document is intentionally dense. It is the authoritative technical context for the BioLiminal sensing and ML layer as of 2026-04-09. It supersedes prior assumptions in `BRAINLIFT.pdf` where they conflict (notably the "free tier = on-device only" assumption).

**Source materials synthesized:**
- 14 peer-reviewed papers in `docs/research/sensing/` (PDFs)
- 7 web/reference HTML docs in `docs/research/sensing/`
- `docs/research/complete-research-document.md` — the foundational two-layer thesis (camera + sEMG)
- `docs/operations/BRAINLIFT.pdf` — cognitive design and SPOVs
- `docs/operations/gtm.md` — go-to-market plan
- `docs/research/sensing/ML.json` — CSL JSON bibliography (Zotero export)
- 3 targeted web research queries (MotionBERT, temporal scoring, body-type adaptation)

**Conventions:**
- Angles in degrees, distances in mm, accuracy as Pearson r or RMSE as specified
- Model names in `code format`; paper citations in (Author Year) with DOI in Section 8
- "Free" and "Premium" refer to feature depth tiers, NOT compute location (see §2.1)
- MPJPE = Mean Per-Joint Position Error (3D ground-truth benchmark metric)
- PCK = Percentage of Correct Keypoints (2D localization metric)
- DOF = Degrees of Freedom
- r = Pearson correlation coefficient
- SBL/BFL/FFL = Superficial Back Line / Back Functional Line / Front Functional Line (fascial chains with strong evidence per Wilke 2016)

---

## 1. Phone Camera Pose Estimation — Measured Accuracy Envelope

### 1.1 Per-joint accuracy baseline (MediaPipe on smartphones)

Source: Akturk et al. 2026 (DOI: 10.1007/s11042-026-21256-z). n=15 volunteers, sit-to-stand movement, sagittal plane, single smartphone camera at 720p, compared against marker-based system + MATLAB Multibody simulation via inverse dynamics.

| Joint | Correlation (r) | Reliability |
|-------|----------------|-------------|
| Hip | 0.94 | Production-ready for joint moment estimation |
| Knee | 0.95 | Production-ready for joint moment estimation |
| Ankle | 0.11 | Unreliable — exclude from primary analysis |

**Implication for screening protocol:** Any movement assessment that depends primarily on ankle kinematics (e.g., ankle dorsiflexion restriction detection) cannot rely on MediaPipe alone. Ankle measurement can be used only as a qualitative cue, not a quantitative flag. This constrains Superficial Back Line (SBL) chain reasoning — SBL involvement often manifests at the ankle, and we must reach it via hip/knee/spine patterns instead of direct ankle measurement.

**Note on protocol validity:** Akturk's validation is limited to sit-to-stand. Extrapolation to deep squat, single-leg squat, and especially forward flexion is not guaranteed. §7.2 identifies the validation gap for forward flexion specifically.

### 1.2 Lab-to-real-world degradation

Source: Singhtaun et al. 2025 (DOI: 10.1145/3719384.3719453). OWAS ergonomic risk assessment using MediaPipe Pose. Evaluation on 72 reference postures (controlled) vs simulated packing station (real-world).

| Body region | Controlled accuracy | Real-world accuracy | Degradation |
|-------------|---------------------|---------------------|-------------|
| Back | 90.74% | 70.42% | −20.32 pp |
| Arms | 92.71% | 82.78% | −9.93 pp |
| Legs | 85.53% | 71.25% | −14.28 pp |
| Full body risk category | — | 77.64% | — |

**Implication:** The ~20pp real-world drop is driven by lighting, clothing occlusion, camera angle, and background. Setup guidance is therefore not a UX polish item — it is the primary accuracy lever for the free tier. This matches the BRAINLIFT doc's Phase 2 (Camera Setup) cognitive load analysis; the design response (progressive validation, one requirement at a time, real-time skeleton overlay with confidence colors) is now empirically justified.

### 1.3 Lightweight scoring pipeline — validated reference architecture

Source: Peng et al. 2026 (DOI: 10.1038/s41598-026-43294-1). BlazePose + Random Forest + Siamese Neural Network.

| Component | Function | Accuracy |
|-----------|----------|----------|
| BlazePose | Keypoint extraction (33 landmarks) | — |
| Random Forest | Pose classification | 98% |
| Joint angle computation | Per-rep angle error | <6% |
| Siamese NN + similarity metric | Quality scoring vs reference | 92-98% correlation with expert scores |

**Integration path:** This is a direct blueprint for BioLiminal's baseline scoring pipeline. We can adopt this architecture wholesale for the first-pass movement quality scorer. The siamese scoring component maps to our "compare user movement against chain-specific reference patterns" requirement.

### 1.4 Capable-phone upgrade path

Source: Han et al. 2025 ("Enhancing accuracy in dynamic pose estimation using HRPose"). HRNet feature extraction + SinglePose AI keypoint localization.

Key architectural property: HRNet maintains high-resolution feature maps throughout the extraction process rather than progressively downsampling. This preserves fine-grained spatial detail, which matters most during fast movements and occlusion scenarios — both of which occur in our single-leg movements and deep squats.

**Adaptive tier strategy:** At session start, probe phone GPU capability (via WebGPU feature detection or similar). Route to HRPose pipeline if capable, MediaPipe otherwise. Report model used in session metadata for later accuracy calibration.

---

## 2. Product Architecture — Updated Tier Model

### 2.1 Correction to prior tier assumptions

**Prior model (incorrect):** Free tier = on-device MediaPipe. Premium tier = server-side deeper models. This conflated feature depth with compute location.

**Updated model:** Tiers are defined by **feature depth**. Compute location is a separate axis determined by latency requirements and cost:

- **Real-time feedback during capture** → on-device (any tier)
- **Post-capture analysis for report generation** → server-side (any tier)
- **Adaptive:** phone capability check at session start determines how much runs locally

This means a free-tier user can still receive server-processed analysis — they just get a less detailed report, fewer chain cross-references, and simpler scoring. The compute bill is an operational concern, not a tier definition.

### 2.2 Tier feature matrix

| Capability | Free | Premium |
|-----------|------|---------|
| Pose estimation model | MediaPipe BlazePose (33 keypoints) | HSMR → SKEL (46 biomechanical DOF) |
| 2D→3D lifting | Optional (angles from 2D sufficient for basic flags) | MotionBERT (monocular video → 3D) |
| Skeletal representation | Independent joints with ball-socket assumption | Biomechanically constrained DOF per joint |
| Chain reasoning engine | Rule-based threshold table | Graph neural network on skeleton graph |
| Spine detail | 3 landmarks (shoulders, hip midpoint approximations) | Full SKEL spine kinematic tree with joint limits |
| Continuous movement tracking (e.g., rollup) | Not included | Per-frame SKEL + phase segmentation |
| Multi-movement temporal tracking | Basic rep counting | DTW-aligned per-rep comparison + trend metrics |
| Body type adjustment | Intake questionnaire (Beighton proxy) | SKEL β shape parameters + optional video Beighton |
| Movement quality scoring | Random forest classifier on joint angles | Siamese network similarity + confidence intervals |
| Session report | Summary with flags and disclaimers | Full chain narrative, spine sequence analysis, temporal story |

### 2.3 HSMR / SKEL — the primary unlock

Source: Xia et al. (CVPR, HSMR paper — `docs/research/sensing/biomechanically-accurate-skeleton.pdf`).

**SKEL model properties:**
- 46 pose parameters vs SMPL's 72 — only real human DOF modeled
- Each pose parameter = single DOF, Euler-angle representation
- Explicit joint rotation limits per parameter (e.g., knee: 1 DOF, 0° extension to 135° flexion)
- Surface mesh topology shared with SMPL (enables interop with existing tools)
- Shape parameters `β` shared with SMPL (enables body composition estimation — see §5)

**HSMR regression pipeline (forward pass, production-ready):**
1. Input: single RGB image of person
2. ViT backbone extracts image features
3. Transformer head regresses SKEL parameters:
   - Pose `q` in continuous rotation representation (not Euler directly — more stable regression target)
   - Shape `β` (body proportions)
   - Camera `π`
4. Convert to rotation matrix `q_mat`, apply parameter loss during training
5. Convert to Euler `q_Euler` for downstream SKEL model consumption

**Training data generation:** SMPL (pseudo-GT) → SKEL fitting via optimization (SKELify). Iteratively refined during training as model predictions improve. Initial refinement is offline and imperfect; periodic batch-mode refinement progressively improves pseudo-GT quality.

**Benchmark performance vs HMR2.0 (the direct SMPL-based baseline):**

| Dataset | Metric | HMR2.0 | HSMR | Delta |
|---------|--------|--------|------|-------|
| COCO | PCK @0.05 | 0.86 | 0.85 | −0.01 |
| COCO | PCK @0.1 | 0.96 | 0.96 | 0.00 |
| LSP-Extended | PCK @0.05 | 0.53 | 0.51 | −0.02 |
| PoseTrack | PCK @0.1 | 0.98 | 0.98 | 0.00 |
| 3DPW | MPJPE | 81.3 | 81.5 | +0.2 |
| Human3.6M | MPJPE | 50.0 | 50.4 | +0.4 |
| Human3.6M | PA-MPJPE | 32.4 | 32.9 | +0.5 |
| **MOYO (extreme poses)** | **MPJPE** | **123.3** | **104.5** | **−18.8** |
| **MOYO (extreme poses)** | **PA-MPJPE** | **90.4** | **79.6** | **−10.8** |

**Joint violation rates (frequency of predicted joint angles exceeding biomechanical limits, MOYO dataset):**

| Model | Left elbow >10° | Right knee >10° | Left elbow >30° | Right knee >30° |
|-------|-----------------|-----------------|-----------------|-----------------|
| PARE | 36.4% | 23.2% | 5.5% | 0.4% |
| CLIFF | 34.2% | 31.0% | 5.2% | 0.3% |
| HybrIK | 58.7% | 48.6% | 16.4% | 17.5% |
| PLIKS | 41.6% | 43.8% | 8.3% | 8.5% |
| HMR2.0 | 47.6% | 56.4% | 8.5% | 1.6% |
| **HSMR** | **0.0%** | **4.5%** | **0.0%** | **0.0%** |

**Implication:** Any SMPL-based method we evaluate will produce biomechanically impossible joint rotations at rates from 23% to 58% at the 10° threshold. HSMR is the only model we reviewed that produces anatomically valid output by construction. For a movement screening product that claims to inform healthcare/fitness decisions, this is non-negotiable.

**Performance vs optimization-based SKEL fit:** The "HMR2.0 + SKEL fit" two-stage baseline (regress SMPL, then fit SKEL) takes ~3 minutes per frame. HSMR end-to-end forward pass is orders of magnitude faster. Server-viable for batch report generation.

### 2.4 2D→3D monocular lifting

Source: web research, 2026-04-09 (see §8.2).

| Model | Year | MPJPE (H36M, mm) | Monocular | License | Status |
|-------|------|------------------|-----------|---------|--------|
| VideoPose3D | 2019 | ~37-40 | Yes | — | Deprecated for new pipelines |
| MotionBERT | 2023 (ICCV) | 35.8 | Yes | Apache 2.0 | **Recommended starting point** |
| MotionAGFormer | 2024 (WACV) | 37.8 | Yes | MIT | Alternative |
| TCPFormer | 2025 | 33.5 | Yes | TBD | Upgrade path (code pending) |
| OPFormer | 2025 | 37.6 | Yes | TBD | Part-aware alternative |
| PriorFormer | 2025 | ~38-40 | Yes | TBD | Real-time focus |
| Pose2Sim | — | 15-30 (OpenSim metric) | **NO — multi-cam only** | Apache 2.0 | Not viable for single phone |

**Recommended pipeline for premium tier:**
1. Phone captures video at 30 fps
2. On-device MediaPipe extracts 33 2D keypoints per frame (or HRPose on capable phones)
3. Server receives keypoint stream
4. MotionBERT lifts 2D sequence to 3D joint positions
5. HSMR fits SKEL biomechanical skeleton to the 3D joints
6. Chain reasoning engine consumes SKEL output

**Why MotionBERT first, not HSMR directly:** HSMR takes single images as input and produces SKEL from each frame independently. MotionBERT gives us temporal consistency across frames, which matters for continuous movements (§3). Running both is the belt-and-suspenders approach: MotionBERT provides temporally smooth 3D joint positions, HSMR provides the biomechanical constraint layer.

### 2.5 Graph neural networks for chain reasoning

Source: Yang et al. 2025 (DOI: 10.1007/s10462-025-11442-0) — survey of graph networks for human skeleton modeling.

**Why graph networks map to fascial chains:**
- Skeleton naturally represented as graph: joints = nodes, bones = edges
- Fascial chains are graph paths: SBL traverses plantar fascia → calves → hamstrings → erector spinae → back of skull
- Graph Convolutional Networks (GCNs) propagate information along graph edges, enabling detection of co-occurring patterns at distant joints
- This is the computational formalization of SPOV 3 ("the body is a system, and treating joints independently produces wrong answers")

**Implementation direction:** Start with rule-based chain reasoning (conditional logic over joint angle thresholds) for the free tier. Train a GCN on collected session data for the premium tier, with chain involvement as the supervised label (clinician-reviewed). The survey covers GCN, MS-G3D, CTR-GCN, and Point Transformer variants — selection depends on compute budget and training data scale.

---

## 3. Spinal Rollup & Continuous Movement Analysis

This is a **newly scoped requirement** not fully covered by the BRAINLIFT protocol design. Some screening movements (notably the toe-touch-to-standing rollup) require continuous frame-by-frame analysis rather than single-frame or per-rep scoring.

### 3.1 Why single-frame analysis fails for rollup

A spinal rollup is a continuous motion where the diagnostic signal is **the sequencing of vertebral segment motion**, not any single posture along the way:
- A healthy rollup unfolds smoothly from the top down (or from pelvis up, depending on cueing)
- A compensation pattern shows segments moving out of order, hinging at specific points, or staying rigid while adjacent segments do all the work
- The final standing posture can look identical in a healthy vs compensating rollup
- The whole diagnostic value is in the timeline

### 3.2 Diagnostic targets for rollup analysis

| Target | What we measure | Why it matters |
|--------|-----------------|----------------|
| Segment initiation order | Which spine segment begins moving first per frame | Indicates motor control pattern (lumbar-led vs hip-led vs thoracic-led) |
| Segment mobility distribution | Frame-by-frame curvature contribution per spine region | Detects hinge points (one segment doing 80% of the bending) |
| Inter-segmental timing | Lag between adjacent segment motion onsets | Reveals rigidity (large lag) or coupling (zero lag) |
| Curve evolution | How spine curvature changes across movement phases | Compares against reference rollup pattern |
| Hip-spine coupling | Ratio of lumbar flexion to hip flexion at each phase | The classic "lumbar-pelvic rhythm" measurement |
| Reversal smoothness | Acceleration profile at bottom of movement | Detects hanging on passive structures vs active control |

### 3.3 Technical requirements

**Spine representation minimum:** The 3 MediaPipe torso landmarks (shoulders midpoint, hip midpoint, approximate thoracic) cannot produce segmental analysis. We need SKEL's full spine kinematic tree to measure segment-by-segment motion.

**Frame rate:** MediaPipe runs at 25-30+ fps on smartphones. For rollup analysis, we need every frame processed or a structured keyframe sampling strategy (e.g., every N frames + dense sampling near movement phase transitions).

**Processing:** Per-frame SKEL fitting via HSMR is server-side. Free tier cannot offer rollup analysis unless we develop a lighter approach or find that MediaPipe's 3 spine points (with accuracy validation — see §7.2) can produce a meaningful subset.

### 3.4 Phase segmentation requirement

The DTW-based temporal comparison from §4 handles discrete reps well but doesn't decompose continuous movements. For rollup, we need automatic phase detection:

| Phase | Detection signal |
|-------|------------------|
| Initial bend | Hip flexion angle exceeds 15° from vertical |
| Mid-descent | Hip flexion in 45-75° range |
| Near-floor | Hip flexion > 75°, fingertip-to-ground distance minimized |
| Reversal | Hip flexion derivative changes sign |
| Mid-rise | Hip flexion in 75-45° range, vertical velocity positive |
| Full stand | Hip flexion < 15°, vertical velocity ≈ 0 |

Within each phase, compare spine curvature against a reference pattern. Aggregate phase-level deviations into a rollup quality score.

**This is unpublished methodology as far as our literature review has found.** See §7.1, §7.3, §7.4 for the specific research gaps this creates.

---

## 4. Multi-Movement Temporal Analysis — Cross-Protocol Fatigue Detection

### 4.1 Reference methodology

Source: "Real time action scoring system for movement analysis and feedback in physical therapy" (Scientific Reports 2025, DOI: 10.1038/s41598-025-29062-7). Web research finding — PDF not in our collection.

**Pipeline:**
1. Extract joint angle time series per rep (using MediaPipe or equivalent pose estimator)
2. Compute angular velocity, ROM, range-of-motion per rep
3. Align reps against reference rep via Dynamic Time Warping (DTW)
4. Compute Normalized Cross-Correlation (NCC) for similarity scoring
5. Trend analysis across reps: detect monotonic changes in ROM, velocity, compensation angles

**Validation:** Outperforms RepNet on both accuracy and computational cost. Runs on pose keypoints alone — no additional hardware, no additional models, no training data beyond reference movements.

### 4.2 Application to BioLiminal protocol

BioLiminal runs a 4-movement screening protocol. Within each movement, the user performs multiple reps. Across movements, we need to detect whether compensation patterns develop or worsen.

**Per-rep metrics:**
- Joint angle amplitude (peak flexion/extension)
- Joint angle velocity profile (acceleration, peak velocity, deceleration)
- ROM (maximum - minimum)
- Compensation angles (e.g., knee valgus, trunk lean)

**Per-movement trend metrics (within a single movement's reps):**
- ROM decrease = fatigue of primary movers
- Velocity decrease = loss of power/coordination
- Compensation angle increase = load shifting to secondary structures
- Reversal point asymmetry = control breakdown

**Cross-movement metrics (across the 4-movement protocol):**
- Chain-level compensation buildup (e.g., knee valgus present in movement 1, more pronounced in movement 3)
- Fatigue carryover (ROM reduction present at movement 4 start that wasn't there at movement 1 start)
- Emergent compensations (new compensation pattern appears in later movements)

### 4.3 Product narrative implications

The per-movement snapshot narrative ("your knee collapsed 12°") becomes a temporal narrative ("your knee stability decreased 15% between movement 1 and movement 3, and the compensation spread to your hip during movement 4, consistent with SBL chain involvement").

This is a differentiation moment: **every competitor product (Hinge Health, Sword Health, DARI Motion, Kemtai, Tempo) scores frames or individual exercises.** None track compensation evolution across a movement sequence. This directly supports SPOV 1 ("chain-aware video triage catches systemic dysfunction that symptom-focused clinical visits miss") with a concrete technical differentiator.

---

## 5. Body Type Adaptation

### 5.1 Problem statement

Fixed biomechanical thresholds systematically misclassify populations that deviate from the population mean. Specifically:

- **Hypermobile individuals** (Ehlers-Danlos, general joint laxity): show 3.5° lower knee valgus and 4.5° greater external rotation at baseline than non-hypermobile controls (PMC8558993). Fixed thresholds produce false negatives (miss real issues because baseline is wider) and false positives (flag normal ranges as abnormal because they exceed rigid thresholds).
- **Women**: ~5-8° more baseline valgus than men (Hewett 2005 data, reanalyzed).
- **Youth (<16)**: different normative ROM tables published in PT literature.

Without body-type adjustment, BioLiminal's chain reasoning produces systematically wrong interpretations for these populations. This is a scientific validity issue, not a polish issue.

### 5.2 Detection methods (tiered)

| Method | Tier | Data source | Cost |
|--------|------|-------------|------|
| Intake questionnaire | Free | Beighton-adjacent yes/no questions (palms flat to floor, thumb to forearm, elbow hyperextension, knee hyperextension, little finger backward) | Free, single UI screen |
| SKEL shape parameters | Premium | `β` vector from HSMR output — encodes height, limb proportions, BMI proxy | Free side effect of HSMR |
| Video-based Beighton | Premium (future) | Dedicated movements during onboarding: thumb-to-forearm, palms-to-floor, etc. Pose estimation measures joint angles. | Additional onboarding flow |

**Video Beighton validation:** 2026 study (PubMed 41639883, n=225 EDS patients) achieved 91.9% recall for hypermobility detection from video alone. This is production-viable; we can add it as a premium feature post-launch.

### 5.3 SKEL shape parameters for anthropometry

Source: web research + HSMR paper. SKEL shares shape space with SMPL.

- First two principal components of `β` capture most variance: PC1 ≈ height/size, PC2 ≈ weight/build
- Full `β` vector (10D) encodes limb length ratios, torso:limb ratio, upper:lower body proportions
- BMnet and STAR extend SMPL for extreme BMI modeling — relevant if we see accuracy issues in population tails
- Adversarial Body Simulator (ABS) demonstrates SMPL's range of valid body shapes

**Integration path:**
1. Run HSMR on onboarding capture
2. Extract `β` vector
3. Classify into body type bucket (average, tall, short, wide, narrow, hypermobile-likely based on limb proportions and intake Qs)
4. Pass body type into chain reasoning threshold selector

### 5.4 Threshold adjustment — literature synthesis approach

**No paper in our review prescribes movement-screening threshold adjustments by body type.** This gap is genuinely novel territory.

**Workable interim approach:** Assemble a conditional threshold table from existing biomechanics literature. Example (placeholder numbers, to be refined):

| Population | Knee valgus "concern" | Knee valgus "flag" | Source basis |
|------------|----------------------|---------------------|--------------|
| Default (adult, non-hypermobile, male) | >8° | >12° | Hewett 2005 (10° = 2.5x ACL risk) |
| Adult, female | >10° | >14° | Hewett 2005 sex difference data |
| Hypermobile | >12° | >16° | PMC8558993 (3.5° baseline shift) |
| Youth (<16) | >10° | >15° | PT normative tables |

**Effort to produce v1 table:** ~3 days of literature synthesis. This is not machine learning. It's clinical knowledge assembly.

**Validation path (post-launch):** Every session logs full data. After N sessions (N TBD based on power analysis), compare threshold-adjusted classifications against clinician review. Iterate table. Eventually this becomes training data for a learned threshold model — but that is post-launch, not pre-launch.

### 5.5 Research contribution framing

Per SPOV 4 ("this is a research instrument first — the product direction follows the data"): the fact that no threshold adjustment tables exist is itself publishable. BioLiminal can be the first to:
1. Quantify the magnitude of misclassification from fixed thresholds in diverse populations
2. Publish empirically validated body-type-adjusted threshold tables
3. Open-source the calibration dataset (with consent)

This is a genuine research contribution, not just a product feature. It reinforces the GTM positioning as an open-source research instrument.

---

## 6. Product Architecture Change Summary

### 6.1 What changed from the original BRAINLIFT design

| Area | BRAINLIFT design | Updated design | Driver |
|------|------------------|----------------|--------|
| Tier definition | Free = on-device, Premium = server | Free/Premium = feature depth, compute location is independent | Correction of conflated axes |
| Pose model (premium) | Unspecified — "better model" | HSMR → SKEL specifically | Xia et al. HSMR finding |
| 3D reconstruction | Not explicitly addressed | MotionBERT as server-side 2D→3D lifter | Web research Gap 1 |
| Spine analysis | Basic (3 landmarks) | Full SKEL spine for premium; rollup sequencing as new requirement | User clarification about rollup movements |
| Cross-movement tracking | Not specified | DTW + trend detection across reps and movements | Scientific Reports 2025 paper |
| Body type handling | Implicitly ignored | Questionnaire + SKEL β parameters + video Beighton (future) | PMC8558993 + web research Gap 3 |
| Chain reasoning | Rule-based only | Rule-based (free) + GCN on skeleton graph (premium) | Yang et al. graph network survey |

### 6.2 What stayed the same

- Four-movement screening protocol structure
- Three-chain scope (SBL, BFL, FFL) — the chains with strong evidence
- Single phone camera as primary input modality
- Wellness/fitness positioning (not clinical, not FDA-regulated)
- Cognitive design phases (landing, setup, movement, results) from BRAINLIFT
- Report output as conversation starters for professional visits, not standalone conclusions
- SPOV 4 research-instrument-first positioning

### 6.3 New technical primitives to build or integrate

| Primitive | Build vs integrate | Complexity | Dependencies |
|-----------|-------------------|------------|--------------|
| MediaPipe pose capture (mobile) | Integrate (Google) | Low | Flutter MediaPipe package |
| HRPose fallback (capable phones) | Integrate | Medium | WebGPU capability detection |
| Session metadata schema | Build | Low | — |
| 2D→3D lifting via MotionBERT | Integrate | Medium | Server infra, Python/PyTorch |
| HSMR model serving | Integrate | Medium | GPU inference endpoint |
| SKEL parameter extractor | Integrate (comes with HSMR) | Low | HSMR pipeline |
| Per-rep DTW alignment | Build | Low | Standard DTW library |
| Trend analysis across reps | Build | Low | — |
| Phase segmentation for continuous movements | Build (novel) | High | Open research — §7.3 |
| Spine sequencing analyzer (rollup) | Build (novel) | High | Open research — §7.1 |
| Graph NN chain reasoning | Build + train | High | Labeled training data |
| Body type classifier | Build (lookup table + rules) | Low | Literature synthesis |
| Threshold adjustment table | Build (literature synthesis) | Low (3 days) | — |
| Video Beighton scorer | Build (future) | Medium | Post-launch |

---

## 7. Open Research Areas

These are gaps in our current literature that require further investigation before implementation. Each is scoped as a concrete research task with specific search directions. No priority is assigned — the team determines sequencing based on their own judgment of product dependencies.

### 7.1 Spinal rollup analysis from video

**Gap:** No paper in the current collection covers frame-by-frame spine curve tracking during continuous forward flexion and re-extension. HSMR provides per-frame spine via SKEL, but the analysis layer — phase decomposition, segmental timing, hinge detection, comparison against healthy reference — is unbuilt and largely unresearched.

**What to find:**
- Reference pattern for healthy rollup sequencing (quantified, not qualitative)
- Criteria for distinguishing "hinging" (localized bending) from "rolling" (distributed bending) in joint angle data
- Lumbar-pelvic rhythm measurements during the descent and ascent phases
- Normative ROM distributions per spine segment during the movement

**Search terms:**
- "segmental spinal motion" + "forward flexion"
- "lumbar-pelvic rhythm" + "quantitative"
- "spinal rollup assessment" + "biomechanics"
- "Pilates rollup" + "biomechanical analysis"
- OpenSim spine models + forward flexion simulation
- Sahrmann movement system impairment syndromes (especially lumbar flexion syndrome)

**Databases:** PubMed, Google Scholar, PEDro (physiotherapy evidence), Cochrane PT reviews

**Deliverable:** A document summarizing healthy rollup patterns with quantified metrics (angle ranges per phase, timing ranges, acceptable variation bounds) that can be encoded into the spine sequencing analyzer.

### 7.2 MediaPipe spine accuracy during forward flexion

**Gap:** Akturk et al. validated MediaPipe accuracy for sit-to-stand, which involves limited spinal motion. We have no data on how the 3 MediaPipe torso landmarks (left shoulder, right shoulder, hip midpoint) perform during deep forward flexion, where the torso is approximately horizontal and the camera's sagittal view is compromised.

**Why this matters:** If MediaPipe spine accuracy degrades significantly during rollup, the free tier cannot offer any spine analysis for that movement. This would force the rollup into a premium-only feature, which changes the GTM positioning.

**What to find:**
- Any MediaPipe validation study that includes forward flexion or bending movements
- Comparison of MediaPipe torso landmark accuracy vs marker-based systems in non-upright postures
- Effect of self-occlusion (arms crossing in front of torso during rollup) on MediaPipe landmark confidence scores

**Search terms:**
- "MediaPipe Pose" + "forward flexion" OR "bending" OR "trunk flexion"
- "markerless pose estimation" + "non-upright" OR "forward bend"
- MediaPipe validation + VICON + squat/deadlift

**Deliverable:** Either a cited accuracy number we can use, or a protocol for our own validation (MediaPipe vs a trusted reference during rollup, on team members).

### 7.3 Phase segmentation for continuous movements

**Gap:** Automatic detection of movement phase boundaries from joint angle time series. DTW compares reps but assumes rep boundaries are known. For continuous movements, we need unsupervised phase boundary detection.

**What to find:**
- Changepoint detection applied to kinematic time series
- Hidden Markov Models (HMM) for exercise phase segmentation
- Unsupervised action segmentation in sports biomechanics literature
- Any paper that segments a single continuous exercise into canonical phases

**Search terms:**
- "movement phase detection" + "joint angles" OR "kinematic"
- "exercise segmentation" + "unsupervised"
- "temporal action segmentation" + "rehabilitation" OR "sports"
- "changepoint detection" + "motion capture"

**Candidate approaches to evaluate:**
- Rule-based: velocity sign changes + angle thresholds
- HMM with hand-crafted states (initial, descent, bottom, ascent, final)
- Deep learning: Temporal Convolutional Networks trained on labeled phase boundaries
- Zero-shot: compare to reference movement via sliding-window DTW, extract phase boundaries from alignment path

**Deliverable:** A phase segmentation method evaluated on a small set of rollup recordings, with documented accuracy (correct phase boundary detection rate).

### 7.4 Normative spine sequencing data

**Gap:** Even with technical capability to measure spine sequencing, we need reference patterns to compare against. What does a healthy rollup look like in quantified spine segment timing?

**What to find:**
- PT assessment manuals with quantified rollup/forward flexion criteria
- Motion capture studies of healthy adults performing rollup
- Population datasets with spine kinematics during forward flexion

**Search terms:**
- Sahrmann movement system assessment — specific criteria for lumbar flexion syndrome
- "Functional Movement Screen" spine criteria (FMS)
- "Selective Functional Movement Assessment" (SFMA) spine breakouts
- OpenCap database (Stanford open biomechanics)
- "normative database" + "trunk flexion" + "kinematic"

**Deliverable:** A reference rollup pattern (healthy adult) with quantified per-segment angle timing, hip-spine coupling ratios, and acceptable variation ranges.

### 7.5 Combined EMG + video spine analysis

**Gap:** Per the BioLiminal two-layer thesis, the camera sees movement but only muscles tell the truth. For the spine specifically, erector spinae EMG during rollup reveals whether the user is actively controlling the descent or hanging on passive structures (flexion-relaxation phenomenon). This is the ultimate premium tier — sEMG compression garment + video combined.

**What to find:**
- Marras & Granata (already cited in complete-research-document.md) — EMG-assisted spinal loading models
- Flexion-relaxation phenomenon quantification via sEMG
- Any study that combined sEMG erector spinae with video-based kinematics during forward flexion
- BioAmp sensor placement for erector spinae (already in hardware research)

**Search terms:**
- "flexion-relaxation phenomenon" + "sEMG"
- "erector spinae" + "forward bending" + "EMG"
- "sEMG" + "video motion capture" + "spine" + "forward flexion"

**Deliverable:** A decision about whether to include erector spinae EMG in the v1 hardware (currently 4ch prototype focuses on L/R erector spinae + VL/VM quad, which already covers this if we align the rollup test with those channels).

### 7.6 Population-specific threshold validation protocol

**Gap:** We can assemble a v1 threshold adjustment table from literature (§5.4), but validating it requires our own data. The validation protocol needs to be defined before data collection starts.

**What to find / decide:**
- Statistical power analysis: how many sessions per population (hypermobile, female, youth, baseline) to achieve 80% power at α=0.05 for detecting threshold improvement?
- Clinician review protocol: how many clinicians review per session? How do we resolve disagreements?
- Primary endpoint: false positive rate, false negative rate, or combined (e.g., F1)?
- Blinding: should clinicians be blinded to body type classification during review?

**Search terms:**
- Movement screening validation methodology
- Clinical prediction rule validation studies
- Inter-rater reliability in movement screening

**Deliverable:** A pre-registered validation protocol document that can be filed before data collection begins. Aligns with SPOV 4's research-instrument positioning.

---

## 8. Sources & Bibliography

### 8.1 Primary papers reviewed (in `docs/research/sensing/`)

| Paper | DOI | Key finding | Used in section(s) |
|-------|-----|-------------|---------------------|
| Akturk, Derdiyok, Serbest (2026) — "Markerless joint angle estimation using MediaPipe with a rapid setup for joint moment calculation" | 10.1007/s11042-026-21256-z | Hip r=0.94, knee r=0.95, ankle r=0.11 from single smartphone camera; n=15 sit-to-stand | §1.1, §1.2, §7.2 |
| Singhtaun, Natsupakpong, Lorprasertkul (2025) — "Ergonomic Risk Assessment Using Human Pose Estimation with MediaPipe Pose" | 10.1145/3719384.3719453 | OWAS risk 90.74/92.71/85.53% controlled → 70.42/82.78/71.25% real-world | §1.2 |
| Peng, Mao, Fang (2026) — "Human pose recognition and automated scoring detection for sports rehabilitation" | 10.1038/s41598-026-43294-1 | BlazePose + Random Forest 98% accuracy, <6% joint angle error, 92-98% SNN scoring correlation | §1.3 |
| Han, Yi, Feng, Qi, Zhou (2025) — "Enhancing accuracy in dynamic pose estimation for sports competitions using HRPose" | (not in ML.json) | HRNet + SinglePose AI for dynamic/occluded movement scenarios | §1.4 |
| Xia, Zhou, Vouga, Huang, Pavlakos (CVPR) — "Reconstructing Humans with a Biomechanically Accurate Skeleton" (HSMR) | CVPR open access — isshikihugh.github.io/HSMR/ | HSMR: 0% joint violations, 18.8mm better MPJPE on MOYO extreme poses, forward-pass SKEL regression | §2.3, §3.3 |
| Edriss, Romagnoli, Caprioli, Bonaiuto, Padua, Annino (2025) — "Commercial vision sensors and AI-based pose estimation frameworks for markerless motion analysis in sports and exercises" | 10.3389/fphys.2025.1649330 | Mini review of MediaPipe, OpenPose, AlphaPose, DensePose, Kinect, ZED, RealSense | §2.4 |
| Yang, Li, Niu, Yue (2025) — "Graph network learning for human skeleton modeling: a survey" | 10.1007/s10462-025-11442-0 | GCN, MS-G3D, CTR-GCN, Point Transformer for skeleton graph modeling | §2.5 |
| Chen, Feng, Paes, Nilsson, Lovreglio (2025) — "Real-time human pose estimation and tracking on monocular videos: A systematic literature review" | 10.1016/j.neucom.2025.131309 | 68-paper review of real-time monocular pose estimation; accuracy-efficiency tradeoffs | §1, §4 |
| Kappan, Sandoval, Meijering, Cruz (2025) — "A survey on deep learning for 2D and 3D human pose estimation" | 10.1007/s10462-025-11430-4 | Comprehensive DL survey with dataset and metric comparison tables | Background |
| Li, Makihara, Xu, Yagi (2022) — "Multi-View Large Population Gait Database With Human Meshes" | 10.1109/TBIOM.2022.3174559 | OUMVLP-Mesh: 10,000+ subjects, 14 view angles, 3D mesh training from multi-view | §2 |
| Mata, Tangwannawit (2025) — "Kinematic Skeleton Extraction from 3D Model Based on Hierarchical Segmentation" | 10.3390/sym17060879 | PointNet-based 3D point cloud skeleton extraction, 22.82mm MPJPE, 20 joints, 37 segments | §2 |
| Abromavičius, Gisleris, Daunoravičienė, Žižienė, Serackis, Maskeliūnas (2025) — "Enhanced Human Skeleton Tracking for Improved Joint Position and Depth Accuracy in Rehabilitation Exercises" | 10.3390/app15020906 | Dual-camera (90° rotated) reduces depth error by up to 0.4m | §2 |
| Ciardiello, Agnello, Petyx, Martinelli, Cesarelli, Santone, Mercaldo (2026) — "A Method for Human Pose Estimation and Joint Angle Computation Through Deep Learning" | 10.3390/jimaging12040157 | YOLO8n + 25 custom keypoints for physiotherapy, 150K+ annotated images | Background |
| Brunner, Bordes, Mayrhuber, Winkler, Dorfer, Oczak (2026) — "Skeleton integrity: A method for the efficient fine-tuning of pose estimation models for pigs" | 10.1016/j.biosystemseng.2025.104380 | Frame selection strategy for low-data fine-tuning; ViTPose base; method transferable to human domain | Background |

### 8.2 Web research sources (not in local PDF collection)

| Source | URL / identifier | Finding | Used in |
|--------|-----------------|---------|---------|
| MotionBERT (Zhu et al., ICCV 2023) | github.com/Walter0807/MotionBERT | 35.8mm MPJPE on H36M; Apache 2.0; temporal transformer for 2D→3D lifting | §2.4 |
| TCPFormer | arXiv:2501.01770v1 | 33.5mm MPJPE (+12.9% vs MotionBERT); code pending | §2.4 |
| MotionAGFormer | WACV 2024 | 37.8mm MPJPE; MIT license; GCN + Transformer hybrid | §2.4 |
| OPFormer | Nature Sci Rep 2025, DOI: 10.1038/s41598-025-16381-y | 37.6mm MPJPE; part-aware decomposition | §2.4 |
| PriorFormer | arXiv:2508.18238 | Lightweight, real-time, incorporates geometric priors | §2.4 |
| VideoPose3D (Pavllo et al., CVPR 2019) | github.com/facebookresearch/VideoPose3D | Historical baseline; deprecated for new work | §2.4 |
| Pose2Sim | github.com/perfanalytics/pose2sim | Multi-camera markerless kinematics; Apache 2.0; NOT monocular | §2.4 |
| "Real time action scoring system for movement analysis and feedback in physical therapy" | Sci Rep 2025, DOI: 10.1038/s41598-025-29062-7 | DTW + NCC on joint angle features; outperforms RepNet | §4.1 |
| "Enhanced Action Quality Assessment with Dual-Stream Pose and Video Feature Integration" | ECCV 2024 Workshops | Pose + video dual-stream quality regression | §4, §7.1 |
| "Fitness Action Counting Algorithm based on Pose estimation" | ICAIPR 2024, DOI: 10.1145/3703935.3704003 | YOLOv5s + MediaPipe + KNN for rep counting | Background |
| STGCN-PAD anomaly detection | 2024, DOI: 10.1007/s10044-024-01382-w | ST-GCN applied to anomaly detection (adjacent to fatigue detection) | §4 |
| Beighton score vision-based assessment | PubMed 41639883, 2026 | n=225 EDS patients, 91.9% recall for hypermobility detection from video | §5.2 |
| Hypermobility biomechanics | PMC8558993 | Hypermobile athletes: 3.5° less valgus, 4.5° more external rotation than controls | §5.1 |
| SMPL body model | smpl.is.tue.mpg.de | Shape space `β` for body composition modeling; BMnet, STAR extensions | §5.3 |
| Height estimation from limb lengths | PMC12906959 (2026) | Regression equations from forearm/lower leg lengths | §5.3 |
| Hypermobility and lower limb biomechanics | MDPI IJERPH 2025, DOI: 10.3390/ijerph22121776 | Q-angle, internal hip rotation, ankle ROM differences in hypermobile populations | §5.1 |
| Hypermobility impact on cutting biomechanics | Taylor & Francis 2025, DOI: 10.1080/02640414.2025.2511358 | Sex and activity-specific calibration considerations | §5.1 |

### 8.3 Foundational project documents

| Document | Purpose | Relevance |
|----------|---------|-----------|
| `docs/operations/BRAINLIFT.pdf` | Cognitive design and SPOVs | Baseline product framing; SPOVs 1-4 |
| `docs/research/complete-research-document.md` | Two-layer thesis (camera + sEMG) | Injury mechanics, EMG signals, opposing research |
| `docs/operations/gtm.md` | Go-to-market plan | 100 GitHub stars in 3 weeks; open-source chain reasoning engine |
| `docs/research/sensing/ML.json` | CSL JSON Zotero bibliography | Full bibliographic data for all sensing papers |
| `docs/research/sensing/catalog.md` | File catalog with tier assignments | Per-file relevance scoring |
| `docs/research/sensing/research-gaps.md` | Hardware claim audit | 7 unbacked claims, safety constraints |
| `docs/research/sensing/verification-results.md` | Source verification — Merletti, Jiang, Kalichman | Caveats on cited claims |
| `CLAUDE.md` | Project conventions, tier constraints | Authoritative for file placement, scope boundaries |

---

## 9. Papers to Acquire (Not Yet in Collection)

These are papers identified during the review as potentially filling remaining gaps. Acquisition is recommended but not required for architectural decisions already made.

| Paper | Gap it fills | Action |
|-------|--------------|--------|
| MotionBERT (Zhu et al., ICCV 2023) | §2.4 implementation reference | Clone repo, read code |
| "Real time action scoring system" (Sci Rep 2025, DOI: 10.1038/s41598-025-29062-7) | §4.1 DTW/NCC methodology | Download PDF |
| Beighton vision-based scoring (PubMed 41639883, 2026) | §5.2 automated hypermobility detection | Request via institutional library |
| Sahrmann movement system assessment framework | §7.1, §7.4 spine sequencing references | Acquire book or published framework docs |
| Lumbar-pelvic rhythm studies | §7.4 normative rollup data | Systematic literature search |
| TCPFormer (arXiv 2501.01770, 2025) | §2.4 future upgrade | Watch for code release |
| "Enhanced Action Quality Assessment" (ECCV 2024 Workshops) | §7.1 quality regression reference | Download if accessible |
| OpenCap database (Stanford) | §7.4 open biomechanics data for rollup | Register and explore |
| FMS/SFMA spine criteria | §7.4 quantified healthy patterns | Acquire published FMS/SFMA materials |

---

## 10. Decisions Needed from the Team

These are open questions requiring team alignment before implementation proceeds. They are not blocked by further research — they require human judgment.

1. **Rollup inclusion.** Is the toe-touch rollup actually in the 4-movement protocol? The BRAINLIFT doc implies overhead squat, single-leg squat, push-up, and one other movement, but rollup was not explicitly listed. If rollup is in, §3 and §7.1 become high-priority research. If not, spine sequencing analysis can be deferred.

2. **Server dependency for free tier.** Are we willing to serve processed results to free-tier users from our servers, or do we want "free" to mean "zero server cost to us"? This is a cost question, not a technical one. Server inference for MotionBERT + HSMR is not free at scale.

3. **Body type scope at launch.** Ship with just the questionnaire, or include SKEL β extraction at launch? The questionnaire alone is sufficient for the first threshold adjustments; SKEL adds precision but doesn't change the first-order decisions.

4. **Graph NN vs rules-only for chain reasoning at launch.** Ship v1 with rule-based chain reasoning (deterministic, auditable, no training data required) or invest in graph NN training before launch? Rules-only is faster to ship and aligns with the open-source positioning in gtm.md. Graph NN is the more compelling technical story but requires labeled training data we don't have yet.

5. **Premium tier price point.** This document assumes a premium tier exists. Is pricing scoped to cover the compute costs of HSMR/MotionBERT serving per session? If not, premium feature scope must be reduced.

6. **Model serving infrastructure.** HSMR and MotionBERT require GPU inference. Do we use a managed service (Replicate, Modal, Vercel Sandbox) or deploy our own? This affects architecture decisions in tools/ and software/.
