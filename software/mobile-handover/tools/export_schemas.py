#!/usr/bin/env python3
"""Regenerate request + response JSON schemas from the live pydantic models.

Exports:
- schemas/session.schema.json — POST /sessions request body (Session)
- schemas/report.schema.json  — GET /sessions/{id}/report response (Report)

Run after any change to software/server/src/auralink/api/schemas.py or
software/server/src/auralink/report/schemas.py to keep the handover schemas
in lockstep.

Usage:
    cd software/mobile-handover/tools
    ../../server/.venv/bin/python export_schemas.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HANDOVER = HERE.parent
SERVER_SRC = HANDOVER.parent / "server" / "src"
SCHEMAS_DIR = HANDOVER / "schemas"

sys.path.insert(0, str(SERVER_SRC))
from auralink.api.schemas import Session  # noqa: E402
from auralink.report.schemas import Report  # noqa: E402

SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)

for model, filename in [(Session, "session.schema.json"), (Report, "report.schema.json")]:
    out = SCHEMAS_DIR / filename
    out.write_text(json.dumps(model.model_json_schema(), indent=2) + "\n")
    print(f"wrote {out.relative_to(HANDOVER.parent)}")
