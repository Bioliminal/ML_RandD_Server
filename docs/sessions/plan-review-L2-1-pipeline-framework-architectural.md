# L2-1 Pipeline Framework — Architectural Review

**Plan:** `docs/plans/2026-04-10-L2-1-pipeline-framework.md`
**Reviewer focus:** Abstractions, interface contracts, ordering, integration seams, test feasibility.
**Scope:** Judgment only. Structural correctness handled separately.

## Summary

The plan is well-structured and internally consistent. `Stage(name, run)` + `StageContext` is correctly sized for this scope, `PipelineArtifacts` field flow is coherent across Tasks 2/10/11/12, and the `StageRegistry.register_movement()` contract matches the Plan 4 seam. Verified claims against scaffold: `segment_reps` will detect exactly 3 reps from the synthetic cosine fixture (events `(0,max),(15,min),(30,max),(45,min),(60,max),(75,min),(89,max)` → 3 valid triples at 90° amplitude ≥ 30°); the orchestrator's degenerate all-`(0.5,0.5)` test passes through every stage via documented fallbacks (`_FALLBACK_SCALE=1e-6 > 0`, empty reps OK, `RepBoundaries(by_angle={})` is non-None). No blocking issues found — a handful of medium-severity tightenings below.

---

## Issues

### Dimension 1 — Abstraction Quality

**Dimension 1 — `StageContext.artifacts` is an untyped `dict[str, Any]`**
- Where: Task 1 (`stages/base.py`), consumed in Tasks 6 (`normalize`), 7 (`rep_segment`), 8 (`per_rep_metrics`), 9 (`within_movement_trend`).
- What: Stages read prior outputs as `ctx.artifacts["normalize"]` with a local type annotation (`normalized: NormalizedAngleTimeSeries = ...`). The key name is a stringly-typed coupling to whatever the orchestrator happened to register. There is no enforced invariant that `"normalize"` resolves to `NormalizedAngleTimeSeries`.
- Why it matters: Plan 4 adds stages to the registry; if a future registration names its output stage differently, Plan 1 stages break silently at runtime with a `KeyError` inside the stage function (surfacing as a `StageError` with an opaque message). Also brittle for tests that bypass the orchestrator and hand-build context.
- Recommendation: Not blocking at Plan 1 scope, but document the canonical stage-name → artifact-type map as a module-level constant in `stages/base.py` (or a docstring table on `StageContext`). Plan 4 should be required to use those same keys. At minimum add a note in the plan stating that the six stage names `quality_gate`, `angle_series`, `normalize`, `rep_segment`, `per_rep_metrics`, `within_movement_trend` are part of the public contract consumed by downstream stages.

**Dimension 1 — `PipelineArtifacts` key remapping (`normalize` → `normalized_angle_series`, `rep_segment` → `rep_boundaries`) is an unstated convention**
- Where: Task 10 `_assemble_artifacts` (lines 1849-1857 of the plan).
- What: Stage names in `ctx.artifacts` (`normalize`, `rep_segment`) diverge from the `PipelineArtifacts` field names (`normalized_angle_series`, `rep_boundaries`). The mapping only exists as a six-line hardcoded assembly function.
- Why it matters: When Plan 4 adds new stages to the registry, it must either (a) rely on Plan 1's `_assemble_artifacts` ignoring unknown artifacts, or (b) replace `_assemble_artifacts`. Plan 1 doesn't specify which. If `_assemble_artifacts` remains hardcoded, Plan 4's new stages' outputs will silently drop from `PipelineArtifacts`.
- Recommendation: Either rename stage keys to match field names (simplest), or add one sentence to Task 10 stating that `_assemble_artifacts` only extracts Plan 1's known fields and Plan 2 will extend `PipelineArtifacts` (via model inheritance or new fields) plus update `_assemble_artifacts`. Plan 4 explicitly needs guidance here since it's ordered to run before Plan 2.

### Dimension 2 — Interface Contracts

**Dimension 2 — `Stage` is a frozen `@dataclass`, but Task 10 passes `lambda` into `Stage.run` in tests**
- Where: Task 10 Cycle 10b test `test_run_pipeline_wraps_unexpected_stage_failure_as_stage_error` and `test_run_pipeline_unknown_movement_raises_pipeline_error`.
- What: `Stage(name="quality_gate", run=lambda c: _pass())` — a frozen dataclass with a `Callable` field will hash on the callable. `lambda` objects are hashable but identity-based; this is fine functionally. More relevant: the tests construct `Stage` objects whose `name="quality_gate"` but whose `run` is a lambda returning a freshly-constructed passing `SessionQualityReport`. The orchestrator special-cases `stage.name == "quality_gate"` for branching, and `_assemble_artifacts` reads `ctx.artifacts["quality_gate"]` — consistent. No bug, but note that the orchestrator's quality-gate behavior is keyed on the stage **name string**, not on a `QualityGateStage` subtype. A future typo ("quality-gate" vs "quality_gate") silently disables the gate.
- Why it matters: Fragile coupling between orchestrator and registry. Plan 4 adding a new movement could accidentally register a different quality-gate name and bypass the rejection path — the session would pass through with an unvalidated report.
- Recommendation: Extract the stage-name constant to `stages/base.py` or `stages/quality_gate.py` as `QUALITY_GATE_STAGE_NAME = "quality_gate"` and import it in both the orchestrator and any registry builder. The plan already defines `_STAGE_NAME_QUALITY_GATE` as a private constant in `orchestrator.py` — promote it to a shared module so Plan 4 is forced to use the same symbol.

**Dimension 2 — `save_artifacts` signature is consistent, but path convention is load-bearing and undocumented in the plan header**
- Where: Task 11a storage extension, Task 11b integration test asserting `tmp_path / "sessions" / f"{session_id}.artifacts.json"`.
- What: `SessionStorage.__init__` takes `base_dir` and persists sessions at `base_dir / f"{session_id}.json"`. The new `_artifacts_path_for` uses `self.base_dir / f"{session_id}.artifacts.json"`. But the integration test asserts `tmp_path / "sessions" / f"{session_id}.artifacts.json"` — implying `settings.sessions_dir` resolves to `tmp_path / "sessions"` given `AURALINK_DATA_DIR=tmp_path`.
- Why it matters: The test silently depends on `get_settings()` constructing `sessions_dir` as `<AURALINK_DATA_DIR>/sessions`. If that convention already exists in `config.py` it's fine; if not, this test fails with a missing-file assertion. The plan does not state this invariant.
- Recommendation: Add one line to Task 11 Cycle 11b Step 1 confirming `settings.sessions_dir == Path(AURALINK_DATA_DIR) / "sessions"`, or change the assertion to navigate via `storage.base_dir` rather than hardcoding the `/sessions` subdirectory.

### Dimension 3 — Dependency Ordering

**Dimension 3 — Task 14a (fixture helper) splitting is correct but the plan documents the reshuffling inline in Task 11 body instead of Task 14's body**
- Where: Task 11 Step 1 note (lines ~2014-2016) + Task 14 phase split.
- What: The reshuffled execution order (`1..10, 14a, 11, 12, 13, 14b, 15`) is called out inside Task 11 Cycle 11b Step 1 as a "note to the executor." The note says "pause Task 11 and run Task 14a first," which is non-obvious guidance for a linear executor.
- Why it matters: `parallel-plan-executor` executes tasks in the listed order. If the executor reads tasks sequentially, it will encounter Task 11's failing test import (`from tests.fixtures.synthetic_overhead_squat import ...`) before Task 14a runs, and the red-phase verification step will fail with `ModuleNotFoundError` rather than the intended "POST handler does not run the pipeline yet" failure. The plan acknowledges this at execution note line 2549 but the task is still listed as Task 11 before Task 14 in document order.
- Recommendation: Not blocking — the execution note at the end is explicit. But recommend either (a) renumbering Task 14a to Task 10.5 and moving it to that physical position in the document, or (b) inlining a minimal two-frame payload directly in Task 11's test (then Task 14a can be folded back into Task 14 as a single late task). Option (b) is cleaner because it removes the executor's need to remember the reshuffle.

### Dimension 4 — Integration Risk at Task Boundaries

**Dimension 4 — Task 13 → Task 14b exception-handler gap**
- Where: Task 13 (exception handlers) and Task 14b (e2e happy path).
- What: Task 14b only exercises the success path (POST synthetic squat → GET report). If Task 13 omits one of the three handlers (`QualityGateError`, `StageError`, `PipelineError`), Task 14b will not catch the regression because no error is raised. Task 13's own test (`test_quality_gate_rejection_returns_422`) only tests `QualityGateError` — `StageError` and generic `PipelineError` handlers are covered by no test at all.
- Why it matters: A regression where the `StageError` handler is accidentally deleted would ship silently. Plan 2 and Plan 3 will add new stages that can raise `StageError`; losing the handler now turns their 500 responses into unhandled-exception leaks.
- Recommendation: Add two more integration tests to Task 13 — one forcing a `StageError` (inject a broken stage via a test-only registry override, similar to Task 10's `_boom` test but through the HTTP layer) and one for the base `PipelineError` path (unknown movement type, e.g., register no stages and POST). This is one additional TDD cycle inside Task 13.

**Dimension 4 — Plan 1 → Plan 4 seam: `register_movement()` contract is clear, but the "post-init extension API" claim requires import-order discipline**
- Where: Plan 1 Task 10 defines `DEFAULT_REGISTRY` at module import time; Plan 4 Task 9 (per parent spec) will call `DEFAULT_REGISTRY.register_movement("push_up", ...)` + `"rollup"`.
- What: Because `DEFAULT_REGISTRY` is a module-level singleton mutated in place, Plan 4's extension code must run once at process startup before any request hits the orchestrator. If Plan 4 puts the registration in a module that is only imported conditionally (e.g., lazy import inside a route), the `push_up` movement will raise `PipelineError("no stages registered for movement 'push_up'")` despite Plan 4 having landed.
- Why it matters: Latent bug across the Plan 1 → Plan 4 seam. The test suite would catch it only if Plan 4's tests explicitly post a push-up session through the full `create_app()`.
- Recommendation: Add one sentence to Task 10 Cycle 10a stating the intended extension pattern: "Plan 4 should perform its `register_movement()` calls in a module that is imported from `api/main.py` at app construction time (e.g., a new `pipeline/extensions.py` imported from `create_app`)." This preempts the fragile-import footgun.

**Dimension 4 — Plan 1 → Plan 5 seam: `?sync=true` no-op is sufficient**
- Where: Task 11 Cycle 11b handler signature `sync: bool = Query(default=True)` and `_ = sync`.
- What: FastAPI parses `?sync=true` into the `sync` kwarg. The `_ = sync` line is a no-op. Plan 5's migration test will POST `?sync=true` expecting the current behavior (synchronous, returns finished artifacts) and POST without the flag expecting async. Because Plan 1 already accepts the flag, Plan 5's migration test will see identical responses during Plan 1 (both sync) and divergent responses after Plan 5's flip — exactly the semantics Plan 5 needs.
- Why it matters: Verified the seam is sufficient.
- Recommendation: None — but note that `sync: bool = Query(default=True)` with default `True` means Plan 5 must change the default to `False`, not just the behavior. Add a one-line reminder in the plan: "Plan 5 will change `default=True` to `default=False` and branch on `sync`." Non-blocking.

### Dimension 5 — Test Strategy Feasibility

**Dimension 5 — Task 14b synthetic fixture will detect exactly 3 reps (verified)**
- Where: Task 14b assertion `len(by_angle["left_knee_flexion"]) == 3`.
- What: I traced the cosine signal `knee_flex = 135 + 45*cos(2πi/30)` across 3 reps × 30 frames = 90 frames. Local maxima at indices 0, 30, 60, 89 (endpoint, val≈179); local minima at 15, 45, 75. Sorted events yield triples (0,15,30), (30,45,60), (60,75,89) — 3 valid reps at amplitude 90° ≥ `min_amplitude=30`. **Claim holds.** The phase reset across reps is not a discontinuity because `cos(2π)=cos(0)=1`, so the signal is smooth at rep boundaries. However, the test depends on `_frame_for_knee_angle` actually producing the requested `knee_flexion_deg` through `knee_flexion_angle()` — this is not self-evidently true from the trigonometry in the fixture helper (which uses `angle_from_down_rad = π - knee_flex_rad` and places the ankle at `knee + r*(sin, cos)` from the knee).
- Why it matters: If `knee_flexion_angle(frame)` returns something other than the requested value, the detected reps may still exist but at different amplitudes, potentially failing `min_amplitude >= 30`. I could not verify this without running the code.
- Recommendation: Task 14a (fixture helper) should add a **self-test** before Task 14b: a two-line assertion that for `knee_flexion_deg=90`, the reconstructed frame round-trips through `knee_flexion_angle(frame, "left")` to approximately 90° (±2°). This catches the fixture-math-wrong-ness class of failure at the fixture boundary rather than deep inside the e2e test, which is hard to diagnose. Five lines of code, saves a debugging rathole.

**Dimension 5 — Task 4 quality-gate incremental test pattern is safe**
- Where: Cycles 4a → 4d each add a new check and new tests without modifying earlier ones.
- What: Verified by walking the test file mental model. Cycle 4a's `test_accepts_normal_frame_rate` uses `visibility=1.0, presence=1.0, frame_rate=30, frames=30` → 1.0s duration. **`duration_s = 30/30 = 1.0` which equals `MIN_DURATION_S = 1.0`.** The duration check in Cycle 4c uses `duration_s < MIN_DURATION_S` (strict less-than), so 1.0 still passes. Same for Cycle 4b's `test_accepts_good_visibility` (30 frames, 1.0s duration, exact boundary).
- Why it matters: Edge case — if someone changes `<` to `<=` in Cycle 4c's duration check, the Cycle 4a/4b "accepts" tests would start failing. Fragile but not wrong.
- Recommendation: Strengthen Cycle 4a/4b's `test_accepts_*` frame counts to 40 frames (1.33s) to put them safely above the duration threshold. Five-character fix per test. Non-blocking.

**Dimension 5 — Task 10 orchestrator happy-path test passes with degenerate `(0.5, 0.5)` landmarks (verified)**
- Where: `test_run_pipeline_produces_pipeline_artifacts_for_good_session`.
- What: Traced through all six stages with all landmarks at `(0.5, 0.5)`. Quality gate: frame_rate=30 ✓, avg_visibility=1.0 ✓, duration=60/30=2.0s ✓, missing_landmarks=0 ✓ → passes. Angle series: all `angle_between_points` calls hit `ba_norm == 0` fallback → 0.0 degrees for every angle. Normalization: `_hip_shoulder_distance` = 0 for every frame → `np.median([0]*60) = 0 ≤ 0` → `scale = _FALLBACK_SCALE = 1e-6 > 0` ✓ (pydantic `gt=0` satisfied). Rep segmentation: flat 0.0 signal → `segment_reps` returns `[]` → `by_angle = {"left_knee_flexion": [], "right_knee_flexion": []}` → `RepBoundaries(by_angle={...})` **non-None object** ✓. Per-rep metrics: empty reps → `PerRepMetrics(primary_angle="left_knee_flexion", reps=[])` ✓. Within-movement trend: empty → all slopes 0, `fatigue_detected=False` → valid model ✓. `_assemble_artifacts`: all `.get()` calls return non-None pydantic models. **All assertions hold.**
- Why it matters: Verified — this is a rare case where a degenerate input happens to exercise every fallback correctly.
- Recommendation: None. Consider adding a one-line comment to the test explaining *why* it works with degenerate input ("exercises every stage's zero-input fallback path without requiring realistic pose data"). Optional.

**Dimension 5 — All `uv run pytest` paths are valid post-scaffold**
- Where: Every task's test command.
- What: Verified against current tree: `software/server` has `pyproject.toml` with `uv`-style deps, `tests/unit/`, `tests/integration/` exist (scaffold baseline 31 tests). New directories `tests/unit/pipeline/`, `tests/unit/pose/`, `tests/fixtures/` are created with `__init__.py`. Import path `from tests.fixtures.synthetic_overhead_squat import ...` requires `tests/__init__.py` or `conftest.py` that adds `tests` to the import path. **The plan assumes `tests/__init__.py` exists; if the scaffold only has `conftest.py`, this import will fail.**
- Why it matters: Common FastAPI/pytest gotcha. If `tests/` is not a package, `from tests.fixtures...` fails with `ModuleNotFoundError`.
- Recommendation: Task 14a Step 1 should also ensure `software/server/tests/__init__.py` exists (or verify the scaffold's `conftest.py` path-injects appropriately). Add a one-line check: `ls software/server/tests/__init__.py || touch software/server/tests/__init__.py`. This is a one-minute pre-flight but avoids a hard-to-diagnose red phase.

---

## Non-blocking recommendations

- Promote `_STAGE_NAME_QUALITY_GATE` from a private orchestrator constant to a shared symbol in `stages/quality_gate.py` so Plan 4 cannot accidentally name-collide.
- Add two integration tests for `StageError` and `PipelineError` exception handlers in Task 13 (one TDD cycle each).
- Document the canonical stage-name → artifact-type map in `stages/base.py` so Plan 4 has an authoritative reference.
- Add a fixture round-trip self-assertion at Task 14a (verify `_frame_for_knee_angle(knee_flexion_deg=90)` yields ≈90° through `knee_flexion_angle`).
- Ensure `software/server/tests/__init__.py` exists before Task 14a commits.
- Add a pre-flight note in Task 11 Cycle 11b about `settings.sessions_dir` path convention.
- Tighten Cycle 4a/4b "accepts" tests to 40 frames to move away from the duration-threshold boundary.
- Widen Task 14a fixture helper ordering — move physically next to Task 10, or inline a minimal payload in Task 11 to remove the reshuffle footgun.

---

## Status

**Approved**

No blocking architectural issues. The plan is coherent, the abstractions fit the scope, interface contracts trace cleanly from Task 2 through Task 12, the Plan 1 → Plan 4 / Plan 5 seams are sufficient (with one clarification recommended for Plan 4 import ordering), and the two tests I traced in detail (`test_run_pipeline_produces_pipeline_artifacts_for_good_session` and Task 14b's 3-rep assertion) will pass as written. The non-blocking recommendations listed above should be picked up during `task-executor` execution where cheap (especially the `tests/__init__.py` check and the fixture self-assertion) and deferred where they would bloat the plan.
