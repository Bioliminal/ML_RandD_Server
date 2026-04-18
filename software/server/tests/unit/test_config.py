from bioliminal.config import Settings


def test_settings_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    settings = Settings()
    assert settings.data_dir == tmp_path
    assert settings.sessions_dir == tmp_path / "sessions"
    assert settings.app_name == "bioliminal-server"


def test_settings_ensure_dirs_creates_sessions_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOLIMINAL_DATA_DIR", str(tmp_path))
    settings = Settings()
    assert not settings.sessions_dir.exists()
    settings.ensure_dirs()
    assert settings.sessions_dir.exists()
    assert settings.sessions_dir.is_dir()
