from auralink.pipeline.artifacts import SessionQualityReport


class PipelineError(Exception):
    """Base class for all pipeline-side errors."""


class StageError(PipelineError):
    def __init__(self, stage_name: str, detail: str):
        super().__init__(f"stage '{stage_name}' failed: {detail}")
        self.stage_name = stage_name
        self.detail = detail


class QualityGateError(PipelineError):
    def __init__(self, report: SessionQualityReport):
        issue_count = len(report.issues)
        super().__init__(f"quality gate rejected session: {issue_count} issue(s)")
        self.report = report
