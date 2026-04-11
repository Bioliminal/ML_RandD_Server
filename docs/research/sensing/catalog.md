# Sensing & ML Research — File Catalog

## Product Tier Architecture

| Tier | Runtime | Model | Output |
|------|---------|-------|--------|
| Free (any phone) | On-device | MediaPipe BlazePose → joint angles → rule-based chain logic | Basic movement screen, joint angle flags, simple chain attribution |
| Mid (capable phone) | On-device | HRPose or YOLO-Pose → better keypoints → chain logic | More accurate keypoints in dynamic movements, better confidence |
| Premium (server) | Server-side | HSMR (SKEL model) → biomechanical skeleton → full chain analysis | True joint DOF, spine detail, impossible-rotation filtering, detailed report |

## Academic Papers (PDFs)

### High Priority — Direct Product Impact

| File | Topic | ML.json | Tier | Key Finding |
|------|-------|---------|------|-------------|
| `biomechanically-accurate-skeleton.pdf` | HSMR: biomechanically accurate skeleton from single image | 343–371 | Premium | SKEL: 46 DOF (vs SMPL 72), 0% joint violations (vs 20-56% in SMPL methods), 18.8mm better on extreme poses. Single-image input. **Spine answer.** |
| `markerless-mediapipe-joint-moments.pdf` | MediaPipe joint angle + moment calculation | 847–893 | Free | Hip R=0.94, Knee R=0.95, Ankle R=0.11. Inverse dynamics from single phone camera. **Accuracy floor.** |
| `ergonomic-risk-mediapipe.pdf` | MediaPipe posture risk classification (OWAS) | 480–526 | Free | 90% controlled → 70% real-world. **20% degradation factor from setup quality.** |
| `pose-recognition-rehab-scoring.pdf` | BlazePose + Random Forest + Siamese scoring | 214–258 | Free | 98% pose recognition, <6% joint angle error, 92-98% scoring correlation. **Proven lightweight pipeline.** |
| `dynamic-pose-estimation-hrpose.pdf` | HRNet + SinglePose AI for sports | *not in ML.json* | Mid | Best for fast/dynamic movements. Heavier but significantly more accurate under occlusion/speed. |
| `vision-sensors-markerless-motion-review.pdf` | Commercial sensors & AI frameworks review | 153–213 | All | Compares OpenPose, MediaPipe, AlphaPose, DensePose. 2D-to-3D lifting discussion. **Framework selection guide.** |

### Medium Priority — Architecture & Training Reference

| File | Topic | ML.json | Tier | Key Finding |
|------|-------|---------|------|-------------|
| `realtime-pose-estimation-review.pdf` | Systematic review: 68 papers on real-time pose | 910–963 | Free/Mid | Accuracy-efficiency tradeoffs, hardware configs. **Adaptive tier selection guide.** |
| `deep-learning-pose-estimation-survey.pdf` | Survey: 2D/3D pose estimation methods | 259–310 | All | Benchmark tables, dataset comparison, evaluation metrics. **Training data selection.** |
| `graph-network-skeleton-survey.pdf` | Graph networks for skeleton modeling | 662–714 | Premium | Models skeleton as connected system (not independent joints). **Maps to chain reasoning math.** |
| `multi-view-gait-database.pdf` | Multi-view mesh estimation framework | 715–753 | Premium | Train on multi-view, deploy on single-view. Full parametric shape+pose. |
| `kinematic-skeleton-extraction-3d.pdf` | 3D point cloud skeleton, 37 segments, 20 joints | 802–845 | Premium | 22.82mm MPJPE, robust under occlusion. Validation/training resource. |
| `enhanced-skeleton-tracking-rehab.pdf` | Dual-camera depth correction for rehab | 2–61 | Mid/Premium | 0.4m depth error reduction. "Film from two angles" workflow feasible. |
| `pose-estimation-joint-angle-deep-learning.pdf` | YOLO8n + 25 keypoints for physio | 89–152 | Mid | Custom skeleton for physio. mAP@50=0.58 (low). Joint angle computation pipeline reference. |

### Low Priority — Niche or Tangential

| File | Topic | ML.json | Tier | Note |
|------|-------|---------|------|------|
| `skeleton-integrity-pose-fine-tuning.pdf` | Frame selection for model fine-tuning | 585–643 | — | Only relevant if fine-tuning own model. Method is domain-agnostic despite pig study. |

### Added 2026-04-10 (from unsorted/)

| File | Topic | Tier | Key Finding |
|------|-------|------|-------------|
| `Uhlrich et al. - 2023 - OpenCap Human movement dynamics from smartphone videos.pdf` | OpenCap: open-source kinematics + kinetics from 2 smartphone videos | Premium | Pose estimation → biomechanical model → physics-based simulation. **Reference architecture for server-side pipeline.** Stanford/Delp lab. |
| `Gilon et al. - 2026 - OpenCap Monocular 3D Human Kinematics and Musculoskeletal Dynamics from a Single Smartphone Video.pdf` | Single-video extension of OpenCap | Premium | WHAM pose + optimization + physics+ML kinetics. 4.8° MAE rotational, 3.4 cm pelvis translation. **48%/69% better than CV-only baseline.** Single-phone path to dynamics. |
| `Miller et al. - 2025 - Integrating Machine Learning with Musculoskeletal Simulation Improves OpenCap Video-Based Dynamics E.pdf` | Hybrid ML + physics for OpenCap dynamics | Premium | Improves GRF, joint moments, joint contact forces from smartphone video kinematics. **Direct premium-tier pipeline reference.** |
| `Shin et al. - 2024 - WHAM Reconstructing World-Grounded Humans with Accurate 3D Motion.pdf` | World-grounded 3D human motion recovery | Premium | Handles moving cameras without foot sliding. CVPR 2024. **Backbone used by OpenCap Monocular.** |
| `Liu et al. - 2025 - TCPFormer Learning Temporal Correlation with Implicit Pose Proxy for 3D Human Pose Estimation.pdf` | SOTA multi-frame 3D lifting | Mid/Premium | Implicit pose proxy for temporal correlation. Outperforms MotionBERT on Human3.6M. **Watch for code release.** |
| `Xu et al. - 2022 - ViTPose Simple Vision Transformer Baselines for Human Pose Estimation.pdf` | Plain-ViT 2D keypoint baseline | Mid | 80.9 AP MS COCO, scalable 100M–1B params. **Candidate 2D backbone.** |
| `Sabo et al. - 2026 - Development and evaluation of a vision pose-tracking based Beighton score tool for generalized joint.pdf` | Video-based Beighton hypermobility screen | Premium | 91.9% sensitivity, 42.4% specificity, n=125. **Premium hypermobility screening.** (Already cited as PubMed 41639883.) |
| `best-practices.html` | OpenCap capture best-practices web page | — | Reference — setup/data-collection protocol guidance for OpenCap-based capture. |

## Web References (HTML)

| File | Source | Relevance |
|------|--------|-----------|
| `best-pose-estimation-models.html` | Roboflow — model comparison & deployment (ML.json 62–88) | High — framework selection |
| `human-pose-estimation-technology-guide.html` | MobiDev — fitness/sports app guide (ML.json 965–987) | High — product architecture |
| `android-sdk.html` | QuickPose — pose SDK for Android (ML.json 372–389) | Medium — competitor/integration |
| `unity-isdk-body-pose-detection.html` | Meta ISDK body pose (ML.json 311–327) | Low — VR/AR specific |
| `2602.html` | Skarimva — multi-view action recognition (ML.json 328–342) | Low — multi-view only |
| `2506.html` | SeeKer — skeleton anomaly detection (ML.json 895–908) | Low — surveillance domain |
| `Mediapipe-Poses-position-detection-of-33-posture-joints-*.html` | MediaPipe 33-joint diagram (ML.json 644–661) | Reference — landmark map |

## Internal Docs

| File | Purpose |
|------|---------|
| `ML.json` | CSL JSON bibliography (Zotero export) |
| `research-gaps.md` | Hardware claim audit — 7 unbacked claims, 2 critical safety gaps |
| `verification-results.md` | Source verification — Merletti, Jiang, Kalichman confirmed with caveats |

## Research Gaps & Web Research Findings (2026-04-09)

### Gap 1: 2D-to-3D Lifting (single phone → 3D skeleton)

**Status: Solved.** Multiple production-ready options exist.

| Model | MPJPE (mm) | Monocular | License | Notes |
|-------|-----------|-----------|---------|-------|
| MotionBERT (ICCV 2023) | 35.8 | Yes | Apache 2.0 | Proven, widely used. **Start here.** |
| TCPFormer (2025) | 33.5 | Yes | TBD | 12.9% better than MotionBERT. Watch for code release. |
| OPFormer (2025) | 37.6 | Yes | TBD | Part-aware decomposition. |
| VideoPose3D (2019) | ~37-40 | Yes | — | Outdated, not recommended for new work. |
| Pose2Sim | 15-30 | Multi-cam only | Apache 2.0 | **Not viable for single phone.** |

**Recommendation:** MotionBERT for server-side 3D lifting. HSMR/SKEL for premium (biomechanical accuracy > raw MPJPE).

### Gap 2: Temporal/Sequence Models (fatigue/degradation over reps)

**Status: Partially solved.** No off-the-shelf "fatigue meter" but a proven pipeline exists.

- **Best approach (2025):** Joint angle features (ROM, angular velocity) + Dynamic Time Warping (DTW) + Normalized Cross-Correlation (NCC) for temporal alignment across reps. From: "Real time action scoring system for movement analysis and feedback in physical therapy" (Scientific Reports 2025). Outperforms RepNet. Fully reproducible from pose keypoints.
- **ST-GCN family** (MS-G3D, CTR-GCN): Action classification only, not quality tracking. Could be repurposed with temporal regression head.
- **ECCV 2024:** "Enhanced Action Quality Assessment" — dual-stream pose+video for quality regression. Closest to what we need.
- **No existing tool** does per-rep fatigue scoring. Must build: extract angle time-series per rep → compute trend (ROM decrease, velocity decrease, compensation angle increase) → flag degradation.

**Recommendation:** Build custom pipeline: MediaPipe keypoints → joint angle extraction → per-rep DTW alignment → trend analysis. Validated approach from PT literature.

### Gap 3: Body Composition / Anthropometry / Hypermobility

**Status: Partially solved.** Detection works. Threshold adjustment tables don't exist.

- **Beighton score from video (2026):** 91.9% recall for hypermobility positives using pose estimation on elbows, knees, fingers, thumbs, spine. n=225 EDS patients. Viable for premium tier screening.
- **SMPL shape → BMI:** First two principal components capture height/weight. BMnet and STAR models extend this. HSMR/SKEL shape parameters `β` directly encode body proportions.
- **Anthropometric estimation:** 2D pose (MediaPipe/OpenPose) extracts limb lengths reliably. Cross-population limb-to-height ratios enable physique classification.
- **Critical gap: No adjustment tables exist.** Research shows hypermobile individuals have different Q-angles, hip rotation, ankle ROM — but no paper prescribes *how much* to adjust screening thresholds. This is novel territory the product would need to calibrate through its own data collection (aligns with SPOV 4: research instrument first).

**Recommendation:** Use SKEL shape parameters + Beighton screening questions (or video-based detection in premium) to flag likely hypermobility. Apply conservative interpretation (wider "normal" ranges) rather than fixed threshold shifts until own data validates specific adjustments.

### Papers to Acquire for These Gaps

1. MotionBERT — ICCV 2023, Zhu et al. (code: github.com/Walter0807/MotionBERT)
2. "Real time action scoring system for movement analysis" — Scientific Reports 2025 (doi: 10.1038/s41598-025-29062-7)
3. "Enhanced Action Quality Assessment" — ECCV 2024 Workshops
4. Beighton score vision-based assessment — PubMed 41639883 (2026)
5. TCPFormer — arXiv 2501.01770v1 (2025)

## ML.json Entries Without Local Files

- **Lines 391–479**: "Comparative Analysis of ML Models in Predicting Blood Donation Behavior" (2 duplicate entries — unrelated, remove from Zotero)
- **Lines 527–584**: YOLOv8 pose estimation with EMRF/EFPN (no PDF saved)
- **Lines 754–801**: BP-YOLO product detection (unrelated, remove from Zotero)
