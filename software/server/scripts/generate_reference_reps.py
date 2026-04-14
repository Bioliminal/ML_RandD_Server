"""Build-time generator for canonical reference reps (Plan 3).

Consumes generate_reference_rep() from tests/fixtures/synthetic/generator.py
— the shared synthetic generator owned by Plan 4 — runs the Plan 1 stages
(quality_gate, angle_series, normalize) on each resulting single-rep
session, extracts the normalized angle traces, and persists them as JSON
under software/server/config/reference_reps/.

Runtime temporal.reference_reps.load_reference_rep() reads these JSON
files at startup. The runtime never imports tests.fixtures — this script
is the only bridge.

Run with:
    cd software/server && uv run python scripts/generate_reference_reps.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_SERVER_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_SERVER_ROOT / "src"))
sys.path.insert(0, str(_SERVER_ROOT))  # for tests.fixtures import

from auralink.api.schemas import Session  # noqa: E402
from auralink.pipeline.stages.angle_series import run_angle_series  # noqa: E402
from auralink.pipeline.stages.base import StageContext  # noqa: E402
from auralink.pipeline.stages.normalize import run_normalize  # noqa: E402
from auralink.pipeline.stages.quality_gate import run_quality_gate  # noqa: E402
from tests.fixtures.synthetic.generator import generate_reference_rep  # noqa: E402

_OUTPUT_DIR = _SERVER_ROOT / "config" / "reference_reps"

_MOVEMENTS_WITH_REPS = (
    "overhead_squat",
    "single_leg_squat",
    "push_up",
)


def _normalized_angles_for_movement(movement: str) -> tuple[dict[str, list[float]], int, float]:
    payload = generate_reference_rep(movement=movement, frames_per_rep=30, frame_rate=30.0)
    session = Session.model_validate(payload)
    ctx = StageContext(session=session)
    ctx.artifacts["quality_gate"] = run_quality_gate(ctx)
    ctx.artifacts["angle_series"] = run_angle_series(ctx)
    ctx.artifacts["normalize"] = run_normalize(ctx)
    normalized = ctx.artifacts["normalize"]
    return normalized.angles, len(session.frames), session.metadata.frame_rate


def _write_reference_rep(movement: str) -> Path:
    angles, frames_per_rep, frame_rate = _normalized_angles_for_movement(movement)
    payload = {
        "movement": movement,
        "angles": angles,
        "frame_rate": frame_rate,
        "frames_per_rep": frames_per_rep,
    }
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _OUTPUT_DIR / f"{movement}.json"
    out_path.write_text(json.dumps(payload, indent=2))
    return out_path


def main() -> None:
    written: list[Path] = []
    for movement in _MOVEMENTS_WITH_REPS:
        path = _write_reference_rep(movement)
        print(f"wrote {path}")
        written.append(path)
    print(f"done: {len(written)} reference reps written to {_OUTPUT_DIR}")


if __name__ == "__main__":
    main()
