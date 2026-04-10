# L2 Plan 4 — ML Integration Interfaces + Fixture Harness (Stub)

**Status:** Stub — flesh out with `writing-plans` before execution.
**Parent:** `2026-04-10-analysis-pipeline-epoch.md`
**Depends on:** Plan 1 (pipeline framework)

## Goal

Define the protocols and stage interfaces that MotionBERT, HSMR/SKEL, and the GCN chain reasoner will plug into once those models are ready. Ship no-op / identity implementations so the pipeline runs end-to-end with no ML. Add a fixture harness: synthetic fixture generator for all four movements, a loader that reads golden captures from the Flutter team, and end-to-end integration tests per movement type.

The test: landing MotionBERT later should change ~30 lines of config + one concrete class, zero structural changes.

## File Tree Delta

```
software/server/src/auralink/
├── ml/
│   ├── __init__.py             # NEW
│   ├── loader.py               # NEW — ModelLoader protocol + NoOpLoader
│   ├── lifter.py               # NEW — Lifter protocol + IdentityLifter (2D passthrough)
│   ├── skeleton.py             # NEW — SkeletonFitter protocol + NoOpSkeletonFitter
│   └── phase_segmenter.py      # NEW — PhaseSegmenter protocol + SinglePhaseSegmenter stub
├── pipeline/stages/
│   ├── lift.py                 # NEW — Lifter stage (2D → 3D; identity for now)
│   ├── skeleton.py             # NEW — SkeletonFitter stage (3D → SKEL; no-op for now)
│   └── phase_segment.py        # NEW — alternative to rep_segment for continuous movements
├── pipeline/orchestrator.py    # MODIFIED — movement-type dispatch: rep-based vs phase-based
└── models/registry.py          # MODIFIED — real registration API for future models

tests/
├── unit/ml/                    # NEW — protocol + stub tests
├── fixtures/synthetic/
│   ├── __init__.py             # NEW
│   ├── generator.py            # NEW — synthetic rep generator with injectable compensations
│   ├── overhead_squat_clean.json     # NEW — generated baseline
│   ├── overhead_squat_valgus.json    # NEW — generated with injected 12° valgus
│   ├── single_leg_squat_clean.json   # NEW
│   ├── push_up_clean.json            # NEW
│   └── rollup_clean.json             # NEW — single-phase stub data
├── fixtures/loader.py          # NEW — fixture discovery + loading helper
└── integration/
    ├── test_overhead_squat_e2e.py   # NEW — pipeline runs clean
    ├── test_single_leg_squat_e2e.py # NEW
    ├── test_push_up_e2e.py          # NEW
    └── test_rollup_stub_e2e.py      # NEW — verifies rollup doesn't crash with stub
```

## Protocols (rough)

- **`ModelLoader`** — `register(name, loader_fn)`, `load(name)`, `is_loaded(name)`, `info()`
- **`Lifter`** — `lift(angle_series_2d) -> angle_series_3d`. `IdentityLifter` returns input unchanged.
- **`SkeletonFitter`** — `fit(joint_positions_3d) -> skeleton_params`. `NoOpSkeletonFitter` returns an empty skeleton bundle.
- **`PhaseSegmenter`** — `segment(signal) -> list[Phase]`. `SinglePhaseSegmenter` returns one phase spanning the entire signal (rollup stub).

## Task List

1. `ModelLoader` protocol + `NoOpLoader` impl
2. `Lifter` protocol + `IdentityLifter` impl
3. `SkeletonFitter` protocol + `NoOpSkeletonFitter` impl
4. `PhaseSegmenter` protocol + `SinglePhaseSegmenter` impl (rollup stub)
5. `ModelRegistry` refactor — real registration + discovery
6. Lifter stage (wraps `Lifter`; sits between normalization and rep/phase segmentation)
7. SkeletonFitter stage (wraps `SkeletonFitter`; sits between lifter and rep/phase segmentation)
8. PhaseSegment stage (alternative to Plan 1's rep_segment stage; dispatches via `MovementType`)
9. Orchestrator dispatch: movement type → pipeline composition (rep-based vs phase-based)
10. Synthetic fixture generator (parameterized: movement, rep count, injected compensations)
11. Generate synthetic fixtures for overhead_squat (clean + valgus variant)
12. Generate synthetic fixtures for single_leg_squat, push_up, rollup (clean)
13. Fixture loader helper (discovers fixtures by pattern, loads into `Session` pydantic)
14. Integration test: overhead_squat clean fixture → pipeline runs end-to-end
15. Integration test: single_leg_squat + push_up e2e
16. Integration test: rollup stub e2e (verifies no crash, stub produces single phase)
17. Final validation

## Dependencies

- Plan 1 complete (stage framework exists to compose into).
- NO blocking dependency on Plan 2, 3, or 5. Can execute independently.

## Exit Criteria

- ~15 new tests.
- Pipeline runs end-to-end on all 4 movement types using synthetic fixtures. No ML model loaded, no crash.
- `Lifter` stage is in the pipeline and returns its input unchanged; removing `IdentityLifter` and dropping in a real `MotionBERT` implementation requires zero orchestrator changes.
- `PhaseSegmenter` stub returns a single phase for rollup; rep-based segmentation still runs for squats and push-ups.
- Fixture loader can load both synthetic files and (when they arrive) Flutter golden captures via the same interface.
- Model registry placeholder from scaffold plan Task 10 is now a real registration API (still no real models registered).

## Deferred to L3

- Exact data structure for `skeleton_params` — design against SKEL's 46-DOF shape without committing to a specific library.
- Synthetic fixture realism — iterate based on what the stages need. Start simple: sinusoidal angle trajectories with gaussian noise.
- Fixture filename convention — should match the Flutter team's output format (confirmed in the session alignment: `{movement}_{device}_{capture_date}.json`).

## Notes for writing-plans

- The synthetic generator is the critical piece. It must produce fixtures that exercise every downstream stage. Coordinate with Plan 3's reference-rep generator — they might share code.
- When real models land, `IdentityLifter` / `NoOpSkeletonFitter` stay in place as test doubles for CI and local dev. Don't delete them.
- Consider whether the ML stages should be optional (skipped when no model is loaded) or mandatory (identity impls run always). Default: mandatory — keeps the pipeline composition uniform.
- Rollup's phase segmentation stub is the epoch's biggest fiction. Document clearly that this is scaffolding and real rollup analysis requires research gap §7.3 to close.
