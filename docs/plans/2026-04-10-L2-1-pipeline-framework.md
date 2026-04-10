# L2 Plan 1 — Pipeline Framework + Core Analysis Stages

> **Execution:** Use `parallel-plan-executor` (sequential-in-main-tree). Do NOT use `subagent-driven-development`. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** Ready for plan-review
**Parent:** `docs/plans/2026-04-10-analysis-pipeline-epoch.md`
**Depends on:** Server scaffold (`docs/plans/2026-04-09-server-scaffold.md`) — completed at commit `537b911` (31 tests passing baseline).

**Goal:** Replace the `pipeline.orchestrator` stub with a real stage framework. Define the `Stage` abstraction, the `PipelineArtifacts` pydantic bundle, the `StageRegistry` (with a post-init extension API so Plan 4 can add new movement types without touching Plan 1 code), and all six core analysis stages (quality gate, angle series, normalize, rep segment, per-rep metrics, within-movement trend). Wire the orchestrator into `POST /sessions` (runs synchronously after `storage.save()`, persists artifacts alongside the raw session, accepts `?sync=true` as a recognized no-op flag upfront so Plan 5 can flip the default without breaking tests), and serve `GET /sessions/{id}/report` returning the raw artifact bundle.

**Architecture:** Every stage is a frozen dataclass `Stage(name, run)` where `run` is a pure `Callable[[StageContext], Any]`. The orchestrator walks the stage list for the session's movement type, caches each stage's output in `StageContext.artifacts` keyed by stage name, and assembles a final `PipelineArtifacts` pydantic model at the end. Per-movement stage composition lives in a `StageRegistry` with a public `register_movement()` API. Plan 1 registers `overhead_squat` and `single_leg_squat` into the default registry; Plan 4 later adds `push_up` and `rollup` without modifying `orchestrator.py`. Quality gate failures raise `QualityGateError` and propagate to a FastAPI exception handler that maps to HTTP 422. All other stage exceptions wrap into `StageError` and map to HTTP 500.

**Tech Stack:** Python 3.11+, FastAPI, pydantic v2, numpy, pytest — scaffold stack. **No new runtime dependencies.**

**Commit cadence:** One commit per TDD cycle (red → green → one behavior committed). Multi-behavior tasks such as the quality gate produce multiple commits inside the task. Every commit must leave the suite green.

---

## File Structure

Files created or modified in this plan:

```
software/server/src/auralink/
├── pipeline/
│   ├── artifacts.py             # NEW
│   ├── errors.py                # NEW
│   ├── registry.py              # NEW
│   ├── orchestrator.py          # MODIFIED — replaces the stub
│   ├── storage.py               # MODIFIED — add save_artifacts / load_artifacts
│   └── stages/
│       ├── __init__.py          # NEW
│       ├── base.py              # NEW — Stage, StageContext
│       ├── quality_gate.py      # NEW
│       ├── angle_series.py      # NEW
│       ├── normalize.py         # NEW
│       ├── rep_segment.py       # NEW
│       ├── per_rep_metrics.py   # NEW
│       └── within_movement_trend.py
├── pose/
│   └── joint_angles.py          # MODIFIED — add trunk_lean_angle()
└── api/
    ├── errors.py                # NEW — FastAPI exception handlers
    ├── main.py                  # MODIFIED — register handlers + reports router
    └── routes/
        ├── sessions.py          # MODIFIED — run pipeline, accept ?sync=true
        └── reports.py           # NEW

software/server/tests/
├── fixtures/
│   ├── __init__.py              # NEW (if missing)
│   └── synthetic_overhead_squat.py     # NEW — Plan 4 will absorb
├── unit/pipeline/
│   ├── __init__.py              # NEW
│   ├── test_base.py             # NEW
│   ├── test_artifacts.py        # NEW
│   ├── test_errors.py           # NEW
│   ├── test_quality_gate.py     # NEW
│   ├── test_angle_series.py     # NEW
│   ├── test_normalize.py        # NEW
│   ├── test_rep_segment.py      # NEW
│   ├── test_per_rep_metrics.py  # NEW
│   ├── test_within_movement_trend.py   # NEW
│   ├── test_registry.py         # NEW
│   └── test_orchestrator.py     # NEW
├── unit/pose/
│   └── test_trunk_lean_angle.py # NEW
└── integration/
    ├── test_session_pipeline.py        # NEW — POST runs pipeline
    ├── test_report_endpoint.py         # NEW — GET /sessions/{id}/report
    ├── test_error_handling.py          # NEW — 422 on quality gate reject
    └── test_e2e_overhead_squat.py      # NEW — round-trip with synthetic fixture
```

**Note on the synthetic fixture helper.** Plan 4 owns the shared `tests/fixtures/synthetic/generator.py` exposing `generate_session()` and `generate_reference_rep()`. Plan 1 needs integration-test data before Plan 4 lands, so it ships a scoped single-purpose helper (`tests/fixtures/synthetic_overhead_squat.py`) covering overhead_squat only. This is not a competing generator: Plan 4 will absorb it or replace its call sites when it lands its own generator module.

---

## Artifact Schemas (authoritative shapes)

Defined in `pipeline/artifacts.py` (Task 2). Referenced throughout the rest of the plan.

| Schema | Fields |
|---|---|
| `QualityIssue` | `code: str`, `detail: str` |
| `SessionQualityReport` | `passed: bool`, `issues: list[QualityIssue]`, `metrics: dict[str, float]` |
| `AngleTimeSeries` | `angles: dict[str, list[float]]`, `timestamps_ms: list[int]` |
| `NormalizedAngleTimeSeries` | `angles: dict[str, list[float]]`, `timestamps_ms: list[int]`, `scale_factor: float` |
| `RepBoundaryModel` | `start_index: int`, `bottom_index: int`, `end_index: int`, `start_angle: float`, `bottom_angle: float`, `end_angle: float` |
| `RepBoundaries` | `by_angle: dict[str, list[RepBoundaryModel]]` |
| `RepMetric` | `rep_index: int`, `amplitude_deg: float`, `peak_velocity_deg_per_s: float`, `rom_deg: float`, `mean_trunk_lean_deg: float`, `mean_knee_valgus_deg: float` |
| `PerRepMetrics` | `primary_angle: str`, `reps: list[RepMetric]` |
| `WithinMovementTrend` | `rom_slope_deg_per_rep: float`, `velocity_slope_deg_per_s_per_rep: float`, `valgus_slope_deg_per_rep: float`, `trunk_lean_slope_deg_per_rep: float`, `fatigue_detected: bool` |
| `PipelineArtifacts` | `quality_report: SessionQualityReport`, `angle_series: AngleTimeSeries \| None`, `normalized_angle_series: NormalizedAngleTimeSeries \| None`, `rep_boundaries: RepBoundaries \| None`, `per_rep_metrics: PerRepMetrics \| None`, `within_movement_trend: WithinMovementTrend \| None` |

---

### Task 1: `Stage` abstraction and `StageContext`

**Files:**
- Create: `software/server/src/auralink/pipeline/stages/__init__.py` (empty)
- Create: `software/server/src/auralink/pipeline/stages/base.py`
- Create: `software/server/tests/unit/pipeline/__init__.py` (empty)
- Create: `software/server/tests/unit/pipeline/test_base.py`

- [ ] **Step 1: Write the failing test**

`software/server/tests/unit/pipeline/test_base.py`:
```python
from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.stages.base import Stage, StageContext


def _minimal_session() -> Session:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    frame = Frame(timestamp_ms=0, landmarks=[lm for _ in range(33)])
    return Session(
        metadata=SessionMetadata(
            movement="overhead_squat",
            device="test",
            model="test",
            frame_rate=30.0,
        ),
        frames=[frame],
    )


def test_context_exposes_session_and_movement_type():
    session = _minimal_session()
    ctx = StageContext(session=session)
    assert ctx.session is session
    assert ctx.movement_type == "overhead_squat"
    assert ctx.artifacts == {}
    assert ctx.config == {}


def test_stage_runs_callable_on_context():
    session = _minimal_session()
    ctx = StageContext(session=session)
    stage = Stage(name="count_frames", run=lambda c: len(c.session.frames))
    assert stage.name == "count_frames"
    assert stage.run(ctx) == 1
```

- [ ] **Step 2: Run test to verify it fails**

`cd software/server && uv run pytest tests/unit/pipeline/test_base.py -v`
Expected: `ModuleNotFoundError: No module named 'auralink.pipeline.stages'`.

- [ ] **Step 3: Create `pipeline/stages/__init__.py` (empty)**

- [ ] **Step 4: Implement `pipeline/stages/base.py`**

```python
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from auralink.api.schemas import MovementType, Session


@dataclass
class StageContext:
    session: Session
    artifacts: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)

    @property
    def movement_type(self) -> MovementType:
        return self.session.metadata.movement


@dataclass(frozen=True)
class Stage:
    name: str
    run: Callable[[StageContext], Any]
```

- [ ] **Step 5: Create `tests/unit/pipeline/__init__.py` (empty)**

- [ ] **Step 6: Run test to verify it passes**

`cd software/server && uv run pytest tests/unit/pipeline/test_base.py -v`
Expected: `2 passed`.

- [ ] **Step 7: Commit**

```bash
git add software/server/src/auralink/pipeline/stages/__init__.py \
        software/server/src/auralink/pipeline/stages/base.py \
        software/server/tests/unit/pipeline/__init__.py \
        software/server/tests/unit/pipeline/test_base.py
git commit -m "feat(pipeline): add Stage and StageContext abstractions"
```

---

### Task 2: Pipeline artifact schemas

**Files:**
- Create: `software/server/src/auralink/pipeline/artifacts.py`
- Create: `software/server/tests/unit/pipeline/test_artifacts.py`

- [ ] **Step 1: Write the failing test**

`software/server/tests/unit/pipeline/test_artifacts.py`:
```python
import pytest
from pydantic import ValidationError

from auralink.pipeline.artifacts import (
    AngleTimeSeries,
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    PipelineArtifacts,
    QualityIssue,
    RepBoundaries,
    RepBoundaryModel,
    RepMetric,
    SessionQualityReport,
    WithinMovementTrend,
)


def test_quality_issue_requires_code_and_detail():
    issue = QualityIssue(code="low_frame_rate", detail="23.4 < 25")
    assert issue.code == "low_frame_rate"
    assert issue.detail == "23.4 < 25"


def test_session_quality_report_defaults_pass_when_empty():
    report = SessionQualityReport(passed=True, issues=[], metrics={"frame_rate": 30.0})
    assert report.passed is True
    assert report.metrics["frame_rate"] == 30.0


def test_angle_time_series_shape():
    series = AngleTimeSeries(
        angles={"left_knee_flexion": [180.0, 150.0, 120.0]},
        timestamps_ms=[0, 33, 66],
    )
    assert series.angles["left_knee_flexion"][1] == 150.0
    assert len(series.timestamps_ms) == 3


def test_normalized_angle_time_series_requires_scale_factor():
    normalized = NormalizedAngleTimeSeries(
        angles={"trunk_lean": [2.0]},
        timestamps_ms=[0],
        scale_factor=0.25,
    )
    assert normalized.scale_factor == 0.25
    with pytest.raises(ValidationError):
        NormalizedAngleTimeSeries(angles={}, timestamps_ms=[])


def test_rep_boundary_model_indices_must_be_non_negative():
    rep = RepBoundaryModel(
        start_index=0, bottom_index=14, end_index=29,
        start_angle=180.0, bottom_angle=90.0, end_angle=180.0,
    )
    assert rep.end_index == 29
    with pytest.raises(ValidationError):
        RepBoundaryModel(
            start_index=-1, bottom_index=5, end_index=10,
            start_angle=180.0, bottom_angle=90.0, end_angle=180.0,
        )


def test_rep_boundaries_keyed_by_angle_name():
    boundaries = RepBoundaries(
        by_angle={
            "left_knee_flexion": [
                RepBoundaryModel(
                    start_index=0, bottom_index=14, end_index=29,
                    start_angle=180.0, bottom_angle=90.0, end_angle=180.0,
                )
            ]
        }
    )
    assert len(boundaries.by_angle["left_knee_flexion"]) == 1


def test_per_rep_metrics_and_rep_metric():
    metrics = PerRepMetrics(
        primary_angle="left_knee_flexion",
        reps=[
            RepMetric(
                rep_index=0,
                amplitude_deg=90.0,
                peak_velocity_deg_per_s=240.0,
                rom_deg=90.0,
                mean_trunk_lean_deg=4.5,
                mean_knee_valgus_deg=3.1,
            )
        ],
    )
    assert metrics.primary_angle == "left_knee_flexion"
    assert metrics.reps[0].amplitude_deg == 90.0


def test_within_movement_trend_fatigue_flag():
    trend = WithinMovementTrend(
        rom_slope_deg_per_rep=-3.0,
        velocity_slope_deg_per_s_per_rep=-12.0,
        valgus_slope_deg_per_rep=1.5,
        trunk_lean_slope_deg_per_rep=0.5,
        fatigue_detected=True,
    )
    assert trend.fatigue_detected is True


def test_pipeline_artifacts_only_quality_report_required():
    bundle = PipelineArtifacts(
        quality_report=SessionQualityReport(passed=False, issues=[], metrics={}),
    )
    assert bundle.quality_report.passed is False
    assert bundle.angle_series is None
    assert bundle.within_movement_trend is None
```

- [ ] **Step 2: Run test to verify it fails**

`cd software/server && uv run pytest tests/unit/pipeline/test_artifacts.py -v`
Expected: `ModuleNotFoundError: No module named 'auralink.pipeline.artifacts'`.

- [ ] **Step 3: Implement `pipeline/artifacts.py`**

```python
from pydantic import BaseModel, Field


class QualityIssue(BaseModel):
    code: str
    detail: str


class SessionQualityReport(BaseModel):
    passed: bool
    issues: list[QualityIssue] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)


class AngleTimeSeries(BaseModel):
    angles: dict[str, list[float]]
    timestamps_ms: list[int]


class NormalizedAngleTimeSeries(BaseModel):
    angles: dict[str, list[float]]
    timestamps_ms: list[int]
    scale_factor: float = Field(gt=0)


class RepBoundaryModel(BaseModel):
    start_index: int = Field(ge=0)
    bottom_index: int = Field(ge=0)
    end_index: int = Field(ge=0)
    start_angle: float
    bottom_angle: float
    end_angle: float


class RepBoundaries(BaseModel):
    by_angle: dict[str, list[RepBoundaryModel]] = Field(default_factory=dict)


class RepMetric(BaseModel):
    rep_index: int = Field(ge=0)
    amplitude_deg: float
    peak_velocity_deg_per_s: float
    rom_deg: float
    mean_trunk_lean_deg: float
    mean_knee_valgus_deg: float


class PerRepMetrics(BaseModel):
    primary_angle: str
    reps: list[RepMetric] = Field(default_factory=list)


class WithinMovementTrend(BaseModel):
    rom_slope_deg_per_rep: float
    velocity_slope_deg_per_s_per_rep: float
    valgus_slope_deg_per_rep: float
    trunk_lean_slope_deg_per_rep: float
    fatigue_detected: bool


class PipelineArtifacts(BaseModel):
    quality_report: SessionQualityReport
    angle_series: AngleTimeSeries | None = None
    normalized_angle_series: NormalizedAngleTimeSeries | None = None
    rep_boundaries: RepBoundaries | None = None
    per_rep_metrics: PerRepMetrics | None = None
    within_movement_trend: WithinMovementTrend | None = None
```

- [ ] **Step 4: Run test to verify it passes**

`cd software/server && uv run pytest tests/unit/pipeline/test_artifacts.py -v`
Expected: `9 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/artifacts.py \
        software/server/tests/unit/pipeline/test_artifacts.py
git commit -m "feat(pipeline): add artifact schemas for stage outputs"
```

---

### Task 3: Error hierarchy

**Files:**
- Create: `software/server/src/auralink/pipeline/errors.py`
- Create: `software/server/tests/unit/pipeline/test_errors.py`

- [ ] **Step 1: Write the failing test**

`software/server/tests/unit/pipeline/test_errors.py`:
```python
import pytest

from auralink.pipeline.artifacts import QualityIssue, SessionQualityReport
from auralink.pipeline.errors import (
    PipelineError,
    QualityGateError,
    StageError,
)


def test_pipeline_error_is_base():
    err = PipelineError("oops")
    assert isinstance(err, Exception)
    assert str(err) == "oops"


def test_stage_error_carries_stage_name_and_detail():
    err = StageError(stage_name="angle_series", detail="NaN in input")
    assert err.stage_name == "angle_series"
    assert err.detail == "NaN in input"
    assert "angle_series" in str(err)
    assert isinstance(err, PipelineError)


def test_quality_gate_error_carries_report():
    report = SessionQualityReport(
        passed=False,
        issues=[QualityIssue(code="low_visibility", detail="avg 0.3 < 0.5")],
        metrics={"avg_visibility": 0.3},
    )
    err = QualityGateError(report=report)
    assert err.report is report
    assert err.report.issues[0].code == "low_visibility"
    assert isinstance(err, PipelineError)


def test_stage_error_raises_and_catches():
    with pytest.raises(PipelineError):
        raise StageError(stage_name="foo", detail="bar")
```

- [ ] **Step 2: Run test to verify it fails**

`cd software/server && uv run pytest tests/unit/pipeline/test_errors.py -v`
Expected: `ModuleNotFoundError: No module named 'auralink.pipeline.errors'`.

- [ ] **Step 3: Implement `pipeline/errors.py`**

```python
from auralink.pipeline.artifacts import SessionQualityReport


class PipelineError(Exception):
    """Base class for all pipeline-side errors."""


class StageError(PipelineError):
    def __init__(self, stage_name: str, detail: str):
        super().__init__(f"stage '{stage_name}' failed: {detail}")
        self.stage_name = stage_name
        self.detail = detail


class QualityGateError(PipelineError):
    def __init__(self, report: SessionQualityReport):
        issue_count = len(report.issues)
        super().__init__(f"quality gate rejected session: {issue_count} issue(s)")
        self.report = report
```

- [ ] **Step 4: Run test to verify it passes**

`cd software/server && uv run pytest tests/unit/pipeline/test_errors.py -v`
Expected: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/errors.py \
        software/server/tests/unit/pipeline/test_errors.py
git commit -m "feat(pipeline): add PipelineError hierarchy"
```

---

### Task 4: Quality gate stage

Implements four separate checks, each as its own TDD cycle with its own commit. The stage function returns a `SessionQualityReport` — it does **not** raise; the orchestrator raises `QualityGateError` when `report.passed is False`.

**Files (all work in this task):**
- Create: `software/server/src/auralink/pipeline/stages/quality_gate.py`
- Create: `software/server/tests/unit/pipeline/test_quality_gate.py`

Helper fixtures at the top of `test_quality_gate.py` — add once at Step 1 and reused across all four cycles:
```python
from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.stages.base import StageContext
from auralink.pipeline.stages.quality_gate import run_quality_gate


def _lm(visibility: float = 1.0, presence: float = 1.0) -> Landmark:
    return Landmark(x=0.5, y=0.5, z=0.0, visibility=visibility, presence=presence)


def _frame(timestamp_ms: int, visibility: float = 1.0, presence: float = 1.0) -> Frame:
    return Frame(timestamp_ms=timestamp_ms, landmarks=[_lm(visibility, presence) for _ in range(33)])


def _session(frames: list[Frame], frame_rate: float = 30.0) -> Session:
    return Session(
        metadata=SessionMetadata(
            movement="overhead_squat",
            device="test",
            model="test",
            frame_rate=frame_rate,
        ),
        frames=frames,
    )


def _ctx(session: Session) -> StageContext:
    return StageContext(session=session)
```

And a stub `quality_gate.py` that starts empty (added in Step 2):
```python
from auralink.pipeline.artifacts import QualityIssue, SessionQualityReport
from auralink.pipeline.stages.base import StageContext

MIN_FRAME_RATE = 20.0
MIN_AVG_VISIBILITY = 0.5
MIN_DURATION_S = 1.0
MAX_MISSING_LANDMARK_FRACTION = 0.05


def run_quality_gate(ctx: StageContext) -> SessionQualityReport:
    issues: list[QualityIssue] = []
    metrics: dict[str, float] = {}
    return SessionQualityReport(
        passed=not issues,
        issues=issues,
        metrics=metrics,
    )
```

#### Cycle 4a: Frame-rate check

- [ ] **Step 1: Write the failing test + create helper file + stub module**

Append to `tests/unit/pipeline/test_quality_gate.py`:
```python
def test_rejects_low_frame_rate():
    session = _session([_frame(i * 100) for i in range(30)], frame_rate=15.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is False
    assert any(issue.code == "low_frame_rate" for issue in report.issues)
    assert report.metrics["frame_rate"] == 15.0


def test_accepts_normal_frame_rate():
    session = _session([_frame(i * 33) for i in range(30)], frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is True
    assert report.issues == []
```

- [ ] **Step 2: Run test to verify it fails**

`cd software/server && uv run pytest tests/unit/pipeline/test_quality_gate.py::test_rejects_low_frame_rate -v`
Expected: assertion error on `report.passed is False`.

- [ ] **Step 3: Implement frame-rate check in `quality_gate.py`**

Replace the body of `run_quality_gate`:
```python
def run_quality_gate(ctx: StageContext) -> SessionQualityReport:
    issues: list[QualityIssue] = []
    metrics: dict[str, float] = {}

    frame_rate = ctx.session.metadata.frame_rate
    metrics["frame_rate"] = frame_rate
    if frame_rate < MIN_FRAME_RATE:
        issues.append(
            QualityIssue(
                code="low_frame_rate",
                detail=f"{frame_rate:.1f} fps < {MIN_FRAME_RATE:.0f} fps minimum",
            )
        )

    return SessionQualityReport(passed=not issues, issues=issues, metrics=metrics)
```

- [ ] **Step 4: Run tests to verify pass**

`cd software/server && uv run pytest tests/unit/pipeline/test_quality_gate.py -v`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/stages/quality_gate.py \
        software/server/tests/unit/pipeline/test_quality_gate.py
git commit -m "feat(pipeline): quality gate - frame rate check"
```

#### Cycle 4b: Visibility check

- [ ] **Step 1: Write the failing test**

Append to `test_quality_gate.py`:
```python
def test_rejects_low_average_visibility():
    frames = [_frame(i * 33, visibility=0.3) for i in range(30)]
    session = _session(frames, frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is False
    assert any(issue.code == "low_visibility" for issue in report.issues)
    assert report.metrics["avg_visibility"] == pytest.approx(0.3)


def test_accepts_good_visibility():
    frames = [_frame(i * 33, visibility=0.9) for i in range(30)]
    session = _session(frames, frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is True
```

Also add `import pytest` at the top of the file if not already there.

- [ ] **Step 2: Run and verify it fails**

`cd software/server && uv run pytest tests/unit/pipeline/test_quality_gate.py -v`
Expected: the low-visibility test fails (no visibility logic yet).

- [ ] **Step 3: Add visibility check to `run_quality_gate`**

After the frame-rate block and before the return, add:
```python
    all_vis: list[float] = []
    for frame in ctx.session.frames:
        for lm in frame.landmarks:
            all_vis.append(lm.visibility)
    avg_vis = sum(all_vis) / len(all_vis) if all_vis else 0.0
    metrics["avg_visibility"] = avg_vis
    if avg_vis < MIN_AVG_VISIBILITY:
        issues.append(
            QualityIssue(
                code="low_visibility",
                detail=f"avg visibility {avg_vis:.2f} < {MIN_AVG_VISIBILITY:.2f}",
            )
        )
```

- [ ] **Step 4: Run all quality gate tests**

`cd software/server && uv run pytest tests/unit/pipeline/test_quality_gate.py -v`
Expected: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/stages/quality_gate.py \
        software/server/tests/unit/pipeline/test_quality_gate.py
git commit -m "feat(pipeline): quality gate - average visibility check"
```

#### Cycle 4c: Duration check

- [ ] **Step 1: Write the failing test**

Append to `test_quality_gate.py`:
```python
def test_rejects_short_session():
    frames = [_frame(i * 33) for i in range(20)]
    session = _session(frames, frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is False
    assert any(issue.code == "short_duration" for issue in report.issues)


def test_accepts_session_with_sufficient_duration():
    frames = [_frame(i * 33) for i in range(40)]
    session = _session(frames, frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is True
```

- [ ] **Step 2: Run and verify failure**

`cd software/server && uv run pytest tests/unit/pipeline/test_quality_gate.py -v`
Expected: short-duration test fails.

- [ ] **Step 3: Add duration check**

Add after the visibility block:
```python
    frame_count = len(ctx.session.frames)
    duration_s = frame_count / frame_rate if frame_rate > 0 else 0.0
    metrics["duration_s"] = duration_s
    if duration_s < MIN_DURATION_S:
        issues.append(
            QualityIssue(
                code="short_duration",
                detail=f"{duration_s:.2f}s < {MIN_DURATION_S:.1f}s minimum",
            )
        )
```

- [ ] **Step 4: Run all quality gate tests**

`cd software/server && uv run pytest tests/unit/pipeline/test_quality_gate.py -v`
Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/stages/quality_gate.py \
        software/server/tests/unit/pipeline/test_quality_gate.py
git commit -m "feat(pipeline): quality gate - duration check"
```

#### Cycle 4d: Missing-landmark check

- [ ] **Step 1: Write the failing test**

Append to `test_quality_gate.py`:
```python
def test_rejects_many_missing_landmarks():
    # presence < 0.5 counts as missing; build frames where 10% of landmarks are missing
    frames = []
    for i in range(30):
        landmarks = [_lm(visibility=1.0, presence=1.0) for _ in range(30)]
        landmarks.extend([_lm(visibility=1.0, presence=0.2) for _ in range(3)])
        frames.append(Frame(timestamp_ms=i * 33, landmarks=landmarks))
    session = _session(frames, frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is False
    assert any(issue.code == "missing_landmarks" for issue in report.issues)


def test_accepts_few_missing_landmarks():
    frames = [_frame(i * 33, presence=1.0) for i in range(30)]
    session = _session(frames, frame_rate=30.0)
    report = run_quality_gate(_ctx(session))
    assert report.passed is True
```

- [ ] **Step 2: Run and verify failure**

Expected: the many-missing-landmarks test fails (no missing-landmark logic yet).

- [ ] **Step 3: Add missing-landmark check**

Add after the duration block, before the return:
```python
    total_landmarks = 0
    missing_landmarks = 0
    for frame in ctx.session.frames:
        for lm in frame.landmarks:
            total_landmarks += 1
            if lm.presence < 0.5:
                missing_landmarks += 1
    missing_fraction = missing_landmarks / total_landmarks if total_landmarks else 0.0
    metrics["missing_landmark_fraction"] = missing_fraction
    if missing_fraction > MAX_MISSING_LANDMARK_FRACTION:
        issues.append(
            QualityIssue(
                code="missing_landmarks",
                detail=f"{missing_fraction:.1%} missing > {MAX_MISSING_LANDMARK_FRACTION:.0%}",
            )
        )
```

- [ ] **Step 4: Run all quality gate tests**

`cd software/server && uv run pytest tests/unit/pipeline/test_quality_gate.py -v`
Expected: `8 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/stages/quality_gate.py \
        software/server/tests/unit/pipeline/test_quality_gate.py
git commit -m "feat(pipeline): quality gate - missing landmark fraction check"
```

---

### Task 5: Angle time-series stage

Adds `trunk_lean_angle()` to `pose/joint_angles.py` (new function) and builds the `angle_series` stage that computes the seven tracked angles per frame.

**Files:**
- Modify: `software/server/src/auralink/pose/joint_angles.py`
- Create: `software/server/tests/unit/pose/test_trunk_lean_angle.py`
- Create: `software/server/src/auralink/pipeline/stages/angle_series.py`
- Create: `software/server/tests/unit/pipeline/test_angle_series.py`

#### Cycle 5a: `trunk_lean_angle`

- [ ] **Step 1: Write the failing test**

`software/server/tests/unit/pose/test_trunk_lean_angle.py`:
```python
import math

import pytest

from auralink.api.schemas import Frame, Landmark
from auralink.pose.joint_angles import trunk_lean_angle


def _frame_with(left_sh, right_sh, left_hip, right_hip) -> Frame:
    base = [Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0, presence=1.0) for _ in range(33)]
    base[11] = Landmark(x=left_sh[0], y=left_sh[1], z=0.0, visibility=1.0, presence=1.0)
    base[12] = Landmark(x=right_sh[0], y=right_sh[1], z=0.0, visibility=1.0, presence=1.0)
    base[23] = Landmark(x=left_hip[0], y=left_hip[1], z=0.0, visibility=1.0, presence=1.0)
    base[24] = Landmark(x=right_hip[0], y=right_hip[1], z=0.0, visibility=1.0, presence=1.0)
    return Frame(timestamp_ms=0, landmarks=base)


def test_trunk_vertical_is_zero():
    # shoulder midpoint directly above hip midpoint (image y decreases upward, so shoulder y < hip y)
    frame = _frame_with(
        left_sh=(0.45, 0.3), right_sh=(0.55, 0.3),
        left_hip=(0.45, 0.5), right_hip=(0.55, 0.5),
    )
    assert trunk_lean_angle(frame) == pytest.approx(0.0, abs=1e-6)


def test_trunk_leaning_forward_45_degrees():
    # shoulder midpoint 45 degrees forward (+x) of hip midpoint
    # hip mid at (0.5, 0.5); shoulder mid at (0.5 + d, 0.5 - d) for any d>0 → 45°
    frame = _frame_with(
        left_sh=(0.65, 0.35), right_sh=(0.75, 0.35),
        left_hip=(0.45, 0.55), right_hip=(0.55, 0.55),
    )
    assert trunk_lean_angle(frame) == pytest.approx(45.0, abs=1.0)


def test_trunk_with_zero_length_trunk_returns_zero():
    frame = _frame_with(
        left_sh=(0.5, 0.5), right_sh=(0.5, 0.5),
        left_hip=(0.5, 0.5), right_hip=(0.5, 0.5),
    )
    assert trunk_lean_angle(frame) == 0.0
```

Also create `software/server/tests/unit/pose/__init__.py` if it does not yet exist.

- [ ] **Step 2: Run and verify failure**

`cd software/server && uv run pytest tests/unit/pose/test_trunk_lean_angle.py -v`
Expected: `ImportError: cannot import name 'trunk_lean_angle'`.

- [ ] **Step 3: Implement `trunk_lean_angle` in `pose/joint_angles.py`**

Append to the end of the file:
```python
def trunk_lean_angle(frame: Frame) -> float:
    """Trunk lean — angle between the trunk axis and the image vertical.

    Trunk axis = shoulder midpoint minus hip midpoint. Vertical is (0, -1)
    because image y increases downward. Returned in degrees, always >= 0.
    """
    l_sh = _xy(frame, LandmarkIndex.LEFT_SHOULDER)
    r_sh = _xy(frame, LandmarkIndex.RIGHT_SHOULDER)
    l_hip = _xy(frame, LandmarkIndex.LEFT_HIP)
    r_hip = _xy(frame, LandmarkIndex.RIGHT_HIP)
    shoulder_mid = (l_sh + r_sh) / 2.0
    hip_mid = (l_hip + r_hip) / 2.0
    trunk = shoulder_mid - hip_mid
    norm = float(np.linalg.norm(trunk))
    if norm == 0.0:
        return 0.0
    vertical = np.array([0.0, -1.0], dtype=np.float64)
    cos_angle = float(np.dot(trunk, vertical) / norm)
    cos_angle = max(-1.0, min(1.0, cos_angle))
    return float(np.degrees(np.arccos(cos_angle)))
```

- [ ] **Step 4: Run test to verify pass**

`cd software/server && uv run pytest tests/unit/pose/test_trunk_lean_angle.py -v`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pose/joint_angles.py \
        software/server/tests/unit/pose/__init__.py \
        software/server/tests/unit/pose/test_trunk_lean_angle.py
git commit -m "feat(pose): add trunk_lean_angle computation"
```

#### Cycle 5b: `angle_series` stage

- [ ] **Step 1: Write the failing test**

`software/server/tests/unit/pipeline/test_angle_series.py`:
```python
from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.stages.angle_series import TRACKED_ANGLE_NAMES, run_angle_series
from auralink.pipeline.stages.base import StageContext


def _frame(timestamp_ms: int) -> Frame:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    return Frame(timestamp_ms=timestamp_ms, landmarks=[lm for _ in range(33)])


def _session(frame_count: int) -> Session:
    return Session(
        metadata=SessionMetadata(
            movement="overhead_squat", device="t", model="t", frame_rate=30.0
        ),
        frames=[_frame(i * 33) for i in range(frame_count)],
    )


def test_angle_series_produces_one_entry_per_tracked_angle():
    ctx = StageContext(session=_session(10))
    result = run_angle_series(ctx)
    assert set(result.angles.keys()) == set(TRACKED_ANGLE_NAMES)
    assert result.timestamps_ms == [i * 33 for i in range(10)]


def test_angle_series_values_match_frame_count():
    ctx = StageContext(session=_session(12))
    result = run_angle_series(ctx)
    for name in TRACKED_ANGLE_NAMES:
        assert len(result.angles[name]) == 12


def test_tracked_angle_names_are_canonical():
    assert "left_knee_flexion" in TRACKED_ANGLE_NAMES
    assert "right_knee_flexion" in TRACKED_ANGLE_NAMES
    assert "left_knee_valgus" in TRACKED_ANGLE_NAMES
    assert "right_knee_valgus" in TRACKED_ANGLE_NAMES
    assert "left_hip_flexion" in TRACKED_ANGLE_NAMES
    assert "right_hip_flexion" in TRACKED_ANGLE_NAMES
    assert "trunk_lean" in TRACKED_ANGLE_NAMES
```

- [ ] **Step 2: Run and verify failure**

`cd software/server && uv run pytest tests/unit/pipeline/test_angle_series.py -v`
Expected: module import error.

- [ ] **Step 3: Implement `pipeline/stages/angle_series.py`**

```python
from auralink.api.schemas import Frame
from auralink.pipeline.artifacts import AngleTimeSeries
from auralink.pipeline.stages.base import StageContext
from auralink.pose.joint_angles import (
    hip_flexion_angle,
    knee_flexion_angle,
    knee_valgus_angle,
    trunk_lean_angle,
)

TRACKED_ANGLE_NAMES = (
    "left_knee_flexion",
    "right_knee_flexion",
    "left_hip_flexion",
    "right_hip_flexion",
    "left_knee_valgus",
    "right_knee_valgus",
    "trunk_lean",
)


def _compute_angle(name: str, frame: Frame) -> float:
    if name == "left_knee_flexion":
        return knee_flexion_angle(frame, "left")
    if name == "right_knee_flexion":
        return knee_flexion_angle(frame, "right")
    if name == "left_hip_flexion":
        return hip_flexion_angle(frame, "left")
    if name == "right_hip_flexion":
        return hip_flexion_angle(frame, "right")
    if name == "left_knee_valgus":
        return knee_valgus_angle(frame, "left")
    if name == "right_knee_valgus":
        return knee_valgus_angle(frame, "right")
    if name == "trunk_lean":
        return trunk_lean_angle(frame)
    raise ValueError(f"unknown tracked angle: {name}")


def run_angle_series(ctx: StageContext) -> AngleTimeSeries:
    frames = ctx.session.frames
    timestamps = [f.timestamp_ms for f in frames]
    angles: dict[str, list[float]] = {
        name: [_compute_angle(name, f) for f in frames] for name in TRACKED_ANGLE_NAMES
    }
    return AngleTimeSeries(angles=angles, timestamps_ms=timestamps)
```

- [ ] **Step 4: Run tests**

`cd software/server && uv run pytest tests/unit/pipeline/test_angle_series.py -v`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/stages/angle_series.py \
        software/server/tests/unit/pipeline/test_angle_series.py
git commit -m "feat(pipeline): add angle_series stage computing 7 tracked angles"
```

---

### Task 6: Normalization stage

Reads scale factor = median hip-shoulder distance across frames, and re-emits the same angle series as `NormalizedAngleTimeSeries` with `scale_factor` attached. Angles themselves are scale-invariant, so normalization only records the scale factor for downstream stages (Plan 3 DTW).

**Files:**
- Create: `software/server/src/auralink/pipeline/stages/normalize.py`
- Create: `software/server/tests/unit/pipeline/test_normalize.py`

- [ ] **Step 1: Write the failing test**

`software/server/tests/unit/pipeline/test_normalize.py`:
```python
import pytest

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.artifacts import AngleTimeSeries
from auralink.pipeline.stages.base import StageContext
from auralink.pipeline.stages.normalize import run_normalize


def _frame(shoulder_y: float, hip_y: float) -> Frame:
    base = [Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0, presence=1.0) for _ in range(33)]
    base[11] = Landmark(x=0.5, y=shoulder_y, z=0.0, visibility=1.0, presence=1.0)
    base[12] = Landmark(x=0.5, y=shoulder_y, z=0.0, visibility=1.0, presence=1.0)
    base[23] = Landmark(x=0.5, y=hip_y, z=0.0, visibility=1.0, presence=1.0)
    base[24] = Landmark(x=0.5, y=hip_y, z=0.0, visibility=1.0, presence=1.0)
    return Frame(timestamp_ms=0, landmarks=base)


def _session() -> Session:
    return Session(
        metadata=SessionMetadata(
            movement="overhead_squat", device="t", model="t", frame_rate=30.0
        ),
        frames=[_frame(0.3, 0.6)],
    )


def test_normalize_emits_scale_factor_from_hip_shoulder_distance():
    ctx = StageContext(session=_session())
    ctx.artifacts["angle_series"] = AngleTimeSeries(
        angles={"trunk_lean": [5.0]},
        timestamps_ms=[0],
    )
    result = run_normalize(ctx)
    assert result.scale_factor == pytest.approx(0.3, abs=1e-6)
    assert result.angles == {"trunk_lean": [5.0]}
    assert result.timestamps_ms == [0]


def test_normalize_zero_distance_falls_back_to_small_positive():
    session = Session(
        metadata=SessionMetadata(
            movement="overhead_squat", device="t", model="t", frame_rate=30.0
        ),
        frames=[_frame(0.5, 0.5)],
    )
    ctx = StageContext(session=session)
    ctx.artifacts["angle_series"] = AngleTimeSeries(angles={}, timestamps_ms=[0])
    result = run_normalize(ctx)
    assert result.scale_factor > 0.0
```

- [ ] **Step 2: Run and verify failure**

`cd software/server && uv run pytest tests/unit/pipeline/test_normalize.py -v`
Expected: module not found.

- [ ] **Step 3: Implement `pipeline/stages/normalize.py`**

```python
import numpy as np

from auralink.api.schemas import Frame
from auralink.pipeline.artifacts import AngleTimeSeries, NormalizedAngleTimeSeries
from auralink.pipeline.stages.base import StageContext
from auralink.pose.keypoints import LandmarkIndex

_FALLBACK_SCALE = 1e-6


def _hip_shoulder_distance(frame: Frame) -> float:
    l_sh = frame.landmarks[LandmarkIndex.LEFT_SHOULDER]
    r_sh = frame.landmarks[LandmarkIndex.RIGHT_SHOULDER]
    l_hip = frame.landmarks[LandmarkIndex.LEFT_HIP]
    r_hip = frame.landmarks[LandmarkIndex.RIGHT_HIP]
    sh_mid = np.array([(l_sh.x + r_sh.x) / 2, (l_sh.y + r_sh.y) / 2])
    hip_mid = np.array([(l_hip.x + r_hip.x) / 2, (l_hip.y + r_hip.y) / 2])
    return float(np.linalg.norm(sh_mid - hip_mid))


def run_normalize(ctx: StageContext) -> NormalizedAngleTimeSeries:
    raw: AngleTimeSeries = ctx.artifacts["angle_series"]
    distances = [_hip_shoulder_distance(f) for f in ctx.session.frames]
    scale = float(np.median(distances)) if distances else _FALLBACK_SCALE
    if scale <= 0.0:
        scale = _FALLBACK_SCALE
    return NormalizedAngleTimeSeries(
        angles=raw.angles,
        timestamps_ms=raw.timestamps_ms,
        scale_factor=scale,
    )
```

- [ ] **Step 4: Run tests**

`cd software/server && uv run pytest tests/unit/pipeline/test_normalize.py -v`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/stages/normalize.py \
        software/server/tests/unit/pipeline/test_normalize.py
git commit -m "feat(pipeline): add normalize stage recording hip-shoulder scale factor"
```

---

### Task 7: Rep segmentation stage

Wraps the existing `analysis.rep_segmentation.segment_reps` and runs it over the primary rep-carrying angles for the movement. For `overhead_squat` and `single_leg_squat`, primary angles are `left_knee_flexion` and `right_knee_flexion`.

**Files:**
- Create: `software/server/src/auralink/pipeline/stages/rep_segment.py`
- Create: `software/server/tests/unit/pipeline/test_rep_segment.py`

- [ ] **Step 1: Write the failing test**

`software/server/tests/unit/pipeline/test_rep_segment.py`:
```python
import numpy as np

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.artifacts import NormalizedAngleTimeSeries
from auralink.pipeline.stages.base import StageContext
from auralink.pipeline.stages.rep_segment import (
    PRIMARY_REP_ANGLES_BY_MOVEMENT,
    run_rep_segment,
)


def _ctx_with_angles(movement: str, angle_lookup: dict[str, list[float]]) -> StageContext:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    frames = [Frame(timestamp_ms=i * 33, landmarks=[lm for _ in range(33)]) for i in range(len(next(iter(angle_lookup.values()))))]
    session = Session(
        metadata=SessionMetadata(movement=movement, device="t", model="t", frame_rate=30.0),
        frames=frames,
    )
    ctx = StageContext(session=session)
    ctx.artifacts["normalize"] = NormalizedAngleTimeSeries(
        angles=angle_lookup,
        timestamps_ms=[f.timestamp_ms for f in frames],
        scale_factor=0.3,
    )
    return ctx


def test_rep_segment_identifies_two_reps_in_squat_pattern():
    descent = np.linspace(180, 90, 15).tolist()
    ascent = np.linspace(90, 180, 15).tolist()
    one_rep = descent + ascent
    series = one_rep + one_rep
    ctx = _ctx_with_angles(
        "overhead_squat",
        {"left_knee_flexion": series, "right_knee_flexion": series, "trunk_lean": [0.0] * len(series)},
    )
    result = run_rep_segment(ctx)
    assert "left_knee_flexion" in result.by_angle
    assert len(result.by_angle["left_knee_flexion"]) == 2
    assert len(result.by_angle["right_knee_flexion"]) == 2


def test_rep_segment_returns_empty_for_flat_signal():
    flat = [180.0] * 60
    ctx = _ctx_with_angles(
        "overhead_squat",
        {"left_knee_flexion": flat, "right_knee_flexion": flat, "trunk_lean": [0.0] * 60},
    )
    result = run_rep_segment(ctx)
    assert result.by_angle["left_knee_flexion"] == []


def test_primary_angles_table_covers_squat_movements():
    assert PRIMARY_REP_ANGLES_BY_MOVEMENT["overhead_squat"] == ("left_knee_flexion", "right_knee_flexion")
    assert PRIMARY_REP_ANGLES_BY_MOVEMENT["single_leg_squat"] == ("left_knee_flexion", "right_knee_flexion")
```

- [ ] **Step 2: Run and verify failure**

`cd software/server && uv run pytest tests/unit/pipeline/test_rep_segment.py -v`
Expected: module not found.

- [ ] **Step 3: Implement `pipeline/stages/rep_segment.py`**

```python
from auralink.analysis.rep_segmentation import segment_reps
from auralink.api.schemas import MovementType
from auralink.pipeline.artifacts import NormalizedAngleTimeSeries, RepBoundaries, RepBoundaryModel
from auralink.pipeline.stages.base import StageContext

PRIMARY_REP_ANGLES_BY_MOVEMENT: dict[MovementType, tuple[str, ...]] = {
    "overhead_squat": ("left_knee_flexion", "right_knee_flexion"),
    "single_leg_squat": ("left_knee_flexion", "right_knee_flexion"),
}

MIN_AMPLITUDE_DEG = 30.0


def run_rep_segment(ctx: StageContext) -> RepBoundaries:
    normalized: NormalizedAngleTimeSeries = ctx.artifacts["normalize"]
    primary = PRIMARY_REP_ANGLES_BY_MOVEMENT.get(ctx.movement_type, ())
    by_angle: dict[str, list[RepBoundaryModel]] = {}
    for angle_name in primary:
        series = normalized.angles.get(angle_name, [])
        raw_reps = segment_reps(series, min_amplitude=MIN_AMPLITUDE_DEG)
        by_angle[angle_name] = [
            RepBoundaryModel(
                start_index=rep.start_index,
                bottom_index=rep.bottom_index,
                end_index=rep.end_index,
                start_angle=rep.start_angle,
                bottom_angle=rep.bottom_angle,
                end_angle=rep.end_angle,
            )
            for rep in raw_reps
        ]
    return RepBoundaries(by_angle=by_angle)
```

- [ ] **Step 4: Run tests**

`cd software/server && uv run pytest tests/unit/pipeline/test_rep_segment.py -v`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/stages/rep_segment.py \
        software/server/tests/unit/pipeline/test_rep_segment.py
git commit -m "feat(pipeline): add rep_segment stage wrapping segment_reps"
```

---

### Task 8: Per-rep metrics stage

For each rep in the left-knee-flexion series (the primary angle used for rep indexing), compute:
- `amplitude_deg`: max start/end angle minus bottom angle
- `peak_velocity_deg_per_s`: max |Δangle| * frame_rate over the rep window
- `rom_deg`: max(angle) − min(angle) over the rep window
- `mean_trunk_lean_deg`: average trunk_lean over the rep window
- `mean_knee_valgus_deg`: average of max(left_knee_valgus, right_knee_valgus) per frame

Only the primary angle for the movement (`left_knee_flexion`) is used as the rep-index source — reuses the left side for simplicity in this plan; Plan 2 extends reasoning to bilateral signals.

**Files:**
- Create: `software/server/src/auralink/pipeline/stages/per_rep_metrics.py`
- Create: `software/server/tests/unit/pipeline/test_per_rep_metrics.py`

- [ ] **Step 1: Write the failing test**

`software/server/tests/unit/pipeline/test_per_rep_metrics.py`:
```python
import numpy as np

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.artifacts import (
    NormalizedAngleTimeSeries,
    RepBoundaries,
    RepBoundaryModel,
)
from auralink.pipeline.stages.base import StageContext
from auralink.pipeline.stages.per_rep_metrics import run_per_rep_metrics


def _ctx(knee_flex: list[float], trunk: list[float], valgus_l: list[float], valgus_r: list[float]):
    n = len(knee_flex)
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    frames = [Frame(timestamp_ms=i * 33, landmarks=[lm] * 33) for i in range(n)]
    session = Session(
        metadata=SessionMetadata(
            movement="overhead_squat", device="t", model="t", frame_rate=30.0
        ),
        frames=frames,
    )
    ctx = StageContext(session=session)
    ctx.artifacts["normalize"] = NormalizedAngleTimeSeries(
        angles={
            "left_knee_flexion": knee_flex,
            "right_knee_flexion": knee_flex,
            "trunk_lean": trunk,
            "left_knee_valgus": valgus_l,
            "right_knee_valgus": valgus_r,
        },
        timestamps_ms=[f.timestamp_ms for f in frames],
        scale_factor=0.3,
    )
    ctx.artifacts["rep_segment"] = RepBoundaries(
        by_angle={
            "left_knee_flexion": [
                RepBoundaryModel(
                    start_index=0, bottom_index=n // 2, end_index=n - 1,
                    start_angle=knee_flex[0],
                    bottom_angle=knee_flex[n // 2],
                    end_angle=knee_flex[n - 1],
                )
            ]
        }
    )
    return ctx


def test_per_rep_metrics_computes_amplitude_rom_and_velocity():
    descent = np.linspace(180, 90, 15).tolist()
    ascent = np.linspace(90, 180, 15).tolist()
    knee = descent + ascent
    trunk = [5.0] * len(knee)
    valgus_l = [3.0] * len(knee)
    valgus_r = [1.0] * len(knee)
    ctx = _ctx(knee, trunk, valgus_l, valgus_r)

    result = run_per_rep_metrics(ctx)
    assert result.primary_angle == "left_knee_flexion"
    assert len(result.reps) == 1
    rep = result.reps[0]
    assert rep.rep_index == 0
    assert rep.amplitude_deg == 90.0
    assert rep.rom_deg == 90.0
    # peak |delta| ~ (180-90)/14 ~ 6.43 degrees per frame * 30 fps ~ 193 deg/s
    assert 150 < rep.peak_velocity_deg_per_s < 250
    assert rep.mean_trunk_lean_deg == 5.0
    assert rep.mean_knee_valgus_deg == 3.0  # max(3.0, 1.0) averaged


def test_per_rep_metrics_empty_when_no_reps():
    n = 30
    ctx = _ctx([180.0] * n, [0.0] * n, [0.0] * n, [0.0] * n)
    ctx.artifacts["rep_segment"] = RepBoundaries(by_angle={"left_knee_flexion": []})
    result = run_per_rep_metrics(ctx)
    assert result.reps == []
```

- [ ] **Step 2: Run and verify failure**

`cd software/server && uv run pytest tests/unit/pipeline/test_per_rep_metrics.py -v`
Expected: module not found.

- [ ] **Step 3: Implement `pipeline/stages/per_rep_metrics.py`**

```python
import numpy as np

from auralink.pipeline.artifacts import (
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    RepBoundaries,
    RepMetric,
)
from auralink.pipeline.stages.base import StageContext

PRIMARY_ANGLE = "left_knee_flexion"


def _slice(series: list[float], start: int, end: int) -> list[float]:
    return series[start : end + 1]


def run_per_rep_metrics(ctx: StageContext) -> PerRepMetrics:
    normalized: NormalizedAngleTimeSeries = ctx.artifacts["normalize"]
    reps: RepBoundaries = ctx.artifacts["rep_segment"]
    frame_rate = ctx.session.metadata.frame_rate
    boundaries = reps.by_angle.get(PRIMARY_ANGLE, [])

    knee = normalized.angles.get(PRIMARY_ANGLE, [])
    trunk = normalized.angles.get("trunk_lean", [])
    valgus_l = normalized.angles.get("left_knee_valgus", [])
    valgus_r = normalized.angles.get("right_knee_valgus", [])

    out: list[RepMetric] = []
    for idx, rep in enumerate(boundaries):
        window = _slice(knee, rep.start_index, rep.end_index)
        rom = float(max(window) - min(window)) if window else 0.0
        amplitude = float(max(rep.start_angle, rep.end_angle) - rep.bottom_angle)

        if len(window) >= 2:
            deltas = np.abs(np.diff(np.asarray(window, dtype=np.float64)))
            peak_velocity = float(np.max(deltas) * frame_rate)
        else:
            peak_velocity = 0.0

        trunk_window = _slice(trunk, rep.start_index, rep.end_index) or [0.0]
        valgus_left_window = _slice(valgus_l, rep.start_index, rep.end_index) or [0.0]
        valgus_right_window = _slice(valgus_r, rep.start_index, rep.end_index) or [0.0]
        mean_trunk = float(np.mean(trunk_window))
        per_frame_max_valgus = [
            max(a, b) for a, b in zip(valgus_left_window, valgus_right_window, strict=False)
        ]
        mean_valgus = float(np.mean(per_frame_max_valgus)) if per_frame_max_valgus else 0.0

        out.append(
            RepMetric(
                rep_index=idx,
                amplitude_deg=amplitude,
                peak_velocity_deg_per_s=peak_velocity,
                rom_deg=rom,
                mean_trunk_lean_deg=mean_trunk,
                mean_knee_valgus_deg=mean_valgus,
            )
        )

    return PerRepMetrics(primary_angle=PRIMARY_ANGLE, reps=out)
```

- [ ] **Step 4: Run tests**

`cd software/server && uv run pytest tests/unit/pipeline/test_per_rep_metrics.py -v`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/stages/per_rep_metrics.py \
        software/server/tests/unit/pipeline/test_per_rep_metrics.py
git commit -m "feat(pipeline): add per_rep_metrics stage computing amplitude/rom/velocity"
```

---

### Task 9: Within-movement trend stage

Computes linear slopes over per-rep metrics (`rom_deg`, `peak_velocity_deg_per_s`, `mean_knee_valgus_deg`, `mean_trunk_lean_deg`) and flags `fatigue_detected` when `rom_slope <= -2.0` or `valgus_slope >= 1.0` or `trunk_lean_slope >= 1.0`.

**Files:**
- Create: `software/server/src/auralink/pipeline/stages/within_movement_trend.py`
- Create: `software/server/tests/unit/pipeline/test_within_movement_trend.py`

- [ ] **Step 1: Write the failing test**

`software/server/tests/unit/pipeline/test_within_movement_trend.py`:
```python
from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.artifacts import PerRepMetrics, RepMetric
from auralink.pipeline.stages.base import StageContext
from auralink.pipeline.stages.within_movement_trend import run_within_movement_trend


def _ctx_with_reps(reps: list[RepMetric]) -> StageContext:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    session = Session(
        metadata=SessionMetadata(
            movement="overhead_squat", device="t", model="t", frame_rate=30.0
        ),
        frames=[Frame(timestamp_ms=0, landmarks=[lm] * 33)],
    )
    ctx = StageContext(session=session)
    ctx.artifacts["per_rep_metrics"] = PerRepMetrics(primary_angle="left_knee_flexion", reps=reps)
    return ctx


def _rep(i: int, rom: float, vel: float, valgus: float, trunk: float) -> RepMetric:
    return RepMetric(
        rep_index=i,
        amplitude_deg=rom,
        peak_velocity_deg_per_s=vel,
        rom_deg=rom,
        mean_trunk_lean_deg=trunk,
        mean_knee_valgus_deg=valgus,
    )


def test_within_movement_trend_detects_decreasing_rom_as_fatigue():
    reps = [
        _rep(0, rom=90, vel=200, valgus=2, trunk=3),
        _rep(1, rom=85, vel=195, valgus=3, trunk=3),
        _rep(2, rom=78, vel=180, valgus=4, trunk=4),
        _rep(3, rom=72, vel=170, valgus=6, trunk=5),
    ]
    result = run_within_movement_trend(_ctx_with_reps(reps))
    assert result.rom_slope_deg_per_rep < -5.0
    assert result.fatigue_detected is True


def test_within_movement_trend_clean_session_no_fatigue():
    reps = [
        _rep(0, rom=90, vel=200, valgus=2, trunk=3),
        _rep(1, rom=91, vel=201, valgus=2, trunk=3),
        _rep(2, rom=90, vel=200, valgus=2, trunk=3),
        _rep(3, rom=91, vel=202, valgus=2, trunk=3),
    ]
    result = run_within_movement_trend(_ctx_with_reps(reps))
    assert result.fatigue_detected is False
    assert abs(result.rom_slope_deg_per_rep) < 1.0


def test_within_movement_trend_empty_reps_produces_zero_slopes():
    result = run_within_movement_trend(_ctx_with_reps([]))
    assert result.rom_slope_deg_per_rep == 0.0
    assert result.fatigue_detected is False
```

- [ ] **Step 2: Run and verify failure**

`cd software/server && uv run pytest tests/unit/pipeline/test_within_movement_trend.py -v`
Expected: module not found.

- [ ] **Step 3: Implement `pipeline/stages/within_movement_trend.py`**

```python
import numpy as np

from auralink.pipeline.artifacts import PerRepMetrics, WithinMovementTrend
from auralink.pipeline.stages.base import StageContext

FATIGUE_ROM_SLOPE_THRESHOLD = -2.0
FATIGUE_VALGUS_SLOPE_THRESHOLD = 1.0
FATIGUE_TRUNK_LEAN_SLOPE_THRESHOLD = 1.0


def _slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    xs = np.arange(len(values), dtype=np.float64)
    ys = np.asarray(values, dtype=np.float64)
    slope, _intercept = np.polyfit(xs, ys, 1)
    return float(slope)


def run_within_movement_trend(ctx: StageContext) -> WithinMovementTrend:
    metrics: PerRepMetrics = ctx.artifacts["per_rep_metrics"]
    reps = metrics.reps
    rom_slope = _slope([r.rom_deg for r in reps])
    vel_slope = _slope([r.peak_velocity_deg_per_s for r in reps])
    valgus_slope = _slope([r.mean_knee_valgus_deg for r in reps])
    trunk_slope = _slope([r.mean_trunk_lean_deg for r in reps])

    fatigue = (
        rom_slope <= FATIGUE_ROM_SLOPE_THRESHOLD
        or valgus_slope >= FATIGUE_VALGUS_SLOPE_THRESHOLD
        or trunk_slope >= FATIGUE_TRUNK_LEAN_SLOPE_THRESHOLD
    )

    return WithinMovementTrend(
        rom_slope_deg_per_rep=rom_slope,
        velocity_slope_deg_per_s_per_rep=vel_slope,
        valgus_slope_deg_per_rep=valgus_slope,
        trunk_lean_slope_deg_per_rep=trunk_slope,
        fatigue_detected=fatigue,
    )
```

- [ ] **Step 4: Run tests**

`cd software/server && uv run pytest tests/unit/pipeline/test_within_movement_trend.py -v`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/stages/within_movement_trend.py \
        software/server/tests/unit/pipeline/test_within_movement_trend.py
git commit -m "feat(pipeline): add within_movement_trend stage for fatigue detection"
```

---

### Task 10: `StageRegistry` + orchestrator

Replaces the orchestrator stub with a real implementation and introduces `StageRegistry` as a separate module so Plan 4 can `import` and extend the default registry.

**Files:**
- Create: `software/server/src/auralink/pipeline/registry.py`
- Create: `software/server/tests/unit/pipeline/test_registry.py`
- Modify: `software/server/src/auralink/pipeline/orchestrator.py`
- Create: `software/server/tests/unit/pipeline/test_orchestrator.py`

#### Cycle 10a: `StageRegistry`

- [ ] **Step 1: Write the failing test**

`software/server/tests/unit/pipeline/test_registry.py`:
```python
import pytest

from auralink.pipeline.errors import PipelineError
from auralink.pipeline.registry import StageRegistry
from auralink.pipeline.stages.base import Stage


def _noop_stage(name: str) -> Stage:
    return Stage(name=name, run=lambda ctx: None)


def test_register_and_get_stages():
    reg = StageRegistry()
    stages = [_noop_stage("a"), _noop_stage("b")]
    reg.register_movement("overhead_squat", stages)
    assert reg.has_movement("overhead_squat")
    assert [s.name for s in reg.get_stages("overhead_squat")] == ["a", "b"]


def test_register_is_idempotent_last_wins():
    reg = StageRegistry()
    reg.register_movement("overhead_squat", [_noop_stage("a")])
    reg.register_movement("overhead_squat", [_noop_stage("b")])
    assert [s.name for s in reg.get_stages("overhead_squat")] == ["b"]


def test_get_stages_unknown_movement_raises():
    reg = StageRegistry()
    with pytest.raises(PipelineError):
        reg.get_stages("unknown_movement")


def test_get_stages_returns_a_copy():
    reg = StageRegistry()
    reg.register_movement("overhead_squat", [_noop_stage("a")])
    got = reg.get_stages("overhead_squat")
    got.append(_noop_stage("tampered"))
    assert len(reg.get_stages("overhead_squat")) == 1
```

- [ ] **Step 2: Run and verify failure**

`cd software/server && uv run pytest tests/unit/pipeline/test_registry.py -v`
Expected: module not found.

- [ ] **Step 3: Implement `pipeline/registry.py`**

```python
from auralink.pipeline.errors import PipelineError
from auralink.pipeline.stages.base import Stage


class StageRegistry:
    def __init__(self) -> None:
        self._by_movement: dict[str, list[Stage]] = {}

    def register_movement(self, movement_type: str, stages: list[Stage]) -> None:
        self._by_movement[movement_type] = list(stages)

    def get_stages(self, movement_type: str) -> list[Stage]:
        if movement_type not in self._by_movement:
            raise PipelineError(f"no stages registered for movement '{movement_type}'")
        return list(self._by_movement[movement_type])

    def has_movement(self, movement_type: str) -> bool:
        return movement_type in self._by_movement
```

- [ ] **Step 4: Run tests**

`cd software/server && uv run pytest tests/unit/pipeline/test_registry.py -v`
Expected: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/registry.py \
        software/server/tests/unit/pipeline/test_registry.py
git commit -m "feat(pipeline): add StageRegistry with register_movement extension API"
```

#### Cycle 10b: Orchestrator rewrite

- [ ] **Step 1: Write the failing test**

`software/server/tests/unit/pipeline/test_orchestrator.py`:
```python
import pytest

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.artifacts import PipelineArtifacts
from auralink.pipeline.errors import PipelineError, QualityGateError, StageError
from auralink.pipeline.orchestrator import DEFAULT_REGISTRY, run_pipeline
from auralink.pipeline.registry import StageRegistry
from auralink.pipeline.stages.base import Stage


def _lm(vis: float = 1.0, pres: float = 1.0) -> Landmark:
    return Landmark(x=0.5, y=0.5, z=0.0, visibility=vis, presence=pres)


def _good_session(frame_count: int = 60) -> Session:
    frames = [Frame(timestamp_ms=i * 33, landmarks=[_lm() for _ in range(33)]) for i in range(frame_count)]
    return Session(
        metadata=SessionMetadata(
            movement="overhead_squat", device="t", model="t", frame_rate=30.0
        ),
        frames=frames,
    )


def test_default_registry_has_overhead_squat_and_single_leg_squat():
    assert DEFAULT_REGISTRY.has_movement("overhead_squat")
    assert DEFAULT_REGISTRY.has_movement("single_leg_squat")


def test_run_pipeline_produces_pipeline_artifacts_for_good_session():
    artifacts = run_pipeline(_good_session())
    assert isinstance(artifacts, PipelineArtifacts)
    assert artifacts.quality_report.passed is True
    assert artifacts.angle_series is not None
    assert artifacts.normalized_angle_series is not None
    assert artifacts.rep_boundaries is not None
    assert artifacts.per_rep_metrics is not None
    assert artifacts.within_movement_trend is not None


def test_run_pipeline_raises_quality_gate_error_on_bad_session():
    bad = Session(
        metadata=SessionMetadata(
            movement="overhead_squat", device="t", model="t", frame_rate=10.0
        ),
        frames=_good_session(30).frames,
    )
    with pytest.raises(QualityGateError) as exc:
        run_pipeline(bad)
    assert any(issue.code == "low_frame_rate" for issue in exc.value.report.issues)


def test_run_pipeline_wraps_unexpected_stage_failure_as_stage_error():
    reg = StageRegistry()
    def _boom(_ctx):
        raise RuntimeError("boom")
    reg.register_movement("overhead_squat", [Stage(name="quality_gate", run=lambda c: _pass()), Stage(name="angle_series", run=_boom)])
    with pytest.raises(StageError) as exc:
        run_pipeline(_good_session(), registry=reg)
    assert exc.value.stage_name == "angle_series"


def _pass():
    from auralink.pipeline.artifacts import SessionQualityReport
    return SessionQualityReport(passed=True, issues=[], metrics={})


def test_run_pipeline_unknown_movement_raises_pipeline_error():
    reg = StageRegistry()
    with pytest.raises(PipelineError):
        run_pipeline(_good_session(), registry=reg)
```

- [ ] **Step 2: Run and verify failure**

`cd software/server && uv run pytest tests/unit/pipeline/test_orchestrator.py -v`
Expected: multiple failures — `DEFAULT_REGISTRY` not defined, `run_pipeline` still returns a dict from the stub.

- [ ] **Step 3: Rewrite `pipeline/orchestrator.py`**

```python
from auralink.api.schemas import Session
from auralink.pipeline.artifacts import PipelineArtifacts
from auralink.pipeline.errors import PipelineError, QualityGateError, StageError
from auralink.pipeline.registry import StageRegistry
from auralink.pipeline.stages.angle_series import run_angle_series
from auralink.pipeline.stages.base import Stage, StageContext
from auralink.pipeline.stages.normalize import run_normalize
from auralink.pipeline.stages.per_rep_metrics import run_per_rep_metrics
from auralink.pipeline.stages.quality_gate import run_quality_gate
from auralink.pipeline.stages.rep_segment import run_rep_segment
from auralink.pipeline.stages.within_movement_trend import run_within_movement_trend

_STAGE_NAME_QUALITY_GATE = "quality_gate"


def _default_stage_list() -> list[Stage]:
    return [
        Stage(name=_STAGE_NAME_QUALITY_GATE, run=run_quality_gate),
        Stage(name="angle_series", run=run_angle_series),
        Stage(name="normalize", run=run_normalize),
        Stage(name="rep_segment", run=run_rep_segment),
        Stage(name="per_rep_metrics", run=run_per_rep_metrics),
        Stage(name="within_movement_trend", run=run_within_movement_trend),
    ]


def _build_default_registry() -> StageRegistry:
    registry = StageRegistry()
    registry.register_movement("overhead_squat", _default_stage_list())
    registry.register_movement("single_leg_squat", _default_stage_list())
    return registry


DEFAULT_REGISTRY = _build_default_registry()


def run_pipeline(
    session: Session,
    registry: StageRegistry | None = None,
) -> PipelineArtifacts:
    reg = registry if registry is not None else DEFAULT_REGISTRY
    stages = reg.get_stages(session.metadata.movement)

    ctx = StageContext(session=session)
    for stage in stages:
        try:
            result = stage.run(ctx)
        except PipelineError:
            raise
        except Exception as exc:
            raise StageError(stage_name=stage.name, detail=str(exc)) from exc

        ctx.artifacts[stage.name] = result

        if stage.name == _STAGE_NAME_QUALITY_GATE and not result.passed:
            raise QualityGateError(report=result)

    return _assemble_artifacts(ctx)


def _assemble_artifacts(ctx: StageContext) -> PipelineArtifacts:
    return PipelineArtifacts(
        quality_report=ctx.artifacts[_STAGE_NAME_QUALITY_GATE],
        angle_series=ctx.artifacts.get("angle_series"),
        normalized_angle_series=ctx.artifacts.get("normalize"),
        rep_boundaries=ctx.artifacts.get("rep_segment"),
        per_rep_metrics=ctx.artifacts.get("per_rep_metrics"),
        within_movement_trend=ctx.artifacts.get("within_movement_trend"),
    )
```

- [ ] **Step 4: Run orchestrator + full pipeline suite**

`cd software/server && uv run pytest tests/unit/pipeline -v`
Expected: orchestrator tests pass and all previous tests still pass.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/orchestrator.py \
        software/server/tests/unit/pipeline/test_orchestrator.py
git commit -m "feat(pipeline): real orchestrator with default registry and stage dispatch"
```

---

### Task 11: Persist artifacts + wire `POST /sessions` (with `?sync=true` no-op)

**Files:**
- Modify: `software/server/src/auralink/pipeline/storage.py`
- Create: `software/server/tests/unit/test_storage_artifacts.py`
- Modify: `software/server/src/auralink/api/routes/sessions.py`
- Create: `software/server/tests/integration/test_session_pipeline.py`

#### Cycle 11a: Storage adds `save_artifacts` / `load_artifacts`

- [ ] **Step 1: Write the failing test**

`software/server/tests/unit/test_storage_artifacts.py`:
```python
import pytest

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.artifacts import PipelineArtifacts, QualityIssue, SessionQualityReport
from auralink.pipeline.storage import SessionStorage


def _session() -> Session:
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)
    frame = Frame(timestamp_ms=0, landmarks=[lm for _ in range(33)])
    return Session(
        metadata=SessionMetadata(
            movement="overhead_squat", device="t", model="t", frame_rate=30.0
        ),
        frames=[frame],
    )


def _artifacts() -> PipelineArtifacts:
    return PipelineArtifacts(
        quality_report=SessionQualityReport(
            passed=True,
            issues=[QualityIssue(code="ok", detail="all checks passed")],
            metrics={"frame_rate": 30.0},
        ),
    )


def test_save_and_load_artifacts_round_trip(tmp_path):
    storage = SessionStorage(base_dir=tmp_path)
    session_id = storage.save(_session())
    storage.save_artifacts(session_id, _artifacts())
    loaded = storage.load_artifacts(session_id)
    assert loaded.quality_report.passed is True
    assert loaded.quality_report.issues[0].code == "ok"


def test_load_artifacts_missing_raises_file_not_found(tmp_path):
    storage = SessionStorage(base_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        storage.load_artifacts("nonexistent-id")
```

- [ ] **Step 2: Run and verify failure**

`cd software/server && uv run pytest tests/unit/test_storage_artifacts.py -v`
Expected: `AttributeError: 'SessionStorage' object has no attribute 'save_artifacts'`.

- [ ] **Step 3: Extend `pipeline/storage.py`**

Add at the end of the `SessionStorage` class:
```python
    def save_artifacts(self, session_id: str, artifacts: "PipelineArtifacts") -> None:
        path = self._artifacts_path_for(session_id)
        path.write_text(artifacts.model_dump_json(indent=2))

    def load_artifacts(self, session_id: str) -> "PipelineArtifacts":
        from auralink.pipeline.artifacts import PipelineArtifacts
        path = self._artifacts_path_for(session_id)
        if not path.exists():
            raise FileNotFoundError(f"artifacts for session {session_id} not found at {path}")
        return PipelineArtifacts.model_validate_json(path.read_text())

    def _artifacts_path_for(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.artifacts.json"
```

And add the type-only import at the top of the module:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from auralink.pipeline.artifacts import PipelineArtifacts
```

- [ ] **Step 4: Run tests**

`cd software/server && uv run pytest tests/unit/test_storage_artifacts.py -v`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/storage.py \
        software/server/tests/unit/test_storage_artifacts.py
git commit -m "feat(storage): save_artifacts/load_artifacts alongside session json"
```

#### Cycle 11b: POST /sessions runs pipeline and accepts `?sync=true`

- [ ] **Step 1: Write the failing test**

`software/server/tests/integration/test_session_pipeline.py`:
```python
from fastapi.testclient import TestClient

from auralink.api.main import create_app

from tests.fixtures.synthetic_overhead_squat import build_overhead_squat_payload


def test_post_sessions_runs_pipeline_and_persists_artifacts(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    payload = build_overhead_squat_payload(rep_count=2, frames_per_rep=30)
    response = client.post("/sessions?sync=true", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert "session_id" in body

    session_id = body["session_id"]
    artifacts_path = tmp_path / "sessions" / f"{session_id}.artifacts.json"
    assert artifacts_path.exists(), "pipeline artifacts should be persisted after POST"


def test_sync_flag_is_accepted_as_noop(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    payload = build_overhead_squat_payload()
    r1 = client.post("/sessions?sync=true", json=payload)
    r2 = client.post("/sessions", json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 201
```

This test depends on the fixture helper from Task 14. **Build the fixture helper in Task 14 first**, or temporarily inline a minimal payload — the cleanest ordering is: implement Task 14 Step 1 (fixture helper) BEFORE this task. To avoid a forward dependency, Task 14 is reshuffled so the fixture helper lands before Task 11 in the execution order. The executor should process tasks in the order: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, **14a (fixture helper only)**, 11, 12, 13, **14b (e2e integration test)**, 15.

**Note to the executor:** when picking up Task 11 Step 1, first confirm that Task 14a has shipped `tests/fixtures/synthetic_overhead_squat.py`. If not, pause Task 11 and run Task 14a first.

- [ ] **Step 2: Run and verify failure**

`cd software/server && uv run pytest tests/integration/test_session_pipeline.py -v`
Expected: test fails because `POST /sessions` still uses the scaffold handler that does not run the pipeline.

- [ ] **Step 3: Modify `api/routes/sessions.py` to run the pipeline**

Replace the `create_session` handler with:
```python
from fastapi import APIRouter, Depends, HTTPException, Query, status

from auralink.api.schemas import Session, SessionCreateResponse
from auralink.config import Settings, get_settings
from auralink.pipeline.orchestrator import run_pipeline
from auralink.pipeline.storage import SessionStorage

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_storage(settings: Settings = Depends(get_settings)) -> SessionStorage:
    return SessionStorage(base_dir=settings.sessions_dir)


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session: Session,
    sync: bool = Query(default=True),
    storage: SessionStorage = Depends(_get_storage),
) -> SessionCreateResponse:
    session_id = storage.save(session)
    # sync is a recognized no-op flag in Plan 1; Plan 5 will flip the default
    # to async and honor sync=true for synchronous execution.
    _ = sync
    artifacts = run_pipeline(session)
    storage.save_artifacts(session_id, artifacts)
    return SessionCreateResponse(
        session_id=session_id,
        frames_received=len(session.frames),
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

- [ ] **Step 4: Run integration test**

`cd software/server && uv run pytest tests/integration/test_session_pipeline.py -v`
Expected: `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/api/routes/sessions.py \
        software/server/tests/integration/test_session_pipeline.py
git commit -m "feat(api): POST /sessions runs pipeline and persists artifacts; ?sync=true accepted"
```

---

### Task 12: `GET /sessions/{id}/report` endpoint

**Files:**
- Create: `software/server/src/auralink/api/routes/reports.py`
- Modify: `software/server/src/auralink/api/main.py`
- Create: `software/server/tests/integration/test_report_endpoint.py`

- [ ] **Step 1: Write the failing test**

`software/server/tests/integration/test_report_endpoint.py`:
```python
from fastapi.testclient import TestClient

from auralink.api.main import create_app

from tests.fixtures.synthetic_overhead_squat import build_overhead_squat_payload


def test_get_report_returns_artifacts_after_post(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    post = client.post("/sessions?sync=true", json=build_overhead_squat_payload())
    session_id = post.json()["session_id"]

    response = client.get(f"/sessions/{session_id}/report")
    assert response.status_code == 200
    body = response.json()
    assert body["quality_report"]["passed"] is True
    assert body["angle_series"] is not None
    assert body["within_movement_trend"] is not None


def test_get_report_404_when_session_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    response = client.get("/sessions/does-not-exist/report")
    assert response.status_code == 404
```

- [ ] **Step 2: Run and verify failure**

Expected: 404 on the first test because the route is not registered.

- [ ] **Step 3: Create `api/routes/reports.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status

from auralink.config import Settings, get_settings
from auralink.pipeline.artifacts import PipelineArtifacts
from auralink.pipeline.storage import SessionStorage

router = APIRouter(prefix="/sessions", tags=["reports"])


def _get_storage(settings: Settings = Depends(get_settings)) -> SessionStorage:
    return SessionStorage(base_dir=settings.sessions_dir)


@router.get("/{session_id}/report", response_model=PipelineArtifacts)
def get_report(
    session_id: str,
    storage: SessionStorage = Depends(_get_storage),
) -> PipelineArtifacts:
    try:
        return storage.load_artifacts(session_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no report for session {session_id}",
        ) from exc
```

- [ ] **Step 4: Register the router in `api/main.py`**

```python
from fastapi import FastAPI

from auralink.api.routes import health, reports, sessions
from auralink.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health.router)
    app.include_router(sessions.router)
    app.include_router(reports.router)
    return app


app = create_app()
```

- [ ] **Step 5: Run the report endpoint tests**

`cd software/server && uv run pytest tests/integration/test_report_endpoint.py -v`
Expected: `2 passed`.

- [ ] **Step 6: Commit**

```bash
git add software/server/src/auralink/api/routes/reports.py \
        software/server/src/auralink/api/main.py \
        software/server/tests/integration/test_report_endpoint.py
git commit -m "feat(api): GET /sessions/{id}/report returns PipelineArtifacts bundle"
```

---

### Task 13: FastAPI exception handlers

Map `PipelineError` hierarchy to HTTP responses.

**Files:**
- Create: `software/server/src/auralink/api/errors.py`
- Modify: `software/server/src/auralink/api/main.py`
- Create: `software/server/tests/integration/test_error_handling.py`

- [ ] **Step 1: Write the failing test**

`software/server/tests/integration/test_error_handling.py`:
```python
import copy

from fastapi.testclient import TestClient

from auralink.api.main import create_app

from tests.fixtures.synthetic_overhead_squat import build_overhead_squat_payload


def test_quality_gate_rejection_returns_422(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())
    payload = copy.deepcopy(build_overhead_squat_payload())
    payload["metadata"]["frame_rate"] = 10.0  # below MIN_FRAME_RATE = 20

    response = client.post("/sessions?sync=true", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "quality_gate_rejected"
    assert any(issue["code"] == "low_frame_rate" for issue in body["issues"])
```

- [ ] **Step 2: Run and verify failure**

Expected: current behavior raises an unhandled `QualityGateError` → 500 response instead of 422 with structured body.

- [ ] **Step 3: Create `api/errors.py`**

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from auralink.pipeline.errors import PipelineError, QualityGateError, StageError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(QualityGateError)
    async def _quality_gate(request: Request, exc: QualityGateError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "quality_gate_rejected",
                "issues": [issue.model_dump() for issue in exc.report.issues],
                "metrics": exc.report.metrics,
            },
        )

    @app.exception_handler(StageError)
    async def _stage_error(request: Request, exc: StageError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": "stage_failed",
                "stage": exc.stage_name,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(PipelineError)
    async def _pipeline_error(request: Request, exc: PipelineError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": "pipeline_failed", "detail": str(exc)},
        )
```

- [ ] **Step 4: Wire handlers into `api/main.py`**

```python
from fastapi import FastAPI

from auralink.api.errors import register_exception_handlers
from auralink.api.routes import health, reports, sessions
from auralink.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(sessions.router)
    app.include_router(reports.router)
    return app


app = create_app()
```

- [ ] **Step 5: Run the failure test**

`cd software/server && uv run pytest tests/integration/test_error_handling.py -v`
Expected: `1 passed`.

- [ ] **Step 6: Commit**

```bash
git add software/server/src/auralink/api/errors.py \
        software/server/src/auralink/api/main.py \
        software/server/tests/integration/test_error_handling.py
git commit -m "feat(api): exception handlers map PipelineError hierarchy to HTTP responses"
```

---

### Task 14: Synthetic overhead-squat fixture helper + end-to-end integration test

The executor processes this task in **two phases**. Phase 14a ships the fixture helper (no tests of its own — validated by downstream integration tests). Phase 14b lands the end-to-end integration test that stitches everything together.

#### Phase 14a: Fixture helper

Runs **before Task 11** per the ordering note. At this point Tasks 1–10 are green.

**Files:**
- Create: `software/server/tests/fixtures/__init__.py` (if missing)
- Create: `software/server/tests/fixtures/synthetic_overhead_squat.py`

- [ ] **Step 1: Create `tests/fixtures/__init__.py`**

Empty file.

- [ ] **Step 2: Implement the fixture helper**

`software/server/tests/fixtures/synthetic_overhead_squat.py`:
```python
"""Single-purpose synthetic fixture for overhead_squat integration tests.

Plan 4 will absorb this into the shared `tests/fixtures/synthetic/generator.py`.
Until then, callers in Plan 1's integration tests use build_overhead_squat_payload().
"""

import math


def _landmark(x: float, y: float) -> dict:
    return {"x": x, "y": y, "z": 0.0, "visibility": 1.0, "presence": 1.0}


def _frame_for_knee_angle(
    timestamp_ms: int,
    knee_flexion_deg: float,
    knee_valgus_deg: float = 0.0,
    trunk_lean_deg: float = 4.0,
) -> dict:
    """Stylized pose: hip at (0.5, 0.5), knee and ankle positioned so
    knee_flexion_angle() returns the requested value, with a small constant
    knee valgus and a small constant trunk lean.
    """
    hip = (0.5, 0.5)
    knee = (0.5, 0.7)
    r = 0.2
    angle_from_down_rad = math.radians(180.0 - knee_flexion_deg)
    # Apply valgus as a small horizontal offset on the ankle position.
    valgus_offset = math.radians(knee_valgus_deg) * 0.1
    ankle_x = knee[0] + r * math.sin(angle_from_down_rad) + valgus_offset
    ankle_y = knee[1] + r * math.cos(angle_from_down_rad)

    trunk_rad = math.radians(trunk_lean_deg)
    shoulder_x = hip[0] + 0.2 * math.sin(trunk_rad)
    shoulder_y = hip[1] - 0.2 * math.cos(trunk_rad)

    landmarks: list[dict] = [_landmark(0.0, 0.0) for _ in range(33)]
    landmarks[11] = _landmark(shoulder_x - 0.05, shoulder_y)  # LEFT_SHOULDER
    landmarks[12] = _landmark(shoulder_x + 0.05, shoulder_y)  # RIGHT_SHOULDER
    landmarks[23] = _landmark(hip[0] - 0.05, hip[1])          # LEFT_HIP
    landmarks[24] = _landmark(hip[0] + 0.05, hip[1])          # RIGHT_HIP
    landmarks[25] = _landmark(knee[0] - 0.05, knee[1])        # LEFT_KNEE
    landmarks[26] = _landmark(knee[0] + 0.05, knee[1])        # RIGHT_KNEE
    landmarks[27] = _landmark(ankle_x - 0.05, ankle_y)        # LEFT_ANKLE
    landmarks[28] = _landmark(ankle_x + 0.05, ankle_y)        # RIGHT_ANKLE

    for i in range(33):
        if landmarks[i]["x"] == 0.0 and landmarks[i]["y"] == 0.0:
            landmarks[i] = _landmark(0.5, 0.5)

    return {"timestamp_ms": timestamp_ms, "landmarks": landmarks}


def build_overhead_squat_payload(
    rep_count: int = 2,
    frames_per_rep: int = 30,
    frame_rate: float = 30.0,
    knee_valgus_deg: float = 2.0,
    trunk_lean_deg: float = 4.0,
) -> dict:
    """Build a POST /sessions payload representing `rep_count` overhead squats."""
    frames: list[dict] = []
    frame_interval_ms = int(round(1000.0 / frame_rate))
    for rep in range(rep_count):
        for i in range(frames_per_rep):
            theta = (i / frames_per_rep) * 2.0 * math.pi
            knee_flex = 135.0 + 45.0 * math.cos(theta)  # 90..180..90
            frames.append(
                _frame_for_knee_angle(
                    timestamp_ms=(rep * frames_per_rep + i) * frame_interval_ms,
                    knee_flexion_deg=knee_flex,
                    knee_valgus_deg=knee_valgus_deg,
                    trunk_lean_deg=trunk_lean_deg,
                )
            )
    return {
        "metadata": {
            "movement": "overhead_squat",
            "device": "synthetic",
            "model": "synthetic_v1",
            "frame_rate": frame_rate,
        },
        "frames": frames,
    }
```

- [ ] **Step 3: Commit**

```bash
git add software/server/tests/fixtures/__init__.py \
        software/server/tests/fixtures/synthetic_overhead_squat.py
git commit -m "test(fixtures): synthetic overhead_squat fixture helper (Plan 4 will absorb)"
```

#### Phase 14b: End-to-end integration test

Runs **after** Tasks 11–13 are green.

**Files:**
- Create: `software/server/tests/integration/test_e2e_overhead_squat.py`

- [ ] **Step 1: Write the end-to-end test**

`software/server/tests/integration/test_e2e_overhead_squat.py`:
```python
from fastapi.testclient import TestClient

from auralink.api.main import create_app

from tests.fixtures.synthetic_overhead_squat import build_overhead_squat_payload


def test_overhead_squat_round_trip_produces_populated_report(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    client = TestClient(create_app())

    payload = build_overhead_squat_payload(rep_count=3, frames_per_rep=30)
    post = client.post("/sessions?sync=true", json=payload)
    assert post.status_code == 201
    session_id = post.json()["session_id"]

    report = client.get(f"/sessions/{session_id}/report")
    assert report.status_code == 200
    body = report.json()

    assert body["quality_report"]["passed"] is True
    assert body["angle_series"]["angles"]["left_knee_flexion"]
    assert body["normalized_angle_series"]["scale_factor"] > 0
    assert len(body["rep_boundaries"]["by_angle"]["left_knee_flexion"]) == 3
    assert len(body["per_rep_metrics"]["reps"]) == 3
    assert "fatigue_detected" in body["within_movement_trend"]
```

- [ ] **Step 2: Run test**

`cd software/server && uv run pytest tests/integration/test_e2e_overhead_squat.py -v`
Expected: `1 passed`.

If the synthetic fixture does not produce exactly 3 reps, tune `frames_per_rep` or the starting phase in `build_overhead_squat_payload` until the assertion passes; do not weaken the assertion.

- [ ] **Step 3: Commit**

```bash
git add software/server/tests/integration/test_e2e_overhead_squat.py
git commit -m "test(pipeline): end-to-end overhead_squat round-trip integration test"
```

---

### Task 15: Final validation

- [ ] **Step 1: Full test suite**

`cd software/server && uv run pytest -v`
Expected: all tests passing — the 31 scaffold tests plus all new tests added by this plan.

- [ ] **Step 2: Lint**

```bash
cd software/server
uv run ruff check .
uv run black --check .
```
Expected: clean. Fix any lint issues found; recommit as `chore: ruff/black cleanup`.

- [ ] **Step 3: Dev-server smoke test**

```bash
cd software/server
./scripts/dev.sh &
DEV_PID=$!
sleep 2
curl -sf localhost:8000/health
curl -sf -X POST localhost:8000/sessions\?sync=true \
    -H "Content-Type: application/json" \
    -d "$(python -c 'import json; from tests.fixtures.synthetic_overhead_squat import build_overhead_squat_payload; print(json.dumps(build_overhead_squat_payload()))')"
kill $DEV_PID
```
Expected: both curl calls return 2xx. The POST returns a `session_id`; a follow-up `GET /sessions/<id>/report` returns populated artifacts. Kill the dev server afterwards.

- [ ] **Step 4: Final validation commit**

```bash
git add -A
git diff --cached --quiet || git commit -m "chore: plan 1 final validation (full suite green, dev smoke ok)"
```
(Only commits if there is something to commit — lint fixes or test additions.)

---

## Exit Criteria

- All previous scaffold tests still pass (31 baseline).
- ~35–45 new tests across unit (`tests/unit/pipeline/`, `tests/unit/pose/test_trunk_lean_angle.py`) and integration (`tests/integration/test_session_pipeline.py`, `test_report_endpoint.py`, `test_error_handling.py`, `test_e2e_overhead_squat.py`).
- End-to-end integration test: a synthetic overhead_squat fixture POSTs successfully, the pipeline runs through all six stages, and `GET /sessions/{id}/report` returns a `PipelineArtifacts` bundle with populated quality report, angle series, normalized angle series, rep boundaries, per-rep metrics, and within-movement trend.
- `pipeline.orchestrator.run_pipeline()` is no longer a stub — it composes stages via the registry and returns `PipelineArtifacts`.
- `DEFAULT_REGISTRY` is importable and has `overhead_squat` + `single_leg_squat` registered; Plan 4 can add more movements via `register_movement()`.
- A fixture with `frame_rate=10.0` is rejected as HTTP 422 with a `quality_gate_rejected` error body containing the `low_frame_rate` issue.
- `POST /sessions` accepts `?sync=true` as a recognized no-op query parameter; omitting it behaves identically in this plan.
- `save_artifacts` / `load_artifacts` added to `SessionStorage`, persisting `<session_id>.artifacts.json` alongside the raw session JSON.
- Ruff + black clean. Dev server smoke test passes.

## Deferred to L3 (refined during execution)

- Exact pydantic field names on each artifact may shift during implementation as stages compose; keep the table in this plan in sync.
- Fatigue thresholds (`FATIGUE_ROM_SLOPE_THRESHOLD`, etc.) are first-pass values — Plan 2 may tune them against its threshold config.
- Visibility / frame-rate defaults in the quality gate are first-pass; tune when real Flutter golden captures arrive (flag as a Plan 1 follow-up if needed).
- The synthetic fixture helper's knee-valgus encoding is approximate — Plan 4's generator will supersede it with a properly parameterized compensation injection model.

## Execution notes

- Execute with `parallel-plan-executor` in sequential-in-main-tree mode. Do NOT use worktrees or parallel subagent dispatch — this repo's memory (`feedback_no_subagent_worktrees.md`) prohibits it.
- Each TDD cycle yields one commit. Tasks 4, 5, 10, 11, and 14 contain multiple cycles and therefore multiple commits inside a single task.
- Task ordering for execution: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, **14a (fixture helper)**, 11, 12, 13, **14b (e2e test)**, 15.
- The `?sync=true` flag is a no-op in this plan; Plan 5 flips the default and reuses the same flag for tests.
- The `StageRegistry` must remain import-safe from Plan 4: its `register_movement(movement_type, stages)` signature is the public contract.
