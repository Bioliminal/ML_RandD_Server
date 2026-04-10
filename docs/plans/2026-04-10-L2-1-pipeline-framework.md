# L2 Plan 1 — Pipeline Framework + Core Analysis Stages (Stub)

**Status:** Stub — flesh out with `writing-plans` before execution.
**Parent:** `2026-04-10-analysis-pipeline-epoch.md`
**Depends on:** Server scaffold (`2026-04-09-server-scaffold.md`) — completed.

## Goal

Replace the `pipeline.orchestrator` stub with a real stage framework. Define the `Stage` protocol, artifact schemas, quality gates, and the core analysis stages needed to turn a `Session` into a structured pre-report artifact bundle. Wire the orchestrator into `POST /sessions` (runs the pipeline, persists the artifacts) and expose `GET /sessions/{id}/report` returning the raw artifacts (chain reasoning comes in Plan 2).

## File Tree Delta

```
software/server/src/auralink/
├── pipeline/
│   ├── artifacts.py             # NEW — pydantic artifact schemas at every stage boundary
│   ├── errors.py                # NEW — PipelineError hierarchy, StageError, QualityGateError
│   ├── orchestrator.py          # MODIFIED — real stage registry + dispatch, replaces the stub
│   └── stages/
│       ├── __init__.py          # NEW
│       ├── base.py              # NEW — Stage protocol, StageContext dataclass
│       ├── quality_gate.py      # NEW — frame rate, visibility, duration, landmark completeness checks
│       ├── angle_series.py      # NEW — all frames → AngleTimeSeries
│       ├── normalize.py         # NEW — body-size normalization via hip-shoulder distance
│       ├── rep_segment.py       # NEW — wraps analysis.rep_segmentation as a Stage
│       ├── per_rep_metrics.py   # NEW — amplitude, velocity, ROM, compensation angles per rep
│       └── within_movement_trend.py  # NEW — within-movement trend metrics
├── api/
│   ├── routes/
│   │   ├── sessions.py          # MODIFIED — POST runs the pipeline
│   │   └── reports.py           # NEW — GET /sessions/{id}/report
│   └── errors.py                # NEW — FastAPI exception handlers mapping PipelineError → HTTPException
tests/
├── unit/pipeline/               # NEW — per-stage unit tests
└── integration/test_report_endpoint.py  # NEW — POST then GET round-trip with synthetic fixture
```

## Artifact Schemas (rough)

- **`SessionQualityReport`** — result of quality gate (`passed: bool`, `issues: list[QualityIssue]`, `metrics: dict`)
- **`AngleTimeSeries`** — `dict[str, list[float]]` keyed by `{side}_{joint}_{angle_type}`, plus frame timestamps
- **`NormalizedAngleTimeSeries`** — same shape plus normalization factors
- **`RepBoundaries`** — wraps the existing `analysis.rep_segmentation.RepBoundary` list per tracked angle
- **`PerRepMetrics`** — per-rep amplitude, peak velocity, ROM, mean compensation angles
- **`WithinMovementTrend`** — monotonic change detection across reps (ROM decrease, velocity decrease, compensation increase)
- **`PipelineArtifacts`** — container holding all of the above, keyed by stage name

## Task List (one-liners; TDD detail comes during writing-plans)

1. `Stage` protocol + `StageContext` dataclass + base tests
2. Artifact schemas in `pipeline/artifacts.py` (pydantic, one test per schema shape)
3. Error hierarchy in `pipeline/errors.py`
4. Quality gate stage (frame rate, visibility, duration, landmark completeness; each as a separate TDD cycle)
5. Angle time-series stage (compute all tracked angles across every frame)
6. Normalization stage (hip-shoulder distance as scale factor)
7. Rep segmentation stage (wraps `segment_reps`, takes `NormalizedAngleTimeSeries`, returns `RepBoundaries`)
8. Per-rep metrics stage (amplitude, velocity profile, ROM, compensation angles per rep)
9. Within-movement trend stage (monotonic change detection)
10. Orchestrator with stage registry + per-movement pipeline composition (config-driven: which stages apply to which `MovementType`). **The registry must expose a post-initialization extension API** (e.g. `registry.register_movement(movement_type, stage_list)`) so Plan 4 can add rollup's phase-based composition without touching `orchestrator.py`. Plan 1 owns the dispatch mechanism; Plan 4 only adds entries through this API.
11. Wire `POST /sessions` to run the pipeline synchronously after `storage.save()` and persist artifacts alongside the raw session. **Ship `?sync=true` as a recognized (no-op) query parameter in this plan**, even though sync is the default here. This ensures Plan 5 can later flip the default to async while existing tests continue to work by passing `?sync=true` explicitly. Every integration test in this plan passes `?sync=true` to stay green across the Plan 5 transition.
12. New `GET /sessions/{id}/report` endpoint returning the artifact bundle as JSON
13. FastAPI exception handlers for `PipelineError` hierarchy
14. End-to-end integration test: POST a synthetic overhead_squat → GET returns populated artifacts
15. Final validation task (full suite, smoke test, lint)

## Dependencies

- Scaffold plan completed (all 13 tasks).
- No external blockers.

## Exit Criteria

- ~25-30 new tests, all passing.
- End-to-end integration test: a synthetic overhead_squat fixture POSTs successfully and `GET /sessions/{id}/report` returns a `PipelineArtifacts` bundle with populated quality report, angle series, rep boundaries, per-rep metrics, and trend metrics.
- `pipeline.orchestrator.run_pipeline()` is no longer a stub — it composes stages via the registry.
- Quality gate rejects a fixture with 1 landmark stripped out, returning an HTTP 422 with a structured error body.
- Ruff + black clean. Dev server smoke-test passes.

## Deferred to L3 (during execution)

- Exact pydantic field names on each artifact (refine as stages compose).
- The specific compensation angle set (knee valgus + trunk lean at minimum; others TBD based on which reps expose the signal).
- Quality gate threshold defaults (start with frame_rate ≥ 20, visibility ≥ 0.5 average, duration ≥ 1s, missing landmarks ≤ 5%; tune once fixtures are real).
- Whether stages are classes or functions (leaning functions — simpler, no state needed beyond what `StageContext` carries).

## Notes for writing-plans

- Each stage gets its own TDD cycle with 2-4 tests. Watch for tests that only check "no exception thrown" — require value assertions per `task-executor` Path A.
- Stage composition order matters: quality_gate → angle_series → normalize → rep_segment → per_rep_metrics → within_movement_trend. Document this order in `orchestrator.py` as data, not control flow.
- The orchestrator should raise `PipelineError` on quality gate failure and allow upstream code to map to HTTP 422.
- `POST /sessions` runs **synchronously by default** in this plan AND accepts `?sync=true` as a recognized no-op query parameter upfront. Plan 5 later flips the default to async while preserving `?sync=true` behavior; every test added by this plan must pass `?sync=true` explicitly so the suite remains stable across the Plan 5 transition.
