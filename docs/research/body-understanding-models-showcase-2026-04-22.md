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

---

## Slide Design — "Bones or density: two paths past BlazePose"

### Why not a live demo
Off the critical path. Both SKEL/HSMR and Sapiens require gated model weights (SMPL at MPI; Sapiens-Lite CC-BY-NC), ~2+ GB downloads, CUDA setup. Work runway Wed PM → Thu 12:00 noon is S1/S2/S3. A static slide is the right artifact.

### Artifacts
- **Primary slide:** `assets/deeper-body-models-slide-2026-04-22.svg` — single 16:9 slide holding both A and B side-by-side, brand-matched.
- **Optional supporting reference (not on slide):** `assets/rollup-spine-comparison-2026-04-22.svg` — rollup-specific BlazePose vs SKEL comparison. Kept as a doc reference diagram; superseded on the slide because "1 → 3 spine segments" undersells SKEL's real value (joint-level anatomical resolution).

### Brand conformance (matched to existing artifacts)

| Element | Source | Value |
|---|---|---|
| Primary ink | `bioliminal-ops/operations/pdf-build/style.css` · Technical Brief cover | `#0A2540` deep navy |
| Accent link blue | same | `#0A5CAD` |
| Body ink | same | `#1F2D3D` / `#445570` muted |
| Background | same, cover-ish | `#FDFDFC` off-white |
| Display face | `bioliminal-mobile-application/assets/fonts/Fraunces-Variable.ttf` | Fraunces (serif, for titles + taglines) |
| Body face | `IBMPlexSans-Variable.ttf` | IBM Plex Sans (bullets, eyebrows, footer) |
| BlazePose dot | this series | `#E76F51` (orange — "today" signal) |
| Sapiens body dots | derived from primary | `#0A2540` body · `#0A5CAD` face · `#38BDF8` hands (Sky 400 ties to mobile app accent) |
| SKEL bone fill | derived | `#F2E8D5` ivory on navy stroke |
| Logo mark | `bioliminal-mobile-application/assets/branding/bioliminal-mark.svg` | inlined bottom-right |

The Technical Brief palette (light, navy) is used because this is a projected outward-facing artifact in the same convention as `technical-brief-v1.pdf`. Mobile Slate-900 dark palette is the product UI, not the outward narrative.

### Slide layout (single 16:9)

```
┌─ top 6px navy strip ─────────────────────────────────────────────┐
│                                                                  │
│  WHAT DEEPER BODY MODELS COULD UNLOCK                            │
│  Bones, or density — two paths past BlazePose.                   │
│  Both research-licensed today. Commercial-clean path already     │
│  priced in the viability matrix.                                 │
│ ─────────────────────────────────────────────────────────────── │
│  OPTION A — SKEL              │  OPTION B — SAPIENS              │
│  Bones, not skin.             │  308 landmarks + per-pixel body. │
│                               │                                  │
│  [split figure: BP dots on    │  [figure: 33 dots] → [figure:    │
│   left half, anatomical       │   308 dots, dense on face/hands] │
│   skeleton on right half]     │  33                    308       │
│                               │                                  │
│  ◆ True elbow from bone —     │  ◆ Grip & wrist neutrality —     │
│    no pronation drift         │    40 hand landmarks             │
│  ◆ Femur vs tibia separable — │  ◆ Scapular tuck via 28-class    │
│    Thomas test scoreable      │    segmentation                  │
│  ◆ Scapula distinct from      │  ◆ Grimace & Valsalva — 243      │
│    humerus — wall slide       │    face landmarks                │
│                               │                                  │
│  Score mobility the way a     │  Hands, face, and the body       │
│  PT grades it.                │  under clothing — seen.          │
│ ─────────────────────────────────────────────────────────────── │
│  Today · BlazePose · 33 · commercial-clean · ships in the app   │
│  Frontier · SKEL & Sapiens · research-licensed · slide only      │
│  Gated on · commercial dataset access — viability matrix    [b] │
└──────────────────────────────────────────────────────────────────┘
```

Everything above is already rendered in the SVG — drop it into a single slide at 16:9 and it's done. No deck-side layout work required.

### Verbal beat (≤ 25 s)

> "Two directions beyond BlazePose. SKEL gives us the skeleton under the skin — elbow angle from bone, hip rotation separable from tibia, scapula distinct from shoulder. Sapiens gives us 308 landmarks instead of 33 — grip, face, the body under clothing. Both are research-licensed today; the commercial-clean version is gated on dataset access we've already priced. These are the two honest upgrade paths for the 4-movement protocol."

### Honesty guardrails — do not overclaim in Q&A

- **No "per-vertebra" claim.** SKEL's spine is 3 segments (lumbar / thorax / cervical). Per-vertebra is a CT/MRI problem, not an RGB-video problem. If asked: "3 regional segments — matches the resolution a PT grades at. Per-vertebra needs imaging."
- **License framing stays explicit.** SKEL CC-BY-NC-SA, Sapiens-Lite CC-BY-NC 4.0. Both are frontier signals, not product picks. The "BlazePose clean today, frontier priced post-showcase" narrative is stronger when this is said plainly.
- **One slide, not a category survey.** If the audience wants "what about NLF / WHAM / GVHMR / SMPLer-X," point to this doc for the long list.
