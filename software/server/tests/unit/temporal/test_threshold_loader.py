from pathlib import Path

import pytest

from auralink.temporal.threshold_loader import (
    TemporalThresholds,
    load_temporal_thresholds,
)


def _write_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "thresholds.yaml"
    p.write_text(
        """
ncc_clean_min: 0.95
ncc_concern_min: 0.75
rom_deviation_concern_pct: 15.0
rom_deviation_flag_pct: 25.0
form_drift_ncc_slope_threshold: -0.02
form_drift_rom_mean_deviation_pct: 15.0
"""
    )
    return p


def test_loads_yaml_into_dataclass(tmp_path):
    p = _write_yaml(tmp_path)
    thresholds = load_temporal_thresholds(p)
    assert isinstance(thresholds, TemporalThresholds)
    assert thresholds.ncc_clean_min == 0.95
    assert thresholds.rom_deviation_flag_pct == 25.0
    assert thresholds.form_drift_ncc_slope_threshold == -0.02


def test_default_path_resolves_to_repo_config():
    thresholds = load_temporal_thresholds()
    assert isinstance(thresholds, TemporalThresholds)
    assert 0.0 < thresholds.ncc_concern_min < thresholds.ncc_clean_min <= 1.0


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_temporal_thresholds(tmp_path / "does_not_exist.yaml")
