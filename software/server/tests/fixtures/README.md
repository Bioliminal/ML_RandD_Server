# Test Fixtures

This directory holds recorded session JSON files used as ground-truth inputs for
integration and pipeline tests.

## Golden captures (from Flutter team)

The Flutter capture layer ships with a golden-capture test harness that records
raw BlazePose landmark streams (direct MediaPipe Tasks) for reference movements
on real devices. These recordings become the canonical fixtures for server-side
pipeline validation.

Expected format: JSON matching `bioliminal.api.schemas.Session`. Filename pattern:

    {movement}_{device}_{capture_date}.json

Example: `overhead_squat_pixel8_20260415.json`

## Naming conventions

Keep fixtures small — for regression tests, ~5 seconds of capture at 30fps is
plenty. If a fixture exceeds 1MB, trim the frame range before committing.

## What goes here vs `data/`

- `tests/fixtures/` → committed to git, small, curated for testing
- `data/sessions/` → local dev data, gitignored, arbitrary size
