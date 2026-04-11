# ML Model License Audit — 2026-04-11

**Verification method.** GitHub LICENSE files fetched directly via `gh api` (authoritative, high confidence). Non-GitHub hosts (MPI project pages, opencap.ai, simtk.org, ai.google.dev) were not reachable from this sandbox — those entries are flagged "could not verify directly" and lean on text pulled from the OpenCap-Monocular README, which itself summarizes the third-party licensing burden.

## Per-model license table

| Model | License | Commercial OK? | Source URL | Confidence | Notes |
|---|---|---|---|---|---|
| WHAM (code) | MIT | Yes (code only) | https://raw.githubusercontent.com/yohanshin/WHAM/main/LICENSE | High | Code is MIT — "Permission is hereby granted, free of charge... including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell". BUT WHAM depends at inference time on SMPL body models, which are non-commercial (see SMPL row). WHAM README: "To download SMPL body models... you need to register for SMPL and SMPLify." |
| WHAM (pretrained checkpoints / AMASS-trained weights) | De facto non-commercial (inherited from AMASS + SMPL) | No — conditional | https://github.com/yohanshin/WHAM (README, "Training" section) | Medium | README: "WHAM training involves into two different stages; (1) 2D to SMPL lifting through AMASS dataset...". AMASS is CC BY-NC 4.0 (could not fetch license page directly, but this is the documented public record). Using a network trained on CC-BY-NC data for commercial output is legally unsettled — treat as a blocker until an IP lawyer clears it. |
| OpenCap Core | Apache 2.0 | Yes | https://raw.githubusercontent.com/opencap-org/opencap-core/main/LICENSE | High | Standard Apache 2.0. The code itself is commercially usable. The repo was recently moved from `stanfordnmbl/opencap-core` to `opencap-org/opencap-core` (GitHub redirected). README does caveat that the hosted service at opencap.ai is "freely available for academic research use" — that restriction applies to the cloud service, not the code. |
| OpenCap Monocular | **PolyForm Noncommercial 1.0.0** | **No** | https://raw.githubusercontent.com/utahmobl/opencap-monocular/main/LICENSE | High | README: "This project is licensed under the PolyForm Noncommercial License 1.0.0 — **non-commercial use only**. Commercial use requires a separate agreement. Contact the authors for inquiries." Pipeline step 2 is "WHAM 3D pose estimation" — it bundles/depends on WHAM weights and SMPL at inference. |
| opencap.ai hosted service | Research-only (per README statement; formal ToS not verified) | No (for commercial) | https://github.com/opencap-org/opencap-core (README §1) | Medium | opencap-core README, describing app.opencap.ai: "We are running the pipeline in the cloud; this service is freely available for academic research use." Could not fetch opencap.ai/terms directly from this sandbox — recommend manual confirmation before any product decision. |
| AMASS dataset | CC BY-NC 4.0 (widely documented; license page not fetched) | No | https://amass.is.tue.mpg.de/license.html (not fetched) | Medium | CC BY-NC 4.0 is the public record — the "NC" clause prohibits commercial use of the dataset or of derivatives "primarily intended for or directed toward commercial advantage". Applies transitively to WHAM's pretrained weights (trained on AMASS). Could not fetch the MPI page from this sandbox — flag for manual verification. |
| HSMR (Xia et al. CVPR 2025) | MIT | Yes (code only) | https://raw.githubusercontent.com/IsshikiHugh/HSMR/main/LICENSE | High | Code: MIT ("Copyright (c) 2024 Yan XIA ... rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell"). BUT HSMR builds on SKEL, which is SMPL-family and non-commercial. README lists adapted code from SKEL, 4D-Humans, SMPLify-X, SPIN, ProHMR, ViTPose, Detectron2, GVHMR — the model weights / body model dependency is the blocker, not the code. |
| MotionBERT | Apache 2.0 | Yes | https://raw.githubusercontent.com/Walter0807/MotionBERT/main/LICENSE | High | Standard Apache 2.0. Note: downstream checkpoints trained on Human3.6M (academic-only dataset) may carry inherited restrictions — check the specific checkpoint you plan to ship. |
| MediaPipe Pose Landmarker (code) | Apache 2.0 | Yes | https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/LICENSE | High | MediaPipe repo is Apache 2.0. |
| MediaPipe Pose Landmarker (`.task` model file) | Could not verify directly | Likely yes (per Google ML Kit / MediaPipe model terms, widely used commercially) | https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker (not fetched) | Medium | Google's published MediaPipe solutions are distributed for commercial use per their Model Terms, but this sandbox could not fetch the model card. Flag for manual verification before shipping — confirm on the model card page that the specific `.task` file has no additional restrictions. |
| Rajagopal 2016 MSK model (simtk.org) | Could not verify directly | Likely permissive (OpenSim-model convention), but unconfirmed | https://simtk.org/projects/full_body (not fetched) | Low | simtk.org is outside the sandbox allowlist. OpenSim musculoskeletal models on simtk.org are typically distributed under a non-viral academic-friendly license, but the Rajagopal model's specific terms must be confirmed manually. Do NOT assume Apache 2.0 just because OpenSim core is. |
| OpenSim (core) | Apache 2.0 | Yes | https://raw.githubusercontent.com/opensim-org/opensim-core/main/LICENSE.txt | High | Confirmed Apache 2.0. |
| ViTPose | Apache 2.0 | Yes | https://raw.githubusercontent.com/ViTAE-Transformer/ViTPose/main/LICENSE | High | Standard Apache 2.0. Note: some ViTPose checkpoints were trained on MS COCO (CC BY 4.0) and MPII (for research only) — check the specific checkpoint you ship. |
| SMPL / SMPL-X body models (dependency of WHAM, OpenCap-Monocular, HSMR) | Max Planck Non-Commercial Research License | **No** | https://smpl.is.tue.mpg.de/modellicense (not fetched; quoted from OpenCap-Monocular README) | High | OpenCap-Monocular README verbatim: "The SMPL body models required by this pipeline are licensed by the Max Planck Institute for non-commercial scientific research only... For commercial SMPL licensing, contact ps-license@tue.mpg.de." This is the single biggest blocker in the stack. |

## Critical question 1: Can the WHAM + OpenCap Monocular pipeline be used in a paid product?

**No — not without two commercial licenses from Max Planck.**

The blockers, in order:

1. **OpenCap Monocular itself is PolyForm Noncommercial 1.0.0.** Verbatim from the repo README: "non-commercial use only. Commercial use requires a separate agreement." That alone is dispositive — you cannot ship the OpenCap Monocular pipeline in a paid product without contacting the University of Utah MoBL group for a commercial agreement.

2. **SMPL body model is Max Planck Non-Commercial.** Even if OpenCap Monocular relicensed its own code, the pipeline calls SMPL at inference time. MPI's license is "non-commercial scientific research only". Commercial use requires a separate paid license from `ps-license@tue.mpg.de`.

3. **WHAM pretrained weights inherit AMASS's CC BY-NC 4.0.** The code is MIT and technically clean, but the distributed checkpoints were trained on AMASS. Using CC-BY-NC-derived model weights in a commercial product is legally unsettled and would, at minimum, require retraining from scratch on a clean dataset.

Net: three independent non-commercial licenses stack on this pipeline. It is a research-only artifact and should be treated as such for the capstone.

## Critical question 2: If WHAM is the blocker, what commercial-friendly alternatives exist for monocular world-grounded 3D pose?

The real blocker is SMPL + AMASS, not WHAM specifically. Any SMPL-based method inherits the same problem. Commercial-friendly options:

1. **MediaPipe Pose Landmarker (Google).** Apache 2.0 code, Google ML Kit model terms on the `.task` file (widely shipped in commercial mobile apps). 3D landmarks in a rooted-pelvis coordinate frame — not true world-grounded, but usable for most motion-analysis and rep-counting use cases. **Accuracy tradeoff: significantly worse than WHAM on 3DPW/EMDB benchmarks**, but the only truly clean option with a production-grade runtime. Recommend as default.

2. **MotionBERT (Apache 2.0) + a commercial-clean 2D detector.** Code is Apache 2.0. The catch is the weights — the released checkpoints are trained on Human3.6M, which is research-only. A team with budget could retrain MotionBERT on a commercially-licensed 2D+3D dataset (e.g., FIT3D, Fit3D commercial tier, or synthetic data from BEDLAM — BEDLAM itself is released for research only, so watch out). Expect 3–6 months of engineering effort.

3. **ViTPose (Apache 2.0) as a 2D backbone + lift to 3D with custom training.** Same story: clean code, dirty checkpoints. Viable only if you retrain on clean data. Best for teams that already have their own 3D motion capture datasets.

4. **Commercial SDKs (Wrnch/Hinge Health, Sports Data Labs, Kinatrax, Google ML Kit Pose Detection, Apple Vision framework).** If the capstone evolves into a product, the cleanest path is licensing a commercial pose SDK rather than fighting the SMPL license chain. Apple Vision and Google ML Kit are free-for-commercial; Wrnch-class SDKs are paid.

**There is no free, commercial-ready, world-grounded monocular 3D pose estimator with WHAM-level accuracy as of 2026-04-11.** The accuracy/license tradeoff is real and a product decision, not a research decision.

## Critical question 3: Does the opencap.ai hosted service allow commercial use, even if we don't redistribute the models?

**No — per the opencap-core README.**

Verbatim from the official opencap-core README (high confidence, the repo is the canonical source): "We are running the pipeline in the cloud; this service is freely available for academic research use. Visit opencap.ai/get-started to start collecting data."

The phrase "freely available for academic research use" is an explicit scope limitation on the hosted service. Using app.opencap.ai to process videos for a commercial product would violate that scope even if no code or model is redistributed.

**Caveat.** I was not able to fetch opencap.ai/terms directly from this sandbox (non-GitHub hosts blocked). There may be a more formal ToS document with additional clauses (or, less likely, a commercial tier). Before any product decision, manually open https://www.opencap.ai/terms and https://www.opencap.ai/privacy in a browser and confirm.

## Critical question 4: What can the AuraLink team safely build right now without licensing risk?

### Clean for commercial use (ship-ready)

- **MediaPipe Pose Landmarker** — Apache 2.0 code + Google model terms. Production-grade, real-time, mobile-friendly. Recommend as the default for any commercial-path prototype.
- **OpenSim core + OpenCap Core (code)** — both Apache 2.0. Can be bundled into a commercial product as long as you attribute and you don't use MPI body models or opencap.ai hosted processing.
- **ViTPose code, MotionBERT code** — both Apache 2.0. Safe to fork and integrate, but the distributed checkpoints are not safe for commercial deployment without retraining.

### Clean for the academic capstone (research use, not shippable)

- **WHAM, OpenCap Monocular, HSMR, AMASS** — all usable for a university capstone under their research/non-commercial terms. Fine for the demo, the writeup, the defense, and the academic paper. **Not** fine for spinning the project out into a paid product without renegotiating licenses.
- **SMPL / SMPL-X body models** — free for the capstone under the MPI non-commercial research license. Register, accept the terms, use for academic work.
- **Rajagopal MSK model** — likely fine for academic use (this is the standard convention for simtk.org biomechanics models), but confirm on simtk.org before relying on it.

### Blocked for commercial use

- **OpenCap Monocular** — PolyForm Noncommercial. Hard blocker.
- **SMPL / SMPL-X** — MPI non-commercial. Hard blocker. Cascades into any SMPL-based method (WHAM, HSMR, 4D-Humans, SLAHMR, SMPLify-X, most of the CVPR 3D-human-reconstruction literature).
- **AMASS-trained weights** (including WHAM's distributed checkpoints) — CC BY-NC 4.0 transitively. Hard blocker for the weights; code is fine.
- **opencap.ai hosted service** — academic research use only per README.
- **Human3.6M-trained checkpoints** (including stock MotionBERT weights) — research only.

### Action items for AuraLink

1. **Capstone demo: use WHAM + OpenCap Monocular.** Good accuracy, fully covered by academic use. Document the license chain in the project writeup so reviewers see you understand it.
2. **Any commercial pivot: switch to MediaPipe Pose Landmarker** as the baseline, accept the accuracy drop, and evaluate whether a commercial pose SDK is worth budgeting for.
3. **Before the final defense**, manually verify these four items that this sandbox could not reach: (a) opencap.ai/terms formal ToS, (b) amass.is.tue.mpg.de/license.html exact CC BY-NC 4.0 text, (c) simtk.org Rajagopal 2016 model license, (d) ai.google.dev MediaPipe Pose Landmarker model card terms. All four are reachable from a normal browser.
4. **Do not ship a product that depends on SMPL without a commercial license from `ps-license@tue.mpg.de`.** MPI does license SMPL commercially — budget for it if the product path is real.

## Verification gaps (be honest)

Four license pages could not be fetched directly from this sandbox (non-GitHub hosts blocked by outbound network policy):

- https://wham.is.tue.mpg.de/ — WHAM project page, for any model-weights license statement beyond the MIT code license
- https://amass.is.tue.mpg.de/license.html — AMASS formal CC BY-NC 4.0 text
- https://www.opencap.ai/terms — opencap.ai formal Terms of Service
- https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker — MediaPipe Pose Landmarker model card / model terms
- https://simtk.org/projects/full_body — Rajagopal 2016 MSK model license

The headline conclusions (OpenCap Monocular = PolyForm NC, SMPL = MPI non-commercial, WHAM code = MIT, OpenCap Core = Apache 2.0, ViTPose/MotionBERT/OpenSim/MediaPipe code = Apache 2.0, HSMR code = MIT) are all verified from canonical GitHub LICENSE files or from verbatim README text and are high confidence. The cascading-license conclusion (that the WHAM + OpenCap Monocular pipeline is not commercially shippable) is also high confidence because PolyForm NC on OpenCap Monocular is itself dispositive.
