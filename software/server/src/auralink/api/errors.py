from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from auralink.pipeline.errors import PipelineError, QualityGateError, StageError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(QualityGateError)
    async def _quality_gate(request: Request, exc: QualityGateError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "quality_gate_rejected",
                "issues": [issue.model_dump() for issue in exc.report.issues],
                "metrics": exc.report.metrics,
            },
        )

    @app.exception_handler(StageError)
    async def _stage_error(request: Request, exc: StageError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": "stage_failed",
                "stage": exc.stage_name,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(PipelineError)
    async def _pipeline_error(request: Request, exc: PipelineError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"error": "pipeline_failed", "detail": str(exc)},
        )
