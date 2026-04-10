# L2 Plan 5 — Operations + Observability (Stub)

**Status:** Stub — flesh out with `writing-plans` before execution.
**Parent:** `2026-04-10-analysis-pipeline-epoch.md`
**Depends on:** Plan 1 (pipeline framework)

## Goal

Harden the server for demos and early deployment. Add pipeline run tracking (every session POST creates a `PipelineRun` entity tracking stage progress), async pipeline execution (`POST /sessions` returns immediately with a run ID, work happens in the background), structured logging with correlation IDs, and per-stage timing.

Exit state: you can POST a session, immediately get a run ID back, poll `GET /runs/{id}/status`, and see stage-by-stage progress. Errors land as structured events tied to correlation IDs.

## File Tree Delta

```
software/server/src/auralink/
├── ops/
│   ├── __init__.py            # NEW
│   ├── run_tracking.py        # NEW — PipelineRun entity + storage
│   ├── logging.py             # NEW — structured logger config + formatters
│   ├── correlation.py         # NEW — correlation ID context var + helpers
│   └── timing.py              # NEW — stage timing decorator
├── api/
│   ├── middleware.py          # NEW — correlation ID injection middleware
│   └── routes/
│       ├── sessions.py        # MODIFIED — async execution, returns run ID
│       └── runs.py            # NEW — GET /runs/{id}/status
└── pipeline/
    ├── orchestrator.py        # MODIFIED — emits stage events, uses timing decorator
    └── events.py              # NEW — PipelineEvent hierarchy

tests/
├── unit/ops/                  # NEW
└── integration/test_async_pipeline.py  # NEW — POST returns run ID, status endpoint tracks completion
```

## Schemas (rough)

- **`PipelineRun`** — `id`, `session_id`, `status: Literal["pending", "running", "complete", "failed"]`, `created_at`, `updated_at`, `completed_stages: list[str]`, `current_stage: str | None`, `error: ErrorDetail | None`
- **`PipelineEvent`** — `run_id`, `stage_name`, `event: Literal["started", "completed", "failed"]`, `timestamp`, `duration_ms`, `metadata: dict`
- **Run storage** — local filesystem alongside session storage; follow the same pattern

## Task List

1. `PipelineRun` pydantic schema + run storage module
2. Correlation ID context var + helper functions
3. Correlation ID middleware (injects header `X-Correlation-Id` if missing, propagates to logs)
4. Structured logger config (JSON formatter, stdlib logging)
5. Stage timing decorator (`@timed_stage` that records duration + emits events)
6. `PipelineEvent` hierarchy + event emitter
7. Orchestrator refactor to emit events + update `PipelineRun` status
8. Async pipeline execution via FastAPI `BackgroundTasks`
9. Flip the default `POST /sessions` behavior to async: create `PipelineRun`, schedule background task, return run ID in response body. **Sync mode remains available via `?sync=true`** (already shipped as a no-op flag in Plan 1). Audit every integration test added by Plans 1 and 2 that assumes sync POST → GET semantics and migrate them to pass `?sync=true` explicitly as part of this task. The test suite must be green after the flip.
10. New `GET /runs/{id}/status` endpoint
11. New `GET /runs/{id}/events` endpoint (stream of events for debugging)
12. Integration test: POST returns run ID immediately, status polls transition pending → running → complete
13. Integration test: a failing quality gate produces a `failed` run with structured error
14. Final validation

## Dependencies

- Plan 1 complete (orchestrator exists).
- Optional: waits for Plans 2 + 3 to be merged so run tracking covers the full pipeline, but can run independently if needed.

## Exit Criteria

- ~12-15 new tests.
- `POST /sessions` returns immediately with a run ID; pipeline runs in the background.
- `GET /runs/{id}/status` transitions pending → running → complete for a successful session.
- Every log line has a correlation ID; logs are structured JSON.
- Per-stage timing recorded in the run history.
- A failed quality gate shows up as `status: failed` with a structured error detail.
- All previous tests still pass.

## Deferred to L3

- Log aggregation target (local file vs stdout vs OTEL exporter) — start with stdout, leave the exporter interface open.
- Retention policy for `PipelineRun` records — leave them forever for now; add cleanup later if needed.
- Whether `PipelineEvent` lands in a dedicated event log (JSONL file) or embedded in the `PipelineRun` record.
- If `BackgroundTasks` turns out to be insufficient (e.g., for heavy ML inference later), the plan defers to adopting TaskIQ or Celery in a follow-on.

## Notes for writing-plans

- FastAPI `BackgroundTasks` run in-process. For a real production deployment we'd need a proper task queue, but for a capstone demo in-process is fine. Document this explicitly.
- Correlation IDs should propagate from HTTP headers into background tasks. Python `contextvars` supports this, but test it carefully — async context propagation has sharp edges.
- Don't over-engineer structured logging. Start with `python-json-logger` or manual JSON formatter. Reject any plan iteration that pulls in `structlog`-level machinery unless justified.
- `?sync=true` is a **hard requirement, not optional** — Plan 1 already shipped it as a recognized no-op flag. This plan flips the default to async; existing tests opt back into sync via `?sync=true`. Preserve the exact query param spelling used in Plan 1. The task is not done until every test that relied on sync semantics has been audited and migrated, and the full suite is green after the flip.
- Events endpoint is debug-only — not part of the public API. Document that.
