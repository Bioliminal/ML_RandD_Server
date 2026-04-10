"""Model checkpoint management — placeholder.

Tracks which models are loaded at runtime. Future plans will add
MotionBERT and HSMR loaders that register themselves here at startup.
"""

from dataclasses import dataclass, field


@dataclass
class ModelRegistry:
    loaded: dict[str, str] = field(default_factory=dict)

    def register(self, name: str, version: str) -> None:
        self.loaded[name] = version

    def info(self) -> dict[str, str]:
        return dict(self.loaded)


REGISTRY = ModelRegistry()
