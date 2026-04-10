import os
from pathlib import Path

from auralink.config import Settings


def test_settings_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("AURALINK_DATA_DIR", str(tmp_path))
    settings = Settings()
    assert settings.data_dir == tmp_path
    assert settings.sessions_dir == tmp_path / "sessions"
    assert settings.app_name == "auralink-server"
