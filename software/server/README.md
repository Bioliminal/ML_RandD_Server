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

## Showcase deployment (2026-04-23, 16:40)

Same server host as the 4/20 demo: a Windows workstation with a
P100/V100-class GPU, exposed to the phone via a Cloudflare named tunnel
at `https://bioliminal-demo.aaroncarney.me` → `localhost:8000`. Pipeline
is CPU-only for bicep curl (rule eval + geometry on BlazePose
landmarks); the GPU is reserved for post-showcase upgrades.

Pre-show checks (Thu 12:00 noon scope freeze, per
`bioliminal-ops/decisions/2026-04-22-showcase-scope.md`):

- `bicep_curl` movement type accepted on `/sessions`
- `bicep.yaml` rules load + `chain_observations` populated in Report
- Privacy `/health` returns `default_retention_days`
- `software/tools/smoke_demo_server.py` green against the deployed tunnel
- Pose-only `SessionPayload` (no sEMG channels) round-trips and produces a populated Report

Standup + tunnel runbooks:
- `bioliminal-ops/operations/comms/2026-04-16-demo-server-standup.md`
- `bioliminal-ops/operations/comms/2026-04-18-cloudflare-tunnel-setup.md`

Mobile-facing contract: `bioliminal-ops/operations/handover/mobile/README.md`
and the machine-readable schemas under `.../handover/mobile/schemas/`
(`session.schema.json` for the request, `report.schema.json` for the
response). See `software/MOBILE_HANDOVER.md` for the move rationale.

## 4/20 demo

The first live demo shipped on 2026-04-20 with firmware-led rep counting
and haptic cueing. The 4/21 amendment moved rep counting authority to
pose (firmware keeps a local fallback + accepts `OP_REP_CONFIRMED`
reconciliation on FF04); fatigue + haptic stayed firmware-led. Server
behavior is unchanged across the amendment — `rep_segmentation.py`
already validated against pose, and ML#18 + ML#12 are merged.

Validation work for the showcase pose-only path lives at
`bioliminal-ops/operations/handovers/2026-04-21-ml-rep-validation.md` —
ground-truth fixtures + `test_bicep_pose_only_e2e.py`.
