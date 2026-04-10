# AuraLink Server

Python server for AuraLink's movement screening ML pipeline. Accepts pose keypoint sessions from the Flutter app, runs analysis, returns reports.

## Quick Start

```bash
cd software/server
uv sync
uv run uvicorn auralink.api.main:app --reload
```

Server runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

## Run Tests

```bash
uv run pytest
```

## Project Layout

See `docs/research-integration-report.md` section 6 for architectural context. Pipeline stages live under `src/auralink/` organized by domain (pose, analysis, reasoning, etc.).
