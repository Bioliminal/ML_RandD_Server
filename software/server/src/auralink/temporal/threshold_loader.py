"""YAML loader for temporal analysis thresholds.

Mirrors the structure of reasoning/threshold_loader.py. Loaded once at
startup (from rep_comparison stage) and passed as an explicit argument into
compare_rep() / summarize_comparisons() so tests can inject overrides.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config" / "temporal"
_DEFAULT_PATH = _CONFIG_DIR / "thresholds.yaml"


class TemporalThresholds(BaseModel):
    """Thresholds used by the rep_comparison stage and within-movement summary.

    See config/temporal/thresholds.yaml for the canonical default values and
    their literature provenance.
    """

    ncc_clean_min: float = Field(gt=0.0, le=1.0)
    ncc_concern_min: float = Field(gt=0.0, le=1.0)
    rom_deviation_concern_pct: float = Field(gt=0.0)
    rom_deviation_flag_pct: float = Field(gt=0.0)
    form_drift_ncc_slope_threshold: float
    form_drift_rom_mean_deviation_pct: float = Field(gt=0.0)


def load_temporal_thresholds(path: Path | None = None) -> TemporalThresholds:
    """Read and validate the temporal thresholds YAML."""
    p = path or _DEFAULT_PATH
    if not p.exists():
        raise FileNotFoundError(f"temporal thresholds not found: {p}")
    raw = yaml.safe_load(p.read_text())
    return TemporalThresholds.model_validate(raw)
