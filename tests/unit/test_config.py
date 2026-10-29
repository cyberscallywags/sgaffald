from app.config import Settings


def test_defaults_are_safe_for_tests(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    s = Settings(_env_file=None)
    assert s.app_env == "test"
    assert s.llm_model == "test"


def test_env_overrides_and_hides_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("NEO4J_PASSWORD", "s3cret")
    s = Settings(_env_file=None)
    assert s.app_env == "production"
    assert s.neo4j_password.get_secret_value() == "s3cret"
    assert "s3cret" not in repr(s)


def test_cors_origins_parse_from_json(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["capacitor://localhost","http://localhost"]')
    s = Settings(_env_file=None)
    assert s.cors_origins == ["capacitor://localhost", "http://localhost"]
