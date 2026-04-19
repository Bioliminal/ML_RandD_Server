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


def test_settings_default_retention_days_is_30(monkeypatch):
    """ML#20 demo-day: server publishes a default retention window so the
    consent fingerprint can fall back to it when ConsentMetadata.data_retention_days
    is None. 30 days picked per the issue's proposal."""
    monkeypatch.delenv("BIOLIMINAL_DEFAULT_RETENTION_DAYS", raising=False)
    settings = Settings()
    assert settings.default_retention_days == 30


def test_settings_default_retention_days_overridable(monkeypatch):
    monkeypatch.setenv("BIOLIMINAL_DEFAULT_RETENTION_DAYS", "7")
    settings = Settings()
    assert settings.default_retention_days == 7
