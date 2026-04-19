from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BIOLIMINAL_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "bioliminal-server"
    data_dir: Path = Field(default=Path("./data"))

    # ML#20 demo-day default retention window. ConsentMetadata.data_retention_days
    # falls back to this when the client doesn't specify. Pruning enforcement is
    # post-demo (see ML#20 deferred items); this is the published policy value.
    default_retention_days: int = Field(default=30, ge=1)

    @computed_field
    @property
    def sessions_dir(self) -> Path:
        return self.data_dir / "sessions"

    def ensure_dirs(self) -> None:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    return Settings()
