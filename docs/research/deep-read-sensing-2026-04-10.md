# Deep Read — Sensing/ML Papers Added 2026-04-10

**Purpose:** Per-paper technical extraction + pipeline synthesis for the AuraLink server/mobile stack.
**Scope:** 8 ML/vision items moved from `unsorted/` → `sensing/` on 2026-04-10.
**Upstream:** `docs/operations/comms/research-integration-report.md` (2026-04-09). This document refines / partially contradicts the pipeline recommendation in that report.

> ⚠️ **Note on confidence.** Some runtime numbers in this doc (parameter counts, inference latency) are inferred from paper descriptions rather than directly measured. They are flagged where that's the case. Benchmark numbers and dataset facts are from the papers themselves.

---

## Paper-by-paper

### 1. Uhlrich et al. 2023 — OpenCap (PLOS Comp Bio 19(10):e1011462)

- **Pipeline:** Two or more synchronized smartphones → per-frame 2D pose (HRNet-W48 / OpenPose) → triangulated 3D keypoints → inverse kinematics against an OpenSim musculoskeletal model → physics-based muscle/force simulation.
- **Skeleton:** OpenSim lower-limb model (Rajagopal 2016 derivative). 37 DoF, 80 muscle-tendon units.
- **Training data:** Stanford-collected 100-subject validation set; multi-camera marker data as ground truth.
- **Checkpoint/license:** Open-source code (github.com/stanfordnmbl/opencap-core), free cloud processing at opencap.ai (consent-gated data sharing).
- **Runtime:** Cloud processing, ~10–30 min per recording. **Not real-time, not single-frame.**
- **Accuracy:** Walking kinematics agree with marker-based mocap within ~2–3° for major joints; validated on walking, squat, STS, drop-jump.
- **Fine-tuning:** Not a learned end-to-end model — pose detector is pretrained; kinematics is physics-based inverse kinematics. No fine-tuning required for base use. Can swap MSK model (e.g., use a custom Rajagopal variant) without retraining.
- **Integration path (AuraLink):** Premium server tier. But the **dual-camera requirement is a non-starter for consumer single-phone capture.** Use only if we support a dual-phone or phone-plus-tripod capture flow.
- **Limitations:** Multi-camera requirement; cloud-only inference; ~tens-of-minutes latency unsuitable for real-time feedback.

### 2. Gilon, Miller, Uhlrich 2026 — OpenCap Monocular (Utah preprint)

- **This is the critical paper.** Single smartphone video → 3D kinematics + musculoskeletal dynamics.
- **Pipeline:** Raw monocular video → **WHAM** (Shin 2024) for initial world-grounded 3D pose → biomechanical-constraint optimization refines pose against a skeletal model → physics-based simulation + ML regression head estimates joint moments, GRFs, muscle forces.
- **Skeleton:** OpenSim-style anatomical model (lower limb + trunk).
- **Training/validation:** Re-validated against marker-based mocap + force plate data from Stanford/Utah datasets. Walking, squatting, sit-to-stand.
- **Accuracy (monocular):** 4.8° mean absolute error for rotational DoFs; 3.4 cm for pelvis translation. **48% better rotational / 69% better translational than CV-only regression baseline.** GRF estimation accuracy comparable to dual-camera OpenCap for walking.
- **Checkpoint/license:** Open-source (`github.com/utahmobl/opencap-monocular` per author email affiliations; verify URL before use). Research license; same ecosystem as OpenCap.
- **Runtime:** Cloud/server GPU. Optimization step is the bottleneck — seconds-to-minutes per capture. Not real-time.
- **Fine-tuning:** Data needed to improve: subject-level anthropometry can be scaled (β shape vector or direct measurements). Can retrain the ML kinetics head on additional force-plate + video pairs.
- **Integration path (AuraLink):** **This is the strongest single-phone premium candidate.** It already solves the MediaPipe → 3D → biomechanical → kinetics pipeline we were planning to assemble from MotionBERT + HSMR + a custom kinetics layer.
- **Limitations:** Still validated only on walking / squat / STS. Rollup, push-up, single-leg squat coverage unproven. Requires subject height input (minor UX ask). Optimization is server-side only — no on-device variant.

### 3. Miller, Tan, Falisse, Uhlrich 2025 — Hybrid ML + MSK Simulation (bioRxiv)

- **Contribution:** Shows that **neither pure physics nor pure ML** gives best dynamics estimates. A hybrid that uses ML to predict GRF + center-of-pressure and physics to enforce dynamic consistency is best.
- **Reported improvements over baselines:** ~29–45% lower error on joint moments, GRF error down ~40%, knee loading metrics improved 13–30% vs prior OpenCap pipeline.
- **Use in AuraLink:** Direct evidence that we should *not* implement a pure ML "joint moment regressor" and call it done. This justifies adopting the full OpenCap Monocular stack rather than replacing pieces with hand-rolled ML.
- **Limitations:** n=10 walking only in validation cohort. Still bioRxiv, not peer-reviewed.

### 4. Shin, Kim, Halilaj, Black 2024 — WHAM (CVPR 2024)

- **Problem solved:** Monocular video → world-grounded 3D human pose + global trajectory (not camera frame). Handles moving camera, prevents foot sliding via contact-aware trajectory refinement.
- **Architecture:** ViT-style visual encoder → motion encoder/decoder (RNN + feature integration from 2D keypoints and pixels) → contact-aware trajectory decoder. Output is SMPL-family parameters + global translation.
- **Training data:** AMASS (large mocap) → synthetic 2D projections, 3DPW, BEDLAM, EMDB for benchmarking. SMPL-based ground truth.
- **Accuracy:** State-of-the-art on in-the-wild benchmarks (PA-MPJPE, G-MPJPE, jitter, trajectory error). Outperforms TRACE and SLAHMR on moving-camera cases.
- **Checkpoint/license:** Research license at wham.is.tue.mpg.de. **Non-commercial research-only terms from Max Planck / Tübingen — flag for capstone, may constrain any future productization.**
- **Runtime:** Paper emphasizes efficiency vs optimization-based alternatives (SLAHMR). Likely GPU-only, not on-device. Exact FPS/parameter count not quoted — treat as "server GPU, near-real-time at best."
- **Fine-tuning:** Inherits SMPL skeleton. Adapting to a different skeleton requires rebuilding the decoder head — non-trivial.
- **Integration path (AuraLink):** Used as the 3D pose backbone by OpenCap Monocular (§2). If we adopt OpenCap Monocular, WHAM comes with it. We would not deploy WHAM standalone.
- **Limitations:** SMPL's joint-limit violations are still present (HSMR handles that better — see §2.3 of the integration report). WHAM does not enforce biomechanical joint limits; that's why OpenCap Monocular adds the optimization layer on top.

### 5. Liu et al. 2025 — TCPFormer (arXiv 2501.01770)

- **Architecture:** Transformer-based 2D→3D temporal lifter with an **implicit pose proxy** as intermediate representation. Each proxy entry builds one temporal correlation, giving richer temporal modeling than MotionBERT's single 1-to-T mapping.
- **Training data:** Human3.6M + MPI-INF-3DHP (standard academic 3D pose benchmarks).
- **Accuracy:** ~33.5 mm MPJPE on Human3.6M. ~12.9% better than MotionBERT (35.8 → 33.5).
- **Checkpoint/license:** Code not yet released as of early 2026. Treat as "watch this" rather than "ship this."
- **Runtime:** Not mobile. Transformer sequence model, GPU inference.
- **Integration path:** **Direct alternative to MotionBERT** in the two-stage (2D lift → skeleton fit) path. Until code drops, MotionBERT remains the only shippable option in this family.
- **Limitation vs OpenCap Monocular path:** Still only a pose lifter — does not produce kinetics. You still need to bolt on a biomechanical fitter + kinetics stage downstream.

### 6. Xu et al. 2022 — ViTPose (NeurIPS 2022)

- **Architecture:** Plain ViT backbone (no hierarchical/CNN priors) + lightweight pose-head decoder. Scales from 100M to 1B parameters across ViTPose-S / B / L / H variants.
- **Training data:** COCO + MPII 2D keypoint datasets. ImageNet-21K for backbone pretraining.
- **Accuracy:** 80.9 AP on COCO test-dev at the H scale (SOTA at publication). ViTPose-B (~86M params) is the typical "usable" size.
- **Checkpoint/license:** Apache 2.0, github.com/ViTAE-Transformer/ViTPose. Good license for us.
- **Runtime:** ViTPose-B benchmarks at ~158 fps on a single A100 (from the paper). **Not tested on phones in the paper.** The "S" variant with int8 quantization could theoretically run on a high-end Android but it's not a demonstrated mobile solution.
- **Fine-tuning:** Supports knowledge-token distillation from big → small models. Straightforward to fine-tune the decoder on custom keypoint definitions.
- **Integration path:** **Mid-tier 2D keypoint detector** — an alternative to MediaPipe when the phone has the horsepower. Would replace MediaPipe in the upstream of any of our lift paths (WHAM, MotionBERT, TCPFormer).
- **Limitations:** Mobile port is research effort we would own, not a drop-in.

### 7. Sabo et al. 2026 — Vision-based Beighton (PubMed 41639883)

- **Use case:** Automated hypermobility screening from video, not movement quality. Produces a Beighton-style score.
- **Backbone:** MediaPipe / MobileNet pose + downstream classifier. Phone-viable by design.
- **Study:** 125 adults at EDS clinic, 91.9% sensitivity, 42.4% specificity.
- **Integration path:** Optional premium add-on (research-report §5.2). Not part of the core movement-screening pipeline.
- **Note:** This is exactly what the research-integration-report.md already anticipates. No change.

### 8. `best-practices.html` (OpenCap web guide)

- Capture protocol: 2+ smartphones at ~90°, ≥30 fps, lighting, subject height input, specific movement protocols (walking, squat, STS).
- Confirms that OpenCap's **recommended** use is dual-camera. OpenCap Monocular (§2) is the newer single-camera branch that loosens this constraint.

---

## Synthesis

### Pipeline architecture — recommended revision

**Current plan (per research-integration-report.md §2.4):**
```
MediaPipe 2D  →  MotionBERT (2D→3D lift)  →  HSMR (fit SKEL)  →  chain reasoning
```

**Revised plan (this review):**
```
MediaPipe 2D (on-device capture)  →  server upload
  → WHAM (world-grounded 3D)
  → OpenCap-Monocular optimization + MSK kinetics (Rajagopal/Uhlrich)
  → joint moments + GRFs + muscle forces
  → chain reasoning
```

**Why the revision:**
- OpenCap Monocular gives us **kinetics "for free"** (joint moments, GRFs, muscle forces). The Hewett-2005-style thresholds we are encoding (knee valgus moment, hip adduction moment) are **actually** defined on kinetics, not on pose angles. The MotionBERT+HSMR path was going to stop at pose; we'd still have had to hand-roll a kinetics layer downstream.
- Miller 2025 is direct evidence that the hybrid physics+ML approach beats pure ML for exactly the numbers we care about (knee loading, joint moments).
- WHAM is already embedded in OpenCap Monocular, so we inherit state-of-the-art monocular 3D lift without adding a second model.
- Published validation is monocular (Gilon 2026) — matches our single-phone capture assumption.

**What we keep from the old plan:**
- **HSMR / SKEL** stays on the table as a **parallel branch**, not a downstream stage. Use cases:
  1. **Rollup sequencing** — SKEL's 46-DoF spine tree is still the right tool for per-segment rollup analysis. OpenCap Monocular's lower-limb emphasis doesn't give us that spine detail.
  2. **Joint-limit validation** — HSMR guarantees 0% joint-limit violations. Layer it as a sanity check on WHAM's SMPL output and flag frames where they diverge significantly.
- **MediaPipe on-device** stays as the capture layer + free tier.

### Multi-model strategy — when is ensembling worth it?

Three useful multi-model patterns emerge:

1. **Sequential (same signal, refined):** `MediaPipe 2D → WHAM 3D → OpenCap-Mono optimization`. This is not an ensemble; each stage consumes the previous. Already the plan.
2. **Per-movement dispatch:** different movements route to different model stacks.
   - Overhead squat / single-leg squat / push-up → WHAM + OpenCap-Monocular (kinetics-led).
   - Rollup → HSMR (spine-detail-led) + phase segmentation.
   - Beighton / hypermobility screen → MediaPipe + Sabo classifier.
   - This maps directly onto our `MovementType`-dispatched pipeline in `pipeline/orchestrator.py`.
3. **Parallel redundancy (cross-check):** run two models on the same clip and flag disagreements. Worth doing only on a sample — e.g., run HSMR on key frames of squat captures to validate WHAM's joint angles. Does **not** belong in the hot path.

Skip true ensembling (averaging outputs of multiple 3D lifters). The gains are small and the latency + cost doubles.

### Phone-viable models — ranked for the mobile teammate

| Rank | Model | Params | Runtime on phone | Ship status | Notes |
|---|---|---|---|---|---|
| 1 | **MediaPipe BlazePose (Full / Heavy)** | ~5–10M | ~30–50 ms/frame | Ship now | Flutter plugin; tested; already the plan of record. Use `full` variant by default. |
| 2 | **MoveNet Thunder (TF Lite)** | ~13M | ~25–50 ms | Ship now | Google alternative with slightly better accuracy on fast motion; single-person only. Worth benchmarking vs BlazePose on squat video. |
| 3 | **HRPose / HRNet-small (TF Lite or ONNX Runtime Mobile)** | ~9–13M | ~80–150 ms | Medium effort | Better accuracy on dynamic/occluded movements (research-report §1.4). Premium mid-tier phone upgrade path. |
| 4 | **ViTPose-S (quantized, ONNX Runtime Mobile)** | ~15M | ~100–200 ms (estimated) | High effort | No upstream mobile build; we'd own the quantization work. Defer unless MediaPipe proves inadequate. |
| 5 | **WHAM / OpenCap Monocular / HSMR** | 10–100M+ | ❌ cloud only | Do not ship | All remain server-side. Phone's job is capture + basic angle flags. |

**Bottom line for the phone teammate:** ship **MediaPipe BlazePose (Full)** as the baseline, keep the client capture-agnostic (upload 2D keypoint streams + raw video chunks to the server), and leave slots for MoveNet and HRPose behind the same capture interface so we can swap models without a new app release.

### Datasets available for fine-tuning

| Dataset | Size | License | Directly useful for | Access |
|---|---|---|---|---|
| **Human3.6M** | 3.6M frames, 11 subjects, 17 action types | Academic, requires registration | 3D lift model fine-tuning (TCPFormer / MotionBERT / WHAM variants). **Not movement-screening specific.** | vision.imar.ro/human3.6m |
| **AMASS** | 15M+ frames, 300+ subjects, 400+ motions | CC BY-NC 4.0 (non-commercial) | WHAM retraining / contact-label augmentation. Rich ADL coverage. **Non-commercial blocks future productization.** | amass.is.tue.mpg.de |
| **3DPW** | 60k frames, in-the-wild | CC BY 4.0 | Monocular robustness evaluation. | virtualhumans.mpi-inf.mpg.de/3DPW |
| **MPI-INF-3DHP** | 1.3M frames, 8 subjects, outdoor+indoor | Academic | 3D lift fine-tuning. | vcai.mpi-inf.mpg.de/3dhp-dataset |
| **BEDLAM** | 380k synthetic frames, 271 subjects | CC BY 4.0 | WHAM-family pretraining / augmentation with clean ground truth. | bedlam.is.tue.mpg.de |
| **COCO Keypoints** | 200k images, 1.5M keypoints | CC BY 4.0 | 2D pose model fine-tuning (ViTPose-S, MediaPipe would require Google pipeline). | cocodataset.org |
| **MPII Human Pose** | 25k images, 40k people | Academic (permissive) | 2D pose. | human-pose.mpi-inf.mpg.de |
| **OpenCap dataset** | 100+ subjects, marker mocap + smartphone video + force plates | Data-use agreement | **Gold standard for us.** This *is* the target distribution for movement-screening dynamics. Same team as OpenCap Monocular. | simtk.org/projects/opencap |
| **MOYO** | Extreme yoga poses, 3D mocap | Research | Joint-limit stress testing (where HSMR wins). | moyo.is.tue.mpg.de |
| **Fit3D / AIFit** | Fitness video + 3D pose | Academic | Fine-tuning for squat / lunge / plank variants. | fit3d.imar.ro |

**Priority acquisitions for our use case:**
1. **OpenCap dataset** — closest distribution match. Request via SimTK.
2. **Fit3D / AIFit** — fitness-specific movements (squats, lunges). Covers the weakest gap: OpenCap has walking/STS, not full movement-screening protocols.
3. **AMASS subset (non-commercial research use)** — sanity benchmark for rollup and continuous movements.
4. **Our own captures** — this is the one that actually matters. See "self-collected data" below.

### Self-collected data plan (the only way to fine-tune for *our* protocol)

No public dataset covers our exact 4-movement screening protocol with the ground truth we'd need for rule calibration. We will need to collect our own. Minimum viable:
- 4 movements × 5 reps × N subjects, with:
  - Synchronized smartphone video (pose)
  - At least one gold-standard comparator on a subset (force plates, marker mocap, or clinical assessment by a PT)
  - Intake form: age, sex, height, weight, hypermobility (Beighton self-report)
- N for a first calibration pass: 20–30 subjects spanning age, sex, hypermobility status. This is capstone-scale feasible.
- For premium model post-training (learned chain reasoner / threshold model): N=100+ over 6–12 months post-launch. Not in scope for the capstone.

### Contradictions with `docs/operations/comms/research-integration-report.md`

1. **Pipeline choice (§2.4).** The report recommends MotionBERT + HSMR as the 2D-lift → skeleton path. **This review recommends WHAM + OpenCap Monocular instead**, with HSMR kept as a parallel branch for rollup/spine detail. Reasoning above.
2. **"Server infra, Python/PyTorch" (§6.3).** Still correct, but now points at OpenCap's existing Python stack rather than a custom MotionBERT+HSMR assembly. Less code to own.
3. **"Graph NN chain reasoning requires labeled training data" (§6.3).** Still true. But OpenCap Monocular gives us kinetics outputs we can feed directly into rule-based reasoning today; GNN is deferrable.
4. **§7.1 rollup phase segmentation.** OpenCap Monocular does not solve rollup. HSMR + a custom phase segmenter remains the plan for that movement.

### Section 9 gap status (Papers to Acquire)

| Paper | Status after this review |
|---|---|
| MotionBERT (Zhu 2023) | **Still not acquired.** Low priority if we commit to the WHAM/OpenCap Monocular path. |
| "Real time action scoring system" Sci Rep 2025 | Still not acquired. Needed for Plan 3 DTW/NCC ground truth. |
| Beighton video scoring (Sabo 2026) | ✅ Acquired (this batch). |
| Sahrmann MSI framework | ✅ Partial — we now have Sahrmann 2017 + 2021, Van Dillen 2016 RCT, Harris-Hayes 2016/2018, Joyce 2023 critique. See biomech deep-read for what this buys us. |
| Lumbar-pelvic rhythm studies | Still not acquired. |
| TCPFormer | ✅ Acquired (this batch). No code yet — not actionable. |
| Enhanced Action Quality Assessment ECCV 2024 | Still not acquired. |
| **OpenCap database** | ✅ **Effectively acquired** — we now have OpenCap (Uhlrich 2023), OpenCap Monocular (Gilon 2026), Hybrid ML+Sim (Miller 2025), WHAM (the backbone), and best-practices.html. This was the biggest gap and it's now filled. |
| FMS/SFMA spine criteria | Still not acquired. |

**Newly acquired, not in Section 9:**
- **WHAM (Shin 2024)** — turned out to be critical; it's the backbone of OpenCap Monocular.
- **Rajagopal 2016** — the MSK model under OpenCap.
- **ViTPose (Xu 2022)** — useful as a mid-tier 2D option.
- **Uhlrich 2022 muscle coordination retraining** — relevant for the EMG biofeedback layer the hardware team is building.

---

*Generated 2026-04-10 from agent deep-read of 8 sensing papers.*
