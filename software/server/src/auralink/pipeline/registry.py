from auralink.pipeline.errors import PipelineError
from auralink.pipeline.stages.base import Stage


class StageRegistry:
    def __init__(self) -> None:
        self._by_movement: dict[str, list[Stage]] = {}

    def register_movement(self, movement_type: str, stages: list[Stage]) -> None:
        self._by_movement[movement_type] = list(stages)

    def get_stages(self, movement_type: str) -> list[Stage]:
        if movement_type not in self._by_movement:
            raise PipelineError(f"no stages registered for movement '{movement_type}'")
        return list(self._by_movement[movement_type])

    def has_movement(self, movement_type: str) -> bool:
        return movement_type in self._by_movement
