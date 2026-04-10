from fastapi import APIRouter, Depends, HTTPException, status

from auralink.config import Settings, get_settings
from auralink.pipeline.artifacts import PipelineArtifacts
from auralink.pipeline.storage import SessionStorage

router = APIRouter(prefix="/sessions", tags=["reports"])


def _get_storage(settings: Settings = Depends(get_settings)) -> SessionStorage:
    return SessionStorage(base_dir=settings.sessions_dir)


@router.get("/{session_id}/report", response_model=PipelineArtifacts)
def get_report(
    session_id: str,
    storage: SessionStorage = Depends(_get_storage),
) -> PipelineArtifacts:
    try:
        return storage.load_artifacts(session_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no report for session {session_id}",
        ) from exc
