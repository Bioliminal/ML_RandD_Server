from pathlib import Path

import pytest

from bioliminal.reasoning.body_type import BodyTypeProfile
from bioliminal.reasoning.config_schemas import (
    BodyTypeAdjustmentsConfig,
    ThresholdSetConfig,
)
from bioliminal.reasoning.threshold_loader import (
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


def test_adjust_for_body_type_hypermobile_overrides(default_yaml: Path, adjustments_yaml: Path):
    base = load_default_thresholds(default_yaml)
    adjustments = load_body_type_adjustments(adjustments_yaml)
    profile = BodyTypeProfile(hypermobile=True)
    adjusted = adjust_for_body_type(base, profile, adjustments)
    assert adjusted.knee_valgus_concern == 10.0
    assert adjusted.knee_valgus_flag == 15.0
    assert adjusted.trunk_lean_concern == 6.0


def test_adjust_for_body_type_no_match_returns_base(default_yaml: Path, adjustments_yaml: Path):
    base = load_default_thresholds(default_yaml)
    adjustments = load_body_type_adjustments(adjustments_yaml)
    profile = BodyTypeProfile(hypermobile=False)
    adjusted = adjust_for_body_type(base, profile, adjustments)
    assert adjusted.knee_valgus_concern == 8.0
    assert adjusted.knee_valgus_flag == 12.0
