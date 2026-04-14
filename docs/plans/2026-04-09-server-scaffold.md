# BioLiminal Server Scaffold — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the Python server project for BioLiminal's ML pipeline — ingest pose keypoint sessions from the Flutter app, compute joint angles, segment reps, and prepare the scaffolding hooks for MotionBERT, HSMR, DTW, and chain reasoning to drop in later.

**Architecture:** FastAPI server with a stage-based pipeline. Every stage is a pure function over JSON session artifacts (keypoints → angles → reps → 3D lift → SKEL → chain reasoning → report). Stages are independently testable and composable. Model loading happens once at startup via a registry. No ML models are integrated in this scaffold — they land in follow-on plans. This scaffold ships a working session ingest → joint angles → rep segmentation → basic chain placeholder pipeline that can be validated end-to-end with Flutter golden-capture fixtures.

**Tech Stack:**
- Python 3.11+ (compat with MotionBERT and HSMR PyTorch versions later)
- FastAPI + uvicorn (web layer)
- pydantic v2 (schemas)
- NumPy (joint angle math)
- pytest (tests)
- ruff + black (lint + format)
- uv (package manager — fast, reproducible)

**Repository path:** `software/server/` inside the existing Capstone repo.

---

## File Structure

Files to create in this scaffold:

```
software/server/
├── pyproject.toml
├── README.md
├── .gitignore
├── .python-version                       # 3.11
├── src/
│   └── auralink/
│       ├── __init__.py
│       ├── config.py                     # env vars, paths
│       ├── api/
│       │   ├── __init__.py
│       │   ├── main.py                   # FastAPI app factory
│       │   ├── schemas.py                # pydantic session models
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── health.py
│       │       └── sessions.py
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── orchestrator.py           # stage orchestration (stub, dispatch table)
│       │   └── storage.py                # local disk session artifact storage
│       ├── pose/
│       │   ├── __init__.py
│       │   ├── keypoints.py              # BlazePose 33-landmark constants + helpers
│       │   └── joint_angles.py           # hip, knee, valgus, trunk angle math
│       ├── analysis/
│       │   ├── __init__.py
│       │   └── rep_segmentation.py       # detect rep boundaries from angle series
│       ├── reasoning/
│       │   ├── __init__.py
│       │   ├── chains.py                 # SBL/BFL/FFL chain definitions
│       │   └── thresholds.py             # default threshold table (placeholder values)
│       └── models/
│           ├── __init__.py
│           └── registry.py               # placeholder for model checkpoint management
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/
│   │   └── README.md                     # notes on fixture format, golden capture integration
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_config.py
│   │   ├── test_schemas.py
│   │   ├── test_storage.py
│   │   ├── test_keypoints.py
│   │   ├── test_joint_angles.py
│   │   └── test_rep_segmentation.py
│   └── integration/
│       ├── __init__.py
│       ├── test_health.py
│       └── test_sessions_endpoint.py
└── scripts/
    └── dev.sh                            # dev server startup convenience
```

Plus a new doc at `software/server/docs/blazepose_landmark_reference.md` — an internal server-side reference for the BlazePose 33-landmark ordering. The canonical Flutter ↔ server model interface contract (`docs/custom_model_contract.md`) is owned by the Flutter team and lives in the Flutter repo area.

---

### Task 1: Project initialization

**Files:**
- Create: `software/server/pyproject.toml`
- Create: `software/server/.gitignore`
- Create: `software/server/.python-version`
- Create: `software/server/README.md`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "auralink-server"
version = "0.1.0"
description = "BioLiminal movement screening server — ingests pose keypoints, runs analysis pipeline, returns reports"
requires-python = ">=3.11,<3.13"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",
    "numpy>=1.26.0",
    "python-multipart>=0.0.17",
]

[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "ruff>=0.7.0",
    "black>=24.10.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/auralink"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]

[tool.black]
line-length = 100
target-version = ["py311"]
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
env/
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.env
.env.local
data/
!data/.gitkeep
*.ckpt
*.pth
*.safetensors
```

- [ ] **Step 3: Create `.python-version`**

```
3.11
```

- [ ] **Step 4: Create `README.md`**

```markdown
# BioLiminal Server

Python server for BioLiminal's movement screening ML pipeline. Accepts pose keypoint sessions from the Flutter app, runs analysis, returns reports.

## Quick Start

```bash
cd software/server
uv sync
uv run uvicorn auralink.api.main:app --reload
```

Server runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

## Run Tests

```bash
uv run pytest
```

## Project Layout

See `docs/operations/comms/research-integration-report.md` section 6 for architectural context. Pipeline stages live under `src/auralink/` organized by domain (pose, analysis, reasoning, etc.).
```

- [ ] **Step 5: Commit**

```bash
git add software/server/pyproject.toml software/server/.gitignore software/server/.python-version software/server/README.md
git commit -m "chore: scaffold BioLiminal server project"
```

---

### Task 2: Config module

**Files:**
- Create: `software/server/src/auralink/__init__.py`
- Create: `software/server/src/auralink/config.py`
- Test: `software/server/tests/unit/test_config.py`

- [ ] **Step 1: Create package init files**

Create empty `software/server/src/auralink/__init__.py`.

- [ ] **Step 2: Write failing test for config loading**

Create `software/server/tests/__init__.py` and `software/server/tests/unit/__init__.py` as empty files.

Then create `software/server/tests/unit/test_config.py`:

```python
import os
from pathlib import Path

from auralink.config import Settings


def test_settings_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    settings = Settings()
    assert settings.data_dir == tmp_path
    assert settings.sessions_dir == tmp_path / "sessions"
    assert settings.app_name == "auralink-server"


def test_settings_ensure_dirs_creates_sessions_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    settings = Settings()
    assert not settings.sessions_dir.exists()
    settings.ensure_dirs()
    assert settings.sessions_dir.exists()
    assert settings.sessions_dir.is_dir()
```

- [ ] **Step 3: Run the test and confirm it fails**

```bash
cd software/server && uv run pytest tests/unit/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'auralink.config'`

- [ ] **Step 4: Create `config.py`**

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

    @computed_field
    @property
    def sessions_dir(self) -> Path:
        return self.data_dir / "sessions"

    def ensure_dirs(self) -> None:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 5: Run the test and confirm it passes**

```bash
cd software/server && uv run pytest tests/unit/test_config.py -v
```

Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add software/server/src/auralink/__init__.py software/server/src/auralink/config.py software/server/tests/__init__.py software/server/tests/unit/__init__.py software/server/tests/unit/test_config.py
git commit -m "feat: add settings module with data dir management"
```

---

### Task 3: Session pydantic schemas

**Files:**
- Create: `software/server/src/auralink/api/__init__.py`
- Create: `software/server/src/auralink/api/schemas.py`
- Test: `software/server/tests/unit/test_schemas.py`

- [ ] **Step 1: Write failing test**

Create `software/server/tests/unit/test_schemas.py`:

```python
import pytest
from pydantic import ValidationError

from auralink.api.schemas import Landmark, Frame, SessionMetadata, Session


def test_landmark_valid():
    lm = Landmark(x=0.5, y=0.5, z=0.0, visibility=0.95, presence=0.99)
    assert lm.x == 0.5
    assert lm.visibility == 0.95


def test_landmark_rejects_out_of_range_visibility():
    with pytest.raises(ValidationError):
        Landmark(x=0.5, y=0.5, z=0.0, visibility=1.5, presence=0.99)


def test_frame_requires_33_landmarks():
    landmarks = [
        Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0, presence=1.0)
        for _ in range(33)
    ]
    frame = Frame(timestamp_ms=0, landmarks=landmarks)
    assert len(frame.landmarks) == 33


def test_frame_rejects_wrong_landmark_count():
    landmarks = [
        Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0, presence=1.0)
        for _ in range(10)
    ]
    with pytest.raises(ValidationError):
        Frame(timestamp_ms=0, landmarks=landmarks)


def test_session_metadata():
    meta = SessionMetadata(
        movement="overhead_squat",
        device="Pixel 8",
        model="mlkit_pose_detection",
        frame_rate=30.0,
    )
    assert meta.movement == "overhead_squat"


def test_session_round_trip():
    landmarks = [
        Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0, presence=1.0)
        for _ in range(33)
    ]
    session = Session(
        metadata=SessionMetadata(
            movement="overhead_squat",
            device="Pixel 8",
            model="mlkit_pose_detection",
            frame_rate=30.0,
        ),
        frames=[Frame(timestamp_ms=0, landmarks=landmarks)],
    )
    dumped = session.model_dump_json()
    loaded = Session.model_validate_json(dumped)
    assert loaded.metadata.movement == "overhead_squat"
    assert len(loaded.frames) == 1
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd software/server && uv run pytest tests/unit/test_schemas.py -v
```

Expected: `ModuleNotFoundError: No module named 'auralink.api'`

- [ ] **Step 3: Create `api/__init__.py` and `api/schemas.py`**

Create empty `software/server/src/auralink/api/__init__.py`.

Create `software/server/src/auralink/api/schemas.py`:

```python
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Landmark(BaseModel):
    """Single BlazePose landmark.

    Coordinates in normalized [0, 1] space (x, y) or input-relative (z).
    Visibility and presence are sigmoid'd values in [0, 1].
    """

    x: float
    y: float
    z: float
    visibility: float = Field(ge=0.0, le=1.0)
    presence: float = Field(ge=0.0, le=1.0)


class Frame(BaseModel):
    """A single captured frame with 33 BlazePose landmarks in canonical order."""

    timestamp_ms: int = Field(ge=0)
    landmarks: list[Landmark]

    @field_validator("landmarks")
    @classmethod
    def require_33_landmarks(cls, v: list[Landmark]) -> list[Landmark]:
        if len(v) != 33:
            raise ValueError(f"expected 33 BlazePose landmarks, got {len(v)}")
        return v


MovementType = Literal[
    "overhead_squat",
    "single_leg_squat",
    "push_up",
    "rollup",
]


class SessionMetadata(BaseModel):
    movement: MovementType
    device: str
    model: str  # e.g. "mlkit_pose_detection", "mediapipe_blazepose_full"
    frame_rate: float = Field(gt=0)
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Session(BaseModel):
    metadata: SessionMetadata
    frames: list[Frame]


class SessionCreateResponse(BaseModel):
    session_id: str
    frames_received: int
```

- [ ] **Step 4: Run the test and confirm it passes**

```bash
cd software/server && uv run pytest tests/unit/test_schemas.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/api/__init__.py software/server/src/auralink/api/schemas.py software/server/tests/unit/test_schemas.py
git commit -m "feat: add session pydantic schemas with landmark validation"
```

---

### Task 4: Storage abstraction

**Files:**
- Create: `software/server/src/auralink/pipeline/__init__.py`
- Create: `software/server/src/auralink/pipeline/storage.py`
- Test: `software/server/tests/unit/test_storage.py`

- [ ] **Step 1: Write failing test**

Create `software/server/tests/unit/test_storage.py`:

```python
import pytest

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata
from auralink.pipeline.storage import SessionStorage


@pytest.fixture
def sample_session() -> Session:
    landmarks = [
        Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0, presence=1.0)
        for _ in range(33)
    ]
    return Session(
        metadata=SessionMetadata(
            movement="overhead_squat",
            device="Pixel 8",
            model="mlkit_pose_detection",
            frame_rate=30.0,
        ),
        frames=[Frame(timestamp_ms=i * 33, landmarks=landmarks) for i in range(5)],
    )


def test_save_and_load_session(tmp_path, sample_session):
    storage = SessionStorage(base_dir=tmp_path)
    session_id = storage.save(sample_session)
    assert session_id
    loaded = storage.load(session_id)
    assert loaded.metadata.movement == "overhead_squat"
    assert len(loaded.frames) == 5


def test_load_missing_session_raises(tmp_path):
    storage = SessionStorage(base_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        storage.load("nonexistent-id")


def test_save_creates_unique_ids(tmp_path, sample_session):
    storage = SessionStorage(base_dir=tmp_path)
    id1 = storage.save(sample_session)
    id2 = storage.save(sample_session)
    assert id1 != id2
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd software/server && uv run pytest tests/unit/test_storage.py -v
```

Expected: `ModuleNotFoundError: No module named 'auralink.pipeline'`

- [ ] **Step 3: Create storage module**

Create empty `software/server/src/auralink/pipeline/__init__.py`.

Create `software/server/src/auralink/pipeline/storage.py`:

```python
import uuid
from pathlib import Path

from auralink.api.schemas import Session


class SessionStorage:
    """Local filesystem storage for session artifacts.

    Stores each session as a single JSON file keyed by generated UUID.
    Later replaceable with object storage without changing callers.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session: Session) -> str:
        session_id = str(uuid.uuid4())
        path = self._path_for(session_id)
        path.write_text(session.model_dump_json(indent=2))
        return session_id

    def load(self, session_id: str) -> Session:
        path = self._path_for(session_id)
        if not path.exists():
            raise FileNotFoundError(f"session {session_id} not found at {path}")
        return Session.model_validate_json(path.read_text())

    def _path_for(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"
```

- [ ] **Step 4: Run the test and confirm it passes**

```bash
cd software/server && uv run pytest tests/unit/test_storage.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/__init__.py software/server/src/auralink/pipeline/storage.py software/server/tests/unit/test_storage.py
git commit -m "feat: add session storage abstraction over local filesystem"
```

---

### Task 5: BlazePose keypoint constants

**Files:**
- Create: `software/server/src/auralink/pose/__init__.py`
- Create: `software/server/src/auralink/pose/keypoints.py`
- Test: `software/server/tests/unit/test_keypoints.py`

- [ ] **Step 1: Write failing test**

Create `software/server/tests/unit/test_keypoints.py`:

```python
from auralink.pose.keypoints import (
    BLAZEPOSE_LANDMARK_COUNT,
    LandmarkIndex,
    landmark_index,
)


def test_landmark_count():
    assert BLAZEPOSE_LANDMARK_COUNT == 33


def test_known_indices():
    assert LandmarkIndex.NOSE == 0
    assert LandmarkIndex.LEFT_HIP == 23
    assert LandmarkIndex.RIGHT_HIP == 24
    assert LandmarkIndex.LEFT_KNEE == 25
    assert LandmarkIndex.RIGHT_KNEE == 26
    assert LandmarkIndex.LEFT_ANKLE == 27
    assert LandmarkIndex.RIGHT_ANKLE == 28


def test_landmark_index_lookup_by_name():
    assert landmark_index("left_hip") == 23
    assert landmark_index("right_knee") == 26
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd software/server && uv run pytest tests/unit/test_keypoints.py -v
```

Expected: `ModuleNotFoundError: No module named 'auralink.pose'`

- [ ] **Step 3: Create keypoints module**

Create empty `software/server/src/auralink/pose/__init__.py`.

Create `software/server/src/auralink/pose/keypoints.py`:

```python
"""BlazePose 33-landmark canonical ordering.

Reference: https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/pose.md
This ordering is the canonical contract between the Flutter capture layer
(MLKit / MediaPipe) and the server-side analysis pipeline.
"""

from enum import IntEnum

BLAZEPOSE_LANDMARK_COUNT = 33


class LandmarkIndex(IntEnum):
    NOSE = 0
    LEFT_EYE_INNER = 1
    LEFT_EYE = 2
    LEFT_EYE_OUTER = 3
    RIGHT_EYE_INNER = 4
    RIGHT_EYE = 5
    RIGHT_EYE_OUTER = 6
    LEFT_EAR = 7
    RIGHT_EAR = 8
    MOUTH_LEFT = 9
    MOUTH_RIGHT = 10
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_PINKY = 17
    RIGHT_PINKY = 18
    LEFT_INDEX = 19
    RIGHT_INDEX = 20
    LEFT_THUMB = 21
    RIGHT_THUMB = 22
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32


def landmark_index(name: str) -> int:
    """Look up landmark index by lowercase underscored name.

    Example: landmark_index("left_hip") == 23
    """
    return LandmarkIndex[name.upper()].value
```

- [ ] **Step 4: Run the test and confirm it passes**

```bash
cd software/server && uv run pytest tests/unit/test_keypoints.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pose/__init__.py software/server/src/auralink/pose/keypoints.py software/server/tests/unit/test_keypoints.py
git commit -m "feat: add BlazePose 33-landmark canonical ordering"
```

---

### Task 6: Joint angle computation

**Files:**
- Create: `software/server/src/auralink/pose/joint_angles.py`
- Test: `software/server/tests/unit/test_joint_angles.py`

- [ ] **Step 1: Write failing tests**

Create `software/server/tests/unit/test_joint_angles.py`:

```python
import math

import numpy as np
import pytest

from auralink.api.schemas import Frame, Landmark
from auralink.pose.joint_angles import (
    angle_between_points,
    hip_flexion_angle,
    knee_flexion_angle,
    knee_valgus_angle,
)


def _lm(x: float, y: float, z: float = 0.0) -> Landmark:
    return Landmark(x=x, y=y, z=z, visibility=1.0, presence=1.0)


def _frame_with_overrides(overrides: dict[int, Landmark]) -> Frame:
    default = _lm(0.5, 0.5)
    landmarks = [overrides.get(i, default) for i in range(33)]
    return Frame(timestamp_ms=0, landmarks=landmarks)


def test_angle_between_points_90_degrees():
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 0.0])
    c = np.array([0.0, 1.0])
    assert angle_between_points(a, b, c) == pytest.approx(90.0, abs=0.01)


def test_angle_between_points_180_degrees():
    a = np.array([0.0, 0.0])
    b = np.array([1.0, 0.0])
    c = np.array([2.0, 0.0])
    assert angle_between_points(a, b, c) == pytest.approx(180.0, abs=0.01)


def test_angle_between_points_45_degrees():
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 0.0])
    c = np.array([1.0, 1.0])
    assert angle_between_points(a, b, c) == pytest.approx(45.0, abs=0.01)


def test_knee_flexion_straight_leg():
    # Hip above knee above ankle, straight vertical line
    frame = _frame_with_overrides({
        23: _lm(0.5, 0.3),   # left hip
        25: _lm(0.5, 0.5),   # left knee
        27: _lm(0.5, 0.7),   # left ankle
    })
    # Straight leg → knee angle ≈ 180°
    assert knee_flexion_angle(frame, side="left") == pytest.approx(180.0, abs=0.5)


def test_knee_flexion_90_degrees():
    # Hip → knee is vertical, knee → ankle is horizontal
    frame = _frame_with_overrides({
        23: _lm(0.5, 0.3),   # left hip
        25: _lm(0.5, 0.5),   # left knee
        27: _lm(0.7, 0.5),   # left ankle to the right
    })
    assert knee_flexion_angle(frame, side="left") == pytest.approx(90.0, abs=0.5)


def test_hip_flexion_standing():
    # Shoulder above hip above knee, straight line
    frame = _frame_with_overrides({
        11: _lm(0.5, 0.1),   # left shoulder
        23: _lm(0.5, 0.4),   # left hip
        25: _lm(0.5, 0.7),   # left knee
    })
    assert hip_flexion_angle(frame, side="left") == pytest.approx(180.0, abs=0.5)


def test_hip_flexion_seated():
    # Torso vertical, thigh horizontal → hip angle ≈ 90°
    frame = _frame_with_overrides({
        11: _lm(0.5, 0.1),   # left shoulder
        23: _lm(0.5, 0.4),   # left hip
        25: _lm(0.8, 0.4),   # left knee horizontal from hip
    })
    assert hip_flexion_angle(frame, side="left") == pytest.approx(90.0, abs=0.5)


def test_knee_valgus_neutral():
    # Hip, knee, ankle colinear vertically → valgus angle 0°
    frame = _frame_with_overrides({
        23: _lm(0.5, 0.3),   # left hip
        25: _lm(0.5, 0.5),   # left knee
        27: _lm(0.5, 0.7),   # left ankle
    })
    assert knee_valgus_angle(frame, side="left") == pytest.approx(0.0, abs=0.5)


def test_knee_valgus_inward_collapse():
    # Knee has collapsed medially (toward center) relative to hip-ankle line
    frame = _frame_with_overrides({
        23: _lm(0.4, 0.3),   # left hip, on the left
        25: _lm(0.5, 0.5),   # left knee, collapsed inward
        27: _lm(0.4, 0.7),   # left ankle, below hip
    })
    angle = knee_valgus_angle(frame, side="left")
    assert angle > 5.0
```

- [ ] **Step 2: Run the tests and confirm they fail**

```bash
cd software/server && uv run pytest tests/unit/test_joint_angles.py -v
```

Expected: `ModuleNotFoundError: No module named 'auralink.pose.joint_angles'`

- [ ] **Step 3: Create joint_angles module**

Create `software/server/src/auralink/pose/joint_angles.py`:

```python
"""Joint angle computation from BlazePose keypoints.

All angles in degrees. Functions accept a Frame and a side ("left" or "right")
and return the computed joint angle. The math operates in 2D (x, y) — z is
ignored at this scaffolding stage. 3D-aware versions come after MotionBERT
integration.
"""

from typing import Literal

import numpy as np

from auralink.api.schemas import Frame
from auralink.pose.keypoints import LandmarkIndex

Side = Literal["left", "right"]


def _xy(frame: Frame, idx: int) -> np.ndarray:
    lm = frame.landmarks[idx]
    return np.array([lm.x, lm.y], dtype=np.float64)


def angle_between_points(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Return angle ABC in degrees — the angle at vertex B."""
    ba = a - b
    bc = c - b
    ba_norm = np.linalg.norm(ba)
    bc_norm = np.linalg.norm(bc)
    if ba_norm == 0 or bc_norm == 0:
        return 0.0
    cos_angle = np.dot(ba, bc) / (ba_norm * bc_norm)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def knee_flexion_angle(frame: Frame, side: Side) -> float:
    """Knee flexion angle — hip-knee-ankle. 180° = straight leg."""
    if side == "left":
        hip_idx = LandmarkIndex.LEFT_HIP
        knee_idx = LandmarkIndex.LEFT_KNEE
        ankle_idx = LandmarkIndex.LEFT_ANKLE
    else:
        hip_idx = LandmarkIndex.RIGHT_HIP
        knee_idx = LandmarkIndex.RIGHT_KNEE
        ankle_idx = LandmarkIndex.RIGHT_ANKLE
    return angle_between_points(
        _xy(frame, hip_idx),
        _xy(frame, knee_idx),
        _xy(frame, ankle_idx),
    )


def hip_flexion_angle(frame: Frame, side: Side) -> float:
    """Hip flexion angle — shoulder-hip-knee. 180° = standing upright."""
    if side == "left":
        shoulder_idx = LandmarkIndex.LEFT_SHOULDER
        hip_idx = LandmarkIndex.LEFT_HIP
        knee_idx = LandmarkIndex.LEFT_KNEE
    else:
        shoulder_idx = LandmarkIndex.RIGHT_SHOULDER
        hip_idx = LandmarkIndex.RIGHT_HIP
        knee_idx = LandmarkIndex.RIGHT_KNEE
    return angle_between_points(
        _xy(frame, shoulder_idx),
        _xy(frame, hip_idx),
        _xy(frame, knee_idx),
    )


def knee_valgus_angle(frame: Frame, side: Side) -> float:
    """Knee valgus — angle between hip→knee and hip→ankle vectors.

    0° = knee lies on the hip-ankle ray (neutral alignment).
    Positive values indicate the knee has shifted off-line; for a frontal
    camera view this approximates medial collapse (valgus) for small
    deviations. Not a true perpendicular-distance measurement.

    This is a 2D approximation in the coronal plane — camera must be positioned
    frontally for the measurement to be meaningful. The 3D-aware version lands
    after MotionBERT integration.
    """
    if side == "left":
        hip_idx = LandmarkIndex.LEFT_HIP
        knee_idx = LandmarkIndex.LEFT_KNEE
        ankle_idx = LandmarkIndex.LEFT_ANKLE
    else:
        hip_idx = LandmarkIndex.RIGHT_HIP
        knee_idx = LandmarkIndex.RIGHT_KNEE
        ankle_idx = LandmarkIndex.RIGHT_ANKLE

    hip = _xy(frame, hip_idx)
    knee = _xy(frame, knee_idx)
    ankle = _xy(frame, ankle_idx)

    hip_to_ankle = ankle - hip
    hip_to_knee = knee - hip

    hip_ankle_norm = np.linalg.norm(hip_to_ankle)
    hip_knee_norm = np.linalg.norm(hip_to_knee)
    if hip_ankle_norm == 0 or hip_knee_norm == 0:
        return 0.0

    cos_angle = np.dot(hip_to_ankle, hip_to_knee) / (hip_ankle_norm * hip_knee_norm)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))
```

- [ ] **Step 4: Run the tests and confirm they pass**

```bash
cd software/server && uv run pytest tests/unit/test_joint_angles.py -v
```

Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pose/joint_angles.py software/server/tests/unit/test_joint_angles.py
git commit -m "feat: add 2D joint angle computation for hip, knee, valgus"
```

---

### Task 7: Rep segmentation

**Files:**
- Create: `software/server/src/auralink/analysis/__init__.py`
- Create: `software/server/src/auralink/analysis/rep_segmentation.py`
- Test: `software/server/tests/unit/test_rep_segmentation.py`

- [ ] **Step 1: Write failing test**

Create `software/server/tests/unit/test_rep_segmentation.py`:

```python
import numpy as np

from auralink.analysis.rep_segmentation import RepBoundary, segment_reps


def test_segment_reps_single_rep():
    # Simulate one clean squat: angle goes from 180 → 90 → 180 over 30 frames
    descent = np.linspace(180, 90, 15)
    ascent = np.linspace(90, 180, 15)
    angles = np.concatenate([descent, ascent])
    boundaries = segment_reps(angles.tolist(), min_amplitude=30.0)
    assert len(boundaries) == 1
    rep = boundaries[0]
    assert rep.start_index == 0
    assert rep.end_index == 29
    assert rep.bottom_index == 14


def test_segment_reps_multiple_reps():
    # Three reps back to back
    rep_angles = np.concatenate([
        np.linspace(180, 90, 10),
        np.linspace(90, 180, 10),
    ])
    angles = np.tile(rep_angles, 3)
    boundaries = segment_reps(angles.tolist(), min_amplitude=30.0)
    assert len(boundaries) == 3


def test_segment_reps_ignores_noise():
    # Small oscillations without meeting amplitude threshold
    angles = [180.0 + 2.0 * np.sin(i * 0.5) for i in range(50)]
    boundaries = segment_reps(angles, min_amplitude=30.0)
    assert len(boundaries) == 0


def test_rep_boundary_indices_are_valid():
    descent = np.linspace(180, 90, 15)
    ascent = np.linspace(90, 180, 15)
    angles = np.concatenate([descent, ascent])
    boundaries = segment_reps(angles.tolist(), min_amplitude=30.0)
    for rep in boundaries:
        assert rep.start_index < rep.bottom_index < rep.end_index
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd software/server && uv run pytest tests/unit/test_rep_segmentation.py -v
```

Expected: `ModuleNotFoundError: No module named 'auralink.analysis'`

- [ ] **Step 3: Create rep_segmentation module**

Create empty `software/server/src/auralink/analysis/__init__.py`.

Create `software/server/src/auralink/analysis/rep_segmentation.py`:

```python
"""Rep segmentation from a scalar joint-angle time series.

A rep is bounded by two local maxima (near the "top" of the movement)
with a local minimum (the "bottom") between them. We identify reps by:

1. Find all local maxima and local minima in the angle series.
2. For each adjacent (max, min, max) triple, compute amplitude (max - min).
3. Keep triples whose amplitude exceeds min_amplitude (filters noise).

This is sufficient for squats, lunges, push-ups — movements with a clear
flexion→extension cycle around a single joint angle. Continuous movements
like rollup use phase_segmentation instead (not in this scaffold).
"""

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class RepBoundary:
    start_index: int
    bottom_index: int
    end_index: int
    start_angle: float
    bottom_angle: float
    end_angle: float


def _find_local_extrema(
    series: Sequence[float],
) -> tuple[list[int], list[int]]:
    """Return (maxima_indices, minima_indices).

    Handles plateaus: each run of equal values is treated as a single
    extremum anchored at its leftmost index. Endpoints count as extrema
    based on the direction of the adjacent non-equal value.
    """
    maxima: list[int] = []
    minima: list[int] = []
    n = len(series)
    if n < 3:
        return maxima, minima

    i = 0
    while i < n:
        j = i
        while j + 1 < n and series[j + 1] == series[i]:
            j += 1

        prev_val = series[i - 1] if i > 0 else None
        next_val = series[j + 1] if j + 1 < n else None
        val = series[i]

        if prev_val is None and next_val is not None:
            if val >= next_val:
                maxima.append(i)
            else:
                minima.append(i)
        elif next_val is None and prev_val is not None:
            if val >= prev_val:
                maxima.append(i)
            else:
                minima.append(i)
        elif prev_val is not None and next_val is not None:
            if val > prev_val and val > next_val:
                maxima.append(i)
            elif val < prev_val and val < next_val:
                minima.append(i)

        i = j + 1

    return maxima, minima


def segment_reps(
    angle_series: Sequence[float],
    min_amplitude: float = 30.0,
) -> list[RepBoundary]:
    """Segment a scalar angle series into rep boundaries.

    Args:
        angle_series: Sequence of joint angles in degrees over time.
        min_amplitude: Minimum amplitude (max - min) to qualify as a rep.

    Returns:
        List of RepBoundary objects in temporal order.
    """
    maxima, minima = _find_local_extrema(angle_series)
    if not maxima or not minima:
        return []

    # Merge into a sorted event list
    events = sorted(
        [(i, "max") for i in maxima] + [(i, "min") for i in minima]
    )

    reps: list[RepBoundary] = []
    # Walk events looking for (max, min, max) triples
    for j in range(len(events) - 2):
        e1, e2, e3 = events[j], events[j + 1], events[j + 2]
        if e1[1] == "max" and e2[1] == "min" and e3[1] == "max":
            start, bottom, end = e1[0], e2[0], e3[0]
            amplitude = max(angle_series[start], angle_series[end]) - angle_series[bottom]
            if amplitude >= min_amplitude:
                reps.append(
                    RepBoundary(
                        start_index=start,
                        bottom_index=bottom,
                        end_index=end,
                        start_angle=angle_series[start],
                        bottom_angle=angle_series[bottom],
                        end_angle=angle_series[end],
                    )
                )
    return reps
```

- [ ] **Step 4: Run the test and confirm it passes**

```bash
cd software/server && uv run pytest tests/unit/test_rep_segmentation.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/analysis/__init__.py software/server/src/auralink/analysis/rep_segmentation.py software/server/tests/unit/test_rep_segmentation.py
git commit -m "feat: add rep segmentation from joint angle time series"
```

---

### Task 8: FastAPI app with health endpoint

**Files:**
- Create: `software/server/src/auralink/api/main.py`
- Create: `software/server/src/auralink/api/routes/__init__.py`
- Create: `software/server/src/auralink/api/routes/health.py`
- Test: `software/server/tests/integration/__init__.py`
- Test: `software/server/tests/integration/test_health.py`

- [ ] **Step 1: Write failing test**

Create `software/server/tests/integration/__init__.py` (empty).

Create `software/server/tests/integration/test_health.py`:

```python
from fastapi.testclient import TestClient

from auralink.api.main import create_app


def test_health_endpoint():
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "auralink-server"
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd software/server && uv run pytest tests/integration/test_health.py -v
```

Expected: `ModuleNotFoundError: No module named 'auralink.api.main'`

- [ ] **Step 3: Create routes package and health endpoint**

Create empty `software/server/src/auralink/api/routes/__init__.py`.

Create `software/server/src/auralink/api/routes/health.py`:

```python
from fastapi import APIRouter

from auralink.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "app": settings.app_name}
```

- [ ] **Step 4: Create app factory**

Create `software/server/src/auralink/api/main.py`:

```python
from fastapi import FastAPI

from auralink.api.routes import health
from auralink.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health.router)
    return app


app = create_app()
```

- [ ] **Step 5: Run the test and confirm it passes**

```bash
cd software/server && uv run pytest tests/integration/test_health.py -v
```

Expected: 1 passed

- [ ] **Step 6: Commit**

```bash
git add software/server/src/auralink/api/main.py software/server/src/auralink/api/routes/__init__.py software/server/src/auralink/api/routes/health.py software/server/tests/integration/__init__.py software/server/tests/integration/test_health.py
git commit -m "feat: add FastAPI app factory and health endpoint"
```

---

### Task 9: Session ingest endpoint

**Files:**
- Create: `software/server/src/auralink/api/routes/sessions.py`
- Modify: `software/server/src/auralink/api/main.py` (add sessions router)
- Test: `software/server/tests/integration/test_sessions_endpoint.py`

- [ ] **Step 1: Write failing test**

Create `software/server/tests/integration/test_sessions_endpoint.py`:

```python
from fastapi.testclient import TestClient

from auralink.api.main import create_app


def _sample_payload() -> dict:
    landmark = {
        "x": 0.5,
        "y": 0.5,
        "z": 0.0,
        "visibility": 1.0,
        "presence": 1.0,
    }
    frame = {
        "timestamp_ms": 0,
        "landmarks": [landmark for _ in range(33)],
    }
    return {
        "metadata": {
            "movement": "overhead_squat",
            "device": "Pixel 8",
            "model": "mlkit_pose_detection",
            "frame_rate": 30.0,
        },
        "frames": [frame],
    }


def test_post_session_returns_id(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    response = client.post("/sessions", json=_sample_payload())
    assert response.status_code == 201
    body = response.json()
    assert "session_id" in body
    assert body["frames_received"] == 1


def test_post_session_rejects_bad_landmark_count(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    payload = _sample_payload()
    payload["frames"][0]["landmarks"] = payload["frames"][0]["landmarks"][:10]
    response = client.post("/sessions", json=payload)
    assert response.status_code == 422


def test_get_session_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    post_response = client.post("/sessions", json=_sample_payload())
    session_id = post_response.json()["session_id"]

    get_response = client.get(f"/sessions/{session_id}")
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["metadata"]["movement"] == "overhead_squat"
    assert len(body["frames"]) == 1
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
cd software/server && uv run pytest tests/integration/test_sessions_endpoint.py -v
```

Expected: 404 on POST /sessions — route not registered.

- [ ] **Step 3: Create sessions route**

Create `software/server/src/auralink/api/routes/sessions.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status

from auralink.api.schemas import Session, SessionCreateResponse
from auralink.config import Settings, get_settings
from auralink.pipeline.storage import SessionStorage

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_storage(settings: Settings = Depends(get_settings)) -> SessionStorage:
    return SessionStorage(base_dir=settings.sessions_dir)


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session: Session,
    storage: SessionStorage = Depends(_get_storage),
) -> SessionCreateResponse:
    session_id = storage.save(session)
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

- [ ] **Step 4: Register the router**

Modify `software/server/src/auralink/api/main.py` — replace existing content:

```python
from fastapi import FastAPI

from auralink.api.routes import health, sessions
from auralink.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health.router)
    app.include_router(sessions.router)
    return app


app = create_app()
```

- [ ] **Step 5: Run the test and confirm it passes**

```bash
cd software/server && uv run pytest tests/integration/test_sessions_endpoint.py -v
```

Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add software/server/src/auralink/api/routes/sessions.py software/server/src/auralink/api/main.py software/server/tests/integration/test_sessions_endpoint.py
git commit -m "feat: add session ingest and retrieval endpoints"
```

---

### Task 10: Placeholder modules for future stages

These modules exist as import targets so later plans can extend them without restructuring. No tests — they're stubs.

**Files:**
- Create: `software/server/src/auralink/pipeline/orchestrator.py`
- Create: `software/server/src/auralink/reasoning/__init__.py`
- Create: `software/server/src/auralink/reasoning/chains.py`
- Create: `software/server/src/auralink/reasoning/thresholds.py`
- Create: `software/server/src/auralink/models/__init__.py`
- Create: `software/server/src/auralink/models/registry.py`

- [ ] **Step 1: Create orchestrator stub**

Create `software/server/src/auralink/pipeline/orchestrator.py`:

```python
"""Pipeline orchestrator — placeholder.

The orchestrator chains analysis stages together in order:
ingest → joint angles → rep segmentation → (3D lift) → (SKEL) → chain reasoning → report.

Each stage consumes and produces a session artifact. This file will be
filled in by a later plan once MotionBERT and HSMR are integrated.
"""

from auralink.api.schemas import Session


def run_pipeline(session: Session) -> dict:
    """Placeholder — returns session metadata only.

    Full pipeline implementation lives in a follow-on plan.
    """
    return {
        "movement": session.metadata.movement,
        "frame_count": len(session.frames),
        "status": "scaffolded — no analysis stages wired yet",
    }
```

- [ ] **Step 2: Create reasoning stubs**

Create empty `software/server/src/auralink/reasoning/__init__.py`.

Create `software/server/src/auralink/reasoning/chains.py`:

```python
"""Fascial chain definitions — SBL, BFL, FFL.

Per the research integration report §2.5, chains are modeled as
graph paths over the skeleton. Only the three chains with strong
anatomical evidence (Wilke 2016, Kalichman 2025) are included.
"""

from dataclasses import dataclass
from enum import Enum


class ChainName(str, Enum):
    SBL = "superficial_back_line"
    BFL = "back_functional_line"
    FFL = "front_functional_line"


@dataclass(frozen=True)
class ChainDefinition:
    name: ChainName
    description: str
    anatomical_path: list[str]


CHAIN_DEFINITIONS: dict[ChainName, ChainDefinition] = {
    ChainName.SBL: ChainDefinition(
        name=ChainName.SBL,
        description="Plantar fascia through calves, hamstrings, erector spinae, to skull base.",
        anatomical_path=[
            "plantar_fascia",
            "gastrocnemius",
            "hamstrings",
            "sacrotuberous_ligament",
            "erector_spinae",
            "epicranial_fascia",
        ],
    ),
    ChainName.BFL: ChainDefinition(
        name=ChainName.BFL,
        description="Latissimus dorsi through thoracolumbar fascia to contralateral gluteus maximus.",
        anatomical_path=[
            "latissimus_dorsi",
            "thoracolumbar_fascia",
            "contralateral_gluteus_maximus",
            "vastus_lateralis",
        ],
    ),
    ChainName.FFL: ChainDefinition(
        name=ChainName.FFL,
        description="Pectoralis major through rectus abdominis to contralateral adductors.",
        anatomical_path=[
            "pectoralis_major",
            "rectus_abdominis",
            "contralateral_adductor_longus",
        ],
    ),
}
```

Create `software/server/src/auralink/reasoning/thresholds.py`:

```python
"""Joint angle thresholds for chain reasoning.

v1 uses a single default population. Body-type adjustment (hypermobile,
female, youth) arrives in a follow-on plan that fills in the conditional
table. See research-integration-report.md §5.4.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ThresholdSet:
    knee_valgus_concern: float  # degrees
    knee_valgus_flag: float
    hip_drop_concern: float
    hip_drop_flag: float


# Placeholder values — calibrate from research before shipping.
# Sources: Hewett 2005 (10° valgus = 2.5x ACL risk)
DEFAULT_THRESHOLDS = ThresholdSet(
    knee_valgus_concern=8.0,
    knee_valgus_flag=12.0,
    hip_drop_concern=5.0,
    hip_drop_flag=10.0,
)
```

- [ ] **Step 3: Create models registry stub**

Create empty `software/server/src/auralink/models/__init__.py`.

Create `software/server/src/auralink/models/registry.py`:

```python
"""Model checkpoint management — placeholder.

Tracks which models are loaded at runtime. Future plans will add
MotionBERT and HSMR loaders that register themselves here at startup.
"""

from dataclasses import dataclass, field


@dataclass
class ModelRegistry:
    loaded: dict[str, str] = field(default_factory=dict)

    def register(self, name: str, version: str) -> None:
        self.loaded[name] = version

    def info(self) -> dict[str, str]:
        return dict(self.loaded)


REGISTRY = ModelRegistry()
```

- [ ] **Step 4: Verify nothing broke**

```bash
cd software/server && uv run pytest -v
```

Expected: all tests pass (no new tests in this task, but existing tests must still pass since imports changed).

- [ ] **Step 5: Commit**

```bash
git add software/server/src/auralink/pipeline/orchestrator.py software/server/src/auralink/reasoning/ software/server/src/auralink/models/
git commit -m "chore: add placeholder modules for chains, thresholds, models"
```

---

### Task 11: Dev script and test fixtures directory

**Files:**
- Create: `software/server/scripts/dev.sh`
- Create: `software/server/tests/conftest.py`
- Create: `software/server/tests/fixtures/README.md`

- [ ] **Step 1: Create dev script**

Create `software/server/scripts/dev.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

export AURALINK_DATA_DIR="${AURALINK_DATA_DIR:-./data}"
mkdir -p "$AURALINK_DATA_DIR"

uv run uvicorn auralink.api.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
chmod +x software/server/scripts/dev.sh
```

- [ ] **Step 2: Create pytest conftest**

Create `software/server/tests/conftest.py`:

```python
"""Shared pytest fixtures for BioLiminal server tests."""

import pytest

from auralink.api.schemas import Frame, Landmark, Session, SessionMetadata


@pytest.fixture
def neutral_landmark() -> Landmark:
    return Landmark(x=0.5, y=0.5, z=0.0, visibility=1.0, presence=1.0)


@pytest.fixture
def neutral_frame(neutral_landmark: Landmark) -> Frame:
    return Frame(
        timestamp_ms=0,
        landmarks=[neutral_landmark for _ in range(33)],
    )


@pytest.fixture
def minimal_session(neutral_frame: Frame) -> Session:
    return Session(
        metadata=SessionMetadata(
            movement="overhead_squat",
            device="test-device",
            model="test-model",
            frame_rate=30.0,
        ),
        frames=[neutral_frame],
    )
```

- [ ] **Step 3: Create fixtures README**

Create `software/server/tests/fixtures/README.md`:

```markdown
# Test Fixtures

This directory holds recorded session JSON files used as ground-truth inputs for
integration and pipeline tests.

## Golden captures (from Flutter team)

The Flutter capture layer ships with a golden-capture test harness that records
raw MLKit landmark streams for reference movements on real devices. These
recordings become the canonical fixtures for server-side pipeline validation.

Expected format: JSON matching `auralink.api.schemas.Session`. Filename pattern:

```
{movement}_{device}_{capture_date}.json
```

Example: `overhead_squat_pixel8_20260415.json`

## Naming conventions

Keep fixtures small — for regression tests, ~5 seconds of capture at 30fps is
plenty. If a fixture exceeds 1MB, trim the frame range before committing.

## What goes here vs `data/`

- `tests/fixtures/` → committed to git, small, curated for testing
- `data/sessions/` → local dev data, gitignored, arbitrary size
```

- [ ] **Step 4: Verify test suite still passes**

```bash
cd software/server && uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add software/server/scripts/dev.sh software/server/tests/conftest.py software/server/tests/fixtures/README.md
git commit -m "chore: add dev script, conftest, and fixtures directory"
```

---

### Task 12: BlazePose landmark reference doc

**Files:**
- Create: `software/server/docs/blazepose_landmark_reference.md`

Server-side internal reference for the BlazePose 33-landmark ordering that the analysis pipeline assumes. The canonical Flutter ↔ server model interface contract (`custom_model_contract.md`) is owned by the Flutter team; this doc complements it with the server's view of the landmark schema.

- [ ] **Step 1: Create the reference doc**

Create `software/server/docs/blazepose_landmark_reference.md`:

```markdown
# BlazePose Landmark Reference (Server)

Internal reference for the BlazePose 33-landmark ordering assumed by the BioLiminal server's analysis pipeline. The canonical model interface contract is `custom_model_contract.md` (owned by the Flutter team). This doc is the server's view of the landmark schema.

## Canonical Spec — BlazePose 33 Landmarks

### Input
- **Shape:** `[1, 256, 256, 3]` float32 for `BlazePose Full`, `[1, 192, 192, 3]` for `BlazePose Lite`
- **Normalization:** `pixel / 255.0` → range `[0, 1]`
- **Color order:** RGB, not BGR

### Output
- **Landmarks tensor:** shape `[1, 195]` flattened, reshapes to `[1, 39, 5]`
  - 39 landmarks (33 body + 6 auxiliary)
  - 5 values per landmark: `[x, y, z, visibility, presence]`
- **Pose presence flag:** scalar, sigmoid'd, `≥0.5` = person detected
- **Segmentation mask:** optional, ignored downstream
- **Heatmaps:** intermediate, ignored downstream

### Coordinate Space
- `x`, `y`: input pixel coordinates (`[0, 256]` Full, `[0, 192]` Lite). **Not normalized** to `[0, 1]` at model output — Flutter app rescales to `[0, 1]` before sending to server.
- `z`: depth relative to hip midpoint in the same pixel units. Not meters.

### Visibility & Presence
- **Already sigmoid'd** in model output, range `[0, 1]`. Do not apply sigmoid again.
- `visibility` = landmark is in-frame and unoccluded
- `presence` = landmark is detected at all

### Landmark Ordering
Landmarks 0-32 follow the canonical BlazePose body ordering:

| Index | Name |
|-------|------|
| 0 | nose |
| 1 | left_eye_inner |
| 2 | left_eye |
| 3 | left_eye_outer |
| 4 | right_eye_inner |
| 5 | right_eye |
| 6 | right_eye_outer |
| 7 | left_ear |
| 8 | right_ear |
| 9 | mouth_left |
| 10 | mouth_right |
| 11 | left_shoulder |
| 12 | right_shoulder |
| 13 | left_elbow |
| 14 | right_elbow |
| 15 | left_wrist |
| 16 | right_wrist |
| 17 | left_pinky |
| 18 | right_pinky |
| 19 | left_index |
| 20 | right_index |
| 21 | left_thumb |
| 22 | right_thumb |
| 23 | left_hip |
| 24 | right_hip |
| 25 | left_knee |
| 26 | right_knee |
| 27 | left_ankle |
| 28 | right_ankle |
| 29 | left_heel |
| 30 | right_heel |
| 31 | left_foot_index |
| 32 | right_foot_index |

Landmarks 33-38 are auxiliary (used internally by BlazePose for next-frame ROI prediction). They are ignored by BioLiminal.

Reference: https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/pose.md

## Server-Side Contract

The server consumes JSON sessions matching the pydantic schema in `auralink.api.schemas.Session`:

```json
{
  "metadata": {
    "movement": "overhead_squat",
    "device": "Pixel 8",
    "model": "mlkit_pose_detection",
    "frame_rate": 30.0,
    "captured_at": "2026-04-09T14:32:00Z"
  },
  "frames": [
    {
      "timestamp_ms": 0,
      "landmarks": [
        {"x": 0.52, "y": 0.31, "z": -0.08, "visibility": 0.98, "presence": 0.99}
      ]
    }
  ]
}
```

Landmark coordinates are normalized to `[0, 1]` before sending to the server. The Flutter app is responsible for rescaling from model pixel-space to `[0, 1]` frame-space.

## If You Cannot Match the Canonical Spec

Provide a mapping table. The mapping layer lives in the Flutter capture layer, not the server. The server only accepts BlazePose 33-landmark format.

Example mapping table entry:
```yaml
custom_model_output_index: 5
blazepose_canonical_index: 11  # left_shoulder
transform: null  # or "swap_xy" / "flip_y" if needed
```

## Why This Matters

Every downstream reference in BioLiminal — joint angle math, chain reasoning, threshold tables, test fixtures, research paper citations — assumes BlazePose 33-landmark ordering. Deviating creates permanent tax on every future integration.
```

- [ ] **Step 2: Commit**

```bash
git add software/server/docs/blazepose_landmark_reference.md
git commit -m "docs: add server-side BlazePose landmark reference"
```

---

### Task 13: Full test run and scaffolding validation

- [ ] **Step 1: Run complete test suite**

```bash
cd software/server && uv run pytest -v
```

Expected: all tests pass. Count should be approximately:
- Task 2: 2 tests (config)
- Task 3: 6 tests (schemas)
- Task 4: 3 tests (storage)
- Task 5: 3 tests (keypoints)
- Task 6: 9 tests (joint angles)
- Task 7: 4 tests (rep segmentation)
- Task 8: 1 test (health endpoint)
- Task 9: 3 tests (sessions endpoint)
- **Total: ~31 tests**

- [ ] **Step 2: Verify dev server starts**

```bash
cd software/server && ./scripts/dev.sh &
sleep 3
curl -s http://localhost:8000/health
kill %1
```

Expected: `{"status":"ok","app":"auralink-server"}`

- [ ] **Step 3: Verify ruff and black pass**

```bash
cd software/server && uv run ruff check . && uv run black --check .
```

Expected: no errors.

- [ ] **Step 4: Final commit if anything changed**

```bash
git status
# If clean, skip. Otherwise:
git add -u
git commit -m "chore: scaffold validation — all tests pass, server starts, lint clean"
```

---

## Self-Review Checklist

1. **Spec coverage:** Every file listed in the File Structure section has a task creating it. ✓
2. **Placeholder scan:** No "TBD" or "TODO implement later" in the task bodies. Placeholder modules (Task 10) are explicitly marked as stubs for future plans.
3. **Type consistency:** `Session`, `Frame`, `Landmark`, `SessionMetadata` names used consistently across Tasks 3, 4, 8, 9, 11. `LandmarkIndex` used consistently in Tasks 5 and 6.
4. **Task ordering:** Tasks are dependency-ordered. Task 2 (config) before Task 8 (app using config). Task 3 (schemas) before Task 4 (storage uses schemas). Task 5 (keypoints) before Task 6 (joint angles uses keypoints). Task 6 (joint angles) before Task 7 (rep segmentation consumes angle series). Task 8 (health endpoint) before Task 9 (sessions endpoint, both on the same app).

## What's NOT in This Plan

These land in follow-on plans once the scaffold is merged:

- MotionBERT integration (2D→3D lifting)
- HSMR integration (SKEL fitting)
- DTW rep comparison and trend analysis
- Phase segmentation for continuous movements (rollup)
- Chain reasoning engine evaluation
- Report generation templates
- Body type classifier and threshold adjustment tables
- Flutter mobile app (teammate's domain)
- Golden-capture fixtures from Flutter (imported when available)
- Model serving infrastructure (Replicate, Modal, or self-hosted)

---

## Execution Handoff

Plan complete. Given the user's "begin scaffolding now" directive, I'm executing inline in this session using sequential task execution. Each task completes with TDD (red → green → commit) per the skill.
