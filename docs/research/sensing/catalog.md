# Sensing & ML Research — File Catalog

**All primary-source pose-estimation / ML-vision PDFs are now canonical in the sibling `research/` repo** (migrated 2026-04-15). This directory retains:

- HTML developer/vendor references that support engineering decisions in this repo.
- Two arxiv-paper HTML captures (2506.html, 2602.html) that are pending re-intake as PDFs into the research repo.
- `research-gaps.md` and `verification-results.md` — engineering-facing hand-authored notes.
- `ML.json` — Zotero CSL-JSON bibliography export (kept for Zotero-side workflows; the research repo regenerates its own bibliography).

## Where the papers live

Every PDF formerly in this directory now has a citekey, full frontmatter, and a stub synopsis in `research/sensing/` (sibling repo). Look up papers by author/year via `research/indexes/by-author.md` or `research/indexes/by-year.md`, or via the regenerated `research/bibliography/bibliography.json`.

Engineering-relevant papers to know (all in the research repo now):

- **HSMR** — `xia2025-reconstructing-humans-with-a-biomechanically-accurate-skeleton` — SKEL-based 3D lifter used for rollup spine sequencing.
- **MediaPipe joint moments** — `akturk2026-markerless-joint-angle-estimation-using-mediapipe-with-a` — Hip R=0.94, Knee R=0.95, Ankle R=0.11 single-phone baseline.
- **MediaPipe ergonomic risk** — `singhtaun2024-ergonomic-risk-assessment-using-human-pose-estimation-with` — 90% controlled → 70% real-world setup-quality degradation.
- **OpenCap** — `uhlrich2023-opencap-human-movement-dynamics-from-smartphone-videos` — multi-camera smartphone kinematics + kinetics reference.
- **OpenCap Monocular** — `gilon2026-opencap-monocular-3d-human-kinematics-and-musculoskeletal` — single-camera extension (the one that reshaped the pipeline decision).
- **Hybrid ML + sim** — `miller2025-integrating-machine-learning-with-musculoskeletal` — justification for not ensembling 3D lifters.
- **WHAM** — `shin2024-wham-reconstructing-world-grounded-humans-with-accurate-3d` — world-grounded 3D pose, OpenCap Monocular's backbone.
- **Sabo Beighton** — `sabo2026-development-and-evaluation-of-a-vision-pose-tracking-based` — premium hypermobility screen.
- **TCPFormer** — `liu2025-tcpformer-learning-temporal-correlation-with-implicit-pose` — watch for code release.
- **ViTPose** — `xu2022-vitpose-simple-vision-transformer-baselines-for-human-pose` — candidate 2D backbone.
- **Real-time review** — `chen2025-real-time-human-pose-estimation-and-tracking-on-monocular` — adaptive-tier selection guide.

## Web references retained here (engineering decisions, not primary research)

| File | Source | Purpose |
|------|--------|---------|
| `best-practices.html` | OpenCap docs | Capture setup protocol for OpenCap-based workflows |
| `best-pose-estimation-models.html` | Roboflow | Model-comparison and deployment guide |
| `human-pose-estimation-technology-guide.html` | MobiDev | Fitness/sports-app architecture guide |
| `android-sdk.html` | QuickPose.ai | Competitor/integration reference for Android pose SDKs |
| `unity-isdk-body-pose-detection.html` | Meta ISDK | VR/AR body-pose detection (tangential, kept for reference) |
| `Mediapipe-Poses-position-detection-of-33-posture-joints-*.html` | ResearchGate figure | MediaPipe 33-landmark visualization |

## Pending re-intake into research repo

These are papers saved as HTML. They need to be re-intaked as proper paper entries in the research repo — ideally by downloading the PDF from arxiv, running the intake playbook, and linking back. Left here as a tracking reminder.

| File | Identification | Action |
|------|----------------|--------|
| `2506.html` | arxiv:2506.18368v1 — "Sequential keypoint density estimator: an overlooked baseline of skeleton-based video anomaly detection" | Re-download as PDF, intake into `research/sensing/` |
| `2602.html` | arxiv:2602.23231v1 — "Skarimva: Skeleton-based Action Recognition is a Multi-view Application" | Re-download as PDF, intake into `research/sensing/` |

## Internal engineering notes (stay here)

| File | Purpose |
|------|---------|
| `ML.json` | Zotero CSL-JSON export (kept for Zotero-side workflows) |
| `research-gaps.md` | Engineering-facing hardware claim audit |
| `verification-results.md` | Source verification notes (Merletti, Jiang, Kalichman) |

## Historical research-gap notes

The three-gap analysis (2D-to-3D lifting, temporal/sequence models, body composition/anthropometry) that used to live here has been superseded by the pipeline-architecture-decision doc and the paired monocular-pipeline-landscape literature synthesis. See:

- `../pipeline-architecture-decision-2026-04-10.md` (this repo, engineering decision)
- `research/synthesis/deep-read-monocular-pipeline-landscape-2026-04-10.md` (sibling repo, literature synthesis)
