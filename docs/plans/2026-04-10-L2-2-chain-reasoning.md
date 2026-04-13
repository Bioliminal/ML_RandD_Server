# L2 Plan 2 — Chain Reasoning v1 + Report Assembly

**Status:** Ready for execution via parallel-plan-executor
**Parent:** `2026-04-10-analysis-pipeline-epoch.md`
**Depends on:** Plan 1 (pipeline framework, PerRepMetrics, WithinMovementTrend), Plan 4 (synthetic fixtures, load_fixture helper)
**Supersedes:** Stub version of this file from 2026-04-10
**Created:** 2026-04-11
**Execution:** parallel-plan-executor, 19 tasks, 8 waves, max parallelism 6

## Goal

Turn the raw `PipelineArtifacts` produced by Plan 1 into a structured, human-readable `Report` with rule-based chain reasoning over the Superficial Back Line (SBL), Back Functional Line (BFL), and Front Functional Line (FFL). Ship the free-tier end-to-end value: `POST /sessions` → `GET /sessions/{id}/report` returns a wellness-positioned report with chain observations.

## Design Decisions (Locked)

1. **Report is assembled on-demand in the endpoint**, NOT as a pipeline stage. The `GET /sessions/{id}/report` handler loads `PipelineArtifacts` from storage, calls `assemble_report(artifacts, session_metadata)`, and returns the result.
2. **Chain reasoning IS a pipeline stage.** It reads artifacts, produces `list[ChainObservation]`, and stores them back on `PipelineArtifacts.chain_observations`.
3. **Rules and thresholds are YAML-driven.** Pydantic models (`RuleConfig`, `ThresholdSetConfig`) validate loaded YAML. Pure `pyyaml` + pydantic — no `pydantic-yaml` dependency.
4. **Threshold adjustments via body-type profile.** `BodyTypeProfile` drives `adjust_for_body_type(base, profile, adjustments) -> ThresholdSetConfig`.
5. **Temporal / cross-movement slots are empty stubs.** Plan 3 fills them.
6. **Wellness language enforcement is a pytest scan** over `config/rules/*.yaml` narrative templates (regex against forbidden terms).
7. **One new runtime dep:** `pyyaml>=6.0`. Added explicitly as Task PRE1 in Wave 0 (runs alone before Wave A) because B1, B2, and F2 all import yaml.
8. **Wellness positioning:** All narrative text uses "your movement shows X pattern", "body connection from A to B", "opportunity to explore". NEVER "diagnosis", "dysfunction", "drivers of pain", "injury", "damage", "pathology".

## File Tree Delta

```
software/server/src/auralink/
├── reasoning/
│   ├── observations.py         # NEW — ChainObservation schema
│   ├── body_type.py            # NEW — BodyTypeProfile schema
│   ├── config_schemas.py       # NEW — pydantic models for YAML config
│   ├── thresholds.py           # MODIFIED — ThresholdSet re-exports ThresholdSetConfig
│   ├── threshold_loader.py     # NEW — YAML loaders + body-type adjustment
│   ├── rule_loader.py          # NEW — YAML rule loader
│   └── rule_engine.py          # NEW — ChainReasoner protocol + RuleBasedChainReasoner
├── report/
│   ├── __init__.py             # NEW (empty)
│   ├── schemas.py              # NEW — Report pydantic model + stubs
│   └── assembler.py            # NEW — assemble_report()
├── pipeline/
│   ├── artifacts.py            # MODIFIED (B4) — adds chain_observations field
│   ├── orchestrator.py         # MODIFIED (E1) — wires run_chain_reasoning + _assemble_artifacts
│   └── stages/
│       ├── base.py             # MODIFIED (D1) — adds STAGE_NAME_CHAIN_REASONING constant
│       └── chain_reasoning.py  # NEW (D1) — run_chain_reasoning module-level function
└── api/routes/reports.py       # MODIFIED (E2) — returns Report not raw artifacts

software/server/config/
├── thresholds/
│   ├── default.yaml                     # NEW
│   └── body_type_adjustments.yaml       # NEW
└── rules/
    ├── sbl.yaml                         # NEW
    ├── bfl.yaml                         # NEW
    └── ffl.yaml                         # NEW

software/server/tests/
├── unit/reasoning/                      # NEW — per-module tests
├── unit/report/                         # NEW — schema + assembler tests
├── unit/pipeline/                       # MODIFIED — chain reasoning stage + orchestrator wiring + artifacts field tests
├── unit/api/                            # MODIFIED — reports route tests
└── integration/test_full_report.py      # NEW — fixture → full report
```

## Task List

---

#### Task PRE1: Add pyyaml runtime dependency

**Label:** skip-tdd

**Files owned (exclusive to this task):**
- `software/server/pyproject.toml`

**Depends on:** nothing

**Rationale:** Tasks B1, B2, and F2 all `import yaml`, but `pyyaml` is NOT currently in `software/server/pyproject.toml` `[project.dependencies]`. Adding the dep inside a parallel wave would race; PRE1 lives in its own Wave 0 that runs alone before Wave A.

**Steps:**

1. Read the current `software/server/pyproject.toml` `[project] dependencies` list.
2. If `pyyaml` is not already present, add `"pyyaml>=6.0"` to the list. Any alphabetical position in the list is acceptable.
3. Run `cd software/server && uv sync` to install it into the uv-managed venv.
4. **Verify:** `cd software/server && uv run python -c "import yaml; print(yaml.__version__)"` — should print a version string (e.g., `6.0.2`).

**Expected result:** `pyyaml>=6.0` appears in `[project.dependencies]`; `uv sync` completes without error; the verify command prints a version.

**Commit message:** `chore(deps): add pyyaml for chain reasoning config loaders`

---

#### Task A1: ChainObservation schema

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/reasoning/observations.py`
- `software/server/tests/unit/reasoning/test_observations.py`

**Depends on:** nothing

**Exact file contents (verbatim):**

`software/server/src/auralink/reasoning/observations.py`:
```python
from enum import StrEnum

from pydantic import BaseModel, Field

from auralink.reasoning.chains import ChainName


class ObservationSeverity(StrEnum):
    INFO = "info"
    CONCERN = "concern"
    FLAG = "flag"


class ChainObservation(BaseModel):
    chain: ChainName
    severity: ObservationSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    trigger_rule: str
    involved_joints: list[str] = Field(default_factory=list)
    evidence: dict[str, float] = Field(default_factory=dict)
    narrative: str
```

**Test file:**

`software/server/tests/unit/reasoning/test_observations.py`:
```python
import pytest
from pydantic import ValidationError

from auralink.reasoning.chains import ChainName
from auralink.reasoning.observations import ChainObservation, ObservationSeverity


def test_creates_observation():
    obs = ChainObservation(
        chain=ChainName.SBL,
        severity=ObservationSeverity.CONCERN,
        confidence=0.8,
        trigger_rule="sbl_knee_valgus_concern",
        involved_joints=["ankle", "knee", "hip"],
        evidence={"mean_knee_valgus_deg": 9.5},
        narrative="Your knee tracking shows 9.5 degrees of inward movement.",
    )
    assert obs.chain == ChainName.SBL
    assert obs.severity == ObservationSeverity.CONCERN
    assert obs.involved_joints == ["ankle", "knee", "hip"]


def test_rejects_confidence_above_one():
    with pytest.raises(ValidationError):
        ChainObservation(
            chain=ChainName.SBL,
            severity=ObservationSeverity.INFO,
            confidence=1.5,
            trigger_rule="x",
            narrative="n",
        )


def test_serializes_to_dict_with_chain_value():
    obs = ChainObservation(
        chain=ChainName.BFL,
        severity=ObservationSeverity.FLAG,
        confidence=0.9,
        trigger_rule="bfl_test",
        narrative="n",
    )
    data = obs.model_dump(mode="json")
    assert data["chain"] == "back_functional_line"
    assert data["severity"] == "flag"
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/reasoning/test_observations.py -v`

**Expected result:** `3 passed`

**Commit message:** `feat(reasoning): add ChainObservation pydantic schema`

---

#### Task A2: BodyTypeProfile schema

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/reasoning/body_type.py`
- `software/server/tests/unit/reasoning/test_body_type.py`

**Depends on:** nothing

**Exact file contents (verbatim):**

`software/server/src/auralink/reasoning/body_type.py`:
```python
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class Sex(StrEnum):
    FEMALE = "female"
    MALE = "male"
    UNSPECIFIED = "unspecified"


class BodyTypeProfile(BaseModel):
    sex: Sex = Sex.UNSPECIFIED
    hypermobile: bool = False
    age_range: Literal["youth", "adult", "senior"] = "adult"
```

**Test file:**

`software/server/tests/unit/reasoning/test_body_type.py`:
```python
from auralink.reasoning.body_type import BodyTypeProfile, Sex


def test_default_profile():
    profile = BodyTypeProfile()
    assert profile.sex == Sex.UNSPECIFIED
    assert profile.hypermobile is False
    assert profile.age_range == "adult"


def test_hypermobile_profile():
    profile = BodyTypeProfile(sex=Sex.FEMALE, hypermobile=True, age_range="youth")
    assert profile.sex == Sex.FEMALE
    assert profile.hypermobile is True
    assert profile.age_range == "youth"
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/reasoning/test_body_type.py -v`

**Expected result:** `2 passed`

**Commit message:** `feat(reasoning): add BodyTypeProfile schema`

---

#### Task A3: Config schemas (ThresholdSetConfig, BodyTypeAdjustment, RuleConfig)

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/reasoning/config_schemas.py`
- `software/server/tests/unit/reasoning/test_config_schemas.py`

**Depends on:** nothing

**Exact file contents (verbatim):**

`software/server/src/auralink/reasoning/config_schemas.py`:
```python
from typing import Literal

from pydantic import BaseModel, Field

from auralink.reasoning.chains import ChainName


class ThresholdSetConfig(BaseModel):
    knee_valgus_concern: float
    knee_valgus_flag: float
    hip_drop_concern: float
    hip_drop_flag: float
    trunk_lean_concern: float
    trunk_lean_flag: float


class BodyTypeAdjustment(BaseModel):
    applies_to_sex: list[str] = Field(default_factory=list)
    applies_to_hypermobile: bool | None = None
    applies_to_age_range: list[str] = Field(default_factory=list)
    threshold_overrides: dict[str, float] = Field(default_factory=dict)


class BodyTypeAdjustmentsConfig(BaseModel):
    adjustments: list[BodyTypeAdjustment] = Field(default_factory=list)


class RuleConfig(BaseModel):
    rule_id: str
    chain: ChainName
    applies_to_movements: list[str] = Field(min_length=1)
    metric_key: Literal[
        "mean_knee_valgus_deg",
        "mean_trunk_lean_deg",
        "rom_deg",
        "peak_velocity_deg_per_s",
    ]
    aggregation: Literal["max", "min", "mean"]
    threshold_concern_ref: str
    threshold_flag_ref: str
    involved_joints: list[str] = Field(default_factory=list)
    narrative_template: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
```

**Test file:**

`software/server/tests/unit/reasoning/test_config_schemas.py`:
```python
import pytest
from pydantic import ValidationError

from auralink.reasoning.chains import ChainName
from auralink.reasoning.config_schemas import (
    BodyTypeAdjustment,
    RuleConfig,
    ThresholdSetConfig,
)


def test_threshold_set_config_validates():
    cfg = ThresholdSetConfig(
        knee_valgus_concern=8.0,
        knee_valgus_flag=12.0,
        hip_drop_concern=5.0,
        hip_drop_flag=10.0,
        trunk_lean_concern=6.0,
        trunk_lean_flag=10.0,
    )
    assert cfg.knee_valgus_flag == 12.0


def test_rule_config_validates():
    rule = RuleConfig(
        rule_id="sbl_test",
        chain=ChainName.SBL,
        applies_to_movements=["overhead_squat"],
        metric_key="mean_knee_valgus_deg",
        aggregation="max",
        threshold_concern_ref="knee_valgus_concern",
        threshold_flag_ref="knee_valgus_flag",
        involved_joints=["knee"],
        narrative_template="value {value:.1f}",
    )
    assert rule.confidence == 0.8
    assert rule.chain == ChainName.SBL


def test_rule_config_rejects_bad_metric_key():
    with pytest.raises(ValidationError):
        RuleConfig(
            rule_id="bad",
            chain=ChainName.SBL,
            applies_to_movements=["overhead_squat"],
            metric_key="not_a_real_metric",
            aggregation="max",
            threshold_concern_ref="x",
            threshold_flag_ref="y",
            narrative_template="n",
        )


def test_body_type_adjustment_defaults():
    adj = BodyTypeAdjustment()
    assert adj.applies_to_sex == []
    assert adj.applies_to_hypermobile is None
    assert adj.applies_to_age_range == []
    assert adj.threshold_overrides == {}
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/reasoning/test_config_schemas.py -v`

**Expected result:** `4 passed`

**Commit message:** `feat(reasoning): add pydantic config schemas for thresholds and rules`

---

#### Task A4: Threshold YAML config files

**Label:** skip-tdd

**Files owned (exclusive to this task):**
- `software/server/config/thresholds/default.yaml`
- `software/server/config/thresholds/body_type_adjustments.yaml`

**Depends on:** nothing

**Exact file contents (verbatim):**

`software/server/config/thresholds/default.yaml`:
```yaml
knee_valgus_concern: 8.0
knee_valgus_flag: 12.0
hip_drop_concern: 5.0
hip_drop_flag: 10.0
trunk_lean_concern: 6.0
trunk_lean_flag: 10.0
```

`software/server/config/thresholds/body_type_adjustments.yaml`:
```yaml
adjustments:
  - applies_to_hypermobile: true
    threshold_overrides:
      knee_valgus_concern: 10.0
      knee_valgus_flag: 15.0
      hip_drop_concern: 7.0
      hip_drop_flag: 12.0
  - applies_to_age_range: [youth]
    threshold_overrides:
      trunk_lean_concern: 8.0
      trunk_lean_flag: 12.0
```

**Verification command (no tests — loader tests in B1 validate schema):**
```
python -c "import yaml; yaml.safe_load(open('software/server/config/thresholds/default.yaml')); yaml.safe_load(open('software/server/config/thresholds/body_type_adjustments.yaml'))"
```

**Expected result:** runs clean (exit 0, no output)

**Commit message:** `feat(config): add threshold YAML config for chain reasoning`

---

#### Task A5: SBL rule YAML

**Label:** skip-tdd

**Files owned (exclusive to this task):**
- `software/server/config/rules/sbl.yaml`

**Depends on:** nothing

**Exact file contents (verbatim):**

`software/server/config/rules/sbl.yaml`:
```yaml
rules:
  - rule_id: sbl_knee_valgus_concern
    chain: superficial_back_line
    applies_to_movements: [overhead_squat, single_leg_squat]
    metric_key: mean_knee_valgus_deg
    aggregation: max
    threshold_concern_ref: knee_valgus_concern
    threshold_flag_ref: knee_valgus_flag
    involved_joints: [ankle, knee, hip]
    narrative_template: "Your knee tracking shows {value:.1f} degrees of inward movement — an opportunity to explore the ankle-to-hip body connection along the back line."
    confidence: 0.75
  - rule_id: sbl_trunk_lean_concern
    chain: superficial_back_line
    applies_to_movements: [overhead_squat]
    metric_key: mean_trunk_lean_deg
    aggregation: max
    threshold_concern_ref: trunk_lean_concern
    threshold_flag_ref: trunk_lean_flag
    involved_joints: [ankle, hip, spine]
    narrative_template: "Your trunk lean measured {value:.1f} degrees during the squat — the back-line chain from calves to spine may be an area to explore."
    confidence: 0.7
```

**Verification command:**
```
python -c "import yaml; yaml.safe_load(open('software/server/config/rules/sbl.yaml'))"
```

**Expected result:** runs clean (exit 0)

**Commit message:** `feat(config): add SBL rule definitions`

---

#### Task A6: BFL + FFL rule YAML

**Label:** skip-tdd

**Files owned (exclusive to this task):**
- `software/server/config/rules/bfl.yaml`
- `software/server/config/rules/ffl.yaml`

**Depends on:** nothing

**Exact file contents (verbatim):**

`software/server/config/rules/bfl.yaml`:
```yaml
rules:
  - rule_id: bfl_hip_drop_concern
    chain: back_functional_line
    applies_to_movements: [single_leg_squat]
    metric_key: mean_trunk_lean_deg
    aggregation: max
    threshold_concern_ref: hip_drop_concern
    threshold_flag_ref: hip_drop_flag
    involved_joints: [hip, contralateral_shoulder]
    narrative_template: "Your lateral trunk shift of {value:.1f} degrees suggests an opportunity to explore the lat-to-glute body connection."
    confidence: 0.7
```

`software/server/config/rules/ffl.yaml`:
```yaml
rules:
  - rule_id: ffl_trunk_shift_concern
    chain: front_functional_line
    applies_to_movements: [overhead_squat]
    metric_key: mean_trunk_lean_deg
    aggregation: max
    threshold_concern_ref: trunk_lean_concern
    threshold_flag_ref: trunk_lean_flag
    involved_joints: [contralateral_shoulder, hip, opposite_knee]
    narrative_template: "Your front-line movement pattern shows {value:.1f} degrees of trunk movement — exploring the pec-to-adductor connection may be helpful."
    confidence: 0.65
```

**Verification command:**
```
python -c "import yaml; yaml.safe_load(open('software/server/config/rules/bfl.yaml')); yaml.safe_load(open('software/server/config/rules/ffl.yaml'))"
```

**Expected result:** runs clean (exit 0)

**Commit message:** `feat(config): add BFL and FFL rule definitions`

---

#### Task B1: Threshold loader + body-type adjustment

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/reasoning/threshold_loader.py`
- `software/server/src/auralink/reasoning/thresholds.py` (MODIFIED — re-exports `ThresholdSetConfig` as `ThresholdSet`)
- `software/server/tests/unit/reasoning/test_threshold_loader.py`

**Depends on:** A2 (BodyTypeProfile), A3 (config schemas)

**Pre-step:** Subagent MUST first read `software/server/src/auralink/reasoning/thresholds.py` to see the current dataclass-based `ThresholdSet` + `DEFAULT_THRESHOLDS`. Replace that file's contents with a re-export from `config_schemas` so existing imports of `ThresholdSet` still work.

**Exact file contents (verbatim):**

`software/server/src/auralink/reasoning/thresholds.py`:
```python
"""Backwards-compatible re-exports. Canonical models live in config_schemas."""

from auralink.reasoning.config_schemas import ThresholdSetConfig as ThresholdSet

__all__ = ["ThresholdSet"]
```

`software/server/src/auralink/reasoning/threshold_loader.py`:
```python
from pathlib import Path

import yaml

from auralink.reasoning.body_type import BodyTypeProfile
from auralink.reasoning.config_schemas import (
    BodyTypeAdjustmentsConfig,
    ThresholdSetConfig,
)

_DEFAULT_PATH = Path(__file__).resolve().parents[3] / "config" / "thresholds" / "default.yaml"
_ADJUSTMENTS_PATH = Path(__file__).resolve().parents[3] / "config" / "thresholds" / "body_type_adjustments.yaml"


def load_default_thresholds(path: Path | None = None) -> ThresholdSetConfig:
    p = path or _DEFAULT_PATH
    raw = yaml.safe_load(p.read_text())
    return ThresholdSetConfig.model_validate(raw)


def load_body_type_adjustments(path: Path | None = None) -> BodyTypeAdjustmentsConfig:
    p = path or _ADJUSTMENTS_PATH
    raw = yaml.safe_load(p.read_text())
    return BodyTypeAdjustmentsConfig.model_validate(raw)


def adjust_for_body_type(
    base: ThresholdSetConfig,
    profile: BodyTypeProfile,
    adjustments: BodyTypeAdjustmentsConfig,
) -> ThresholdSetConfig:
    merged = base.model_dump()
    for adj in adjustments.adjustments:
        if adj.applies_to_sex and profile.sex.value not in adj.applies_to_sex:
            continue
        if adj.applies_to_hypermobile is not None and adj.applies_to_hypermobile != profile.hypermobile:
            continue
        if adj.applies_to_age_range and profile.age_range not in adj.applies_to_age_range:
            continue
        merged.update(adj.threshold_overrides)
    return ThresholdSetConfig.model_validate(merged)
```

**Test file:**

`software/server/tests/unit/reasoning/test_threshold_loader.py`:
```python
from pathlib import Path

import pytest

from auralink.reasoning.body_type import BodyTypeProfile
from auralink.reasoning.config_schemas import (
    BodyTypeAdjustmentsConfig,
    ThresholdSetConfig,
)
from auralink.reasoning.threshold_loader import (
    adjust_for_body_type,
    load_body_type_adjustments,
    load_default_thresholds,
)


@pytest.fixture
def default_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "default.yaml"
    p.write_text(
        "knee_valgus_concern: 8.0\n"
        "knee_valgus_flag: 12.0\n"
        "hip_drop_concern: 5.0\n"
        "hip_drop_flag: 10.0\n"
        "trunk_lean_concern: 6.0\n"
        "trunk_lean_flag: 10.0\n"
    )
    return p


@pytest.fixture
def adjustments_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "body_type_adjustments.yaml"
    p.write_text(
        "adjustments:\n"
        "  - applies_to_hypermobile: true\n"
        "    threshold_overrides:\n"
        "      knee_valgus_concern: 10.0\n"
        "      knee_valgus_flag: 15.0\n"
    )
    return p


def test_load_default_thresholds(default_yaml: Path):
    cfg = load_default_thresholds(default_yaml)
    assert isinstance(cfg, ThresholdSetConfig)
    assert cfg.knee_valgus_flag == 12.0


def test_load_body_type_adjustments(adjustments_yaml: Path):
    cfg = load_body_type_adjustments(adjustments_yaml)
    assert isinstance(cfg, BodyTypeAdjustmentsConfig)
    assert len(cfg.adjustments) == 1
    assert cfg.adjustments[0].applies_to_hypermobile is True


def test_adjust_for_body_type_hypermobile_overrides(
    default_yaml: Path, adjustments_yaml: Path
):
    base = load_default_thresholds(default_yaml)
    adjustments = load_body_type_adjustments(adjustments_yaml)
    profile = BodyTypeProfile(hypermobile=True)
    adjusted = adjust_for_body_type(base, profile, adjustments)
    assert adjusted.knee_valgus_concern == 10.0
    assert adjusted.knee_valgus_flag == 15.0
    assert adjusted.trunk_lean_concern == 6.0


def test_adjust_for_body_type_no_match_returns_base(
    default_yaml: Path, adjustments_yaml: Path
):
    base = load_default_thresholds(default_yaml)
    adjustments = load_body_type_adjustments(adjustments_yaml)
    profile = BodyTypeProfile(hypermobile=False)
    adjusted = adjust_for_body_type(base, profile, adjustments)
    assert adjusted.knee_valgus_concern == 8.0
    assert adjusted.knee_valgus_flag == 12.0
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/reasoning/test_threshold_loader.py -v`

**Expected result:** `4 passed`

**Commit message:** `feat(reasoning): add threshold YAML loader with body-type adjustment`

---

#### Task B2: Rule loader

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/reasoning/rule_loader.py`
- `software/server/tests/unit/reasoning/test_rule_loader.py`

**Depends on:** A3 (config schemas)

**Exact file contents (verbatim):**

`software/server/src/auralink/reasoning/rule_loader.py`:
```python
from pathlib import Path

import yaml
from pydantic import TypeAdapter

from auralink.reasoning.config_schemas import RuleConfig

_RULES_DIR = Path(__file__).resolve().parents[3] / "config" / "rules"

_RuleListAdapter = TypeAdapter(list[RuleConfig])


def load_rules(rules_dir: Path | None = None) -> list[RuleConfig]:
    d = rules_dir or _RULES_DIR
    all_rules: list[RuleConfig] = []
    seen_ids: set[str] = set()
    for yaml_path in sorted(d.glob("*.yaml")):
        raw = yaml.safe_load(yaml_path.read_text())
        rules = _RuleListAdapter.validate_python(raw["rules"])
        for rule in rules:
            if rule.rule_id in seen_ids:
                raise ValueError(
                    f"duplicate rule_id {rule.rule_id!r} found in {yaml_path.name}"
                )
            seen_ids.add(rule.rule_id)
        all_rules.extend(rules)
    return all_rules
```

**Test file:**

`software/server/tests/unit/reasoning/test_rule_loader.py`:
```python
from pathlib import Path

import pytest
from pydantic import ValidationError

from auralink.reasoning.rule_loader import load_rules


def _write_rule_file(path: Path, rule_id: str, chain: str) -> None:
    path.write_text(
        "rules:\n"
        f"  - rule_id: {rule_id}\n"
        f"    chain: {chain}\n"
        "    applies_to_movements: [overhead_squat]\n"
        "    metric_key: mean_knee_valgus_deg\n"
        "    aggregation: max\n"
        "    threshold_concern_ref: knee_valgus_concern\n"
        "    threshold_flag_ref: knee_valgus_flag\n"
        "    involved_joints: [knee]\n"
        '    narrative_template: "value {value:.1f}"\n'
        "    confidence: 0.8\n"
    )


def test_loads_multi_file_rules_directory(tmp_path: Path):
    _write_rule_file(tmp_path / "sbl.yaml", "sbl_x", "superficial_back_line")
    _write_rule_file(tmp_path / "bfl.yaml", "bfl_y", "back_functional_line")
    rules = load_rules(tmp_path)
    rule_ids = {r.rule_id for r in rules}
    assert rule_ids == {"sbl_x", "bfl_y"}


def test_loads_sorts_files_alphabetically(tmp_path: Path):
    _write_rule_file(tmp_path / "z.yaml", "z_rule", "superficial_back_line")
    _write_rule_file(tmp_path / "a.yaml", "a_rule", "superficial_back_line")
    rules = load_rules(tmp_path)
    assert [r.rule_id for r in rules] == ["a_rule", "z_rule"]


def test_rejects_malformed_rule(tmp_path: Path):
    (tmp_path / "bad.yaml").write_text(
        "rules:\n"
        "  - rule_id: bad\n"
        "    chain: not_a_real_chain\n"
        "    applies_to_movements: [overhead_squat]\n"
        "    metric_key: mean_knee_valgus_deg\n"
        "    aggregation: max\n"
        "    threshold_concern_ref: x\n"
        "    threshold_flag_ref: y\n"
        '    narrative_template: "n"\n'
    )
    with pytest.raises(ValidationError):
        load_rules(tmp_path)


def test_rejects_duplicate_rule_id_across_files(tmp_path: Path):
    _write_rule_file(tmp_path / "sbl.yaml", "shared_id", "superficial_back_line")
    _write_rule_file(tmp_path / "bfl.yaml", "shared_id", "back_functional_line")
    with pytest.raises(ValueError, match="duplicate rule_id"):
        load_rules(tmp_path)
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/reasoning/test_rule_loader.py -v`

**Expected result:** `4 passed`

**Commit message:** `feat(reasoning): add rule YAML loader`

---

#### Task B3: Report schemas (with empty Plan-3 slots)

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/report/__init__.py`
- `software/server/src/auralink/report/schemas.py`
- `software/server/tests/unit/report/test_schemas.py`

**Depends on:** A1 (ChainObservation)

**Exact file contents (verbatim):**

`software/server/src/auralink/report/__init__.py`:
```python
```

`software/server/src/auralink/report/schemas.py`:
```python
from pydantic import BaseModel, Field

from auralink.pipeline.artifacts import (
    AngleTimeSeries,
    LiftedAngleTimeSeries,
    NormalizedAngleTimeSeries,
    PerRepMetrics,
    PhaseBoundaries,
    RepBoundaries,
    SessionQualityReport,
    SkeletonBundle,
    WithinMovementTrend,
)
from auralink.reasoning.observations import ChainObservation


class TemporalSection(BaseModel):
    """Placeholder slot — Plan 3 populates with DTW/temporal analysis."""


class CrossMovementSection(BaseModel):
    """Placeholder slot — Plan 3 populates with cross-movement aggregation."""


class ReportMetadata(BaseModel):
    session_id: str
    movement: str
    captured_at_ms: int | None = None


class MovementSection(BaseModel):
    movement: str
    quality_report: SessionQualityReport
    angle_series: AngleTimeSeries | None = None
    normalized_angle_series: NormalizedAngleTimeSeries | None = None
    rep_boundaries: RepBoundaries | None = None
    per_rep_metrics: PerRepMetrics | None = None
    within_movement_trend: WithinMovementTrend | None = None
    lift_result: LiftedAngleTimeSeries | None = None
    skeleton_result: SkeletonBundle | None = None
    phase_boundaries: PhaseBoundaries | None = None
    chain_observations: list[ChainObservation] = Field(default_factory=list)


class Report(BaseModel):
    metadata: ReportMetadata
    movement_section: MovementSection
    overall_narrative: str
    temporal_section: TemporalSection | None = None
    cross_movement_section: CrossMovementSection | None = None
```

**Design note — maximally inclusive MovementSection:** The section exposes every artifact field rather than pre-pruning. Rationale: Reports are a live view on top of artifacts, the phone client ignores fields it does not render, and downstream consumers (analytics, debug UIs, future DTW visualizations) get raw data without a separate endpoint. If payload size becomes a real issue we add a `?compact=true` query param at the endpoint boundary, not by narrowing the schema. Subagent must verify all imported symbols exist in `auralink.pipeline.artifacts` — if any name differs, STATUS: CHECKPOINT.

Note: the subagent must verify that `PerRepMetrics`, `PhaseBoundaries`, `SessionQualityReport`, `WithinMovementTrend`, `AngleTimeSeries`, `NormalizedAngleTimeSeries`, `RepBoundaries`, `LiftedAngleTimeSeries`, and `SkeletonBundle` are importable from `auralink.pipeline.artifacts`. If any name differs, report STATUS: CHECKPOINT.

**Test file:**

`software/server/tests/unit/report/test_schemas.py`:
```python
from auralink.pipeline.artifacts import SessionQualityReport
from auralink.report.schemas import (
    CrossMovementSection,
    MovementSection,
    Report,
    ReportMetadata,
    TemporalSection,
)


def _minimal_quality_report() -> SessionQualityReport:
    return SessionQualityReport.model_construct()


def test_temporal_section_instantiable():
    t = TemporalSection()
    assert t is not None


def test_cross_movement_section_instantiable():
    c = CrossMovementSection()
    assert c is not None


def test_report_round_trips():
    report = Report(
        metadata=ReportMetadata(session_id="s1", movement="overhead_squat"),
        movement_section=MovementSection(
            movement="overhead_squat",
            quality_report=_minimal_quality_report(),
        ),
        overall_narrative="Your movement shows a clean overall pattern.",
    )
    data = report.model_dump()
    restored = Report.model_validate(data)
    assert restored.metadata.session_id == "s1"
    assert restored.movement_section.movement == "overhead_squat"
```

Note: `SessionQualityReport.model_construct()` bypasses validation so tests do not need to fabricate the full internal structure. If `SessionQualityReport` requires fields at construction, subagent should adjust by passing minimal kwargs from the actual schema (read `pipeline/artifacts.py` first).

**Focused test command:** `cd software/server && uv run pytest tests/unit/report/test_schemas.py -v`

**Expected result:** `3 passed`

**Commit message:** `feat(report): add Report pydantic schema with Plan-3 slot stubs`

---

#### Task B4: Add chain_observations field to PipelineArtifacts

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/pipeline/artifacts.py`
- `software/server/tests/unit/pipeline/test_artifacts_chain_observations.py`

**Depends on:** A1 (ChainObservation)

**Rationale:** Split out from the original D1 bundle to eliminate a Wave D race condition. D1 (stage function) and D2 (assembler) both read the `chain_observations` field; if either task also mutates `artifacts.py` in parallel, they collide. B4 lands the field addition alone in Wave B so D1 and D2 can run safely in parallel.

**Edit to `software/server/src/auralink/pipeline/artifacts.py`:**

1. Add import (group with existing imports at the top of the file):
```python
from auralink.reasoning.observations import ChainObservation
```

2. Add a new optional field to `PipelineArtifacts` (group with the other `| None = None` fields):
```python
    chain_observations: list[ChainObservation] | None = None
```

Subagent must guard against circular import between `pipeline/artifacts.py` and `reasoning/observations.py`. Since `observations.py` only imports from `reasoning/chains.py`, the import should be safe — verify by running tests.

**Test file:**

`software/server/tests/unit/pipeline/test_artifacts_chain_observations.py`:
```python
from auralink.pipeline.artifacts import PipelineArtifacts
from auralink.reasoning.chains import ChainName
from auralink.reasoning.observations import ChainObservation, ObservationSeverity


def test_pipeline_artifacts_accepts_chain_observations():
    obs = ChainObservation(
        chain=ChainName.SBL,
        severity=ObservationSeverity.CONCERN,
        confidence=0.75,
        trigger_rule="sbl_rule",
        narrative="n",
    )
    artifacts = PipelineArtifacts.model_construct(chain_observations=[obs])
    data = artifacts.model_dump()
    restored = PipelineArtifacts.model_validate(data)
    assert restored.chain_observations is not None
    assert len(restored.chain_observations) == 1
    assert restored.chain_observations[0].trigger_rule == "sbl_rule"
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/pipeline/test_artifacts_chain_observations.py -v`

**Expected result:** `1 passed`

**Commit message:** `feat(pipeline): add chain_observations field to PipelineArtifacts`

---

#### Task C1: ChainReasoner protocol + RuleBasedChainReasoner

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/reasoning/rule_engine.py`
- `software/server/tests/unit/reasoning/test_rule_engine.py`

**Depends on:** A1 (observations), A2 (body_type), A3 (config_schemas), B1 (threshold_loader.adjust_for_body_type)

**Convention note:** Plan 4's `ml/` modules (loader.py, lifter.py, skeleton.py, phase_segmenter.py) put each Protocol and its default implementation in the SAME file. Plan 2 follows that convention — `ChainReasoner` Protocol and `RuleBasedChainReasoner` implementation live together in `rule_engine.py`. Do not create a separate `engine.py`.

**Exact file contents (verbatim):**

`software/server/src/auralink/reasoning/rule_engine.py`:
```python
from typing import Protocol

from auralink.pipeline.artifacts import PerRepMetrics
from auralink.reasoning.body_type import BodyTypeProfile
from auralink.reasoning.config_schemas import (
    BodyTypeAdjustmentsConfig,
    RuleConfig,
    ThresholdSetConfig,
)
from auralink.reasoning.observations import ChainObservation, ObservationSeverity
from auralink.reasoning.threshold_loader import adjust_for_body_type


class ChainReasoner(Protocol):
    def reason(
        self,
        per_rep_metrics: PerRepMetrics | None,
        movement: str,
        body_type: BodyTypeProfile | None = None,
    ) -> list[ChainObservation]: ...


def _aggregate(values: list[float], aggregation: str) -> float:
    if not values:
        return 0.0
    if aggregation == "max":
        return max(values)
    if aggregation == "min":
        return min(values)
    if aggregation == "mean":
        return sum(values) / len(values)
    raise ValueError(f"unknown aggregation: {aggregation}")


def _extract_metric(metrics: PerRepMetrics, metric_key: str) -> list[float]:
    return [getattr(rep, metric_key) for rep in metrics.reps]


class RuleBasedChainReasoner:
    def __init__(
        self,
        rules: list[RuleConfig],
        base_thresholds: ThresholdSetConfig,
        adjustments: BodyTypeAdjustmentsConfig,
    ) -> None:
        self._rules = rules
        self._base = base_thresholds
        self._adjustments = adjustments

    def reason(
        self,
        per_rep_metrics: PerRepMetrics | None,
        movement: str,
        body_type: BodyTypeProfile | None = None,
    ) -> list[ChainObservation]:
        if per_rep_metrics is None:
            return []
        thresholds = self._base
        if body_type is not None:
            thresholds = adjust_for_body_type(self._base, body_type, self._adjustments)
        threshold_dict = thresholds.model_dump()
        observations: list[ChainObservation] = []
        for rule in self._rules:
            if movement not in rule.applies_to_movements:
                continue
            values = _extract_metric(per_rep_metrics, rule.metric_key)
            if not values:
                continue
            aggregated = _aggregate(values, rule.aggregation)
            concern = threshold_dict.get(rule.threshold_concern_ref)
            flag = threshold_dict.get(rule.threshold_flag_ref)
            if concern is None or flag is None:
                continue
            severity: ObservationSeverity | None = None
            if aggregated >= flag:
                severity = ObservationSeverity.FLAG
            elif aggregated >= concern:
                severity = ObservationSeverity.CONCERN
            if severity is None:
                continue
            narrative = rule.narrative_template.format(value=aggregated)
            observations.append(
                ChainObservation(
                    chain=rule.chain,
                    severity=severity,
                    confidence=rule.confidence,
                    trigger_rule=rule.rule_id,
                    involved_joints=rule.involved_joints,
                    evidence={rule.metric_key: aggregated},
                    narrative=narrative,
                )
            )
        return observations
```

**Test file:**

`software/server/tests/unit/reasoning/test_rule_engine.py`:
```python
import pytest

from auralink.pipeline.artifacts import PerRepMetrics, RepMetric
from auralink.reasoning.body_type import BodyTypeProfile
from auralink.reasoning.chains import ChainName
from auralink.reasoning.config_schemas import (
    BodyTypeAdjustment,
    BodyTypeAdjustmentsConfig,
    RuleConfig,
    ThresholdSetConfig,
)
from auralink.reasoning.observations import ObservationSeverity
from auralink.reasoning.rule_engine import RuleBasedChainReasoner


def _rep(valgus: float = 0.0, trunk_lean: float = 0.0) -> RepMetric:
    return RepMetric(
        rep_index=0,
        amplitude_deg=90.0,
        peak_velocity_deg_per_s=180.0,
        rom_deg=90.0,
        mean_trunk_lean_deg=trunk_lean,
        mean_knee_valgus_deg=valgus,
    )


def _per_rep(reps: list[RepMetric]) -> PerRepMetrics:
    return PerRepMetrics(primary_angle="knee_flexion", reps=reps)


def _thresholds() -> ThresholdSetConfig:
    return ThresholdSetConfig(
        knee_valgus_concern=8.0,
        knee_valgus_flag=12.0,
        hip_drop_concern=5.0,
        hip_drop_flag=10.0,
        trunk_lean_concern=6.0,
        trunk_lean_flag=10.0,
    )


def _valgus_rule() -> RuleConfig:
    return RuleConfig(
        rule_id="sbl_knee_valgus_concern",
        chain=ChainName.SBL,
        applies_to_movements=["overhead_squat"],
        metric_key="mean_knee_valgus_deg",
        aggregation="max",
        threshold_concern_ref="knee_valgus_concern",
        threshold_flag_ref="knee_valgus_flag",
        involved_joints=["ankle", "knee", "hip"],
        narrative_template="knee valgus {value:.1f}",
        confidence=0.75,
    )


def test_returns_empty_when_per_rep_metrics_is_none():
    reasoner = RuleBasedChainReasoner(
        rules=[_valgus_rule()],
        base_thresholds=_thresholds(),
        adjustments=BodyTypeAdjustmentsConfig(),
    )
    assert reasoner.reason(None, "overhead_squat") == []


def test_rule_fires_at_concern_severity():
    per_rep = _per_rep([_rep(valgus=9.5)])
    reasoner = RuleBasedChainReasoner(
        rules=[_valgus_rule()],
        base_thresholds=_thresholds(),
        adjustments=BodyTypeAdjustmentsConfig(),
    )
    obs = reasoner.reason(per_rep, "overhead_squat")
    assert len(obs) == 1
    assert obs[0].severity == ObservationSeverity.CONCERN
    assert obs[0].chain == ChainName.SBL


def test_rule_fires_at_flag_severity():
    per_rep = _per_rep([_rep(valgus=13.0)])
    reasoner = RuleBasedChainReasoner(
        rules=[_valgus_rule()],
        base_thresholds=_thresholds(),
        adjustments=BodyTypeAdjustmentsConfig(),
    )
    obs = reasoner.reason(per_rep, "overhead_squat")
    assert len(obs) == 1
    assert obs[0].severity == ObservationSeverity.FLAG


def test_rule_skipped_when_movement_does_not_match():
    per_rep = _per_rep([_rep(valgus=13.0)])
    reasoner = RuleBasedChainReasoner(
        rules=[_valgus_rule()],
        base_thresholds=_thresholds(),
        adjustments=BodyTypeAdjustmentsConfig(),
    )
    assert reasoner.reason(per_rep, "push_up") == []


def test_body_type_adjustment_raises_threshold_so_rule_does_not_fire():
    per_rep = _per_rep([_rep(valgus=9.5)])
    adjustments = BodyTypeAdjustmentsConfig(
        adjustments=[
            BodyTypeAdjustment(
                applies_to_hypermobile=True,
                threshold_overrides={
                    "knee_valgus_concern": 10.0,
                    "knee_valgus_flag": 15.0,
                },
            )
        ]
    )
    reasoner = RuleBasedChainReasoner(
        rules=[_valgus_rule()],
        base_thresholds=_thresholds(),
        adjustments=adjustments,
    )
    profile = BodyTypeProfile(hypermobile=True)
    assert reasoner.reason(per_rep, "overhead_squat", body_type=profile) == []


def test_narrative_template_formats_value():
    per_rep = _per_rep([_rep(valgus=9.5)])
    reasoner = RuleBasedChainReasoner(
        rules=[_valgus_rule()],
        base_thresholds=_thresholds(),
        adjustments=BodyTypeAdjustmentsConfig(),
    )
    obs = reasoner.reason(per_rep, "overhead_squat")
    assert obs[0].narrative == "knee valgus 9.5"
```

Note: `PerRepMetrics` and `RepMetric` field names (`rep_index`, `amplitude_deg`, `peak_velocity_deg_per_s`, `rom_deg`, `mean_trunk_lean_deg`, `mean_knee_valgus_deg`) are the contract this plan was written against — verified against `pipeline/artifacts.py` at plan time.

**Focused test command:** `cd software/server && uv run pytest tests/unit/reasoning/test_rule_engine.py -v`

**Expected result:** `6 passed`

**Commit message:** `feat(reasoning): add RuleBasedChainReasoner rule-evaluation engine`

---

#### Task D1: run_chain_reasoning stage function

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/pipeline/stages/chain_reasoning.py`
- `software/server/src/auralink/pipeline/stages/base.py` (MODIFIED — add one constant)
- `software/server/tests/unit/pipeline/test_chain_reasoning_stage.py`

**Depends on:** A1 (observations), C1 (ChainReasoner protocol), B4 (chain_observations field)

**Ground truth (verified against code, not subject to improvisation):** The existing `Stage` in `software/server/src/auralink/pipeline/stages/base.py` is `@dataclass(frozen=True)` wrapping `run: Callable[[StageContext], Any]`. All existing stages (see `lift.py`, `normalize.py`, `per_rep_metrics.py`) are module-level functions of shape `run_xxx(ctx: StageContext, impl: Protocol | None = None) -> Artifact`. The chain reasoning stage MUST follow this convention — NO classes. `STAGE_NAME_*` constants live in `base.py`, not in individual stage modules.

**Edit to `software/server/src/auralink/pipeline/stages/base.py`:**

Add a new constant directly after the existing `STAGE_NAME_PHASE_SEGMENT = "phase_segment"` line (currently line 33):
```python
STAGE_NAME_CHAIN_REASONING = "chain_reasoning"
```

**Exact file contents (verbatim):**

`software/server/src/auralink/pipeline/stages/chain_reasoning.py`:
```python
from auralink.pipeline.stages.base import (
    STAGE_NAME_CHAIN_REASONING,
    STAGE_NAME_PER_REP_METRICS,
    StageContext,
)
from auralink.reasoning.observations import ChainObservation
from auralink.reasoning.rule_engine import ChainReasoner, RuleBasedChainReasoner
from auralink.reasoning.rule_loader import load_rules
from auralink.reasoning.threshold_loader import (
    load_body_type_adjustments,
    load_default_thresholds,
)


def _build_default_reasoner() -> RuleBasedChainReasoner:
    return RuleBasedChainReasoner(
        rules=load_rules(),
        base_thresholds=load_default_thresholds(),
        adjustments=load_body_type_adjustments(),
    )


_default_reasoner: ChainReasoner = _build_default_reasoner()


def run_chain_reasoning(
    ctx: StageContext,
    reasoner: ChainReasoner | None = None,
) -> list[ChainObservation]:
    """Apply rule-based chain reasoning over per-rep metrics.

    Reads PerRepMetrics from the prior stage and returns a list of
    ChainObservations. Returns an empty list if per_rep_metrics is missing
    (push_up stops at skeleton; rollup uses phase_segment instead of reps).
    """
    impl = reasoner if reasoner is not None else _default_reasoner
    per_rep = ctx.artifacts.get(STAGE_NAME_PER_REP_METRICS)
    return impl.reason(
        per_rep,
        ctx.session.metadata.movement,
        body_type=None,
    )
```

Note: `STAGE_NAME_CHAIN_REASONING` is imported from `base.py` (where D1 also adds it); it is NOT defined in this file. This matches the existing convention (see `lift.py` importing `STAGE_NAME_NORMALIZE` from `base.py`).

**Test file:**

`software/server/tests/unit/pipeline/test_chain_reasoning_stage.py`:
```python
from datetime import UTC, datetime

from auralink.api.schemas import Session, SessionMetadata
from auralink.pipeline.stages.base import STAGE_NAME_PER_REP_METRICS, StageContext
from auralink.pipeline.stages.chain_reasoning import run_chain_reasoning
from auralink.reasoning.chains import ChainName
from auralink.reasoning.observations import ChainObservation, ObservationSeverity


class _FakeReasoner:
    def __init__(self, observations: list[ChainObservation]):
        self._observations = observations
        self.calls: list[tuple] = []

    def reason(self, per_rep_metrics, movement, body_type=None):
        self.calls.append((per_rep_metrics, movement, body_type))
        return list(self._observations)


def _ctx(movement: str = "overhead_squat") -> StageContext:
    session = Session(
        metadata=SessionMetadata(
            movement=movement,
            device="test",
            model="test",
            frame_rate=30.0,
            captured_at=datetime.now(UTC),
        ),
        frames=[],
    )
    return StageContext(session=session)


def test_run_chain_reasoning_returns_empty_when_per_rep_missing():
    ctx = _ctx()
    fake = _FakeReasoner([])
    result = run_chain_reasoning(ctx, reasoner=fake)
    assert result == []
    assert fake.calls == [(None, "overhead_squat", None)]


def test_run_chain_reasoning_passes_movement_and_per_rep_to_reasoner():
    ctx = _ctx(movement="single_leg_squat")
    ctx.artifacts[STAGE_NAME_PER_REP_METRICS] = "sentinel-per-rep"
    fake = _FakeReasoner([])
    run_chain_reasoning(ctx, reasoner=fake)
    assert fake.calls == [("sentinel-per-rep", "single_leg_squat", None)]


def test_run_chain_reasoning_returns_reasoner_observations_unchanged():
    obs_a = ChainObservation(
        chain=ChainName.SBL,
        severity=ObservationSeverity.CONCERN,
        confidence=0.8,
        trigger_rule="sbl_a",
        narrative="a",
    )
    obs_b = ChainObservation(
        chain=ChainName.BFL,
        severity=ObservationSeverity.FLAG,
        confidence=0.7,
        trigger_rule="bfl_b",
        narrative="b",
    )
    ctx = _ctx()
    ctx.artifacts[STAGE_NAME_PER_REP_METRICS] = "x"
    fake = _FakeReasoner([obs_a, obs_b])
    result = run_chain_reasoning(ctx, reasoner=fake)
    assert result == [obs_a, obs_b]
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/pipeline/test_chain_reasoning_stage.py -v`

**Expected result:** `3 passed`

**Commit message:** `feat(pipeline): add run_chain_reasoning stage function`

---

#### Task D2: Report assembler

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/report/assembler.py`
- `software/server/tests/unit/report/test_assembler.py`

**Depends on:** A1 (observations), B3 (Report schemas)

**Exact file contents (verbatim):**

`software/server/src/auralink/report/assembler.py`:
```python
from auralink.pipeline.artifacts import PipelineArtifacts
from auralink.report.schemas import (
    MovementSection,
    Report,
    ReportMetadata,
)


def _build_overall_narrative(section: MovementSection) -> str:
    if not section.quality_report.passed:
        return (
            "We could not generate a complete movement read from this session. "
            "See the quality report for details on what to adjust for the next capture."
        )
    obs = section.chain_observations
    if not obs:
        return "Your movement shows a clean overall pattern — no notable compensations detected."
    flagged = [o for o in obs if o.severity.value == "flag"]
    concern = [o for o in obs if o.severity.value == "concern"]
    parts: list[str] = []
    if flagged:
        parts.append(f"Your movement shows {len(flagged)} notable pattern(s) worth exploring further.")
    if concern:
        parts.append(f"There are {len(concern)} area(s) of early-stage variation in your body connections.")
    return " ".join(parts)


def assemble_report(
    artifacts: PipelineArtifacts,
    session_id: str,
    movement: str,
    captured_at_ms: int | None = None,
) -> Report:
    movement_section = MovementSection(
        movement=movement,
        quality_report=artifacts.quality_report,
        angle_series=artifacts.angle_series,
        normalized_angle_series=artifacts.normalized_angle_series,
        rep_boundaries=artifacts.rep_boundaries,
        per_rep_metrics=artifacts.per_rep_metrics,
        within_movement_trend=artifacts.within_movement_trend,
        lift_result=artifacts.lift_result,
        skeleton_result=artifacts.skeleton_result,
        phase_boundaries=artifacts.phase_boundaries,
        chain_observations=artifacts.chain_observations or [],
    )
    return Report(
        metadata=ReportMetadata(
            session_id=session_id,
            movement=movement,
            captured_at_ms=captured_at_ms,
        ),
        movement_section=movement_section,
        overall_narrative=_build_overall_narrative(movement_section),
    )
```

**Test file:**

`software/server/tests/unit/report/test_assembler.py`:
```python
from auralink.pipeline.artifacts import PipelineArtifacts, SessionQualityReport
from auralink.reasoning.chains import ChainName
from auralink.reasoning.observations import ChainObservation, ObservationSeverity
from auralink.report.assembler import assemble_report


def _artifacts(chain_observations=None) -> PipelineArtifacts:
    return PipelineArtifacts.model_construct(
        quality_report=SessionQualityReport.model_construct(),
        chain_observations=chain_observations,
    )


def _flag_obs() -> ChainObservation:
    return ChainObservation(
        chain=ChainName.SBL,
        severity=ObservationSeverity.FLAG,
        confidence=0.8,
        trigger_rule="sbl_flag",
        narrative="n",
    )


def _concern_obs() -> ChainObservation:
    return ChainObservation(
        chain=ChainName.BFL,
        severity=ObservationSeverity.CONCERN,
        confidence=0.7,
        trigger_rule="bfl_concern",
        narrative="n",
    )


def test_assemble_with_no_observations_produces_clean_narrative():
    report = assemble_report(
        artifacts=_artifacts([]),
        session_id="s1",
        movement="overhead_squat",
    )
    assert "clean overall pattern" in report.overall_narrative
    assert report.movement_section.chain_observations == []


def test_assemble_with_one_flag_observation():
    report = assemble_report(
        artifacts=_artifacts([_flag_obs()]),
        session_id="s1",
        movement="overhead_squat",
    )
    assert "notable pattern" in report.overall_narrative
    assert len(report.movement_section.chain_observations) == 1


def test_assemble_copies_artifacts_fields_into_movement_section():
    artifacts = _artifacts([])
    report = assemble_report(
        artifacts=artifacts,
        session_id="s1",
        movement="overhead_squat",
        captured_at_ms=1234,
    )
    assert report.metadata.session_id == "s1"
    assert report.metadata.movement == "overhead_squat"
    assert report.metadata.captured_at_ms == 1234
    assert report.movement_section.movement == "overhead_squat"


def test_assemble_with_concern_and_flag_produces_compound_narrative():
    report = assemble_report(
        artifacts=_artifacts([_flag_obs(), _concern_obs()]),
        session_id="s1",
        movement="overhead_squat",
    )
    assert "notable pattern" in report.overall_narrative
    assert "early-stage variation" in report.overall_narrative
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/report/test_assembler.py -v`

**Expected result:** `4 passed`

**Commit message:** `feat(report): add report assembler with wellness-positioned narrative`

---

#### Task E1: Orchestrator wiring — chain_reasoning stage appended to default + push_up lists

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/pipeline/orchestrator.py` (MODIFIED)
- `software/server/tests/unit/pipeline/test_orchestrator_chain_wiring.py`

**Depends on:** D1 (run_chain_reasoning), B1 (threshold_loader), B2 (rule_loader), B4 (chain_observations field)

**Ground truth (verified, not subject to improvisation):** `_default_stage_list`, `_push_up_stage_list`, `_rollup_stage_list`, and `_assemble_artifacts` are private module-level functions in `orchestrator.py`. Each list builds `Stage(name=..., run=run_xxx)` from imported module-level stage functions. `_assemble_artifacts(ctx)` is hard-coded: it reads `ctx.artifacts.get(STAGE_NAME_X)` for every output field of `PipelineArtifacts`. Adding a new artifact field REQUIRES extending `_assemble_artifacts` — it does not auto-populate. The default reasoner lives in `stages/chain_reasoning.py` as a module-level singleton (D1); no factories, closures, or global caches live in `orchestrator.py`.

**Implementation steps:**

1. Extend the base.py import block to include `STAGE_NAME_CHAIN_REASONING`:
```python
from auralink.pipeline.stages.base import (
    STAGE_NAME_ANGLE_SERIES,
    STAGE_NAME_CHAIN_REASONING,
    STAGE_NAME_LIFT,
    STAGE_NAME_NORMALIZE,
    STAGE_NAME_PER_REP_METRICS,
    STAGE_NAME_PHASE_SEGMENT,
    STAGE_NAME_QUALITY_GATE,
    STAGE_NAME_REP_SEGMENT,
    STAGE_NAME_SKELETON,
    STAGE_NAME_WITHIN_MOVEMENT_TREND,
    Stage,
    StageContext,
)
```

2. Add a new stage import alongside the other `run_xxx` imports:
```python
from auralink.pipeline.stages.chain_reasoning import run_chain_reasoning
```

3. Append a chain-reasoning stage at the END of `_default_stage_list()` (after the `STAGE_NAME_WITHIN_MOVEMENT_TREND` line):
```python
        Stage(name=STAGE_NAME_CHAIN_REASONING, run=run_chain_reasoning),
```

4. Append the same line at the END of `_push_up_stage_list()` (after the `STAGE_NAME_SKELETON` line).

5. Do NOT modify `_rollup_stage_list()` — rollup skips chain reasoning because it has no per-rep metrics.

6. **Update `_assemble_artifacts()`** — add one new kwarg AFTER the existing `phase_boundaries=...` line:
```python
        chain_observations=ctx.artifacts.get(STAGE_NAME_CHAIN_REASONING),
```

**Test file:**

`software/server/tests/unit/pipeline/test_orchestrator_chain_wiring.py`:
```python
from unittest.mock import patch

from auralink.pipeline.orchestrator import (
    _assemble_artifacts,
    _default_stage_list,
    _push_up_stage_list,
    _rollup_stage_list,
)
from auralink.pipeline.stages.base import (
    STAGE_NAME_CHAIN_REASONING,
    STAGE_NAME_QUALITY_GATE,
    StageContext,
)


def _stage_names(stages) -> list[str]:
    return [s.name for s in stages]


def test_default_stage_list_ends_with_chain_reasoning():
    names = _stage_names(_default_stage_list())
    assert "chain_reasoning" in names
    assert names[-1] == "chain_reasoning"


def test_push_up_stage_list_ends_with_chain_reasoning():
    names = _stage_names(_push_up_stage_list())
    assert "chain_reasoning" in names
    assert names[-1] == "chain_reasoning"


def test_rollup_stage_list_does_not_contain_chain_reasoning():
    names = _stage_names(_rollup_stage_list())
    assert "chain_reasoning" not in names


def test_assemble_artifacts_populates_chain_observations():
    """_assemble_artifacts must copy chain_reasoning stage output onto PipelineArtifacts."""
    class _FakeSession:
        class metadata:
            movement = "overhead_squat"

    ctx = StageContext.__new__(StageContext)
    ctx.session = _FakeSession()
    ctx.artifacts = {
        STAGE_NAME_QUALITY_GATE: object(),
        STAGE_NAME_CHAIN_REASONING: ["sentinel-observation"],
    }
    ctx.config = {}

    with patch("auralink.pipeline.orchestrator.PipelineArtifacts") as fake_pa:
        _assemble_artifacts(ctx)
        kwargs = fake_pa.call_args.kwargs
        assert kwargs["chain_observations"] == ["sentinel-observation"]
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/pipeline/test_orchestrator_chain_wiring.py -v`

**Expected result:** `4 passed`

**Commit message:** `feat(pipeline): wire run_chain_reasoning into default + push_up stage lists`

---

#### Task E2: Update GET /sessions/{id}/report to return Report

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/src/auralink/api/routes/reports.py` (MODIFIED)
- `software/server/tests/unit/api/test_reports_route.py`

**Depends on:** D2 (assemble_report)

**Ground truth (verified, not subject to improvisation):** `SessionStorage` exposes `save`, `load(session_id) -> Session`, `save_artifacts`, and `load_artifacts(session_id) -> PipelineArtifacts`. There is NO `load_session` method — use `storage.load()`. `SessionMetadata.captured_at` is a `datetime` (see `api/schemas.py:48`) — there is NO `captured_at_ms` field. Convert via `int(session.metadata.captured_at.timestamp() * 1000)`.

**Exact file contents (verbatim):**

`software/server/src/auralink/api/routes/reports.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status

from auralink.config import Settings, get_settings
from auralink.pipeline.storage import SessionStorage
from auralink.report.assembler import assemble_report
from auralink.report.schemas import Report

router = APIRouter(prefix="/sessions", tags=["reports"])


def _get_storage(settings: Settings = Depends(get_settings)) -> SessionStorage:
    return SessionStorage(base_dir=settings.sessions_dir)


@router.get("/{session_id}/report", response_model=Report)
def get_report(
    session_id: str,
    storage: SessionStorage = Depends(_get_storage),
) -> Report:
    try:
        artifacts = storage.load_artifacts(session_id)
        session = storage.load(session_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no report for session {session_id}",
        ) from exc

    captured_at_ms = int(session.metadata.captured_at.timestamp() * 1000)
    return assemble_report(
        artifacts=artifacts,
        session_id=session_id,
        movement=session.metadata.movement,
        captured_at_ms=captured_at_ms,
    )
```

**Test file:**

`software/server/tests/unit/api/test_reports_route.py`:
```python
from fastapi.testclient import TestClient

from auralink.api.app import create_app


def test_get_report_returns_404_for_missing_session(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_SESSIONS_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)
    response = client.get("/sessions/does-not-exist/report")
    assert response.status_code == 404
```

Note: a full end-to-end fixture → POST → GET test lives in F1 (`tests/integration/test_full_report.py`). E2 intentionally keeps only the route-level 404 test to avoid duplicating F1's coverage.

**Focused test command:** `cd software/server && uv run pytest tests/unit/api/test_reports_route.py -v`

**Expected result:** `1 passed`

**Commit message:** `feat(api): GET /sessions/{id}/report returns structured Report`

---

#### Task F1: Integration test — fixture → full report

**Label:** TDD (integration)

**Files owned (exclusive to this task):**
- `software/server/tests/integration/test_full_report.py`

**Depends on:** E1 (orchestrator wiring), E2 (reports route)

**Test file:**

`software/server/tests/integration/test_full_report.py`:
```python
from fastapi.testclient import TestClient

from auralink.api.app import create_app
from tests.fixtures.loader import load_fixture


def test_overhead_squat_valgus_produces_sbl_observation(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_SESSIONS_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    session = load_fixture("overhead_squat", variant="valgus")
    post = client.post("/sessions", json=session.model_dump(mode="json"))
    assert post.status_code in (200, 201)
    session_id = post.json()["session_id"]

    report = client.get(f"/sessions/{session_id}/report")
    assert report.status_code == 200
    body = report.json()
    observations = body["movement_section"]["chain_observations"]
    sbl_obs = [
        o
        for o in observations
        if o["chain"] == "superficial_back_line"
        and o["severity"] in {"concern", "flag"}
    ]
    assert len(sbl_obs) >= 1, (
        f"expected at least one SBL concern/flag observation, got {observations}"
    )


def test_overhead_squat_clean_produces_no_observations(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_SESSIONS_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    session = load_fixture("overhead_squat", variant="clean")
    post = client.post("/sessions", json=session.model_dump(mode="json"))
    assert post.status_code in (200, 201)
    session_id = post.json()["session_id"]

    report = client.get(f"/sessions/{session_id}/report")
    assert report.status_code == 200
    body = report.json()
    assert body["movement_section"]["chain_observations"] == []
    assert "clean overall pattern" in body["overall_narrative"]


def test_single_leg_squat_clean_runs_end_to_end_with_bfl_rule_loaded(tmp_path, monkeypatch):
    """BFL rule coverage — single_leg_squat is the movement the BFL rule applies to.

    Note: the synthetic `single_leg_squat_clean` fixture does not inject a
    compensation, so it may or may not produce an observation depending on
    baseline pose values. The assertion is structural: a successful e2e run
    with BFL rules loaded, no 5xx, and either 0 observations or any
    observation that (if present) belongs to a recognized chain.
    """
    monkeypatch.setenv("AURALINK_SESSIONS_DIR", str(tmp_path))
    app = create_app()
    client = TestClient(app)

    session = load_fixture("single_leg_squat", variant="clean")
    post = client.post("/sessions", json=session.model_dump(mode="json"))
    assert post.status_code in (200, 201)
    session_id = post.json()["session_id"]

    report = client.get(f"/sessions/{session_id}/report")
    assert report.status_code == 200
    body = report.json()
    assert body["movement_section"]["movement"] == "single_leg_squat"
    recognized_chains = {
        "superficial_back_line",
        "back_functional_line",
        "front_functional_line",
    }
    for obs in body["movement_section"]["chain_observations"]:
        assert obs["chain"] in recognized_chains
```

**Focused test command:** `cd software/server && uv run pytest tests/integration/test_full_report.py -v`

**Expected result:** `3 passed`

**Commit message:** `test(integration): end-to-end report generation from synthetic fixtures`

---

#### Task F2: Wellness language lint test

**Label:** TDD

**Files owned (exclusive to this task):**
- `software/server/tests/unit/reasoning/test_wellness_language.py`

**Depends on:** A5, A6 (rule YAML files must exist)

**Test file:**

`software/server/tests/unit/reasoning/test_wellness_language.py`:
```python
import re
from pathlib import Path

import yaml

_FORBIDDEN_TERMS = [
    "diagnosis",
    "dysfunction",
    "drivers of pain",
    "injury",
    "damage",
    "pathology",
]

_RULES_DIR = Path(__file__).resolve().parents[3] / "config" / "rules"


def test_no_forbidden_wellness_terms_in_rule_narratives():
    violations: list[str] = []
    for yaml_path in sorted(_RULES_DIR.glob("*.yaml")):
        data = yaml.safe_load(yaml_path.read_text())
        for rule in data.get("rules", []):
            narrative = rule.get("narrative_template", "")
            for term in _FORBIDDEN_TERMS:
                if re.search(rf"\b{re.escape(term)}\b", narrative, re.IGNORECASE):
                    violations.append(
                        f"{yaml_path.name}:{rule.get('rule_id')} contains forbidden term '{term}': {narrative!r}"
                    )
    assert not violations, "wellness-language violations:\n" + "\n".join(violations)
```

**Focused test command:** `cd software/server && uv run pytest tests/unit/reasoning/test_wellness_language.py -v`

**Expected result:** `1 passed`

**Commit message:** `test(reasoning): enforce wellness-language lint on rule narratives`

---

#### Task G1: Final validation (single-task wave)

**Label:** skip-tdd

**Files owned:** none (verification + optional lint cleanup commit)

**Depends on:** F1, F2 (all prior waves complete)

**Steps (execute in order):**

1. **Full test suite:**
   ```
   cd software/server && uv run pytest -q
   ```
   Expected: ~43 new tests on top of the 136 baseline (~179 total). All pass.

2. **Ruff auto-fix:**
   ```
   cd software/server && uv run ruff check . --fix
   cd software/server && uv run ruff check .
   ```
   Expected: final check exits clean (0 issues).

3. **Black format:**
   ```
   cd software/server && uv run black .
   cd software/server && uv run black --check .
   ```
   Expected: `--check` exits clean.

4. **Re-run full test suite:**
   ```
   cd software/server && uv run pytest -q
   ```
   Expected: same ~179 tests pass.

5. **Dev-server smoke test.** First write the smoke script to a temp file with NO list indentation (the heredoc terminator `PY` must be at column 0 or bash will not recognize it):

```
cat > /tmp/auralink_smoke.py <<'PY'
import json, urllib.request
from tests.fixtures.loader import load_fixture
session = load_fixture("overhead_squat", variant="valgus")
req = urllib.request.Request(
    "http://127.0.0.1:8765/sessions",
    data=session.model_dump_json().encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
session_id = json.loads(urllib.request.urlopen(req).read())["session_id"]
report = json.loads(urllib.request.urlopen(f"http://127.0.0.1:8765/sessions/{session_id}/report").read())
obs = report["movement_section"]["chain_observations"]
sbl = [o for o in obs if o["chain"] == "superficial_back_line" and o["severity"] in {"concern", "flag"}]
assert sbl, f"expected SBL observation, got {obs}"
print("SMOKE OK:", len(sbl), "SBL observation(s)")
PY
cd software/server && uv run uvicorn auralink.api.app:create_app --factory --port 8765 &
SERVER_PID=$!
sleep 2
cd software/server && uv run python /tmp/auralink_smoke.py
kill $SERVER_PID
```
   Expected: prints `SMOKE OK: N SBL observation(s)` where N >= 1. Server cleanly killed.

6. **If ruff/black changed anything, commit the cleanup:**
   ```
   git add -u software/server/
   git commit -m "chore(server): ruff/black cleanup after plan 2"
   ```
   Only commit files under `software/server/` — never `git add -A`.

**Expected result:** All five verification steps pass. If any step fails, subagent reports STATUS: FAILED with the failing step and the last 50 lines of output.

**Commit message (if cleanup needed):** `chore(server): ruff/black cleanup after plan 2`

---

## Plan Revision 2026-04-11 — Wave Structure

Wave groupings enforce parallelism and dependency barriers. Subagents within a wave run concurrently (max 6). Barriers between waves.

```
Wave 0 (1):           PRE1
Wave A (parallel, 6): A1, A2, A3, A4, A5, A6
Wave B (parallel, 4): B1, B2, B3, B4
Wave C (1):           C1
Wave D (parallel, 2): D1, D2
Wave E (parallel, 2): E1, E2
Wave F (parallel, 2): F1, F2
Wave G (1):           G1
```

### Task State (JSON)

```json
{
  "plan_id": "2026-04-10-L2-2-chain-reasoning",
  "waves": [
    {
      "wave": "0",
      "max_parallel": 1,
      "tasks": [
        {
          "id": "PRE1",
          "title": "Add pyyaml runtime dependency",
          "label": "skip-tdd",
          "files_owned": [
            "software/server/pyproject.toml"
          ],
          "depends_on": [],
          "expected_tests": 0,
          "commit_msg": "chore(deps): add pyyaml for chain reasoning config loaders"
        }
      ]
    },
    {
      "wave": "A",
      "max_parallel": 6,
      "tasks": [
        {
          "id": "A1",
          "title": "ChainObservation schema",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/reasoning/observations.py",
            "software/server/tests/unit/reasoning/test_observations.py"
          ],
          "depends_on": [],
          "expected_tests": 3,
          "commit_msg": "feat(reasoning): add ChainObservation pydantic schema"
        },
        {
          "id": "A2",
          "title": "BodyTypeProfile schema",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/reasoning/body_type.py",
            "software/server/tests/unit/reasoning/test_body_type.py"
          ],
          "depends_on": [],
          "expected_tests": 2,
          "commit_msg": "feat(reasoning): add BodyTypeProfile schema"
        },
        {
          "id": "A3",
          "title": "Config schemas (ThresholdSetConfig, BodyTypeAdjustment, RuleConfig)",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/reasoning/config_schemas.py",
            "software/server/tests/unit/reasoning/test_config_schemas.py"
          ],
          "depends_on": [],
          "expected_tests": 4,
          "commit_msg": "feat(reasoning): add pydantic config schemas for thresholds and rules"
        },
        {
          "id": "A4",
          "title": "Threshold YAML config files",
          "label": "skip-tdd",
          "files_owned": [
            "software/server/config/thresholds/default.yaml",
            "software/server/config/thresholds/body_type_adjustments.yaml"
          ],
          "depends_on": [],
          "expected_tests": 0,
          "commit_msg": "feat(config): add threshold YAML config for chain reasoning"
        },
        {
          "id": "A5",
          "title": "SBL rule YAML",
          "label": "skip-tdd",
          "files_owned": [
            "software/server/config/rules/sbl.yaml"
          ],
          "depends_on": [],
          "expected_tests": 0,
          "commit_msg": "feat(config): add SBL rule definitions"
        },
        {
          "id": "A6",
          "title": "BFL + FFL rule YAML",
          "label": "skip-tdd",
          "files_owned": [
            "software/server/config/rules/bfl.yaml",
            "software/server/config/rules/ffl.yaml"
          ],
          "depends_on": [],
          "expected_tests": 0,
          "commit_msg": "feat(config): add BFL and FFL rule definitions"
        }
      ]
    },
    {
      "wave": "B",
      "max_parallel": 4,
      "tasks": [
        {
          "id": "B1",
          "title": "Threshold loader + body-type adjustment",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/reasoning/threshold_loader.py",
            "software/server/src/auralink/reasoning/thresholds.py",
            "software/server/tests/unit/reasoning/test_threshold_loader.py"
          ],
          "depends_on": ["A2", "A3"],
          "expected_tests": 4,
          "commit_msg": "feat(reasoning): add threshold YAML loader with body-type adjustment"
        },
        {
          "id": "B2",
          "title": "Rule loader",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/reasoning/rule_loader.py",
            "software/server/tests/unit/reasoning/test_rule_loader.py"
          ],
          "depends_on": ["A3"],
          "expected_tests": 4,
          "commit_msg": "feat(reasoning): add rule YAML loader"
        },
        {
          "id": "B3",
          "title": "Report schemas (with empty Plan-3 slots)",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/report/__init__.py",
            "software/server/src/auralink/report/schemas.py",
            "software/server/tests/unit/report/test_schemas.py"
          ],
          "depends_on": ["A1"],
          "expected_tests": 3,
          "commit_msg": "feat(report): add Report pydantic schema with Plan-3 slot stubs"
        },
        {
          "id": "B4",
          "title": "Add chain_observations field to PipelineArtifacts",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/pipeline/artifacts.py",
            "software/server/tests/unit/pipeline/test_artifacts_chain_observations.py"
          ],
          "depends_on": ["A1"],
          "expected_tests": 1,
          "commit_msg": "feat(pipeline): add chain_observations field to PipelineArtifacts"
        }
      ]
    },
    {
      "wave": "C",
      "max_parallel": 1,
      "tasks": [
        {
          "id": "C1",
          "title": "ChainReasoner protocol + RuleBasedChainReasoner",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/reasoning/rule_engine.py",
            "software/server/tests/unit/reasoning/test_rule_engine.py"
          ],
          "depends_on": ["A1", "A2", "A3", "B1"],
          "expected_tests": 6,
          "commit_msg": "feat(reasoning): add RuleBasedChainReasoner rule-evaluation engine"
        }
      ]
    },
    {
      "wave": "D",
      "max_parallel": 2,
      "tasks": [
        {
          "id": "D1",
          "title": "run_chain_reasoning stage function",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/pipeline/stages/chain_reasoning.py",
            "software/server/src/auralink/pipeline/stages/base.py",
            "software/server/tests/unit/pipeline/test_chain_reasoning_stage.py"
          ],
          "depends_on": ["A1", "C1", "B4"],
          "expected_tests": 3,
          "commit_msg": "feat(pipeline): add run_chain_reasoning stage function"
        },
        {
          "id": "D2",
          "title": "Report assembler",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/report/assembler.py",
            "software/server/tests/unit/report/test_assembler.py"
          ],
          "depends_on": ["A1", "B3", "B4"],
          "expected_tests": 4,
          "commit_msg": "feat(report): add report assembler with wellness-positioned narrative"
        }
      ]
    },
    {
      "wave": "E",
      "max_parallel": 2,
      "tasks": [
        {
          "id": "E1",
          "title": "Orchestrator wiring — run_chain_reasoning + _assemble_artifacts update",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/pipeline/orchestrator.py",
            "software/server/tests/unit/pipeline/test_orchestrator_chain_wiring.py"
          ],
          "depends_on": ["B1", "B2", "B4", "D1"],
          "expected_tests": 4,
          "commit_msg": "feat(pipeline): wire run_chain_reasoning into default + push_up stage lists"
        },
        {
          "id": "E2",
          "title": "Update GET /sessions/{id}/report to return Report",
          "label": "TDD",
          "files_owned": [
            "software/server/src/auralink/api/routes/reports.py",
            "software/server/tests/unit/api/test_reports_route.py"
          ],
          "depends_on": ["D2"],
          "expected_tests": 1,
          "commit_msg": "feat(api): GET /sessions/{id}/report returns structured Report"
        }
      ]
    },
    {
      "wave": "F",
      "max_parallel": 2,
      "tasks": [
        {
          "id": "F1",
          "title": "Integration test — fixture → full report",
          "label": "TDD",
          "files_owned": [
            "software/server/tests/integration/test_full_report.py"
          ],
          "depends_on": ["E1", "E2"],
          "expected_tests": 3,
          "commit_msg": "test(integration): end-to-end report generation from synthetic fixtures"
        },
        {
          "id": "F2",
          "title": "Wellness language lint test",
          "label": "TDD",
          "files_owned": [
            "software/server/tests/unit/reasoning/test_wellness_language.py"
          ],
          "depends_on": ["A5", "A6"],
          "expected_tests": 1,
          "commit_msg": "test(reasoning): enforce wellness-language lint on rule narratives"
        }
      ]
    },
    {
      "wave": "G",
      "max_parallel": 1,
      "tasks": [
        {
          "id": "G1",
          "title": "Final validation",
          "label": "skip-tdd",
          "files_owned": [],
          "depends_on": ["F1", "F2"],
          "expected_tests": 0,
          "commit_msg": "chore(server): ruff/black cleanup after plan 2"
        }
      ]
    }
  ],
  "totals": {
    "tasks": 19,
    "waves": 8,
    "max_parallelism": 6,
    "expected_new_tests": 43
  }
}
```

Expected new test count breakdown: PRE1=0 + A1=3 + A2=2 + A3=4 + A4=0 + A5=0 + A6=0 + B1=4 + B2=4 + B3=3 + B4=1 + C1=6 + D1=3 + D2=4 + E1=4 + E2=1 + F1=3 + F2=1 + G1=0 = 43.

## Exit Criteria

- ~43 new tests pass (per task expected counts sum: 0+3+2+4+0+0+0+4+4+3+1+6+3+4+4+1+3+1 = 43).
- Synthetic `overhead_squat_valgus` fixture produces at least one SBL `ChainObservation` with severity `concern` or `flag`.
- Synthetic `overhead_squat_clean` fixture produces zero observations and the "clean overall pattern" narrative.
- Wellness language lint passes over all `config/rules/*.yaml` files.
- `ruff check` and `black --check` are clean.
- Dev-server smoke test passes end-to-end.
- `GET /sessions/{id}/report` returns the `Report` pydantic model (not raw `PipelineArtifacts`).

## Deferred & Cross-Cutting Concerns

### Scope deferred to later plans

- **`BodyTypeProfile` attachment to session ingest.** Plan 2 ships the pydantic schema, the `adjust_for_body_type()` mechanism, and unit tests for the adjustment logic. The `ChainReasoningStage` constructor accepts `body_type: BodyTypeProfile | None = None`; v1 orchestrator wiring passes `None`. Reason: the "where does the profile live" question is tangled up with user-model scope (see sEMG note below), and Plan 2 should not pin that decision prematurely. Plan 2 is the "mechanism exists, off by default" milestone.
- **DTW / temporal analysis** — Plan 3 populates `TemporalSection`.
- **Cross-movement aggregation** — Plan 3 populates `CrossMovementSection`.
- **LLM-generated narratives** — out of scope; all text is template-driven.

### Cross-cutting architectural choices worth documenting

- **Single-metric rule engine.** `RuleConfig.metric_key` is pinned to a single `PerRepMetrics` field per rule (`Literal["mean_knee_valgus_deg", "mean_trunk_lean_deg", "rom_deg", "peak_velocity_deg_per_s"]`). This is deliberate for v1 — pose-only data fits naturally into per-rep scalar metrics, and the simplicity is testable. **Known limitation:** rules cannot express multi-signal conditions like "high knee valgus AND high hamstring co-activation." When sEMG lands, this will need to evolve — either by widening `RuleConfig` to `conditions: list[Condition]` with a combinator, or by introducing a second reasoner that consumes a joint pose+EMG artifact bundle. The choice belongs in the sEMG integration epoch, not here.

- **BodyTypeProfile scope will shift from session-level to user-level when sEMG arrives.** Current mental model (v1): attach profile optionally to a session. Better mental model (post-sEMG): profile is a user-level attribute that calibrates both pose thresholds AND sEMG activation baselines, and is re-used across every session that user records. Plan 2 does not commit to either location — the profile is a standalone pydantic model with no session or user bindings, so future wiring can go either way.

- **Report is a view on artifacts, not a stored artifact.** Assembly runs on-demand in the endpoint. The canonical data lives in `PipelineArtifacts`; the `Report` shape is free to evolve without a backfill. If we ever need stored reports (e.g., for a mobile client that wants guaranteed historical consistency), add a cache layer behind the endpoint — don't move assembly into the pipeline.

- **Chain observations ARE stored** — they live on `PipelineArtifacts.chain_observations` because they are analytical output, not a presentation concern. Re-generating them would require re-running the reasoner and re-computing deterministic thresholds. Storing them is simpler and keeps the reasoner out of the read path.

- **MovementSection is intentionally maximally inclusive.** Every artifact field is exposed to the client. The phone renders what it needs and ignores the rest. Payload-size control is an endpoint-stage concern (future `?compact=true` query param), not a schema concern.
