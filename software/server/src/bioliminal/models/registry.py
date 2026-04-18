"""Model registry — tracks ModelLoader instances by name.

Plan 4 refactor: the placeholder `ModelRegistry(loaded: dict[str, str])` is
replaced by a real registration API that holds `ModelLoader` instances. Future
plans register concrete loaders (MotionBERT, HSMR) by calling
`REGISTRY.register(MotionBERTLoader())` at application startup.
"""

from bioliminal.ml.loader import ModelLoader


class ModelRegistry:
    def __init__(self) -> None:
        self._loaders: dict[str, ModelLoader] = {}

    def register(self, loader: ModelLoader) -> None:
        self._loaders[loader.name] = loader

    def get(self, name: str) -> ModelLoader:
        if name not in self._loaders:
            raise KeyError(f"no loader registered with name '{name}'")
        return self._loaders[name]

    def is_registered(self, name: str) -> bool:
        return name in self._loaders

    def loaded_models(self) -> list[str]:
        return [name for name, loader in self._loaders.items() if loader.is_loaded()]

    def info(self) -> dict[str, dict[str, str]]:
        return {name: loader.info() for name, loader in self._loaders.items()}


REGISTRY = ModelRegistry()
