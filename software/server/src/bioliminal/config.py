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

    @computed_field
    @property
    def sessions_dir(self) -> Path:
        return self.data_dir / "sessions"

    def ensure_dirs(self) -> None:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    return Settings()
