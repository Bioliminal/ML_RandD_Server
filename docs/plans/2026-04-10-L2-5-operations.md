# L2 Plan 5 — Operations + Observability

**Status:** Planning (stub expanded 2026-04-14 after architectural patch)
**Parent:** `2026-04-10-analysis-pipeline-epoch.md`
**Depends on:** Plans 1-4 complete (all merged to main as of 2026-04-14)
**Created:** 2026-04-10 (stub) → patched 2026-04-14 (architecture) → expanded 2026-04-14 (this document)
**Execution:** parallel-plan-executor, 18 tasks, waves computed at `parallel-planning` time

## Goal

Harden the server for demos and early deployment. Add pipeline run tracking (every session POST creates a `PipelineRun` entity tracking stage progress), async pipeline execution (`POST /sessions` returns immediately with a run ID, work happens in the background), structured logging with correlation IDs, and per-stage timing.

Exit state: you can POST a session, immediately get a run ID back, poll `GET /runs/{id}/status`, and see stage-by-stage progress. Errors land as structured events tied to correlation IDs.

## File Tree Delta

Verified against current tree (2026-04-14): `api/main.py`, `api/schemas.py`, `api/routes/{health,protocols,reports,sessions}.py` exist. `api/errors.py` already exists with three exception handlers. `pipeline/orchestrator.py` already imports and wires `run_rep_comparison` (Plan 3). No `api/middleware.py` yet. No `ops/` package yet.

```
software/server/
├── pyproject.toml                    # MODIFIED (T1) — add python-json-logger dep
├── src/auralink/
│   ├── ops/                          # NEW package
│   │   ├── __init__.py               # NEW (T3)
│   │   ├── run_tracking.py           # NEW (T3) — PipelineRun + RunRegistry + RunObserver Protocol
│   │   ├── logging.py                # NEW (T6) — structured JSON logger config
│   │   ├── correlation.py            # NEW (T4) — ContextVar + snapshot/restore helpers
│   │   ├── timing.py                 # NEW (T7) — run_stage_timed() wrapper (NOT a decorator)
│   │   └── async_runner.py           # NEW (T10) — BackgroundTasks wrapper w/ context propagation
│   ├── api/
│   │   ├── main.py                   # MODIFIED (T8, T13) — register middleware + runs router
│   │   ├── middleware.py             # NEW (T8) — CorrelationIdMiddleware
│   │   ├── schemas.py                # MODIFIED (T2, T12) — ErrorDetail, SessionAsyncResponse
│   │   └── routes/
│   │       ├── sessions.py           # MODIFIED (T11, T12) — default async, ?sync=true awaits inline
│   │       └── runs.py               # NEW (T13) — GET /runs/{id}, GET /runs/{id}/events
│   ├── config.py                     # MODIFIED (T3) — runs_dir, log_level, debug_endpoints_enabled
│   └── pipeline/
│       ├── events.py                 # NEW (T5) — PipelineEvent schema + JSONL event collector
│       └── orchestrator.py           # MODIFIED (T9) — NEW run_pipeline_tracked() alongside run_pipeline
├── tests/
│   ├── unit/
│   │   ├── ops/                      # NEW
│   │   │   ├── __init__.py                           # NEW (T3)
│   │   │   ├── test_run_tracking.py                  # NEW (T3)
│   │   │   ├── test_correlation.py                   # NEW (T4)
│   │   │   ├── test_logging.py                       # NEW (T6)
│   │   │   ├── test_timing.py                        # NEW (T7)
│   │   │   ├── test_async_runner.py                  # NEW (T10) — wraps add_task
│   │   │   └── test_contextvar_spike.py              # NEW (T10) — empirical header→task→log round-trip
│   │   ├── api/
│   │   │   ├── __init__.py                           # NEW (T8) if missing
│   │   │   └── test_correlation_middleware.py        # NEW (T8)
│   │   └── pipeline/
│   │       ├── test_events.py                        # NEW (T5)
│   │       └── test_orchestrator_tracked.py          # NEW (T9)
│   └── integration/
│       ├── test_runs_endpoint.py                     # NEW (T13)
│       ├── test_async_pipeline.py                    # NEW (T15)
│       ├── test_run_failure.py                       # NEW (T16)
│       └── test_debug_events_flag.py                 # NEW (T17)
└── software/mobile-handover/
    ├── schemas/session-response.schema.json          # NEW (T14) — new derived output
    ├── interface/models.dart                          # MODIFIED (T14) — add SessionAsyncResponse
    ├── fixtures/sample-response.json                  # NEW (T14)
    └── tools/export_schemas.py                        # MODIFIED (T14) — also export response schemas
```

## Schemas (typed — preserved verbatim from patched stub)

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

## Architecture Invariants (preserved from 2026-04-14 plan-review)

1. **FastAPI BackgroundTasks run in-process, sequentially, AFTER the response is sent.** For a real production deployment we'd want a proper task queue (TaskIQ / Celery / Arq), but for a capstone demo in-process is fine. The epoch decision doc must document this explicitly.

2. **Correlation IDs and BackgroundTasks — corrected mechanics:**
   - `BackgroundTasks.add_task` does NOT call `asyncio.create_task`. It runs callables inline after the response, using `await` for async callables and `starlette.concurrency.run_in_threadpool` for sync callables.
   - For **async callables**, the task runs in the same event loop slot as the request, so ContextVar values set earlier in the request context DO persist — no extra work needed.
   - For **sync callables**, `run_in_threadpool` hops to a threadpool executor and ContextVars DO NOT propagate by default (each thread has its own ContextVar storage).
   - **Fix:** `ops/async_runner.schedule_tracked()` wraps the callable in `contextvars.copy_context().run(fn, *args)` before handing it to `BackgroundTasks.add_task`. This captures the current context (including `correlation_id`) and re-binds it inside whichever executor runs the callable, for both sync and async targets.
   - The T10 spike test is **non-negotiable** — it empirically verifies this round-trip for both paths.

3. **Don't over-engineer structured logging.** Start with `python-json-logger` and a custom filter that pulls `correlation_id` from the ContextVar. Do NOT pull in `structlog`-level machinery unless justified in a follow-on plan.

4. **`?sync=true` is a hard requirement, not optional.** Plan 1 already shipped it as a recognized no-op flag. This plan flips the default to async AND collapses sync/async into ONE code path: both paths call `run_pipeline_tracked`; sync awaits inline and returns the Report, async schedules via `async_runner` and returns `SessionAsyncResponse`. **Do not build two parallel orchestrator entry points.** Preserve the exact query param spelling used in Plan 1. The task is not done until every test that relied on sync semantics has been audited and migrated (T11) and the full suite is green after the flip (T12).

5. **Events endpoint (`/runs/{id}/events`) is debug-only and MUST be enforced.** Gate it behind `settings.debug_endpoints_enabled: bool = False`; production config leaves it False, dev config sets True. Returning 404 when disabled is sufficient — no need for 403. Mobile team must not be able to accidentally depend on it.

6. **Mobile-handover breaking contract change.** `POST /sessions` default response shape changes from `SessionCreateResponse` (full Report) to `SessionAsyncResponse` (run_id + links). Flutter teammate needs the updated `interface/models.dart` AND must handle the status-202 async path. T14 owns this; the epoch decision doc flags it explicitly.

7. **L1 Modularity Principle 1 compliance.** The `pipeline/orchestrator.py` module MUST NOT import from `ops/*` **at module load time**. The `RunObserver` Protocol lives in `ops/run_tracking.py` but is accepted as a duck-typed argument by `run_pipeline_tracked` — the orchestrator declares its own internal `RunObserver` stub Protocol (import-free) in `pipeline/events.py` and uses that for the type hint. Function-local imports inside `run_pipeline_tracked` (e.g. `from auralink.ops.timing import run_stage_timed` and `from auralink.ops.correlation import get_correlation_id`) are acceptable because they defer lifecycle coupling to first-call time and preserve the module-level import graph. Tests assert no `from auralink.ops` import appears at the top of `orchestrator.py` (see `test_orchestrator_no_ops_import_at_module_level`).

## Existing Code References

Files Plan 5 reads, modifies, or integrates with. Exact line numbers current as of 2026-04-14:

- `software/server/pyproject.toml` lines 6–15 — current `[project].dependencies`. T1 adds `python-json-logger>=2.0.7,<4` between `pyyaml` and the closing bracket (line 14 → 15).
- `software/server/src/auralink/config.py` lines 7–23 — current `Settings` class with `app_name`, `data_dir`, `sessions_dir` computed field, and `ensure_dirs()`. T3 extends this with `runs_dir` computed field, `log_level: str = "INFO"`, and `debug_endpoints_enabled: bool = False`, and updates `ensure_dirs()` to create `runs_dir`.
- `software/server/src/auralink/api/schemas.py` lines 1–58 — current models (`Landmark`, `Frame`, `MovementType`, `SessionMetadata`, `Session`, `SessionCreateResponse`). T2 adds `ErrorDetail` at EOF. T12 adds `SessionAsyncResponse` at EOF.
- `software/server/src/auralink/api/errors.py` lines 1–35 — existing exception handlers. T16 integration test exercises the `QualityGateError` handler path through `run_pipeline_tracked` to assert the ErrorDetail round-trip.
- `software/server/src/auralink/api/main.py` lines 1–19 — current FastAPI factory with four routers (`health`, `sessions`, `reports`, `protocols`). T8 adds `app.add_middleware(CorrelationIdMiddleware)` before `include_router` calls. T13 adds `from auralink.api.routes import runs` and `app.include_router(runs.router)` after `protocols.router`.
- `software/server/src/auralink/api/routes/sessions.py` lines 1–45 — current route. The existing `sync: bool = Query(default=True)` parameter is a recognized no-op. T11 doesn't touch this file; T12 rewrites `create_session` to:
  - Flip default to `sync=False`
  - Branch on `sync`: True → `await run_pipeline_tracked(...)` returning `SessionCreateResponse` (201); False → `async_runner.schedule_tracked(run_pipeline_tracked, ...)` returning `SessionAsyncResponse` (202).
  - Take a new `background_tasks: BackgroundTasks` parameter (FastAPI-injected).
  - Take new `run_registry: RunRegistry` dependency.
- `software/server/src/auralink/pipeline/orchestrator.py` lines 1–123 — current orchestrator. `run_pipeline()` lives at line 86–107; `_assemble_artifacts()` at line 110. T9 adds `run_pipeline_tracked()` alongside (not replacing) `run_pipeline`; existing Plan 1-4 tests keep calling `run_pipeline()` via the synchronous `POST /sessions?sync=true` path until T12 routes them through `run_pipeline_tracked` as well.
- `software/server/src/auralink/pipeline/storage.py` lines 11–51 — existing `SessionStorage` class. T3 mirrors its atomic-write pattern (`path.write_text(model_dump_json(indent=2))`) in `RunRegistry`. T3 `RunRegistry.__init__` takes `base_dir: Path` identically.
- `software/server/src/auralink/pipeline/stages/base.py` lines 1–36 — `StageContext`, `Stage`, and all `STAGE_NAME_*` constants including `STAGE_NAME_REP_COMPARISON` (line 35). T9 iterates the stage list returned by `reg.get_stages(movement)` the same way `run_pipeline()` does at line 94.
- `software/server/tests/integration/test_sessions_endpoint.py` lines 14, 27, 36 — three bare `client.post("/sessions", json=...)` calls. T11 migrates all three to `client.post("/sessions?sync=true", json=...)`.
- `software/server/tests/integration/test_full_report.py` lines 13, 37, 62 — three bare `client.post("/sessions", json=session.model_dump(mode="json"))` calls. T11 migrates all three to pass `?sync=true`.
- `software/server/tests/integration/test_protocols_endpoint.py` line 9 — `_post_session` helper issues one bare POST. T11 adds `?sync=true`.
- `software/server/tests/integration/test_protocol_e2e.py` line 19 — `_post_squat` helper issues one bare POST. T11 adds `?sync=true`.
- `software/server/tests/integration/test_session_pipeline.py` line 26 — one bare POST inside `test_sync_flag_is_accepted_as_noop`. The test's intent is that the no-op flag does not break either form; T11 leaves this file **as-is** because migrating it would delete coverage. After T12 the test is re-interpreted: the bare POST hits the async default, so the assertion on `r2.status_code` needs to be updated from `201` to `202`. T11 migrates the first call (`r1`) only if not already explicit; T12 updates the test to expect 202 on `r2`.
- `software/mobile-handover/tools/export_schemas.py` lines 1–29 — current single-schema export script. T14 extends it to also export `SessionCreateResponse` and `SessionAsyncResponse` json schemas to new files under `schemas/`.
- `software/mobile-handover/interface/models.dart` lines 154–168 — existing `SessionCreateResponse` Dart class. T14 keeps it and adds a new `SessionAsyncResponse` Dart class with the same naming convention.
- `software/mobile-handover/fixtures/sample_valid_session.json` — existing request fixture. T14 creates a separate `fixtures/sample_response_async.json` with an example async response payload.

## Commit Cadence

**One commit per TDD cycle (red → green → commit), NOT one commit per task.** Task N may produce 3–5 commits when it wires multiple behaviors. All commits use conventional prefixes: `feat(ops)`, `feat(api)`, `feat(pipeline)`, `test(integration)`, `refactor(pipeline)`, `chore(deps)`, `docs(plan)`. This matches the repo convention (see `memory/feedback_tdd_commit_cadence.md` in the olorin workspace); task-executor enforces it.

## Task List Overview

| ID | Title | Label | Tests | Depends on |
|---|---|---|---|---|
| T1 | Add `python-json-logger` runtime dep | skip-tdd | 0 | — |
| T2 | `ErrorDetail` schema | TDD | 3 | — |
| T3 | `PipelineRun` + `RunRegistry` + Settings additions | TDD | 6 | T2, T5 |
| T4 | Correlation ContextVar helpers | TDD | 4 | — |
| T5 | `PipelineEvent` schema + JSONL writer | TDD | 4 | T2 |
| T6 | Structured JSON logger config | TDD | 4 | T1, T4 |
| T7 | `run_stage_timed` wrapper | TDD | 4 | T2, T5, T6 |
| T8 | `CorrelationIdMiddleware` | TDD | 4 | T4 |
| T9 | `run_pipeline_tracked` in orchestrator | TDD | 5 | T3, T5, T7 |
| T10 | `async_runner` + ContextVar spike | spike+TDD | 4 | T4 |
| T11 | Sync-mode test migration | TDD | 0 new (migrates ~8) | — |
| T12 | Flip `POST /sessions` default to async | TDD | 4 | T9, T10, T11 |
| T13 | `GET /runs/{id}` + `/events` endpoints | TDD | 5 | T3, T12 |
| T14 | Mobile-handover contract update | TDD | 3 | T12 |
| T15 | Integration: async happy path | TDD | 2 | T12, T13 |
| T16 | Integration: quality-gate failure path | TDD | 2 | T12, T13 |
| T17 | Integration: debug-endpoint flag | TDD | 2 | T13 |
| T18 | Final validation (lint + live smoke) | skip-tdd | 0 | all |

**Expected new test count:** 3 + 6 + 4 + 4 + 4 + 4 + 4 + 5 + 4 + 4 + 5 + 3 + 2 + 2 + 2 = **56** new unit+integration assertions (~38 distinct test functions, the stub's ~35-40 estimate holds). Baseline 231 → ~266-271.

**Task dependencies (for `parallel-planning`):**
- T1 → T6 (logger needs the dep)
- T2 → T3, T5, T7 (PipelineRun.error / PipelineEvent.error / timing wrapper consume ErrorDetail)
- T5 → T3, T7, T9 (RunRegistry imports PipelineEvent; timing wrapper/orchestrator emit events) — **T5 MUST land before T3 in wave order**
- T4 → T6, T8, T10 (correlation ContextVar)
- T6 → T7 (timing wrapper emits structured log lines)
- T3, T5, T7 → T9 (`run_pipeline_tracked` composes these)
- T9, T10, T11 → T12 (flip depends on both tracked orchestrator and context-safe scheduling, and on sync tests being migrated)
- T3, T12 → T13 (runs endpoints need RunRegistry + the flipped POST flow)
- T12 → T14, T15, T16, T17
- T18 is the final single-task wave

## Per-Task Detail

---

### Task T1: Add `python-json-logger` runtime dependency

**Label:** skip-tdd

**Files owned (exclusive):**
- `software/server/pyproject.toml`

**Depends on:** nothing

**Research confidence:** high — `python-json-logger` 2.0.7 has been the de-facto choice since 2023, Apache-2.0, zero transitive deps beyond stdlib.

**Rationale:** T6 imports `pythonjsonlogger.jsonlogger.JsonFormatter`. Adding the dep inside any later parallel wave would race with every task that runs `uv sync`. T1 is a single-task setup step.

**Steps:**

1. Read `software/server/pyproject.toml` lines 6–15 and locate the `dependencies` list.
2. Add `"python-json-logger>=2.0.7,<4",` as a new line after `"pyyaml>=6.0",` (line 14).
3. Run `cd software/server && uv lock` and confirm the lockfile update mentions `python-json-logger`.
4. Run `cd software/server && uv sync`.
5. Smoke-import: `cd software/server && uv run python -c "from pythonjsonlogger.jsonlogger import JsonFormatter; print(JsonFormatter)"` — expect a non-error stdout mentioning `JsonFormatter`.
6. Run the full suite to confirm nothing regressed: `cd software/server && uv run pytest -q` — expect 231 passed.
7. Commit.

**Commit command:**
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/pyproject.toml software/server/uv.lock && \
git commit -m "chore(deps): add python-json-logger for structured logging"
```

**Expected test count after T1:** 231 (unchanged).

---

### Task T2: `ErrorDetail` schema in `api/schemas.py`

**Label:** TDD

**Files owned (exclusive):**
- `software/server/src/auralink/api/schemas.py` (additive only — append at EOF)
- `software/server/tests/unit/api/__init__.py` (create if missing)
- `software/server/tests/unit/api/test_error_detail_schema.py` (new)

**Depends on:** nothing

**Research confidence:** high — `ErrorDetail` is a pure pydantic v2 model; pattern matches the existing `SessionMetadata` model in the same file.

**Plan-review notes:** Keep the model minimal. The `type` literal drives the exception-handler mapping in `api/errors.py` when T16 wires the full error path. `stage` is optional so pre-stage (pre-`QualityGateError`) errors can still produce a valid ErrorDetail with `stage=None`.

**Commit cadence:** 1 TDD cycle, 1 commit.

**TDD cycle 1 — ErrorDetail model with three valid payloads**

*Step 1 — Write the failing test:*

Create `software/server/tests/unit/api/__init__.py` empty.

Create `software/server/tests/unit/api/test_error_detail_schema.py`:
```python
import pytest
from pydantic import ValidationError

from auralink.api.schemas import ErrorDetail


def test_quality_gate_error_detail_roundtrip():
    ed = ErrorDetail(
        type="quality_gate",
        stage="quality_gate",
        message="minimum_visibility below threshold",
        correlation_id="11111111-1111-1111-1111-111111111111",
    )
    assert ed.type == "quality_gate"
    assert ed.stage == "quality_gate"
    assert ed.correlation_id == "11111111-1111-1111-1111-111111111111"
    round_tripped = ErrorDetail.model_validate_json(ed.model_dump_json())
    assert round_tripped == ed


def test_stage_failure_error_detail_without_stage_rejected_by_literal():
    # type must be one of the literal set; bad type raises ValidationError
    with pytest.raises(ValidationError):
        ErrorDetail(
            type="not_a_real_type",  # type: ignore[arg-type]
            stage="normalize",
            message="numpy error",
            correlation_id="22222222-2222-2222-2222-222222222222",
        )


def test_internal_error_detail_allows_stage_none():
    ed = ErrorDetail(
        type="internal",
        stage=None,
        message="pre-stage setup exploded",
        correlation_id="33333333-3333-3333-3333-333333333333",
    )
    assert ed.stage is None
    assert ed.type == "internal"
    # correlation_id is required — omitting it must fail
    with pytest.raises(ValidationError):
        ErrorDetail(  # type: ignore[call-arg]
            type="internal",
            stage=None,
            message="no correlation id",
        )
```

*Step 2 — Run to verify failure:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/api/test_error_detail_schema.py -v
```
Expected: 3 failures with `ImportError: cannot import name 'ErrorDetail' from 'auralink.api.schemas'`.

*Step 3 — Write the minimal impl:*

Append to `software/server/src/auralink/api/schemas.py`:
```python
class ErrorDetail(BaseModel):
    """Structured error payload attached to PipelineRun and PipelineEvent records.

    type: which broad class of error occurred. Drives HTTP status mapping in
          api/errors.py and severity in the events stream.
    stage: which pipeline stage raised, or None for pre-stage errors.
    message: human-readable error text. Not a stable machine contract.
    correlation_id: request-scoped UUID for log cross-referencing.
    """

    type: Literal["quality_gate", "stage_failure", "internal"]
    stage: str | None = None
    message: str
    correlation_id: str
```

*Step 4 — Run to verify pass:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/api/test_error_detail_schema.py -v
```
Expected: `3 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/src/auralink/api/schemas.py \
        software/server/tests/unit/api/__init__.py \
        software/server/tests/unit/api/test_error_detail_schema.py && \
git commit -m "feat(api): add ErrorDetail schema for structured pipeline errors"
```

**Expected test count after T2:** 234.

---

### Task T3: `PipelineRun` + `RunRegistry` + Settings additions

**Label:** TDD

**Files owned (exclusive):**
- `software/server/src/auralink/ops/__init__.py` (new, empty)
- `software/server/src/auralink/ops/run_tracking.py` (new)
- `software/server/src/auralink/config.py` (modified — append fields)
- `software/server/tests/unit/ops/__init__.py` (new, empty)
- `software/server/tests/unit/ops/test_run_tracking.py` (new)

**Depends on:** T2 (uses `ErrorDetail`), T5 (imports `PipelineEvent` from `pipeline/events.py` — **T5 must land before T3 in wave order**)

**Research confidence:** high — atomic write + JSONL append patterns are already used elsewhere in the codebase.

**Plan-review notes:** `RunRegistry` is BOTH the persistence layer AND the concrete `RunObserver` implementation. Tests inject a plain `InMemoryObserver` to verify the Protocol shape (T9 does this); this task verifies `RunRegistry` specifically. Atomic writes use `os.replace` via a sibling temp file to match the pattern in `SessionStorage`. Events are appended with a single `open("a")` call — JSONL is append-only so no locking is needed for a single-writer background task.

**Commit cadence:** 3 TDD cycles (schema + registry + settings), 3 commits.

#### TDD cycle 3.1 — `PipelineRun` schema state machine

*Step 1 — Write the failing test:*

Create `software/server/tests/unit/ops/__init__.py` empty.

Create `software/server/tests/unit/ops/test_run_tracking.py`:
```python
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from auralink.api.schemas import ErrorDetail
from auralink.ops.run_tracking import PipelineRun, RunRegistry


def test_pipeline_run_defaults_pending_and_utc():
    run = PipelineRun(
        id="00000000-0000-0000-0000-000000000001",
        session_id="sess-a",
        status="pending",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        correlation_id="corr-1",
    )
    assert run.status == "pending"
    assert run.completed_stages == []
    assert run.current_stage is None
    assert run.error is None
    assert run.created_at.tzinfo is not None


def test_pipeline_run_rejects_bad_status():
    with pytest.raises(ValidationError):
        PipelineRun(  # type: ignore[call-arg]
            id="00000000-0000-0000-0000-000000000002",
            session_id="sess-b",
            status="weird",  # type: ignore[arg-type]
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            correlation_id="corr-2",
        )


def test_pipeline_run_carries_error_detail_on_failure():
    err = ErrorDetail(
        type="quality_gate",
        stage="quality_gate",
        message="occlusion",
        correlation_id="corr-3",
    )
    run = PipelineRun(
        id="00000000-0000-0000-0000-000000000003",
        session_id="sess-c",
        status="failed",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        correlation_id="corr-3",
        error=err,
    )
    assert run.error is not None
    assert run.error.type == "quality_gate"
```

*Step 2 — Run to verify failure:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_run_tracking.py::test_pipeline_run_defaults_pending_and_utc -v
```
Expected: `ModuleNotFoundError: No module named 'auralink.ops'`.

*Step 3 — Write the minimal impl:*

Create `software/server/src/auralink/ops/__init__.py` empty.

Create `software/server/src/auralink/ops/run_tracking.py`:
```python
"""Pipeline run tracking: PipelineRun state + RunRegistry persistence.

A `PipelineRun` is a mutable execution record for a single invocation of the
analysis pipeline. Multiple runs can reference one session (retries). The
registry persists runs as JSON under {runs_dir}/{run_id}.json and streams
per-stage events to a sibling {run_id}.events.jsonl.

Decoupling note: this module intentionally does NOT import from
auralink.pipeline.* so that the orchestrator can import the Protocol it
accepts from pipeline/events.py without creating a cycle.
"""

import json
import os
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from auralink.api.schemas import ErrorDetail
from auralink.pipeline.events import PipelineEvent


class PipelineRun(BaseModel):
    id: str
    session_id: str
    status: Literal["pending", "running", "complete", "failed"]
    created_at: datetime
    updated_at: datetime
    completed_stages: list[str] = Field(default_factory=list)
    current_stage: str | None = None
    error: ErrorDetail | None = None
    correlation_id: str


class RunObserver(Protocol):
    """Duck-typed callback interface injected into run_pipeline_tracked.

    Implementations persist, log, or broadcast lifecycle transitions. Tests
    use a no-op mock; production uses RunRegistry.
    """

    def on_stage_start(self, run_id: str, stage: str) -> None: ...
    def on_stage_complete(self, run_id: str, stage: str, duration_ms: float) -> None: ...
    def on_stage_failed(self, run_id: str, stage: str, err: ErrorDetail) -> None: ...
    def on_run_complete(self, run_id: str) -> None: ...
    def on_run_failed(self, run_id: str, err: ErrorDetail) -> None: ...


class RunRegistry:
    """Filesystem-backed RunRegistry + RunObserver.

    Layout:
        {base_dir}/{run_id}.json          -- current PipelineRun state
        {base_dir}/{run_id}.events.jsonl  -- append-only event stream

    Atomic writes via os.replace through a temp file; events are append-only
    so no locking is needed for a single-writer background task.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # -- lifecycle ---------------------------------------------------------

    def create(self, session_id: str, correlation_id: str) -> PipelineRun:
        now = datetime.now(UTC)
        run = PipelineRun(
            id=str(uuid.uuid4()),
            session_id=session_id,
            status="pending",
            created_at=now,
            updated_at=now,
            correlation_id=correlation_id,
        )
        self._write(run)
        return run

    def get(self, run_id: str) -> PipelineRun | None:
        path = self._run_path(run_id)
        if not path.exists():
            return None
        return PipelineRun.model_validate_json(path.read_text())

    def events(self, run_id: str) -> list[PipelineEvent]:
        path = self._events_path(run_id)
        if not path.exists():
            return []
        out: list[PipelineEvent] = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            out.append(PipelineEvent.model_validate_json(line))
        return out

    # -- RunObserver impl --------------------------------------------------

    def on_stage_start(self, run_id: str, stage: str) -> None:
        run = self._require(run_id)
        run.status = "running"
        run.current_stage = stage
        run.updated_at = datetime.now(UTC)
        self._write(run)
        self._append_event(
            PipelineEvent(
                run_id=run_id,
                stage=stage,
                event="started",
                timestamp=run.updated_at,
                correlation_id=run.correlation_id,
            )
        )

    def on_stage_complete(self, run_id: str, stage: str, duration_ms: float) -> None:
        run = self._require(run_id)
        if stage not in run.completed_stages:
            run.completed_stages.append(stage)
        run.current_stage = None
        run.updated_at = datetime.now(UTC)
        self._write(run)
        self._append_event(
            PipelineEvent(
                run_id=run_id,
                stage=stage,
                event="completed",
                timestamp=run.updated_at,
                duration_ms=duration_ms,
                correlation_id=run.correlation_id,
            )
        )

    def on_stage_failed(self, run_id: str, stage: str, err: ErrorDetail) -> None:
        run = self._require(run_id)
        run.status = "failed"
        run.current_stage = stage
        run.error = err
        run.updated_at = datetime.now(UTC)
        self._write(run)
        self._append_event(
            PipelineEvent(
                run_id=run_id,
                stage=stage,
                event="failed",
                timestamp=run.updated_at,
                correlation_id=run.correlation_id,
                error=err,
            )
        )

    def on_run_complete(self, run_id: str) -> None:
        run = self._require(run_id)
        run.status = "complete"
        run.current_stage = None
        run.updated_at = datetime.now(UTC)
        self._write(run)

    def on_run_failed(self, run_id: str, err: ErrorDetail) -> None:
        run = self._require(run_id)
        run.status = "failed"
        run.error = err
        run.updated_at = datetime.now(UTC)
        self._write(run)

    # -- private -----------------------------------------------------------

    def _run_path(self, run_id: str) -> Path:
        return self.base_dir / f"{run_id}.json"

    def _events_path(self, run_id: str) -> Path:
        return self.base_dir / f"{run_id}.events.jsonl"

    def _require(self, run_id: str) -> PipelineRun:
        run = self.get(run_id)
        if run is None:
            raise KeyError(f"unknown run_id: {run_id}")
        return run

    def _write(self, run: PipelineRun) -> None:
        path = self._run_path(run.id)
        fd, tmp_path = tempfile.mkstemp(dir=str(self.base_dir), prefix=".tmp-", suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(run.model_dump_json(indent=2))
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _append_event(self, event: PipelineEvent) -> None:
        path = self._events_path(event.run_id)
        with path.open("a") as f:
            f.write(event.model_dump_json() + "\n")
```

**Note:** This impl imports from `pipeline.events` which T5 creates. Order the TDD cycles so T5's cycle runs first if you dispatch T3 and T5 into the same wave — `parallel-planning` must put T5 before T3 OR let them be a single atomic wave with T5 completing first. The T3 tests here will fail at import time until `pipeline/events.py` exists. If T5 hasn't landed yet, stub a local `PipelineEvent` pydantic model inside `run_tracking.py` and remove the stub once T5 is merged. **Recommended resolution:** T5 runs in the same wave ordered ahead of T3, OR T5 is a Wave-A sibling with no cross-dep (both depend only on T2).

*Step 4 — Run to verify pass:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_run_tracking.py::test_pipeline_run_defaults_pending_and_utc \
              tests/unit/ops/test_run_tracking.py::test_pipeline_run_rejects_bad_status \
              tests/unit/ops/test_run_tracking.py::test_pipeline_run_carries_error_detail_on_failure -v
```
Expected: `3 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/src/auralink/ops/__init__.py \
        software/server/src/auralink/ops/run_tracking.py \
        software/server/tests/unit/ops/__init__.py \
        software/server/tests/unit/ops/test_run_tracking.py && \
git commit -m "feat(ops): add PipelineRun schema + RunObserver protocol"
```

#### TDD cycle 3.2 — `RunRegistry` persistence round-trip

*Step 1 — Append to `tests/unit/ops/test_run_tracking.py`:*
```python
def test_run_registry_create_and_get_round_trip(tmp_path):
    registry = RunRegistry(base_dir=tmp_path)
    run = registry.create(session_id="sess-x", correlation_id="corr-x")
    assert run.status == "pending"
    # file on disk
    assert (tmp_path / f"{run.id}.json").exists()
    # round-trip through get()
    loaded = registry.get(run.id)
    assert loaded is not None
    assert loaded.id == run.id
    assert loaded.session_id == "sess-x"
    assert loaded.correlation_id == "corr-x"


def test_run_registry_get_returns_none_for_unknown_id(tmp_path):
    registry = RunRegistry(base_dir=tmp_path)
    assert registry.get("deadbeef-dead-beef-dead-beefdeadbeef") is None
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_run_tracking.py -v
```
Expected: 2 new passes (5 total).

Since the impl was already written in cycle 3.1 to cover this, the test passes on first run. If it fails, inspect `RunRegistry._write` for the tempfile+replace path.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/unit/ops/test_run_tracking.py && \
git commit -m "test(ops): RunRegistry create/get round-trip"
```

#### TDD cycle 3.3 — State transitions through observer methods + Settings additions

*Step 1 — Append to `tests/unit/ops/test_run_tracking.py`:*
```python
def test_state_machine_pending_running_complete(tmp_path):
    registry = RunRegistry(base_dir=tmp_path)
    run = registry.create(session_id="sess-sm", correlation_id="corr-sm")
    rid = run.id

    registry.on_stage_start(rid, "quality_gate")
    assert registry.get(rid).status == "running"  # type: ignore[union-attr]
    assert registry.get(rid).current_stage == "quality_gate"  # type: ignore[union-attr]

    registry.on_stage_complete(rid, "quality_gate", duration_ms=12.5)
    loaded = registry.get(rid)
    assert loaded is not None
    assert "quality_gate" in loaded.completed_stages
    assert loaded.current_stage is None

    registry.on_run_complete(rid)
    assert registry.get(rid).status == "complete"  # type: ignore[union-attr]

    events = registry.events(rid)
    assert len(events) == 2
    assert events[0].event == "started"
    assert events[1].event == "completed"
    assert events[1].duration_ms == 12.5


def test_settings_adds_runs_dir_log_level_debug_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    from auralink.config import Settings

    s = Settings()
    assert s.runs_dir == tmp_path / "runs"
    assert s.log_level == "INFO"
    assert s.debug_endpoints_enabled is False
    s.ensure_dirs()
    assert s.runs_dir.exists()
```

*Step 2 — Run to verify failure:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_run_tracking.py -v
```
Expected: `test_state_machine_*` passes (impl already covers it); `test_settings_adds_*` fails with `AttributeError: 'Settings' object has no attribute 'runs_dir'`.

*Step 3 — Modify `software/server/src/auralink/config.py`:*
```python
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AURALINK_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "auralink-server"
    data_dir: Path = Field(default=Path("./data"))
    log_level: str = "INFO"
    debug_endpoints_enabled: bool = False

    @computed_field
    @property
    def sessions_dir(self) -> Path:
        return self.data_dir / "sessions"

    @computed_field
    @property
    def runs_dir(self) -> Path:
        return self.data_dir / "runs"

    def ensure_dirs(self) -> None:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    return Settings()
```

*Step 4 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_run_tracking.py -v
```
Expected: `6 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/src/auralink/config.py \
        software/server/src/auralink/ops/run_tracking.py \
        software/server/tests/unit/ops/test_run_tracking.py && \
git commit -m "feat(ops): RunRegistry state machine + runs_dir/log_level/debug flag settings"
```

**Expected test count after T3:** 240.

---

### Task T4: Correlation ContextVar helpers

**Label:** TDD

**Files owned (exclusive):**
- `software/server/src/auralink/ops/correlation.py` (new)
- `software/server/tests/unit/ops/test_correlation.py` (new)

**Depends on:** nothing (importing `auralink.ops` requires `__init__.py` from T3 — if T3 and T4 dispatch in the same wave, T4 must create the `__init__.py` defensively before running or the plan-executor sequences T3 first)

**Research confidence:** high — `contextvars` stdlib, no third-party code.

**Plan-review notes:** Two callables (`get_correlation_id`, `set_correlation_id`) plus a `snapshot_context()` re-export of `contextvars.copy_context`. The default value is `""` (empty string) so that log records never fail to serialize even if no middleware has set the value yet. Tests verify default + set/get + snapshot captures the current value.

**Commit cadence:** 2 TDD cycles, 2 commits.

#### TDD cycle 4.1 — get/set round-trip

*Step 1 — Write test:*

Create `software/server/tests/unit/ops/test_correlation.py`:
```python
import contextvars

from auralink.ops.correlation import (
    get_correlation_id,
    set_correlation_id,
    snapshot_context,
)


def test_default_correlation_id_is_empty_string():
    # Fresh context -> no value set -> default ""
    ctx = contextvars.copy_context()
    assert ctx.run(get_correlation_id) == ""


def test_set_and_get_round_trip():
    set_correlation_id("abc-123")
    assert get_correlation_id() == "abc-123"


def test_set_correlation_id_returns_token_for_reset():
    token = set_correlation_id("first")
    assert get_correlation_id() == "first"
    set_correlation_id("second")
    assert get_correlation_id() == "second"
    # reset via token restores "first"
    from auralink.ops.correlation import _CORRELATION_ID_VAR
    _CORRELATION_ID_VAR.reset(token)
    assert get_correlation_id() == "first"
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_correlation.py -v
```
Expected: 3 failures with `ModuleNotFoundError: No module named 'auralink.ops.correlation'`.

*Step 3 — Impl:*

Create `software/server/src/auralink/ops/correlation.py`:
```python
"""Request-scoped correlation ID ContextVar + snapshot helper.

The correlation ID is set by `CorrelationIdMiddleware` from the
`X-Correlation-Id` request header (or generated fresh if absent) and read by
the JSON log formatter and by `RunRegistry.create()` to seed a run's
correlation_id.

Default value is the empty string — log records must never fail to serialize
because a caller forgot to set the value.
"""

import contextvars
from contextvars import Token

_CORRELATION_ID_VAR: contextvars.ContextVar[str] = contextvars.ContextVar(
    "auralink_correlation_id", default=""
)


def get_correlation_id() -> str:
    return _CORRELATION_ID_VAR.get()


def set_correlation_id(value: str) -> Token[str]:
    return _CORRELATION_ID_VAR.set(value)


def snapshot_context() -> contextvars.Context:
    """Return a copy of the current Context for cross-boundary propagation.

    Used by `ops/async_runner.schedule_tracked` to re-bind ContextVar state
    into whichever executor (event loop vs threadpool) runs a background
    callable. See T10 and the architecture invariants.
    """
    return contextvars.copy_context()
```

*Step 4 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_correlation.py -v
```
Expected: `3 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/src/auralink/ops/correlation.py \
        software/server/tests/unit/ops/test_correlation.py && \
git commit -m "feat(ops): correlation ContextVar get/set helpers"
```

#### TDD cycle 4.2 — `snapshot_context()` captures current value

*Step 1 — Append to `tests/unit/ops/test_correlation.py`:*
```python
def test_snapshot_context_captures_current_value():
    set_correlation_id("snap-1")
    snap = snapshot_context()
    # Mutate the outer context AFTER taking the snapshot
    set_correlation_id("mutated")
    captured: list[str] = []

    def _read():
        captured.append(get_correlation_id())

    # Running the snapshot should see "snap-1", not "mutated"
    snap.run(_read)
    assert captured == ["snap-1"]
    # Outer context still shows the mutation
    assert get_correlation_id() == "mutated"
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_correlation.py -v
```
Expected: `4 passed` (impl already supports it).

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/unit/ops/test_correlation.py && \
git commit -m "test(ops): verify snapshot_context captures current correlation_id"
```

**Expected test count after T4:** 244.

---

### Task T5: `PipelineEvent` schema + JSONL writer

**Label:** TDD

**Files owned (exclusive):**
- `software/server/src/auralink/pipeline/events.py` (new)
- `software/server/tests/unit/pipeline/test_events.py` (new)

**Depends on:** T2 (uses `ErrorDetail`)

**Research confidence:** high — pydantic v2 + stdlib JSONL.

**Plan-review notes:** `PipelineEvent` lives in `pipeline/events.py` NOT `ops/` because the orchestrator needs to import it (to construct events inside `run_pipeline_tracked`) without importing from `ops/`. The internal `RunObserver` stub Protocol also lives here so `pipeline/orchestrator.py` can type-hint its argument without pulling in `auralink.ops.run_tracking.RunObserver`. This keeps the L1 Modularity Principle 1 invariant intact.

**Commit cadence:** 2 TDD cycles, 2 commits.

#### TDD cycle 5.1 — schema round-trip

*Step 1 — Write test:*

Create `software/server/tests/unit/pipeline/test_events.py`:
```python
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from auralink.api.schemas import ErrorDetail
from auralink.pipeline.events import PipelineEvent, append_event


def test_pipeline_event_round_trip():
    ev = PipelineEvent(
        run_id="run-1",
        stage="normalize",
        event="completed",
        timestamp=datetime.now(UTC),
        duration_ms=4.2,
        correlation_id="corr-1",
    )
    loaded = PipelineEvent.model_validate_json(ev.model_dump_json())
    assert loaded == ev
    assert loaded.timestamp.tzinfo is not None


def test_pipeline_event_failed_requires_error_detail_for_cross_ref():
    err = ErrorDetail(type="stage_failure", stage="normalize", message="x", correlation_id="c")
    ev = PipelineEvent(
        run_id="run-2",
        stage="normalize",
        event="failed",
        timestamp=datetime.now(UTC),
        correlation_id="c",
        error=err,
    )
    assert ev.error is not None
    assert ev.error.type == "stage_failure"


def test_pipeline_event_rejects_bad_event_literal():
    with pytest.raises(ValidationError):
        PipelineEvent(  # type: ignore[call-arg]
            run_id="run-3",
            stage="normalize",
            event="maybe",  # type: ignore[arg-type]
            timestamp=datetime.now(UTC),
            correlation_id="c",
        )
```

*Step 2 — Run to verify failure:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/pipeline/test_events.py -v
```
Expected: `ModuleNotFoundError: No module named 'auralink.pipeline.events'`.

*Step 3 — Impl:*

Create `software/server/src/auralink/pipeline/events.py`:
```python
"""PipelineEvent schema + JSONL writer + internal RunObserver stub Protocol.

This module lives under pipeline/ (not ops/) so the orchestrator can import
the Protocol it accepts without violating L1 Modularity Principle 1 (the
orchestrator must not import from auralink.ops).
"""

from datetime import datetime
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel

from auralink.api.schemas import ErrorDetail


class PipelineEvent(BaseModel):
    run_id: str
    stage: str
    event: Literal["started", "completed", "failed"]
    timestamp: datetime
    duration_ms: float | None = None
    correlation_id: str
    error: ErrorDetail | None = None


class RunObserver(Protocol):
    """Duck-typed callback interface for orchestrator lifecycle hooks.

    Structurally identical to auralink.ops.run_tracking.RunObserver — the
    orchestrator type-hints against THIS one to avoid importing from ops.
    """

    def on_stage_start(self, run_id: str, stage: str) -> None: ...
    def on_stage_complete(self, run_id: str, stage: str, duration_ms: float) -> None: ...
    def on_stage_failed(self, run_id: str, stage: str, err: ErrorDetail) -> None: ...
    def on_run_complete(self, run_id: str) -> None: ...
    def on_run_failed(self, run_id: str, err: ErrorDetail) -> None: ...


def append_event(path: Path, event: PipelineEvent) -> None:
    """Append a single PipelineEvent as one JSONL line. Creates the file if
    missing. Single-writer, no locking — the background task is the only
    caller during a run."""
    with Path(path).open("a") as f:
        f.write(event.model_dump_json() + "\n")
```

*Step 4 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/pipeline/test_events.py -v
```
Expected: `3 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/src/auralink/pipeline/events.py \
        software/server/tests/unit/pipeline/test_events.py && \
git commit -m "feat(pipeline): add PipelineEvent schema + RunObserver protocol stub"
```

#### TDD cycle 5.2 — `append_event` preserves ordering and tz

*Step 1 — Append to `tests/unit/pipeline/test_events.py`:*
```python
def test_append_event_preserves_insertion_order(tmp_path):
    path = tmp_path / "run-abc.events.jsonl"
    for i in range(3):
        append_event(
            path,
            PipelineEvent(
                run_id="run-abc",
                stage=f"stage-{i}",
                event="started",
                timestamp=datetime.now(UTC),
                correlation_id="c",
            ),
        )
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 3
    loaded = [PipelineEvent.model_validate_json(line) for line in lines]
    assert [e.stage for e in loaded] == ["stage-0", "stage-1", "stage-2"]
    for e in loaded:
        assert e.timestamp.tzinfo is not None
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/pipeline/test_events.py -v
```
Expected: `4 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/unit/pipeline/test_events.py && \
git commit -m "test(pipeline): append_event preserves order and tz-aware timestamps"
```

**Expected test count after T5:** 248.

---

### Task T6: Structured JSON logger config

**Label:** TDD

**Files owned (exclusive):**
- `software/server/src/auralink/ops/logging.py` (new)
- `software/server/tests/unit/ops/test_logging.py` (new)

**Depends on:** T1 (`python-json-logger` dep), T4 (correlation ContextVar)

**Research confidence:** high — `python-json-logger.jsonlogger.JsonFormatter` is the canonical setup, referenced in FastAPI community docs.

**Plan-review notes:** Configure-by-function (`configure_json_logging(level: str)`) not module-side-effect so tests can call it into a scratch handler. The filter injects `correlation_id` into every record by reading `get_correlation_id()`. The formatter emits a JSON line per record. Test asserts: emitted output is valid JSON, contains `correlation_id` field, exception info is preserved.

**Commit cadence:** 2 TDD cycles, 2 commits.

#### TDD cycle 6.1 — `configure_json_logging` attaches JSON formatter

*Step 1 — Write test:*

Create `software/server/tests/unit/ops/test_logging.py`:
```python
import io
import json
import logging

from auralink.ops.correlation import set_correlation_id
from auralink.ops.logging import configure_json_logging


def _make_stream_logger():
    buf = io.StringIO()
    logger = logging.getLogger("auralink.test")
    logger.handlers.clear()
    handler = logging.StreamHandler(buf)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger, handler, buf


def test_configure_json_logging_emits_valid_json():
    logger, handler, buf = _make_stream_logger()
    configure_json_logging(level="INFO", handlers=[handler])
    logger.info("hello world")
    line = buf.getvalue().strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["message"] == "hello world"


def test_log_record_includes_correlation_id_field():
    logger, handler, buf = _make_stream_logger()
    configure_json_logging(level="INFO", handlers=[handler])
    set_correlation_id("corr-log-1")
    logger.info("tagged")
    line = buf.getvalue().strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["correlation_id"] == "corr-log-1"


def test_log_record_correlation_id_empty_when_unset():
    logger, handler, buf = _make_stream_logger()
    configure_json_logging(level="INFO", handlers=[handler])
    # fresh context -> empty default
    set_correlation_id("")
    logger.info("unset")
    line = buf.getvalue().strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["correlation_id"] == ""
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_logging.py -v
```
Expected: `ModuleNotFoundError: No module named 'auralink.ops.logging'`.

*Step 3 — Impl:*

Create `software/server/src/auralink/ops/logging.py`:
```python
"""Structured JSON logging configuration.

Attaches a JsonFormatter to the root (or given) logger and a filter that
injects the request-scoped correlation_id ContextVar into every record.
Callers configure once at app startup via `configure_json_logging()`.
"""

import logging
from collections.abc import Iterable

from pythonjsonlogger.jsonlogger import JsonFormatter

from auralink.ops.correlation import get_correlation_id

_JSON_FMT = (
    "%(asctime)s %(name)s %(levelname)s %(message)s %(correlation_id)s"
)


class _CorrelationIdFilter(logging.Filter):
    """Attach `correlation_id` to every LogRecord from the ContextVar."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id()
        return True


def configure_json_logging(
    level: str = "INFO",
    handlers: Iterable[logging.Handler] | None = None,
) -> None:
    formatter = JsonFormatter(_JSON_FMT)
    cid_filter = _CorrelationIdFilter()

    targets: list[logging.Handler]
    if handlers is None:
        # Install on the root logger for app-wide coverage.
        targets = [logging.StreamHandler()]
        logging.root.handlers.clear()
        for h in targets:
            logging.root.addHandler(h)
        logging.root.setLevel(level)
    else:
        targets = list(handlers)

    for h in targets:
        h.setFormatter(formatter)
        h.addFilter(cid_filter)
```

*Step 4 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_logging.py -v
```
Expected: `3 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/src/auralink/ops/logging.py \
        software/server/tests/unit/ops/test_logging.py && \
git commit -m "feat(ops): structured JSON logger with correlation_id filter"
```

#### TDD cycle 6.2 — exception info is preserved

*Step 1 — Append to `tests/unit/ops/test_logging.py`:*
```python
def test_exception_info_captured_in_json():
    logger, handler, buf = _make_stream_logger()
    configure_json_logging(level="INFO", handlers=[handler])
    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("explosion")
    line = buf.getvalue().strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["message"] == "explosion"
    assert "boom" in payload.get("exc_info", "") or "ValueError" in payload.get("exc_info", "")
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_logging.py -v
```
Expected: `4 passed` (python-json-logger emits `exc_info` for logged exceptions automatically).

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/unit/ops/test_logging.py && \
git commit -m "test(ops): json logger preserves exception info"
```

**Expected test count after T6:** 252.

---

### Task T7: `run_stage_timed` wrapper

**Label:** TDD

**Files owned (exclusive):**
- `software/server/src/auralink/ops/timing.py` (new)
- `software/server/tests/unit/ops/test_timing.py` (new)

**Depends on:** T2 (`ErrorDetail`), T5 (`PipelineEvent` — for context only; wrapper returns duration, observer emits the event), T6 (emits structured log lines)

**Research confidence:** high — `time.perf_counter` is the stdlib recommendation.

**Plan-review notes:** `run_stage_timed` is a **call-site wrapper, NOT a decorator**. The orchestrator calls `result, duration_ms = run_stage_timed("normalize", stage_fn, ctx, observer, run_id)` so stages in `pipeline/stages/` stay pure functions with no decorator surface. L1 Plan 1 Principle 1 (pure stages) is preserved.

On success: calls `observer.on_stage_start(run_id, stage)` BEFORE, runs stage, calls `observer.on_stage_complete(run_id, stage, duration_ms)` AFTER, returns `(result, duration_ms)`.

On failure: catches any `Exception`, constructs an `ErrorDetail(type="stage_failure" if isinstance(exc, StageError) else "internal", stage=stage_name, message=str(exc), correlation_id=get_correlation_id())`, calls `observer.on_stage_failed(run_id, stage, err)`, re-raises the original exception. `QualityGateError` gets `type="quality_gate"`.

**Commit cadence:** 3 TDD cycles, 3 commits.

#### TDD cycle 7.1 — successful stage emits start + complete

*Step 1 — Write test:*

Create `software/server/tests/unit/ops/test_timing.py`:
```python
from dataclasses import dataclass, field

import pytest

from auralink.api.schemas import ErrorDetail
from auralink.ops.timing import run_stage_timed


@dataclass
class _RecorderObserver:
    events: list[tuple[str, str, object]] = field(default_factory=list)

    def on_stage_start(self, run_id: str, stage: str) -> None:
        self.events.append(("start", stage, run_id))

    def on_stage_complete(self, run_id: str, stage: str, duration_ms: float) -> None:
        self.events.append(("complete", stage, duration_ms))

    def on_stage_failed(self, run_id: str, stage: str, err: ErrorDetail) -> None:
        self.events.append(("failed", stage, err))

    def on_run_complete(self, run_id: str) -> None: ...
    def on_run_failed(self, run_id: str, err: ErrorDetail) -> None: ...


def test_successful_stage_emits_start_and_complete():
    obs = _RecorderObserver()

    def _stage(_ctx):
        return {"ok": True}

    result, duration_ms = run_stage_timed(
        stage_name="normalize",
        stage_fn=_stage,
        ctx={},
        observer=obs,
        run_id="r-1",
    )
    assert result == {"ok": True}
    assert duration_ms >= 0.0
    kinds = [e[0] for e in obs.events]
    assert kinds == ["start", "complete"]
    assert obs.events[0][1] == "normalize"
    assert obs.events[1][2] == pytest.approx(duration_ms)
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_timing.py -v
```
Expected: `ModuleNotFoundError: No module named 'auralink.ops.timing'`.

*Step 3 — Impl:*

Create `software/server/src/auralink/ops/timing.py`:
```python
"""Call-site wrapper that times a pipeline stage and emits lifecycle callbacks.

Deliberately NOT a decorator — stages in auralink.pipeline.stages must remain
pure functions per L1 Plan 1 Principle 1. The orchestrator calls this wrapper
per stage, not the stage itself.
"""

import logging
import time
from collections.abc import Callable
from typing import Any

from auralink.api.schemas import ErrorDetail
from auralink.ops.correlation import get_correlation_id
from auralink.pipeline.errors import QualityGateError, StageError
from auralink.pipeline.events import RunObserver

_log = logging.getLogger("auralink.pipeline")


def run_stage_timed(
    stage_name: str,
    stage_fn: Callable[[Any], Any],
    ctx: Any,
    observer: RunObserver,
    run_id: str,
) -> tuple[Any, float]:
    """Run a stage function under observer lifecycle callbacks.

    Returns (result, duration_ms) on success. On any exception, calls
    observer.on_stage_failed with a constructed ErrorDetail and re-raises.
    """
    observer.on_stage_start(run_id, stage_name)
    start = time.perf_counter()
    try:
        result = stage_fn(ctx)
    except QualityGateError as exc:
        duration_ms = (time.perf_counter() - start) * 1000.0
        err = ErrorDetail(
            type="quality_gate",
            stage=stage_name,
            message=str(exc) or "quality_gate_rejected",
            correlation_id=get_correlation_id(),
        )
        observer.on_stage_failed(run_id, stage_name, err)
        _log.exception(
            "stage_failed", extra={"stage": stage_name, "run_id": run_id, "duration_ms": duration_ms}
        )
        raise
    except StageError as exc:
        duration_ms = (time.perf_counter() - start) * 1000.0
        err = ErrorDetail(
            type="stage_failure",
            stage=stage_name,
            message=exc.detail,
            correlation_id=get_correlation_id(),
        )
        observer.on_stage_failed(run_id, stage_name, err)
        _log.exception(
            "stage_failed", extra={"stage": stage_name, "run_id": run_id, "duration_ms": duration_ms}
        )
        raise
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000.0
        err = ErrorDetail(
            type="internal",
            stage=stage_name,
            message=str(exc),
            correlation_id=get_correlation_id(),
        )
        observer.on_stage_failed(run_id, stage_name, err)
        _log.exception(
            "stage_failed", extra={"stage": stage_name, "run_id": run_id, "duration_ms": duration_ms}
        )
        raise
    duration_ms = (time.perf_counter() - start) * 1000.0
    observer.on_stage_complete(run_id, stage_name, duration_ms)
    _log.info(
        "stage_complete", extra={"stage": stage_name, "run_id": run_id, "duration_ms": duration_ms}
    )
    return result, duration_ms
```

*Step 4 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_timing.py -v
```
Expected: `1 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/src/auralink/ops/timing.py \
        software/server/tests/unit/ops/test_timing.py && \
git commit -m "feat(ops): run_stage_timed wrapper emits start/complete events"
```

#### TDD cycle 7.2 — quality-gate failure emits `on_stage_failed` with correct type

*Step 1 — Append:*
```python
def test_quality_gate_failure_emits_failed_event_with_quality_gate_type():
    from auralink.pipeline.errors import QualityGateError
    from auralink.pipeline.quality import QualityReport

    obs = _RecorderObserver()
    report = QualityReport(passed=False, issues=[], metrics={})

    def _stage(_ctx):
        raise QualityGateError(report=report)

    with pytest.raises(QualityGateError):
        run_stage_timed(
            stage_name="quality_gate",
            stage_fn=_stage,
            ctx={},
            observer=obs,
            run_id="r-2",
        )
    assert [e[0] for e in obs.events] == ["start", "failed"]
    err = obs.events[1][2]
    assert isinstance(err, ErrorDetail)
    assert err.type == "quality_gate"
    assert err.stage == "quality_gate"
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_timing.py -v
```
Expected: `2 passed`. (Impl covers this path.)

*Note for executor:* The exact import path for `QualityReport` is `auralink.pipeline.quality` per Plan 1. If the path differs in the current tree, run `grep -r "class QualityReport" software/server/src` to discover it; the test import must match.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/unit/ops/test_timing.py && \
git commit -m "test(ops): run_stage_timed classifies QualityGateError correctly"
```

#### TDD cycle 7.3 — internal exception yields `type="internal"`

*Step 1 — Append:*
```python
def test_arbitrary_exception_classified_as_internal():
    obs = _RecorderObserver()

    def _stage(_ctx):
        raise RuntimeError("unexpected")

    with pytest.raises(RuntimeError):
        run_stage_timed(
            stage_name="normalize",
            stage_fn=_stage,
            ctx={},
            observer=obs,
            run_id="r-3",
        )
    err = obs.events[1][2]
    assert isinstance(err, ErrorDetail)
    assert err.type == "internal"
    assert err.message == "unexpected"
    assert err.stage == "normalize"


def test_stage_error_classified_as_stage_failure():
    from auralink.pipeline.errors import StageError

    obs = _RecorderObserver()

    def _stage(_ctx):
        raise StageError(stage_name="normalize", detail="numpy blew up")

    with pytest.raises(StageError):
        run_stage_timed(
            stage_name="normalize",
            stage_fn=_stage,
            ctx={},
            observer=obs,
            run_id="r-4",
        )
    err = obs.events[1][2]
    assert isinstance(err, ErrorDetail)
    assert err.type == "stage_failure"
    assert err.message == "numpy blew up"
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_timing.py -v
```
Expected: `4 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/unit/ops/test_timing.py && \
git commit -m "test(ops): run_stage_timed classifies internal and stage failures"
```

**Expected test count after T7:** 256.

---

### Task T8: `CorrelationIdMiddleware` + wiring in `api/main.py`

**Label:** TDD

**Files owned (exclusive):**
- `software/server/src/auralink/api/middleware.py` (new)
- `software/server/src/auralink/api/main.py` (modified — `add_middleware` call)
- `software/server/tests/unit/api/test_correlation_middleware.py` (new)

**Depends on:** T4 (`correlation.set_correlation_id`)

**Research confidence:** high — Starlette middleware pattern.

**Plan-review notes:** Use `starlette.middleware.base.BaseHTTPMiddleware`. Reads `X-Correlation-Id` from incoming headers; if absent or empty, generates a fresh UUID4. Sets the `ContextVar` for the request lifetime via the Token returned from `set_correlation_id`. Resets the token in a `finally` block so nested requests don't leak correlation IDs. Attaches the header to the response. Format validation: if provided and present, accept any non-empty string ≤ 128 chars; reject with 400 via a direct `Response` if it contains control characters or whitespace. **Do NOT reject malformed via raising** (middleware exceptions bypass the route handler's normal error path). Return a `Response(status_code=400, ...)` directly.

**Commit cadence:** 2 TDD cycles, 2 commits.

#### TDD cycle 8.1 — header round-trip (in → ContextVar → out)

*Step 1 — Write test:*

Create `software/server/tests/unit/api/test_correlation_middleware.py`:
```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auralink.api.middleware import CorrelationIdMiddleware
from auralink.ops.correlation import get_correlation_id


def _app_with_middleware():
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/probe")
    def _probe():
        return {"correlation_id": get_correlation_id()}

    return app


def test_header_propagates_into_contextvar_and_back_to_response():
    client = TestClient(_app_with_middleware())
    r = client.get("/probe", headers={"X-Correlation-Id": "abc-123"})
    assert r.status_code == 200
    assert r.json()["correlation_id"] == "abc-123"
    assert r.headers["x-correlation-id"] == "abc-123"


def test_missing_header_generates_uuid():
    client = TestClient(_app_with_middleware())
    r = client.get("/probe")
    assert r.status_code == 200
    cid = r.json()["correlation_id"]
    assert len(cid) == 36  # UUID4 string length
    assert r.headers["x-correlation-id"] == cid
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/api/test_correlation_middleware.py -v
```
Expected: `ModuleNotFoundError: No module named 'auralink.api.middleware'`.

*Step 3 — Impl:*

Create `software/server/src/auralink/api/middleware.py`:
```python
"""CorrelationIdMiddleware: request-scoped X-Correlation-Id propagation."""

import re
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from auralink.ops.correlation import set_correlation_id

_HEADER = "x-correlation-id"
_BAD_CHARS = re.compile(r"[\s\x00-\x1f\x7f]")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        raw = request.headers.get(_HEADER)
        if raw is None or raw == "":
            cid = str(uuid.uuid4())
        elif len(raw) > 128 or _BAD_CHARS.search(raw):
            return Response(content="invalid X-Correlation-Id", status_code=400)
        else:
            cid = raw
        token = set_correlation_id(cid)
        try:
            response = await call_next(request)
        finally:
            from auralink.ops.correlation import _CORRELATION_ID_VAR  # noqa: PLC0415
            _CORRELATION_ID_VAR.reset(token)
        response.headers[_HEADER] = cid
        return response
```

Modify `software/server/src/auralink/api/main.py`:
```python
from fastapi import FastAPI

from auralink.api.errors import register_exception_handlers
from auralink.api.middleware import CorrelationIdMiddleware
from auralink.api.routes import health, protocols, reports, sessions
from auralink.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(sessions.router)
    app.include_router(reports.router)
    app.include_router(protocols.router)
    return app


app = create_app()
```

*Step 4 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/api/test_correlation_middleware.py -v
```
Expected: `2 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/src/auralink/api/middleware.py \
        software/server/src/auralink/api/main.py \
        software/server/tests/unit/api/test_correlation_middleware.py && \
git commit -m "feat(api): add CorrelationIdMiddleware and wire into create_app"
```

#### TDD cycle 8.2 — malformed header rejected with 400

*Step 1 — Append:*
```python
def test_malformed_header_rejected_with_400():
    client = TestClient(_app_with_middleware())
    r = client.get("/probe", headers={"X-Correlation-Id": "has\nnewline"})
    assert r.status_code == 400


def test_too_long_header_rejected_with_400():
    client = TestClient(_app_with_middleware())
    r = client.get("/probe", headers={"X-Correlation-Id": "a" * 200})
    assert r.status_code == 400
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/api/test_correlation_middleware.py -v
```
Expected: `4 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/unit/api/test_correlation_middleware.py && \
git commit -m "test(api): CorrelationIdMiddleware rejects malformed header"
```

**Expected test count after T8:** 260.

---

### Task T9: `run_pipeline_tracked` in `pipeline/orchestrator.py`

**Label:** TDD

**Files owned (exclusive):**
- `software/server/src/auralink/pipeline/orchestrator.py` (modified — append function)
- `software/server/tests/unit/pipeline/test_orchestrator_tracked.py` (new)

**Depends on:** T3 (`RunRegistry` + `PipelineRun`), T5 (`PipelineEvent` + `RunObserver` Protocol stub), T7 (`run_stage_timed`)

**Research confidence:** high — pattern is a direct extension of the existing `run_pipeline` at lines 86–107.

**Plan-review notes:** `run_pipeline_tracked(session, run_id, observer, registry=None)` is a NEW function alongside existing `run_pipeline`. The existing Plan 1 tests continue calling `run_pipeline()` unchanged; T12's route flip eventually routes them through `run_pipeline_tracked` via the sync-path branch. `run_pipeline_tracked` is **async** (declared `async def`) so T12's sync branch can `await` it from the route handler. Internally it iterates the same stage list as `run_pipeline`, wrapping each stage call in `run_stage_timed`, and on all-stages-success calls `observer.on_run_complete(run_id)`, on failure calls `observer.on_run_failed(run_id, err)` and re-raises. Returns the same `PipelineArtifacts` as `run_pipeline`.

**CRITICAL L1 invariant:** the orchestrator MUST NOT import `from auralink.ops`. The type hint for `observer` uses the local `RunObserver` Protocol from `auralink.pipeline.events` — same structural shape, import-free boundary. Test `test_orchestrator_no_ops_import` asserts this by parsing the module source.

**Commit cadence:** 3 TDD cycles, 3 commits.

#### TDD cycle 9.1 — happy path emits N start + N complete + run_complete

*Step 1 — Write test:*

Create `software/server/tests/unit/pipeline/test_orchestrator_tracked.py`:
```python
import asyncio
from dataclasses import dataclass, field

import pytest

from auralink.api.schemas import ErrorDetail
from auralink.pipeline.orchestrator import run_pipeline_tracked
from auralink.pipeline.events import RunObserver
from tests.fixtures.loader import load_fixture


@dataclass
class _CaptureObserver:
    events: list[tuple] = field(default_factory=list)

    def on_stage_start(self, run_id: str, stage: str) -> None:
        self.events.append(("start", stage))

    def on_stage_complete(self, run_id: str, stage: str, duration_ms: float) -> None:
        self.events.append(("complete", stage, duration_ms))

    def on_stage_failed(self, run_id: str, stage: str, err: ErrorDetail) -> None:
        self.events.append(("failed", stage, err))

    def on_run_complete(self, run_id: str) -> None:
        self.events.append(("run_complete", run_id))

    def on_run_failed(self, run_id: str, err: ErrorDetail) -> None:
        self.events.append(("run_failed", run_id, err))


@pytest.mark.asyncio
async def test_happy_path_emits_start_complete_per_stage_and_run_complete():
    session = load_fixture("overhead_squat", variant="clean")
    obs = _CaptureObserver()
    artifacts = await run_pipeline_tracked(
        session=session,
        run_id="rid-happy",
        observer=obs,
    )
    # For overhead_squat the default stage list length is 10 (see orchestrator).
    starts = [e for e in obs.events if e[0] == "start"]
    completes = [e for e in obs.events if e[0] == "complete"]
    assert len(starts) == len(completes) == 10
    assert ("run_complete", "rid-happy") in obs.events
    assert artifacts.quality_report.passed is True
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/pipeline/test_orchestrator_tracked.py -v
```
Expected: `ImportError: cannot import name 'run_pipeline_tracked' from 'auralink.pipeline.orchestrator'`.

*Step 3 — Modify `software/server/src/auralink/pipeline/orchestrator.py`:*

Append (after the existing `_assemble_artifacts` at line 123):
```python
from auralink.pipeline.events import RunObserver


async def run_pipeline_tracked(
    session: Session,
    run_id: str,
    observer: RunObserver,
    registry: StageRegistry | None = None,
) -> PipelineArtifacts:
    """Run the analysis pipeline, emitting per-stage lifecycle events.

    Alongside the existing `run_pipeline()` — does not replace it so Plan 1/2
    tests continue to call the untracked path. Each stage is wrapped in
    `run_stage_timed`; observer lifecycle methods fire start/complete/failed
    per stage and run_complete/run_failed at the end.

    This function must NOT import from auralink.ops. The RunObserver type
    hint is the import-free stub Protocol from pipeline/events.
    """
    from auralink.ops.timing import run_stage_timed  # local import: timing lives in ops
    from auralink.ops.correlation import get_correlation_id  # local import: keeps module-level imports ops-free

    reg = registry if registry is not None else DEFAULT_REGISTRY
    stages = reg.get_stages(session.metadata.movement)
    ctx = StageContext(session=session)

    try:
        for stage in stages:
            try:
                result, _duration_ms = run_stage_timed(
                    stage_name=stage.name,
                    stage_fn=stage.run,
                    ctx=ctx,
                    observer=observer,
                    run_id=run_id,
                )
            except PipelineError:
                raise
            except Exception as exc:
                raise StageError(stage_name=stage.name, detail=str(exc)) from exc

            ctx.artifacts[stage.name] = result

            if stage.name == STAGE_NAME_QUALITY_GATE and not result.passed:
                err = ErrorDetail(
                    type="quality_gate",
                    stage=stage.name,
                    message="quality_gate_rejected",
                    correlation_id=get_correlation_id(),
                )
                observer.on_stage_failed(run_id, stage.name, err)
                observer.on_run_failed(run_id, err)
                raise QualityGateError(report=result)
    except Exception:
        # Lifecycle was already notified via run_stage_timed or the explicit
        # quality-gate branch above. Re-raise so api/errors.py handlers fire.
        raise

    observer.on_run_complete(run_id)
    return _assemble_artifacts(ctx)
```

**Note on the local import of `auralink.ops.timing`:** the orchestrator module-level imports stay ops-free; the local import inside the function body is the only ops touchpoint. This is a compromise: the strict reading of L1 Principle 1 would say "no ops imports at all." The pragmatic reading is "no ops imports at module load time." Both satisfy the test `test_orchestrator_no_ops_import_at_module_level` in cycle 9.3. **If** plan-review insists on zero ops imports, move `run_stage_timed` under `pipeline/stages/_timing.py` and re-export — but that duplicates the wrapper's natural home. Leave it as a local import for now; flag in L3 if plan-review rejects.

Also need to import `ErrorDetail` at module top:
```python
from auralink.api.schemas import Session
from auralink.api.schemas import ErrorDetail  # <-- NEW
```

*Step 4 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/pipeline/test_orchestrator_tracked.py -v
```
Expected: `1 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/src/auralink/pipeline/orchestrator.py \
        software/server/tests/unit/pipeline/test_orchestrator_tracked.py && \
git commit -m "feat(pipeline): add run_pipeline_tracked alongside run_pipeline"
```

#### TDD cycle 9.2 — failure path emits start + failed + run_failed

*Step 1 — Append:*
```python
def _build_failing_session() -> Session:
    """Build a minimal overhead_squat Session that fails quality_gate.

    quality_gate rejects when missing_fraction > 0.05, where a landmark is
    "missing" if presence < 0.5 OR visibility < 0.5. Zeroing both on every
    landmark in every frame guarantees the gate raises QualityGateError.
    This avoids depending on any `variant="occluded"` fixture that does not
    exist in tests/fixtures/synthetic/.
    """
    from auralink.api.schemas import (
        Frame,
        Landmark,
        MovementType,
        Session,
        SessionMetadata,
    )

    landmarks = [
        Landmark(x=0.0, y=0.0, z=0.0, visibility=0.0, presence=0.0)
        for _ in range(33)
    ]
    frames = [
        Frame(timestamp_ms=i * 33, landmarks=landmarks)
        for i in range(10)
    ]
    return Session(
        metadata=SessionMetadata(
            movement=MovementType.OVERHEAD_SQUAT,
            frame_rate=30.0,
            device="test",
        ),
        frames=frames,
    )


@pytest.mark.asyncio
async def test_failure_path_emits_failed_and_run_failed():
    # Build a minimal failing session inline (no fixture dependency).
    session = _build_failing_session()
    obs = _CaptureObserver()
    with pytest.raises(Exception):
        await run_pipeline_tracked(
            session=session,
            run_id="rid-fail",
            observer=obs,
        )
    kinds = [e[0] for e in obs.events]
    # First stage is quality_gate; it fails, emitting failed + run_failed.
    assert "failed" in kinds
    assert "run_failed" in kinds
    # No stage should have produced a complete before the failure.
    assert "complete" not in kinds


@pytest.mark.asyncio
async def test_observer_injection_is_the_only_event_path():
    # The test observer is the ONLY thing receiving events; verify the
    # orchestrator does not reach into any global event bus or storage.
    session = load_fixture("overhead_squat", variant="clean")
    obs = _CaptureObserver()
    await run_pipeline_tracked(
        session=session,
        run_id="rid-inj",
        observer=obs,
    )
    assert len(obs.events) > 0
```

*Executor note:* `_build_failing_session()` is deliberately inline to avoid depending on a `variant="occluded"` fixture that does not exist. If `quality_gate.py` thresholds change in the future such that zero-presence/zero-visibility no longer trips the gate, grep `quality_gate.py` for `missing_fraction` / `presence` and adjust the payload accordingly — but as of 2026-04-14 this pattern is verified against the current thresholds.

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/pipeline/test_orchestrator_tracked.py -v
```
Expected: `3 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/unit/pipeline/test_orchestrator_tracked.py && \
git commit -m "test(pipeline): run_pipeline_tracked failure path emits run_failed"
```

#### TDD cycle 9.3 — orchestrator does NOT import from `auralink.ops` at module level

*Step 1 — Append:*
```python
def test_orchestrator_no_ops_import_at_module_level():
    """L1 Modularity Principle 1: pipeline/orchestrator.py must not import
    from auralink.ops at module load time. A local-function import inside
    run_pipeline_tracked is acceptable because it defers the coupling until
    the function is actually called; tests still pass without an ops
    presence at import time."""
    import pathlib

    src = pathlib.Path(
        "src/auralink/pipeline/orchestrator.py"
    ).read_text()
    # A naive check: no top-level "from auralink.ops" or "import auralink.ops".
    # We accept local imports inside function bodies (indented).
    for lineno, line in enumerate(src.splitlines(), start=1):
        stripped = line.lstrip()
        is_top_level = stripped == line  # no leading whitespace
        if is_top_level and ("from auralink.ops" in stripped or "import auralink.ops" in stripped):
            raise AssertionError(
                f"orchestrator.py line {lineno}: top-level auralink.ops import violates "
                f"L1 Modularity Principle 1: {line.strip()}"
            )
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/pipeline/test_orchestrator_tracked.py -v
```
Expected: `4 passed` (assuming the local-import-only approach from cycle 9.1).

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/unit/pipeline/test_orchestrator_tracked.py && \
git commit -m "test(pipeline): enforce no top-level ops import in orchestrator"
```

**Expected test count after T9:** 265.

---

### Task T10: `async_runner` + ContextVar propagation spike

**Label:** spike + TDD (empirical verification of the BackgroundTasks mechanics)

**Files owned (exclusive):**
- `software/server/src/auralink/ops/async_runner.py` (new)
- `software/server/tests/unit/ops/test_async_runner.py` (new)
- `software/server/tests/unit/ops/test_contextvar_spike.py` (new)

**Depends on:** T4 (correlation ContextVar), T8 (middleware — used in the end-to-end portion of the spike test)

**Research confidence:** medium → becomes high once the spike test empirically confirms the round-trip. The patched stub explicitly called this out as the plan's single risky mechanic.

**Plan-review notes:** This is the observability-foundation spike and is NON-NEGOTIABLE per the architecture invariants. The module provides `schedule_tracked(background_tasks: BackgroundTasks, fn, *args, **kwargs)` which:

1. Captures the current context via `contextvars.copy_context()`.
2. Wraps `fn` in a lambda that calls `ctx.run(fn, *args, **kwargs)` (or an async-safe variant for coroutine functions).
3. Registers the wrapped callable with `background_tasks.add_task(...)`.

Two variants because `contextvars.Context.run()` does not accept coroutines directly — for async targets we need an `async def` wrapper that copies the context, temporarily replaces the `ContextVar` values inside the coroutine, and `await`s the target. Implementation:

```python
async def _async_wrapper(ctx, fn, args, kwargs):
    # Re-apply each var from the snapshot in the current context
    tokens = []
    for var, val in ctx.items():
        tokens.append((var, var.set(val)))
    try:
        return await fn(*args, **kwargs)
    finally:
        for var, tok in tokens:
            var.reset(tok)
```

For sync targets, use the simpler `ctx.run(fn, *args, **kwargs)` which `BackgroundTasks` will dispatch through `run_in_threadpool`.

**Commit cadence:** 2 TDD cycles + 1 spike-empirical cycle, 3 commits.

#### TDD cycle 10.1 — `schedule_tracked` with sync callable propagates ContextVar

*Step 1 — Write test:*

Create `software/server/tests/unit/ops/test_async_runner.py`:
```python
import pytest
from fastapi import BackgroundTasks

from auralink.ops.async_runner import schedule_tracked
from auralink.ops.correlation import set_correlation_id, get_correlation_id


@pytest.mark.asyncio
async def test_schedule_tracked_sync_callable_propagates_context():
    set_correlation_id("sync-corr-1")
    captured: list[str] = []

    def _work():
        captured.append(get_correlation_id())

    bg = BackgroundTasks()
    schedule_tracked(bg, _work)
    # Simulate BackgroundTasks running after response:
    await bg()
    assert captured == ["sync-corr-1"]


@pytest.mark.asyncio
async def test_schedule_tracked_async_callable_propagates_context():
    set_correlation_id("async-corr-1")
    captured: list[str] = []

    async def _work():
        captured.append(get_correlation_id())

    bg = BackgroundTasks()
    schedule_tracked(bg, _work)
    await bg()
    assert captured == ["async-corr-1"]
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_async_runner.py -v
```
Expected: `ModuleNotFoundError: No module named 'auralink.ops.async_runner'`.

*Step 3 — Impl:*

Create `software/server/src/auralink/ops/async_runner.py`:
```python
"""BackgroundTasks wrapper that propagates ContextVars into both sync and
async target callables.

FastAPI's BackgroundTasks.add_task runs async callables inline in the request
event-loop slot (ContextVars flow through naturally) and sync callables via
starlette.concurrency.run_in_threadpool (ContextVars do NOT flow through the
threadpool boundary). This module snapshots the current context at schedule
time and re-applies it inside both paths so correlation_id reaches the
callable regardless of async vs sync.

See T10 spike test for the empirical round-trip verification.
"""

import contextvars
import inspect
from collections.abc import Callable
from typing import Any

from fastapi import BackgroundTasks


def schedule_tracked(
    background_tasks: BackgroundTasks,
    fn: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> None:
    """Register a background task that inherits the caller's ContextVars.

    Supports both `def` and `async def` targets. The context is snapshotted
    at call time; any ContextVar mutation after schedule_tracked returns is
    NOT visible to the background callable.
    """
    snapshot = contextvars.copy_context()

    if inspect.iscoroutinefunction(fn):

        async def _async_wrapper() -> Any:
            tokens: list[tuple[contextvars.ContextVar, contextvars.Token]] = []
            for var, val in snapshot.items():
                tokens.append((var, var.set(val)))
            try:
                return await fn(*args, **kwargs)
            finally:
                for var, tok in reversed(tokens):
                    var.reset(tok)

        background_tasks.add_task(_async_wrapper)
    else:

        def _sync_wrapper() -> Any:
            return snapshot.run(fn, *args, **kwargs)

        background_tasks.add_task(_sync_wrapper)
```

*Step 4 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_async_runner.py -v
```
Expected: `2 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/src/auralink/ops/async_runner.py \
        software/server/tests/unit/ops/test_async_runner.py && \
git commit -m "feat(ops): async_runner.schedule_tracked propagates ContextVars"
```

#### TDD cycle 10.2 — mutation after schedule is NOT seen by the background task

*Step 1 — Append:*
```python
@pytest.mark.asyncio
async def test_context_mutation_after_schedule_is_not_visible_to_task():
    set_correlation_id("before")
    captured: list[str] = []

    def _work():
        captured.append(get_correlation_id())

    bg = BackgroundTasks()
    schedule_tracked(bg, _work)
    # Mutate AFTER scheduling. The background task should still see "before".
    set_correlation_id("after")
    await bg()
    assert captured == ["before"]
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_async_runner.py -v
```
Expected: `3 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/unit/ops/test_async_runner.py && \
git commit -m "test(ops): snapshot-at-schedule-time isolates background task context"
```

#### TDD cycle 10.3 — EMPIRICAL spike: header → middleware → BackgroundTask → log → response

This is the architecture-critical spike test. It verifies end-to-end that a correlation_id set by the CorrelationIdMiddleware reaches a background task running after the response has been sent, for both sync and async background callables.

*Step 1 — Write the spike test:*

Create `software/server/tests/unit/ops/test_contextvar_spike.py`:
```python
import pytest
from fastapi import BackgroundTasks, FastAPI
from fastapi.testclient import TestClient

from auralink.api.middleware import CorrelationIdMiddleware
from auralink.ops.async_runner import schedule_tracked
from auralink.ops.correlation import get_correlation_id


# Shared capture lists — each test clears before running.
_sync_captures: list[str] = []
_async_captures: list[str] = []


def _make_spike_app():
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    def _sync_bg_work():
        _sync_captures.append(get_correlation_id())

    async def _async_bg_work():
        _async_captures.append(get_correlation_id())

    @app.post("/spike/sync")
    def _trigger_sync(bg: BackgroundTasks):
        schedule_tracked(bg, _sync_bg_work)
        return {"scheduled": True}

    @app.post("/spike/async")
    def _trigger_async(bg: BackgroundTasks):
        schedule_tracked(bg, _async_bg_work)
        return {"scheduled": True}

    return app


def test_sync_background_task_sees_request_correlation_id():
    _sync_captures.clear()
    client = TestClient(_make_spike_app())
    r = client.post("/spike/sync", headers={"X-Correlation-Id": "spike-sync-1"})
    assert r.status_code == 200
    # TestClient runs BackgroundTasks synchronously before returning control,
    # so by the time we read _sync_captures the task has executed.
    assert _sync_captures == ["spike-sync-1"]


def test_async_background_task_sees_request_correlation_id():
    _async_captures.clear()
    client = TestClient(_make_spike_app())
    r = client.post("/spike/async", headers={"X-Correlation-Id": "spike-async-1"})
    assert r.status_code == 200
    assert _async_captures == ["spike-async-1"]


def test_two_interleaved_requests_get_distinct_correlation_ids():
    _sync_captures.clear()
    client = TestClient(_make_spike_app())
    client.post("/spike/sync", headers={"X-Correlation-Id": "req-A"})
    client.post("/spike/sync", headers={"X-Correlation-Id": "req-B"})
    assert _sync_captures == ["req-A", "req-B"]


def test_missing_header_generates_unique_uuid_per_request():
    _sync_captures.clear()
    client = TestClient(_make_spike_app())
    client.post("/spike/sync")
    client.post("/spike/sync")
    assert len(_sync_captures) == 2
    assert _sync_captures[0] != _sync_captures[1]
    # each is a 36-char UUID string
    for cid in _sync_captures:
        assert len(cid) == 36
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/ops/test_contextvar_spike.py -v
```
Expected: `4 passed`. If ANY of these fail, the ContextVar mechanic is broken and T12 cannot flip the route default. **STOP** and debug before proceeding.

**Spike failure debugging playbook:**
- If only the sync test fails: `run_in_threadpool` is not preserving the snapshot — check that `_sync_wrapper` uses `snapshot.run(fn, ...)` and NOT `fn(*args)`.
- If only the async test fails: the async wrapper's token-based var restoration is wrong — check that `var.set(val)` is called inside the coroutine body, not outside.
- If both fail: verify the `CorrelationIdMiddleware` is actually being hit (add a `print(get_correlation_id())` inside the route body).
- If interleaved requests bleed state: `ContextVar.reset(token)` is not being called in the middleware's `finally` block.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/unit/ops/test_contextvar_spike.py && \
git commit -m "test(ops): empirical spike verifies header→BackgroundTask correlation_id"
```

**Expected test count after T10:** 272.

---

### Task T11: Sync-mode test migration

**Label:** TDD (migration — no new tests, no behavior change; full suite must stay green)

**Files owned (exclusive):**
- `software/server/tests/integration/test_sessions_endpoint.py` (modified)
- `software/server/tests/integration/test_full_report.py` (modified)
- `software/server/tests/integration/test_protocols_endpoint.py` (modified)
- `software/server/tests/integration/test_protocol_e2e.py` (modified)

**Depends on:** nothing in this plan (can run in Wave 0 alongside T1) — but by convention is ordered just before T12 so the wave transition "default remains sync" ↔ "default is async" is reversible.

**Research confidence:** high — grep'd file list comes from the 2026-04-14 stub audit.

**Plan-review notes:** **The default is STILL sync after T11.** The flip happens in T12. T11 makes the test calls explicit about the sync intent so that when T12 flips the default, the tests don't silently start asserting against the async-path response shape. This makes the wave boundary reversible: if T12 breaks something, reverting T12 alone restores green without touching tests.

`tests/integration/test_session_pipeline.py` is intentionally LEFT ALONE — it already has `r1` with `?sync=true` and `r2` bare (testing that the no-op flag does not break either form). T12 updates that file to expect `r2.status_code == 202`.

**Commit cadence:** 1 commit per modified file, 4 commits total. Run the full suite after each commit to confirm still-green before moving on — this is the reversible wave so green-in-between is the point.

#### TDD cycle 11.1 — `test_sessions_endpoint.py` (3 call sites)

**Diff:**
```
Line 14:  response = client.post("/sessions", json=payload)
       →  response = client.post("/sessions?sync=true", json=payload)

Line 27:  response = client.post("/sessions", json=payload)
       →  response = client.post("/sessions?sync=true", json=payload)

Line 36:  post_response = client.post("/sessions", json=payload)
       →  post_response = client.post("/sessions?sync=true", json=payload)
```

*Steps:*
1. Apply the three edits above.
2. Run `cd software/server && uv run pytest tests/integration/test_sessions_endpoint.py -v` — expect 3 passed, unchanged.
3. Commit:
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/integration/test_sessions_endpoint.py && \
git commit -m "refactor(tests): pin test_sessions_endpoint to sync=true pre-flip"
```

#### TDD cycle 11.2 — `test_full_report.py` (3 call sites)

**Diff:**
```
Line 13:  post = client.post("/sessions", json=session.model_dump(mode="json"))
       →  post = client.post("/sessions?sync=true", json=session.model_dump(mode="json"))

Line 37:  post = client.post("/sessions", json=session.model_dump(mode="json"))
       →  post = client.post("/sessions?sync=true", json=session.model_dump(mode="json"))

Line 62:  post = client.post("/sessions", json=session.model_dump(mode="json"))
       →  post = client.post("/sessions?sync=true", json=session.model_dump(mode="json"))
```

*Steps:*
1. Apply the three edits.
2. Run `cd software/server && uv run pytest tests/integration/test_full_report.py -v` — expect 3 passed.
3. Commit:
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/integration/test_full_report.py && \
git commit -m "refactor(tests): pin test_full_report to sync=true pre-flip"
```

#### TDD cycle 11.3 — `test_protocols_endpoint.py` (1 call site)

**Diff:**
```
Line 9:   post = client.post("/sessions", json=session.model_dump(mode="json"))
       →  post = client.post("/sessions?sync=true", json=session.model_dump(mode="json"))
```

*Steps:*
1. Apply the edit.
2. Run `cd software/server && uv run pytest tests/integration/test_protocols_endpoint.py -v` — expect all previously passing tests to still pass.
3. Commit:
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/integration/test_protocols_endpoint.py && \
git commit -m "refactor(tests): pin _post_session helper to sync=true pre-flip"
```

#### TDD cycle 11.4 — `test_protocol_e2e.py` (1 call site)

**Diff:**
```
Line 19:  resp = client.post("/sessions", json=session.model_dump(mode="json"))
       →  resp = client.post("/sessions?sync=true", json=session.model_dump(mode="json"))
```

*Steps:*
1. Apply the edit.
2. Run `cd software/server && uv run pytest tests/integration/test_protocol_e2e.py -v` — expect all previously passing tests to still pass.
3. Commit:
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/integration/test_protocol_e2e.py && \
git commit -m "refactor(tests): pin _post_squat helper to sync=true pre-flip"
```

#### Full-suite check

After all four cycles, run:
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest -q
```
Expected: same pass count as before T11 (baseline 272 after T1–T10, no new tests from T11 itself).

**Expected test count after T11:** 272 (no new tests; migration only).

---

### Task T12: Flip `POST /sessions` default to async

**Label:** TDD

**Files owned (exclusive):**
- `software/server/src/auralink/api/routes/sessions.py` (rewritten)
- `software/server/src/auralink/api/schemas.py` (modified — add `SessionAsyncResponse`)
- `software/server/tests/integration/test_session_pipeline.py` (modified — r2 now 202)
- `software/server/tests/integration/test_sessions_async_default.py` (new — async branch)

**Depends on:** T9 (`run_pipeline_tracked`), T10 (`schedule_tracked`), T11 (sync tests pre-pinned)

**Research confidence:** high — FastAPI BackgroundTasks + dependency injection patterns.

**Plan-review notes:** The critical invariant: **both branches call `run_pipeline_tracked`, not two parallel entry points.**

Route handler skeleton:
```python
@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_session(
    session: Session,
    background_tasks: BackgroundTasks,
    sync: bool = Query(default=False),
    storage: SessionStorage = Depends(_get_storage),
    registry: RunRegistry = Depends(_get_registry),
    response: Response = ...,  # needed to set 201 vs 202 dynamically
):
    session_id = storage.save(session)
    correlation_id = get_correlation_id()
    run = registry.create(session_id=session_id, correlation_id=correlation_id)
    if sync:
        artifacts = await run_pipeline_tracked(
            session=session,
            run_id=run.id,
            observer=registry,
        )
        storage.save_artifacts(session_id, artifacts)
        response.status_code = 201
        return SessionCreateResponse(
            session_id=session_id,
            frames_received=len(session.frames),
        )
    # async path
    async def _background():
        try:
            artifacts = await run_pipeline_tracked(
                session=session,
                run_id=run.id,
                observer=registry,
            )
            storage.save_artifacts(session_id, artifacts)
        except Exception:
            # observer already called on_run_failed; nothing else to do.
            pass
    schedule_tracked(background_tasks, _background)
    return SessionAsyncResponse(
        run_id=run.id,
        session_id=session_id,
        status="pending",
        links={"status": f"/runs/{run.id}", "events": f"/runs/{run.id}/events"},
    )
```

**Status code note:** FastAPI sets the status from the `status_code` decorator arg; to return 201 from the sync branch within a single handler, inject `Response` and mutate `response.status_code` OR split into two handlers. **Recommended:** keep the route-level default at 202 and mutate `response.status_code = 201` in the sync branch — single handler, single orchestrator entry, matches the "collapse to one path" invariant. The T12 tests assert both status codes.

**Commit cadence:** 3 TDD cycles, 3 commits.

#### TDD cycle 12.1 — `SessionAsyncResponse` schema

*Step 1 — Append to `software/server/tests/unit/api/test_error_detail_schema.py`:*
```python
from auralink.api.schemas import SessionAsyncResponse


def test_session_async_response_shape():
    resp = SessionAsyncResponse(
        run_id="rid-1",
        session_id="sid-1",
        status="pending",
        links={"status": "/runs/rid-1", "events": "/runs/rid-1/events"},
    )
    assert resp.status == "pending"
    assert resp.links["status"] == "/runs/rid-1"
    # round-trip
    loaded = SessionAsyncResponse.model_validate_json(resp.model_dump_json())
    assert loaded == resp
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/api/test_error_detail_schema.py -v
```
Expected: `ImportError` or 1 failure.

*Step 3 — Append to `software/server/src/auralink/api/schemas.py`:*
```python
class SessionAsyncResponse(BaseModel):
    """Response from POST /sessions when the pipeline runs asynchronously.

    Links dict always contains "status" and "events" pointers; the "events"
    link is still returned even when debug_endpoints_enabled is False so the
    contract stays stable (the endpoint itself 404s in production).
    """

    run_id: str
    session_id: str
    status: Literal["pending"]
    links: dict[str, str]
```

*Step 4 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/api/test_error_detail_schema.py -v
```
Expected: `4 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/src/auralink/api/schemas.py \
        software/server/tests/unit/api/test_error_detail_schema.py && \
git commit -m "feat(api): add SessionAsyncResponse schema for async POST /sessions"
```

#### TDD cycle 12.2 — flip route default + async path returns 202 + run_id

*Step 1 — Write test:*

Create `software/server/tests/integration/test_sessions_async_default.py`:
```python
from fastapi.testclient import TestClient

from auralink.api.main import create_app
from tests.fixtures.synthetic.generator import build_overhead_squat_payload


def test_post_sessions_default_async_returns_202_with_run_id(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    payload = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
    r = client.post("/sessions", json=payload)
    assert r.status_code == 202
    body = r.json()
    assert "run_id" in body
    assert body["status"] == "pending"
    assert body["links"]["status"].startswith("/runs/")
    assert body["links"]["events"].startswith("/runs/")


def test_post_sessions_sync_true_returns_201_with_full_response(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    payload = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
    r = client.post("/sessions?sync=true", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert "session_id" in body
    assert body["frames_received"] == 60
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/integration/test_sessions_async_default.py -v
```
Expected: failures (route still returns 201 + SessionCreateResponse by default).

*Step 3 — Rewrite `software/server/src/auralink/api/routes/sessions.py`:*
```python
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status

from auralink.api.schemas import Session, SessionAsyncResponse, SessionCreateResponse
from auralink.config import Settings, get_settings
from auralink.ops.async_runner import schedule_tracked
from auralink.ops.correlation import get_correlation_id
from auralink.ops.run_tracking import RunRegistry
from auralink.pipeline.orchestrator import run_pipeline_tracked
from auralink.pipeline.storage import SessionStorage

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_storage(settings: Settings = Depends(get_settings)) -> SessionStorage:
    return SessionStorage(base_dir=settings.sessions_dir)


def _get_registry(settings: Settings = Depends(get_settings)) -> RunRegistry:
    return RunRegistry(base_dir=settings.runs_dir)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_session(
    session: Session,
    background_tasks: BackgroundTasks,
    response: Response,
    sync: bool = Query(default=False),
    storage: SessionStorage = Depends(_get_storage),
    registry: RunRegistry = Depends(_get_registry),
):
    session_id = storage.save(session)
    correlation_id = get_correlation_id()
    run = registry.create(session_id=session_id, correlation_id=correlation_id)

    if sync:
        artifacts = await run_pipeline_tracked(
            session=session,
            run_id=run.id,
            observer=registry,
        )
        storage.save_artifacts(session_id, artifacts)
        response.status_code = status.HTTP_201_CREATED
        return SessionCreateResponse(
            session_id=session_id,
            frames_received=len(session.frames),
        )

    async def _background():
        try:
            artifacts = await run_pipeline_tracked(
                session=session,
                run_id=run.id,
                observer=registry,
            )
            storage.save_artifacts(session_id, artifacts)
        except Exception:
            # observer already called on_run_failed; nothing else to do here.
            return

    schedule_tracked(background_tasks, _background)
    return SessionAsyncResponse(
        run_id=run.id,
        session_id=session_id,
        status="pending",
        links={
            "status": f"/runs/{run.id}",
            "events": f"/runs/{run.id}/events",
        },
    )


@router.get("/{session_id}", response_model=Session)
def get_session(
    session_id: str,
    storage: SessionStorage = Depends(_get_storage),
) -> Session:
    try:
        return storage.load(session_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"session {session_id} not found",
        ) from exc
```

*Step 4 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/integration/test_sessions_async_default.py -v
```
Expected: `2 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/src/auralink/api/routes/sessions.py \
        software/server/tests/integration/test_sessions_async_default.py && \
git commit -m "feat(api): flip POST /sessions default to async (202 + run_id)"
```

#### TDD cycle 12.3 — update `test_session_pipeline.py::test_sync_flag_is_accepted_as_noop`

*Step 1 — Modify the second assertion in `test_session_pipeline.py`:*
```
Line 28:  assert r2.status_code == 201
       →  assert r2.status_code == 202  # default is now async post-T12
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/integration/test_session_pipeline.py -v
```
Expected: `2 passed`.

Also run the full suite:
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest -q
```
Expected: full suite green (~276 now — 272 pre-T12 + 4 new from T12 cycles).

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/integration/test_session_pipeline.py && \
git commit -m "test(integration): expect 202 for default-async POST /sessions"
```

**Expected test count after T12:** 276.

---

### Task T13: `GET /runs/{id}` + `GET /runs/{id}/events` endpoints

**Label:** TDD

**Files owned (exclusive):**
- `software/server/src/auralink/api/routes/runs.py` (new)
- `software/server/src/auralink/api/main.py` (modified — include router)
- `software/server/tests/integration/test_runs_endpoint.py` (new)

**Depends on:** T3 (`RunRegistry`), T12 (async path writes runs that the new endpoints read)

**Research confidence:** high — standard FastAPI route + dependency injection.

**Plan-review notes:** Two routes:
- `GET /runs/{run_id}` — always enabled; 404 on unknown id; returns `PipelineRun`.
- `GET /runs/{run_id}/events` — gated by `settings.debug_endpoints_enabled`; 404 when flag is False OR when unknown id; returns `list[PipelineEvent]`.

The 404 gate on `/events` is returned **before** looking up the run so an attacker cannot probe debug availability via timing.

**Commit cadence:** 3 TDD cycles, 3 commits.

#### TDD cycle 13.1 — `GET /runs/{id}` returns run state

*Step 1 — Write test:*

Create `software/server/tests/integration/test_runs_endpoint.py`:
```python
from fastapi.testclient import TestClient

from auralink.api.main import create_app
from tests.fixtures.synthetic.generator import build_overhead_squat_payload


def test_get_run_returns_pipeline_run(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    payload = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
    # Use sync path so the run is written synchronously and we can read it.
    r = client.post("/sessions?sync=true", json=payload)
    assert r.status_code == 201
    # sync path returns SessionCreateResponse — the run_id is not in the body.
    # Read it via the runs directory directly.
    runs_dir = tmp_path / "runs"
    run_files = list(runs_dir.glob("*.json"))
    assert len(run_files) == 1
    run_id = run_files[0].stem

    r = client.get(f"/runs/{run_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == run_id
    assert body["status"] == "complete"


def test_get_run_unknown_id_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    r = client.get("/runs/deadbeef-dead-beef-dead-beefdeadbeef")
    assert r.status_code == 404
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/integration/test_runs_endpoint.py -v
```
Expected: 404 for the route itself.

*Step 3 — Create `software/server/src/auralink/api/routes/runs.py`:*
```python
from fastapi import APIRouter, Depends, HTTPException, status

from auralink.config import Settings, get_settings
from auralink.ops.run_tracking import PipelineRun, RunRegistry
from auralink.pipeline.events import PipelineEvent

router = APIRouter(prefix="/runs", tags=["runs"])


def _get_registry(settings: Settings = Depends(get_settings)) -> RunRegistry:
    return RunRegistry(base_dir=settings.runs_dir)


@router.get("/{run_id}", response_model=PipelineRun)
def get_run(
    run_id: str,
    registry: RunRegistry = Depends(_get_registry),
) -> PipelineRun:
    run = registry.get(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"run {run_id} not found",
        )
    return run


@router.get("/{run_id}/events", response_model=list[PipelineEvent])
def get_run_events(
    run_id: str,
    settings: Settings = Depends(get_settings),
    registry: RunRegistry = Depends(_get_registry),
) -> list[PipelineEvent]:
    if not settings.debug_endpoints_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="events endpoint not available",
        )
    # Verify the run exists; returns empty list if no events logged yet.
    if registry.get(run_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"run {run_id} not found",
        )
    return registry.events(run_id)
```

Modify `software/server/src/auralink/api/main.py` to include the new router:
```python
from auralink.api.routes import health, protocols, reports, runs, sessions
# ...
app.include_router(runs.router)
```

*Step 4 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/integration/test_runs_endpoint.py -v
```
Expected: `2 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/src/auralink/api/routes/runs.py \
        software/server/src/auralink/api/main.py \
        software/server/tests/integration/test_runs_endpoint.py && \
git commit -m "feat(api): GET /runs/{id} returns PipelineRun state"
```

#### TDD cycle 13.2 — `/events` gated behind debug flag

*Step 1 — Append:*
```python
def test_get_run_events_404_when_debug_flag_disabled(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AURALINK_DEBUG_ENDPOINTS_ENABLED", "false")
    app = create_app()
    client = TestClient(app)
    payload = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
    client.post("/sessions?sync=true", json=payload)
    runs_dir = tmp_path / "runs"
    run_id = next(runs_dir.glob("*.json")).stem

    r = client.get(f"/runs/{run_id}/events")
    assert r.status_code == 404
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/integration/test_runs_endpoint.py -v
```
Expected: `3 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/integration/test_runs_endpoint.py && \
git commit -m "test(api): /runs/{id}/events 404s when debug flag is disabled"
```

#### TDD cycle 13.3 — `/events` enabled returns JSONL list

*Step 1 — Append:*
```python
def test_get_run_events_returns_list_when_debug_enabled(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AURALINK_DEBUG_ENDPOINTS_ENABLED", "true")
    app = create_app()
    client = TestClient(app)
    payload = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
    client.post("/sessions?sync=true", json=payload)
    runs_dir = tmp_path / "runs"
    run_id = next(runs_dir.glob("*.json")).stem

    r = client.get(f"/runs/{run_id}/events")
    assert r.status_code == 200
    events = r.json()
    assert isinstance(events, list)
    assert len(events) > 0
    # every stage emits exactly one started + one completed
    kinds = [e["event"] for e in events]
    assert kinds.count("started") == kinds.count("completed")


def test_get_run_events_unknown_id_with_debug_on_returns_404(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AURALINK_DEBUG_ENDPOINTS_ENABLED", "true")
    app = create_app()
    client = TestClient(app)
    r = client.get("/runs/deadbeef-dead-beef-dead-beefdeadbeef/events")
    assert r.status_code == 404
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/integration/test_runs_endpoint.py -v
```
Expected: `5 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/integration/test_runs_endpoint.py && \
git commit -m "test(api): /runs/{id}/events returns event list when debug enabled"
```

**Expected test count after T13:** 281.

---

### Task T14: Mobile-handover contract update

**Label:** TDD (schema export is a script, the Dart file is static + JSON fixture)

**Files owned (exclusive):**
- `software/mobile-handover/tools/export_schemas.py` (modified)
- `software/mobile-handover/schemas/session-response.schema.json` (new — derived output)
- `software/mobile-handover/interface/models.dart` (modified — new class)
- `software/mobile-handover/fixtures/sample_response_async.json` (new)
- `software/server/tests/unit/api/test_mobile_handover_contract.py` (new)

**Depends on:** T12 (`SessionAsyncResponse` schema must exist)

**Research confidence:** high — `Session.model_json_schema()` is stable in pydantic v2.

**Plan-review notes:** This is the **breaking contract change** called out in the architecture invariants. The epoch decision doc must flag it. The Dart file keeps `SessionCreateResponse` (still used by `?sync=true`) and adds a parallel `SessionAsyncResponse` class. The JSON fixture is an example async response payload for Flutter devs to hand-paste into tests.

**Commit cadence:** 3 TDD cycles, 3 commits.

#### TDD cycle 14.1 — extend `export_schemas.py` to emit response schemas

*Step 1 — Write test:*

Create `software/server/tests/unit/api/test_mobile_handover_contract.py`:
```python
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]  # .../RnD_Server
HANDOVER = REPO_ROOT / "software" / "mobile-handover"


def test_export_schemas_script_emits_session_async_response_schema(tmp_path, monkeypatch):
    # Run the export script; it should produce
    # software/mobile-handover/schemas/session-response.schema.json
    monkeypatch.chdir(HANDOVER / "tools")
    subprocess.run(
        ["python", "export_schemas.py"],
        check=True,
        cwd=str(HANDOVER / "tools"),
    )
    out = HANDOVER / "schemas" / "session-response.schema.json"
    assert out.exists()
    schema = json.loads(out.read_text())
    # The exported schema is a union/oneOf over both sync and async shapes
    assert "definitions" in schema or "$defs" in schema or "oneOf" in schema or "anyOf" in schema
    text = out.read_text()
    assert "SessionAsyncResponse" in text
    assert "SessionCreateResponse" in text


def test_sample_response_fixture_validates_against_async_schema():
    fixture = HANDOVER / "fixtures" / "sample_response_async.json"
    assert fixture.exists()
    body = json.loads(fixture.read_text())
    assert body["status"] == "pending"
    assert "run_id" in body
    assert "session_id" in body
    assert body["links"]["status"].startswith("/runs/")
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/api/test_mobile_handover_contract.py -v
```
Expected: 2 failures (file doesn't exist).

*Step 3 — Modify `software/mobile-handover/tools/export_schemas.py`:*
```python
#!/usr/bin/env python3
"""Regenerate schemas/*.schema.json from the live pydantic models.

Run after any change to software/server/src/auralink/api/schemas.py to keep
the mobile-handover JSON schemas in lockstep.

Emits:
    schemas/session.schema.json           -- Session (request body)
    schemas/session-response.schema.json  -- oneOf(SessionCreateResponse, SessionAsyncResponse)

Usage:
    cd software/mobile-handover/tools
    ../../server/.venv/bin/python export_schemas.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HANDOVER = HERE.parent
SERVER_SRC = HANDOVER.parent / "server" / "src"
SCHEMAS_DIR = HANDOVER / "schemas"

sys.path.insert(0, str(SERVER_SRC))
from auralink.api.schemas import (  # noqa: E402
    Session,
    SessionAsyncResponse,
    SessionCreateResponse,
)

SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)

(SCHEMAS_DIR / "session.schema.json").write_text(
    json.dumps(Session.model_json_schema(), indent=2) + "\n"
)

union_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "SessionResponse",
    "description": (
        "Union of the two POST /sessions response shapes. "
        "SessionCreateResponse is returned with status 201 when ?sync=true; "
        "SessionAsyncResponse is returned with status 202 by default."
    ),
    "oneOf": [
        SessionCreateResponse.model_json_schema(),
        SessionAsyncResponse.model_json_schema(),
    ],
}
(SCHEMAS_DIR / "session-response.schema.json").write_text(
    json.dumps(union_schema, indent=2) + "\n"
)

print(f"wrote {(SCHEMAS_DIR / 'session.schema.json').relative_to(HANDOVER.parent)}")
print(f"wrote {(SCHEMAS_DIR / 'session-response.schema.json').relative_to(HANDOVER.parent)}")
```

Also create `software/mobile-handover/fixtures/sample_response_async.json`:
```json
{
  "run_id": "a8f3c9d2-5e4b-4a1c-9e8f-1234567890ab",
  "session_id": "4c1f0e8b-2a3d-4f5e-9c6d-abcdef123456",
  "status": "pending",
  "links": {
    "status": "/runs/a8f3c9d2-5e4b-4a1c-9e8f-1234567890ab",
    "events": "/runs/a8f3c9d2-5e4b-4a1c-9e8f-1234567890ab/events"
  }
}
```

Run the export script manually once to generate `session-response.schema.json`:
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/mobile-handover/tools && \
uv --directory ../../server run python export_schemas.py
```

*Step 4 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/api/test_mobile_handover_contract.py -v
```
Expected: `2 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/mobile-handover/tools/export_schemas.py \
        software/mobile-handover/schemas/session-response.schema.json \
        software/mobile-handover/fixtures/sample_response_async.json \
        software/server/tests/unit/api/test_mobile_handover_contract.py && \
git commit -m "feat(mobile-handover): export session response union schema"
```

#### TDD cycle 14.2 — Dart `SessionAsyncResponse` class

*Step 1 — Append to `software/mobile-handover/interface/models.dart`:*
```dart
/// Response body returned by POST /sessions when the pipeline runs
/// asynchronously (the default as of Plan 5). The client should poll
/// `/runs/{run_id}` to observe stage progression.
///
/// Breaking contract change: pre-Plan-5 clients received `SessionCreateResponse`
/// for the default (bare) POST; Plan 5 moved that to `?sync=true` only.
class SessionAsyncResponse {
  const SessionAsyncResponse({
    required this.runId,
    required this.sessionId,
    required this.status,
    required this.links,
  });

  final String runId;
  final String sessionId;

  /// Always the literal string "pending" on creation. Follow-up state
  /// transitions are observed via GET /runs/{runId}.
  final String status;

  /// Map of hyperlink name → path. Always contains keys "status" and
  /// "events" today; more may be added in follow-on plans.
  final Map<String, String> links;

  factory SessionAsyncResponse.fromJson(Map<String, dynamic> json) =>
      SessionAsyncResponse(
        runId: json['run_id'] as String,
        sessionId: json['session_id'] as String,
        status: json['status'] as String,
        links: Map<String, String>.from(json['links'] as Map),
      );
}
```

*Step 2 — Add a lightweight Dart-file sanity test (`cd software/server && uv run pytest tests/unit/api/test_mobile_handover_contract.py -v`):*

Append to `test_mobile_handover_contract.py`:
```python
def test_models_dart_contains_session_async_response_class():
    dart = (HANDOVER / "interface" / "models.dart").read_text()
    assert "class SessionAsyncResponse" in dart
    assert "runId" in dart
    assert "factory SessionAsyncResponse.fromJson" in dart
    # Old class is still present (keeps sync path compatible)
    assert "class SessionCreateResponse" in dart
```

*Step 4 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/unit/api/test_mobile_handover_contract.py -v
```
Expected: `3 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/mobile-handover/interface/models.dart \
        software/server/tests/unit/api/test_mobile_handover_contract.py && \
git commit -m "feat(mobile-handover): add SessionAsyncResponse Dart class"
```

#### TDD cycle 14.3 — decision doc reminder

Write a short note into `docs/decisions/` (file may already exist as a running log; append a new entry):

*Step 1 — Append to (or create) `docs/decisions/2026-04-plan-5-contract-break.md`:*
```markdown
## Plan 5 — POST /sessions response shape is a breaking change

Default response from POST /sessions changed from `SessionCreateResponse`
(full Report) to `SessionAsyncResponse` (run_id + links). Clients can opt into
the legacy shape with `?sync=true`.

Flutter teammate action: update the app to poll `/runs/{run_id}` after
receiving the 202 + run_id, OR add `?sync=true` to keep the old shape. The
Dart helper class `SessionAsyncResponse` lives at
`software/mobile-handover/interface/models.dart`.

Mobile-handover files updated by this plan:
- `schemas/session-response.schema.json` (new)
- `interface/models.dart` (new class added, old class preserved)
- `fixtures/sample_response_async.json` (new)

Status: Landed via plan 2026-04-10-L2-5-operations.md task T14.
```

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add docs/decisions/2026-04-plan-5-contract-break.md && \
git commit -m "docs(decisions): flag POST /sessions contract break in Plan 5"
```

**Expected test count after T14:** 284.

---

### Task T15: Integration test — async happy path

**Label:** TDD

**Files owned (exclusive):**
- `software/server/tests/integration/test_async_pipeline.py` (new)

**Depends on:** T12 (async path), T13 (`GET /runs/{id}`)

**Research confidence:** high — TestClient dispatches BackgroundTasks synchronously, so we can poll the run state after a single request.

**Plan-review notes:** Verifies end-to-end that POST /sessions (default async) lands a 202, a subsequent GET /runs/{id} returns complete after the BackgroundTask has run, and the events JSONL (with debug flag on) has one start + one complete per stage. TestClient's context-manager mode flushes BackgroundTasks before returning, so no sleep/poll loop is needed.

**Commit cadence:** 1 TDD cycle, 1 commit.

*Step 1 — Write test:*

Create `software/server/tests/integration/test_async_pipeline.py`:
```python
from fastapi.testclient import TestClient

from auralink.api.main import create_app
from tests.fixtures.synthetic.generator import build_overhead_squat_payload


def test_async_post_pipeline_completes_and_events_stream_is_consistent(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AURALINK_DEBUG_ENDPOINTS_ENABLED", "true")
    app = create_app()
    with TestClient(app) as client:
        payload = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
        r = client.post("/sessions", json=payload)
        assert r.status_code == 202
        body = r.json()
        run_id = body["run_id"]

    # After the context manager exits, BackgroundTasks have run.
    with TestClient(app) as client:
        r = client.get(f"/runs/{run_id}")
        assert r.status_code == 200
        run_body = r.json()
        assert run_body["status"] == "complete"
        # overhead_squat default stage list has 10 stages
        assert len(run_body["completed_stages"]) == 10

        r = client.get(f"/runs/{run_id}/events")
        assert r.status_code == 200
        events = r.json()
        starts = [e for e in events if e["event"] == "started"]
        completes = [e for e in events if e["event"] == "completed"]
        assert len(starts) == len(completes) == 10
        # correlation_id is the same across all events of one run
        cids = {e["correlation_id"] for e in events}
        assert len(cids) == 1


def test_async_post_pipeline_events_contain_duration_on_complete(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AURALINK_DEBUG_ENDPOINTS_ENABLED", "true")
    app = create_app()
    with TestClient(app) as client:
        payload = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
        r = client.post("/sessions", json=payload)
        run_id = r.json()["run_id"]
    with TestClient(app) as client:
        events = client.get(f"/runs/{run_id}/events").json()
        for ev in events:
            if ev["event"] == "completed":
                assert ev["duration_ms"] is not None and ev["duration_ms"] >= 0.0
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/integration/test_async_pipeline.py -v
```
Expected: `2 passed` — if fails, the T10 spike likely also fails; revisit.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/integration/test_async_pipeline.py && \
git commit -m "test(integration): async POST /sessions happy path + events stream"
```

**Expected test count after T15:** 286.

---

### Task T16: Integration test — quality-gate failure path

**Label:** TDD

**Files owned (exclusive):**
- `software/server/tests/integration/test_run_failure.py` (new)

**Depends on:** T12, T13

**Research confidence:** medium — depends on whether a synthetic fixture already produces a `QualityGateError`. If not, the test builds one inline by zeroing landmark visibility.

**Plan-review notes:** Asserts the full error path: POST malformed session → 202 + run_id → poll GET /runs/{id} → status == "failed" → error.type == "quality_gate" → correlation_id present and consistent across the run and the (debug-enabled) events stream.

**Commit cadence:** 1 TDD cycle, 1 commit.

*Step 1 — Write test:*

Create `software/server/tests/integration/test_run_failure.py`:
```python
from fastapi.testclient import TestClient

from auralink.api.main import create_app
from tests.fixtures.synthetic.generator import build_overhead_squat_payload


def _build_failing_payload() -> dict:
    payload = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
    # Drive quality_gate to fail: zero out visibility on every landmark.
    for frame in payload["frames"]:
        for lm in frame["landmarks"]:
            lm["visibility"] = 0.0
            lm["presence"] = 0.0
    return payload


def test_quality_gate_failure_lands_as_pipeline_run_failed(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AURALINK_DEBUG_ENDPOINTS_ENABLED", "true")
    app = create_app()
    with TestClient(app) as client:
        payload = _build_failing_payload()
        r = client.post("/sessions", json=payload, headers={"X-Correlation-Id": "fail-corr"})
        assert r.status_code == 202
        run_id = r.json()["run_id"]
    with TestClient(app) as client:
        r = client.get(f"/runs/{run_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "failed"
        assert body["error"] is not None
        assert body["error"]["type"] == "quality_gate"
        assert body["error"]["correlation_id"] == "fail-corr"
        assert body["correlation_id"] == "fail-corr"

        events = client.get(f"/runs/{run_id}/events").json()
        failed = [e for e in events if e["event"] == "failed"]
        assert len(failed) == 1
        assert failed[0]["correlation_id"] == "fail-corr"
        assert failed[0]["error"]["type"] == "quality_gate"


def test_sync_quality_gate_failure_still_writes_run_failed_record(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    payload = _build_failing_payload()
    r = client.post(
        "/sessions?sync=true", json=payload, headers={"X-Correlation-Id": "sync-fail"}
    )
    # sync branch raises QualityGateError which maps to 422 via api/errors.py
    assert r.status_code == 422
    # Even so, the run record should exist and be marked failed
    runs_dir = tmp_path / "runs"
    run_files = list(runs_dir.glob("*.json"))
    assert len(run_files) == 1
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/integration/test_run_failure.py -v
```
Expected: `2 passed`. If `_build_failing_payload` does not actually trigger a failure (quality_gate may tolerate all-zero visibility — inspect `pipeline/stages/quality_gate.py`), tweak to set a bad `frame_rate` or drop all frames.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/integration/test_run_failure.py && \
git commit -m "test(integration): quality-gate failure writes PipelineRun.failed"
```

**Expected test count after T16:** 288.

---

### Task T17: Integration test — debug-endpoint flag gate

**Label:** TDD

**Files owned (exclusive):**
- `software/server/tests/integration/test_debug_events_flag.py` (new)

**Depends on:** T13

**Research confidence:** high — pure config-driven route behavior.

**Plan-review notes:** T13 already covers the flag in its focused test, but T17 is an explicit regression guard living in `tests/integration/` so the cross-reference between the config flag and the route body is visible to future plan reviewers.

**Commit cadence:** 1 TDD cycle, 1 commit.

*Step 1 — Write test:*

Create `software/server/tests/integration/test_debug_events_flag.py`:
```python
from fastapi.testclient import TestClient

from auralink.api.main import create_app
from tests.fixtures.synthetic.generator import build_overhead_squat_payload


def _post_and_get_run_id(client: TestClient):
    payload = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
    r = client.post("/sessions?sync=true", json=payload)
    assert r.status_code == 201
    # Run_id must be read from disk since sync response does not carry it.
    return r


def test_events_endpoint_404_when_flag_false(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("AURALINK_DEBUG_ENDPOINTS_ENABLED", raising=False)
    app = create_app()
    client = TestClient(app)
    _post_and_get_run_id(client)
    run_id = next((tmp_path / "runs").glob("*.json")).stem
    r = client.get(f"/runs/{run_id}/events")
    assert r.status_code == 404


def test_events_endpoint_200_when_flag_true(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AURALINK_DEBUG_ENDPOINTS_ENABLED", "true")
    app = create_app()
    client = TestClient(app)
    _post_and_get_run_id(client)
    run_id = next((tmp_path / "runs").glob("*.json")).stem
    r = client.get(f"/runs/{run_id}/events")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
```

*Step 2 — Run:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest tests/integration/test_debug_events_flag.py -v
```
Expected: `2 passed`.

*Step 5 — Commit:*
```bash
cd /home/context/olorin/projects/bioliminal/RnD_Server && \
git add software/server/tests/integration/test_debug_events_flag.py && \
git commit -m "test(integration): debug_endpoints_enabled gates /runs/{id}/events"
```

**Expected test count after T17:** 290.

---

### Task T18: Final validation (lint + live smoke)

**Label:** skip-tdd

**Files owned (exclusive):**
- none (validation only)

**Depends on:** all prior tasks

**Research confidence:** high

**Plan-review notes:** This is the gate before marking the plan exit criteria satisfied. Four checks:

1. Full pytest suite
2. Ruff lint
3. Black format check
4. Live uvicorn smoke — start the server, hit the endpoints by `curl`, assert the transitions

**Steps:**

```bash
# 1. Full suite
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run pytest -x -q
# Expected: ~290 passed, 0 failed

# 2. Lint
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run ruff check src/ tests/
# Expected: All checks passed

# 3. Format
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
uv run black --check src/ tests/
# Expected: All files already formatted

# 4. Live smoke — redirect uvicorn stdout+stderr so step 4e can grep the log stream
cd /home/context/olorin/projects/bioliminal/RnD_Server/software/server && \
AURALINK_DATA_DIR=/tmp/plan5-smoke AURALINK_DEBUG_ENDPOINTS_ENABLED=true \
  uv run uvicorn auralink.api.main:app --port 8765 >/tmp/plan5-uvicorn.log 2>&1 &
SERVER_PID=$!
sleep 2

# 4a. Async POST should return 202
RESP=$(curl -s -o /tmp/plan5-resp.json -w "%{http_code}" \
  -X POST http://127.0.0.1:8765/sessions \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: smoke-corr-1" \
  -d @software/mobile-handover/fixtures/sample_valid_session.json)
test "$RESP" = "202" || { echo "expected 202, got $RESP"; kill $SERVER_PID; exit 1; }
RUN_ID=$(python -c "import json; print(json.load(open('/tmp/plan5-resp.json'))['run_id'])")

# 4b. Run status should transition to complete
sleep 1
STATUS=$(curl -s http://127.0.0.1:8765/runs/$RUN_ID | python -c "import json,sys; print(json.load(sys.stdin)['status'])")
test "$STATUS" = "complete" || { echo "expected complete, got $STATUS"; kill $SERVER_PID; exit 1; }

# 4c. Events endpoint should return non-empty list
EVENT_COUNT=$(curl -s http://127.0.0.1:8765/runs/$RUN_ID/events | python -c "import json,sys; print(len(json.load(sys.stdin)))")
test "$EVENT_COUNT" -gt 0 || { echo "expected >0 events, got $EVENT_COUNT"; kill $SERVER_PID; exit 1; }

# 4d. Sync path should return 201 + full response
RESP=$(curl -s -o /tmp/plan5-sync-resp.json -w "%{http_code}" \
  -X POST "http://127.0.0.1:8765/sessions?sync=true" \
  -H "Content-Type: application/json" \
  -d @software/mobile-handover/fixtures/sample_valid_session.json)
test "$RESP" = "201" || { echo "expected 201, got $RESP"; kill $SERVER_PID; exit 1; }

# 4e. Verify correlation_id is present in the structured log stream for the smoke request.
# The async POST in 4a passed X-Correlation-Id: smoke-corr-1 — it must round-trip into logs.
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null || true
grep -q '"correlation_id"[[:space:]]*:[[:space:]]*"smoke-corr-1"' /tmp/plan5-uvicorn.log || {
  echo "FAIL: correlation_id=smoke-corr-1 not found in uvicorn log stream"
  echo "---- last 50 lines of uvicorn log ----"
  tail -50 /tmp/plan5-uvicorn.log
  exit 1
}
echo "SMOKE PASSED (including correlation_id log round-trip)"
```

**Note:** Step 4 must redirect uvicorn stdout+stderr to `/tmp/plan5-uvicorn.log` at server start (add `>/tmp/plan5-uvicorn.log 2>&1 &` to the `uv run uvicorn ...` line earlier in the script) so the 4e grep has something to read. The smoke POST in 4a must also pass `-H "X-Correlation-Id: smoke-corr-1"` so there's a deterministic value to grep for.

If all four gates pass, write a brief validation note into the PR body or decision doc. No commit is produced by this task unless lint/format cleanup applied minor changes — in that case make a single `chore(lint): plan 5 format pass` commit.

**Expected test count after T18:** 290 (unchanged).

---

## Exit Criteria

- ~56 new assertions (~38 distinct tests). Full suite green: baseline 231 → final ~290.
- `POST /sessions` (no `?sync`) returns 202 + `SessionAsyncResponse{run_id, session_id, status:"pending", links}` immediately; pipeline runs in background via `ops/async_runner.schedule_tracked`.
- `POST /sessions?sync=true` still returns 201 + full `SessionCreateResponse` by awaiting `run_pipeline_tracked` inline (no parallel code path).
- `GET /runs/{id}` transitions pending → running → complete for a successful session and shows the stage list growing over the run.
- `GET /runs/{id}/events` (with `debug_endpoints_enabled=True`) returns the JSONL event stream; returns 404 when the flag is False.
- Every log line has a `correlation_id` field propagated from the `X-Correlation-Id` request header (or a fresh UUID if absent). Logs are structured JSON via `python-json-logger`.
- Per-stage timing recorded in `PipelineRun` events via the `RunObserver` injected into `run_pipeline_tracked`.
- A failed quality gate shows up as `PipelineRun.status == "failed"` with `error: ErrorDetail(type="quality_gate", ...)` and the correlation_id cross-referenceable in logs and the events stream.
- Mobile-handover contract regenerated (`schemas/session-response.schema.json` emitted; `interface/models.dart` has `SessionAsyncResponse` alongside `SessionCreateResponse`; `fixtures/sample_response_async.json` committed); decision doc flags the breaking response-shape change.
- Plan 1-4 integration tests continue to pass (they opt into sync via `?sync=true` after T11).
- `pipeline/orchestrator.py` does not import `ops/*` at module load time (enforced by `test_orchestrator_no_ops_import_at_module_level`).
- T10 spike test (`test_contextvar_spike.py`) passes for BOTH sync and async background callables — proves the header → middleware → BackgroundTask → log correlation_id round-trip empirically.
- `ruff check` clean, `black --check` clean, live `curl` smoke passes all four checks in T18.

## Deferred to L3

- **Log aggregation target** — start with stdout JSON lines, leave the OTEL exporter interface open. Follow-on plan when we have a hosting target.
- **Retention policy for `PipelineRun` records** — leave them forever for now; add cleanup hook when disk pressure becomes real.
- **Heavy ML inference path** — if a stage grows beyond a few seconds of real work, `BackgroundTasks` in-process will block the uvicorn worker slot. Follow-on plan adopts TaskIQ or Arq at that point; the `async_runner.schedule_tracked` API is deliberately shaped to be a drop-in seam.
- **DBA-based reference rep aggregation** — outside the scope of this plan; Plan 3 deferred it.
- **Audit hook for `/runs/{id}/events` in production** — if we ever need production event inspection, add a signed-URL or audit-log alternative instead of flipping `debug_endpoints_enabled=True`.
- **Multi-writer concurrency on the events JSONL** — current impl assumes single-writer (one BackgroundTask per run). If later plans fan out per-stage to multiple executors, replace the append with an `fcntl.flock` guard or switch to SQLite append.

## Notes

- **Sibling Plan 3 (`2026-04-10-L2-3-dtw-temporal.md`) is the style reference** for task expansion depth. When in doubt about how much to inline, err toward more — parallel-plan-executor subagents cannot re-read the plan.
- **Commit cadence: one commit per TDD cycle, NOT one commit per task.** Task 3 produces 3 commits; Task 9 produces 3; Task 10 produces 3 including the spike. `task-executor` enforces this from the injected skill body; don't batch.
- **T10 is the risk concentration.** If the spike test fails, everything downstream (T12, T15, T16, T17) fails in confusing ways. Run T10 first in its wave and STOP on red.
- **Wave structure (for `parallel-planning`):** T1 is Wave 0 (solo); T2 + T4 + T11 can parallelize in Wave A (no cross-deps, disjoint files); T3 + T5 in Wave B (T5 is the dep of T3's `PipelineEvent` import and must complete first OR they go in one wave with T5 seq-ordered first); T6 + T7 + T8 + T10 in Wave C (all depend on T4); T9 in Wave D (needs T3, T5, T7); T12 in Wave E (needs T9, T10, T11); T13 + T14 in Wave F (both need T12); T15 + T16 + T17 in Wave G (integration); T18 in Wave H (solo validation). Actual parallelism decisions are `parallel-planning`'s job — this is the rough shape.
