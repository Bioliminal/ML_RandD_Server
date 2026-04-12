"""Regenerate all synthetic JSON fixtures deterministically.

Run from repo root:
    uv run python scripts/regenerate_fixtures.py

This script is intentionally minimal — all realism lives in generator.py.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "software" / "server"))

from tests.fixtures.synthetic.generator import generate_session  # noqa: E402

OUT_DIR = REPO_ROOT / "software" / "server" / "tests" / "fixtures" / "synthetic"

FIXTURES = [
    ("overhead_squat_clean.json", {"movement": "overhead_squat", "rep_count": 2, "frames_per_rep": 30}),
    (
        "overhead_squat_valgus.json",
        {
            "movement": "overhead_squat",
            "rep_count": 2,
            "frames_per_rep": 30,
            "injected_compensations": {"knee_valgus_deg": 12.0, "trunk_lean_deg": 4.0},
        },
    ),
    ("single_leg_squat_clean.json", {"movement": "single_leg_squat", "rep_count": 2, "frames_per_rep": 30}),
    ("push_up_clean.json", {"movement": "push_up", "rep_count": 2, "frames_per_rep": 30}),
    ("rollup_clean.json", {"movement": "rollup", "rep_count": 1, "frames_per_rep": 60}),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, kwargs in FIXTURES:
        payload = generate_session(**kwargs)
        out = OUT_DIR / filename
        out.write_text(json.dumps(payload, indent=2))
        print(f"wrote {out.relative_to(REPO_ROOT)}  ({len(payload['frames'])} frames)")


if __name__ == "__main__":
    main()
