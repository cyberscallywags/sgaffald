import pytest

from app import serve


@pytest.mark.parametrize(("service", "port"), [("api", 8000), ("ui", 8080)])
def test_web_services_run_under_uvicorn(monkeypatch, service, port):
    calls = []
    monkeypatch.setattr("uvicorn.run", lambda target, **kw: calls.append((target, kw)))
    monkeypatch.setenv("HOST", "127.0.0.1")

    serve.main([service])

    assert calls == [(f"app.{service}.main:app", {"host": "127.0.0.1", "port": port})]


def test_service_falls_back_to_the_environment(monkeypatch):
    calls = []
    monkeypatch.setattr("uvicorn.run", lambda target, **kw: calls.append(target))
    monkeypatch.setenv("SERVICE", "api")

    serve.main([])

    assert calls == ["app.api.main:app"]


def test_unknown_service_exits_with_a_message(monkeypatch):
    monkeypatch.delenv("SERVICE", raising=False)
    with pytest.raises(SystemExit, match="Unknown SERVICE 'nope'"):
        serve.main(["nope"])
