"""End-to-end checks across every container. Requires `task up` (or the CI compose step)."""

import os
from uuid import uuid4

import httpx
import pytest
from neo4j import GraphDatabase

pytestmark = pytest.mark.integration

API = os.getenv("API_URL", "http://localhost:8000")
UI = os.getenv("UI_URL", "http://localhost:8080")
ADMIN = os.getenv("ADMIN_URL", "http://localhost:8501")
MOBILE = os.getenv("MOBILE_URL", "http://localhost:8100")
DOCS = os.getenv("DOCS_URL", "http://localhost:8200")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "sgaffald-test-only")


@pytest.fixture(scope="module")
def name() -> str:
    return f"it-{uuid4().hex[:8]}"


def test_api_sees_neo4j():
    body = httpx.get(f"{API}/health").json()
    assert body["neo4j"] is True, body


def test_api_writes_to_neo4j(name):
    assert httpx.post(f"{API}/items", json={"name": name}).status_code == 201
    with GraphDatabase.driver(NEO4J_URI, auth=("neo4j", NEO4J_PASSWORD)) as driver:
        records, _, _ = driver.execute_query(
            "MATCH (i:Item {name: $name}) RETURN count(i) AS n", name=name
        )
    assert records[0]["n"] == 1


def test_neo4j_is_enterprise():
    with GraphDatabase.driver(NEO4J_URI, auth=("neo4j", NEO4J_PASSWORD)) as driver:
        records, _, _ = driver.execute_query("CALL dbms.components() YIELD edition RETURN edition")
    assert records[0]["edition"] == "enterprise"


def test_ui_renders_item_via_api(name):
    assert httpx.get(f"{UI}/").status_code == 200
    assert name in httpx.get(f"{UI}/api/items").text


def test_agent_answers():
    r = httpx.post(f"{API}/ask", json={"question": "What items exist?"}, timeout=30)
    assert r.status_code == 200 and r.json()["answer"]


def test_admin_is_up():
    assert httpx.get(f"{ADMIN}/_stcore/health").text == "ok"


def test_mobile_serves_app():
    r = httpx.get(f"{MOBILE}/items")  # deep link falls back to the SPA shell
    assert r.status_code == 200 and "<app-root>" in r.text


def test_web_and_mobile_share_one_site_manifest():
    site = httpx.get(f"{API}/site").json()
    assert httpx.get(f"{MOBILE}/api/site").json() == site
    assert site["theme"]["primary"] in httpx.get(f"{UI}/").text


def test_mobile_proxies_api_to_neo4j(name):
    assert httpx.get(f"{MOBILE}/api/health").json()["neo4j"] is True
    created = httpx.post(f"{MOBILE}/api/items", json={"name": f"{name}-mobile"})
    assert created.status_code == 201
    names = [i["name"] for i in httpx.get(f"{API}/items").json()]
    assert f"{name}-mobile" in names


def test_api_allows_native_app_origin():
    r = httpx.options(
        f"{API}/items",
        headers={
            "Origin": "capacitor://localhost",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "capacitor://localhost"


def test_docs_serves_portal_and_manual():
    assert httpx.get(f"{DOCS}/healthz").json() == {"status": "ok"}
    portal = httpx.get(f"{DOCS}/")
    assert portal.status_code == 200 and "csw-crest-512.webp" in portal.text
    # /manual/ redirects to the Sphinx home page, which exists
    assert "url=manual.html" in httpx.get(f"{DOCS}/manual/").text
    assert httpx.get(f"{DOCS}/manual/manual.html").status_code == 200
    assert httpx.get(f"{DOCS}/assets/images/csw-crest-512.png").status_code == 200


def test_docs_reference_is_generated_from_the_running_code():
    # the image ran app.docgen: every API route is documented on both sites
    paths = httpx.get(f"{API}/openapi.json").json()["paths"]
    portal = httpx.get(f"{DOCS}/reference/http-api/").text
    manual = httpx.get(f"{DOCS}/manual/reference/http-api.html").text
    for path in paths:
        assert path in portal and path in manual


def test_apps_link_to_the_docs():
    assert httpx.get(f"{API}/site").json()["docs_url"] == DOCS
    assert DOCS in httpx.get(f"{UI}/api/").text
