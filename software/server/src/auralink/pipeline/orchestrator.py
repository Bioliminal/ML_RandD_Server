"""Pipeline orchestrator — placeholder.

The orchestrator chains analysis stages together in order:
ingest -> joint angles -> rep segmentation -> (3D lift) -> (SKEL) -> chain reasoning -> report.

Each stage consumes and produces a session artifact. This file will be
filled in by a later plan once MotionBERT and HSMR are integrated.
"""

from auralink.api.schemas import Session


def run_pipeline(session: Session) -> dict:
    """Placeholder — returns session metadata only.

    Full pipeline implementation lives in a follow-on plan.
    """
    return {
        "movement": session.metadata.movement,
        "frame_count": len(session.frames),
        "status": "scaffolded - no analysis stages wired yet",
    }
