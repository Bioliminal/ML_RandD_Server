# L2 Plan 5 — Operations + Observability (Stub — architecture patched 2026-04-14)

**Status:** Stub with corrected architecture. Flesh out with `writing-plans` + `parallel-planning` before execution. Architectural corrections from the 2026-04-14 plan-review are inlined below; expansion should preserve them verbatim.
**Parent:** `2026-04-10-analysis-pipeline-epoch.md`
**Depends on:** Plans 1-4 complete (all merged to main as of 2026-04-14)

## Goal

Harden the server for demos and early deployment. Add pipeline run tracking (every session POST creates a `PipelineRun` entity tracking stage progress), async pipeline execution (`POST /sessions` returns immediately with a run ID, work happens in the background), structured logging with correlation IDs, and per-stage timing.

Exit state: you can POST a session, immediately get a run ID back, poll `GET /runs/{id}/status`, and see stage-by-stage progress. Errors land as structured events tied to correlation IDs.

## File Tree Delta

Verified against current tree (2026-04-14): `api/main.py`, `api/schemas.py`, `api/routes/{health,protocols,reports,sessions}.py` exist. No `api/middleware.py` yet.

```
software/server/
├── pyproject.toml                    # MODIFIED — add python-json-logger dep
├── src/auralink/
│   ├── ops/                          # NEW package
│   │   ├── __init__.py               # NEW
│   │   ├── run_tracking.py           # NEW — PipelineRun + RunRegistry + RunObserver Protocol
│   │   ├── logging.py                # NEW — structured JSON logger config
│   │   ├── correlation.py            # NEW — ContextVar + snapshot/restore helpers
│   │   ├── timing.py                 # NEW — run_stage_timed() wrapper (NOT a decorator)
│   │   └── async_runner.py           # NEW — BackgroundTasks wrapper w/ context propagation
│   ├── api/
│   │   ├── main.py                   # MODIFIED — register middleware + runs router
│   │   ├── middleware.py             # NEW — CorrelationIdMiddleware
│   │   ├── schemas.py                # MODIFIED — SessionAsyncResponse (run_id), ErrorDetail
│   │   └── routes/
│   │       ├── sessions.py           # MODIFIED — default async, ?sync=true awaits inline
│   │       └── runs.py               # NEW — GET /runs/{id}, GET /runs/{id}/events
│   ├── config.py                     # MODIFIED — runs_dir, log_level, debug_endpoints_enabled
│   └── pipeline/
│       ├── events.py                 # NEW — PipelineEvent schema + JSONL event collector
│       └── orchestrator.py           # MODIFIED — NEW run_pipeline_tracked() alongside run_pipeline (existing run_pipeline stays untouched to keep Plan 1/2 tests green)
├── tests/
│   ├── unit/
│   │   ├── ops/                      # NEW
│   │   │   ├── __init__.py
│   │   │   ├── test_run_tracking.py          # PipelineRun state machine + RunRegistry + RunObserver Protocol
│   │   │   ├── test_correlation.py           # ContextVar get/set + snapshot_context()
│   │   │   ├── test_logging.py               # JSON formatter + correlation_id field injection
│   │   │   ├── test_timing.py                # run_stage_timed() duration capture + error path
│   │   │   ├── test_async_runner.py          # BackgroundTasks wrapper propagates context to sync + async callables
│   │   │   └── test_contextvar_spike.py      # EMPIRICAL spike: asserts X-Correlation-Id round-trips from header → BackgroundTask (sync path via threadpool, async path inline) → log line
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── test_correlation_middleware.py   # header in → ContextVar set → header out; missing header → generated UUID
│   │   └── pipeline/
│   │       ├── test_events.py                # PipelineEvent schema + JSONL collector append
│   │       └── test_orchestrator_tracked.py  # run_pipeline_tracked emits start/complete events per stage, updates PipelineRun via injected RunObserver
│   └── integration/
│       ├── test_runs_endpoint.py             # GET /runs/{id} + GET /runs/{id}/events
│       ├── test_async_pipeline.py            # POST /sessions (no sync) → 202 + run_id → poll /runs/{id} → complete
│       ├── test_run_failure.py               # quality gate failure → PipelineRun.status == failed, ErrorDetail populated
│       └── test_debug_events_flag.py         # /runs/{id}/events returns 404 when settings.debug_endpoints_enabled == False
└── software/mobile-handover/
    ├── schemas/session-response.schema.json  # MODIFIED — breaking: async response shape
    ├── interface/models.dart                  # MODIFIED — mirror new SessionAsyncResponse
    └── fixtures/sample-response.json         # MODIFIED — async example payload
```

## Schemas (typed)

```python
# auralink/api/schemas.py (additions)
class ErrorDetail(BaseModel):
    type: Literal["quality_gate", "stage_failure", "internal"]
    stage: str | None = None          # which stage raised (None for pre-stage errors)
    message: str                       # human-readable
    correlation_id: str                # for log cross-ref

class SessionAsyncResponse(BaseModel):  # NEW — returned from POST /sessions (async default)
    run_id: str                        # UUID4
    session_id: str
    status: Literal["pending"]         # always "pending" on creation
    links: dict[str, str]              # {"status": "/runs/{id}", "events": "/runs/{id}/events"}

# existing SessionCreateResponse (Plan 1) is kept for ?sync=true — returns the full Report inline

# auralink/ops/run_tracking.py
class PipelineRun(BaseModel):
    id: str                            # UUID4
    session_id: str
    status: Literal["pending", "running", "complete", "failed"]
    created_at: datetime               # tz-aware UTC
    updated_at: datetime
    completed_stages: list[str] = []
    current_stage: str | None = None
    error: ErrorDetail | None = None
    correlation_id: str                # seed for the run (async: fresh UUID; sync: inherited from request)

class RunObserver(Protocol):           # INJECTED into run_pipeline_tracked — keeps orchestrator decoupled
    def on_stage_start(self, run_id: str, stage: str) -> None: ...
    def on_stage_complete(self, run_id: str, stage: str, duration_ms: float) -> None: ...
    def on_stage_failed(self, run_id: str, stage: str, err: ErrorDetail) -> None: ...
    def on_run_complete(self, run_id: str) -> None: ...
    def on_run_failed(self, run_id: str, err: ErrorDetail) -> None: ...

class RunRegistry:                     # Concrete RunObserver impl + storage
    # filesystem layout: {data_dir}/runs/{run_id}.json  +  {data_dir}/runs/{run_id}.events.jsonl
    # Lifecycle is DISTINCT from SessionStorage: sessions are immutable inputs,
    # runs are mutable execution records. Multiple runs can reference one session (retries).
    def create(self, session_id: str, correlation_id: str) -> PipelineRun: ...
    def get(self, run_id: str) -> PipelineRun | None: ...
    def events(self, run_id: str) -> list[PipelineEvent]: ...
    # + RunObserver methods that persist state transitions

# auralink/pipeline/events.py
class PipelineEvent(BaseModel):
    run_id: str
    stage: str
    event: Literal["started", "completed", "failed"]
    timestamp: datetime                # tz-aware UTC
    duration_ms: float | None = None   # populated on completed/failed
    correlation_id: str
    error: ErrorDetail | None = None   # populated only on failed
```

**Run storage:** `{data_dir}/runs/` — separate subtree from `{data_dir}/sessions/`. Atomic writes via `os.replace` following the existing `SessionStorage` pattern. Events are append-only JSONL (`{run_id}.events.jsonl`) to make the GET /runs/{id}/events endpoint a simple file read.

**Why RunObserver Protocol, not direct storage writes:** `pipeline/orchestrator.py` stays a pure composer per L1 Modularity Principle 1. The orchestrator receives a `RunObserver` argument and calls lifecycle methods; tests inject a no-op observer, production injects `RunRegistry`. No import of `ops/` inside the orchestrator module → no circular dep, no lifecycle coupling.

## Task List

Tasks ordered by data-flow dependency. Waves, parallelism, and exact dep graph to be added by `parallel-planning` at expansion time. Task labels: **TDD** / **skip-tdd** / **spike**.

1. **[skip-tdd]** Add `python-json-logger>=2.0.7,<4` to `pyproject.toml`, `uv lock`, `uv sync`. Smoke-import the module.
2. **[TDD]** `ErrorDetail` schema in `api/schemas.py`. Tests: valid payloads for each `type` literal, correlation_id required, stage optional.
3. **[TDD]** `PipelineRun` schema + `RunRegistry` (filesystem persistence + `RunObserver` interface impl) in `ops/run_tracking.py`. Tests: state machine transitions (pending→running→complete, pending→running→failed), atomic write round-trip, `get()` returns `None` for unknown id, `events()` reads JSONL. Also add `runs_dir: Path` + `log_level: str` + `debug_endpoints_enabled: bool = False` to `config.py:Settings`.
4. **[TDD]** Correlation ID `ContextVar` + `get_correlation_id()` + `set_correlation_id()` + `snapshot_context()` helpers in `ops/correlation.py`. Tests: default value, set/get round-trip, `snapshot_context()` captures all ContextVars for cross-boundary restore.
5. **[TDD]** `PipelineEvent` schema + append-only JSONL writer in `pipeline/events.py`. Tests: serialize/deserialize, append preserves ordering, timestamp is tz-aware UTC.
6. **[TDD]** Structured JSON logger config in `ops/logging.py`. Uses `python-json-logger.JsonFormatter`, attaches a filter that injects `correlation_id` from `ops/correlation.py` into every record. Tests: formatter emits JSON, correlation_id populated from ContextVar, works for both `logger.info()` and exception logging.
7. **[TDD]** `run_stage_timed(stage_name, stage_fn, ctx, observer)` wrapper in `ops/timing.py`. **NOT a decorator** — a call-site wrapper so stages in `pipeline/stages/` stay decorator-free and Plan 1 Principle 1 ("stages are pure functions") is preserved. Tests: successful stage → observer.on_stage_start + on_stage_complete with duration, raising stage → observer.on_stage_failed with ErrorDetail.
8. **[TDD]** `CorrelationIdMiddleware` in `api/middleware.py`. Reads `X-Correlation-Id` header (generates UUID4 if missing), sets the `ContextVar`, attaches to response header. Tests: header propagation in both directions, missing header → new UUID, malformed header rejected with 400.
9. **[TDD]** `run_pipeline_tracked(session, observer, ctx)` in `pipeline/orchestrator.py`. A NEW function alongside the existing `run_pipeline()` — existing Plan 1/2 tests continue to call `run_pipeline()` unchanged. `run_pipeline_tracked` wraps each stage in `run_stage_timed`, emits events through the observer, and returns the same `PipelineArtifacts` as `run_pipeline`. On stage failure, observer gets `ErrorDetail(type="quality_gate" | "stage_failure", ...)` and the run ends. Tests: happy path emits N start + N complete events for N stages, failure path emits start + failed, no events are emitted via direct orchestrator import (observer injection verified by mock).
10. **[spike, TDD]** Contextvar propagation spike in `ops/async_runner.py` + `tests/unit/ops/test_contextvar_spike.py`. This task exists because plan line 85 (the pre-patch notes) had a technically wrong claim about contextvars — see "Notes" section below for the corrected mechanics. The async_runner module wraps `BackgroundTasks.add_task` with an explicit `contextvars.copy_context().run()` binding so ContextVar values (including `correlation_id`) propagate into BOTH async and sync-via-threadpool callables. The test asserts an empirical round-trip: inject a correlation_id into the ContextVar, enqueue a sync AND an async background task, each task reads the ContextVar and writes to a capture list, assert both see the injected value. This is the observability-foundation spike — do not skip it.
11. **[TDD, 9a]** Sync-mode test migration. Migrate the 7 bare `POST /sessions` calls across 4 integration test files to pass `?sync=true` explicitly. **Full list from 2026-04-14 grep of the bioliminal repo:**
    - `tests/integration/test_sessions_endpoint.py` lines 14, 27, 36 (3 calls)
    - `tests/integration/test_full_report.py` lines 13, 37, 62 (3 calls)
    - `tests/integration/test_protocols_endpoint.py` line 9 (1 call — inside `_post_session` helper)
    - `tests/integration/test_protocol_e2e.py` line 19 (1 call — inside `_post_squat` helper)
    - Also audit `tests/integration/test_session_pipeline.py` line 26 (1 call, may already be testing async — verify and migrate or annotate as intentional).
    After migration: run full suite, still green, **default remains sync** (flip happens in Task 12). This makes the risky wave transition reversible.
12. **[TDD, 9b]** Flip the `POST /sessions` default to async in `api/routes/sessions.py`. Return `SessionAsyncResponse` with status 202 when `?sync` is absent or false; when `?sync=true`, call `run_pipeline_tracked` and `await` inline, returning the full `SessionCreateResponse` (Report) with status 201. **Sync path reuses the same orchestrator entry (`run_pipeline_tracked`) — no parallel implementation.** Use `ops/async_runner.schedule_tracked(...)` for the background case so ContextVars propagate. Tests: async path returns 202 + run_id, sync path returns 201 + full report, response shape matches `SessionAsyncResponse` / `SessionCreateResponse` respectively.
13. **[TDD]** `GET /runs/{run_id}` + `GET /runs/{run_id}/events` endpoints in `api/routes/runs.py`. Register router in `api/main.py`. The `/events` endpoint is gated by `settings.debug_endpoints_enabled`: returns 404 when False. Tests: unknown run_id → 404, valid run → current state, events stream readable, debug-flag gate enforced.
14. **[TDD]** Mobile-handover OpenAPI contract update. Regenerate `software/mobile-handover/schemas/session-response.schema.json` via the existing `tools/export_schemas.py`. Update `software/mobile-handover/interface/models.dart` to mirror `SessionAsyncResponse` as a new Dart class; KEEP the existing sync `SessionCreateResponse` Dart class (both are valid response shapes). Update `software/mobile-handover/fixtures/sample-response.json` with an async example. Tests: pydantic→JSON-schema export runs, Dart file parses, fixture validates against schema. **This is a breaking contract change** — document in the decision doc at epoch completion.
15. **[TDD]** Integration test: async happy path (`tests/integration/test_async_pipeline.py`). POST overhead_squat session, assert 202 + run_id, poll `GET /runs/{id}` until status == complete, assert `completed_stages` matches the stage list, assert events JSONL has one start + one complete per stage.
16. **[TDD]** Integration test: quality-gate failure path (`tests/integration/test_run_failure.py`). POST a malformed session that fails quality_gate, poll `GET /runs/{id}` until status == failed, assert `error: ErrorDetail(type="quality_gate", ...)`, assert correlation_id is present in both the run and the logged error.
17. **[TDD]** Integration test: debug-endpoint flag (`tests/integration/test_debug_events_flag.py`). With `debug_endpoints_enabled=False` → `/runs/{id}/events` returns 404; with `=True` → returns 200 with events list.
18. **[skip-tdd]** Final validation: `uv run pytest -x -q` (full suite), `uv run ruff check software/server/`, `uv run black --check software/server/`, live smoke: start uvicorn, `curl -X POST /sessions` → assert 202 + run_id, `curl /runs/{id}` → assert pending/running/complete transition, `curl /runs/{id}/events` (with debug flag) → assert non-empty event list, assert every log line since startup has a `correlation_id` field.

**Expected new test count:** ~35-40 tests (baseline 231 → ~266-271).

**Task dependencies (input to `parallel-planning`):**
- T1 → T6 (logger needs the dep)
- T2 → T3 (PipelineRun.error uses ErrorDetail)
- T3 → T7, T9, T13, T15, T16 (RunRegistry + RunObserver)
- T4 → T6, T8, T10 (correlation ContextVar)
- T5 → T7, T9, T15 (PipelineEvent)
- T2, T6 → T7 (timing wrapper uses ErrorDetail + logger)
- T3, T4, T5, T7 → T9 (`run_pipeline_tracked` composes everything above)
- T4 → T10 (async_runner uses snapshot_context)
- T9, T10 → T12 (flip depends on both tracked orchestrator and context-safe scheduling)
- T11 must land before T12 (audit-and-migrate before flip — reversible wave transition)
- T12 → T13, T14, T15, T16, T17
- T18 is the final validation single-task wave

## Dependencies

- Plan 1 complete (orchestrator exists).
- Optional: waits for Plans 2 + 3 to be merged so run tracking covers the full pipeline, but can run independently if needed.

## Exit Criteria

- ~35-40 new tests. Full suite green (~266-271 total).
- `POST /sessions` (no `?sync`) returns 202 + `SessionAsyncResponse{run_id, session_id, status:"pending", links}` immediately; pipeline runs in background via `ops/async_runner`.
- `POST /sessions?sync=true` still returns 201 + full Report by awaiting `run_pipeline_tracked` inline (no parallel code path).
- `GET /runs/{id}` transitions pending → running → complete for a successful session.
- `GET /runs/{id}/events` (with `debug_endpoints_enabled=True`) returns the JSONL event stream; returns 404 when the flag is False.
- Every log line has a `correlation_id` field propagated from the `X-Correlation-Id` request header (or a fresh UUID if absent). Logs are structured JSON via `python-json-logger`.
- Per-stage timing recorded in `PipelineRun.events` via the `RunObserver` injected into `run_pipeline_tracked`.
- A failed quality gate shows up as `PipelineRun.status == "failed"` with `error: ErrorDetail(type="quality_gate", ...)` and the correlation_id cross-referenceable in logs.
- Mobile-handover contract regenerated and committed; decision doc flags the breaking response-shape change.
- Plan 1-4 integration tests continue to pass (they opt into sync via `?sync=true` after T11).
- `pipeline/orchestrator.py` does not import `ops/*`; the orchestrator composes stages and calls `RunObserver` methods through an injected argument (decoupling verified by a dedicated unit test in `tests/unit/pipeline/test_orchestrator_tracked.py`).

## Deferred to L3

- Log aggregation target (local file vs stdout vs OTEL exporter) — start with stdout, leave the exporter interface open.
- Retention policy for `PipelineRun` records — leave them forever for now; add cleanup later if needed.
- Whether `PipelineEvent` lands in a dedicated event log (JSONL file) or embedded in the `PipelineRun` record.
- If `BackgroundTasks` turns out to be insufficient (e.g., for heavy ML inference later), the plan defers to adopting TaskIQ or Celery in a follow-on.

## Notes for writing-plans

- FastAPI `BackgroundTasks` run in-process, sequentially, AFTER the response is sent. For a real production deployment we'd need a proper task queue (TaskIQ / Celery / Arq), but for a capstone demo in-process is fine. Document this explicitly in the decision doc.

- **Correlation IDs and BackgroundTasks — the correct mechanics (corrected 2026-04-14):**
  - FastAPI `BackgroundTasks.add_task` does NOT call `asyncio.create_task`. It runs callables inline after the response, using `await` for async callables and `starlette.concurrency.run_in_threadpool` for sync callables.
  - **For async callables**, the task runs in the same event loop slot as the request, so ContextVar values set earlier in the request context DO persist — no extra work needed.
  - **For sync callables**, `run_in_threadpool` hops to a threadpool executor and ContextVars DO NOT propagate by default (each thread has its own ContextVar storage).
  - The fix: `ops/async_runner.schedule_tracked()` wraps the callable in `contextvars.copy_context().run(fn, *args)` before handing it to `BackgroundTasks.add_task`. This captures the current context (including `correlation_id`) and re-binds it inside whichever executor runs the callable, for both sync and async targets.
  - The T10 spike test is non-negotiable — it empirically verifies this round-trip for both paths. Plan line 85 in the pre-patch stub hand-waved this; the expansion must not.

- Don't over-engineer structured logging. Start with `python-json-logger` and a custom filter that pulls `correlation_id` from the ContextVar. Reject any plan iteration that pulls in `structlog`-level machinery unless justified.

- `?sync=true` is a **hard requirement, not optional** — Plan 1 already shipped it as a recognized no-op flag. This plan flips the default to async AND collapses sync/async into ONE code path: both paths call `run_pipeline_tracked`; sync awaits inline and returns the Report, async schedules via `async_runner` and returns `SessionAsyncResponse`. **Do not build two parallel orchestrator entry points.** Preserve the exact query param spelling used in Plan 1. The task is not done until every test that relied on sync semantics has been audited and migrated (see T11 for the explicit file list), and the full suite is green after the flip.

- **Events endpoint (`/runs/{id}/events`) is debug-only and MUST be enforced**, not commented. Gate it behind `settings.debug_endpoints_enabled: bool = False`; production config leaves it False, dev config sets True. Returning 404 when disabled is sufficient — no need for 403. Mobile team must not be able to accidentally depend on it.

- **Mobile-handover breaking contract change.** `POST /sessions` response shape changes from `SessionCreateResponse` (full Report) to `SessionAsyncResponse` (run_id + links) by default. Flutter teammate needs the updated `interface/models.dart` AND must handle the status-202 async path. T14 is the task that owns this; the epoch decision doc must flag it explicitly.

- **L1 Modularity Principle 1 compliance.** The `pipeline/orchestrator.py` module MUST NOT import from `ops/*`. The `RunObserver` Protocol lives in `ops/run_tracking.py` but is accepted as a duck-typed argument by `run_pipeline_tracked` — the orchestrator declares the Protocol-like shape inline or via a stub import-free Protocol defined in `pipeline/events.py`. Tests assert no `from auralink.ops` import appears in `orchestrator.py`.
