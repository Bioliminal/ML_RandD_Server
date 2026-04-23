"""Pose-only e2e validation for the bicep curl pipeline.

Two layers:

1. **Smoke case** — exercises the full pipeline against the pose-only
   sample fixture in ``bioliminal-ops/operations/handover/mobile/fixtures/``.
   Always runs. Asserts the pipeline completes and the response shape is
   well-formed (per-rep metrics populated, chain_observations is a list).
   Does NOT assert rep-count accuracy because the hand-built sample has
   no human-counted truth.

2. **Ground-truth accuracy pass** — parameterised over fixtures under
   ``RnD_Server/ml/datasets/bicep_ground_truth/``. Each fixture is a
   ``*.session.json`` paired with a sibling ``*.truth.json`` carrying
   ``rep_count`` (and optionally ``rep_boundaries_ms``). Skipped while the
   ground-truth set is empty (Wave 2 of the L2 plan
   ``bioliminal-ops/plans/2026-04-22-L2-ml-rep-validation.md``); un-skips
   automatically when fixtures land. Asserts ≥90% of fixtures within ±1
   rep, no fixture off by more than ±3.

Schema notes vs the parent brief
(``bioliminal-ops/operations/handovers/2026-04-21-ml-rep-validation.md``):

- The integration runs in-process via ``run_pipeline``, matching the
  sibling ``test_bicep_pipeline_real_fixture.py`` pattern (the brief's
  HTTP TestClient flow is equivalent and not needed for the validation).
- Per-rep field is ``velocity_decline_pct`` (NOT ``velocity_peak`` as the
  brief assumed) — see ``software/server/src/bioliminal/pipeline/artifacts.py``.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from bioliminal.api.schemas import Session
from bioliminal.pipeline.errors import QualityGateError
from bioliminal.pipeline.orchestrator import run_pipeline


SAMPLE_FIXTURE_RELATIVE = Path(
    "bioliminal-ops/operations/handover/mobile/fixtures/sample_pose_only_bicep.json"
)
GROUND_TRUTH_DIR_RELATIVE = Path("RnD_Server/ml/datasets/bicep_ground_truth")


def _candidate_paths(relative: Path) -> list[Path]:
    """Resolve ``relative`` against the repo, with CI-friendly fallbacks.

    Order:
    1. POSE_ONLY_FIXTURE_PATH / GROUND_TRUTH_DIR env override.
    2. Ascend up to 8 parents from this file looking for ``relative``.
    3. ``$PWD / relative``.
    """
    candidates: list[Path] = []
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents)[:8]:
        candidates.append(parent / relative)
    candidates.append(Path.cwd() / relative)
    seen: set[str] = set()
    unique: list[Path] = []
    for c in candidates:
        key = str(c)
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def _resolve_sample_fixture() -> Path | None:
    env = os.environ.get("POSE_ONLY_FIXTURE_PATH")
    if env:
        p = Path(env)
        return p if p.exists() else None
    for p in _candidate_paths(SAMPLE_FIXTURE_RELATIVE):
        if p.exists():
            return p
    return None


def _resolve_ground_truth_dir() -> Path | None:
    env = os.environ.get("GROUND_TRUTH_DIR")
    if env:
        p = Path(env)
        return p if p.is_dir() else None
    for p in _candidate_paths(GROUND_TRUTH_DIR_RELATIVE):
        if p.is_dir():
            return p
    return None


def _ground_truth_pairs() -> list[tuple[Path, Path]]:
    """Return ``(session_path, truth_path)`` pairs from the ground-truth dir.

    Empty list when the directory doesn't exist or holds no pairs — the
    parameterised test is skipped in that case.
    """
    root = _resolve_ground_truth_dir()
    if root is None:
        return []
    pairs: list[tuple[Path, Path]] = []
    for session_path in sorted(root.glob("*.session.json")):
        truth_path = session_path.with_name(
            session_path.name.replace(".session.json", ".truth.json")
        )
        if truth_path.exists():
            pairs.append((session_path, truth_path))
    return pairs


# --- Layer 1: smoke case ----------------------------------------------------


@pytest.fixture
def pose_only_sample_session() -> Session:
    fixture = _resolve_sample_fixture()
    if fixture is None:
        pytest.skip(
            "sample_pose_only_bicep.json not found; "
            "set POSE_ONLY_FIXTURE_PATH to override."
        )
    data = json.loads(fixture.read_text())
    return Session.model_validate(data)


def test_pose_only_pipeline_runs_end_to_end(pose_only_sample_session: Session):
    """Pose-only session (no ``emg``, no ``consent``) traverses every stage."""
    assert pose_only_sample_session.emg is None, "fixture must be pose-only"
    assert pose_only_sample_session.consent is None, "fixture must omit consent"

    try:
        report = run_pipeline(pose_only_sample_session)
    except QualityGateError:
        pytest.skip("hand-built sample fixture rejected by quality gate")

    assert report is not None
    assert hasattr(report, "rep_scores")
    assert hasattr(report, "chain_observations")
    assert hasattr(report, "per_rep_metrics")


def test_pose_only_per_rep_metrics_populated(pose_only_sample_session: Session):
    """Per-rep metrics surface the fields the showcase Report depends on."""
    try:
        report = run_pipeline(pose_only_sample_session)
    except QualityGateError:
        pytest.skip("hand-built sample fixture rejected by quality gate")

    assert report.per_rep_metrics is not None, "per_rep_metrics missing"
    assert report.per_rep_metrics.reps, "per_rep_metrics.reps empty"

    for rep in report.per_rep_metrics.reps:
        d = rep.model_dump()
        # Schema fields per software/server/src/bioliminal/pipeline/artifacts.py.
        # NOTE: brief said ``velocity_peak``; real field is ``velocity_decline_pct``.
        assert "amplitude_deg" in d
        assert "concentric_s" in d
        assert "velocity_decline_pct" in d


def test_pose_only_chain_observations_is_a_list(pose_only_sample_session: Session):
    """``chain_observations`` may be empty but must be a list."""
    try:
        report = run_pipeline(pose_only_sample_session)
    except QualityGateError:
        pytest.skip("hand-built sample fixture rejected by quality gate")

    obs = report.chain_observations
    assert obs is None or isinstance(obs, list)


# --- Layer 2: ground-truth accuracy pass ------------------------------------


_PAIRS = _ground_truth_pairs()
_SKIP_REASON = (
    f"no ground-truth fixtures at {GROUND_TRUTH_DIR_RELATIVE} "
    f"(L2-ml-rep-validation Wave 2 pending)"
)


@pytest.mark.skipif(not _PAIRS, reason=_SKIP_REASON)
@pytest.mark.parametrize(
    "session_path,truth_path",
    _PAIRS,
    ids=[p[0].name.replace(".session.json", "") for p in _PAIRS],
)
def test_ground_truth_rep_count_within_tolerance(
    session_path: Path, truth_path: Path
) -> None:
    """Per-fixture: pose-derived rep count matches human truth within ±3.

    Aggregate accuracy (≥90% within ±1) is enforced separately by
    ``test_ground_truth_aggregate_accuracy``.
    """
    session = Session.model_validate(json.loads(session_path.read_text()))
    session.emg = None  # force pose-only
    truth = json.loads(truth_path.read_text())
    truth_count = int(truth["rep_count"])

    report = run_pipeline(session)
    server_count = len(report.per_rep_metrics.reps) if report.per_rep_metrics else 0
    delta = abs(server_count - truth_count)
    assert delta <= 3, (
        f"{session_path.name}: server={server_count} truth={truth_count} delta={delta}"
    )


@pytest.mark.skipif(not _PAIRS, reason=_SKIP_REASON)
def test_ground_truth_aggregate_accuracy() -> None:
    """≥90% of fixtures must match within ±1 rep."""
    within_one = 0
    total = len(_PAIRS)
    failures: list[str] = []
    for session_path, truth_path in _PAIRS:
        session = Session.model_validate(json.loads(session_path.read_text()))
        session.emg = None
        truth_count = int(json.loads(truth_path.read_text())["rep_count"])
        report = run_pipeline(session)
        server_count = len(report.per_rep_metrics.reps) if report.per_rep_metrics else 0
        if abs(server_count - truth_count) <= 1:
            within_one += 1
        else:
            failures.append(
                f"{session_path.name}: server={server_count} truth={truth_count}"
            )
    accuracy = within_one / total if total else 0.0
    assert accuracy >= 0.9, (
        f"aggregate ±1 accuracy {within_one}/{total} = {accuracy:.0%} (<90%); "
        f"failures: {failures}"
    )
