# Body-Understanding Models — Showcase Slide Source
**Date:** 2026-04-22
**Audience:** Showcase Thu 2026-04-23 (10 min, 4 people)
**Purpose:** Source material for the "what's beyond BlazePose" slide. Licenses are non-commercial research unless noted — fine for a slide, NOT clean for shipping.

## Baseline
**MediaPipe BlazePose Full** — 33 keypoints, on-device, Apache 2.0 + Google ML Kit terms. What we ship today. Commercial-clean.

## Candidates (ranked by slide punch)

### 1. Sapiens (Meta, ECCV 2024) — biggest numeric punch
One foundation model pretrained on 300M humans: **308 keypoints** (25 body + 40 hands + 243 face), **28-class body-part segmentation**, depth, surface normals. Native 1024×1024.

One-liner: *"Grip, grimace, and scap — the 275 landmarks BlazePose doesn't have."*

License: weights CC-BY-NC 4.0 (non-commercial). Repo: `facebookresearch/sapiens`.

### 2. NLF — Neural Localizer Fields (Sárándi & Pons-Moll, NeurIPS 2024) — biggest conceptual punch
Continuous 3D point queries on the body. No fixed keypoint set — ask for a vertebra, a muscle belly, a tendon insertion, get 3D coords.

One-liner: *"Ask the body anywhere: pelvic tilt, T-spine, malleoli — no fixed keypoint set."*

License: code + weights non-commercial research only. Repo: `isarandi/nlf`.

### 3. SKEL + HSMR (SIGGRAPH Asia 2023 + CVPR 2025) — biggest visual punch
Anatomical skeleton from video: **24 bones, 46 anatomical DoFs**, biomechanically valid joint limits, ribcage + pelvis + femur from monocular RGB. HSMR (2025) is the video→SKEL regressor.

**Spine reality check:** BSM spine is **3 articulated segments** (lumbar / thorax / head), NOT 24 individual vertebrae. No commercial-ish RGB-only model gives per-vertebra landmarks — that's still a CT/MRI problem.

One-liner: *"Score the rollup. Score the Thomas test. Score mobility the way a PT grades it — from bones, not skin."*

License: CC-BY-NC-SA 4.0 (non-commercial). Repo: `MarilynKeller/SKEL`.

### Skipped / de-prioritized
- **OSSO (CVPR 2022):** superseded by SKEL, no video pipeline.
- **DensePose (2018):** Sapiens' segmentation + normals + depth is the modern "every pixel" story.
- **WHAM / TRAM / 4D-Humans:** eclipsed by **GVHMR (SIGGRAPH Asia 2024)** for the world-grounded slide if that angle is needed.
- **SMPLer-X / SMPLest-X:** whole-body SMPL-X, ~144 joints — narrative-adjacent to Sapiens, weaker punch.

## Exercise → unique insight mapping

### Sapiens — 308 landmarks + segmentation + depth + normals

| Exercise | What BlazePose misses | Sapiens advantage |
|---|---|---|
| Deadlift / kettlebell swing | Grip width, wrist neutrality, bar path | 40 hand landmarks catch broken wrist and uneven grip before they become low-back strain |
| Bench press setup | Scapular retraction ("tuck") | 28-class segmentation shows scap position directly; BlazePose shoulder point sits on skin, not scapula |
| Turkish get-up / loaded carries | Face/grimace — strain signal | 243 face landmarks detect Valsalva, jaw clench, breath-holding — early fatigue signal BlazePose is blind to |
| Any exercise in loose clothing (hoodie, baggy shirt) | Joints hidden under fabric | Surface normals + segmentation recover body shape through clothing occlusion |

### NLF — query any 3D point on the body

| Exercise | What BlazePose misses | NLF advantage |
|---|---|---|
| Hip hinge (RDL, good-morning, kettlebell DL) | Pelvic tilt — BlazePose has only a hip *center* | Query ASIS + PSIS → real pelvic tilt angle (the actual thing that fails in hip hinge) |
| Overhead squat (assessment gold standard) | Thoracic extension — no mid-back point | Query T4/T8 → separate thoracic contribution from shoulder flexion |
| Squat depth | "Hip below parallel" proxied from skin landmark | Query greater trochanter vs knee joint center → true femoral depth |
| Single-leg squat / balance | Ankle point drifts with shoe/sock | Query medial + lateral malleoli → real ankle axis for frontal-plane sway |

### SKEL / HSMR — anatomical skeleton, biomech joint limits

| Exercise | What BlazePose misses | SKEL/HSMR advantage |
|---|---|---|
| Bicep curl (current demo) | Elbow angle drifts 10–20° with forearm pronation | True elbow flexion from bone, not skin — addresses a known weakness in the 4/20 demo |
| Shoulder mobility (wall slide, Apley scratch) | Scapulohumeral rhythm — scapula invisible | Actual scapula pose; separates GH from ST contribution |
| Ankle dorsiflexion (knee-to-wall) | Talocrural angle proxied from foot-shin skin | Real talocrural; distinguishes stiff ankle from stiff calf |
| Rollup / segmental spine articulation | Spine is 1 point (mid-torso) | 3-segment spine (lumbar / thorax / head) — only model that can score rollup's segmental unfolding |
| Hip IR/ER (Thomas test, 90/90) | Conflates femoral + tibial rotation | Femur and tibia are separate rigid bodies — the test can actually be scored |

## Recommendation for the slide

**Lead with SKEL/HSMR + the rollup example.** Rationale:

1. Rollup is already in the post-showcase roadmap — it's *our own* next move, not a hypothetical.
2. It's the one movement where BlazePose's single-point spine catastrophically fails, and the failure is obvious to a layperson ("your spine is one dot").
3. It builds the narrative bridge: *"BlazePose today (commercial-clean) → anatomical skeleton tomorrow → justifies the 3D-lift / biomech spend already priced at $70k–$600k."*

Alternate leads:
- **Sapiens** if the audience is more product/UX oriented — the 33→308 comparison is immediately legible.
- **NLF** if the audience is ML-sophisticated — reframes the problem ("the body is a continuous field, not a keypoint set").

All three are research-licensed, which honestly reinforces the investor-defensibility story: BlazePose is what we ship today (clean), these are the frontier, which is why 3D-lift/biomech is priced post-showcase.

## Sources
- [SKEL project](https://skel.is.tue.mpg.de/) · [SKEL GitHub](https://github.com/MarilynKeller/SKEL)
- [HSMR (CVPR 2025)](https://arxiv.org/abs/2503.21751)
- [OSSO (CVPR 2022)](https://arxiv.org/abs/2204.10129)
- [NLF (NeurIPS 2024)](https://arxiv.org/abs/2407.07532) · [NLF GitHub](https://github.com/isarandi/nlf)
- [SMPLer-X (NeurIPS 2023)](https://arxiv.org/abs/2309.17448) · [SMPLest-X (2025)](https://arxiv.org/abs/2501.09782)
- [WHAM (CVPR 2024)](https://wham.is.tue.mpg.de/) · [GVHMR (SIGGRAPH Asia 2024)](https://zju3dv.github.io/gvhmr/)
- [Sapiens (ECCV 2024)](https://arxiv.org/abs/2408.12569) · [Sapiens GitHub](https://github.com/facebookresearch/sapiens)
- [DensePose](http://densepose.org/)
