from fastapi import FastAPI

from auralink.api.routes import health, sessions
from auralink.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health.router)
    app.include_router(sessions.router)
    return app


app = create_app()
