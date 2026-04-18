from typing import Protocol, runtime_checkable


@runtime_checkable
class ModelLoader(Protocol):
    """Protocol for a loadable ML model.

    Concrete implementations (e.g., MotionBERTLoader, HSMRLoader) are added in
    later epochs. Plan 4 ships only NoOpLoader so the pipeline has something to
    register with the ModelRegistry.
    """

    name: str

    def load(self) -> None: ...

    def is_loaded(self) -> bool: ...

    def info(self) -> dict[str, str]: ...


class NoOpLoader:
    """Trivial ModelLoader that always reports loaded.

    Used as the default registered loader so pipeline code can query
    `ModelRegistry.is_registered("noop")` without requiring a real model.
    """

    name: str = "noop"

    def load(self) -> None:
        return None

    def is_loaded(self) -> bool:
        return True

    def info(self) -> dict[str, str]:
        return {"name": self.name, "version": "0", "status": "loaded"}
