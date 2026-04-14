# Progress — AuraLink L2 Plan 4 Execution (ML Interfaces + Fixture Harness)

## Session Directive
> **MANDATORY:** This progress file defines your assignment. Do NOT interpret, summarize, or re-scope.
> Resume work exactly where the previous session left off. Follow the What's Next section literally.
> If the plan or instructions are unclear, ask the user — do not guess or improvise.

## Application Context

AuraLink — UT Austin capstone. AI movement screening tool using phone camera pose estimation + fascial chain reasoning (SBL/BFL/FFL). Free tier = on-device MediaPipe basics, premium tier = server-side analysis with MotionBERT + HSMR/SKEL biomechanical skeleton. 5-person team, Flutter mobile app + Python FastAPI server + future sEMG compression garment.

**Current milestone:** Analysis Pipeline Epoch, **L2 Plan 4** (ML Interfaces + Fixture Harness) — mid-execution. Wave A (T1, T2, T4) and Wave B (T3, T5) complete — 5 of 17 dispatch units done. Plan 1 is FULLY COMPLETE (89/89 tests). Plan 4 execution resumes at **Wave C = T6 (Lifter stage)**.

## Position

- **Project:** Capstone (AuraLink)
- **Repo path:** `/home/context/olorin/projects/Capstone/` (symlink to `/home/context/projects/Capstone/`)
- **Remote:** `https://github.com/AaronCarney/capstone-fascia.git`
- **Branch:** `main`
- **HEAD:** `40152a4 feat(models): real ModelRegistry with ModelLoader-based registration`
- **Phase:** L2 Plan 4 execution — 5 of 17 tasks done, 12 remaining
- **Tests:** 104/104 passing (Plan 1 baseline 89 + P4 Wave A/B: +15)

## L1 Context

- **L1 plan:** `docs/plans/2026-04-10-analysis-pipeline-epoch.md`
- **Current epoch:** Analysis Pipeline (scaffold → end-to-end pipeline + ML hooks)
- **Epoch execution order:** 1 → 4 → 2 → 3 → 5 (Plan 1 ✓, Plan 4 running now, Plans 2/3/5 still stubs)
- **Prior plans complete:** Server scaffold (`docs/plans/2026-04-09-server-scaffold.md`), Plan 1 (`docs/plans/2026-04-10-L2-1-pipeline-framework.md`)

## L2 Context

- **L2 plan:** `docs/plans/2026-04-10-L2-4-ml-interfaces.md` (2424 lines, fully fleshed out + reviewed + patches applied)
- **Plan review status:** Both passes complete. Fixes landed at `0ef09ad`. Two architectural blockers addressed:
  1. Task 17 `git add -A` → explicit `git add -u software/server/`
  2. push_up registration split from `_default_stage_list()` into `_push_up_stage_list()` (stops at skeleton — elbow_flexion deferred)
- **Execution strategy:** `parallel-plan-executor` sequential-in-main-tree. One `task-executor` subagent per task. Per-cycle commits. No worktrees. Narrow file ownership per dispatch.

## Task State (JSON)

```json
{
  "plan_id": "L2-Plan-4",
  "plan_path": "docs/plans/2026-04-10-L2-4-ml-interfaces.md",
  "baseline_commit": "0ef09ad",
  "current_head": "40152a4",
  "test_count_baseline": 89,
  "test_count_current": 104,
  "tasks_done": [
    {"id": "P4-T1", "commit": "a0b0cc6", "description": "ModelLoader protocol + NoOpLoader (src/auralink/ml/loader.py, 3 tests)"},
    {"id": "P4-T2", "commit": "0a01f64", "description": "Lifter protocol + IdentityLifter + local LiftedAngleTimeSeries (src/auralink/ml/lifter.py, 2 tests)"},
    {"id": "P4-T4", "commit": "75c1b6d", "description": "PhaseSegmenter + SinglePhaseSegmenter + local Phase/PhaseBoundaries (src/auralink/ml/phase_segmenter.py, 3 tests)"},
    {"id": "P4-T3", "commit": "10c5c6d", "description": "SkeletonFitter + NoOpSkeletonFitter + local SkeletonBundle (src/auralink/ml/skeleton.py, 2 tests)"},
    {"id": "P4-T5", "commit": "40152a4", "description": "ModelRegistry refactor — real registration API with ModelLoader instances, REGISTRY singleton kept (src/auralink/models/registry.py, 5 tests)"}
  ],
  "tasks_remaining": [
    {"id": "P4-T6", "wave": "C", "description": "Lifter stage wrapping IdentityLifter + STAGE_NAME_LIFT constant in pipeline/stages/base.py. 3 tests.", "key_files": ["software/server/src/auralink/pipeline/stages/lift.py", "software/server/src/auralink/pipeline/stages/base.py", "software/server/tests/unit/pipeline/test_lift_stage.py"], "depends_on": ["T2"], "plan_line": 713},
    {"id": "P4-T7", "wave": "D", "description": "SkeletonFitter stage + STAGE_NAME_SKELETON constant. 3 tests.", "key_files": ["software/server/src/auralink/pipeline/stages/skeleton.py", "software/server/src/auralink/pipeline/stages/base.py", "software/server/tests/unit/pipeline/test_skeleton_stage.py"], "depends_on": ["T3", "T6 (base.py race)"], "plan_line": 823},
    {"id": "P4-T8", "wave": "E", "description": "PhaseSegment stage + STAGE_NAME_PHASE_SEGMENT constant. 3 tests.", "key_files": ["software/server/src/auralink/pipeline/stages/phase_segment.py", "software/server/src/auralink/pipeline/stages/base.py", "software/server/tests/unit/pipeline/test_phase_segment_stage.py"], "depends_on": ["T4", "T7 (base.py race)"], "plan_line": 929},
    {"id": "P4-T9", "wave": "F", "description": "ORCHESTRATOR EXTENSION SEAM — four atomic edits: (a) re-home LiftedAngleTimeSeries/SkeletonBundle/Phase/PhaseBoundaries to artifacts.py, extend PipelineArtifacts with lift_result/skeleton_result/phase_boundaries; (b) replace ml/*.py bodies with re-exports from artifacts.py; (c) rewrite orchestrator.py to add _push_up_stage_list (stops at skeleton) + _rollup_stage_list (phase-based) + register push_up/rollup + extend _assemble_artifacts; (d) add 4 new orchestrator tests. 1 atomic commit touching 6 files.", "key_files": ["software/server/src/auralink/pipeline/artifacts.py", "software/server/src/auralink/ml/lifter.py", "software/server/src/auralink/ml/skeleton.py", "software/server/src/auralink/ml/phase_segmenter.py", "software/server/src/auralink/pipeline/orchestrator.py", "software/server/tests/unit/pipeline/test_orchestrator.py"], "depends_on": ["T6", "T7", "T8"], "plan_line": 1027},
    {"id": "P4-T10", "wave": "G", "description": "Shared synthetic generator migration. Create tests/fixtures/synthetic/generator.py with generate_session() + generate_reference_rep(). DELETE tests/fixtures/synthetic_overhead_squat.py + update 5 callers in same commit: test_session_pipeline.py, test_sessions_endpoint.py, test_report_endpoint.py, test_error_handling.py, test_e2e_overhead_squat.py. 7 generator tests.", "key_files": ["software/server/tests/fixtures/synthetic/__init__.py", "software/server/tests/fixtures/synthetic/generator.py", "software/server/tests/fixtures/synthetic_overhead_squat.py (DELETE)", "5 integration test files (import update)", "software/server/tests/unit/fixtures/test_synthetic_generator.py"], "depends_on": ["T9"], "plan_line": 1351},
    {"id": "P4-T11", "wave": "H", "description": "overhead_squat_clean.json + overhead_squat_valgus.json static fixture files + scripts/regenerate_fixtures.py + test_fixture_files_exist.py.", "key_files": ["software/server/tests/fixtures/synthetic/overhead_squat_clean.json", "software/server/tests/fixtures/synthetic/overhead_squat_valgus.json", "scripts/regenerate_fixtures.py", "software/server/tests/unit/fixtures/test_fixture_files_exist.py"], "depends_on": ["T10"], "plan_line": 1706},
    {"id": "P4-T12", "wave": "I", "description": "Generate 3 more fixture JSON files (single_leg_squat_clean, push_up_clean, rollup_clean). Extend test_fixture_files_exist.py.", "key_files": ["software/server/tests/fixtures/synthetic/single_leg_squat_clean.json", "software/server/tests/fixtures/synthetic/push_up_clean.json", "software/server/tests/fixtures/synthetic/rollup_clean.json"], "depends_on": ["T11"], "plan_line": 1832},
    {"id": "P4-T13", "wave": "I", "description": "Fixture loader helper — tests/fixtures/loader.py with load_fixture(movement, variant). 3 tests.", "key_files": ["software/server/tests/fixtures/loader.py", "software/server/tests/unit/fixtures/test_loader.py"], "depends_on": ["T11"], "plan_line": 1897},
    {"id": "P4-T14", "wave": "J", "description": "overhead_squat clean e2e integration test using load_fixture.", "key_files": ["software/server/tests/integration/test_overhead_squat_e2e_fixture.py"], "depends_on": ["T12", "T13"], "plan_line": 1981},
    {"id": "P4-T15", "wave": "J", "description": "single_leg_squat + push_up e2e integration tests. **push_up assertions were strengthened during plan-review**: asserts body['per_rep_metrics'] is None, body['rep_boundaries'] is None, body['within_movement_trend'] is None because push_up uses _push_up_stage_list that stops at skeleton.", "key_files": ["software/server/tests/integration/test_single_leg_squat_e2e.py", "software/server/tests/integration/test_push_up_e2e.py"], "depends_on": ["T12", "T13"], "plan_line": 2039},
    {"id": "P4-T16", "wave": "J", "description": "rollup stub e2e integration test — asserts phase_boundaries present (1 phase, label 'full_movement'), lift_result and skeleton_result populated, rep-based artifacts None.", "key_files": ["software/server/tests/integration/test_rollup_e2e.py"], "depends_on": ["T12", "T13"], "plan_line": 2122},
    {"id": "P4-T17", "wave": "K", "description": "Final validation — full pytest + ruff + black + dev server smoke test (rollup path + push_up path via curl). Step 5 cleanup commit uses 'git add -u software/server/' (NOT 'git add -A').", "key_files": [], "depends_on": ["T14-T16"], "plan_line": 2181}
  ]
}
```

## What's Next

**Resume point:** Dispatch **P4 T6 (Lifter stage)** as the first action of Wave C. The plan text for T6 is at line 713 of `docs/plans/2026-04-10-L2-4-ml-interfaces.md`. Use the dispatch template from `parallel-plan-executor` with task-executor body inlined, narrow file ownership, verbatim code blocks from the plan file.

### Step 1: Dispatch P4 T6 (Lifter stage)

Read lines 713–822 of `docs/plans/2026-04-10-L2-4-ml-interfaces.md` to get the verbatim test + implementation content. File ownership:
- `software/server/src/auralink/pipeline/stages/lift.py` (CREATE)
- `software/server/src/auralink/pipeline/stages/base.py` (MODIFY — add `STAGE_NAME_LIFT = "lift"`)
- `software/server/tests/unit/pipeline/test_lift_stage.py` (CREATE)

Commit message: `feat(pipeline): add lift stage wrapping IdentityLifter`.

Expected: 104 + 3 = 107 tests passing.

### Step 2–12: Continue the Wave C → K sequence

Waves (already analyzed in the plan's Dependency Graph section, lines 2333+):
- **Wave C:** T6 (lift stage) — 1 commit
- **Wave D:** T7 (skeleton stage) — 1 commit
- **Wave E:** T8 (phase_segment stage) — 1 commit
- **Wave F:** T9 (orchestrator + artifact seam) — **1 atomic commit touching 6 files**. This is the highest-risk task; it re-homes schemas from ml/*.py into artifacts.py and wires the new stages into the orchestrator. Don't split.
- **Wave G:** T10 (generator migration) — 1 atomic commit with `git rm synthetic_overhead_squat.py` + 5 caller updates
- **Wave H:** T11 (overhead_squat fixture files) — 1 commit
- **Wave I:** T12 (remaining fixture files) — 1 commit; T13 (loader) — 1 commit; dispatch sequentially
- **Wave J:** T14 (overhead_squat e2e); T15 (SLS + push_up e2e); T16 (rollup e2e); dispatch sequentially — 3 commits
- **Wave K:** T17 (final validation) — 0 or 1 commit

Expected total Plan 4 commits after resume: 12 (or 13 if T15 splits SLS/push_up into separate commits).

### Step 13: Exit Plan 4

After T17 passes, invoke `finishing-a-development-branch` to decide on merge/PR/handoff. **Per the no-push constraint, default to keep-as-is.** Then proceed to Plan 2 per the epoch execution order 1 → 4 → 2 → 3 → 5.

## Key Files

**Plan docs:**
- `/home/context/olorin/projects/Capstone/docs/plans/2026-04-10-analysis-pipeline-epoch.md` — L1 epoch
- `/home/context/olorin/projects/Capstone/docs/plans/2026-04-10-L2-1-pipeline-framework.md` — Plan 1 (complete)
- `/home/context/olorin/projects/Capstone/docs/plans/2026-04-10-L2-4-ml-interfaces.md` — Plan 4 (executing, 2424 lines)
- `/home/context/olorin/projects/Capstone/docs/plans/2026-04-10-L2-2-chain-reasoning.md` — stub (next after Plan 4)
- `/home/context/olorin/projects/Capstone/docs/plans/2026-04-10-L2-3-dtw-temporal.md` — stub
- `/home/context/olorin/projects/Capstone/docs/plans/2026-04-10-L2-5-operations.md` — stub

**Scaffold code Plan 4 references:**
- `software/server/src/auralink/pipeline/artifacts.py` — existing artifact schemas; T9 will extend with lift_result/skeleton_result/phase_boundaries
- `software/server/src/auralink/pipeline/stages/base.py` — has 6 STAGE_NAME_* constants from Plan 1; T6/T7/T8 add 3 more
- `software/server/src/auralink/pipeline/orchestrator.py` — T9 rewrites extensively (adds _push_up_stage_list, _rollup_stage_list, registers push_up/rollup)
- `software/server/src/auralink/pipeline/stages/rep_segment.py` — has hardcoded `PRIMARY_REP_ANGLES_BY_MOVEMENT` dict covering only overhead_squat and single_leg_squat. **This is WHY push_up uses its own stage list that stops at skeleton** — elbow_flexion support is deferred to a follow-on epoch.
- `software/server/src/auralink/api/schemas.py` — `MovementType = Literal["overhead_squat", "single_leg_squat", "push_up", "rollup"]`
- `software/server/tests/fixtures/synthetic_overhead_squat.py` — Plan 1 T14a artifact; Plan 4 T10 DELETES this and replaces with `tests/fixtures/synthetic/generator.py`

**Completed Plan 4 artifacts (do NOT re-create):**
- `software/server/src/auralink/ml/__init__.py` (empty)
- `software/server/src/auralink/ml/loader.py` (ModelLoader + NoOpLoader)
- `software/server/src/auralink/ml/lifter.py` (Lifter + IdentityLifter + local LiftedAngleTimeSeries — T9 will re-home schema)
- `software/server/src/auralink/ml/skeleton.py` (SkeletonFitter + NoOpSkeletonFitter + local SkeletonBundle — T9 will re-home)
- `software/server/src/auralink/ml/phase_segmenter.py` (PhaseSegmenter + SinglePhaseSegmenter + local Phase/PhaseBoundaries — T9 will re-home)
- `software/server/src/auralink/models/registry.py` (refactored ModelRegistry — Protocol-based)
- `software/server/tests/unit/ml/__init__.py` (empty)
- `software/server/tests/unit/ml/test_loader.py`, `test_lifter.py`, `test_skeleton.py`, `test_phase_segmenter.py`
- `software/server/tests/unit/test_model_registry.py`

## Git State

```bash
$ cd /home/context/olorin/projects/Capstone && git log --oneline -7
40152a4 feat(models): real ModelRegistry with ModelLoader-based registration
10c5c6d feat(ml): add SkeletonFitter protocol and NoOpSkeletonFitter
75c1b6d feat(ml): add PhaseSegmenter protocol and SinglePhaseSegmenter
0a01f64 feat(ml): add Lifter protocol and IdentityLifter
a0b0cc6 feat(ml): add ModelLoader protocol and NoOpLoader
0ef09ad docs(plans): apply plan-review fixes to L2 Plan 4
b2881e5 docs(plans): flesh out L2 Plan 4 (ML interfaces + fixture harness) from stub
```

Working tree clean on scope. Only pre-existing untracked team files in `docs/research/`, `hardware/`, `docs/BRAINLIFT.pdf`, `README.md` modifications etc. — **NOT in scope, must NOT touch**. Concurrent research session may be writing additional files in `docs/research/` during Plan 4 execution — those are also out of scope.

**Remote:** `main` pushed to `AaronCarney/capstone-fascia` through commit `537b911` (scaffold). All commits on top (plan docs + Plan 1 + Plan 4 in progress) are **local-only**. Do not push without explicit user instruction.

## Constraints / Blockers

- **TDD enforcement non-negotiable.** Every Plan 4 task via `parallel-plan-executor` + inlined `task-executor` Path A (or skip-tdd for T11/T12/T17 per plan labels).
- **No worktrees for subagents.** Sequential in main tree.
- **DO NOT touch pre-existing untracked files** in `docs/research/`, `hardware/`, etc. These are team files from other workstreams.
- **Commit summaries at `docs/sessions/summaries/` are gitignored** — subagents can write them but should NOT stage them.
- **Plan 4 push_up architectural decision (carried from plan-review):** push_up uses `_push_up_stage_list()` that stops at skeleton. The rep-based stages (rep_segment, per_rep_metrics, within_movement_trend) require elbow_flexion angles which are deferred. Do NOT revert this when executing T9 or T15.
- **Plan 4's T9 is the highest-risk task.** It atomically edits 6 files. If the re-export pattern (ml/*.py re-exporting from artifacts.py) doesn't work cleanly, STATUS: CHECKPOINT and escalate.
- **Capstone wellness-positioning constraint** applies to Plan 2 (narrative), NOT Plan 4. Plan 4 ships no user-facing text.
- **No real ML model integration this epoch** — everything is Protocol + no-op/identity impls.
- **Ignore Vercel plugin auto-suggestions** — this is a self-hosted FastAPI Python server, not a Vercel deployment. Plugin hooks will inject noise; all references to Vercel docs should be dismissed.

## Environment

- WSL2 Ubuntu; git user: Aaron Carney <aaron.l.carney@gmail.com>
- Python server: `cd software/server && uv run pytest -q` (104 tests passing baseline after P4 T5)
- Server lint: `cd software/server && uv run ruff check . && uv run black --check .`
- Dev server smoke: `cd software/server && ./scripts/dev.sh` then `curl localhost:8000/health`
- Agent dispatch: `parallel-plan-executor` skill + `task-executor` body at `/home/context/olorin/.claude/skills/task-executor/SKILL.md`
- Session resumes via `.claude/hooks/session-start.sh` injection or manual `/resume` / `/catchup` in a fresh terminal.
