# File Inventory — BioLiminal Capstone

**Status:** current
**Created:** 2026-04-14
**Updated:** 2026-04-15
**Owner:** AaronCarney

> Snapshot 2026-04-11. Maps every file in the repo to its folder and the placement rule that put it there. Source of placement rules: `/CLAUDE.md` → "File Organization" section.
>
> This file is descriptive, not prescriptive. When rules and reality disagree, fix one or the other — don't silently ignore.

---

## 1. Top-Level Layout

| Folder | Purpose |
|---|---|
| `hardware/` | Physical build — sensor selection, signal chain, form factor, BOM. Answers "what do we build/buy?" |
| `ml/` | Model training, dataset processing, evaluation. Currently scaffold only (`.gitkeep`). |
| `software/` | Application code — FastAPI server, mobile-handover contract package. |
| `docs/` | Research, plans, decisions, operations (product framing), comms, session handover. |
| `tools/` | Build tooling / CI / scripts. Currently scaffold only (`.gitkeep`). |

Root files: `CLAUDE.md` (placement rules, project constraints), `README.md`, `Justfile`, `.gitignore`.

---

## 2. Per-Folder Contents

### 2.1 `hardware/`

Subdirs `cad/`, `datasheets/`, `firmware/`, `schematics/`, `test-logs/` are scaffold (`.gitkeep` only).

**`hardware/` (root)** — all untracked:

| File | Purpose |
|---|---|
| `critical-muscles.md` | Tiered muscle priority map for sEMG sensor placement (SENIAM + TPD constraints). |
| `form-factor-evaluation.md` | Strap-harness vs compression shirt tradeoff, wearability analysis. |
| `hardware-alignment-injury-prevention.html` | Rajat's injury-prevention-aligned hardware configuration doc (HTML). |
| `hardware-build-4ch-injury-prevention.html` | 4-channel injury prevention build variant (HTML). |
| `hardware-configurations.html` | Session 3 hardware configuration options with SVG diagrams (HTML). |
| `hardware-cueing-research.md` | Cueing modality research — vibrotactile vs pressure, mechanoreceptor science. |
| `hardware-decision-handover.md` | Session 4 handover doc for teammates making purchase decisions. |
| `hardware-engineering-specs.md` | Engineering specs for routed-string TSA, signal chain, mechanical. |
| `sensor-sourcing-reality.md` | Verified pricing/availability snapshot (MyoWare discontinued, etc). |
| `signal-chain-analysis.md` | sEMG signal chain analysis — CMRR, sampling rate, ADC requirements. |
| `strive-analysis-textile-electrodes.md` | Strive competitor teardown + textile electrode feasibility. |
| `torso-justification.md` | Justifies torso-first hardware design (cited but primary purpose = hardware decision). |
| `torso-vest-spec.md` | Distilled hardware spec from `hardware-configurations.html`. |

**`hardware/bom/`** — all untracked except `.gitkeep`:

| File | Purpose |
|---|---|
| `buy-list-final.md` | Final buy list. |
| `component-database.csv` | Single source of truth for components (per CLAUDE.md §Equipment Database). |
| `final-buy-list-with-local.md` | Buy list including local-sourcing adjustments. |
| `mvp-build-decisions.md` | MVP-tier sourcing decisions. |
| `shopping-list-researched_1.html` | Research-backed shopping list (HTML). |
| `wave1-lean-final.html` | Wave 1 lean buy list (HTML). |
| `wave1-lean-final.md` | Wave 1 lean buy list (MD). |

### 2.2 `ml/`

All subdirs (`datasets/`, `evaluation/`, `experiments/`, `models/`, `training/`) are scaffold (`.gitkeep`). No real ML artifacts yet. `.gitignore` excludes `ml/datasets/raw/` and `ml/models/*.{onnx,tflite,pt,h5}`.

### 2.3 `software/`

**`software/server/`** (tracked) — FastAPI backend. Structure:
- `src/auralink/api/` — FastAPI routes (`health.py`, `sessions.py`, `reports.py`), error handlers, pydantic schemas.
- `src/auralink/pipeline/` — Pipeline framework (`orchestrator.py`, `registry.py`, `artifacts.py`, `errors.py`) + stages (`skeleton`, `normalize`, `lift`, `phase_segment`, `rep_segment`, `angle_series`, `per_rep_metrics`, `quality_gate`, `within_movement_trend`).
- `src/auralink/ml/` — ML adapters (`lifter.py`, `loader.py`, `phase_segmenter.py`, `skeleton.py`).
- `src/auralink/models/registry.py` — model registry.
- `src/auralink/pose/` — pose utilities (`keypoints.py`, `joint_angles.py`).
- `src/auralink/reasoning/` — fascial chain reasoning (`chains.py`, `thresholds.py`).
- `src/auralink/analysis/rep_segmentation.py` — rep segmentation logic.
- `src/auralink/config.py` — app config.
- `tests/` — unit + integration tests mirroring `src/` layout; fixtures include `synthetic_overhead_squat.py`.
- `docs/blazepose_landmark_reference.md` — landmark reference (server-internal).
- `scripts/dev.sh`, `pyproject.toml`, `uv.lock`, `README.md`, `.python-version`.

**`software/mobile-handover/`** (tracked) — Dart/JSON contract for Flutter teammate:
- `README.md` — package overview.
- `interface/models.dart`, `pose_detector.dart`, `mediapipe_pose_detector.dart` — Dart data classes + interface.
- `schemas/session.schema.json` — exported JSON schema.
- `fixtures/sample_valid_session.json` — sample valid payload.
- `model/DOWNLOAD.md`, `model/blazepose_landmark_order.md` — MediaPipe model fetch instructions.
- `tools/export_schemas.py`, `tools/post_sample.sh` — regeneration + smoke-test scripts.

**`software/src/`**, **`software/tests/`**, **`software/config/`** — scaffold (`.gitkeep`).

### 2.4 `docs/`

**`docs/plans/`** (tracked):
- `2026-04-09-server-scaffold.md` — server scaffold plan.
- `2026-04-10-analysis-pipeline-epoch.md` — L1 epoch plan for analysis pipeline.
- `2026-04-10-L2-1-pipeline-framework.md` through `L2-5-operations.md` — L2 tactical plans.

**`docs/research/` (root)** — engineering-decision artifacts (literature-synthesis content is in the sibling `research/` repo):

| File | Status | Purpose |
|---|---|---|
| `license-audit-2026-04-11.md` | tracked | License audit for models/frameworks. |
| `license-audit-2026-04-11-v2.md` | tracked | License audit v2 (expanded to datasets). |
| `stack-options-matrix-2026-04-11.md` | tracked | Pose/biomech stack-selection matrix. |
| `dtw-library-comparison-2026-04-14.md` | tracked | DTW library selection. |
| `ncc-implementation-2026-04-14.md` | tracked | NCC algorithm implementation notes. |
| `pipeline-architecture-decision-2026-04-10.md` | tracked | Authoritative pipeline + stack engineering decision. |
| `citations-zotero-export.json` | untracked | Zotero library export (JSON). |
| `citations.ris` | untracked | Zotero library export (RIS). |
| `unsorted/` | untracked (empty) | Staging area, currently empty. |

**`docs/research/biomechanics/`**:
- tracked: `catalog.md`.
- untracked markdown/json: `core-muscles-research.md`, `yijinjing-fascial-chain-remodeling.md`, `adversarial_counter_evidence.json`, `research_interoception_attention_fascia_schleip.json`, `research_intervention_gap.json`, `research_mechanotransduction_sustained_loading.json`.
- untracked HTML references: `Classification_Of_Low_Back_Pain_..._Sahrmann....html` (Physiopedia practitioner summary — pending re-intake as a proper paper if/when the primary source is sourced).
- **Source PDFs migrated out 2026-04-15** — all Sahrmann, Van Dillen, Harris-Hayes, Rajagopal, and Uhlrich papers are now canonical in the sibling `research/` repo with citekeys and frontmatter.

**`docs/research/market/`** — all untracked:
- `market-analysis.md`, `market-analysis.pdf` — competitor/market analysis (Hinge, Sword, DARI, PostureScreen, etc). Retained here because the `.md` is an internal analysis synthesis, not a primary source paper.

**`docs/research/sensing/`**:
- tracked: `catalog.md` (rewritten 2026-04-15 to point at the sibling research repo for primary sources).
- untracked markdown/json: `research-gaps.md`, `verification-results.md`, `ML.json` (Zotero export of sensing ML papers).
- untracked HTML (saved web sources retained for engineering reference): `Mediapipe-Poses-position-detection....html`, `android-sdk.html`, `best-pose-estimation-models.html`, `best-practices.html`, `human-pose-estimation-technology-guide.html`, `unity-isdk-body-pose-detection.html`.
- untracked HTML pending re-intake: `2506.html` (arxiv 2506.18368, Sequential keypoint density estimator) and `2602.html` (arxiv 2602.23231, Skarimva multi-view action recognition) — to be re-downloaded as PDFs and intaked into the research repo.
- **Source PDFs migrated out 2026-04-15** — OpenCap (Uhlrich 2023, Gilon 2026), WHAM, TCPFormer, ViTPose, Miller 2025, Sabo 2026 Beighton, HSMR, and the 13 other pose-estimation / rehab PDFs are now canonical in the sibling `research/` repo.

**`docs/operations/`**:
- tracked: none (dir itself is only populated via comms files).
- untracked: `BRAINLIFT.pdf`, `Balance Brainlift.pdf` (living product-framing artifacts), `gtm.md` (go-to-market strategy, 100 GitHub stars in 3 weeks).

**`docs/operations/comms/`**:
- tracked: `2026-04-11-plan-changes-plain-english.md`, `2026-04-11-server-session-note.md`, `research-integration-report.md`.
- untracked: `research-integration-report.pdf` (PDF render of same report).

**`docs/decisions/`** — all untracked:
- `decisions.md` — decision log template (HW/SW/ML tradeoffs).
- `rajat-alignment-summary.md` — distilled summary of Rajat's research vs torso vest spec (8/12 components aligned).

**`docs/sessions/`**:
- untracked: `plan-review-L2-1-pipeline-framework-architectural.md`, `plan-review-L2-1-pipeline-framework-structural.md`, `progress-Capstone-p4-wave-c.md` (session handover progress file).
- `summaries/` — 19 task summary files (`plan4-task-1..5.md`, `task-9..15.md`, `task-P4-T6..T8.md`, `task-10a/b`, `task-11a/b`, `task-14a/b`). **Gitignored** via `.gitignore:42` (`docs/sessions/summaries/`) — ephemeral AI-assisted execution logs.

### 2.5 `tools/`

Scaffold only (`.gitkeep`).

---

## 3. Placement Verification Table (Untracked Files)

Column `rule` is the CLAUDE.md tiebreaker row that governs placement. Verdicts: **correct** / **misplaced** / **ambiguous**.

### 3.1 `hardware/` root

| File | Current location | Rule | Verdict |
|---|---|---|---|
| `critical-muscles.md` | `hardware/` | "physical component/sensor" (sensor placement) | correct |
| `form-factor-evaluation.md` | `hardware/` | "physical component/form factor" | correct |
| `hardware-alignment-injury-prevention.html` | `hardware/` | "physical component" — evaluates hardware configs | correct |
| `hardware-build-4ch-injury-prevention.html` | `hardware/` | "physical component" — build variant | correct |
| `hardware-configurations.html` | `hardware/` | "physical component" — config options | correct |
| `hardware-cueing-research.md` | `hardware/` | "physical component/actuator" — cueing hardware | correct (per HW vs research key distinction — decides what actuator to build) |
| `hardware-decision-handover.md` | `hardware/` | "physical component" — decision doc for purchases | correct |
| `hardware-engineering-specs.md` | `hardware/` | "physical component" — engineering specs | correct |
| `sensor-sourcing-reality.md` | `hardware/` | "physical component/sourcing" — pricing/availability | ambiguous — CLAUDE.md says "Buying/sourcing/pricing → `hardware/bom/`". This file is sourcing-focused and arguably belongs in `bom/`. Rule that keeps it in root: it's more a reality-check snapshot than a BOM line item. Flagged as ambiguous. |
| `signal-chain-analysis.md` | `hardware/` | "physical component/sensor" — signal chain for sEMG hardware | correct |
| `strive-analysis-textile-electrodes.md` | `hardware/` | ambiguous — competitor analysis suggests `docs/research/market/`, but file's primary purpose is textile electrode feasibility for our hardware. Key distinction: "what should we build?" → `hardware/`. | ambiguous (leans correct) |
| `torso-justification.md` | `hardware/` | explicit example in CLAUDE.md: "torso-justification.md is in `hardware/` because its purpose is justifying the torso-first hardware design" | correct |
| `torso-vest-spec.md` | `hardware/` | "physical component/form factor" | correct |

### 3.2 `hardware/bom/`

| File | Current location | Rule | Verdict |
|---|---|---|---|
| `buy-list-final.md` | `hardware/bom/` | "Buying/sourcing/pricing" | correct |
| `component-database.csv` | `hardware/bom/` | explicit: "single source of truth for all components" | correct |
| `final-buy-list-with-local.md` | `hardware/bom/` | "Buying/sourcing/pricing" | correct |
| `mvp-build-decisions.md` | `hardware/bom/` | "Buying/sourcing/pricing" (MVP buy decisions) | correct |
| `shopping-list-researched_1.html` | `hardware/bom/` | "Buying/sourcing/pricing" | correct |
| `wave1-lean-final.html` | `hardware/bom/` | "Buying/sourcing/pricing" | correct |
| `wave1-lean-final.md` | `hardware/bom/` | "Buying/sourcing/pricing" | correct |

### 3.3 `docs/operations/` + `docs/operations/comms/`

| File | Current location | Rule | Verdict |
|---|---|---|---|
| `BRAINLIFT.pdf` | `docs/operations/` | explicit example: "Examples in `docs/operations/`: `BRAINLIFT.pdf`" | correct |
| `Balance Brainlift.pdf` | `docs/operations/` | "High-level project framing: BrainLifts" — living doc | correct |
| `gtm.md` | `docs/operations/` | explicit example: "`gtm.md` is in `docs/operations/` because it's a product strategy document" | correct |
| `comms/research-integration-report.pdf` | `docs/operations/comms/` | companion PDF render of the already-tracked `.md` version (cross-team handoff artifact) | correct |

### 3.4 `docs/decisions/`

| File | Current location | Rule | Verdict |
|---|---|---|---|
| `decisions.md` | `docs/decisions/` | "Tradeoff decisions that span HW+SW+ML → `docs/decisions/`" | correct |
| `rajat-alignment-summary.md` | `docs/decisions/` | ambiguous — it's a cross-team alignment summary (which smells like `docs/operations/comms/`) *and* a tradeoff comparison (which smells like `docs/decisions/`). Rule that decided: it reconciles divergent HW decisions between two research tracks — cross-domain tradeoff. Could also live in `comms/` as a dated handoff. | ambiguous (leans `comms/` because its primary purpose is communicating Rajat's position for alignment, not logging a final decision). |

### 3.5 `docs/research/` root

| File | Current location | Rule | Verdict |
|---|---|---|---|
| `license-audit-2026-04-11.md` / `-v2` | `docs/research/` | engineering decision — ML model/dataset licensing | correct |
| `stack-options-matrix-2026-04-11.md` | `docs/research/` | engineering decision — pose/biomech stack selection | correct |
| `dtw-library-comparison-2026-04-14.md` | `docs/research/` | engineering decision — library evaluation | correct |
| `ncc-implementation-2026-04-14.md` | `docs/research/` | engineering decision — algorithm implementation notes | correct |
| `pipeline-architecture-decision-2026-04-10.md` | `docs/research/` | authoritative engineering decision grounded in the sibling research repo's literature synthesis | correct |
| `citations-zotero-export.json` | `docs/research/` | **rule gap** — Zotero/RIS exports aren't covered by any tiebreaker. Root is defensible because citations span all three subdirs. | ambiguous (rule gap) |
| `citations.ris` | `docs/research/` | same as above | ambiguous (rule gap) |

### 3.6 `docs/research/biomechanics/`

| File | Current location | Rule | Verdict |
|---|---|---|---|
| `core-muscles-research.md` | `docs/research/biomechanics/` | "Fascial chains, anatomy... McGill" → biomechanics | correct |
| `yijinjing-fascial-chain-remodeling.md` | `docs/research/biomechanics/` | "Fascial chains... movement science" | correct |
| `adversarial_counter_evidence.json` | `docs/research/biomechanics/` | supporting research data for biomechanics claims | correct |
| `research_interoception_attention_fascia_schleip.json` | `docs/research/biomechanics/` | "Schleip" → biomechanics (explicit in CLAUDE.md) | correct |
| `research_intervention_gap.json` | `docs/research/biomechanics/` | intervention gap analysis — biomechanics domain | correct |
| `research_mechanotransduction_sustained_loading.json` | `docs/research/biomechanics/` | mechanotransduction = fascia/connective tissue science | correct |
| `Classification_Of_Low_Back_Pain_..._Sahrmann....html` | `docs/research/biomechanics/` | LBP / movement system impairments = biomechanics | correct |
| `Defining Our Diagnostic Labels....pdf` | `docs/research/biomechanics/` | movement expertise / diagnostic labels = biomechanics | correct |
| `Harris-Hayes et al. - 2016 ... Movement Pattern Training....pdf` | `docs/research/biomechanics/` | "movement patterns" → biomechanics | correct |
| `Joyce et al. - 2023 - Concerns on the Science and Practice of a Movement System.pdf` | `docs/research/biomechanics/` | movement system science = biomechanics | correct |
| `Muscle coordination retraining ... knee contact force.pdf` | `docs/research/biomechanics/` | muscle coordination / joint loading = biomechanics | correct |
| `ijspt-12-862.pdf` | `docs/research/biomechanics/` | IJSPT = sports PT journal, biomechanics domain (assumed by folder placement) | correct |
| `nihms793173.pdf` / `nihms818926.pdf` / `nihms971315.pdf` | `docs/research/biomechanics/` | NIH manuscript IDs in biomech folder; cannot verify content without opening. Placement presumed correct based on sibling files. | correct (presumed) |

### 3.7 `docs/research/market/`

| File | Current location | Rule | Verdict |
|---|---|---|---|
| `market-analysis.md` | `docs/research/market/` | "Competitors, market sizing... → market" | correct |
| `market-analysis.pdf` | `docs/research/market/` | PDF render of above | correct |

### 3.8 `docs/research/sensing/`

All files below are pose-estimation / sEMG / sensor papers, HTML web captures, or analysis notes — all fall under "sEMG signal quality, pose estimation accuracy, CV performance → sensing".

| File | Current location | Rule | Verdict |
|---|---|---|---|
| `research-gaps.md` | `docs/research/sensing/` | gap analysis of what's measurable = sensing | correct |
| `verification-results.md` | `docs/research/sensing/` | source verification for sEMG claims (Merletti 2021) = sensing | correct |
| `ML.json` | `docs/research/sensing/` | Zotero export of sensing ML papers | correct |
| `2506.html` / `2602.html` | `docs/research/sensing/` | saved arXiv pages (2506.18368 etc) on pose/skeleton methods | correct |
| `Mediapipe-Poses-position-detection....html` | `docs/research/sensing/` | MediaPipe pose estimation | correct |
| `android-sdk.html` | `docs/research/sensing/` | ambiguous — SDK page could be a software/implementation reference. Rule that decided: it's in sensing because the SDK is the measurement path for pose. | ambiguous |
| `best-pose-estimation-models.html` | `docs/research/sensing/` | "pose estimation accuracy" | correct |
| `best-practices.html` | `docs/research/sensing/` | ambiguous — "best-practices" for what? presumed pose/sensing based on sibling placement. | ambiguous (rule gap — filename too generic) |
| `biomechanically-accurate-skeleton.pdf` | `docs/research/sensing/` | skeleton tracking accuracy = measurement | correct |
| `deep-learning-pose-estimation-survey.pdf` | `docs/research/sensing/` | pose estimation survey = sensing | correct |
| `dynamic-pose-estimation-hrpose.pdf` | `docs/research/sensing/` | pose estimation | correct |
| `enhanced-skeleton-tracking-rehab.pdf` | `docs/research/sensing/` | skeleton tracking = sensing | correct |
| `ergonomic-risk-mediapipe.pdf` | `docs/research/sensing/` | MediaPipe application = sensing | correct |
| `graph-network-skeleton-survey.pdf` | `docs/research/sensing/` | skeleton method survey = sensing | correct |
| `human-pose-estimation-technology-guide.html` | `docs/research/sensing/` | pose estimation tech guide = sensing | correct |
| `kinematic-skeleton-extraction-3d.pdf` | `docs/research/sensing/` | skeleton extraction = sensing | correct |
| `markerless-mediapipe-joint-moments.pdf` | `docs/research/sensing/` | MediaPipe joint moments = sensing | correct |
| `multi-view-gait-database.pdf` | `docs/research/sensing/` | gait capture dataset = sensing | correct |
| `pose-estimation-joint-angle-deep-learning.pdf` | `docs/research/sensing/` | pose estimation = sensing | correct |
| `pose-recognition-rehab-scoring.pdf` | `docs/research/sensing/` | pose-based scoring = sensing | correct |
| `realtime-pose-estimation-review.pdf` | `docs/research/sensing/` | pose estimation review = sensing | correct |
| `skeleton-integrity-pose-fine-tuning.pdf` | `docs/research/sensing/` | skeleton integrity = sensing | correct |
| `unity-isdk-body-pose-detection.html` | `docs/research/sensing/` | Unity body pose detection = sensing | correct |
| `vision-sensors-markerless-motion-review.pdf` | `docs/research/sensing/` | vision sensors markerless motion = sensing | correct |
| `Gilon et al. - 2026 - OpenCap ... Single Smartphone Video.pdf` | `docs/research/sensing/` | pose/kinematics from video = sensing | correct |
| `Liu et al. - 2025 - TCPFormer ... 3D Human Pose Estimation.pdf` | `docs/research/sensing/` | 3D pose estimation = sensing | correct |
| `Miller et al. - 2025 - Integrating ML with Musculoskeletal Simulation ... OpenCap.pdf` | `docs/research/sensing/` | pose + musculoskeletal dynamics from video = sensing | correct |
| `Sabo et al. - 2026 - ... vision pose-tracking based Beighton score ....pdf` | `docs/research/sensing/` | vision pose tracking = sensing | correct |
| `Shin et al. - 2024 - WHAM Reconstructing World-Grounded Humans....pdf` | `docs/research/sensing/` | 3D pose / motion reconstruction = sensing | correct |
| `Uhlrich et al. - 2023 - OpenCap Human movement dynamics from smartphone videos.pdf` | `docs/research/sensing/` | OpenCap smartphone pose = sensing | correct |
| `Xu et al. - 2022 - ViTPose....pdf` | `docs/research/sensing/` | ViT pose estimation = sensing | correct |

### 3.9 `docs/sessions/`

| File | Current location | Rule | Verdict |
|---|---|---|---|
| `plan-review-L2-1-pipeline-framework-architectural.md` | `docs/sessions/` | "Session handover, context dumps, plan reviews between work sessions → `docs/sessions/`" | correct |
| `plan-review-L2-1-pipeline-framework-structural.md` | `docs/sessions/` | same rule (plan review artifact) | correct |
| `progress-Capstone-p4-wave-c.md` | `docs/sessions/` | "Session handover, context dumps" | correct |

---

## 4. Rule Gaps

Cases where CLAUDE.md doesn't clearly cover a file type or the rule is under-specified:

1. **Citation managers (Zotero `.ris`, `.json` library exports)** — `citations.ris` and `citations-zotero-export.json` live in `docs/research/` root. No rule in CLAUDE.md tells you where citation bibliographies go. Suggest adding: *"Bibliography exports and citation manager dumps that span the whole project → `docs/research/` root. Subdir-specific exports (e.g. `ML.json` for sensing ML) → matching subdir."*

2. **HTML web captures with generic filenames** — Files like `best-practices.html` and `android-sdk.html` (short names, no topic word) can't be placed from filename alone. Suggest naming convention: *"Saved web pages should be renamed on capture to include the topic slug (e.g. `mediapipe-android-sdk.html`, not `android-sdk.html`)."*

3. **Sourcing reality-check docs** — `sensor-sourcing-reality.md` is a pricing/availability audit but not a BOM line-item list. Rules say "Buying/sourcing/pricing → `hardware/bom/`" but also "Specs, evaluation docs, architecture decisions stay in `hardware/`". Needs a tiebreaker for "sourcing analysis that feeds a BOM but isn't itself a BOM." Suggest: *"Sourcing feasibility / availability / discontinuation audits → `hardware/` root (they're inputs to BOM decisions, not BOM items)."*

4. **Cross-team alignment summaries** — `rajat-alignment-summary.md` fits both `docs/decisions/` (cross-domain tradeoff) and `docs/operations/comms/` (cross-team handoff). No rule distinguishes "summary of another teammate's position for alignment" vs "finalized decision." Suggest: *"If the doc's purpose is to reconcile two teammates' proposals and the final decision is still open, it belongs in `docs/operations/comms/` (dated or undated). Once a decision is logged, the decision itself goes in `docs/decisions/`, which can reference the comms doc."*

5. **PDF companions of tracked markdown** — `comms/research-integration-report.pdf` and `docs/research/market/market-analysis.pdf` are PDF renders of markdown siblings. Placement is obvious, but CLAUDE.md is silent on whether duplicating the PDF into git is desired. Not a placement gap, but worth documenting as policy (track both, or track only md + gitignore the pdf?).

6. **NIH manuscript PDFs** — `nihms793173.pdf` etc cannot be classified from filename alone. No rule gap per se, but naming convention suggestion: *"Paper PDFs should be renamed on save to author-year-shortslug format (e.g. `mcgill-2007-core-stability.pdf`) so placement is filename-visible."*

7. **Empty staging directories** — `docs/research/unsorted/` exists but is empty. CLAUDE.md doesn't sanction an "unsorted" bucket. Either delete or document it as an explicit staging rule.

---

## 5. Scaffolded But Unused

These directories exist only with `.gitkeep`:

- `hardware/cad/`, `hardware/datasheets/`, `hardware/firmware/`, `hardware/schematics/`, `hardware/test-logs/`
- `ml/datasets/`, `ml/evaluation/`, `ml/experiments/`, `ml/models/`, `ml/training/`
- `software/src/`, `software/tests/`, `software/config/`
- `tools/`

They're reserved by rule, not broken. Fill as work warrants.
