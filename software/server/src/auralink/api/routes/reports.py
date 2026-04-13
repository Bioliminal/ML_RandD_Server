from fastapi import APIRouter, Depends, HTTPException, status

from auralink.config import Settings, get_settings
from auralink.pipeline.storage import SessionStorage
from auralink.report.assembler import assemble_report
from auralink.report.schemas import Report

router = APIRouter(prefix="/sessions", tags=["reports"])


def _get_storage(settings: Settings = Depends(get_settings)) -> SessionStorage:
    return SessionStorage(base_dir=settings.sessions_dir)


@router.get("/{session_id}/report", response_model=Report)
def get_report(
    session_id: str,
    storage: SessionStorage = Depends(_get_storage),
) -> Report:
    try:
        artifacts = storage.load_artifacts(session_id)
        session = storage.load(session_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no report for session {session_id}",
        ) from exc

    captured_at_ms = int(session.metadata.captured_at.timestamp() * 1000)
    return assemble_report(
        artifacts=artifacts,
        session_id=session_id,
        movement=session.metadata.movement,
        captured_at_ms=captured_at_ms,
    )
