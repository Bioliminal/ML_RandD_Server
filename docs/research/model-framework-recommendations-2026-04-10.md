# Model + Framework Recommendations — AuraLink 2026-04-10

**Audience:** AuraLink team.
**Purpose:** Given the 16 papers added on 2026-04-10, decide (a) which models/frameworks to prep for when the hardware lands, (b) where training data comes from if we need to fine-tune, (c) multi-model strategy, (d) what ships to the mobile teammate, and (e) how to land the Section 10 decisions from the research integration report.
**Upstream:**
- `docs/operations/comms/research-integration-report.md` (2026-04-09 snapshot; superseded in the pipeline-choice section by this doc)
- `docs/research/deep-read-sensing-2026-04-10.md` (per-paper sensing extraction)
- `docs/research/deep-read-biomech-2026-04-10.md` (per-paper biomechanics extraction)

---

## 1. TL;DR

1. **Swap the premium pipeline backbone from MotionBERT+HSMR → WHAM + OpenCap Monocular + kinetics** (Gilon 2026). It's single-phone, already integrates WHAM, gives us joint moments + GRFs + muscle forces out of the box, and is open source at the same `github.com/utahmobl` / `simtk.org/opencap` family. Keep HSMR as a parallel branch specifically for rollup spine sequencing.
2. **Phone teammate ships MediaPipe BlazePose Full.** No other model belongs on the phone at launch. Keep the capture layer model-agnostic so MoveNet/HRPose can be swapped in later.
3. **Fine-tuning is optional for MVP.** Ship with pretrained MediaPipe + OpenCap Monocular. Collect our own ~20–30 subjects × 4 movements for calibration and rule-threshold tuning. Larger datasets (Human3.6M, AMASS, OpenCap public dataset, Fit3D) become relevant only if we observe specific failure modes or want to publish.
4. **MSI framework: cherry-pick.** Adopt Sahrmann-style kinematic pattern rules with outcome citations. Reject the MSI diagnostic labels as report outputs — Van Dillen 2016 (Level 1 RCT) shows the classification didn't beat generic training, and Joyce 2023 critiques the validity of the labels.
5. **Team Section 10 decisions** are actionable now; one open item (Q6: chain reasoner architecture) gets an options-with-tradeoffs section below.

---

## 2. Which models to prep for when the hardware lands

"Hardware" here is the sEMG garment (research-integration-report hardware track). The *pose/video* pipeline doesn't depend on the hardware arriving, so I'm interpreting "prep once hardware is in" as the full-stack model prep we need ready for end-to-end demos.

### 2.1 Phone / client models — ship now

| Model | Role | Why | Status |
|---|---|---|---|
| **MediaPipe BlazePose Full** (`pose_landmarker_full.task`) | On-device 2D keypoints + live guidance | Already in the server schema; Flutter plugin; Apache 2.0; baseline accuracy sufficient for setup validation and rep gating | Ship |
| **MoveNet Thunder (TF Lite)** | Alternate 2D keypoint benchmark | Google alternate, arguably better on fast motion; useful as an A/B baseline during validation | Keep behind interface |
| **HRPose / HRNet-small (ONNX Runtime Mobile or TF Lite)** | Adaptive tier upgrade on capable phones | Better accuracy on occlusion / fast motion; research-integration-report §1.4 | Defer until MediaPipe proves inadequate |

**Action for the phone teammate:** see §7 for the exact hand-off package.

### 2.2 Server models — prep in parallel to hardware

| Model | Role | License | Hosting | Action |
|---|---|---|---|---|
| **WHAM** (Shin 2024) | Monocular video → world-grounded 3D SMPL pose | **Max Planck research license (non-commercial)** — flag for any productization | GPU server | Clone, set up inference container; package as a subprocess called by our pipeline |
| **OpenCap Monocular** (Gilon 2026) | Refines WHAM pose → biomechanically constrained kinematics → joint moments + GRFs + muscle forces | Research (SimTK / OpenSim ecosystem) | GPU server; **opencap.ai offers free hosted inference** | Register a SimTK account now; test hosted endpoint with a sample clip before committing to self-hosting |
| **HSMR** (Xia et al., CVPR — already in `sensing/biomechanically-accurate-skeleton.pdf`) | Single-image SKEL biomechanical skeleton — used for **spine sequencing in rollup** | Research | GPU server | Defer until rollup is prioritized; keep the protocol hooks from L2 Plan 4 |
| **Sabo 2026 Beighton scorer** | Optional premium hypermobility screen | Research | Can run on phone (MobileNet backbone) or server | Defer past v1 per research-integration-report §5.3 |

**Not planned for prep:**
- **MotionBERT** — replaced in the pipeline by WHAM+OpenCap Monocular. Still worth knowing for literature context but no longer on the build path.
- **TCPFormer** — code not released as of this review; re-evaluate when it is.
- **ViTPose** — useful as a mid-tier 2D detector, but we're not adopting it at launch.

### 2.3 Pipeline deltas vs the research integration report

The research integration report §2.4 prescribes `MediaPipe → MotionBERT → HSMR → chain reasoning`. After the deep read:

```
                   on-device                                          server-side
  +-----------+    +----------------+   upload    +------+     +--------------------+     +---------------------+
  | phone cam | -> | MediaPipe Full | ----------> | WHAM | --> | OpenCap Monocular  | --> | rule-based chain    |
  +-----------+    +----------------+             +------+     | (opt + kinetics)   |     | reasoning + report  |
                                                                +--------------------+     +---------------------+
                                                                         |
                                                                         v (for rollup only)
                                                                   +----------+
                                                                   |   HSMR   |
                                                                   | (SKEL    |
                                                                   |  spine)  |
                                                                   +----------+
```

Why: OpenCap Monocular gives us *kinetics* (joint moments, GRFs, muscle forces) not just pose. Our rule thresholds (Hewett, Harris-Hayes) are defined on kinetics. MotionBERT+HSMR would have stopped at pose and we'd still have owed a kinetics layer. See `deep-read-sensing-2026-04-10.md` §Pipeline architecture for the full argument.

---

## 3. Data — where it comes from, how much we need

### 3.1 What we need, ordered by actual need

1. **Our own calibration dataset (blocker for good rule thresholds).** Capstone-scale feasible: 20–30 subjects × 4 movements × ≥5 reps, with basic intake (age, sex, height, weight, hypermobility self-report). Required for: calibrating rule thresholds to what our pipeline actually measures, validating phone-to-server round-trip, fixture data for L2 Plan 4's synthetic generator.
2. **PT-annotated sample (blocker for "real" evaluation).** Subset (5–10 subjects) where a PT scores the same session. Lets us quote clinician-agreement numbers in the final report and the capstone demo. Not a training dataset — an evaluation dataset.
3. **Public datasets (optional, for fine-tuning or publication).** See table below. Only relevant if we observe a specific failure mode or decide to publish a rule-calibration paper.

### 3.2 Public datasets available

| Dataset | Size | License | Best for | Priority |
|---|---|---|---|---|
| **OpenCap public dataset** (Uhlrich 2023) | 100+ subjects, smartphone video + marker mocap + force plates | DUA via SimTK | **Highest relevance.** Direct distribution match. | **Acquire first.** Register on SimTK. |
| **Fit3D / AIFit** | Fitness videos + 3D pose (squats, lunges, planks) | Academic | Squat / single-leg-squat movement-screening validation | Acquire if OpenCap doesn't cover our movements |
| **Human3.6M** | 3.6M frames, 11 subjects | Academic registration | Classic 3D pose benchmark | Only if fine-tuning WHAM |
| **AMASS** | 15M+ frames, 300+ subjects | **CC BY-NC 4.0** (non-commercial) | Sanity benchmark for rollup and ADL; backbone pretraining | Non-commercial license blocks future productization — use cautiously |
| **BEDLAM** | 380k synthetic frames | CC BY 4.0 | Clean-ground-truth augmentation for 3D lifters | Only if fine-tuning |
| **3DPW** | 60k in-the-wild frames | CC BY 4.0 | Monocular robustness eval | Eval only |
| **MPI-INF-3DHP** | 1.3M frames, 8 subjects | Academic | 3D lift fine-tuning | Only if fine-tuning |
| **COCO Keypoints** | 200k images | CC BY 4.0 | 2D pose fine-tuning (ViTPose-S, not MediaPipe) | Only if we swap 2D backbone |
| **MOYO** | Extreme yoga poses | Research | Joint-limit stress test (where HSMR wins) | Already cited; no action |

**Aaron's realistic acquisition timeline:**
- Week 1: Register OpenCap SimTK; request DUA.
- Week 2: Collect our own calibration sessions (team members + friends) alongside Plan 4 synthetic fixture development.
- Week 3: Stretch — download Fit3D, evaluate pipeline on a subset.
- Week 4+: Only touch AMASS/Human3.6M/etc. if a specific failure mode forces it.

### 3.3 Post-training reality check

We should not plan to **retrain** WHAM, HSMR, or OpenCap Monocular for MVP. All three have published accuracy within the envelope we need. What we do need:

- **Fine-tune body-type adjustment thresholds** on our own data (Plan 2 deferred-to-L3 item).
- **Fine-tune per-movement reference reps** (Plan 4 synthetic + Plan 3 DTW reference library) on a mix of synthetic + real captures.
- **Eventually train a learned chain reasoner (GNN)** — deferred post-launch per research-integration-report §6.3; still the right call.

---

## 4. Multi-model strategy

Three patterns, each with a concrete use:

### 4.1 Sequential (the main pipeline)
`MediaPipe → WHAM → OpenCap Monocular → rule reasoner → report`. Not an ensemble; each stage consumes the previous. This is the default path.

### 4.2 Per-movement dispatch (recommended, already matches L2 architecture)
Different movements route to different stage stacks via the orchestrator's `MovementType` dispatch:

| Movement | Stage stack |
|---|---|
| Overhead squat | MediaPipe → WHAM → OpenCap Monocular → rule reasoner |
| Single-leg squat | Same, plus hip-adduction-specific rule (Harris-Hayes 2018) |
| Push-up | Same, with upper-body-emphasis rule subset |
| Rollup | MediaPipe → HSMR (spine detail) → phase segmenter → rule reasoner |
| (future) Beighton onboarding | MediaPipe → Sabo classifier |

This is what L2 Plan 4 already provisions with the `MovementType` dispatch + `PhaseSegmenter` protocol. No architectural change needed — we just wire the real stages into the existing slots.

### 4.3 Parallel cross-check (sampled, for validation only)
On a ~5% sample, run HSMR in parallel with WHAM and flag frames where the SKEL joint-limit-respecting pose diverges more than a threshold from the WHAM SMPL pose. Log-and-alert, don't block. Cheap sanity layer; not in the hot path.

**Don't do:** true ensembling (averaging outputs from multiple lifters). Miller 2025 already established that the hybrid physics+ML approach beats pure averaging, and the latency cost of running two lifters end-to-end is not worth the marginal accuracy gain.

---

## 5. Section 9 — Papers to Acquire status after this batch

From `research-integration-report.md §9`:

| Paper | Status |
|---|---|
| MotionBERT (Zhu 2023) | ❌ Still not in collection. **De-prioritized** — superseded by WHAM/OpenCap Monocular path. |
| "Real time action scoring system" Sci Rep 2025 (DTW/NCC) | ❌ Still needed. Blocks full confidence in L2 Plan 3 methodology. |
| Beighton video scoring (Sabo 2026) | ✅ Acquired. |
| Sahrmann MSI framework | ✅ Partially acquired. Have Sahrmann 2017 + 2021, Van Dillen 2016 RCT (the decisive evidence), Harris-Hayes 2016/2018 (the actionable mechanism), Joyce 2023 critique. Enough to write the `evidence:` blocks for Plan 2 rules. |
| Lumbar-pelvic rhythm studies | ❌ Still needed for rollup reference pattern (research gap §7.4). |
| TCPFormer | ✅ Acquired. Not actionable (no code). |
| Enhanced Action Quality Assessment ECCV 2024 | ❌ Still needed. |
| **OpenCap database** | ✅ **Effectively acquired** — OpenCap (Uhlrich 2023), OpenCap Monocular (Gilon 2026), Hybrid ML+Sim (Miller 2025), WHAM (Shin 2024), Rajagopal 2016 MSK model, best-practices.html. Biggest original gap; now closed. |
| FMS/SFMA spine criteria | ❌ Still needed for normative rollup data. |

**Newly acquired, not originally on the Section 9 list but important:**
- **WHAM** (Shin 2024) — critical, it's the backbone of OpenCap Monocular.
- **Rajagopal 2016** — the MSK model under OpenCap.
- **Uhlrich 2022 muscle coordination retraining** — directly validates the sEMG garment's intervention story.
- **ViTPose** — mid-tier 2D option.
- **Van Dillen 2016 RCT** — the strongest piece of clinical evidence, and its verdict is "MSI classification ≠ better outcomes."

**Still-needed list, ranked for the next research pass:**
1. **OpenCap public dataset access** (SimTK DUA) — unblocks real evaluation data.
2. **FMS/SFMA spine criteria** — unblocks rollup reference patterns.
3. **Lumbar-pelvic rhythm normative studies** — same.
4. "Real time action scoring system" Sci Rep 2025 — unblocks Plan 3 DTW/NCC ground truth.
5. Everything else is optional.

---

## 6. Section 10 — Team decisions landed, plus options for Q6

Recap of the team responses and the action each triggers.

### Q1: Rollup inclusion in the 4-movement protocol
**Response:** *"rajiv is looking into this i think"*
**Status:** Open; blocker on research-integration-report §7.1, §7.3, §7.4.
**Action:** Waiting on Rajiv. No plan change until he reports back. In the meantime, Plan 4's rollup stub stands — we have an interface, not an implementation.

### Q2: Server dependency for free tier
**Response:** *"minimal cost to us is fine. we want the free tier to be good enough that the premium is irresistible. free is not our target audience, premium will make up for the cost of the free tier if we design it correctly"*
**Decision:** **Free tier gets server-processed results.** Compute location decouples from tier (already the plan of record in research-integration-report §2.1). Free tier uploads to the server and gets a server-generated report, just with a narrower feature set.
**Action:**
- Set tier by **feature depth**, not compute location.
- Free tier features: overall quality score, top-level chain flags, 1–2 "biggest finding" callouts, no full chain narrative, no per-rep trend plots, no temporal cross-movement analysis, no body-type-adjusted thresholds.
- Premium tier adds: full chain narrative, per-rep metrics, temporal trends, body-type adjustments, SKEL spine detail for rollup, (future) sEMG integration.
- Cost control: cache server results by session hash; reject obvious-junk uploads at the quality gate; rate-limit per device.

### Q3: Body type scope at launch
**Response:** *"no questionnaire imo, keep onboarding cognitive load small bc it's already a LOT"*
**Decision:** **No intake questionnaire.** Use SKEL `β` shape parameters (auto-extracted from the HSMR / OpenCap Monocular forward pass) as the body-type signal. No user action required.
**Action:**
- Remove the `BodyTypeProfile` questionnaire task from L2 Plan 2 scope (Task 2 currently plans for it — downgrade to an optional field populated from server-side analysis, not user input).
- Populate `BodyTypeProfile` from the `SkeletonFitter` stage output.
- Premium only at launch: server runs full HSMR/OpenCap Monocular. Free tier gets an un-adjusted report until/unless we add auto body-type from MediaPipe 2D proxies (height-from-limb-ratio is possible; accuracy is unvalidated for us).
- **Open sub-question:** does the free tier skip body-type adjustment entirely, or do we run the premium pipeline once per user at onboarding and cache the `β` vector? Recommended: the latter. One expensive run per user, cached forever, applied to every subsequent free-tier session. Cost is trivial at capstone scale.

### Q4: Graph NN vs rule-based chain reasoning at launch
**Response:** *"yeah training data would be ideal - that's up to your timeline aaron"*
**Decision (my judgment call):** **Ship v1 with rule-based.** Train the GNN post-launch once we have real data.
**Reasoning:**
- We do not have labeled training data today. Capstone timeline doesn't accommodate collecting + labeling + training + validating a GNN before the demo.
- Joyce 2023 critique applies directly to learned chain classifiers trained on MSI-style labels. If our labels are weak, our GNN is weak.
- Rule-based is auditable, deterministic, and maps cleanly to the `evidence:` citation fields (see §7 of `deep-read-biomech-2026-04-10.md`).
- Rule-based + YAML config is also the open-source story for the GTM plan — "our rule set is inspectable" is better than "our weights are a black box."
- GNN remains on the roadmap: collect labeled data in months 1–3 post-launch, train in month 4, ship v2.

**Action:** Keep L2 Plan 2 as rule-based-only. Don't add GNN to the epoch.

### Q5: Premium pricing
**Response:** *"already answered in 2"*
**Decision:** Folded into Q2 — premium is "the one you actually want," free is the funnel. Pricing dollar amount is a GTM decision, not a plan decision.
**Action:** None technical. Note in the decision log.

### Q6: "Give us suggestions… options with reasoning, tradeoffs, pros, cons"

I'm reading this as the team asking for options on the architectural choices that aren't obvious. The best fit is **the chain-reasoner architecture at launch** — i.e., how much mechanism we bake in, because it drives 80% of the ML scope. Here are three options:

#### Option A — Pure rule-based YAML, no ML in the reasoner (recommended for v1)

**How it works:** Rules live in `config/rules/*.yaml`. Each rule declares metric, threshold, chain, severity mapping, and an `evidence:` block citing the paper that grounds it. The reasoner is deterministic: evaluate all rules, emit observations, assemble report.

**Pros:**
- Fastest to ship. Fits the current L2 Plan 2 scope without modification.
- Deterministic, auditable, no training data required.
- Plays well with the open-source / wellness positioning — "our rules are inspectable."
- Trivial to update: edit a YAML file, redeploy, no retraining.
- Lines up with the evidence we actually have — Harris-Hayes 2018 gives us one mechanistic rule; Hewett gives us another; Uhlrich gives us the EMG rule (for when the garment exists).

**Cons:**
- Can't capture emergent multi-joint patterns that aren't in the rule table.
- "Rule-based" is less impressive as a capstone headline than "GNN on skeleton graph."
- Every new rule is a human-authoring step.

**Cost:** Baseline (already in the L2 plan).

#### Option B — Rule-based + lightweight learned confidence layer

**How it works:** Same rule-based engine. For each observation, a small learned model (logistic regression or gradient boosting) takes the rule's raw evidence dict + the body-type vector + the trend metrics and outputs a *confidence* in [0,1]. The rule still decides *what* to flag; the learned layer decides *how sure we are*.

**Pros:**
- Still auditable (rules are explicit), but the confidence values reflect real population variance.
- Trainable from a small dataset (tens to low hundreds of labeled sessions).
- Gives the capstone a "learned component" without betting the product on an unproven model.
- Easy A/B against pure rule-based.

**Cons:**
- Still requires a labeled dataset (which we don't have yet).
- Adds a model registry path and a training loop to the codebase for marginal gain.
- Confusing story for users — why is the *same* flagged angle producing different confidence numbers?

**Cost:** ~1 extra task in L2 Plan 2, plus a data-collection effort that blocks training.

#### Option C — Graph Neural Network chain reasoner from day one

**How it works:** Skeleton as graph, GCN propagates joint features along edges, output is per-chain involvement probability. Rules-based reasoner replaced or demoted to a fallback.

**Pros:**
- Strongest capstone technical narrative.
- Captures multi-joint patterns rule tables can't.
- Directly maps to the research-integration-report §2.5 aspirational architecture.

**Cons:**
- **Requires labeled training data we don't have.** At minimum hundreds of labeled sessions with PT-reviewed chain-involvement labels.
- Joyce 2023 critique applies: our labels would inherit the validity problems of the MSI framework we just decided to cherry-pick rather than adopt wholesale.
- Hard to explain to users; hard to debug for us.
- If the model is wrong, we can't edit a YAML file to fix it — we retrain.
- High capstone risk: if the model doesn't converge by the demo, we have nothing.

**Cost:** Multi-month effort; blocks launch.

**My recommendation: Option A at launch, Option B as a follow-on post-launch once calibration data is collected, Option C only as a research publication exercise later.**

This also happens to be what the team hinted at in their Q4 response ("training data would be ideal — up to your timeline"). Aaron's timeline doesn't support Option C pre-launch. Option A is the honest choice; Option B is the growth path.

---

## 7. Hand-off package for the phone / Flutter teammate

> Copy this section verbatim to the phone teammate.

### 7.1 Model to integrate now

**MediaPipe BlazePose Full** — `pose_landmarker_full.task`. Google MediaPipe Tasks API.
- Apache 2.0 license.
- 33 keypoints per frame (canonical BlazePose order).
- Each landmark: `x`, `y` normalized ∈ [0,1], `z` relative depth, `visibility` ∈ [0,1], `presence` ∈ [0,1].
- Target frame rate: 30 fps capture, MediaPipe running at whatever fps the phone can sustain (target ≥ 15 fps on mid-range Android, ≥ 25 fps on flagship).
- Flutter integration: `google_mlkit_pose_detection` package OR direct MediaPipe Tasks plugin (the task file is more flexible for swapping models later).

### 7.2 What to send to the server

Two streams per session, uploaded as one `POST /sessions` request body matching the pydantic schema at `software/server/src/auralink/api/schemas.py`:

1. **`metadata: SessionMetadata`**
   - `movement`: one of `"overhead_squat" | "single_leg_squat" | "push_up" | "rollup"`
   - `device`: phone model string
   - `model`: `"mediapipe_blazepose_full"` (fixed for now; exists as a field so we can swap later)
   - `frame_rate`: actual measured capture fps
   - `captured_at`: ISO8601 UTC timestamp
2. **`frames: list[Frame]`** — one entry per captured frame, each with `timestamp_ms: int` and `landmarks: list[Landmark]` (exactly 33 landmarks or the server rejects the request).

Also include the raw video as a separate multipart upload (endpoint to be added — coordinate with server team). The server needs the raw video for the WHAM + OpenCap Monocular premium pipeline; BlazePose landmarks alone are insufficient for 3D kinetics.

### 7.3 Design constraints

1. **Keep the on-device pose model behind a small Dart interface.** Goal: swap MediaPipe → MoveNet → HRPose without an app release. The interface produces `Frame` objects matching the server schema regardless of the backend.
2. **Don't do any "chain reasoning" or "risk flagging" on the phone.** That belongs on the server. The phone's jobs are: capture, setup validation (progressive requirement checks per research-integration-report §1.2), live skeleton overlay, rep counting for UX feedback, and upload.
3. **Show real-time skeleton overlay with confidence colors.** Low visibility on a landmark → dim / red. This is the empirically justified setup-quality lever from research-integration-report §1.2 (real-world accuracy drops ~20pp without it).
4. **Do not ship a questionnaire at onboarding.** Team decision Q3. Capture height/weight only if absolutely required for a specific movement's calibration, and even then push for auto-estimation on the server side first.
5. **No account-creation gating for the free flow.** Low-friction onboarding is the free-tier pitch.

### 7.4 What the server will return (for the phone to render)

`GET /sessions/{id}/report` — see `software/server/src/auralink/api/routes/reports.py` and the forthcoming `report/schemas.py` from L2 Plan 2. Expect:
- A `quality` block (setup quality, frame-rate quality, visibility quality).
- A list of `ChainObservation`s, each with `chain`, `severity`, `confidence`, `trigger_rule`, `narrative`, `evidence` dict.
- Movement-specific per-rep metrics and within-movement trends (premium only for now).
- A top-level narrative string.

Render the narrative string in the primary card; surface severity-sorted observations as cards below it.

### 7.5 Later, not now (don't preemptively build these)

- MoveNet Thunder fallback.
- HRPose adaptive-tier selector.
- Video Beighton onboarding flow.
- sEMG garment pairing.

---

## 8. Action list (who does what next)

| # | Owner | Action | Blocks |
|---|---|---|---|
| 1 | Phone teammate | Integrate MediaPipe BlazePose Full behind a swap interface; implement upload to `POST /sessions` matching the current pydantic schema | Nothing — can start today |
| 2 | Aaron | Register for OpenCap SimTK DUA; test hosted opencap.ai endpoint with a sample clip | Empirical validation of the pipeline swap |
| 3 | Aaron | Set up WHAM + OpenCap Monocular inference container on a server | Premium pipeline end-to-end demo |
| 4 | Aaron | Revise L2 Plan 2 to: (a) remove questionnaire, (b) add `evidence:` block to rule YAML format, (c) document the MSI cherry-pick stance in rule docstrings, (d) add `BodyTypeProfile` auto-population from `SkeletonFitter` output | Plan 2 execution |
| 5 | Aaron | Amend research-integration-report with a pipeline-revision note pointing at this doc | Team clarity |
| 6 | Aaron | Collect calibration dataset: 20–30 subjects × 4 movements (team + friends) alongside Plan 4 | Rule threshold tuning |
| 7 | Rajiv | Confirm whether rollup is in the 4-movement protocol | Research gap §7.1 prioritization |
| 8 | Team | Review this doc and confirm the pipeline swap + Section 10 decisions | Unblocks the plan updates |

---

*Generated 2026-04-10. Supersedes research-integration-report.md pipeline recommendation (§2.4). Read alongside `deep-read-sensing-2026-04-10.md` and `deep-read-biomech-2026-04-10.md`.*
