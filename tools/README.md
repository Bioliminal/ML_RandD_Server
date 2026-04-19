# tools/

Operational scripts for the bioliminal analysis server. Stdlib-only where
possible so they can run on the demo workstation without setting up the
server's venv.

## smoke_demo_server.py — ML#25 demo-server smoke gate

Runs a deterministic round-trip against the deployed analysis server:

1. **preflight** — hash the fixture, capture movement / frame-count / consent
2. **health** — `GET /health` returns `{"status":"ok","app":...}`. Captures `app` (proves the `bioliminal` rename actually shipped — old builds report `auralink`).
3. **openapi** — `GET /openapi.json` and assert the deployed spec exposes the four routes (`/health`, `POST /sessions`, `GET /sessions/{id}`, `GET /sessions/{id}/report`) and the schema groups: `Session` (or FastAPI's `Session-Input` variant when the in/out schemas diverge), `SessionCreateResponse`, `Report`, `ConsentMetadata`. Schemas only used internally (e.g. `EvidenceBlock`, loaded from YAML at startup and never in a request/response) never appear in `openapi.json`, so they can't be used as deploy-currency proofs. `app='bioliminal-server'` from `/health` is the rename proof.
4. **post-session-3** — `POST /sessions` with the demo fixture, assert 200/201 + `session_id` + `frames_received == len(fixture.frames)`.
5. **get-report-4** — `GET /sessions/{id}/report`, assert `metadata.session_id`, `metadata.movement` (matches fixture), and a non-empty `overall_narrative`.
6. **post-session-5 + get-report-6** — re-post the same fixture. Reports must produce the same `overall_narrative` (deterministic reasoner).
7. **determinism** — narratives identical across the two posts.
8. **reasoner-fires** — POST `overhead_squat_valgus.json` (known-bad) and assert ≥1 chain_observation comes back. Without this, a regression that always returns no observations would still pass the rest of the smoke (the clean fixture is silent by design). Skipped via `--no-valgus` or `--quick`. Reads `chain_observations` from `report.movement_section.chain_observations` — the top-level field does not exist on `Report` and earlier smoke versions reported 0 incorrectly.

Every request and response (bodies, headers, status, latency) is written to
`tools/smoke-logs/<UTC-ISO>-<host>/`. The full `openapi.json` is persisted so
schema drift can be diffed offline.

### Usage

```bash
# Default: hit the public tunnel, full determinism check
python3 tools/smoke_demo_server.py

# Local dev server
python3 tools/smoke_demo_server.py --base-url http://localhost:8000

# Skip the second round-trip if you only need a liveness probe
python3 tools/smoke_demo_server.py --quick

# Echo response narratives (helps when chasing a non-obvious failure)
python3 tools/smoke_demo_server.py -v
```

Exit codes: `0` all pass, `1` one or more checks failed, `2` preflight (fixture missing or bad args).

### When this fails

- **`health` fails with `app='auralink'`** — deployed build is pre-rename, predates `RnD_Server` commit `a2196de` (2026-04-18). Redeploy the demo server.
- **`openapi` reports `missing_schemas`** — a request/response model is gone from the deployed build. Compare the saved `02-openapi-response.json` against the local FastAPI app via `uv run python -c "from bioliminal.api.main import app; import json; print(json.dumps(app.openapi(), indent=2))" | jq '.components.schemas | keys'`.
- **`openapi` reports `missing_paths`** — route file diverged or a router was dropped. Compare deployed `openapi.json` (saved in the run-dir) against `software/server/src/bioliminal/api/main.py`.
- **`post-session` returns 422** — fixture schema drifted from server pydantic models. Regenerate via `bioliminal-ops/operations/handover/mobile/tools/export_schemas.py` and re-export the fixture.
- **`get-report` returns empty `overall_narrative`** — reasoner produced no observations for the fixture. Expected for the placeholder bicep_curl pipeline pre-ML#18; will be a real failure once ML#18+ML#12 land.
- **`determinism` fails** — reasoner is non-deterministic. Likely a dict iteration order leak or a timestamp bleeding into a narrative. Hard fail — investigate before the demo.
