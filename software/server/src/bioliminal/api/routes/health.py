from fastapi import APIRouter

from bioliminal.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str | int]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "default_retention_days": settings.default_retention_days,
    }
