# Model Commercial-Viability Matrix — 2026-04-16

**Status:** current
**Created:** 2026-04-16
**Updated:** 2026-04-16
**Owner:** AaronCarney

**Purpose.** Decision layer sitting *above* the license audit (`license-audit-2026-04-11-v2.md`) and stack-options matrix (`stack-options-matrix-2026-04-11.md`). Those docs enumerate raw facts; this doc orders them into recommendations that hold up under investor / acquirer scrutiny.

**The core question.** What models should the BioLiminal server use — for the Mon 2026-04-20 bicep curl demo AND for the post-demo commercial trajectory — such that (a) the demo ships, (b) nothing in the stack becomes a licensing liability if an interested party looks closely, and (c) the transition from demo to commercial is a known, costed engineering path rather than a rebuild.

**Non-goal.** Re-audit licenses. Every license claim below cites `license-audit-v2` or `stack-options-matrix`. Any new claims (commercial SDKs, retrain costs) cite fresh research explicitly.

**Scope.** Every candidate currently in the research corpus, plus commercial SDKs (Google ML Kit, Apple Vision) where a live evaluation path exists. Competitor platforms (Hinge, Sword, DARI, Kinetisense, PostureScreen) are *not* candidates — they're competitive reference, covered in `market/market-analysis.md`.

---

## 1. Taxonomy (10 tag namespaces)

Every candidate below is tagged against these namespaces. Use these tags when adding new candidates; extend the vocabulary in `research/schemas/tag-vocabulary.yaml` if a new tag is needed.

### 1.1 `stage::`
Where in the pipeline the candidate slots in.
- `phone-pose` — on-device 2D (and optionally relative-depth z) pose extraction
- `server-3d-lift` — 2D keypoints → world-grounded 3D pose
- `server-kinetics` — 3D pose → joint moments / muscle forces / GRFs (biomechanical)
- `server-reasoner` — observations → chain reasoning / rule evaluation / report narrative
- `server-scorer` — per-rep quality scoring / pattern matching
- `biomech-model` — musculoskeletal model definition consumed by OpenSim-class backends
- `dataset` — training / evaluation corpus

### 1.2 `license-code::`
License of the source code repository.
- `apache2` · `mit` · `bsd` · `polyform-nc` · `research-only` · `proprietary-commercial` · `unknown`

### 1.3 `license-weights::`
License on the trained model artifacts (often different from code).
- `clean` (commercial-usable as shipped) · `research-nc` (explicit non-commercial clause) · `derived-nc` (inherits NC from training data) · `blocked` (compound blocker) · `n/a` (no weights — code-only / math-only / dataset)

### 1.4 `training-data::`
What the released weights were trained on, with license of that data.
- `coco-ccby4` · `mpii-bsd-like` · `amass-nc` · `h36m-nc` · `mpi-inf-3dhp-nc` · `3dpw-nc` · `bedlam-nc` · `fit3d-nc` · `emdb-nc` · `proprietary` · `synthetic-clean` · `unknown` · `n/a`

### 1.5 `commercial-path::`
What it takes to ship the candidate in a paid product.
- `ships-as-is` — no action needed, commercial-OK today
- `negotiate-license` — pay-for-use agreement available (MPI commercial via Meshcapade, OpenCap Monocular separate agreement, etc.)
- `retrain-clean-data` — code is OK, weights need retraining on commercial-clean data
- `swap-model` — drop this in favor of a commercial alternative with compatible output
- `infeasible` — no realistic commercial path at current scale

### 1.6 `commercial-effort::`
Scale of effort to execute the `commercial-path`.
- `none` — already commercial
- `small` — hours of integration, <$5k total
- `medium` — weeks to a few months, $5k–$50k total
- `large` — 3–6 engineer-months + $50k–$500k (compute + data + license fees)
- `infeasible-without-funding` — requires venture-scale resources or case-by-case license negotiation with uncertain outcome

### 1.7 `demo-role::`
Role in the Mon 2026-04-20 bicep curl demo.
- `critical-path` — demo fails without it
- `optional` — nice-to-have, included if time allows
- `deferred` — explicitly out of demo scope
- `excluded` — actively rejected for demo

### 1.8 `explainability::`
Transparency of inference to a non-ML observer (investor, clinician, acquirer).
- `interpretable` — deterministic rules / geometry / YAML
- `partially-interpretable` — intermediate outputs (landmarks, angles) are inspectable but model internals are not
- `black-box` — end-to-end neural, no inspectable intermediates

### 1.9 `swap-risk::`
How hard it is to replace this candidate mid-product without rewriting downstream.
- `low` — drop-in, same interface (e.g., one 33-landmark phone model for another)
- `medium` — schema shift required (e.g., 17 vs 33 keypoints, or 2D vs 3D output)
- `high` — rewrites the server pipeline shape (e.g., swapping rule engine for GNN)

### 1.10 `domain-fit::`
Fit for BioLiminal's use case (ordinary phone video of fitness/movement).
- `validated` — peer-reviewed evaluation on this use case
- `likely-good` — design target matches but no direct validation
- `unproven` — plausible but no evidence either way
- `poor` — known mismatch (e.g., trained for lab mocap only)

---

## 2. Evaluation order (what gates what)

Decisions cascade. A candidate that fails an upstream gate does not need downstream analysis.

```
┌──────────────────────────────────────────────────────────────┐
│ 1. LICENSE of weights + training data                        │
│    └─ If blocked for commercial: is there a viable path?     │
├──────────────────────────────────────────────────────────────┤
│ 2. COMMERCIAL-PATH EFFORT                                    │
│    └─ If "infeasible-without-funding": demote to demo-only   │
│       or exclude from matrix                                 │
├──────────────────────────────────────────────────────────────┤
│ 3. PIPELINE FIT (stage:: + output shape)                     │
│    └─ Does it slot into the architecture?                    │
├──────────────────────────────────────────────────────────────┤
│ 4. DOMAIN FIT (for fitness/movement video)                   │
│    └─ Is it actually useful for our use case?                │
├──────────────────────────────────────────────────────────────┤
│ 5. DEPLOYMENT FOOTPRINT (phone vs server, latency)           │
│    └─ Can it run where we need it?                           │
├──────────────────────────────────────────────────────────────┤
│ 6. INTEGRATION COST (engineering effort to ship this sem)    │
│    └─ Can we actually deliver it in the capstone window?     │
└──────────────────────────────────────────────────────────────┘
```

The existing `stack-options-matrix-2026-04-11.md` evaluates gates 3–6 exhaustively. This doc's contribution is gates 1–2 done rigorously, then the synthesis.

---

## 3. Per-candidate tagged rows

Grouped by `stage::`. Unknown fields marked `?`. See `license-audit-v2` for citation of every license claim.

### 3.1 `stage::phone-pose`

| Candidate | license-code | license-weights | training-data | commercial-path | commercial-effort | demo-role | explainability | swap-risk | domain-fit |
|---|---|---|---|---|---|---|---|---|---|
| **MediaPipe BlazePose Full** | apache2 | clean (Google ML Kit terms; model card PDF confirmation pending) | unknown (not disclosed) | ships-as-is | none | critical-path | partially-interpretable | low (drop-in vs Lite/Heavy) | likely-good (design target: fitness/yoga) |
| MediaPipe BlazePose Lite | apache2 | clean | unknown | ships-as-is | none | deferred (A/B alt) | partially-interpretable | low | likely-good |
| MediaPipe BlazePose Heavy | apache2 | clean | unknown | ships-as-is | none | deferred (flagship-only latency) | partially-interpretable | low | likely-good |
| MoveNet Lightning | apache2 | clean (consensus) | unknown | ships-as-is | none | excluded (17kp feature set inferior vs 33kp BlazePose for fitness) | partially-interpretable | medium (17→33 schema shift) | likely-good |
| MoveNet Thunder | apache2 | clean (consensus) | unknown | ships-as-is | none | excluded (same as Lightning) | partially-interpretable | medium | likely-good |
| HRPose / HRNet-small (mobile) | apache2 (HRNet) / varies per port | varies per port | coco-ccby4 (historical HRNet) | ships-as-is (if port is clean) | small-medium (per-port audit + integration) | deferred (commercial-stretch upgrade) | partially-interpretable | medium (17kp + different conventions) | likely-good (strong occlusion handling) |
| Google ML Kit Pose Detection | proprietary-commercial (SDK, **beta** — no SLA, breaking-changes possible per Google ML Kit Terms) | clean (free for commercial use, no per-seat/royalty) | unknown (BlazePose GHUM 3D — same lineage as MediaPipe BlazePose, Z is "image pixels" pseudo-3D, not metric) | ships-as-is | none | optional (Flutter binding path per mobile-handover §3) | partially-interpretable | low (identical 33-kp BlazePose output) | likely-good (Google positions for fitness) |
| Apple Vision Pose (`VNHumanBodyPose3DObservation`, iOS 17+/iPadOS 17+/macOS 14+) | proprietary-commercial | clean (free via Apple Dev Program $99/yr for distribution) | unknown | ships-as-is (iOS ecosystem only; **metric-scale 3D requires LiDAR** — iPhone 12 Pro+ only) | none (but Apple-ecosystem-exclusive) | excluded (Flutter app targets Android + iOS; Apple-only breaks cross-platform; LiDAR dependency further gates it to Pro devices) | partially-interpretable | high (different keypoint convention) | likely-good |
| ViTPose (any size) | apache2 (code) | research-nc (COCO/MPII-trained checkpoints) | coco-ccby4 + mpii-bsd-like | retrain-clean-data (or ships-as-is if careful about checkpoint provenance) | medium (retrain on COCO-only) | excluded (no mobile runtime, server-only) | black-box | high (2D only, requires 3D-lift downstream) | unproven (not benchmarked on fitness video) |

**Phone-pose synthesis.** Only three candidates pass Gate 1+2 *and* are mobile-deployable: MediaPipe BlazePose variants, MoveNet, Google ML Kit Pose (which is itself a BlazePose wrapper). Apple Vision is iOS-only and would fork the Flutter app. HRPose is a forward-compat upgrade lane. Everything else is server-bound.

### 3.2 `stage::server-3d-lift`

| Candidate | license-code | license-weights | training-data | commercial-path | commercial-effort | demo-role | explainability | swap-risk | domain-fit |
|---|---|---|---|---|---|---|---|---|---|
| **WHAM** | mit (code) | blocked (MPI NC; SMPL-family) | amass-nc + 3dpw-nc + bedlam-nc + emdb-nc | negotiate-license OR retrain-clean-data | infeasible-without-funding (no commercial-clean 3D mocap dataset at AMASS scale exists publicly; SMPL commercial license via Meshcapade is case-by-case, price undisclosed) | deferred (not on demo path) | black-box | high (SMPL output → huge downstream reshape) | validated (in-the-wild, not fitness-specific) |
| MotionBERT | apache2 (code) | research-nc (H36M checkpoints) | h36m-nc | retrain-clean-data | large (3–6 eng-months + no commercially-clean 3D pose dataset exists publicly; synthetic alternative BEDLAM is also NC) | deferred (not on demo path) | black-box | high (different skeleton) | poor→unproven (H36M lab distribution, unlikely generalization to fitness video without retrain) |
| TCPFormer | unknown | unknown (no official release) | h36m-nc + mpi-inf-3dhp-nc | infeasible (no authoritative code release) | infeasible-without-funding | excluded (watchlist) | black-box | high | unproven |
| HSMR (SKEL body model) | mit (code) | blocked (SMPL/SKEL-family NC) | n/a (image-only input) | negotiate-license OR swap-model | infeasible-without-funding (SKEL is the distinguishing feature; swapping loses it) | deferred (planned for rollup spine sequencing post-demo) | black-box | high (SKEL → Rajagopal mapping is unpublished) | unproven for movement screening |
| ViTPose + 3D-lift head | apache2 (both) | research-nc (COCO+3D-lift-training-set NC) | coco-ccby4 + h36m-nc | retrain-clean-data | large | excluded | black-box | high | unproven |

**Server-3d-lift synthesis.** This is the **hard commercial bottleneck** of the stack. Every candidate weighted for 3D lift was trained on a non-commercial dataset (AMASS, Human3.6M, BEDLAM, EMDB, 3DPW, Fit3D — all confirmed MPI/IMAR/ETH non-commercial with explicit no-training-for-commercial clauses per `license-audit-v2`). There is no commercially-clean public 3D human motion dataset at a scale that would let you retrain a WHAM- or MotionBERT-class model and ship commercially. The only realistic commercial paths for this stage are:

1. **Negotiate commercial SMPL license** via Meshcapade (`sales@meshcapade.com`) + commercial AMASS license via MPI — uncosted, case-by-case
2. **Collect proprietary 3D mocap dataset** (scale of AMASS is 13k motion sequences) — 6-18 months + $100k+ of mocap costs
3. **Skip 3D lift entirely** — use phone-estimated z-relative depth (BlazePose z field) + 2D geometry. Lossy vs WHAM, but commercial-clean and often sufficient for single-plane movements like bicep curl

For the bicep curl demo, path #3 is not only the commercially-safe choice — it's also architecturally correct. **Elbow flexion is a 2D problem from the BlazePose sagittal landmarks.** WHAM+OpenCap would be using a 16-wheel truck to deliver a pizza.

### 3.3 `stage::server-kinetics`

| Candidate | license-code | license-weights | training-data | commercial-path | commercial-effort | demo-role | explainability | swap-risk | domain-fit |
|---|---|---|---|---|---|---|---|---|---|
| **OpenSim + Rajagopal 2016 (direct)** | apache2 (OpenSim) + mit-use-agreement (Rajagopal) | n/a (physics model, not ML) | n/a | ships-as-is | none | deferred (not needed for bicep curl) | interpretable (mechanics model) | low (input is any 3D keypoint stream) | validated (standard biomech backbone) |
| **Direct geometry (hand-rolled)** | n/a (user code) | n/a | n/a | ships-as-is | none | critical-path (bicep curl elbow angle math) | interpretable | low | validated (Hip R=0.94, Knee R=0.95 from BlazePose per `markerless-mediapipe-joint-moments.pdf`) |
| OpenCap Core (dual-cam) | apache2 | n/a | n/a | ships-as-is (code) | n/a | excluded (requires 2 synced cameras — not consumer) | partially-interpretable | high | unproven for single-phone |
| OpenCap Monocular (full pipeline) | polyform-nc | n/a (wraps WHAM+OpenSim+SMPL) | derived from WHAM chain (amass-nc + 3dpw-nc + bedlam-nc + emdb-nc) | negotiate-license (Utah MoBL) + license chain of WHAM/AMASS/SMPL | infeasible-without-funding | excluded | black-box | high | validated on lab walk/squat/STS |
| Pose2Sim | apache2 | n/a | n/a | ships-as-is | n/a | excluded (multi-camera only) | interpretable | high | validated (multi-cam) |

**Server-kinetics synthesis.** Fully commercial-clean: OpenSim + Rajagopal + direct-geometry. Non-commercial (blocked): OpenCap Monocular (triple-blocker — PolyForm NC + AMASS + SMPL). OpenCap Core is Apache 2.0 code but requires dual-camera so it's architecturally excluded. **Key insight from `license-audit-v2` — the downstream biomechanics stack is fully commercial-clean end-to-end.** The blocker is never kinetics itself, only the 3D pose input into it.

### 3.4 `stage::server-reasoner`

| Candidate | license-code | license-weights | training-data | commercial-path | commercial-effort | demo-role | explainability | swap-risk | domain-fit |
|---|---|---|---|---|---|---|---|---|---|
| **YAML rule engine (custom)** | user-code | n/a | n/a (rules are hand-authored from peer-reviewed thresholds) | ships-as-is | none | critical-path (bicep curl ruleset in `ML_RandD_Server#12`) | interpretable | high (rule engine is product differentiator; swapping → GNN changes user-visible semantics) | validated (rules cite Harris-Hayes, Hewett, Sahrmann) |
| GNN chain reasoner | user-code | would-be-research-nc | would need labeled fascial-chain training data — **does not exist publicly at scale** | infeasible (no training corpus) | infeasible-without-funding | deferred (post-launch research per decision doc §6.4) | black-box | high | unproven |
| DTW / NCC pattern matching | user-code (BSD/Apache in dependent libs per `dtw-library-comparison-2026-04-14.md`) | n/a | n/a | ships-as-is | none | critical-path (rep-quality scoring supporting the rule engine) | interpretable | medium | validated for time-series (stt-pipeline-class applications; movement rep-matching is a good fit) |

**Reasoner synthesis.** The **rule engine is the product differentiator** (per `market-analysis.md` §8 White Space Map — no competitor does chain reasoning). It's also the cleanest commercially because it's 100% our code. GNN is the post-launch research path and is gated on labeled training data we don't have. DTW/NCC is a supporting technique, ships-as-is.

### 3.5 `stage::server-scorer`

| Candidate | license-code | license-weights | training-data | commercial-path | commercial-effort | demo-role | explainability | swap-risk | domain-fit |
|---|---|---|---|---|---|---|---|---|---|
| Siamese quality scorer | user-code | would-be-derived | would need labeled rep-quality dataset | retrain-clean-data | large | deferred (post-launch) | black-box | medium | unproven |
| Sabo Beighton scorer | research-only | research-only | proprietary (n=125 EDS cohort) | infeasible | infeasible-without-funding | excluded (off-scope — hypermobility, not movement quality) | black-box | medium | validated for hypermobility only |
| **DTW/NCC-based scoring (current)** | user-code | n/a | n/a | ships-as-is | none | critical-path | interpretable | low | validated |

### 3.6 `stage::biomech-model`

| Candidate | license-code | license-weights | training-data | commercial-path | commercial-effort | demo-role | explainability | swap-risk | domain-fit |
|---|---|---|---|---|---|---|---|---|---|
| **Rajagopal 2016 (OpenSim full-body MSK)** | mit-use-agreement (per simtk.org, verified in `license-audit-v2`) | n/a | n/a | ships-as-is | none | deferred (not needed for bicep curl) | interpretable | low | validated (peer-reviewed MSK standard) |
| SKEL (used by HSMR) | mpi-nc | n/a | n/a | negotiate-license | infeasible-without-funding | deferred (post-demo) | interpretable | high (no published SKEL→Rajagopal adapter) | unproven for BioLiminal |
| SMPL / SMPL-X | mpi-nc (verified, `license-audit-v2`) | n/a | n/a | negotiate-license via Meshcapade | infeasible-without-funding | excluded | partially-interpretable | high | validated (research standard) |

### 3.7 `stage::dataset`

Full commercial-clearance breakdown in `license-audit-v2` Datasets table. Summary:

| Dataset | Commercial training? | Source |
|---|---|---|
| **MS COCO keypoints** (annotations) | ✅ Yes (CC BY 4.0 annotations) | `license-audit-v2` |
| **MPII Human Pose** (annotations) | ✅ Likely yes (BSD-like historical) | `license-audit-v2` |
| AMASS | ❌ MPI NC (explicit no-training-for-commercial) | `license-audit-v2` |
| Human3.6M | ❌ IMAR NC, institutional-email-gated | `license-audit-v2` |
| 3DPW | ❌ MPI NC | `license-audit-v2` |
| EMDB | ❌ ETH Zurich NC | `license-audit-v2` |
| BEDLAM | ❌ MPI NC (v1's CC BY 4.0 label was wrong) | `license-audit-v2` |
| Fit3D | ❌ IMAR NC (explicit no-training-for-commercial) | `license-audit-v2` |

**Dataset synthesis.** The entire 3D human motion dataset landscape is locked commercial-NC. Commercial retraining of any 3D pose model requires either proprietary data collection or synthetic data from a commercially-licensed generator (none known at AMASS scale). This is the single biggest structural constraint on the stack's commercial story.

---

## 4. Cross-reference: dependency chains + mutual exclusivity

### 4.1 Chain-of-blocker: the WHAM → OpenCap Monocular stack

```
OpenCap Monocular (PolyForm NC) ──┐
        ↓ depends on              │
   WHAM (MPI NC weights) ─────────┤─── all three must clear
        ↓ depends on              │    for commercial deployment
   SMPL (MPI NC) ─────────────────┤
        ↓ weights trained on      │
   AMASS (MPI NC, explicit        │
     no-training-for-commercial) ─┘
```

Any candidate that includes OpenCap Monocular, WHAM weights, SMPL, or AMASS-derived weights inherits this four-way blocker. **This is the biggest latent risk in the current documented-but-disputed `pipeline-architecture-decision-2026-04-10.md`.** Committing to that pipeline for the demo means shipping a demo that cannot go commercial without negotiating four independent licenses.

### 4.2 Mutual exclusivity

- WHAM vs MotionBERT vs TCPFormer — all compete for the `server-3d-lift` slot. Pick zero or one.
- YAML rule engine vs GNN chain reasoner — conceptually replace each other; YAML is v1 ship, GNN is v2 research.
- Direct geometry vs OpenCap Monocular (for kinetics) — replace each other.

### 4.3 Cross-stage compatibility (from `stack-options-matrix-2026-04-11.md` Table 7, distilled)

- BlazePose landmarks → OpenSim + Rajagopal → direct kinetics: **works with a published marker mapping** (medium adapter work)
- BlazePose landmarks → direct geometry → rule engine: **works natively** (what we're doing for demo)
- WHAM (SMPL) → OpenSim + Rajagopal: requires an SMPL→OpenSim body fit, which is effectively the entirety of OpenCap Monocular's front-end (complex)
- 2D-only models (ViTPose, MoveNet, HRPose) → OpenSim: requires a separate 3D-lift stage before OpenSim can consume them

### 4.4 Swap risk — what breaks if we change later

- **Phone model swap** (BlazePose → ML Kit → HRPose): **low risk** IF output schema stays 33-landmark BlazePose convention. The server's `Frame` schema validates exactly 33 landmarks (per `api/schemas.py:22`), so swap targets must preserve that. ML Kit Pose Detection is a drop-in (it IS BlazePose under Google's commercial wrapper). HRPose is 17-landmark COCO → medium risk, would require a keypoint-conversion layer.
- **Server 3D lift added later** (currently no-op → WHAM or MotionBERT): medium risk, adds a new output type (SMPL or H36M joints) that the rule engine must understand. Rule YAML gets augmented, not rewritten.
- **Reasoner swap** (YAML → GNN): high risk. Different semantics, different output shape, different testing strategy. Post-launch research only.

---

## 5. Commercialization cost projections

For every candidate tagged `retrain-clean-data`, `negotiate-license`, or `swap-model`, the cost breakdown:

### 5.1 Retrain a WHAM- or MotionBERT-class 3D lifter on commercial-clean data

- **Dataset gap** (primary blocker): No public 3D human motion dataset at AMASS scale is commercially clearable. Every known candidate is non-commercial:
  - **BEDLAM / BEDLAM2.0** — MPI non-commercial, verified directly (`license-audit-v2`). Generator + rendering pipeline also MPI-NC.
  - **AGORA** — research-only license, verified via fresh web research 2026-04-16.
  - **SURREAL** — public generation code, but uses SMPL which is MPI non-commercial for commercial applications.
  - **AMASS / Human3.6M / Fit3D / EMDB / 3DPW** — all research-only with explicit no-training-for-commercial clauses.
  - **MS COCO** — CC BY 4.0 annotations but **2D-only**, not usable for 3D-lift training without paired 3D ground truth.
  - **Commercially-clean path (no turnkey option)**: custom mocap capture you own + synthetic rendering (Mixamo/Rokoko/Unreal MetaHuman under their respective EULAs, requiring legal review) + COCO-keypoint 2D supervision as one modality. *No public case study of a MotionBERT-class model retrained end-to-end on purely commercial-clean data has been found.*
- **Dataset cost estimates (2026 rates)**:
  - Collect proprietary mocap at AMASS scale (~13k motion sequences): **$200k–$500k + 12–18 months** (Stanford Human Performance Lab-class mocap ≈ $5k/day × 40 subjects × multiple sessions; university partnerships can reduce this)
  - Fine-tune on proprietary subset (~2k sequences): **$50k–$100k + 3–6 months** — smaller dataset, lower final accuracy, viable for targeted fitness domain
- **Compute** (more grounded from 2026-04-16 research): MotionBERT-scale (~90M params) retrain with ablations ≈ 500–2000 H100-hours:
  - Raw compute (Lambda/Vast.ai, late-2025 ~$3/hr H100): **$1.5k–$6k for one successful run**
  - Realistic with ablations, failed runs, hyperparameter sweeps: **$10k–$30k**
  - AWS/GCP rates (more expensive): **$20k–$60k** for same work
- **Engineering**: 3–6 FTE-months for one ML engineer (reproduce architecture, build data pipeline — the hard part — train, validate, package for inference). **Data-licensing diligence alone is ~1 FTE-month.**
- **Total realistic bottom**: **$70k + 6 months** (fine-tune on 2k-sequence proprietary dataset, minimum-viable retrain)
- **Total realistic top**: **$600k + 18 months** (full AMASS-replacement collection)

Tag: `commercial-effort::large` to `infeasible-without-funding` depending on quality target. Sources: `license-audit-v2`; 2026-04-16 background web research on MotionBERT repo + commercial dataset landscape (cached in conversation; no public case study exists of a commercial retrain at this class).

### 5.2 Negotiate commercial SMPL + AMASS license (MPI / Meshcapade)

- **Pricing**: Undisclosed, case-by-case (per `license-audit-v2`). Meshcapade is the Max Planck commercial spinout for SMPL licensing.
- **Timeline**: 1–3 months typical for corporate license negotiation.
- **Rough estimate from comparable research licenses**: $10k–$100k/year depending on use case + deployment scale. No public price sheet exists.
- **Risk**: Licensor can refuse or price-out smaller startups. No obligation to grant.

Tag: `commercial-effort::large` (lower $ but high execution + legal uncertainty).

### 5.3 Negotiate commercial OpenCap Monocular license (Utah MoBL)

- Separate agreement required per `license-audit-v2`. Contact: authors directly (no listed portal).
- **Stacks on top of** SMPL + AMASS licenses — you'd need all three.
- Realistically: `infeasible-without-funding` for a capstone.

### 5.4 Swap: phone model from MediaPipe → Google ML Kit Pose

- **Cost**: ~1 week of integration effort (ML Kit has a maintained Flutter binding, `google_mlkit_pose_detection`, per `mobile-handover/README.md` step 3)
- **Output compatibility**: ML Kit Pose Detection uses the **same BlazePose GHUM 3D model lineage** as MediaPipe — **identical 33-landmark output** in canonical order, with the same x/y/z schema (z is pseudo-depth in image-pixel units, not metric). Drop-in at the landmark-validator level.
- **Why do this?** If Google's MediaPipe Tasks Flutter binding becomes unmaintained or a specific licensing clarification is needed, ML Kit is the commercial-backed path with the same underlying model.
- **Caveat:** Google ML Kit Pose Detection is currently labeled **beta**. No SLA, breaking changes are permitted under Google ML Kit Terms. For production commercial deployment, this is a meaningful risk — consider MediaPipe Tasks (GA) as the primary path and ML Kit as the fallback rather than the reverse.
- Tag: `commercial-effort::small`. Source: web research 2026-04-16 on `developers.google.com/ml-kit/vision/pose-detection` + `developers.google.com/ml-kit/terms`.

### 5.5 Swap: skip 3D lift entirely, use direct geometry on BlazePose

- **Cost**: ~0 (this is the demo path)
- **Quality tradeoff**: No world-grounded 3D, no global translation, no muscle forces without a 3D pose input into OpenSim. 2D sagittal angles + z-relative depth from BlazePose is sufficient for single-plane movements (bicep curl, overhead squat from lateral view) but inadequate for movements with out-of-plane rotation (cable press, squat with asymmetric cue).
- **Viability for the 4-movement post-demo product**: Acceptable for overhead squat (sagittal), push-up (sagittal), single-leg squat (sagittal with known camera pose). Rollup is marginal — spine sequencing benefits from true 3D.
- Tag: `commercial-effort::none` if this is the product path.

---

## 6. Recommendation per pipeline stage

Three picks per stage: **Demo** (4/20), **Commercial-now** (ships-as-is to a paid product), **Commercial-stretch** (better performance, known effort required).

| Stage | Demo | Commercial-now | Commercial-stretch | Bridge strategy |
|---|---|---|---|---|
| **phone-pose** | MediaPipe BlazePose Full | MediaPipe BlazePose Full | Google ML Kit Pose Detection (same model, Google commercial wrapper) | No bridge needed — demo pick IS the commercial pick. ML Kit is a zero-risk pivot if Google's terms ever become ambiguous. HRPose is a later accuracy-upgrade lane (occlusion robustness) once shipping. |
| **server-3d-lift** | *none* (skip for bicep curl) | *none* (direct geometry + z-relative) | MotionBERT retrained on proprietary 3D dataset | Demo skips it (bicep curl is 2D). Post-demo 4-movement product can ship on direct-geometry for 3 of 4 movements (squat/single-leg/push-up). Rollup + any future out-of-plane movement is the upgrade trigger. |
| **server-kinetics** | Direct geometry (elbow angle from landmarks) | Direct geometry + OpenSim+Rajagopal for richer kinetics | Same (OpenSim+Rajagopal is already ship-ready commercial) | No bridge needed — OpenSim pathway is clean from day one, just requires 3D input. Same trigger as 3D-lift upgrade. |
| **server-reasoner** | YAML rule engine | YAML rule engine | GNN chain reasoner (post-launch research, requires labeled training data) | Rules are product differentiator and commercially clean forever. GNN is a 2+ year research path with its own data collection problem. |
| **server-scorer** | DTW/NCC | DTW/NCC | Siamese quality scorer (requires labeled rep-quality data) | DTW/NCC is stable ground truth. Siamese adds quality signal but needs training corpus. |
| **biomech-model** | *none* (direct geometry doesn't use MSK model) | Rajagopal 2016 | Same | OpenSim+Rajagopal is clean. No upgrade path needed. |

### Critical observation

**Demo pick = Commercial-now pick** at every stage. This is not a coincidence — the recommendation deliberately avoids demo-ing anything that can't ship commercially. The stretch-path upgrades (HRPose, 3D lift via retrained MotionBERT, Siamese scorer, GNN reasoner) are all *additive* enhancements, not replacements of demo components. Every upgrade has a known-cost engineering path; nothing requires rewriting the demo stack from scratch.

---

## 7. Investor-defensibility narrative

If an investor / acquirer / interested clinician looks closely at the demo stack, here's the story each component tells:

| Component | Public license | "So can you ship this?" |
|---|---|---|
| MediaPipe BlazePose (phone) | Apache 2.0 (framework) + Google ML Kit commercial terms (model) | **Yes** — shipped in thousands of commercial apps including Google's own ML Kit. |
| Flutter capture + upload pipeline | user code | **Yes** — our code, commercial. |
| Server rule engine (YAML) | user code | **Yes** — our code, and the rule authoring methodology (evidence-anchored clinical heuristics from Harris-Hayes, Hewett, Sahrmann) is our defensible IP. |
| DTW/NCC rep scoring | user code using Apache/BSD libs | **Yes**. |
| sEMG signal processing (ESP32-side) | user firmware | **Yes**. |
| Chain-reasoning rule set | user-authored YAML | **Yes** — this is the product differentiator, not an upstream dependency. |

**Full stack: zero dependency on research-only models, zero dependency on non-commercial datasets, zero licensing fees owed to third parties for the core demo path.** This is meaningfully different from the pipeline documented in `pipeline-architecture-decision-2026-04-10.md`, which chains WHAM → OpenCap Monocular → SMPL with three independent commercial blockers.

**Post-demo upgrade path, if asked:**

> "We're evaluating richer 3D biomechanics for movements that benefit from out-of-plane analysis (rollup spine sequencing, asymmetric cable work). The research-grade options (WHAM, OpenCap Monocular) are non-commercial; we've scoped two commercial paths — negotiate licensing with Max Planck / Meshcapade (uncosted, case-by-case) or retrain a MotionBERT-scale lifter on a proprietary dataset (6 months, $70k–$600k depending on quality target). Neither is on the critical path for our current movement repertoire."

This is the right answer to give an investor. It demonstrates:
- We know the licensing landscape cold
- We have a defensible clean stack shipping today
- We have a priced upgrade path when the product earns the investment
- We aren't quietly depending on things that will break under scrutiny

---

## 8. IC-2 schema implications

With the model recommendations locked, the phone↔server contract can be finalized. Current state (`RnD_Server/software/server/src/auralink/api/schemas.py`):

```python
MovementType = Literal["overhead_squat", "single_leg_squat", "push_up", "rollup"]

class SessionMetadata(BaseModel):
    movement: MovementType
    device: str
    model: str  # e.g. "mediapipe_blazepose_full"
    frame_rate: float
    captured_at: datetime

class Frame(BaseModel):
    timestamp_ms: int
    landmarks: list[Landmark]  # validated to exactly 33

class Session(BaseModel):
    metadata: SessionMetadata
    frames: list[Frame]
```

### 8.1 Required changes for bicep curl demo

1. **Add `"bicep_curl"` to `MovementType`** (one-line schema change, regenerate `session.schema.json`, update mobile-handover `models.dart` enum). Blocks demo capture; trivial to fix.
2. **Decide on sEMG inclusion in `SessionPayload`** — `ML_RandD_Server#13` (demo-critical, needs-decision). Two paths:
   - **Include:** add `sEMGChannel[]` with samples keyed by MCU timestamp. Server fuses in the analysis. Pros: server-side cross-modal reasoning; single canonical record. Cons: large payloads; BLE clock sync complication.
   - **Exclude:** sEMG flows ESP32 → phone only, analyzed on-device for live cue/verify, not uploaded. Server only sees pose. Pros: simpler IC-2; smaller uploads. Cons: no server-side multimodal analysis; report narrative is pose-only.

### 8.2 Recommendation

**Include sEMG in `SessionPayload` as an optional field.** For demo, we need server-side fusion to generate the report narrative that combines activation delta with pose quality. The payload shape:

```python
class sEMGSample(BaseModel):
    channel: int  # 0=biceps, 1=brachioradialis
    timestamp_ms: int  # MCU-clock timestamp
    value: float  # normalized [0,1] or raw mV, TBD with Rajat

class Session(BaseModel):
    metadata: SessionMetadata
    frames: list[Frame]
    emg: list[sEMGSample] | None = None  # optional; phone-only demos omit
```

This is forward-compatible: demo uploads include `emg`; post-demo 4-movement screening uploads can omit it (the pose-only movements don't need it).

### 8.3 Report response schema (still TBD per mobile-handover §1)

Minimum fields for demo:

```python
class RepScore(BaseModel):
    rep_index: int
    activation_delta: float  # sEMG pre/post-cue delta
    cue_fired: bool
    cue_verified: bool  # verify-delta ≥ 15% within 500 ms
    elbow_angle_range: tuple[float, float]  # min, max in degrees

class SessionReport(BaseModel):
    session_id: str
    reps: list[RepScore]
    total_reps: int
    chain_observations: list[str]  # rule-engine output (short phrases)
    narrative: str  # human-readable summary for display
```

This can ship for 4/20. Post-demo report schemas extend this (chain_observations grows, narrative richer, per-movement fields added as MovementType expands).

### 8.4 IC-2 lock checklist

- [ ] Add `"bicep_curl"` to `MovementType` literal
- [ ] Add `sEMGSample` + `emg: list[sEMGSample] | None` to `Session`
- [ ] Define `RepScore` + `SessionReport` for the report endpoint
- [ ] Regenerate `session.schema.json` via `software/mobile-handover/tools/export_schemas.py`
- [ ] Update `mobile-handover/interface/models.dart` to match
- [ ] Update `mobile-handover/fixtures/sample_valid_session.json` to include an EMG fixture
- [ ] Bump `mobile-handover/README.md` §The contract paragraph with bicep-curl specifics

Once done, IC-2 is locked for 4/20. This is the gating item for today's work.

---

## 9. Verification gaps (what this doc does NOT settle)

- **BlazePose GHUM 3D Model Card PDF** — still pending human-in-browser verification per `license-audit-v2`. This is the single thing that would move MediaPipe weights from Medium-High confidence to High. Priority: ask Kelsi to open the PDF on a normal browser and confirm "intended use" explicitly permits commercial distribution.
- **Google ML Kit's beta → GA timeline** — no public roadmap. Product has been in beta for years; Google has not announced a GA date. Risk to monitor for any production commercial deployment.
- **Apple Vision 3D exact platform matrix** — WWDC23 confirms iOS 17+/iPadOS 17+/macOS 14+ and LiDAR-for-metric-3D; a primary-doc-page fetch was sandbox-blocked during research. If the Apple path ever becomes a real option (e.g. a native iOS-only premium tier), re-verify at `developer.apple.com`.
- **MotionBERT retrain cost ground-truth** — ballpark cited here ($10k–$30k compute + 3–6 eng-months + $50k–$500k data) is engineering estimate, not a cited production reference. No public commercial retrain at this class has been found. Production retrain requires a dedicated research sprint if the commercial pivot becomes real.
- **OpenCap SimTK DUA** — not directly relevant to the pipeline recommendation but is a post-demo item (`ML_RandD_Server#2`) that unlocks evaluation data for the 4-movement product.

---

## 10. What this changes

**For 4/20 demo.** Confirms the demo-first framing in `projects/bioliminal/CLAUDE.md` § Current Focus. No WHAM, no OpenCap Monocular, no HSMR, no SMPL. Phone BlazePose → server rule engine + DTW/NCC → report. Fully commercial-clean.

**For post-demo 4-movement product.** Two paths diverge:
- **Clean path (recommended default):** extend the direct-geometry pipeline with OpenSim+Rajagopal for kinetics when/if movements need it. Commercial-ready from day one. Limits: no world-grounded 3D; rollup is marginal.
- **Rich path (requires investment):** pursue commercial WHAM/SMPL licensing OR proprietary 3D dataset collection + retrained lifter. 6-18 months + $70k-600k. Gates the rollup movement and any future out-of-plane work.

**For `pipeline-architecture-decision-2026-04-10.md`.** That doc's recommendation (WHAM+OpenCap+SMPL chain) is now explicitly tagged `commercial-effort::infeasible-without-funding` and demoted to "research-grade option requiring case-by-case license negotiation." The stale-warning header added on 2026-04-16 stands; this doc is the reconciliation the handoff called for.

**For `pipeline-architecture-decision` post-demo reconciliation.** Neither Aaron's earlier MotionBERT+HSMR mental model nor the 4-10 WHAM+OpenCap decision is the right answer. Both trip the same set of licensing blockers. **Rethink the post-demo 3D-lift question as "do we need 3D at all" before "which 3D lifter."** For the movements currently in scope, the answer is likely "no" for 3 of 4, and "marginal" for rollup.

---

## Appendix A: Citations and source docs

- `RnD_Server/docs/research/license-audit-2026-04-11-v2.md` — authoritative license facts, verified via direct GitHub LICENSE fetches + direct license-page fetches where reachable
- `RnD_Server/docs/research/stack-options-matrix-2026-04-11.md` — Tables 1-9 per-candidate metrics, footprint, skeleton mapping, compatibility grid
- `RnD_Server/docs/research/pipeline-architecture-decision-2026-04-10.md` — contested post-demo architecture decision (stale-warning header 2026-04-16)
- `RnD_Server/docs/research/market/market-analysis.md` — competitor landscape, pricing data, regulatory strategy, TAM/SAM/SOM
- `research/synthesis/deep-read-sensing-2026-04-10.md` — per-paper extraction for all pose candidates
- `research/synthesis/deep-read-monocular-pipeline-landscape-2026-04-10.md` — literature synthesis for pipeline rationale
- `research/synthesis/deep-read-ml-upgrade-briefs-2026-04-15.md` — Siamese + GNN research (post-demo)
- `research/synthesis/deep-read-dtw-ncc-methodology-2026-04-14.md` — DTW/NCC math + library options
- `research/sensing/edriss2025-commercial-vision-sensors-and-ai-based-pose-estimation.md` — framework comparison (<10° joint angle error anchor for MediaPipe)
- `research/sensing/akturk2026-markerless-joint-angle-estimation-using-mediapipe-with-a.md` — Hip R=0.94, Knee R=0.95 for direct-geometry from BlazePose
- `bioliminal-mobile-application/mobile-handover/README.md` — IC-2 contract
- `RnD_Server/software/server/src/auralink/api/schemas.py:7-59` — current pydantic schemas

## Appendix B: Changelog

- 2026-04-16 — Initial draft (this document). Supersedes the pipeline choice in `pipeline-architecture-decision-2026-04-10.md` for the bicep curl demo. Post-demo pipeline reconciliation begun.
