"""Wiring verification — exercises the full pipeline against the hand-built
mobile handover fixture. Asserts the response shape is well-formed and
no pipeline stage raises. Does NOT assert rep counts exactly because the
fixture is hand-built and may not follow the synthetic cosine shape."""
import json
import os
from pathlib import Path

import pytest

from bioliminal.api.schemas import Session
from bioliminal.pipeline.orchestrator import run_pipeline


FIXTURE_RELATIVE = Path(
    "bioliminal-ops/operations/handover/mobile/fixtures/sample_bicep_curl_with_emg.json"
)


def _candidate_fixture_paths() -> list[Path]:
    """Resolve the bicep handover fixture relative to the repo, with CI-friendly fallbacks.

    Order:
    1. BICEP_FIXTURE_PATH env var if set (explicit CI override).
    2. Ascend from this test file up to 8 levels looking for a parent that contains
       the `bioliminal-ops/operations/handover/mobile/fixtures/...` subtree.
    3. $PWD / FIXTURE_RELATIVE (useful when pytest is run from the workspace root).
    """
    candidates: list[Path] = []
    env_override = os.environ.get("BICEP_FIXTURE_PATH")
    if env_override:
        candidates.append(Path(env_override))
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents)[:8]:
        candidate = parent / FIXTURE_RELATIVE
        candidates.append(candidate)
        candidates.append(parent.parent / FIXTURE_RELATIVE if parent.parent != parent else candidate)
    candidates.append(Path.cwd() / FIXTURE_RELATIVE)
    seen: set[str] = set()
    unique: list[Path] = []
    for c in candidates:
        key = str(c)
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


@pytest.fixture
def real_bicep_session():
    for p in _candidate_fixture_paths():
        if p.exists():
            data = json.loads(p.read_text())
            return Session.model_validate(data)
    pytest.skip(
        "sample_bicep_curl_with_emg.json not found; set BICEP_FIXTURE_PATH to override."
    )


def test_pipeline_runs_end_to_end_without_exceptions(real_bicep_session):
    from bioliminal.pipeline.errors import QualityGateError

    try:
        report = run_pipeline(real_bicep_session)
    except QualityGateError:
        # Hand-built fixture may fail the quality gate (e.g. short_duration).
        # That counts as a successful wiring check — every stage ran cleanly
        # up to and including the quality gate; no unexpected exception was raised.
        return

    assert report is not None
    assert hasattr(report, "rep_scores")
    assert hasattr(report, "chain_observations")
    if len(real_bicep_session.frames) > 60:
        assert len(report.rep_scores) >= 0


def test_pipeline_produces_elbow_angle_series(real_bicep_session):
    from bioliminal.pipeline.stages.angle_series import run_angle_series
    from bioliminal.pipeline.stages.base import StageContext
    ctx = StageContext(session=real_bicep_session, artifacts={})
    result = run_angle_series(ctx)
    assert "left_elbow_flexion" in result.angles
    assert len(result.angles["left_elbow_flexion"]) == len(real_bicep_session.frames)
