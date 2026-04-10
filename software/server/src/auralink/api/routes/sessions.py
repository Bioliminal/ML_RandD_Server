from fastapi import APIRouter, Depends, HTTPException, status

from auralink.api.schemas import Session, SessionCreateResponse
from auralink.config import Settings, get_settings
from auralink.pipeline.storage import SessionStorage

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_storage(settings: Settings = Depends(get_settings)) -> SessionStorage:
    return SessionStorage(base_dir=settings.sessions_dir)


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session: Session,
    storage: SessionStorage = Depends(_get_storage),
) -> SessionCreateResponse:
    session_id = storage.save(session)
    return SessionCreateResponse(
        session_id=session_id,
        frames_received=len(session.frames),
    )


@router.get("/{session_id}", response_model=Session)
def get_session(
    session_id: str,
    storage: SessionStorage = Depends(_get_storage),
) -> Session:
    try:
        return storage.load(session_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"session {session_id} not found",
        ) from exc
