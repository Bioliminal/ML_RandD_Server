#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

export BIOLIMINAL_DATA_DIR="${BIOLIMINAL_DATA_DIR:-./data}"
mkdir -p "$BIOLIMINAL_DATA_DIR"

uv run uvicorn bioliminal.api.main:app --reload --host 0.0.0.0 --port 8000
