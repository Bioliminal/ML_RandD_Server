import uuid
from pathlib import Path

from auralink.api.schemas import Session


class SessionStorage:
    """Local filesystem storage for session artifacts.

    Stores each session as a single JSON file keyed by generated UUID.
    Later replaceable with object storage without changing callers.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session: Session) -> str:
        session_id = str(uuid.uuid4())
        path = self._path_for(session_id)
        path.write_text(session.model_dump_json(indent=2))
        return session_id

    def load(self, session_id: str) -> Session:
        path = self._path_for(session_id)
        if not path.exists():
            raise FileNotFoundError(f"session {session_id} not found at {path}")
        return Session.model_validate_json(path.read_text())

    def _path_for(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"
