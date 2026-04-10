#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

export AURALINK_DATA_DIR="${AURALINK_DATA_DIR:-./data}"
mkdir -p "$AURALINK_DATA_DIR"

uv run uvicorn auralink.api.main:app --reload --host 0.0.0.0 --port 8000
