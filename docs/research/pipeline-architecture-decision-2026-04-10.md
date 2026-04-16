# Pipeline Architecture Decision — BioLiminal 2026-04-10

> ⚠️ **STALE / DISPUTED — DO NOT TREAT AS SETTLED.** This doc describes a **post-demo** full-product architecture (WHAM + OpenCap Monocular + 4-movement protocol) that was drafted unilaterally and **not confirmed by Aaron**. Aaron's mental model has been MotionBERT + HSMR. Reconciliation is deferred until after the Mon 2026-04-20 bicep curl demo.
>
> **For the 4/20 demo, this doc is not on the critical path.** The demo uses phone BlazePose landmarks + 2-ch sEMG + a bicep-curl-specific rule YAML (`gitlab issue ML_RandD_Server#12`). No WHAM, no OpenCap, no HSMR, no 4-movement protocol.
>
> Current project focus: `projects/bioliminal/CLAUDE.md` § Current Focus.

---

**Audience:** BioLiminal team (Aaron + phone teammate + hardware teammate).
**Status (original, preserved for history):** claimed "Authoritative engineering decision" — see warning above. Supersedes the pipeline-choice section of `docs/operations/comms/research-integration-report.md` (§2.4) and replaces the former `model-framework-recommendations-2026-04-10.md` draft.
**Paired literature synthesis:** `research/synthesis/deep-read-monocular-pipeline-landscape-2026-04-10.md` in the sibling research repo. The literature rationale for every claim in this doc is anchored there — this doc is the *decision*, that doc is the *why*.

---

## 1. TL;DR (what we are shipping)

1. **Premium pipeline:** `MediaPipe BlazePose Full → WHAM → OpenCap Monocular → rule reasoner → report`. Single phone at capture, server-side for 3D lift + kinetics + reasoning. HSMR branches in for rollup spine sequencing only.
2. **On-device model:** MediaPipe BlazePose Full (`pose_landmarker_full.task`), Apache 2.0, 33 keypoints. Nothing else on the phone at launch.
3. **Training strategy:** Ship pretrained. Collect ~20–30 subjects × 4 movements × ≥5 reps for rule-threshold calibration. Public datasets only if a failure mode forces it.
4. **Chain reasoner:** Rule-based YAML at launch. Every rule carries an `evidence:` block citing the mechanism paper. Graph-NN chain reasoner is a post-launch research exercise, not a capstone milestone.
5. **Clinical heuristics:** Cherry-pick Sahrmann-style kinematic patterns grounded by Harris-Hayes mechanism work. **Do not** ship MSI diagnostic labels as report output — Van Dillen 2016 (Level 1 RCT) and Joyce 2023 critique show the label taxonomy does not produce better outcomes or carry construct validity. Mechanism-level rules are fine; label-taxonomy reports are not.

Rationale for every item above is sourced from the literature-synthesis deep-read in the research repo.

---

## 2. Pipeline architecture

```
                   on-device                                          server-side
  +-----------+    +----------------+   upload    +------+     +--------------------+     +---------------------+
  | phone cam | -> | MediaPipe Full | ----------> | WHAM | --> | OpenCap Monocular  | --> | rule-based chain    |
  +-----------+    +----------------+             +------+     | (OpenSim IK/ID +   |     | reasoning + report  |
                                                                |  Rajagopal MSK)   |     +---------------------+
                                                                +--------------------+
                                                                         |
                                                                         v (for rollup only)
                                                                   +----------+
                                                                   |   HSMR   |
                                                                   | (SKEL    |
                                                                   |  spine)  |
                                                                   +----------+
```

**Why this shape and not `MediaPipe → MotionBERT → HSMR`:** the rule thresholds we care about (Hewett, Harris-Hayes) are kinetic, not kinematic. OpenCap Monocular (Gilon 2026) produces joint moments, ground reaction forces, and muscle forces directly. Any pipeline ending at 3D pose would still owe a kinetics layer and we'd be building it from scratch.

### 2.1 Model decisions and status

**Phone / client (ship now):**

| Model | Role | Decision |
|---|---|---|
| **MediaPipe BlazePose Full** (`pose_landmarker_full.task`) | On-device 2D keypoints + live setup-quality feedback | **Ship.** Apache 2.0; Flutter plugin. Keep behind a Dart interface so MoveNet/HRPose can be swapped without a release. |
| MoveNet Thunder (TF Lite) | Alternate 2D detector | Keep behind the same interface. Not shipped; available for A/B validation. |
| HRPose / HRNet-small | Adaptive tier upgrade | Defer until MediaPipe proves inadequate. |

**Server (prep in parallel to hardware arrival):**

| Model | Role | License concern | Action |
|---|---|---|---|
| **WHAM** (Shin 2024) | Monocular video → world-grounded 3D SMPL pose | Max Planck research license (**non-commercial** — IP-lawyer clearance required before productization; AMASS pretraining-inheritance risk) | Clone, containerize inference, package as a subprocess called by the pipeline. |
| **OpenCap Monocular** (Gilon 2026) | WHAM pose → OpenSim IK/ID → joint moments, GRFs, muscle forces | **PolyForm Noncommercial 1.0.0** on code (productization flag) | Register SimTK account; test the hosted `opencap.ai` inference endpoint with a sample clip before committing to self-hosting. Hosted is acceptable for capstone demo; self-host is the launch target. |
| **HSMR** | Rollup spine sequencing via SKEL joint-limit-respecting representation | Research | Defer until rollup is confirmed in the 4-movement protocol. Protocol hooks already in L2 Plan 4. |
| **Sabo 2026 Beighton scorer** | Optional premium hypermobility screen | Research | Defer past v1. |

**Explicitly not adopted:**

- MotionBERT — superseded by WHAM+OpenCap Monocular path. Literature-interesting, not on the build path.
- TCPFormer — no released code.
- ViTPose — not adopted at launch.
- True output-ensembling of multiple 3D lifters — Miller 2025 shows hybrid ML+sim beats averaging; latency cost is not worth the marginal accuracy.

### 2.2 Per-movement stage dispatch

Uses the existing `MovementType` dispatch + `PhaseSegmenter` protocol from L2 Plan 4. No architectural change.

| Movement | Stage stack |
|---|---|
| Overhead squat | MediaPipe → WHAM → OpenCap Monocular → rule reasoner |
| Single-leg squat | Same, plus hip-adduction rule (Harris-Hayes 2018) |
| Push-up | Same, upper-body-emphasis rule subset |
| Rollup | MediaPipe → HSMR (spine detail) → phase segmenter → rule reasoner |
| (future) Beighton onboarding | MediaPipe → Sabo classifier |

### 2.3 Sampled parallel cross-check

Run HSMR on a ~5% sample of frames in parallel with WHAM and flag divergence (SKEL joint-limit pose vs. WHAM SMPL pose) above a threshold. Log-and-alert, do not block. Cheap sanity layer, not in the hot path. **This is a validation mechanism, not an ensemble.**

---

## 3. Data strategy

Ordered by actual need:

1. **Our own calibration dataset (blocker for real rule thresholds).** 20–30 subjects × 4 movements × ≥5 reps, intake limited to age, sex, height, weight, hypermobility self-report. Required to calibrate rule thresholds to what *our* pipeline measures, to validate phone-to-server round-trip, and to ground-truth the synthetic fixtures in L2 Plan 4. Collected alongside team members and friends.
2. **PT-annotated evaluation sample.** 5–10 subjects scored by a PT. Not training data — evaluation data for quoting clinician-agreement numbers in the capstone demo.
3. **Public datasets (optional).** Relevant only if we observe a specific failure mode or decide to publish. The literature-synthesis deep-read catalogs the full landscape; the engineering priority order is:
   1. OpenCap public dataset (Uhlrich 2023) via SimTK DUA — only dataset whose distribution matches our product. Register first.
   2. Fit3D / AIFit — movement-screening coverage of squat/lunge/plank.
   3. Human3.6M — only if fine-tuning WHAM.
   4. Everything else — only if the specific failure mode forces it. AMASS is CC BY-NC and inherits into WHAM weights — do not touch casually.

### 3.1 Acquisition timeline

- Week 1: register OpenCap SimTK account, submit DUA.
- Week 2: collect our own calibration sessions alongside L2 Plan 4 synthetic-fixture development.
- Week 3 (stretch): download Fit3D, evaluate pipeline on a subset.
- Week 4+: AMASS / Human3.6M / etc. only on failure-mode trigger.

### 3.2 Training reality check

We do not retrain WHAM, HSMR, or OpenCap Monocular for MVP. All three have published accuracy inside our envelope. What we *do* train:

- **Body-type adjustment thresholds** on our own data (deferred-to-L3 in Plan 2).
- **Per-movement reference reps** for the DTW reference library (L2 Plan 3 + synthetic fixtures from Plan 4).
- **Learned chain reasoner (GNN)** — deferred post-launch per research-integration-report §6.3. Still the right call.

---

## 4. Multi-model strategy

Three patterns:

- **Sequential (the main pipeline).** `MediaPipe → WHAM → OpenCap Monocular → rule reasoner → report`. Not an ensemble; each stage consumes the previous. Default path.
- **Per-movement dispatch.** Already provisioned by L2 Plan 4 via `MovementType`. See §2.2.
- **Sampled parallel cross-check.** HSMR on 5% of frames as a sanity layer. See §2.3.

**Not doing:** true output-ensembling (averaging outputs from multiple lifters). Justified in §2.1.

---

## 5. Team decisions (prior Section 10 — landed)

### Q1: Rollup inclusion in the 4-movement protocol

**Status:** Blocked on Rajiv. No plan change until he reports back. L2 Plan 4's rollup stub is an interface, not an implementation.

### Q2: Server dependency for free tier

**Team response:** *"minimal cost to us is fine. we want the free tier to be good enough that the premium is irresistible. free is not our target audience, premium will make up for the cost."*

**Decision:** Free tier gets server-processed results. Compute location is decoupled from tier; tier is set by **feature depth**, not by where compute runs.

- Free tier: overall quality score, top-level chain flags, 1–2 "biggest finding" callouts. No full chain narrative, no per-rep trends, no temporal cross-movement analysis, no body-type-adjusted thresholds.
- Premium tier: full chain narrative, per-rep metrics, temporal trends, body-type adjustments, SKEL spine detail for rollup, (future) sEMG integration.
- Cost controls: cache server results by session hash, reject obvious-junk uploads at the quality gate, rate-limit per device.

### Q3: Body-type scope at launch

**Team response:** *"no questionnaire imo, keep onboarding cognitive load small bc it's already a LOT"*

**Decision:** No intake questionnaire. Body-type signal is the SKEL `β` shape parameters, auto-extracted from the HSMR / OpenCap Monocular forward pass. No user action required.

- Remove `BodyTypeProfile` questionnaire task from L2 Plan 2 scope. Downgrade to an optional field populated from server-side analysis.
- Populate `BodyTypeProfile` from `SkeletonFitter` stage output.
- Premium-only at launch: server runs the full HSMR/OpenCap Monocular path for `β` extraction.
- **Free-tier body-type handling:** run the premium pipeline once at onboarding, cache the `β` vector, apply to every subsequent free-tier session. One expensive run per user, trivial at capstone scale, keeps free-tier results body-adjusted.

### Q4: Graph NN vs rule-based chain reasoning at launch

**Team response:** *"yeah training data would be ideal - that's up to your timeline aaron"*

**Decision:** Ship v1 rule-based. GNN is post-launch.

- No labeled training data today. Capstone timeline doesn't fit collection + labeling + training + validation before the demo.
- Joyce 2023 critique of the MSI framework applies to any learned chain classifier trained on MSI-style labels. Weak labels, weak model.
- Rule-based is auditable, deterministic, and maps cleanly to the `evidence:` citation fields that anchor each rule to a mechanism paper.
- "Our rule set is inspectable" is the GTM story for open-source / wellness positioning.
- Path to GNN: collect labeled data months 1–3 post-launch, train month 4, ship v2.

**Plan impact:** L2 Plan 2 stays rule-based-only. Do not add GNN to the current epoch.

### Q5: Premium pricing

Folded into Q2. Dollar amount is a GTM decision, not a plan decision.

### Q6: Chain-reasoner architecture options

Team asked for options with tradeoffs on the architectural choices that aren't obvious. The tightest question is the chain-reasoner architecture, because it drives ~80% of the ML scope.

#### Option A — Pure rule-based YAML, no ML in the reasoner (**chosen for v1**)

Rules in `config/rules/*.yaml`. Each rule declares metric, threshold, chain, severity mapping, and an `evidence:` block citing the anchor paper. Reasoner is deterministic: evaluate all rules, emit observations, assemble report.

**Pros:** Fastest to ship. Fits L2 Plan 2 scope unchanged. Deterministic, auditable, no training data needed. Matches open-source/wellness positioning. Trivial to update (edit YAML, redeploy). Anchored to the evidence we actually have (Harris-Hayes, Hewett, Uhlrich-for-when-garment-arrives).

**Cons:** Can't capture emergent multi-joint patterns that aren't rule-table-encodable. Less impressive as a capstone headline than "GNN on skeleton graph". Every new rule is a human-authoring step.

**Cost:** Baseline (already in L2 Plan 2).

#### Option B — Rule-based + lightweight learned confidence layer (post-launch path)

Same rule-based engine, plus a small learned model (logistic regression or gradient boosting) that takes each rule's evidence dict + body-type vector + trend metrics and outputs confidence in [0,1]. The rule still decides *what* to flag; the learned layer decides *how sure we are*.

**Pros:** Rules stay explicit (auditable). Confidence reflects real population variance. Trainable from tens–low-hundreds of labeled sessions. "Learned component" for capstone narrative without betting the product. A/Bs cleanly against pure rule-based.

**Cons:** Requires labeled dataset (we don't have one). Adds model registry + training loop. User-facing story is harder ("why is the same flag showing different confidence?").

**Cost:** ~1 extra task in L2 Plan 2 + a data-collection effort that blocks training.

#### Option C — GNN chain reasoner from day one (explicitly rejected for v1)

Skeleton as graph, GCN propagates joint features along edges, output is per-chain involvement probability. Rules demoted to fallback or removed.

**Pros:** Strongest capstone technical narrative. Captures multi-joint patterns rules can't. Maps to the research-integration-report §2.5 aspirational architecture.

**Cons:** Requires labeled training data we don't have (hundreds of PT-reviewed sessions). Inherits the MSI-label validity problem (Joyce 2023). Hard to explain to users, hard to debug for us. Retraining instead of YAML edits when wrong. **Capstone risk:** if the model doesn't converge by demo day, we have nothing.

**Cost:** Multi-month effort. Blocks launch.

**Decision:** Option A at launch. Option B as the follow-on once calibration data exists. Option C only as a research publication exercise later.

---

## 6. Phone / Flutter teammate handoff

> Copy this section verbatim to the phone teammate when they start integration.

### 6.1 Model to integrate now

**MediaPipe BlazePose Full** — `pose_landmarker_full.task`. MediaPipe Tasks API.

- Apache 2.0.
- 33 keypoints per frame (canonical BlazePose order). Each landmark: `x`, `y` normalized ∈ [0,1], `z` relative depth, `visibility` ∈ [0,1], `presence` ∈ [0,1].
- Target capture frame rate: 30 fps. MediaPipe should sustain ≥15 fps on mid-range Android, ≥25 fps on flagship.
- Flutter: `google_mlkit_pose_detection` package OR the direct MediaPipe Tasks plugin (the task file is more flexible for swapping models later).

### 6.2 What to send to the server

Two streams per session as one `POST /sessions` request body matching the pydantic schema at `software/server/src/auralink/api/schemas.py`:

1. `metadata: SessionMetadata`:
   - `movement`: one of `"overhead_squat" | "single_leg_squat" | "push_up" | "rollup"`
   - `device`: phone model string
   - `model`: `"mediapipe_blazepose_full"` (fixed for now; field exists for future swaps)
   - `frame_rate`: measured capture fps
   - `captured_at`: ISO8601 UTC timestamp
2. `frames: list[Frame]`: one entry per captured frame with `timestamp_ms: int` and `landmarks: list[Landmark]` (exactly 33 or the server rejects the request).

Also include the raw video as a separate multipart upload (endpoint to be added — coordinate with the server team). The server needs raw video for the WHAM + OpenCap Monocular premium path; landmarks alone are insufficient for kinetics.

### 6.3 Design constraints

1. **On-device pose model lives behind a small Dart interface.** Goal: swap MediaPipe → MoveNet → HRPose without an app release. Interface emits `Frame` objects matching the server schema regardless of backend.
2. **No chain reasoning or risk flagging on the phone.** Phone jobs: capture, progressive setup-quality validation (research-integration-report §1.2), live skeleton overlay, rep counting for UX feedback, upload. Server owns everything else.
3. **Real-time skeleton overlay with confidence colors.** Low-visibility landmarks render dim/red. This is the empirically justified setup-quality lever from research-integration-report §1.2 (real-world accuracy drops ~20pp without it).
4. **No questionnaire at onboarding.** Team decision Q3. Capture height/weight only if absolutely required, and push for server-side auto-estimation first.
5. **No account-creation gating for the free flow.** Low-friction onboarding is the free-tier pitch.

### 6.4 What the server returns (for the phone to render)

`GET /sessions/{id}/report` — see `software/server/src/auralink/api/routes/reports.py` and the forthcoming `report/schemas.py` from L2 Plan 2. Expect:

- A `quality` block (setup quality, frame-rate quality, visibility quality).
- A list of `ChainObservation`s, each with `chain`, `severity`, `confidence`, `trigger_rule`, `narrative`, `evidence` dict.
- Movement-specific per-rep metrics and within-movement trends (premium only for now).
- A top-level narrative string.

Render narrative in the primary card; surface severity-sorted observations as cards below.

### 6.5 Later, not now

- MoveNet Thunder fallback.
- HRPose adaptive-tier selector.
- Video Beighton onboarding flow.
- sEMG garment pairing.

Do not preemptively build these.

---

## 7. Action list

| # | Owner | Action | Blocks |
|---|---|---|---|
| 1 | Phone teammate | Integrate MediaPipe BlazePose Full behind a swap interface; implement upload to `POST /sessions` matching the current pydantic schema | Nothing — can start today |
| 2 | Aaron | Register for OpenCap SimTK DUA; test hosted `opencap.ai` endpoint with a sample clip | Empirical validation of pipeline swap |
| 3 | Aaron | Set up WHAM + OpenCap Monocular inference container on a server | Premium pipeline end-to-end demo |
| 4 | Aaron | Revise L2 Plan 2: (a) remove questionnaire, (b) add `evidence:` block to rule YAML format, (c) document the MSI cherry-pick stance in rule docstrings, (d) populate `BodyTypeProfile` from `SkeletonFitter` output | Plan 2 execution |
| 5 | Aaron | Amend `research-integration-report.md` with a pipeline-revision note pointing at this doc | Team clarity |
| 6 | Aaron | Collect calibration dataset: 20–30 subjects × 4 movements (team + friends) alongside L2 Plan 4 | Rule-threshold tuning |
| 7 | Rajiv | Confirm whether rollup is in the 4-movement protocol | Research gap §7.1 prioritization |
| 8 | Team | Review this doc and confirm the pipeline + Section 10 decisions | Unblocks plan updates |

---

*Authoritative 2026-04-10 engineering decision. Literature rationale in `research/synthesis/deep-read-monocular-pipeline-landscape-2026-04-10.md` (sibling research repo). Paired with `deep-read-sensing-2026-04-10.md` (sibling repo) and `deep-read-biomech-2026-04-10.md` (sibling repo). Supersedes the pipeline section of `docs/operations/comms/research-integration-report.md` §2.4.*
