from fastapi import FastAPI

from bioliminal.api.errors import register_exception_handlers
from bioliminal.api.routes import health, protocols, reports, sessions
from bioliminal.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(sessions.router)
    app.include_router(reports.router)
    app.include_router(protocols.router)
    return app


app = create_app()
