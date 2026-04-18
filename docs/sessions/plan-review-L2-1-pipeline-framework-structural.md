# Plan Review — L2-1 Pipeline Framework (Structural)

**Status:** current
**Created:** 2026-04-14
**Updated:** 2026-04-14
**Owner:** AaronCarney

**Plan:** `docs/plans/2026-04-10-L2-1-pipeline-framework.md`
**Parent epoch:** `docs/plans/2026-04-10-analysis-pipeline-epoch.md`
**Review type:** plan-checker (structural, 8 dimensions)
**Date:** 2026-04-10

## Summary

The plan is well-structured, TDD-per-cycle, and nearly all key links are wired. 15 tasks cover all epoch exit criteria scoped to Plan 1. The 14a/11/…/14b reshuffle is documented in three places consistently (§Task 11 note, §Execution notes, §Task 14 header). Artifact schema is populated by stages and consumed in the e2e test. No cycles, no scope violations. A handful of minor gaps listed below — none are true blockers, but two warnings deserve fixing before execution.

## Findings

- **[WARNING] [Dim 4: Key Links]** `test_error_handling.py` missing `StageError → 500` coverage
  - Task(s): 13
  - Description: Task 3 defines `StageError`, Task 10b raises it, and Task 13 wires a handler for it, but `test_error_handling.py` only asserts the `QualityGateError → 422` path. The `StageError → 500` and generic `PipelineError → 500` branches have handlers with no integration test, so the wiring is unverified at the HTTP layer.
  - Fix: Add one test to `test_error_handling.py` that injects a stage into a test-only registry which raises `RuntimeError` (wrapped to `StageError`), runs it through a `TestClient.post("/sessions")`, and asserts `500` + `{"error": "stage_failed", "stage": ...}`. One extra test, ~15 lines.

- **[WARNING] [Dim 2: Task Completeness / Dim 8: Nyquist]** Task 14a has no verify command
  - Task(s): 14 phase 14a
  - Description: Phase 14a has three steps (create `__init__`, implement fixture helper, commit) with no observable verify step. The plan justifies this ("no tests of its own — validated by downstream integration tests"), but that defers verification to Task 11, which means a broken fixture helper surfaces as an opaque Task 11 integration-test failure.
  - Fix: Add a Step 2.5 "sanity check" verify: `cd software/server && uv run python -c "from tests.fixtures.synthetic_overhead_squat import build_overhead_squat_payload; p=build_overhead_squat_payload(); assert len(p['frames'])==60; assert p['metadata']['movement']=='overhead_squat'"`. Takes 2 seconds, catches import/shape errors immediately.

- **[INFO] [Dim 3: Dependency Correctness]** The execution order 1..10, 14a, 11, 12, 13, 14b, 15 is stated in three places (Task 11 mid-cycle note, Task 14 header, Execution notes §bottom). All three agree — no contradictions found. Consistency verified.

- **[INFO] [Dim 4: Key Links]** `PipelineArtifacts` population audit (verified clean)
  - `quality_report` ← Task 4 (quality_gate stage) → consumed by Task 10b `_assemble_artifacts` + Task 12 report endpoint
  - `angle_series` ← Task 5 → consumed by Task 6 normalize + Task 10b + Task 12
  - `normalized_angle_series` ← Task 6 → consumed by Task 7 rep_segment + Task 8 per_rep_metrics + Task 10b
  - `rep_boundaries` ← Task 7 → consumed by Task 8 + Task 10b
  - `per_rep_metrics` ← Task 8 → consumed by Task 9 + Task 10b
  - `within_movement_trend` ← Task 9 → consumed by Task 10b + Task 12
  - Every field is populated by some stage and read by `_assemble_artifacts`. E2E test (14b) asserts against each one. Clean.

- **[INFO] [Dim 4: Key Links]** `StageRegistry` / `QualityGateError` / fixture helper wiring (verified clean)
  - `StageRegistry` (10a) → used by `run_pipeline` (10b), `DEFAULT_REGISTRY` is `StageRegistry()`.
  - `QualityGateError` (Task 3) → raised in Task 10b orchestrator → handled in Task 13 api/errors.py → asserted in Task 13 test.
  - Fixture helper `build_overhead_squat_payload` (14a) → imported by Tasks 11, 12, 13, 14b integration tests. All four import sites present.

- **[INFO] [Dim 1: Requirement Coverage]** Plan 1 scope vs epoch L1 (verified)
  - Epoch "end-to-end structured report via two API calls" → Tasks 11+12+14b
  - Epoch "Quality gates reject bad sessions" → Task 4 (4 cycles) + Task 13 (HTTP mapping)
  - Epoch "pure-function stages + protocol boundaries" → Tasks 1, 2, 3, 10
  - Epoch "Movement-type dispatch via strategy" → Task 10a registry
  - Epoch "Artifacts are pydantic models" → Task 2
  - Epoch "synthetic fixtures cover overhead_squat" → Task 14a (scoped; Plan 4 absorbs)
  - Chain reasoning, DTW, ML protocols, ops correctly deferred to Plans 2/3/4/5.
  - Plan 1's own exit criteria (35-45 tests, E2E round-trip, 422 on bad session, ?sync=true accepted, save_artifacts, ruff/black, dev smoke) all map to Task 15 + prior tasks.

- **[INFO] [Dim 5: Scope Sanity]** Task count / size check
  - 15 tasks total. Multi-cycle tasks (4×4, 5×2, 10×2, 11×2, 14×2 phases) all have clear red→green boundaries. No single task bundles 5+ disjoint things. Tasks 1, 3, 15 are the smallest — all justified (foundational abstractions / final validation gate).

- **[INFO] [Dim 6: Verification Derivation]** All exit criteria have verify commands
  - Tests: `uv run pytest -v` (Task 15 step 1) + per-cycle `uv run pytest <file> -v`
  - Lint: `uv run ruff check . && uv run black --check .` (Task 15 step 2)
  - Dev smoke: curl health + POST /sessions (Task 15 step 3)
  - 422 behavior: `test_error_handling.py::test_quality_gate_rejection_returns_422`
  - `?sync=true` no-op: `test_session_pipeline.py::test_sync_flag_is_accepted_as_noop`
  - E2E round-trip: `test_e2e_overhead_squat.py`

- **[INFO] [Dim 7: Context Compliance]** All constraints honored
  - Wellness positioning: N/A to Plan 1 (no user-facing narrative text — artifacts are structured fields). Confirmed moot.
  - Chain scope SBL/BFL/FFL: no chain reasoning in Plan 1 — deferred to Plan 2. Confirmed.
  - No new runtime deps: imports are `numpy`, `pydantic`, `fastapi`, `pytest` only. Confirmed.
  - TDD throughout: every task opens with "Step 1: write failing test", "Step 2: verify it fails", "Step 3: implement". Confirmed.
  - Sequential-in-main-tree execution: stated twice (§Execution notes, §plan header). Confirmed.
  - Per-cycle commits: `feedback_tdd_commit_cadence.md` honored — Task 4 has 4 commits, Task 5 has 2, Task 10/11 have 2, Task 14 has 2 phases. Confirmed.

- **[INFO] [Dim 8: Nyquist Compliance]** Verify commands are specific
  - Every non-14a task has `uv run pytest tests/<path> -v` with explicit file path. Task 10b runs `tests/unit/pipeline -v` to confirm no regression across the whole pipeline suite. Task 15 runs the full suite. No "manual check" commands. Only gap is 14a (see warning above).

## Cross-consistency checks

- Execution order mentioned in 3 locations — all say `1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14a, 11, 12, 13, 14b, 15`. Consistent.
- `PipelineArtifacts` schema in §Artifact Schemas table matches field list in Task 2 implementation and field access in Tasks 10b `_assemble_artifacts`, 11 storage, 12 report endpoint, 14b e2e assertions. Consistent.
- `DEFAULT_REGISTRY` name used in Task 10b test + implementation + orchestrator module docs. Consistent.
- Fixture helper file path `tests/fixtures/synthetic_overhead_squat.py` matches across §File Structure, Task 11, 12, 13, 14a, 14b. Consistent.
- Scaffold compatibility: `SessionStorage(base_dir=...)`, `Settings.sessions_dir`, `get_settings()` all exist in scaffold as the plan assumes. Confirmed against actual files.

## Status

`STATUS: APPROVED — 0 blockers, 2 warnings, 7 info`

The 2 warnings are small hygiene improvements (add StageError HTTP test, add 14a sanity check). Plan is ready to execute; warnings can be fixed either pre-execution via a 5-minute plan edit or deferred to Task 15's final validation commit.
