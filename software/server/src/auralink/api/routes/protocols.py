"""POST /protocols — cross-session protocol aggregation endpoint.

Accepts a list of session IDs, loads each session's saved artifacts, assembles
per-session Reports using Plan 2's assembler, and aggregates them via
protocol.aggregator.aggregate_protocol into a ProtocolReport. Cross-session
analysis lives here because pipeline stages run per-session.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from auralink.config import Settings, get_settings
from auralink.pipeline.storage import SessionStorage
from auralink.protocol.aggregator import aggregate_protocol
from auralink.protocol.schemas import ProtocolReport, ProtocolRequest
from auralink.report.assembler import assemble_report
from auralink.report.schemas import Report

router = APIRouter(prefix="/protocols", tags=["protocols"])


def _get_storage(settings: Settings = Depends(get_settings)) -> SessionStorage:
    return SessionStorage(base_dir=settings.sessions_dir)


@router.post("", response_model=ProtocolReport)
def create_protocol(
    request: ProtocolRequest,
    storage: SessionStorage = Depends(_get_storage),
) -> ProtocolReport:
    reports: list[Report] = []
    for session_id in request.session_ids:
        try:
            artifacts = storage.load_artifacts(session_id)
            session = storage.load(session_id)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"session {session_id} not found",
            ) from exc
        captured_at_ms = int(session.metadata.captured_at.timestamp() * 1000)
        reports.append(
            assemble_report(
                artifacts=artifacts,
                session_id=session_id,
                movement=session.metadata.movement,
                captured_at_ms=captured_at_ms,
            )
        )
    return aggregate_protocol(reports=reports, session_ids=list(request.session_ids))
