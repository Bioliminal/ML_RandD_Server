"""Reference rep schema and JSON loader.

A ReferenceRep is a movement-specific canonical rep used as the DTW target
for per-rep comparisons. The on-disk format is JSON, one file per movement,
generated at build time by scripts/generate_reference_reps.py from the
shared synthetic generator (see docs/plans/2026-04-10-L2-3-dtw-temporal.md
architectural decision 6).

Runtime only reads JSON — it never imports from tests/fixtures.
"""

import json
from pathlib import Path

from pydantic import BaseModel, Field

_DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config" / "reference_reps"


class ReferenceRep(BaseModel):
    """A single canonical rep per movement, stored as normalized angle traces.

    `angles` mirrors NormalizedAngleTimeSeries.angles — dict[str, list[float]]
    keyed by the same joint-angle names (e.g., "left_knee_flexion",
    "trunk_lean", "left_knee_valgus", "right_knee_valgus").
    """

    movement: str
    angles: dict[str, list[float]] = Field(min_length=1)
    frame_rate: float = Field(gt=0.0)
    frames_per_rep: int = Field(gt=0)

    def angle_keys(self) -> set[str]:
        return set(self.angles.keys())


def load_reference_rep(movement: str, config_dir: Path | None = None) -> ReferenceRep:
    """Load the canonical reference rep for a movement.

    Parameters
    ----------
    movement : str
        Movement identifier; must match a generated file name stem.
    config_dir : Path | None
        Optional override; defaults to software/server/config/reference_reps.

    Raises
    ------
    FileNotFoundError : if no JSON file exists for that movement.
    pydantic.ValidationError : if the file is present but malformed.
    """
    base = config_dir if config_dir is not None else _DEFAULT_CONFIG_DIR
    path = base / f"{movement}.json"
    if not path.exists():
        raise FileNotFoundError(f"reference rep not found: {path}")
    raw = json.loads(path.read_text())
    return ReferenceRep.model_validate(raw)
