# BioLiminal Server

Python server for BioLiminal's movement screening ML pipeline. Accepts pose keypoint sessions from the Flutter app, runs analysis, returns reports.

## Quick Start

```bash
cd software/server
uv sync
uv run uvicorn bioliminal.api.main:app --reload
```

Server runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

## Run Tests

```bash
uv run pytest
```

## Project Layout

Pipeline stages live under `src/bioliminal/` organized by domain:
`api/` (FastAPI app + routes + request schemas), `pipeline/` (stage
orchestrator + artifacts), `pose/`, `analysis/`, `reasoning/`, `ml/`
(lifter / skeleton / phase-segmenter protocols), `temporal/`, `protocol/`,
`report/` (response schemas + narrative assembler).

## Demo deployment (2026-04-20)

For the 4/20 bicep curl demo the server runs on a Windows workstation with
a P100/V100-class GPU, exposed to the phone via a Cloudflare named tunnel at
`https://bioliminal-demo.aaroncarney.me` → `localhost:8000`. Pipeline is
CPU-only for the demo; the GPU is reserved for post-demo upgrades.

Standup + tunnel runbooks:
- `bioliminal-ops/operations/comms/2026-04-16-demo-server-standup.md`
- `bioliminal-ops/operations/comms/2026-04-18-cloudflare-tunnel-setup.md`

Mobile-facing contract: `bioliminal-ops/operations/handover/mobile/README.md`
and the machine-readable schemas under `.../handover/mobile/schemas/`
(`session.schema.json` for the request, `report.schema.json` for the
response). See `software/MOBILE_HANDOVER.md` for the move rationale.
