# L2 Plan 3 — DTW + Temporal Analysis

**Status:** Planning
**Parent:** `2026-04-10-analysis-pipeline-epoch.md`
**Depends on:** Plan 1 (pipeline framework, PerRepMetrics, NormalizedAngleTimeSeries), Plan 2 (Report schema + assembler + TemporalSection/CrossMovementSection stubs), Plan 4 (synthetic fixtures + `generate_reference_rep()` entry point)
**Created:** 2026-04-14
**Execution:** parallel-plan-executor (sequential-in-main-tree), 17 tasks, 10 waves, max parallelism 5

## Goal

Turn the raw per-rep metrics produced by Plan 1 into per-rep similarity comparisons against a movement-specific reference rep, using Dynamic Time Warping (DTW) for temporal alignment and Normalized Cross-Correlation (NCC) for shape scoring. Aggregate those comparisons into a `MovementTemporalSummary` per session (detecting within-movement form drift), and aggregate multiple sessions into a `ProtocolReport` via a new `POST /protocols` endpoint that surfaces cross-movement patterns such as fatigue carryover. The plan ships the temporal half of the free-tier screening value on top of Plan 2's rule-based reasoner — complementary, not a replacement.

## Architecture

The data flow is strictly additive to the existing per-session pipeline. Plan 1's stages (`angle_series`, `normalize`, `rep_segment`, `per_rep_metrics`, `within_movement_trend`) continue to run unchanged; Plan 3 adds one new stage, `rep_comparison`, which runs after `per_rep_metrics` and consumes both `per_rep_metrics` (for rep boundaries and the primary angle key) and `normalize` (for the full normalized angle traces). For each rep, the stage slices the primary joint angle window, calls `run_dtw()` to align it against the pre-generated reference rep (loaded at startup from `config/reference_reps/{movement}.json`), feeds the DTW-aligned pair into `ncc()` for a shape score, computes `rom_deviation_pct` as an independent amplitude guard (critical — NCC is scale-invariant and would otherwise score a half-range rep near 1.0), and classifies each rep as `clean`/`concern`/`flag` by thresholds loaded from `config/temporal/thresholds.yaml`.

The per-rep `RepComparison` list is then aggregated into a `MovementTemporalSummary` with a numpy-polyfit NCC-slope that mirrors the existing `within_movement_trend` slope convention. `form_drift_detected` fires when the NCC slope is sufficiently negative AND the mean ROM deviation crosses the drift-threshold — drift is a joint condition, not either-or, to avoid false positives from a single noisy rep. The summary attaches to `PipelineArtifacts.movement_temporal_summary` and flows through `_assemble_artifacts()` the same way `chain_observations` does.

Cross-movement aggregation does NOT run as a pipeline stage — stages are per-session, and cross-movement analysis spans multiple sessions by definition. Instead, a new `POST /protocols` endpoint accepts a list of session IDs, loads each session's artifacts via the existing `SessionStorage`, re-assembles each single-session `Report` via Plan 2's `assemble_report()`, and then calls `aggregate_protocol()` which reads the per-session `MovementTemporalSummary` from each report, builds `CrossMovementMetric` entries for `mean_ncc` and `mean_rom_deviation_pct`, and sets `fatigue_carryover_detected` when both metrics trend in the degradation direction across ≥3 sessions. The final `ProtocolReport` is the only new response type; single-session `GET /sessions/{id}/report` now has its `temporal_section` populated but keeps `cross_movement_section=None`.

Plan 2 left two placeholder classes in `report/schemas.py` — `TemporalSection` and `CrossMovementSection` — as empty stubs pending Plan 3. This plan does not restructure the `Report` model; it fills those stubs in-place and updates `report/assembler.py` to populate `temporal_section` from the new artifact field. The `CrossMovementSection` stays `None` on single-session reports and is only populated inside `aggregate_protocol()`.

## Tech Stack

- Python 3.11
- FastAPI (existing)
- pydantic v2 (existing)
- numpy (existing — used for NCC, slope fits, ROM computation)
- pytest / httpx (existing test stack)
- ruff / black (existing)
- uv (existing package manager)
- **dtaidistance ≥ 2.4.0, < 3** — NEW runtime dependency, C-backed exact DTW, Apache-2.0 license, numpy-only transitive deps

## Dependencies Justification

Plan 3 is the single plan in this epoch authorized by L1 to add a runtime dependency. The choice of `dtaidistance` was researched end-to-end in `/home/context/olorin/projects/bioliminal/RnD_Server/docs/research/dtw-library-comparison-2026-04-14.md`. Summary of why this is the right pick and not one of the alternatives:

- **Apache-2.0 license** — permissive, patent-grant, compatible with our MIT/BSD stance. The other actively-maintained option with a native-code backend, `dtw-python`, is GPL-3.0-or-later and is disqualified by our license policy.
- **Active maintenance** — 2.4.0 released February 2026. `fastdtw` (MIT) has not shipped since October 2019 and is broken on numpy 2.x per upstream issue #65, so it is effectively abandoned.
- **Zero transitive bloat** — only numpy is a hard dep; scipy/pandas/matplotlib are optional extras we do not install. `tslearn` (BSD) would drag in scikit-learn + numba + scipy + joblib (~200MB of wheels and a numba JIT warmup on first call) just to call `dtw_path`. Bad ratio for one function.
- **C-backed performance** — <0.2 ms per rep alignment at N=150 per the upstream benchmarks. Our budget is ~100 ms/rep, so we have 500× headroom for when we start batching reps per session or aggregating across a 4-session protocol.
- **Clean API** — both `dtw.distance(a, b)` and `dtw.warping_path(a, b)` are single-call pure functions; `window=` takes a Sakoe-Chiba radius directly; returns are native Python lists/floats, no intermediate cost-matrix objects. That is the narrowest possible surface to wrap.
- **Exact DTW, not approximation** — `fastdtw` is an approximation algorithm (named for speed, not accuracy) and defeats the point of picking a library over a 40-line numpy DP.

Methodology rationale (DTW + NCC + Sakoe-Chiba band) and the empirical NCC thresholds are sourced from `/home/context/olorin/projects/bioliminal/RnD_Server/docs/research/dtw-ncc-methodology-2026-04-14.md`. The NCC numpy reference implementation and edge-case handling are sourced verbatim from `/home/context/olorin/projects/bioliminal/RnD_Server/docs/research/ncc-implementation-2026-04-14.md`. Both research docs are cited in line in the relevant task bodies below.

Docker build note: `dtaidistance` compiles a Cython extension on install. The existing `python:3.11` base image has `build-essential`; verify the dev-container still builds cleanly at task T1 and fall back to pure-Python mode (the library auto-detects) if the toolchain is missing. Pure Python is ~30× slower but still correct and still well under our budget.

## File Tree Delta

```
software/server/
├── pyproject.toml                                         # MODIFIED (T1) — add dtaidistance
├── src/auralink/
│   ├── temporal/                                          # NEW
│   │   ├── __init__.py                                    # NEW (T2)  empty
│   │   ├── ncc.py                                         # NEW (T2)
│   │   ├── dtw.py                                         # NEW (T3)
│   │   ├── reference_reps.py                              # NEW (T4)
│   │   ├── threshold_loader.py                            # NEW (T6)
│   │   ├── comparison.py                                  # NEW (T7)
│   │   └── summary.py                                     # NEW (T8)
│   ├── protocol/                                          # NEW
│   │   ├── __init__.py                                    # NEW (T9)  empty
│   │   ├── schemas.py                                     # NEW (T9)
│   │   └── aggregator.py                                  # NEW (T13)
│   ├── pipeline/
│   │   ├── artifacts.py                                   # MODIFIED (T5, T12)
│   │   ├── orchestrator.py                                # MODIFIED (T12)
│   │   └── stages/
│   │       ├── base.py                                    # MODIFIED (T12) add STAGE_NAME_REP_COMPARISON
│   │       └── rep_comparison.py                          # NEW (T11)
│   ├── api/
│   │   ├── main.py                                        # MODIFIED (T14) include protocols router
│   │   └── routes/
│   │       └── protocols.py                               # NEW (T14)
│   └── report/
│       ├── schemas.py                                     # MODIFIED (T15) fill Plan-3 slots
│       └── assembler.py                                   # MODIFIED (T15) populate temporal_section
├── config/
│   ├── temporal/
│   │   └── thresholds.yaml                                # NEW (T6)
│   └── reference_reps/
│       ├── overhead_squat.json                            # NEW (T10)
│       ├── single_leg_squat.json                          # NEW (T10)
│       └── push_up.json                                   # NEW (T10)
├── scripts/
│   └── generate_reference_reps.py                         # NEW (T10)
└── tests/
    ├── unit/
    │   ├── temporal/                                      # NEW
    │   │   ├── __init__.py                                # NEW (T2)  empty
    │   │   ├── test_ncc.py                                # NEW (T2)
    │   │   ├── test_dtw.py                                # NEW (T3)
    │   │   ├── test_reference_reps.py                     # NEW (T4)
    │   │   ├── test_threshold_loader.py                   # NEW (T6)
    │   │   ├── test_comparison.py                         # NEW (T7)
    │   │   ├── test_summary.py                            # NEW (T8)
    │   │   └── test_reference_rep_files.py                # NEW (T10)
    │   ├── protocol/                                      # NEW
    │   │   ├── __init__.py                                # NEW (T9)  empty
    │   │   ├── test_schemas.py                            # NEW (T9)
    │   │   └── test_aggregator.py                         # NEW (T13)
    │   ├── pipeline/
    │   │   ├── test_artifacts_temporal.py                 # NEW (T5)
    │   │   ├── test_rep_comparison_stage.py               # NEW (T11)
    │   │   └── test_orchestrator_temporal_wiring.py       # NEW (T12)
    │   └── report/
    │       └── test_report_temporal.py                    # NEW (T15)
    └── integration/
        ├── test_protocols_endpoint.py                     # NEW (T14)
        └── test_protocol_e2e.py                           # NEW (T16)
```

## Schemas

All new pydantic types. Where they live:

- `auralink.pipeline.artifacts.RepComparison` — one rep scored against the reference.
- `auralink.pipeline.artifacts.MovementTemporalSummary` — within-movement aggregation over `list[RepComparison]`.
- `auralink.pipeline.artifacts.PipelineArtifacts.movement_temporal_summary` — new optional field.
- `auralink.temporal.reference_reps.ReferenceRep` — reference rep config model (loaded from JSON).
- `auralink.temporal.dtw.DTWResult` — thin pydantic wrapper for the DTW library result.
- `auralink.temporal.threshold_loader.TemporalThresholds` — YAML-backed threshold bundle.
- `auralink.protocol.schemas.ProtocolRequest` — `POST /protocols` request body.
- `auralink.protocol.schemas.CrossMovementMetric` — one metric aggregated across movements.
- `auralink.protocol.schemas.ProtocolReport` — `POST /protocols` response body.
- `auralink.report.schemas.TemporalSection` — filled in by T15 (Plan 2 placeholder).
- `auralink.report.schemas.CrossMovementSection` — filled in by T15 (Plan 2 placeholder).

## Architectural Decisions

1. **DTW library: `dtaidistance`.** Only actively-maintained, permissive, C-backed, numpy-only-deps candidate. Full comparison in `/home/context/olorin/projects/bioliminal/RnD_Server/docs/research/dtw-library-comparison-2026-04-14.md`. See Dependencies Justification section above for the line-by-line rationale.

2. **Sakoe-Chiba band radius r = 10% of the longer sequence length.** Paper (Scientific Reports 2025, DOI 10.1038/s41598-025-29062-7) omitted a global constraint, which is a known DTW pathology — unconstrained DTW can produce degenerate paths where one index matches dozens of frames of the other sequence. A 10% band is the standard biomechanics default (Ferrari et al., Keogh et al.) and upgrades the paper's method by removing the degenerate-path failure mode while still letting a slower-tempo rep match a reference at up to ±10% tempo deviation. Computed at call time as `max(1, int(0.1 * max(len(a), len(b))))` so it scales with rep length.

3. **NCC form: zero-lag zero-normalized, numpy-native ~10 LOC.** After DTW alignment, the two rep angle sequences are equal length with timing already matched, so only zero-lag matters. This form is mathematically identical to Pearson's r on the de-meaned vectors (see `ncc-implementation-2026-04-14.md` §5) and is what OpenCV's `TM_CCOEFF_NORMED`, scikit-image's `match_template`, and the PLOS One FFT-NCC paper (Lewis 1995 / Subramaniam 2018) compute. scipy.signal.correlate adds no value at our rep length (30–150 samples) — its FFT path only wins at ≥500–1000 samples and its own `method='auto'` heuristic would pick `'direct'` at our scale. Pure numpy is the right call; we do not add scipy.

4. **NCC thresholds: ≥0.95 clean, 0.75–0.95 concern, <0.75 flag.** Sourced from the gait biomechanics literature (see `ncc-implementation-2026-04-14.md` §4): Kavanagh et al. gait EMG XCC (0.85–0.95 intra-subject), Ferrari et al. CMC for gait kinematics (>0.90 excellent / 0.75–0.90 good / <0.75 poor), Iosa 2014 clinical gait waveform similarity review (0.8–0.9 acceptable / >0.9 strong), IMU-vs-photogrammetry validation (Frontiers Bioeng 2024, r > 0.75 = sufficient agreement). Same-subject same-exercise NCCs typically cluster in 0.85–0.95; dropping under 0.75 is a reliable signal that the movement has meaningfully changed.

5. **ROM amplitude guard is non-negotiable.** NCC is invariant to linear scaling of the signal — a rep with half the range of motion but the identical shape scores ~1.0. If we relied on NCC alone, a user performing a partial squat in perfect form would score "clean." The fix is a separate amplitude check: `rom_deviation_pct = (rom_user_deg - rom_reference_deg) / rom_reference_deg * 100`. A rep is classified `flag` if `|rom_deviation_pct| >= rom_deviation_flag_pct` (default 25%) regardless of its NCC; `concern` if `|rom_deviation_pct| >= rom_deviation_concern_pct` (default 15%); otherwise fall through to NCC-based classification. Joint condition: `status = max(ncc_status, rom_status)` with severity ordering `clean < concern < flag`. This is explicitly called out in the NCC research doc §4 and is mandatory.

6. **Reference rep sourcing: consume Plan 4's `generate_reference_rep()`, do not re-implement.** The synthetic generator module at `software/server/tests/fixtures/synthetic/generator.py:161` already exports `generate_reference_rep(movement: MovementType, frames_per_rep: int = 30, frame_rate: float = 30.0) -> dict` which returns a session-payload-shaped dict with a single rep. Plan 3 provides a build-time script `scripts/generate_reference_reps.py` that calls this function, feeds the result through Plan 1's `quality_gate → angle_series → normalize` stages to extract the normalized angle trace (so the reference rep lives in the same coordinate frame as anything the runtime compares against), and persists the result as `config/reference_reps/{movement}.json` conforming to the `ReferenceRep` pydantic schema. The runtime loader only reads JSON — it never imports test fixtures. This keeps the `tests/` dependency out of the production import graph and satisfies the L1 "Plan 4 owns fixture generation; Plan 3 consumes" directive.

7. **Reference rep aggregation: single synthetic rep per movement, NOT DBA.** The standard high-fidelity way to build a reference template is DTW Barycenter Averaging (DBA) over many real captures — iteratively average a cohort of reps in DTW-space. We are deliberately NOT doing this in Plan 3 because: (a) we have no real clinician-captured cohort yet, (b) our reference reps come from the same synthetic generator that produces our test fixtures, so averaging N runs of a deterministic generator adds no signal over using a single run, and (c) DBA is ~100 lines of code and has its own tuning knobs (number of barycenter iterations, tolerance, initial template selection). When real clinician demo captures arrive, DBA becomes the obvious upgrade path. For now, a single deterministic synthetic rep is the honest choice. Deferred to L3 follow-on, not to this plan.

8. **Plan 3 adds a NEW stage; the existing `within_movement_trend` from Plan 1 stays.** `within_movement_trend` detects drift by slope-fitting raw ROM/valgus/trunk-lean series — it has no reference rep concept. Plan 3's new `rep_comparison` stage produces the NCC/DTW-based `MovementTemporalSummary`, which is shape-based rather than raw-metric-based. They are complementary, not redundant: ROM slope tells you "this user got lower over time," while NCC slope tells you "this user's shape diverged from the reference over time." Both are kept. The new stage runs AFTER `per_rep_metrics` and BEFORE `chain_reasoning` so that if a future rule wants to fire on temporal-summary data it can.

9. **Protocol aggregation is endpoint-invoked, not a pipeline stage.** Pipeline stages run per-session. Cross-movement analysis spans multiple sessions by definition and is therefore triggered exclusively from `POST /protocols`, which loads each session's saved artifacts, assembles single-session reports, and combines them. There is no `cross_movement_trend` stage and no per-session cross-movement artifact. The `ProtocolReport` response is the only cross-session surface.

10. **Signals: 2D joint-angle traces.** Matches the Scientific Reports 2025 paper, matches the existing Plan 1 `NormalizedAngleTimeSeries`, and matches MediaPipe BlazePose's native output. 3D lift exists behind `run_lift` already but is a parallel track destined for MotionBERT integration in a later epoch; Plan 3 deliberately does not depend on it.

11. **Config-driven thresholds via YAML at startup.** Mirrors the Plan 2 convention (`config/thresholds/default.yaml` and `config/rules/*.yaml`). New file at `config/temporal/thresholds.yaml` holds NCC clean/concern thresholds, ROM deviation concern/flag thresholds, and form-drift slope thresholds. Loaded via `threshold_loader.load_temporal_thresholds()` (mirror of `reasoning/threshold_loader.py`) and passed into `compare_rep()` / `summarize_comparisons()` as an explicit argument — not a module-level global, so tests can inject mocks.

12. **Only overhead_squat and single_leg_squat get the rep_comparison stage.** `push_up` currently stops at `skeleton` per Plan 1 (rep-based stages require elbow_flexion angles which are deferred), so it has no `per_rep_metrics` to compare. `rollup` is phase-based, not rep-based, so there are no reps to align. Adding rep_comparison to either stage list would fail at runtime; the T12 orchestrator wiring explicitly registers it only on the default list used by overhead_squat and single_leg_squat.

## Existing Code References

Files Plan 3 reads, modifies, or integrates with. Exact line numbers current as of 2026-04-14:

- `software/server/src/auralink/pipeline/artifacts.py` lines 41–61 — existing `RepMetric`, `PerRepMetrics`, `WithinMovementTrend`. T5 adds `RepComparison` and `MovementTemporalSummary`. T12 adds `movement_temporal_summary: MovementTemporalSummary | None = None` to `PipelineArtifacts` at line 96.
- `software/server/src/auralink/pipeline/stages/base.py` lines 25–34 — existing `STAGE_NAME_*` constants. T12 adds `STAGE_NAME_REP_COMPARISON = "rep_comparison"`.
- `software/server/src/auralink/pipeline/orchestrator.py` lines 31–44 (`_default_stage_list`), lines 46–56 (`_push_up_stage_list`), lines 59–68 (`_rollup_stage_list`), lines 107–119 (`_assemble_artifacts`). T12 imports `run_rep_comparison`, inserts a `Stage` entry into `_default_stage_list` only (after `run_per_rep_metrics`, before `run_chain_reasoning`), and updates `_assemble_artifacts` to copy `movement_temporal_summary`.
- `software/server/src/auralink/pipeline/stages/per_rep_metrics.py` — existing stage. T11 reads `ctx.artifacts["per_rep_metrics"]` and `ctx.artifacts["normalize"]` the same way.
- `software/server/src/auralink/pipeline/stages/within_movement_trend.py` — existing stage using `numpy.polyfit` for slope. T8 follows the same polyfit pattern for the NCC slope.
- `software/server/src/auralink/report/schemas.py` lines 17–23 — existing placeholder `TemporalSection` and `CrossMovementSection` (empty body, docstring stub). T15 fills them in; line numbers 49–50 hold the optional Report fields.
- `software/server/src/auralink/report/assembler.py` lines 32–59 — existing `assemble_report()`. T15 updates it to populate `temporal_section` from `artifacts.movement_temporal_summary`.
- `software/server/src/auralink/api/main.py` lines 1–18 — existing FastAPI factory. T14 imports and includes the new `protocols` router.
- `software/server/src/auralink/api/routes/reports.py` — existing session-report route. T14's protocols endpoint reuses the same `SessionStorage` dependency injection pattern.
- `software/server/src/auralink/pipeline/storage.py` lines 42–50 — existing `load_artifacts()` / `_artifacts_path_for()`. T14 calls `load_artifacts(session_id)` for each session in a protocol.
- `software/server/tests/fixtures/synthetic/generator.py:161` — existing `generate_reference_rep(movement, frames_per_rep, frame_rate)` function. T10 imports and calls this exactly once per movement.
- `software/server/tests/fixtures/loader.py` — existing `load_fixture(movement, variant)`. T16 uses this to load four separate session fixtures for the cross-movement protocol E2E test.
- `software/server/tests/integration/test_full_report.py` — existing integration test pattern (TestClient + monkeypatch AURALINK_DATA_DIR). T14 and T16 follow the same shape.
- `software/server/src/auralink/reasoning/threshold_loader.py` — existing reasoning YAML loader (pattern reference). T6 mirrors its structure for the temporal thresholds loader.
- `software/server/src/auralink/reasoning/rule_loader.py` — existing YAML glob loader (pattern reference). T6 follows the same `Path(__file__).resolve().parents[3] / "config" / "temporal"` convention.

## Composition / Task List Overview

| ID | Title | Wave | Label | Tests | Depends on |
|---|---|---|---|---|---|
| T1 | Add dtaidistance runtime dependency | 0 | skip-tdd | 0 | — |
| T2 | NCC module | A | TDD | 4 | T1 |
| T3 | DTW wrapper module | A | TDD | 4 | T1 |
| T4 | ReferenceRep schema + loader | A | TDD | 4 | T1 |
| T5 | RepComparison + MovementTemporalSummary schemas | A | TDD | 2 | T1 |
| T6 | Temporal thresholds YAML + loader | A | TDD | 3 | T1 |
| T7 | Per-rep comparison function | B | TDD | 5 | T2, T3, T5, T6 |
| T8 | Within-movement summary module | B | TDD | 4 | T5, T6 |
| T9 | Protocol + ProtocolReport + CrossMovementMetric schemas | B | TDD | 2 | T1 |
| T10 | Reference rep generation script + config files | C | skip-tdd (1 test) | 1 | T4 |
| T11 | rep_comparison pipeline stage | C | TDD | 4 | T4, T7, T8 |
| T12 | Register stage name + orchestrator wiring + artifacts field | D | TDD | 3 | T5, T11 |
| T15 | Populate TemporalSection + CrossMovementSection | E | TDD | 3 | T5, T9, T12 |
| T13 | Protocol aggregator | F | TDD | 4 | T5, T9, T15 |
| T14 | POST /protocols endpoint | G | TDD | 4 | T9, T13 |
| T16 | 4-session protocol E2E integration test | H | TDD | 2 | T14, T15 |
| T17 | Final validation + optional lint cleanup | I | skip-tdd | 0 | T16 |

**Expected new test count:** 0 + 4 + 4 + 4 + 2 + 3 + 5 + 4 + 2 + 1 + 4 + 3 + 3 + 4 + 4 + 2 + 0 = **49** (task order reflects new wave structure: T1, Wave A [T2–T6], Wave B [T7–T9], Wave C [T10, T11], Wave D [T12], Wave E [T15], Wave F [T13], Wave G [T14], Wave H [T16], Wave I [T17]).

Baseline before Plan 3 is ~180 tests (Plan 1 + Plan 2). After Plan 3 exits cleanly the full suite should report ~230 passing. The original L1 budget said "~180 + ~40 = ~220" — the extra 10 tests come from the amplitude-guard coverage (which the L1 budget predated), the explicit orchestrator wiring test, the fatigue-carryover cross-movement variant, and the primary-angle plumbing guard in T10.

## Wave / Dependency Graph

Waves are barrier-sequential. Within a wave, tasks run in parallel up to `max_parallel`. File ownership is disjoint within each wave (the self-review checklist at the bottom verifies this).

```
Wave 0 (1):           T1                                   # dependency install
Wave A (parallel, 5): T2, T3, T4, T5, T6                   # independent primitives
Wave B (parallel, 3): T7, T8, T9                           # comparison + summary + protocol schemas
Wave C (parallel, 2): T10, T11                             # reference rep gen + rep_comparison stage
Wave D (1):           T12                                  # orchestrator wiring (atomic 4-file seam)
Wave E (1):           T15                                  # Report TemporalSection/CrossMovementSection fill-in
Wave F (1):           T13                                  # protocol aggregator (reads real MovementSection fields)
Wave G (1):           T14                                  # POST /protocols endpoint
Wave H (1):           T16                                  # e2e integration
Wave I (1):           T17                                  # final validation
```

Wave barriers explained (every `depends_on` crosses a strict wave boundary):

- T1 must complete before any task in Wave A because T3 (DTW wrapper) imports `dtaidistance`.
- Wave A holds all primitives that have no cross-dependencies. T5 (schemas) is the reason Wave B can start — T7, T8 both depend on `RepComparison`. T6 is a sibling primitive, not a dependency of T5.
- Wave B splits into T7 (needs T2+T3 for NCC+DTW callers and T5 for the return type and T6 for threshold type), T8 (needs T5+T6), and T9 (independent schema work that only needs pydantic — placed here because it's conceptually a protocol-layer type consumed by the aggregator in a later wave).
- Wave C holds the pipeline-adjacent primitives. T10 generates the JSON reference files (consumes T4's `ReferenceRep` schema for the write side). T11 implements the `rep_comparison` stage — its tests monkeypatch the reference-rep config dir via an autouse `tmp_path` fixture, so T11 does NOT need T10's committed JSON files at green-test time. T10 and T11 own disjoint file sets (`scripts/` + `config/reference_reps/` vs `pipeline/stages/rep_comparison.py`) and run in parallel.
- Wave D (T12) is the single-task orchestrator wiring seam. T12 imports `run_rep_comparison` from T11's module at module load time, so it MUST run in a strictly later wave than T11 — any same-wave scheduling would race the import. T12 owns `pipeline/stages/base.py` + `pipeline/orchestrator.py` + `pipeline/artifacts.py` in one atomic commit.
- Wave E (T15) must come after T12 because T15 reads `PipelineArtifacts.movement_temporal_summary` (added by T12) and adds `MovementSection.movement_temporal_summary` to the report schemas.
- Wave F (T13) runs the protocol aggregator. T13 reads `report.movement_section.movement_temporal_summary` via normal pydantic attribute access — that field is added by T15, so T13 must strictly follow T15. The aggregator depends on T9 (schemas) and T5 (for the `MovementTemporalSummary` type it consumes indirectly via `MovementSection`).
- Wave G (T14) runs the `POST /protocols` endpoint. T14 imports `aggregate_protocol` from T13's module, so it must strictly follow T13. T14 also needs T9's `ProtocolRequest` schema (landed in Wave B) and the updated report assembler from T15.
- Wave H (T16) must come after T14 and T15 because it exercises the full flow: sessions POST → artifacts with temporal summary → GET /sessions/{id}/report has populated `temporal_section` → POST /protocols → `ProtocolReport` with `cross_movement_section`.
- Wave I (T17) is sequential final validation.

## Per-Task Detail

---

#### Task T1: Add dtaidistance runtime dependency

**Label:** skip-tdd

**Files owned (exclusive to this task):**
- `software/server/pyproject.toml`

**Depends on:** nothing

**Rationale:** T3 imports `dtaidistance.dtw`. Adding the dep inside a parallel wave would race with every other task that runs `uv sync` implicitly. T1 lives alone in Wave 0 before Wave A fans out.

**Steps:**

1. Read `software/server/pyproject.toml` `[project].dependencies` list (see Existing Code References above — line 6–14).
2. Insert `"dtaidistance>=2.4.0,<3"` into the dependencies list. Alphabetical placement preferred; any valid position is acceptable.
3. Run `cd software/server && uv sync` to install it into the uv-managed venv.
4. **Verify:** `cd software/server && uv run python -c "from dtaidistance import dtw; print(dtw.distance([1.0,2.0,3.0],[1.0,2.0,4.0]))"` — should print a small float (`1.0` on a standard install).

**Expected result:** `dtaidistance>=2.4.0,<3` appears in `[project.dependencies]`; `uv sync` completes; the verify command prints a float.

**Commit message:** `chore(deps): add dtaidistance for DTW temporal analysis`

**Expected test count after this task:** 180 (unchanged — dependency install, no tests).

---

#### Task T2: NCC module

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/temporal/__init__.py`
- `software/server/src/auralink/temporal/ncc.py`
- `software/server/tests/unit/temporal/__init__.py`
- `software/server/tests/unit/temporal/test_ncc.py`

**Depends on:** T1

**Plan-review notes:** Implementation is taken verbatim from `/home/context/olorin/projects/bioliminal/RnD_Server/docs/research/ncc-implementation-2026-04-14.md` §2. The research doc is the single source of truth for this function — do not deviate.

**TDD steps:**

- [ ] Write the four tests below.
- [ ] Run `cd software/server && uv run pytest tests/unit/temporal/test_ncc.py -v` — expect 4 failures (module missing).
- [ ] Create `src/auralink/temporal/__init__.py` (empty) and `tests/unit/temporal/__init__.py` (empty).
- [ ] Create `src/auralink/temporal/ncc.py` with the verbatim implementation below.
- [ ] Re-run the focused test command — expect `4 passed`.
- [ ] Commit.

**Exact file contents (verbatim):**

`software/server/src/auralink/temporal/__init__.py`:
```python
```

`software/server/tests/unit/temporal/__init__.py`:
```python
```

`software/server/src/auralink/temporal/ncc.py`:
```python
"""Zero-mean normalized cross-correlation at zero lag.

After DTW has aligned two equal-length 1D signals, shape similarity collapses
to a single dot-product over de-meaned unit vectors. This is algebraically
identical to Pearson's r but is called NCC here for consistency with the
template-matching literature (OpenCV TM_CCOEFF_NORMED, scikit-image
match_template, Lewis 1995). Full rationale and edge-case handling in
docs/research/ncc-implementation-2026-04-14.md.
"""

import numpy as np


def ncc(x: np.ndarray | list[float], y: np.ndarray | list[float], eps: float = 1e-12) -> float:
    """Zero-mean normalized cross-correlation at zero lag.

    Inputs are 1D arrays of equal length (post-DTW alignment).
    Returns a score in [-1.0, 1.0]. 1.0 means identical shape (up to
    linear scale and offset); 0.0 means uncorrelated; -1.0 means inverted.

    Edge cases:
      - Raises ValueError on length mismatch or non-1D input.
      - Returns NaN if either signal has (near-)zero variance, since
        shape comparison is undefined for a constant signal.
      - NaNs in inputs propagate to a NaN output; callers must mask or
        interpolate upstream.
    """
    xa = np.asarray(x, dtype=np.float64)
    ya = np.asarray(y, dtype=np.float64)
    if xa.ndim != 1 or ya.ndim != 1:
        raise ValueError("ncc expects 1D arrays")
    if xa.shape != ya.shape:
        raise ValueError(f"length mismatch: {xa.shape} vs {ya.shape}")
    if not (np.all(np.isfinite(xa)) and np.all(np.isfinite(ya))):
        return float("nan")
    xc = xa - xa.mean()
    yc = ya - ya.mean()
    denom = float(np.sqrt(np.dot(xc, xc) * np.dot(yc, yc)))
    if denom < eps:
        return float("nan")
    return float(np.dot(xc, yc) / denom)
```

`software/server/tests/unit/temporal/test_ncc.py`:
```python
import math

import numpy as np
import pytest

from auralink.temporal.ncc import ncc


def test_identical_signals_score_one():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert ncc(x, x) == pytest.approx(1.0, abs=1e-12)


def test_inverse_signal_scores_negative_one():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = -x
    assert ncc(x, y) == pytest.approx(-1.0, abs=1e-12)


def test_zero_variance_signal_returns_nan():
    x = np.array([3.0, 3.0, 3.0, 3.0])
    y = np.array([1.0, 2.0, 3.0, 4.0])
    result = ncc(x, y)
    assert math.isnan(result)


def test_length_mismatch_raises():
    with pytest.raises(ValueError):
        ncc(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0]))
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/temporal/test_ncc.py -v`

**Expected result:** `4 passed`

**Commit message:** `feat(temporal): add NCC module with zero-lag zero-normalized form`

**Expected test count after this task:** 184.

---

#### Task T3: DTW wrapper module

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/temporal/dtw.py`
- `software/server/tests/unit/temporal/test_dtw.py`

**Depends on:** T1

**Plan-review notes:** Wraps `dtaidistance.dtw.distance` and `dtaidistance.dtw.warping_path`. Does NOT wrap `dtw.distance_fast` because the `.distance` call already uses the C backend when available. The Sakoe-Chiba band radius is computed at call time; the wrapper does not cache or globalize it. See `/home/context/olorin/projects/bioliminal/RnD_Server/docs/research/dtw-library-comparison-2026-04-14.md` for API rationale.

**TDD steps:**

- [ ] Write the four tests below.
- [ ] Run `cd software/server && uv run pytest tests/unit/temporal/test_dtw.py -v` — expect 4 failures.
- [ ] Create `src/auralink/temporal/dtw.py` with the verbatim implementation below.
- [ ] Re-run — expect `4 passed`.
- [ ] Commit.

**Exact file contents (verbatim):**

`software/server/src/auralink/temporal/dtw.py`:
```python
"""Dynamic Time Warping wrapper over dtaidistance.

Provides a single call-site for aligning two 1D joint-angle sequences with a
Sakoe-Chiba band constraint. Returns both the DTW distance and the explicit
warping path so downstream callers can re-index either sequence onto the
alignment before scoring shape similarity with NCC.

dtaidistance is Apache-2.0, C-backed, numpy-only; see
docs/research/dtw-library-comparison-2026-04-14.md.
"""

from dtaidistance import dtw as _dtai_dtw
from pydantic import BaseModel, Field


class DTWResult(BaseModel):
    """Thin pydantic wrapper so callers can round-trip DTW output through JSON."""

    distance: float = Field(ge=0.0)
    path: list[tuple[int, int]]
    window: int | None = None


def _sakoe_chiba_window(len_a: int, len_b: int, radius_fraction: float = 0.1) -> int:
    """Return the Sakoe-Chiba radius as an integer number of frames.

    Scales with the longer of the two sequences. Floor of 1 so the constraint
    is never degenerate. Paper omitted this entirely; we restore it because
    unconstrained DTW is known to produce pathological paths.
    """
    return max(1, int(radius_fraction * max(len_a, len_b)))


def run_dtw(
    a: list[float],
    b: list[float],
    radius_fraction: float = 0.1,
) -> DTWResult:
    """Align two 1D sequences via DTW under a Sakoe-Chiba band.

    Parameters
    ----------
    a, b : list[float]
        Sequences to align. May be of different length; DTW handles this.
    radius_fraction : float
        Sakoe-Chiba band radius as a fraction of the longer sequence length.
        Default 0.1 matches the biomechanics literature (Ferrari et al.,
        Keogh et al.). Must be in (0, 1].

    Returns
    -------
    DTWResult
        distance : float   -- DTW alignment cost
        path : list[(i,j)] -- (index_in_a, index_in_b) pairs forming the
                              optimal warping path
        window : int       -- the concrete Sakoe-Chiba radius applied
    """
    if not a or not b:
        raise ValueError("run_dtw requires non-empty sequences")
    if not (0.0 < radius_fraction <= 1.0):
        raise ValueError(f"radius_fraction must be in (0, 1]; got {radius_fraction}")

    window = _sakoe_chiba_window(len(a), len(b), radius_fraction)
    distance = float(_dtai_dtw.distance(a, b, window=window))
    raw_path = _dtai_dtw.warping_path(a, b, window=window)
    path = [(int(i), int(j)) for i, j in raw_path]
    return DTWResult(distance=distance, path=path, window=window)
```

`software/server/tests/unit/temporal/test_dtw.py`:
```python
import pytest

from auralink.temporal.dtw import DTWResult, run_dtw


def test_identical_sequences_have_zero_distance_and_diagonal_path():
    seq = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = run_dtw(seq, seq)
    assert isinstance(result, DTWResult)
    assert result.distance == pytest.approx(0.0, abs=1e-9)
    # identical signals align on the main diagonal. Use set equality rather
    # than list equality so the assertion survives dtaidistance version bumps
    # that may reorder the path list (e.g., start→end vs end→start).
    assert set(result.path) == {(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)}
    # extra sanity: every (i, j) step should satisfy i == j for identical seqs
    assert all(i == j for i, j in result.path)


def test_shifted_signal_has_nondiagonal_path():
    a = [0.0, 1.0, 2.0, 3.0, 2.0, 1.0, 0.0]
    b = [0.0, 0.0, 1.0, 2.0, 3.0, 2.0, 1.0]  # same shape, shifted by one
    result = run_dtw(a, b)
    assert result.distance >= 0.0
    # at least one path step deviates from the main diagonal
    assert any(i != j for i, j in result.path)


def test_window_is_populated_from_sequence_length():
    a = [0.0] * 40
    b = [0.0] * 30
    result = run_dtw(a, b, radius_fraction=0.1)
    # max length is 40, 10% = 4
    assert result.window == 4


def test_different_length_sequences_align():
    a = [0.0, 1.0, 2.0, 3.0, 2.0, 1.0, 0.0]
    b = [0.0, 2.0, 3.0, 2.0, 0.0]  # shorter but similar arc
    result = run_dtw(a, b)
    assert result.distance >= 0.0
    # path must terminate at (last_a, last_b)
    assert result.path[-1] == (len(a) - 1, len(b) - 1)
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/temporal/test_dtw.py -v`

**Expected result:** `4 passed`

**Commit message:** `feat(temporal): add DTW wrapper with Sakoe-Chiba window`

**Expected test count after this task:** 188.

---

#### Task T4: ReferenceRep schema + loader

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/temporal/reference_reps.py`
- `software/server/tests/unit/temporal/test_reference_reps.py`

**Depends on:** T1

**Plan-review notes:** The `ReferenceRep` model mirrors the shape of `NormalizedAngleTimeSeries` so that runtime comparison code can treat it as a drop-in. JSON is the on-disk format so the config files can live under `config/reference_reps/` next to other YAML/JSON configs. The loader accepts an optional `config_dir` override for tests.

**TDD steps:**

- [ ] Write the four tests below.
- [ ] Run the focused test command — expect 4 failures.
- [ ] Create `src/auralink/temporal/reference_reps.py`.
- [ ] Re-run — expect `4 passed`.
- [ ] Commit.

**Exact file contents (verbatim):**

`software/server/src/auralink/temporal/reference_reps.py`:
```python
"""Reference rep schema and JSON loader.

A ReferenceRep is a movement-specific canonical rep used as the DTW target
for per-rep comparisons. The on-disk format is JSON, one file per movement,
generated at build time by scripts/generate_reference_reps.py from the
shared synthetic generator (see docs/plans/2026-04-10-L2-3-dtw-temporal.md
architectural decision 6).

Runtime only reads JSON — it never imports from tests/fixtures.
"""

import json
from pathlib import Path

from pydantic import BaseModel, Field

_DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config" / "reference_reps"


class ReferenceRep(BaseModel):
    """A single canonical rep per movement, stored as normalized angle traces.

    `angles` mirrors NormalizedAngleTimeSeries.angles — dict[str, list[float]]
    keyed by the same joint-angle names (e.g., "left_knee_flexion",
    "trunk_lean", "left_knee_valgus", "right_knee_valgus").
    """

    movement: str
    angles: dict[str, list[float]] = Field(min_length=1)
    frame_rate: float = Field(gt=0.0)
    frames_per_rep: int = Field(gt=0)

    def angle_keys(self) -> set[str]:
        return set(self.angles.keys())


def load_reference_rep(movement: str, config_dir: Path | None = None) -> ReferenceRep:
    """Load the canonical reference rep for a movement.

    Parameters
    ----------
    movement : str
        Movement identifier; must match a generated file name stem.
    config_dir : Path | None
        Optional override; defaults to software/server/config/reference_reps.

    Raises
    ------
    FileNotFoundError : if no JSON file exists for that movement.
    pydantic.ValidationError : if the file is present but malformed.
    """
    base = config_dir if config_dir is not None else _DEFAULT_CONFIG_DIR
    path = base / f"{movement}.json"
    if not path.exists():
        raise FileNotFoundError(f"reference rep not found: {path}")
    raw = json.loads(path.read_text())
    return ReferenceRep.model_validate(raw)
```

`software/server/tests/unit/temporal/test_reference_reps.py`:
```python
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from auralink.temporal.reference_reps import ReferenceRep, load_reference_rep


def _write_ref(tmp_path: Path, movement: str, payload: dict) -> Path:
    p = tmp_path / f"{movement}.json"
    p.write_text(json.dumps(payload))
    return p


def test_load_valid_reference_rep(tmp_path):
    _write_ref(
        tmp_path,
        "overhead_squat",
        {
            "movement": "overhead_squat",
            "angles": {
                "left_knee_flexion": [90.0, 100.0, 110.0, 120.0, 130.0],
                "trunk_lean": [4.0, 4.0, 4.0, 4.0, 4.0],
            },
            "frame_rate": 30.0,
            "frames_per_rep": 5,
        },
    )
    rep = load_reference_rep("overhead_squat", config_dir=tmp_path)
    assert isinstance(rep, ReferenceRep)
    assert rep.movement == "overhead_squat"
    assert rep.frames_per_rep == 5
    assert rep.angles["left_knee_flexion"][0] == 90.0


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_reference_rep("overhead_squat", config_dir=tmp_path)


def test_invalid_schema_raises(tmp_path):
    _write_ref(
        tmp_path,
        "overhead_squat",
        {
            "movement": "overhead_squat",
            "angles": {},
            "frame_rate": 30.0,
            "frames_per_rep": 5,
        },
    )
    with pytest.raises(ValidationError):
        load_reference_rep("overhead_squat", config_dir=tmp_path)


def test_angle_keys_returns_set(tmp_path):
    _write_ref(
        tmp_path,
        "push_up",
        {
            "movement": "push_up",
            "angles": {
                "left_elbow_flexion": [90.0, 100.0, 110.0],
                "right_elbow_flexion": [90.0, 100.0, 110.0],
            },
            "frame_rate": 30.0,
            "frames_per_rep": 3,
        },
    )
    rep = load_reference_rep("push_up", config_dir=tmp_path)
    assert rep.angle_keys() == {"left_elbow_flexion", "right_elbow_flexion"}
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/temporal/test_reference_reps.py -v`

**Expected result:** `4 passed`

**Commit message:** `feat(temporal): add ReferenceRep schema and JSON loader`

**Expected test count after this task:** 192.

---

#### Task T5: RepComparison + MovementTemporalSummary schemas

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/pipeline/artifacts.py`
- `software/server/tests/unit/pipeline/test_artifacts_temporal.py`

**Depends on:** T1

**Plan-review notes:** T5 modifies `artifacts.py` by adding two new classes at the bottom of the existing model list, before `PipelineArtifacts`. It does NOT add the new field to `PipelineArtifacts` itself — that happens in T12 where orchestrator wiring needs it. Keeping the `PipelineArtifacts` change in a single atomic commit with the orchestrator makes bisecting easier if the pipeline mis-wires.

**TDD steps:**

- [ ] Read the existing `artifacts.py` (see Existing Code References).
- [ ] Write the test file.
- [ ] Run focused test — expect 2 failures.
- [ ] Edit `artifacts.py` to append the two new classes.
- [ ] Re-run — expect `2 passed`.
- [ ] Commit.

**Edit to `software/server/src/auralink/pipeline/artifacts.py`:** append the following classes AFTER `WithinMovementTrend` (line 61) and BEFORE `LiftedAngleTimeSeries` (line 63). Add `Literal` to the imports at the top of the file — the new `status` field uses it.

Top of file — change line 1 `from pydantic import BaseModel, Field` to:

```python
from typing import Literal

from pydantic import BaseModel, Field
```

Insertion block (verbatim) — drop this between `WithinMovementTrend` and `LiftedAngleTimeSeries`:

```python


class RepComparison(BaseModel):
    """One rep scored against the movement's reference rep.

    ncc_score may be NaN when the user rep is a flat signal (zero variance);
    callers must handle NaN before arithmetic. rom_deviation_pct is a signed
    percentage: positive means the user's range of motion exceeds the
    reference, negative means it falls short. status is the combined
    classification from NCC and ROM thresholds (NCC amplitude-guard rule —
    see plan architectural decision 5).
    """

    rep_index: int = Field(ge=0)
    angle: str
    ncc_score: float
    dtw_distance: float = Field(ge=0.0)
    rom_user_deg: float = Field(ge=0.0)
    rom_reference_deg: float = Field(ge=0.0)
    rom_deviation_pct: float
    status: Literal["clean", "concern", "flag"]


class MovementTemporalSummary(BaseModel):
    """Within-movement temporal aggregation over a list of RepComparisons.

    ncc_slope_per_rep is fit with numpy.polyfit over the NCC scores treating
    rep index as x; a negative slope means shape is drifting away from the
    reference across the set. mean_rom_deviation_pct is a plain mean of the
    rom_deviation_pct field. form_drift_detected is a joint condition — both
    a sufficiently negative NCC slope AND a large mean ROM deviation must be
    present — to avoid false positives from a single noisy rep.
    """

    primary_angle: str
    rep_comparisons: list[RepComparison] = Field(default_factory=list)
    mean_ncc: float
    ncc_slope_per_rep: float
    mean_rom_deviation_pct: float
    form_drift_detected: bool
```

`software/server/tests/unit/pipeline/test_artifacts_temporal.py`:
```python
from auralink.pipeline.artifacts import MovementTemporalSummary, RepComparison


def test_rep_comparison_serializes_all_fields():
    rc = RepComparison(
        rep_index=0,
        angle="left_knee_flexion",
        ncc_score=0.97,
        dtw_distance=1.4,
        rom_user_deg=88.0,
        rom_reference_deg=90.0,
        rom_deviation_pct=-2.22,
        status="clean",
    )
    data = rc.model_dump(mode="json")
    assert data["rep_index"] == 0
    assert data["angle"] == "left_knee_flexion"
    assert data["ncc_score"] == 0.97
    assert data["status"] == "clean"


def test_movement_temporal_summary_holds_comparisons():
    comparisons = [
        RepComparison(
            rep_index=i,
            angle="left_knee_flexion",
            ncc_score=0.95 - 0.02 * i,
            dtw_distance=1.0 + i,
            rom_user_deg=90.0 - 3.0 * i,
            rom_reference_deg=90.0,
            rom_deviation_pct=-3.33 * i,
            status="concern" if i > 0 else "clean",
        )
        for i in range(3)
    ]
    summary = MovementTemporalSummary(
        primary_angle="left_knee_flexion",
        rep_comparisons=comparisons,
        mean_ncc=0.93,
        ncc_slope_per_rep=-0.02,
        mean_rom_deviation_pct=-3.33,
        form_drift_detected=False,
    )
    assert len(summary.rep_comparisons) == 3
    assert summary.primary_angle == "left_knee_flexion"
    assert summary.ncc_slope_per_rep == -0.02
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/pipeline/test_artifacts_temporal.py -v`

**Expected result:** `2 passed`

**Commit message:** `feat(artifacts): add RepComparison and MovementTemporalSummary`

**Expected test count after this task:** 194.

---

#### Task T6: Temporal thresholds YAML + loader

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/config/temporal/thresholds.yaml`
- `software/server/src/auralink/temporal/threshold_loader.py`
- `software/server/tests/unit/temporal/test_threshold_loader.py`

**Depends on:** T1

**Plan-review notes:** Structure mirrors `reasoning/threshold_loader.py` (see Existing Code References). Uses `pyyaml` which is already a dependency after Plan 2. Values come from the literature review in `ncc-implementation-2026-04-14.md` §4 and the ROM drift empirical bands used by the Plan 1 `within_movement_trend` stage (hence the -0.02 slope threshold — ~1% NCC drop per rep compounded).

**TDD steps:**

- [ ] Write the YAML and the three tests below.
- [ ] Run focused test — expect 3 failures.
- [ ] Create `threshold_loader.py` with the verbatim implementation.
- [ ] Re-run — expect `3 passed`.
- [ ] Commit.

**Exact file contents (verbatim):**

`software/server/config/temporal/thresholds.yaml`:
```yaml
# Temporal analysis thresholds for Plan 3 rep_comparison stage.
#
# NCC thresholds from gait biomechanics literature review
# (docs/research/ncc-implementation-2026-04-14.md section 4):
#   Kavanagh et al. 0.85-0.95 intra-subject XCC
#   Ferrari et al. CMC >0.90 excellent / 0.75-0.90 good
#   Iosa 2014 clinical gait 0.8-0.9 acceptable / >0.9 strong
#
# ROM deviation thresholds: 15% concern (noticeable but within ordinary
# intra-subject variation) / 25% flag (meaningful partial-range compensation).
#
# form_drift_ncc_slope_threshold: polyfit slope over NCC across reps.
# -0.02 per rep means a ~2% drop per rep; over 5 reps that is a 10% decline.

ncc_clean_min: 0.95
ncc_concern_min: 0.75
rom_deviation_concern_pct: 15.0
rom_deviation_flag_pct: 25.0
form_drift_ncc_slope_threshold: -0.02
form_drift_rom_mean_deviation_pct: 15.0
```

`software/server/src/auralink/temporal/threshold_loader.py`:
```python
"""YAML loader for temporal analysis thresholds.

Mirrors the structure of reasoning/threshold_loader.py. Loaded once at
startup (from rep_comparison stage) and passed as an explicit argument into
compare_rep() / summarize_comparisons() so tests can inject overrides.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config" / "temporal"
_DEFAULT_PATH = _CONFIG_DIR / "thresholds.yaml"


class TemporalThresholds(BaseModel):
    """Thresholds used by the rep_comparison stage and within-movement summary.

    See config/temporal/thresholds.yaml for the canonical default values and
    their literature provenance.
    """

    ncc_clean_min: float = Field(gt=0.0, le=1.0)
    ncc_concern_min: float = Field(gt=0.0, le=1.0)
    rom_deviation_concern_pct: float = Field(gt=0.0)
    rom_deviation_flag_pct: float = Field(gt=0.0)
    form_drift_ncc_slope_threshold: float
    form_drift_rom_mean_deviation_pct: float = Field(gt=0.0)


def load_temporal_thresholds(path: Path | None = None) -> TemporalThresholds:
    """Read and validate the temporal thresholds YAML."""
    p = path or _DEFAULT_PATH
    if not p.exists():
        raise FileNotFoundError(f"temporal thresholds not found: {p}")
    raw = yaml.safe_load(p.read_text())
    return TemporalThresholds.model_validate(raw)
```

`software/server/tests/unit/temporal/test_threshold_loader.py`:
```python
from pathlib import Path

import pytest

from auralink.temporal.threshold_loader import (
    TemporalThresholds,
    load_temporal_thresholds,
)


def _write_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "thresholds.yaml"
    p.write_text(
        """
ncc_clean_min: 0.95
ncc_concern_min: 0.75
rom_deviation_concern_pct: 15.0
rom_deviation_flag_pct: 25.0
form_drift_ncc_slope_threshold: -0.02
form_drift_rom_mean_deviation_pct: 15.0
"""
    )
    return p


def test_loads_yaml_into_dataclass(tmp_path):
    p = _write_yaml(tmp_path)
    thresholds = load_temporal_thresholds(p)
    assert isinstance(thresholds, TemporalThresholds)
    assert thresholds.ncc_clean_min == 0.95
    assert thresholds.rom_deviation_flag_pct == 25.0
    assert thresholds.form_drift_ncc_slope_threshold == -0.02


def test_default_path_resolves_to_repo_config():
    thresholds = load_temporal_thresholds()
    assert isinstance(thresholds, TemporalThresholds)
    assert 0.0 < thresholds.ncc_concern_min < thresholds.ncc_clean_min <= 1.0


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_temporal_thresholds(tmp_path / "does_not_exist.yaml")
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/temporal/test_threshold_loader.py -v`

**Expected result:** `3 passed`

**Commit message:** `feat(temporal): add threshold YAML config and loader`

**Expected test count after this task:** 197.

---

#### Task T7: Per-rep comparison function

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/temporal/comparison.py`
- `software/server/tests/unit/temporal/test_comparison.py`

**Depends on:** T2, T3, T5, T6

**Plan-review notes:** This task is where the amplitude guard from architectural decision 5 lives. The tests MUST include a half-ROM-but-same-shape rep that gets classified `flag` even though its NCC is ~1.0. That test is the regression guard against anyone later "simplifying" comparison to NCC-only. Reversed rep is classified `flag` both because its NCC is -1.0 AND because its ROM typically matches; the NCC branch alone is sufficient.

**TDD steps:**

- [ ] Write the five tests below.
- [ ] Run focused test — expect 5 failures.
- [ ] Create `comparison.py` with the verbatim implementation.
- [ ] Re-run — expect `5 passed`.
- [ ] Commit.

**Exact file contents (verbatim):**

`software/server/src/auralink/temporal/comparison.py`:
```python
"""Per-rep comparison against a reference rep.

Pipeline: DTW align (run_dtw) -> re-index via warping path -> NCC score
(ncc) -> ROM deviation -> joint clean/concern/flag status.

The status classification enforces the NCC amplitude guard (see
docs/plans/2026-04-10-L2-3-dtw-temporal.md architectural decision 5): NCC
alone is scale-invariant and will score a half-range rep near 1.0, so ROM
deviation is checked independently and the worst of the two classifications
wins.
"""

import math

import numpy as np

from auralink.pipeline.artifacts import RepComparison
from auralink.temporal.dtw import run_dtw
from auralink.temporal.ncc import ncc
from auralink.temporal.threshold_loader import TemporalThresholds

_STATUS_ORDER = {"clean": 0, "concern": 1, "flag": 2}
_INVERSE_ORDER = {v: k for k, v in _STATUS_ORDER.items()}


def _rom(window: list[float]) -> float:
    if not window:
        return 0.0
    return float(max(window) - min(window))


def _classify_ncc(score: float, thresholds: TemporalThresholds) -> str:
    if math.isnan(score):
        return "flag"
    if score >= thresholds.ncc_clean_min:
        return "clean"
    if score >= thresholds.ncc_concern_min:
        return "concern"
    return "flag"


def _classify_rom(deviation_pct: float, thresholds: TemporalThresholds) -> str:
    abs_dev = abs(deviation_pct)
    if abs_dev >= thresholds.rom_deviation_flag_pct:
        return "flag"
    if abs_dev >= thresholds.rom_deviation_concern_pct:
        return "concern"
    return "clean"


def _worst(a: str, b: str) -> str:
    return _INVERSE_ORDER[max(_STATUS_ORDER[a], _STATUS_ORDER[b])]


def compare_rep(
    user_angles: list[float],
    reference_angles: list[float],
    angle_name: str,
    rep_index: int,
    thresholds: TemporalThresholds,
) -> RepComparison:
    """Compare one user rep against the reference rep for a single angle.

    Handles empty windows by returning a `flag` status with a NaN NCC score
    rather than raising — empty reps are usually an upstream rep-segment
    issue and should surface as data quality flags, not pipeline crashes.
    """
    if not user_angles or not reference_angles:
        return RepComparison(
            rep_index=rep_index,
            angle=angle_name,
            ncc_score=float("nan"),
            dtw_distance=0.0,
            rom_user_deg=_rom(user_angles),
            rom_reference_deg=_rom(reference_angles),
            rom_deviation_pct=0.0,
            status="flag",
        )

    dtw_result = run_dtw(user_angles, reference_angles)
    # Re-index both sequences along the warp path so they become equal-length
    # for zero-lag NCC. The warp path is a list of (i_user, j_ref) tuples.
    user_aligned = np.array([user_angles[i] for i, _ in dtw_result.path], dtype=np.float64)
    ref_aligned = np.array([reference_angles[j] for _, j in dtw_result.path], dtype=np.float64)
    ncc_score = ncc(user_aligned, ref_aligned)

    rom_user = _rom(user_angles)
    rom_ref = _rom(reference_angles)
    if rom_ref > 0.0:
        rom_deviation_pct = (rom_user - rom_ref) / rom_ref * 100.0
    else:
        rom_deviation_pct = 0.0

    ncc_status = _classify_ncc(ncc_score, thresholds)
    rom_status = _classify_rom(rom_deviation_pct, thresholds)
    status = _worst(ncc_status, rom_status)

    return RepComparison(
        rep_index=rep_index,
        angle=angle_name,
        ncc_score=float(ncc_score) if not math.isnan(ncc_score) else float("nan"),
        dtw_distance=dtw_result.distance,
        rom_user_deg=rom_user,
        rom_reference_deg=rom_ref,
        rom_deviation_pct=rom_deviation_pct,
        status=status,  # type: ignore[arg-type]
    )
```

`software/server/tests/unit/temporal/test_comparison.py`:
```python
import math

import pytest

from auralink.temporal.comparison import compare_rep
from auralink.temporal.threshold_loader import TemporalThresholds


@pytest.fixture
def thresholds() -> TemporalThresholds:
    return TemporalThresholds(
        ncc_clean_min=0.95,
        ncc_concern_min=0.75,
        rom_deviation_concern_pct=15.0,
        rom_deviation_flag_pct=25.0,
        form_drift_ncc_slope_threshold=-0.02,
        form_drift_rom_mean_deviation_pct=15.0,
    )


def _cosine_rep(n: int = 30, amplitude: float = 45.0, offset: float = 135.0) -> list[float]:
    return [offset + amplitude * math.cos(2.0 * math.pi * i / n) for i in range(n)]


def test_identical_rep_is_clean(thresholds):
    ref = _cosine_rep()
    user = list(ref)
    result = compare_rep(user, ref, "left_knee_flexion", 0, thresholds)
    assert result.status == "clean"
    assert result.ncc_score == pytest.approx(1.0, abs=1e-9)
    assert abs(result.rom_deviation_pct) < 0.5


def test_half_rom_rep_is_flagged_despite_matching_shape(thresholds):
    """NCC amplitude guard — a half-range rep has ncc ~1.0 but must flag."""
    ref = _cosine_rep(amplitude=45.0)
    user = _cosine_rep(amplitude=22.5)  # same shape, half ROM
    result = compare_rep(user, ref, "left_knee_flexion", 1, thresholds)
    assert result.ncc_score == pytest.approx(1.0, abs=1e-9)
    assert result.status == "flag"
    assert result.rom_deviation_pct < -40.0  # roughly -50%


def test_slight_rom_drop_with_matching_shape_is_concern(thresholds):
    ref = _cosine_rep(amplitude=45.0)
    user = _cosine_rep(amplitude=36.0)  # -20% ROM -> concern band
    result = compare_rep(user, ref, "left_knee_flexion", 2, thresholds)
    assert result.ncc_score == pytest.approx(1.0, abs=1e-9)
    assert result.status == "concern"
    assert -25.0 < result.rom_deviation_pct < -15.0


def test_inverse_rep_is_flagged(thresholds):
    ref = _cosine_rep()
    user = [180.0 - v for v in ref]  # shape-inverted
    result = compare_rep(user, ref, "left_knee_flexion", 3, thresholds)
    # status flag from NCC branch (ncc will be -1 or close to it)
    assert result.status == "flag"


def test_empty_user_rep_is_flagged(thresholds):
    ref = _cosine_rep()
    result = compare_rep([], ref, "left_knee_flexion", 4, thresholds)
    assert result.status == "flag"
    assert math.isnan(result.ncc_score)
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/temporal/test_comparison.py -v`

**Expected result:** `5 passed`

**Commit message:** `feat(temporal): add per-rep comparison with NCC + ROM guard`

**Expected test count after this task:** 202.

---

#### Task T8: Within-movement summary module

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/temporal/summary.py`
- `software/server/tests/unit/temporal/test_summary.py`

**Depends on:** T5, T6

**Plan-review notes:** Uses `numpy.polyfit(order=1)` the same way `pipeline/stages/within_movement_trend.py` already does (see Existing Code References) — one consistent slope-fit idiom across the codebase. Drift is a JOINT condition (NCC slope negative enough AND mean ROM deviation large enough); the test matrix includes the three single-signal cases and the combined case to prove the AND semantics.

**TDD steps:**

- [ ] Write the four tests below.
- [ ] Run focused test — expect 4 failures.
- [ ] Create `summary.py` with the verbatim implementation.
- [ ] Re-run — expect `4 passed`.
- [ ] Commit.

**Exact file contents (verbatim):**

`software/server/src/auralink/temporal/summary.py`:
```python
"""Within-movement aggregation over a list of RepComparisons.

Produces a MovementTemporalSummary with the mean NCC, the linear-fit slope
of NCC across reps (same polyfit idiom used by within_movement_trend), and
a form_drift_detected flag that fires on the JOINT condition of negative NCC
slope AND large mean ROM deviation. Joint (not either-or) to avoid false
positives from a single noisy rep or a consistent but shape-matched
lower-ROM set.
"""

import math

import numpy as np

from auralink.pipeline.artifacts import MovementTemporalSummary, RepComparison
from auralink.temporal.threshold_loader import TemporalThresholds


def _slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    xs = np.arange(len(values), dtype=np.float64)
    ys = np.asarray(values, dtype=np.float64)
    slope, _intercept = np.polyfit(xs, ys, 1)
    return float(slope)


def _finite_ncc_scores(comparisons: list[RepComparison]) -> list[float]:
    return [c.ncc_score for c in comparisons if not math.isnan(c.ncc_score)]


def summarize_comparisons(
    comparisons: list[RepComparison],
    primary_angle: str,
    thresholds: TemporalThresholds,
) -> MovementTemporalSummary:
    """Aggregate per-rep comparisons into a within-movement summary.

    NaN NCC scores (empty reps) are excluded from mean/slope computation so
    one dropout does not drag the aggregate. rom_deviation_pct is used as-is
    (there is no defined NaN state for it).
    """
    finite_ncc = _finite_ncc_scores(comparisons)
    mean_ncc = float(np.mean(finite_ncc)) if finite_ncc else float("nan")
    ncc_slope = _slope(finite_ncc)

    rom_dev_values = [c.rom_deviation_pct for c in comparisons]
    mean_rom_dev = float(np.mean(rom_dev_values)) if rom_dev_values else 0.0

    drift = (
        ncc_slope <= thresholds.form_drift_ncc_slope_threshold
        and abs(mean_rom_dev) >= thresholds.form_drift_rom_mean_deviation_pct
    )

    return MovementTemporalSummary(
        primary_angle=primary_angle,
        rep_comparisons=comparisons,
        mean_ncc=mean_ncc if not math.isnan(mean_ncc) else 0.0,
        ncc_slope_per_rep=ncc_slope,
        mean_rom_deviation_pct=mean_rom_dev,
        form_drift_detected=drift,
    )
```

`software/server/tests/unit/temporal/test_summary.py`:
```python
import pytest

from auralink.pipeline.artifacts import RepComparison
from auralink.temporal.summary import summarize_comparisons
from auralink.temporal.threshold_loader import TemporalThresholds


@pytest.fixture
def thresholds() -> TemporalThresholds:
    return TemporalThresholds(
        ncc_clean_min=0.95,
        ncc_concern_min=0.75,
        rom_deviation_concern_pct=15.0,
        rom_deviation_flag_pct=25.0,
        form_drift_ncc_slope_threshold=-0.02,
        form_drift_rom_mean_deviation_pct=15.0,
    )


def _mk(rep_index: int, ncc: float, rom_dev_pct: float) -> RepComparison:
    return RepComparison(
        rep_index=rep_index,
        angle="left_knee_flexion",
        ncc_score=ncc,
        dtw_distance=1.0,
        rom_user_deg=90.0 * (1.0 + rom_dev_pct / 100.0),
        rom_reference_deg=90.0,
        rom_deviation_pct=rom_dev_pct,
        status="clean",
    )


def test_flat_ncc_no_drift(thresholds):
    comparisons = [_mk(i, 0.97, -2.0) for i in range(5)]
    summary = summarize_comparisons(comparisons, "left_knee_flexion", thresholds)
    assert summary.form_drift_detected is False
    assert summary.mean_ncc == pytest.approx(0.97, abs=1e-9)
    assert abs(summary.ncc_slope_per_rep) < 1e-9


def test_ncc_decline_alone_without_rom_deviation_does_not_trigger_drift(thresholds):
    # NCC clearly declining, but ROM deviation stays small -> no drift by
    # the joint-condition rule.
    comparisons = [_mk(i, 0.98 - 0.05 * i, -1.0) for i in range(5)]
    summary = summarize_comparisons(comparisons, "left_knee_flexion", thresholds)
    assert summary.ncc_slope_per_rep <= -0.02
    assert summary.form_drift_detected is False


def test_rom_deviation_alone_without_ncc_decline_does_not_trigger_drift(thresholds):
    comparisons = [_mk(i, 0.97, -20.0) for i in range(5)]
    summary = summarize_comparisons(comparisons, "left_knee_flexion", thresholds)
    assert abs(summary.mean_rom_deviation_pct) >= 15.0
    assert summary.form_drift_detected is False


def test_combined_ncc_decline_and_rom_deviation_triggers_drift(thresholds):
    comparisons = [_mk(i, 0.98 - 0.05 * i, -18.0) for i in range(5)]
    summary = summarize_comparisons(comparisons, "left_knee_flexion", thresholds)
    assert summary.form_drift_detected is True
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/temporal/test_summary.py -v`

**Expected result:** `4 passed`

**Commit message:** `feat(temporal): add within-movement summary aggregator`

**Expected test count after this task:** 206.

---

#### Task T9: Protocol + ProtocolReport + CrossMovementMetric schemas

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/protocol/__init__.py`
- `software/server/src/auralink/protocol/schemas.py`
- `software/server/tests/unit/protocol/__init__.py`
- `software/server/tests/unit/protocol/test_schemas.py`

**Depends on:** T1

**Plan-review notes:** Pure pydantic work; the only dependency is pydantic itself. Kept in Wave B alongside T7 and T8 because it is conceptually grouped with the protocol layer and its size does not justify its own wave.

**TDD steps:**

- [ ] Write the two tests.
- [ ] Run focused test — expect 2 failures.
- [ ] Create `protocol/__init__.py`, `protocol/schemas.py`, and `tests/unit/protocol/__init__.py`.
- [ ] Re-run — expect `2 passed`.
- [ ] Commit.

**Exact file contents (verbatim):**

`software/server/src/auralink/protocol/__init__.py`:
```python
```

`software/server/tests/unit/protocol/__init__.py`:
```python
```

`software/server/src/auralink/protocol/schemas.py`:
```python
"""Protocol-level schemas — cross-session aggregation surface.

A protocol is a sequence of sessions (typically one per movement in the
four-movement screening). Aggregation is triggered by POST /protocols, which
loads per-session artifacts and calls protocol.aggregator.aggregate_protocol
to produce a ProtocolReport. Cross-session analysis is never a pipeline
stage; stages run per-session.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ProtocolRequest(BaseModel):
    """POST /protocols request body: a list of session IDs to aggregate."""

    session_ids: list[str] = Field(min_length=1, max_length=10)


class CrossMovementMetric(BaseModel):
    """One metric aggregated across the movements in a protocol.

    values_by_movement is keyed by movement string (e.g. "overhead_squat").
    trend classifies the sequence: "improving" when lower-is-better metrics
    decrease across sessions or higher-is-better metrics increase; "declining"
    is the opposite; "stable" when neither.
    """

    metric_name: str
    values_by_movement: dict[str, float]
    trend: Literal["improving", "stable", "declining"]


class ProtocolReport(BaseModel):
    """POST /protocols response body.

    per_session_movements maps session_id to movement string for easy
    presentation without re-reading session artifacts. fatigue_carryover_detected
    fires when cross-session mean NCC declines AND mean ROM deviation grows
    across >= 3 sessions.
    """

    session_ids: list[str]
    per_session_movements: dict[str, str]
    cross_movement_metrics: list[CrossMovementMetric] = Field(default_factory=list)
    fatigue_carryover_detected: bool
    summary_narrative: str
```

`software/server/tests/unit/protocol/test_schemas.py`:
```python
import pytest
from pydantic import ValidationError

from auralink.protocol.schemas import CrossMovementMetric, ProtocolReport, ProtocolRequest


def test_protocol_request_min_and_max_length():
    assert ProtocolRequest(session_ids=["a"]).session_ids == ["a"]
    with pytest.raises(ValidationError):
        ProtocolRequest(session_ids=[])
    with pytest.raises(ValidationError):
        ProtocolRequest(session_ids=[f"s{i}" for i in range(11)])


def test_protocol_report_and_cross_movement_metric_round_trip():
    metric = CrossMovementMetric(
        metric_name="mean_ncc",
        values_by_movement={"overhead_squat": 0.93, "single_leg_squat": 0.90},
        trend="declining",
    )
    report = ProtocolReport(
        session_ids=["s1", "s2"],
        per_session_movements={"s1": "overhead_squat", "s2": "single_leg_squat"},
        cross_movement_metrics=[metric],
        fatigue_carryover_detected=True,
        summary_narrative="Your movement shows a cumulative pattern across the session.",
    )
    data = report.model_dump(mode="json")
    restored = ProtocolReport.model_validate(data)
    assert restored.fatigue_carryover_detected is True
    assert restored.cross_movement_metrics[0].metric_name == "mean_ncc"
    assert restored.cross_movement_metrics[0].trend == "declining"
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/protocol/test_schemas.py -v`

**Expected result:** `2 passed`

**Commit message:** `feat(protocol): add Protocol and ProtocolReport schemas`

**Expected test count after this task:** 208.

---

#### Task T10: Reference rep generation script + config files

**Label:** skip-tdd (1 verification test)

**Files owned (exclusive to this task):**
- `software/server/scripts/generate_reference_reps.py`
- `software/server/config/reference_reps/overhead_squat.json`
- `software/server/config/reference_reps/single_leg_squat.json`
- `software/server/config/reference_reps/push_up.json`
- `software/server/tests/unit/temporal/test_reference_rep_files.py`

**Depends on:** T4

**Plan-review notes:** The script is run ONCE at build time (or re-run whenever the synthetic generator or the Plan 1 normalize stage changes). Its output — the three JSON files — is committed to the repo. Do NOT .gitignore `config/reference_reps/` — those files are config artifacts, not generated binaries. The one verification test simply asserts the committed files exist and parse as `ReferenceRep`. `rollup` is phase-based (no reps), so it is deliberately excluded.

**Steps:**

- [ ] Create `scripts/generate_reference_reps.py`.
- [ ] Run it: `cd software/server && uv run python scripts/generate_reference_reps.py`.
- [ ] Verify three JSON files exist under `config/reference_reps/`.
- [ ] Write `tests/unit/temporal/test_reference_rep_files.py`.
- [ ] Run `cd software/server && uv run pytest tests/unit/temporal/test_reference_rep_files.py -v` — expect `1 passed`.
- [ ] Commit the script, the three JSONs, and the test together.

**Exact file contents (verbatim):**

`software/server/scripts/generate_reference_reps.py`:
```python
"""Build-time generator for canonical reference reps (Plan 3).

Consumes generate_reference_rep() from tests/fixtures/synthetic/generator.py
— the shared synthetic generator owned by Plan 4 — runs the Plan 1 stages
(quality_gate, angle_series, normalize) on each resulting single-rep
session, extracts the normalized angle traces, and persists them as JSON
under software/server/config/reference_reps/.

Runtime temporal.reference_reps.load_reference_rep() reads these JSON
files at startup. The runtime never imports tests.fixtures — this script
is the only bridge.

Run with:
    cd software/server && uv run python scripts/generate_reference_reps.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_SERVER_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_SERVER_ROOT / "src"))
sys.path.insert(0, str(_SERVER_ROOT))  # for tests.fixtures import

from auralink.api.schemas import Session  # noqa: E402
from auralink.pipeline.stages.angle_series import run_angle_series  # noqa: E402
from auralink.pipeline.stages.base import StageContext  # noqa: E402
from auralink.pipeline.stages.normalize import run_normalize  # noqa: E402
from auralink.pipeline.stages.quality_gate import run_quality_gate  # noqa: E402
from tests.fixtures.synthetic.generator import generate_reference_rep  # noqa: E402

_OUTPUT_DIR = _SERVER_ROOT / "config" / "reference_reps"

_MOVEMENTS_WITH_REPS = (
    "overhead_squat",
    "single_leg_squat",
    "push_up",
)


def _normalized_angles_for_movement(movement: str) -> tuple[dict[str, list[float]], int, float]:
    payload = generate_reference_rep(movement=movement, frames_per_rep=30, frame_rate=30.0)
    session = Session.model_validate(payload)
    ctx = StageContext(session=session)
    ctx.artifacts["quality_gate"] = run_quality_gate(ctx)
    ctx.artifacts["angle_series"] = run_angle_series(ctx)
    ctx.artifacts["normalize"] = run_normalize(ctx)
    normalized = ctx.artifacts["normalize"]
    return normalized.angles, len(session.frames), session.metadata.frame_rate


def _write_reference_rep(movement: str) -> Path:
    angles, frames_per_rep, frame_rate = _normalized_angles_for_movement(movement)
    payload = {
        "movement": movement,
        "angles": angles,
        "frame_rate": frame_rate,
        "frames_per_rep": frames_per_rep,
    }
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _OUTPUT_DIR / f"{movement}.json"
    out_path.write_text(json.dumps(payload, indent=2))
    return out_path


def main() -> None:
    written: list[Path] = []
    for movement in _MOVEMENTS_WITH_REPS:
        path = _write_reference_rep(movement)
        print(f"wrote {path}")
        written.append(path)
    print(f"done: {len(written)} reference reps written to {_OUTPUT_DIR}")


if __name__ == "__main__":
    main()
```

`software/server/config/reference_reps/overhead_squat.json`, `single_leg_squat.json`, `push_up.json`: **generated by running the script above**. Do not hand-write; run the script and commit its output.

`software/server/tests/unit/temporal/test_reference_rep_files.py`:
```python
from pathlib import Path

from auralink.temporal.reference_reps import ReferenceRep, load_reference_rep

_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config" / "reference_reps"


# Primary angles that rep_comparison will look up per movement, sourced
# from auralink.pipeline.stages.per_rep_metrics.PRIMARY_ANGLE and the
# push_up stage's analogous constant. If these drift, T11's stage fails
# at runtime with a cryptic KeyError — catch it here instead.
_PRIMARY_ANGLE_BY_MOVEMENT = {
    "overhead_squat": "left_knee_flexion",
    "single_leg_squat": "left_knee_flexion",
    "push_up": "left_knee_flexion",  # push_up shares the synthetic sweep
}


def test_committed_reference_reps_load_for_all_rep_based_movements():
    for movement in ("overhead_squat", "single_leg_squat", "push_up"):
        rep = load_reference_rep(movement, config_dir=_CONFIG_DIR)
        assert isinstance(rep, ReferenceRep)
        assert rep.movement == movement
        assert rep.frames_per_rep > 0
        # every angle trace has the same length as frames_per_rep
        for _name, series in rep.angles.items():
            assert len(series) == rep.frames_per_rep


def test_reference_reps_contain_primary_angle_per_movement():
    """Plumbing guard: the primary angle rep_comparison will look up at
    runtime must exist in the committed reference rep. Without this check
    a reference/runtime key mismatch only surfaces in T11's stage tests
    or worse in T17's dev-server smoke."""
    for movement, primary_angle in _PRIMARY_ANGLE_BY_MOVEMENT.items():
        rep = load_reference_rep(movement, config_dir=_CONFIG_DIR)
        assert primary_angle in rep.angles, (
            f"reference rep for {movement} missing primary_angle "
            f"{primary_angle!r}; has {sorted(rep.angles.keys())}"
        )
        assert len(rep.angles[primary_angle]) > 0
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/temporal/test_reference_rep_files.py -v`

**Expected result:** `2 passed`

**Commit message:** `feat(temporal): generate reference reps from Plan 4 synthetic fixtures`

**Expected test count after this task:** 210.

---

#### Task T11: rep_comparison pipeline stage

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/pipeline/stages/rep_comparison.py`
- `software/server/tests/unit/pipeline/test_rep_comparison_stage.py`

**Depends on:** T4, T7, T8

**Plan-review notes:** The stage reads `ctx.artifacts["per_rep_metrics"]` for the rep index list and primary angle name, and `ctx.artifacts["normalize"]` for the raw joint-angle traces keyed by that angle. It then slices each rep window from the raw trace (NOT from the `PerRepMetrics`, which are scalar summaries). Rep boundaries come from `ctx.artifacts["rep_segment"]` (also already populated by Plan 1). The stage caches `load_temporal_thresholds()` and `load_reference_rep(movement)` at call time; if the orchestrator runs the pipeline concurrently per-session this stays correct because both functions are pure. T11 is intentionally NOT listed as depending on T10: T11's tests monkeypatch `auralink.temporal.reference_reps._DEFAULT_CONFIG_DIR` to a `tmp_path` via an autouse fixture and write synthetic reference rep JSON there, so T10's committed `config/reference_reps/*.json` files are not read at green-test time. T10 and T11 therefore run in parallel within Wave C on disjoint file sets.

**TDD steps:**

- [ ] Write the four tests below.
- [ ] Run focused test — expect 4 failures.
- [ ] Create `rep_comparison.py` with the verbatim implementation.
- [ ] Re-run — expect `4 passed`.
- [ ] Commit.

**Exact file contents (verbatim):**

`software/server/src/auralink/pipeline/stages/rep_comparison.py`:
```python
"""rep_comparison pipeline stage.

Consumes:
  - ctx.artifacts["per_rep_metrics"]  (PerRepMetrics, from Plan 1)
  - ctx.artifacts["rep_segment"]      (RepBoundaries, from Plan 1)
  - ctx.artifacts["normalize"]        (NormalizedAngleTimeSeries, from Plan 1)

Produces:
  - MovementTemporalSummary

Runs only on movements that have per_rep_metrics — i.e., overhead_squat and
single_leg_squat. push_up and rollup never hit this stage because they are
not wired into the orchestrator lists for those movements.
"""

from auralink.pipeline.artifacts import (
    MovementTemporalSummary,
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    RepBoundaries,
    RepComparison,
)
from auralink.pipeline.stages.base import StageContext
from auralink.temporal.comparison import compare_rep
from auralink.temporal.reference_reps import load_reference_rep
from auralink.temporal.summary import summarize_comparisons
from auralink.temporal.threshold_loader import load_temporal_thresholds


def run_rep_comparison(ctx: StageContext) -> MovementTemporalSummary:
    metrics: PerRepMetrics = ctx.artifacts["per_rep_metrics"]
    normalized: NormalizedAngleTimeSeries = ctx.artifacts["normalize"]
    rep_boundaries: RepBoundaries = ctx.artifacts["rep_segment"]

    primary_angle = metrics.primary_angle
    movement = ctx.session.metadata.movement

    reference = load_reference_rep(movement)
    if primary_angle not in reference.angles:
        raise KeyError(
            f"reference rep for {movement} has no angle {primary_angle!r}; "
            f"available: {sorted(reference.angles.keys())}"
        )
    reference_angles = reference.angles[primary_angle]

    thresholds = load_temporal_thresholds()
    user_trace = normalized.angles.get(primary_angle, [])
    boundaries = rep_boundaries.by_angle.get(primary_angle, [])

    comparisons: list[RepComparison] = []
    for idx, rep in enumerate(boundaries):
        window = user_trace[rep.start_index : rep.end_index + 1]
        comparisons.append(
            compare_rep(
                user_angles=window,
                reference_angles=reference_angles,
                angle_name=primary_angle,
                rep_index=idx,
                thresholds=thresholds,
            )
        )

    return summarize_comparisons(
        comparisons=comparisons,
        primary_angle=primary_angle,
        thresholds=thresholds,
    )
```

`software/server/tests/unit/pipeline/test_rep_comparison_stage.py`:
```python
import math
from pathlib import Path

import pytest

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.artifacts import (
    MovementTemporalSummary,
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    RepBoundaries,
    RepBoundaryModel,
    RepMetric,
)
from auralink.pipeline.stages.base import StageContext
from auralink.pipeline.stages.rep_comparison import run_rep_comparison


def _make_session(movement: str) -> Session:
    lm = [Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0) for _ in range(33)]
    frame = Frame(timestamp_ms=0, landmarks=lm)
    return Session(
        metadata=SessionMetadata(
            movement=movement,  # type: ignore[arg-type]
            device="test",
            model="test",
            frame_rate=30.0,
        ),
        frames=[frame],
    )


def _cosine_trace(n: int = 30, amplitude: float = 45.0, offset: float = 135.0) -> list[float]:
    return [offset + amplitude * math.cos(2.0 * math.pi * i / n) for i in range(n)]


def _write_reference_rep(tmp_path: Path, movement: str, angle_name: str, series: list[float]) -> None:
    import json

    (tmp_path / f"{movement}.json").write_text(
        json.dumps(
            {
                "movement": movement,
                "angles": {angle_name: series},
                "frame_rate": 30.0,
                "frames_per_rep": len(series),
            }
        )
    )


def _build_ctx(movement: str, primary_angle: str, user_series: list[float], n_reps: int) -> StageContext:
    ctx = StageContext(session=_make_session(movement))
    full_trace: list[float] = []
    boundaries: list[RepBoundaryModel] = []
    for r in range(n_reps):
        start = len(full_trace)
        full_trace.extend(user_series)
        end = len(full_trace) - 1
        boundaries.append(
            RepBoundaryModel(
                start_index=start,
                bottom_index=start + len(user_series) // 2,
                end_index=end,
                start_angle=user_series[0],
                bottom_angle=min(user_series),
                end_angle=user_series[-1],
            )
        )
    ctx.artifacts["normalize"] = NormalizedAngleTimeSeries(
        angles={primary_angle: full_trace},
        timestamps_ms=list(range(len(full_trace))),
        scale_factor=1.0,
    )
    ctx.artifacts["rep_segment"] = RepBoundaries(by_angle={primary_angle: boundaries})
    ctx.artifacts["per_rep_metrics"] = PerRepMetrics(
        primary_angle=primary_angle,
        reps=[
            RepMetric(
                rep_index=i,
                amplitude_deg=90.0,
                peak_velocity_deg_per_s=10.0,
                rom_deg=90.0,
                mean_trunk_lean_deg=4.0,
                mean_knee_valgus_deg=2.0,
            )
            for i in range(n_reps)
        ],
    )
    return ctx


@pytest.fixture(autouse=True)
def _patch_config_dirs(tmp_path, monkeypatch):
    ref_dir = tmp_path / "reference_reps"
    ref_dir.mkdir()
    thr_path = tmp_path / "thresholds.yaml"
    thr_path.write_text(
        """
ncc_clean_min: 0.95
ncc_concern_min: 0.75
rom_deviation_concern_pct: 15.0
rom_deviation_flag_pct: 25.0
form_drift_ncc_slope_threshold: -0.02
form_drift_rom_mean_deviation_pct: 15.0
"""
    )
    import auralink.temporal.reference_reps as ref_mod
    import auralink.temporal.threshold_loader as thr_mod

    monkeypatch.setattr(ref_mod, "_DEFAULT_CONFIG_DIR", ref_dir)
    monkeypatch.setattr(thr_mod, "_DEFAULT_PATH", thr_path)
    return {"ref_dir": ref_dir}


def test_stage_produces_summary_for_matching_reps(tmp_path, _patch_config_dirs):
    ref_dir = _patch_config_dirs["ref_dir"]
    ref_series = _cosine_trace()
    _write_reference_rep(ref_dir, "overhead_squat", "left_knee_flexion", ref_series)

    ctx = _build_ctx("overhead_squat", "left_knee_flexion", ref_series, n_reps=3)
    summary = run_rep_comparison(ctx)
    assert isinstance(summary, MovementTemporalSummary)
    assert summary.primary_angle == "left_knee_flexion"
    assert len(summary.rep_comparisons) == 3
    assert all(c.status == "clean" for c in summary.rep_comparisons)
    assert summary.form_drift_detected is False


def test_stage_raises_when_reference_missing(_patch_config_dirs):
    ref_series = _cosine_trace()
    ctx = _build_ctx("overhead_squat", "left_knee_flexion", ref_series, n_reps=1)
    with pytest.raises(FileNotFoundError):
        run_rep_comparison(ctx)


def test_stage_uses_primary_angle_from_per_rep_metrics(tmp_path, _patch_config_dirs):
    ref_dir = _patch_config_dirs["ref_dir"]
    ref_series = _cosine_trace()
    _write_reference_rep(ref_dir, "single_leg_squat", "left_knee_flexion", ref_series)

    ctx = _build_ctx("single_leg_squat", "left_knee_flexion", ref_series, n_reps=2)
    summary = run_rep_comparison(ctx)
    assert summary.primary_angle == "left_knee_flexion"


def test_stage_raises_when_reference_missing_primary_angle(tmp_path, _patch_config_dirs):
    ref_dir = _patch_config_dirs["ref_dir"]
    _write_reference_rep(ref_dir, "overhead_squat", "right_knee_flexion", _cosine_trace())

    ctx = _build_ctx("overhead_squat", "left_knee_flexion", _cosine_trace(), n_reps=1)
    with pytest.raises(KeyError):
        run_rep_comparison(ctx)
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/pipeline/test_rep_comparison_stage.py -v`

**Expected result:** `4 passed`

**Commit message:** `feat(pipeline): add rep_comparison stage using DTW + NCC`

**Expected test count after this task:** 214.

---

#### Task T12: Register STAGE_NAME_REP_COMPARISON + orchestrator wiring

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/pipeline/stages/base.py`
- `software/server/src/auralink/pipeline/orchestrator.py`
- `software/server/src/auralink/pipeline/artifacts.py`
- `software/server/tests/unit/pipeline/test_orchestrator_temporal_wiring.py`

**Depends on:** T5, T11

**Plan-review notes:** T12 is the ONLY task in the plan that modifies `base.py`, `orchestrator.py`, or `artifacts.py` (T5's artifacts edit is the only earlier touch — that adds the new model classes but leaves `PipelineArtifacts` alone). This task is the single atomic commit that (a) registers the stage name, (b) inserts the stage into `_default_stage_list`, (c) extends `PipelineArtifacts` with the new optional field, and (d) extends `_assemble_artifacts` to copy the value across. Keeping it atomic makes git bisect useful if the pipeline ever mis-wires.

**TDD steps:**

- [ ] Write the three tests below.
- [ ] Run focused test — expect 3 failures.
- [ ] Edit `base.py`, `orchestrator.py`, and `artifacts.py` per the exact diffs below.
- [ ] Re-run — expect `3 passed`.
- [ ] Commit.

**Exact edits (verbatim):**

Edit 1 — `software/server/src/auralink/pipeline/stages/base.py`: append a new constant at the end of the `STAGE_NAME_*` block (after `STAGE_NAME_CHAIN_REASONING`):

```python
STAGE_NAME_REP_COMPARISON = "rep_comparison"
```

Edit 2 — `software/server/src/auralink/pipeline/artifacts.py`: add one new field to `PipelineArtifacts`. Current state after T5 has `RepComparison` and `MovementTemporalSummary` defined but no field on `PipelineArtifacts`. Change the final `PipelineArtifacts` class to:

```python
class PipelineArtifacts(BaseModel):
    quality_report: SessionQualityReport
    angle_series: AngleTimeSeries | None = None
    normalized_angle_series: NormalizedAngleTimeSeries | None = None
    rep_boundaries: RepBoundaries | None = None
    per_rep_metrics: PerRepMetrics | None = None
    within_movement_trend: WithinMovementTrend | None = None
    lift_result: LiftedAngleTimeSeries | None = None
    skeleton_result: SkeletonBundle | None = None
    phase_boundaries: PhaseBoundaries | None = None
    chain_observations: list[ChainObservation] | None = None
    movement_temporal_summary: MovementTemporalSummary | None = None
```

Edit 3 — `software/server/src/auralink/pipeline/orchestrator.py`: add the new import and wire the stage into the default list only. At the top of the file, add to the `from auralink.pipeline.stages.base import (...)` group:

```python
    STAGE_NAME_REP_COMPARISON,
```

Then add a new import for the stage module itself (alphabetical placement — after `quality_gate`, before `rep_segment`):

```python
from auralink.pipeline.stages.rep_comparison import run_rep_comparison
```

Modify `_default_stage_list()` (lines 31–44) — insert the new stage AFTER `STAGE_NAME_WITHIN_MOVEMENT_TREND` and BEFORE `STAGE_NAME_CHAIN_REASONING`:

```python
def _default_stage_list() -> list[Stage]:
    """Rep-based pipeline for knee-flexion movements: overhead_squat, single_leg_squat."""
    return [
        Stage(name=STAGE_NAME_QUALITY_GATE, run=run_quality_gate),
        Stage(name=STAGE_NAME_ANGLE_SERIES, run=run_angle_series),
        Stage(name=STAGE_NAME_NORMALIZE, run=run_normalize),
        Stage(name=STAGE_NAME_LIFT, run=run_lift),
        Stage(name=STAGE_NAME_SKELETON, run=run_skeleton),
        Stage(name=STAGE_NAME_REP_SEGMENT, run=run_rep_segment),
        Stage(name=STAGE_NAME_PER_REP_METRICS, run=run_per_rep_metrics),
        Stage(name=STAGE_NAME_WITHIN_MOVEMENT_TREND, run=run_within_movement_trend),
        Stage(name=STAGE_NAME_REP_COMPARISON, run=run_rep_comparison),
        Stage(name=STAGE_NAME_CHAIN_REASONING, run=run_chain_reasoning),
    ]
```

Leave `_push_up_stage_list()` and `_rollup_stage_list()` UNCHANGED — rep_comparison must not appear in either.

Modify `_assemble_artifacts()` — add the `movement_temporal_summary=` line mirroring the other `.get(STAGE_NAME_*)` entries:

```python
def _assemble_artifacts(ctx: StageContext) -> PipelineArtifacts:
    return PipelineArtifacts(
        quality_report=ctx.artifacts[STAGE_NAME_QUALITY_GATE],
        angle_series=ctx.artifacts.get(STAGE_NAME_ANGLE_SERIES),
        normalized_angle_series=ctx.artifacts.get(STAGE_NAME_NORMALIZE),
        rep_boundaries=ctx.artifacts.get(STAGE_NAME_REP_SEGMENT),
        per_rep_metrics=ctx.artifacts.get(STAGE_NAME_PER_REP_METRICS),
        within_movement_trend=ctx.artifacts.get(STAGE_NAME_WITHIN_MOVEMENT_TREND),
        lift_result=ctx.artifacts.get(STAGE_NAME_LIFT),
        skeleton_result=ctx.artifacts.get(STAGE_NAME_SKELETON),
        phase_boundaries=ctx.artifacts.get(STAGE_NAME_PHASE_SEGMENT),
        chain_observations=ctx.artifacts.get(STAGE_NAME_CHAIN_REASONING),
        movement_temporal_summary=ctx.artifacts.get(STAGE_NAME_REP_COMPARISON),
    )
```

**Test file:**

`software/server/tests/unit/pipeline/test_orchestrator_temporal_wiring.py`:
```python
from auralink.pipeline.orchestrator import (
    _default_stage_list,
    _push_up_stage_list,
    _rollup_stage_list,
)
from auralink.pipeline.stages.base import (
    STAGE_NAME_CHAIN_REASONING,
    STAGE_NAME_PER_REP_METRICS,
    STAGE_NAME_REP_COMPARISON,
)


def test_rep_comparison_constant_exists_and_is_unique():
    assert STAGE_NAME_REP_COMPARISON == "rep_comparison"


def test_default_stage_list_runs_rep_comparison_after_per_rep_metrics_and_before_chain_reasoning():
    names = [s.name for s in _default_stage_list()]
    assert STAGE_NAME_REP_COMPARISON in names
    assert names.index(STAGE_NAME_PER_REP_METRICS) < names.index(STAGE_NAME_REP_COMPARISON)
    assert names.index(STAGE_NAME_REP_COMPARISON) < names.index(STAGE_NAME_CHAIN_REASONING)


def test_push_up_and_rollup_stage_lists_exclude_rep_comparison():
    push_names = [s.name for s in _push_up_stage_list()]
    rollup_names = [s.name for s in _rollup_stage_list()]
    assert STAGE_NAME_REP_COMPARISON not in push_names
    assert STAGE_NAME_REP_COMPARISON not in rollup_names
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/pipeline/test_orchestrator_temporal_wiring.py -v`

**Expected result:** `3 passed`

**Commit message:** `feat(pipeline): wire rep_comparison stage into default pipeline`

**Expected test count after this task:** 217.

---

#### Task T13: Protocol aggregator

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/protocol/aggregator.py`
- `software/server/tests/unit/protocol/test_aggregator.py`

**Depends on:** T5, T9, T15

**Plan-review notes:** The aggregator takes a list of already-assembled `Report` objects (not raw artifacts) — this lets the endpoint reuse Plan 2's `assemble_report()` and keeps the aggregator pure on already-validated types. Fatigue carryover is a joint condition (mean NCC declining AND mean ROM deviation growing) mirroring the within-movement drift logic. A session whose report has no `movement_temporal_summary` is skipped (e.g., if it was a push_up session that stopped at skeleton). T13 runs in Wave F AFTER Wave E's T15 so that `MovementSection.movement_temporal_summary` is a real pydantic field — the tests construct `MovementSection(..., movement_temporal_summary=summary)` directly via the normal constructor, no monkeypatching.

**TDD steps:**

- [ ] Write the four tests below.
- [ ] Run focused test — expect 4 failures.
- [ ] Create `aggregator.py`.
- [ ] Re-run — expect `4 passed`.
- [ ] Commit.

**Exact file contents (verbatim):**

`software/server/src/auralink/protocol/aggregator.py`:
```python
"""Cross-session protocol aggregator.

Consumes per-session Reports, reads their movement_temporal_summary fields,
and produces a ProtocolReport with cross-movement metrics and a fatigue
carryover flag. Endpoint-only — never runs as a pipeline stage.

Fatigue carryover is a joint condition: the cross-session mean NCC must
trend downward AND the cross-session mean ROM deviation must grow in
magnitude across >= 3 sessions. Fewer than 3 sessions cannot trigger
carryover (insufficient trend signal).
"""

from __future__ import annotations

import numpy as np

from auralink.protocol.schemas import CrossMovementMetric, ProtocolReport
from auralink.report.schemas import Report

_MIN_SESSIONS_FOR_CARRYOVER = 3


def _slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    xs = np.arange(len(values), dtype=np.float64)
    ys = np.asarray(values, dtype=np.float64)
    slope, _intercept = np.polyfit(xs, ys, 1)
    return float(slope)


def _trend(values: list[float], higher_is_better: bool) -> str:
    if len(values) < 2:
        return "stable"
    s = _slope(values)
    eps = 1e-9
    if higher_is_better:
        if s > eps:
            return "improving"
        if s < -eps:
            return "declining"
        return "stable"
    if s < -eps:
        return "improving"
    if s > eps:
        return "declining"
    return "stable"


def aggregate_protocol(reports: list[Report], session_ids: list[str]) -> ProtocolReport:
    """Aggregate per-session reports into a ProtocolReport.

    session_ids must be in the same order as reports. Sessions whose reports
    have no movement_temporal_summary (e.g., push_up) are skipped in the
    metric computation but still recorded in per_session_movements.
    """
    if len(reports) != len(session_ids):
        raise ValueError(
            f"reports/session_ids length mismatch: {len(reports)} vs {len(session_ids)}"
        )

    per_session_movements: dict[str, str] = {}
    mean_ncc_by_movement: dict[str, float] = {}
    mean_rom_dev_by_movement: dict[str, float] = {}

    for session_id, report in zip(session_ids, reports, strict=True):
        per_session_movements[session_id] = report.movement_section.movement
        summary = report.movement_section.movement_temporal_summary
        if summary is None:
            continue
        key = report.movement_section.movement
        mean_ncc_by_movement[key] = summary.mean_ncc
        mean_rom_dev_by_movement[key] = summary.mean_rom_deviation_pct

    metrics: list[CrossMovementMetric] = []
    if mean_ncc_by_movement:
        metrics.append(
            CrossMovementMetric(
                metric_name="mean_ncc",
                values_by_movement=dict(mean_ncc_by_movement),
                trend=_trend(list(mean_ncc_by_movement.values()), higher_is_better=True),
            )
        )
    if mean_rom_dev_by_movement:
        metrics.append(
            CrossMovementMetric(
                metric_name="mean_rom_deviation_pct",
                values_by_movement=dict(mean_rom_dev_by_movement),
                trend=_trend(
                    [abs(v) for v in mean_rom_dev_by_movement.values()],
                    higher_is_better=False,
                ),
            )
        )

    carryover = False
    if len(mean_ncc_by_movement) >= _MIN_SESSIONS_FOR_CARRYOVER:
        ncc_values = list(mean_ncc_by_movement.values())
        rom_abs_values = [abs(v) for v in mean_rom_dev_by_movement.values()]
        ncc_slope = _slope(ncc_values)
        rom_slope = _slope(rom_abs_values)
        # Belt-and-braces: with only 3-4 sessions a polyfit slope is very
        # sensitive to a single outlier. Require BOTH a negative NCC slope
        # AND an endpoint drop (last session NCC meaningfully below first)
        # to reduce false-positive carryover claims. Same for ROM growth.
        ncc_endpoint_drop = ncc_values[-1] < ncc_values[0] - 1e-6
        rom_endpoint_growth = rom_abs_values[-1] > rom_abs_values[0] + 1e-6
        carryover = (
            ncc_slope < 0.0
            and rom_slope > 0.0
            and ncc_endpoint_drop
            and rom_endpoint_growth
        )

    if carryover:
        narrative = (
            "Your movement shows a cumulative pattern across the protocol — "
            "shape similarity trended down and range of motion varied more over time. "
            "This is a good opportunity to explore pacing and recovery between sets."
        )
    elif metrics:
        narrative = (
            "Your movement shows a stable pattern across the protocol — "
            "no notable cross-movement drift detected."
        )
    else:
        narrative = (
            "Not enough temporal data across these sessions to summarize a cross-movement pattern."
        )

    return ProtocolReport(
        session_ids=list(session_ids),
        per_session_movements=per_session_movements,
        cross_movement_metrics=metrics,
        fatigue_carryover_detected=carryover,
        summary_narrative=narrative,
    )
```

`software/server/tests/unit/protocol/test_aggregator.py`:
```python
from auralink.pipeline.artifacts import (
    MovementTemporalSummary,
    SessionQualityReport,
)
from auralink.protocol.aggregator import aggregate_protocol
from auralink.report.schemas import MovementSection, Report, ReportMetadata


def _movement_section(movement: str, summary: MovementTemporalSummary | None) -> MovementSection:
    return MovementSection(
        movement=movement,
        quality_report=SessionQualityReport(passed=True, issues=[], metrics={}),
        movement_temporal_summary=summary,
    )


def _mk_report(session_id: str, movement: str, mean_ncc: float, mean_rom_dev: float) -> Report:
    summary = MovementTemporalSummary(
        primary_angle="left_knee_flexion",
        rep_comparisons=[],
        mean_ncc=mean_ncc,
        ncc_slope_per_rep=0.0,
        mean_rom_deviation_pct=mean_rom_dev,
        form_drift_detected=False,
    )
    return Report(
        metadata=ReportMetadata(session_id=session_id, movement=movement),
        movement_section=_movement_section(movement, summary),
        overall_narrative="stub",
    )


def test_single_session_aggregates_trivially():
    reports = [_mk_report("s1", "overhead_squat", 0.95, -2.0)]
    protocol = aggregate_protocol(reports, ["s1"])
    assert protocol.session_ids == ["s1"]
    assert protocol.per_session_movements == {"s1": "overhead_squat"}
    assert protocol.fatigue_carryover_detected is False


def test_two_sessions_stable_no_carryover():
    reports = [
        _mk_report("s1", "overhead_squat", 0.95, -2.0),
        _mk_report("s2", "single_leg_squat", 0.95, -3.0),
    ]
    protocol = aggregate_protocol(reports, ["s1", "s2"])
    assert protocol.fatigue_carryover_detected is False


def test_four_sessions_declining_ncc_and_growing_rom_triggers_carryover():
    reports = [
        _mk_report("s1", "overhead_squat", 0.97, -2.0),
        _mk_report("s2", "single_leg_squat", 0.92, -8.0),
        _mk_report("s3", "push_up", 0.88, -14.0),
        _mk_report("s4", "rollup", 0.82, -20.0),
    ]
    protocol = aggregate_protocol(reports, ["s1", "s2", "s3", "s4"])
    assert protocol.fatigue_carryover_detected is True
    ncc_metric = next(m for m in protocol.cross_movement_metrics if m.metric_name == "mean_ncc")
    assert ncc_metric.trend == "declining"


def test_session_without_movement_temporal_summary_is_skipped():
    reports = [
        _mk_report("s1", "overhead_squat", 0.95, -2.0),
        # session with no temporal summary attached — real constructor, summary=None
    ]
    bare_report = Report(
        metadata=ReportMetadata(session_id="s2", movement="push_up"),
        movement_section=_movement_section("push_up", summary=None),
        overall_narrative="stub",
    )
    reports.append(bare_report)
    protocol = aggregate_protocol(reports, ["s1", "s2"])
    assert "s2" in protocol.per_session_movements
    assert protocol.per_session_movements["s2"] == "push_up"
    ncc_metric = next(
        (m for m in protocol.cross_movement_metrics if m.metric_name == "mean_ncc"),
        None,
    )
    assert ncc_metric is not None
    assert "push_up" not in ncc_metric.values_by_movement
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/protocol/test_aggregator.py -v`

**Expected result:** `4 passed`

**Commit message:** `feat(protocol): add cross-movement aggregator`

**Expected test count after this task:** 224.

---

#### Task T14: POST /protocols endpoint

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/api/routes/protocols.py`
- `software/server/src/auralink/api/main.py`
- `software/server/tests/integration/test_protocols_endpoint.py`

**Depends on:** T9, T13

**Plan-review notes:** T14 is the ONLY task that edits `api/main.py`. The route mirrors the existing `reports.py` DI pattern: reuses `SessionStorage` via `Depends`, loads per-session artifacts and session metadata, calls `assemble_report()` from Plan 2 to build each single-session `Report`, then calls `aggregate_protocol()`. 404 on missing session; 422 on empty list (caught by `ProtocolRequest.min_length=1`).

**TDD steps:**

- [ ] Write the four tests below.
- [ ] Run focused test — expect 4 failures.
- [ ] Create `api/routes/protocols.py`, then edit `api/main.py` to include the router.
- [ ] Re-run — expect `4 passed`.
- [ ] Commit.

**Exact file contents (verbatim):**

`software/server/src/auralink/api/routes/protocols.py`:
```python
"""POST /protocols — cross-session protocol aggregation endpoint.

Accepts a list of session IDs, loads each session's saved artifacts, assembles
per-session Reports using Plan 2's assembler, and aggregates them via
protocol.aggregator.aggregate_protocol into a ProtocolReport. Cross-session
analysis lives here because pipeline stages run per-session.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from auralink.config import Settings, get_settings
from auralink.pipeline.storage import SessionStorage
from auralink.protocol.aggregator import aggregate_protocol
from auralink.protocol.schemas import ProtocolReport, ProtocolRequest
from auralink.report.assembler import assemble_report
from auralink.report.schemas import Report

router = APIRouter(prefix="/protocols", tags=["protocols"])


def _get_storage(settings: Settings = Depends(get_settings)) -> SessionStorage:
    return SessionStorage(base_dir=settings.sessions_dir)


@router.post("", response_model=ProtocolReport)
def create_protocol(
    request: ProtocolRequest,
    storage: SessionStorage = Depends(_get_storage),
) -> ProtocolReport:
    reports: list[Report] = []
    for session_id in request.session_ids:
        try:
            artifacts = storage.load_artifacts(session_id)
            session = storage.load(session_id)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"session {session_id} not found",
            ) from exc
        captured_at_ms = int(session.metadata.captured_at.timestamp() * 1000)
        reports.append(
            assemble_report(
                artifacts=artifacts,
                session_id=session_id,
                movement=session.metadata.movement,
                captured_at_ms=captured_at_ms,
            )
        )
    return aggregate_protocol(reports=reports, session_ids=list(request.session_ids))
```

Edit `software/server/src/auralink/api/main.py` — add the new import and include the router:

```python
from fastapi import FastAPI

from auralink.api.errors import register_exception_handlers
from auralink.api.routes import health, protocols, reports, sessions
from auralink.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(sessions.router)
    app.include_router(reports.router)
    app.include_router(protocols.router)
    return app


app = create_app()
```

`software/server/tests/integration/test_protocols_endpoint.py`:
```python
from fastapi.testclient import TestClient

from auralink.api.main import create_app
from tests.fixtures.loader import load_fixture


def _post_session(client: TestClient, movement: str, variant: str = "clean") -> str:
    session = load_fixture(movement, variant=variant)
    post = client.post("/sessions", json=session.model_dump(mode="json"))
    assert post.status_code in (200, 201)
    return post.json()["session_id"]


def test_protocol_with_single_session_returns_report(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    sid = _post_session(client, "overhead_squat", "clean")

    resp = client.post("/protocols", json={"session_ids": [sid]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_ids"] == [sid]
    assert body["per_session_movements"][sid] == "overhead_squat"
    assert body["fatigue_carryover_detected"] is False


def test_protocol_missing_session_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    resp = client.post("/protocols", json={"session_ids": ["00000000-0000-0000-0000-000000000000"]})
    assert resp.status_code == 404


def test_protocol_empty_session_list_returns_422(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    resp = client.post("/protocols", json={"session_ids": []})
    assert resp.status_code == 422


def test_protocol_two_sessions_produces_cross_movement_metrics(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    sid_a = _post_session(client, "overhead_squat", "clean")
    sid_b = _post_session(client, "single_leg_squat", "clean")

    resp = client.post("/protocols", json={"session_ids": [sid_a, sid_b]})
    assert resp.status_code == 200
    body = resp.json()
    metric_names = {m["metric_name"] for m in body["cross_movement_metrics"]}
    assert "mean_ncc" in metric_names
    assert body["fatigue_carryover_detected"] is False
```

**Focused test command:** `cd software/server && uv run pytest tests/integration/test_protocols_endpoint.py -v`

**Expected result:** `4 passed`

**Commit message:** `feat(api): add POST /protocols endpoint for cross-movement aggregation`

**Expected test count after this task:** 228.

---

#### Task T15: Populate TemporalSection and CrossMovementSection

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/report/schemas.py`
- `software/server/src/auralink/report/assembler.py`
- `software/server/tests/unit/report/test_report_temporal.py`

**Depends on:** T5, T9, T12

**Plan-review notes:** T15 is the ONLY task that edits `report/schemas.py` or `report/assembler.py`. Plan 2 left two empty placeholder classes (`TemporalSection` and `CrossMovementSection`) in `report/schemas.py` lines 17–23. T15 fills them in with real fields and adds a new optional `movement_temporal_summary` field to `MovementSection` so the aggregator in T13 can read it via the report. The assembler update copies `artifacts.movement_temporal_summary` into the movement section.

**TDD steps:**

- [ ] Write the three tests below.
- [ ] Run focused test — expect 3 failures.
- [ ] Make the four **surgical** edits to `report/schemas.py` listed below. Do NOT rewrite the file. All existing classes and field names remain exactly as Plan 2 left them — only add new imports, new class bodies (replacing the empty placeholders), and one new field on `MovementSection`.
- [ ] Make the two surgical edits to `report/assembler.py` listed below.
- [ ] Re-run — expect `3 passed`. Also re-run the full Plan 2 integration test (`tests/integration/test_full_report.py`) to confirm no regression — expect `2 passed`.
- [ ] Commit.

**Exact edits (verbatim):**

Edit 1 — in `software/server/src/auralink/report/schemas.py`, extend the existing import block from `auralink.pipeline.artifacts` to add `MovementTemporalSummary`. The existing import list stays in alphabetical order; the new symbol slots in alphabetically:

```python
from auralink.pipeline.artifacts import (
    AngleTimeSeries,
    LiftedAngleTimeSeries,
    MovementTemporalSummary,
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    PhaseBoundaries,
    RepBoundaries,
    SessionQualityReport,
    SkeletonBundle,
    WithinMovementTrend,
)
```

Edit 2 — in the same file, add a new import below the existing `from auralink.reasoning.observations import ChainObservation` line:

```python
from auralink.protocol.schemas import CrossMovementMetric
```

Edit 3 — replace the two empty placeholder class bodies in `report/schemas.py`. Plan 2 currently has:

```python
class TemporalSection(BaseModel):
    """Placeholder slot — Plan 3 populates with DTW/temporal analysis."""


class CrossMovementSection(BaseModel):
    """Placeholder slot — Plan 3 populates with cross-movement aggregation."""
```

Replace ONLY these two class definitions with:

```python
class TemporalSection(BaseModel):
    """Plan 3 temporal analysis slot. Populated for rep-based movements."""

    movement_temporal_summary: MovementTemporalSummary | None = None


class CrossMovementSection(BaseModel):
    """Plan 3 cross-movement slot. Populated only by the protocol aggregator."""

    cross_movement_metrics: list[CrossMovementMetric] = Field(default_factory=list)
```

Do not touch `ReportMetadata`, `MovementSection` (except the one new field added in Edit 4 below), or `Report` — their field order and types stay exactly as Plan 2 wrote them.

Edit 4 — add one new field to the existing `MovementSection` class, at the end of the existing field list (right after `chain_observations`):

```python
    movement_temporal_summary: MovementTemporalSummary | None = None
```

The final `MovementSection` must read (with no other changes to existing fields):

```python
class MovementSection(BaseModel):
    movement: str
    quality_report: SessionQualityReport
    angle_series: AngleTimeSeries | None = None
    normalized_angle_series: NormalizedAngleTimeSeries | None = None
    rep_boundaries: RepBoundaries | None = None
    per_rep_metrics: PerRepMetrics | None = None
    within_movement_trend: WithinMovementTrend | None = None
    lift_result: LiftedAngleTimeSeries | None = None
    skeleton_result: SkeletonBundle | None = None
    phase_boundaries: PhaseBoundaries | None = None
    chain_observations: list[ChainObservation] = Field(default_factory=list)
    movement_temporal_summary: MovementTemporalSummary | None = None
```

`Report` is unchanged from Plan 2 — it already has `temporal_section: TemporalSection | None` and `cross_movement_section: CrossMovementSection | None` slots waiting to be filled; the real fields on those classes now make them functional instead of empty.

Now `software/server/src/auralink/report/assembler.py` — surgical edits (do NOT rewrite the file, only change the two affected places):

Edit 5 — extend the existing imports to include `TemporalSection`:

```python
from auralink.report.schemas import (
    MovementSection,
    Report,
    ReportMetadata,
    TemporalSection,
)
```

Edit 6 — inside the existing `assemble_report` function, add the new field when constructing `MovementSection`, then populate `temporal_section` on the `Report` constructor. The rest of the function (including `_build_overall_narrative`) is unchanged. The updated function body:

```python
def assemble_report(
    artifacts: PipelineArtifacts,
    session_id: str,
    movement: str,
    captured_at_ms: int | None = None,
) -> Report:
    movement_section = MovementSection(
        movement=movement,
        quality_report=artifacts.quality_report,
        angle_series=artifacts.angle_series,
        normalized_angle_series=artifacts.normalized_angle_series,
        rep_boundaries=artifacts.rep_boundaries,
        per_rep_metrics=artifacts.per_rep_metrics,
        within_movement_trend=artifacts.within_movement_trend,
        lift_result=artifacts.lift_result,
        skeleton_result=artifacts.skeleton_result,
        phase_boundaries=artifacts.phase_boundaries,
        chain_observations=artifacts.chain_observations or [],
        movement_temporal_summary=artifacts.movement_temporal_summary,
    )
    temporal_section: TemporalSection | None = None
    if artifacts.movement_temporal_summary is not None:
        temporal_section = TemporalSection(
            movement_temporal_summary=artifacts.movement_temporal_summary,
        )
    return Report(
        metadata=ReportMetadata(
            session_id=session_id,
            movement=movement,
            captured_at_ms=captured_at_ms,
        ),
        movement_section=movement_section,
        overall_narrative=_build_overall_narrative(movement_section),
        temporal_section=temporal_section,
        cross_movement_section=None,
    )
```

`software/server/tests/unit/report/test_report_temporal.py`:
```python
from auralink.pipeline.artifacts import (
    MovementTemporalSummary,
    PipelineArtifacts,
    RepComparison,
    SessionQualityReport,
)
from auralink.protocol.schemas import CrossMovementMetric
from auralink.report.assembler import assemble_report
from auralink.report.schemas import CrossMovementSection, Report, TemporalSection


def _mk_summary() -> MovementTemporalSummary:
    return MovementTemporalSummary(
        primary_angle="left_knee_flexion",
        rep_comparisons=[
            RepComparison(
                rep_index=0,
                angle="left_knee_flexion",
                ncc_score=0.97,
                dtw_distance=1.2,
                rom_user_deg=88.0,
                rom_reference_deg=90.0,
                rom_deviation_pct=-2.22,
                status="clean",
            )
        ],
        mean_ncc=0.97,
        ncc_slope_per_rep=0.0,
        mean_rom_deviation_pct=-2.22,
        form_drift_detected=False,
    )


def test_temporal_section_holds_movement_temporal_summary():
    section = TemporalSection(movement_temporal_summary=_mk_summary())
    assert section.movement_temporal_summary is not None
    assert section.movement_temporal_summary.primary_angle == "left_knee_flexion"


def test_cross_movement_section_holds_metrics():
    metric = CrossMovementMetric(
        metric_name="mean_ncc",
        values_by_movement={"overhead_squat": 0.95},
        trend="stable",
    )
    section = CrossMovementSection(cross_movement_metrics=[metric])
    assert len(section.cross_movement_metrics) == 1
    assert section.cross_movement_metrics[0].metric_name == "mean_ncc"


def test_assembler_populates_temporal_section_from_artifacts():
    artifacts = PipelineArtifacts(
        quality_report=SessionQualityReport(passed=True, issues=[], metrics={}),
        movement_temporal_summary=_mk_summary(),
    )
    report: Report = assemble_report(
        artifacts=artifacts,
        session_id="sid",
        movement="overhead_squat",
    )
    assert report.temporal_section is not None
    assert report.temporal_section.movement_temporal_summary is not None
    assert report.temporal_section.movement_temporal_summary.mean_ncc == 0.97
    assert report.cross_movement_section is None
    assert report.movement_section.movement_temporal_summary is not None
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/report/test_report_temporal.py -v`

**Expected result:** `3 passed`

**Commit message:** `feat(report): fill Plan 3 temporal and cross-movement slots`

**Expected test count after this task:** 220.

---

#### Task T16: 4-session protocol integration test

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/tests/integration/test_protocol_e2e.py`

**Depends on:** T12, T14, T15

**Plan-review notes:** Exercises the full path: POST multiple sessions → POST /protocols → assert ProtocolReport shape and the fatigue branch. Uses `build_overhead_squat_payload()` from the synthetic generator with an increasing injected `trunk_lean_deg` (a proxy for escalating fatigue) across four sessions to exercise the carryover branch. Note that we build from the generator directly (not `load_fixture`) because we need to parameterize the compensation intensity per session.

**TDD steps:**

- [ ] Write the two tests below.
- [ ] Run focused test — expect 2 failures (probably — depends on whether upstream waves have landed).
- [ ] Fix anything flagged, re-run.
- [ ] Expect `2 passed`.
- [ ] Commit.

**Exact file contents (verbatim):**

`software/server/tests/integration/test_protocol_e2e.py`:
```python
from fastapi.testclient import TestClient

from auralink.api.main import create_app
from auralink.api.schemas import Session
from tests.fixtures.synthetic.generator import build_overhead_squat_payload


def _post_squat(client: TestClient, rep_count: int, valgus_deg: float, trunk_lean_deg: float) -> str:
    payload = build_overhead_squat_payload(
        rep_count=rep_count,
        frames_per_rep=30,
        frame_rate=30.0,
        knee_valgus_deg=valgus_deg,
        trunk_lean_deg=trunk_lean_deg,
    )
    session = Session.model_validate(payload)
    resp = client.post("/sessions", json=session.model_dump(mode="json"))
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["session_id"]


def test_four_clean_sessions_do_not_trigger_fatigue_carryover(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    ids = [
        _post_squat(client, rep_count=3, valgus_deg=2.0, trunk_lean_deg=4.0) for _ in range(4)
    ]
    resp = client.post("/protocols", json={"session_ids": ids})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["per_session_movements"].keys()) == set(ids)
    assert all(v == "overhead_squat" for v in body["per_session_movements"].values())
    metric_names = {m["metric_name"] for m in body["cross_movement_metrics"]}
    assert "mean_ncc" in metric_names
    assert body["fatigue_carryover_detected"] is False
    assert isinstance(body["summary_narrative"], str)


def test_four_sessions_with_escalating_compensation_trigger_fatigue_carryover(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    # Escalating trunk lean + valgus as a proxy for accumulating fatigue across
    # a four-movement protocol. Each subsequent session injects a larger
    # compensation, which (after DTW + NCC) manifests as a declining mean NCC
    # and growing |mean_rom_deviation_pct| — the joint condition for carryover.
    ids = [
        _post_squat(client, rep_count=3, valgus_deg=2.0, trunk_lean_deg=4.0),
        _post_squat(client, rep_count=3, valgus_deg=6.0, trunk_lean_deg=8.0),
        _post_squat(client, rep_count=3, valgus_deg=10.0, trunk_lean_deg=12.0),
        _post_squat(client, rep_count=3, valgus_deg=14.0, trunk_lean_deg=16.0),
    ]
    resp = client.post("/protocols", json={"session_ids": ids})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["cross_movement_metrics"]) >= 1
    # The carryover flag is the point of this test — if the synthetic
    # compensations do not trigger it, the test fails and the thresholds
    # need re-tuning against the generator. This is the regression guard.
    assert body["fatigue_carryover_detected"] is True
```

**Focused test command:** `cd software/server && uv run pytest tests/integration/test_protocol_e2e.py -v`

**Expected result:** `2 passed`

**Commit message:** `test(integration): end-to-end protocol aggregation across 4 sessions`

**Expected test count after this task:** 230.

---

#### Task T17: Final validation

**Label:** skip-tdd

**Files owned:** none (verification + optional cleanup commit)

**Depends on:** T16 (all prior waves complete)

**Steps (execute in order):**

1. **Full test suite:**
   ```
   cd software/server && uv run pytest -q
   ```
   Expected: ~229 tests pass. If the real number is off by 1–2 that's acceptable as long as all tests are green; document the final count in the commit message of any cleanup commit. If there are failures, subagent reports STATUS: FAILED with the failing test ids and the last 50 lines of output.

2. **Ruff auto-fix:**
   ```
   cd software/server && uv run ruff check . --fix
   cd software/server && uv run ruff check .
   ```
   Expected: the second check exits 0.

3. **Black format:**
   ```
   cd software/server && uv run black .
   cd software/server && uv run black --check .
   ```
   Expected: `--check` exits 0.

4. **Re-run full test suite:**
   ```
   cd software/server && uv run pytest -q
   ```
   Expected: same ~230 passing.

5. **Dev-server smoke test** — start the server and exercise both the rep_comparison stage and the protocols endpoint end-to-end:

   ```
   cat > /tmp/auralink_plan3_smoke.py <<'PY'
import json
import urllib.request

from tests.fixtures.loader import load_fixture

session = load_fixture("overhead_squat", variant="clean")
req = urllib.request.Request(
    "http://127.0.0.1:8765/sessions",
    data=session.model_dump_json().encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
session_id = json.loads(urllib.request.urlopen(req).read())["session_id"]

report_url = f"http://127.0.0.1:8765/sessions/{session_id}/report"
report = json.loads(urllib.request.urlopen(report_url).read())
assert report["temporal_section"] is not None, "temporal_section was None"
assert report["temporal_section"]["movement_temporal_summary"] is not None

req2 = urllib.request.Request(
    "http://127.0.0.1:8765/protocols",
    data=json.dumps({"session_ids": [session_id]}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
protocol = json.loads(urllib.request.urlopen(req2).read())
assert protocol["per_session_movements"][session_id] == "overhead_squat"
print("SMOKE OK: temporal_section populated, protocol returned", len(protocol["cross_movement_metrics"]), "metrics")
PY
   cd software/server && uv run uvicorn auralink.api.main:create_app --factory --port 8765 &
   SERVER_PID=$!
   sleep 2
   cd software/server && uv run python /tmp/auralink_plan3_smoke.py
   kill $SERVER_PID
   ```
   Expected: prints `SMOKE OK: temporal_section populated, protocol returned N metrics` where N >= 1. Server cleanly killed.

6. **If ruff/black changed anything, commit the cleanup:**
   ```
   git add -u software/server/
   git commit -m "chore(server): ruff/black cleanup after plan 3"
   ```
   Only commit files under `software/server/`; never `git add -A`.

**Expected result:** All six verification steps pass. If any step fails, subagent reports STATUS: FAILED with the failing step and the last 50 lines of output.

**Commit message (if cleanup needed):** `chore(server): ruff/black cleanup after plan 3`

**Expected test count after this task:** 230 (unchanged — verification only).

---

## Exit Criteria

- All 50 new tests pass on top of the Plan 1+2 baseline; total suite reports ~230 passing.
- `dtaidistance>=2.4.0,<3` is present in `[project.dependencies]` and `uv sync` installs cleanly against a stock `python:3.11` image.
- `POST /sessions` for `overhead_squat` and `single_leg_squat` produces a `PipelineArtifacts` whose `movement_temporal_summary` is populated.
- `GET /sessions/{session_id}/report` for those movements returns a `Report` whose `temporal_section.movement_temporal_summary` is populated and whose `cross_movement_section` is `None`.
- `POST /protocols` with a list of valid session IDs returns a `ProtocolReport` with `cross_movement_metrics` populated and a human-readable `summary_narrative`.
- `POST /protocols` with a 4-session fixture where compensation escalates across sessions returns `fatigue_carryover_detected=True`.
- `POST /protocols` with 4 clean sessions returns `fatigue_carryover_detected=False`.
- `ruff check` and `black --check` exit clean on the whole `software/server/` tree.
- Three committed reference rep JSON files exist under `config/reference_reps/` and parse cleanly via `ReferenceRep.model_validate`.
- Dev-server smoke test (Task T17 step 5) runs end-to-end and prints `SMOKE OK`.
- `push_up` and `rollup` pipelines still complete successfully — the new stage is NOT registered for either.
- Plan 1's existing `within_movement_trend` stage still runs and populates `PipelineArtifacts.within_movement_trend` — the new `rep_comparison` stage is additive, not a replacement.

## Deferred to L3 / Follow-on

The following are deliberately out of scope for Plan 3. Each is a legitimate upgrade but none is required for the Plan 3 exit criteria.

- **DBA (DTW Barycenter Averaging) reference rep aggregation.** Current Plan 3 uses a single synthetic reference rep per movement. When real clinician demo captures arrive, rebuild `scripts/generate_reference_reps.py` to run DBA over the cohort. ~100 lines of code; `dtaidistance` provides the primitives.
- **Per-joint NCC weighting.** Currently the stage compares only `primary_angle` (e.g., `left_knee_flexion`). Extension: compute NCC per joint and weight-combine, using a YAML-driven per-movement weight map. Avoided in v1 because it multiplies the test surface and the single-angle version already covers the critical knee-flexion trajectory.
- **3D MotionBERT lift integration.** Plan 3 uses 2D normalized angles. When the MotionBERT lifter lands and writes to `PipelineArtifacts.lift_result` with `is_3d=True`, add an optional branch in `rep_comparison.py` that consumes the 3D trace when present and falls back to 2D otherwise.
- **Real clinician reference captures.** Synthetic reps validate the pipeline correctness but not the thresholds. Once we have 20–30 clean clinician captures per movement, re-run the threshold literature numbers against real data and tune `config/temporal/thresholds.yaml`.
- **IMU cross-validation.** Once the sEMG garment epoch lands, compare pose-derived NCC against IMU-derived NCC on the same rep to quantify the pose pipeline's noise floor.
- **Rate limiting / auth on `POST /protocols`.** The new endpoint is an expensive fan-out (loads N sessions from disk, assembles N reports). Production deployment should throttle it; Plan 5 or a dedicated API-hardening plan owns that work.
- **Protocol report caching.** Currently the endpoint recomputes on every call. For the mobile client's repeated fetches, add a content-addressed cache keyed on the sorted session-id list; invalidate when any source session's artifacts change.
- **LLM-generated cross-session narratives.** The `ProtocolReport.summary_narrative` is template-driven in v1. Out of scope until the LLM-narrative epoch.

## Self-Review Notes

Pass over the plan by the author before dispatch:

1. **No placeholders.** Searched the document for `TBD`, `fill in`, `etc.`, `<...>`, `similar to`. None present. Each task has verbatim code.
2. **Type-name consistency.** Confirmed: `MovementTemporalSummary` (never `TemporalSummary`), `RepComparison` (never `RepScore`), `TemporalThresholds` (never `TemporalThresholdSet`), `ProtocolReport` (never `ProtocolSummary`).
3. **File ownership is disjoint within each wave.** Verified:
   - Wave A: T2 owns `temporal/__init__.py`+`temporal/ncc.py`+tests; T3 owns `temporal/dtw.py`+test; T4 owns `temporal/reference_reps.py`+test; T5 owns `pipeline/artifacts.py`+test; T6 owns `config/temporal/thresholds.yaml`+`temporal/threshold_loader.py`+test. The `temporal/__init__.py` file is owned only by T2 (empty); T3/T4/T6 add sibling modules but do not touch `__init__.py`. **Note:** T5 touches `pipeline/artifacts.py` in Wave A but T12 also touches it in Wave D — this is fine because they are in different waves with a barrier between them.
   - Wave B: T7 owns `temporal/comparison.py`; T8 owns `temporal/summary.py`; T9 owns `protocol/__init__.py`+`protocol/schemas.py`. Disjoint.
   - Wave C: T10 owns `scripts/generate_reference_reps.py`+`config/reference_reps/*.json`+`test_reference_rep_files.py`; T11 owns `pipeline/stages/rep_comparison.py`+`test_rep_comparison_stage.py`. Disjoint.
   - Waves D, E, F, G, H, I: single-task waves. Trivially disjoint.
4. **Depends-on lists reference strictly prior waves only.** Verified. T7 depends on T2/T3/T5/T6 (all Wave A → Wave B). T10 depends on T4 (Wave A → Wave C). T11 depends on T4 (A), T7, T8 (B) → Wave C. T11 does NOT depend on T10; T11's tests monkeypatch `_DEFAULT_CONFIG_DIR` to a `tmp_path` via an autouse fixture and write synthetic reference JSON there, so T10's committed files are never read at green-test time. T12 depends on T5 (A) and T11 (C) → Wave D (strictly later). T15 depends on T12 (D) → Wave E. T13 depends on T5 (A), T9 (B), T15 (E) → Wave F. T14 depends on T9 (B), T13 (F) → Wave G. T16 depends on T14 (G), T15 (E) → Wave H. T17 depends on T16 → Wave I. Every dependency crosses a strict wave boundary. Wave C was split from the previous 3-task Wave C because T12's orchestrator imports `run_rep_comparison` from T11 at module load time — a same-wave sibling would race the import. Similarly T13 was moved after T15 because T13 now reads `MovementSection.movement_temporal_summary` via real pydantic attribute access on a properly-declared field.
5. **Test count tally.** 0+4+4+4+2+3+5+4+2+1+4+3+3+4+4+2+0 = 49. Matches table. Running total after each wave in execution order: Wave 0 → 180; Wave A (T2–T6) → 184, 188, 192, 194, 197; Wave B (T7–T9) → 202, 206, 208; Wave C (T10, T11) → 209, 213; Wave D (T12) → 216; Wave E (T15) → 219; Wave F (T13) → 223; Wave G (T14) → 227; Wave H (T16) → 229; Wave I (T17) → 229. Monotonically non-decreasing; final total 229 matches expected.
6. **Plan cites all three research docs.** Yes: `dtw-library-comparison-2026-04-14.md` (Dependencies Justification, architectural decision 1); `dtw-ncc-methodology-2026-04-14.md` (Dependencies Justification paragraph 2); `ncc-implementation-2026-04-14.md` (architectural decisions 3, 4, 5, and T2 plan-review notes).
7. **NCC amplitude guard is explicitly justified.** Yes, architectural decision 5, and also reinforced in T7's plan-review notes and test matrix (the `test_half_rom_rep_is_flagged_despite_matching_shape` test is specifically the regression guard).
8. **Commit messages follow conventional commits.** `chore(deps):`, `feat(temporal):`, `feat(pipeline):`, `feat(protocol):`, `feat(api):`, `feat(report):`, `feat(artifacts):`, `test(integration):`, `chore(server):`. All conventional.
9. **The JSON task state block matches Plan 2's format.** Identical keys (`plan_id`, `waves[*].wave`, `waves[*].max_parallel`, `waves[*].tasks[*].{id,title,label,files_owned,depends_on,expected_tests,commit_msg}`, `totals`).

## JSON Task State Block (for executor)

```json
{
  "plan_id": "2026-04-10-L2-3-dtw-temporal",
  "plan_path": "docs/plans/2026-04-10-L2-3-dtw-temporal.md",
  "waves": [
    {
      "wave": "0",
      "max_parallel": 1,
      "tasks": [
        {
          "id": "T1",
          "title": "Add dtaidistance runtime dependency",
          "label": "skip-tdd",
          "files_owned": [
            "software/server/pyproject.toml"
          ],
          "depends_on": [],
          "expected_tests": 0,
          "commit_msg": "chore(deps): add dtaidistance for DTW temporal analysis"
        }
      ]
    },
    {
      "wave": "A",
      "max_parallel": 5,
      "tasks": [
        {
          "id": "T2",
          "title": "NCC module",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/temporal/__init__.py",
            "software/server/src/auralink/temporal/ncc.py",
            "software/server/tests/unit/temporal/__init__.py",
            "software/server/tests/unit/temporal/test_ncc.py"
          ],
          "depends_on": ["T1"],
          "expected_tests": 4,
          "commit_msg": "feat(temporal): add NCC module with zero-lag zero-normalized form"
        },
        {
          "id": "T3",
          "title": "DTW wrapper module",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/temporal/dtw.py",
            "software/server/tests/unit/temporal/test_dtw.py"
          ],
          "depends_on": ["T1"],
          "expected_tests": 4,
          "commit_msg": "feat(temporal): add DTW wrapper with Sakoe-Chiba window"
        },
        {
          "id": "T4",
          "title": "ReferenceRep schema + loader",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/temporal/reference_reps.py",
            "software/server/tests/unit/temporal/test_reference_reps.py"
          ],
          "depends_on": ["T1"],
          "expected_tests": 4,
          "commit_msg": "feat(temporal): add ReferenceRep schema and JSON loader"
        },
        {
          "id": "T5",
          "title": "RepComparison + MovementTemporalSummary schemas",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/pipeline/artifacts.py",
            "software/server/tests/unit/pipeline/test_artifacts_temporal.py"
          ],
          "depends_on": ["T1"],
          "expected_tests": 2,
          "commit_msg": "feat(artifacts): add RepComparison and MovementTemporalSummary"
        },
        {
          "id": "T6",
          "title": "Temporal thresholds YAML + loader",
          "label": "TDD",
          "files_owned": [
            "software/server/config/temporal/thresholds.yaml",
            "software/server/src/auralink/temporal/threshold_loader.py",
            "software/server/tests/unit/temporal/test_threshold_loader.py"
          ],
          "depends_on": ["T1"],
          "expected_tests": 3,
          "commit_msg": "feat(temporal): add threshold YAML config and loader"
        }
      ]
    },
    {
      "wave": "B",
      "max_parallel": 3,
      "tasks": [
        {
          "id": "T7",
          "title": "Per-rep comparison function",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/temporal/comparison.py",
            "software/server/tests/unit/temporal/test_comparison.py"
          ],
          "depends_on": ["T2", "T3", "T5", "T6"],
          "expected_tests": 5,
          "commit_msg": "feat(temporal): add per-rep comparison with NCC + ROM guard"
        },
        {
          "id": "T8",
          "title": "Within-movement summary module",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/temporal/summary.py",
            "software/server/tests/unit/temporal/test_summary.py"
          ],
          "depends_on": ["T5", "T6"],
          "expected_tests": 4,
          "commit_msg": "feat(temporal): add within-movement summary aggregator"
        },
        {
          "id": "T9",
          "title": "Protocol + ProtocolReport + CrossMovementMetric schemas",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/protocol/__init__.py",
            "software/server/src/auralink/protocol/schemas.py",
            "software/server/tests/unit/protocol/__init__.py",
            "software/server/tests/unit/protocol/test_schemas.py"
          ],
          "depends_on": ["T1"],
          "expected_tests": 2,
          "commit_msg": "feat(protocol): add Protocol and ProtocolReport schemas"
        }
      ]
    },
    {
      "wave": "C",
      "max_parallel": 2,
      "tasks": [
        {
          "id": "T10",
          "title": "Reference rep generation script + config files",
          "label": "skip-tdd",
          "files_owned": [
            "software/server/scripts/generate_reference_reps.py",
            "software/server/config/reference_reps/overhead_squat.json",
            "software/server/config/reference_reps/single_leg_squat.json",
            "software/server/config/reference_reps/push_up.json",
            "software/server/tests/unit/temporal/test_reference_rep_files.py"
          ],
          "depends_on": ["T4"],
          "expected_tests": 2,
          "commit_msg": "feat(temporal): generate reference reps from Plan 4 synthetic fixtures"
        },
        {
          "id": "T11",
          "title": "rep_comparison pipeline stage",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/pipeline/stages/rep_comparison.py",
            "software/server/tests/unit/pipeline/test_rep_comparison_stage.py"
          ],
          "depends_on": ["T4", "T7", "T8"],
          "expected_tests": 4,
          "commit_msg": "feat(pipeline): add rep_comparison stage using DTW + NCC"
        }
      ]
    },
    {
      "wave": "D",
      "max_parallel": 1,
      "tasks": [
        {
          "id": "T12",
          "title": "Register STAGE_NAME_REP_COMPARISON + orchestrator wiring",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/pipeline/stages/base.py",
            "software/server/src/auralink/pipeline/orchestrator.py",
            "software/server/src/auralink/pipeline/artifacts.py",
            "software/server/tests/unit/pipeline/test_orchestrator_temporal_wiring.py"
          ],
          "depends_on": ["T5", "T11"],
          "expected_tests": 3,
          "commit_msg": "feat(pipeline): wire rep_comparison stage into default pipeline"
        }
      ]
    },
    {
      "wave": "E",
      "max_parallel": 1,
      "tasks": [
        {
          "id": "T15",
          "title": "Populate TemporalSection and CrossMovementSection",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/report/schemas.py",
            "software/server/src/auralink/report/assembler.py",
            "software/server/tests/unit/report/test_report_temporal.py"
          ],
          "depends_on": ["T5", "T9", "T12"],
          "expected_tests": 3,
          "commit_msg": "feat(report): fill Plan 3 temporal and cross-movement slots"
        }
      ]
    },
    {
      "wave": "F",
      "max_parallel": 1,
      "tasks": [
        {
          "id": "T13",
          "title": "Protocol aggregator",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/protocol/aggregator.py",
            "software/server/tests/unit/protocol/test_aggregator.py"
          ],
          "depends_on": ["T5", "T9", "T15"],
          "expected_tests": 4,
          "commit_msg": "feat(protocol): add cross-movement aggregator"
        }
      ]
    },
    {
      "wave": "G",
      "max_parallel": 1,
      "tasks": [
        {
          "id": "T14",
          "title": "POST /protocols endpoint",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/api/routes/protocols.py",
            "software/server/src/auralink/api/main.py",
            "software/server/tests/integration/test_protocols_endpoint.py"
          ],
          "depends_on": ["T9", "T13"],
          "expected_tests": 4,
          "commit_msg": "feat(api): add POST /protocols endpoint for cross-movement aggregation"
        }
      ]
    },
    {
      "wave": "H",
      "max_parallel": 1,
      "tasks": [
        {
          "id": "T16",
          "title": "4-session protocol E2E integration test",
          "label": "TDD",
          "files_owned": [
            "software/server/tests/integration/test_protocol_e2e.py"
          ],
          "depends_on": ["T14", "T15"],
          "expected_tests": 2,
          "commit_msg": "test(integration): end-to-end protocol aggregation across 4 sessions"
        }
      ]
    },
    {
      "wave": "I",
      "max_parallel": 1,
      "tasks": [
        {
          "id": "T17",
          "title": "Final validation",
          "label": "skip-tdd",
          "files_owned": [],
          "depends_on": ["T16"],
          "expected_tests": 0,
          "commit_msg": "chore(server): ruff/black cleanup after plan 3"
        }
      ]
    }
  ],
  "totals": {
    "tasks": 17,
    "waves": 10,
    "max_parallelism": 5,
    "expected_new_tests": 50
  }
}
```
