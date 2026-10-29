import httpx
import pytest

from app.agent import build_agent
from app.api.main import app
from app.meta import get_meta


@pytest.fixture
async def client(fake_repo):
    # ASGITransport skips the lifespan, so no Neo4j connection is attempted.
    app.state.repo = fake_repo
    app.state.agent = build_agent("test")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://api") as c:
        yield c


async def test_health_ok(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "env": "test", "neo4j": True}


async def test_health_degraded(client, fake_repo):
    fake_repo.healthy = False
    assert (await client.get("/health")).json()["status"] == "degraded"


async def test_create_then_list(client):
    r = await client.post("/items", json={"name": "Castell"})
    assert r.status_code == 201
    listed = (await client.get("/items")).json()
    assert [i["name"] for i in listed] == ["Castell"]


async def test_create_rejects_blank(client):
    assert (await client.post("/items", json={"name": ""})).status_code == 422


async def test_ask_uses_agent_tool(client, fake_repo):
    await client.post("/items", json={"name": "Draig"})
    r = await client.post("/ask", json={"question": "What items exist?"})
    assert r.status_code == 200
    # TestModel calls every tool and echoes the results as its answer.
    assert "Draig" in r.json()["answer"]


async def test_no_cors_for_unlisted_origin(client):
    r = await client.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers


async def test_site_serves_the_manifest(client):
    r = await client.get("/site")
    assert r.status_code == 200
    body = r.json()
    # site.json leaves the name and collective out, so they come from project.toml
    assert body["brand"]["name"] == get_meta().name
    assert body["brand"]["collective"] == get_meta().organisation.name
    assert body["theme"]["primary"].startswith("#")
    assert {"welcome", "about", "pages"} <= body.keys()


async def test_openapi_identity_comes_from_project_toml(client):
    info = (await client.get("/openapi.json")).json()["info"]
    assert info["title"] == f"{get_meta().slug}-api"
    assert info["version"] == get_meta().version


async def test_site_carries_the_docs_url_from_settings(client, monkeypatch):
    from app.config import get_settings

    assert (await client.get("/site")).json()["docs_url"] == "http://localhost:8200"
    monkeypatch.setattr(get_settings(), "docs_url", "")
    assert (await client.get("/site")).json()["docs_url"] is None
