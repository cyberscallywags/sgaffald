import httpx
import pytest

from app.api.main import app as api_app
from app.content import get_site
from app.meta import get_meta
from app.ui import main as ui


@pytest.fixture
async def ui_client(fake_repo, monkeypatch):
    """UI wired to the real API app in-process (API backed by the fake repo)."""
    api_app.state.repo = fake_repo
    monkeypatch.setattr(
        ui,
        "api",
        lambda: httpx.AsyncClient(
            transport=httpx.ASGITransport(app=api_app), base_url="http://api"
        ),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=ui.app), base_url="http://ui"
    ) as c:
        yield c


async def test_landing_serves_fastui_shell(ui_client):
    r = await ui_client.get("/")
    assert r.status_code == 200
    assert "<html" in r.text.lower()


async def test_landing_is_themed_from_the_site_manifest(ui_client):
    r = await ui_client.get("/")
    assert f"--brand-primary: {get_site().theme.primary}" in r.text
    assert f"<title>{get_site().brand.name}</title>" in r.text


async def test_landing_links_the_brand_favicon_and_mark(ui_client):
    r = await ui_client.get("/")
    assert '<link rel="icon" href="/static/favicon.png">' in r.text
    assert "url('/static/mark." in r.text  # the navbar logo


@pytest.mark.parametrize("stem", ["favicon", "mark"])
async def test_static_serves_the_brand_images_sync_copied(ui_client, stem):
    url = ui.static_file(stem)
    assert url, f"run `uv run task sync`: src/app/ui/static/{stem}.* is missing"
    r = await ui_client.get(url)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")


async def test_welcome_renders_the_manifest(ui_client):
    r = await ui_client.get("/api/")
    assert r.status_code == 200
    assert "Planning the application" in r.text
    # the navbar mirrors the mobile side menu: sidebar pages plus About
    assert "/p/roadmap" in r.text and "/about" in r.text


async def test_about_promotes_the_collective(ui_client):
    r = await ui_client.get("/api/about")
    assert r.status_code == 200
    assert get_meta().organisation.name in r.text


async def test_content_page_by_slug(ui_client):
    assert "Data flow" in (await ui_client.get("/api/p/architecture")).text
    assert (await ui_client.get("/api/p/nope")).status_code == 404


async def test_items_page_lists_items_from_api(ui_client, fake_repo):
    await api_app.state.repo.create(ui.ItemIn(name="Cwtch"))
    r = await ui_client.get("/api/items")
    assert r.status_code == 200
    assert "Cwtch" in r.text


async def test_form_submit_creates_item(ui_client, fake_repo):
    r = await ui_client.post("/api/items", data={"name": "Hiraeth"})
    assert r.status_code == 200
    assert [i.name for i in fake_repo.items] == ["Hiraeth"]
    # GoToEvent must change the URL, or the browser keeps showing the stale table
    assert r.json()[0]["event"]["query"] == {"added": fake_repo.items[0].id}


async def test_navbar_links_to_the_docs_portal(ui_client):
    r = await ui_client.get("/api/")
    assert '"url":"http://localhost:8200"' in r.text.replace(" ", "")
    assert '"target":"_blank"' in r.text.replace(" ", "")


async def test_navbar_hides_docs_without_a_docs_url(ui_client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "docs_url", None)
    assert "localhost:8200" not in (await ui_client.get("/api/")).text
