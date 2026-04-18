"""Fixture loader — discovers synthetic + golden captures by filename pattern.

Pattern: `{movement}_{variant}.json`. Variant defaults to `clean`. Searches
`tests/fixtures/synthetic/` first; future Flutter golden captures will be
discovered from `tests/fixtures/golden/` by adding a second search root.
"""

import json
from pathlib import Path
from typing import Literal

from bioliminal.api.schemas import Session

MovementType = Literal["overhead_squat", "single_leg_squat", "push_up", "rollup"]

_SYNTHETIC_DIR = Path(__file__).parent / "synthetic"


def load_fixture(
    movement: MovementType,
    variant: str = "clean",
    search_dir: Path | None = None,
) -> Session:
    base = search_dir if search_dir is not None else _SYNTHETIC_DIR
    path = base / f"{movement}_{variant}.json"
    if not path.exists():
        raise FileNotFoundError(f"fixture not found: {path}")
    return Session.model_validate(json.loads(path.read_text()))
