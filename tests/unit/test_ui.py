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
        lambda token=None: httpx.AsyncClient(
            transport=httpx.ASGITransport(app=api_app),
            base_url="http://api",
            headers={"Authorization": f"Bearer {token}"} if token else {},
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
    await signed_in(ui_client)
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


# ---------------------------------------------------------------- sign-on


def demo_members():
    from app.api.auth import demo_members

    return demo_members()


async def signed_in(ui_client) -> dict:
    """Sign in through the login form; returns the first demo member."""
    from app.config import get_settings

    member = demo_members()[0]
    password = get_settings().auth_demo_password.get_secret_value()
    r = await ui_client.post("/api/login", data={"email": member.email, "password": password})
    assert r.status_code == 200, r.text
    return member


async def test_sign_on_off_shows_no_account_link(ui_client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "auth_mode", "off")
    r = await ui_client.get("/api/")
    assert '"name":"account"' not in r.text.replace(" ", "")
    assert "Sign in" not in r.text
    assert "ModelForm" in (await ui_client.get("/api/items")).text  # everyone can add


@pytest.mark.usefixtures("mock_sign_on")
class TestWebSignOn:
    async def test_signed_out_the_navbar_offers_sign_in(self, ui_client):
        r = await ui_client.get("/api/")
        assert '"url":"/login"' in r.text.replace(" ", "")

    async def test_login_page_has_the_form_and_the_demo_members(self, ui_client):
        r = await ui_client.get("/api/login")
        assert "ModelForm" in r.text
        for member in demo_members():
            assert f"/login/as/{member.id}" in r.text

    async def test_signing_in_goes_to_the_welcome_page(self, ui_client):
        member = demo_members()[0]
        r = await ui_client.get(f"/api/login/as/{member.id}")
        assert r.json()[0]["event"]["url"] == "/welcome"
        assert member.name in (await ui_client.get("/api/welcome")).text

    async def test_signing_in_sets_an_httponly_session_cookie(self, ui_client):
        await signed_in(ui_client)
        cookie = next(c for c in ui_client.cookies.jar if c.name == ui.SESSION_COOKIE)
        assert cookie.has_nonstandard_attr("HttpOnly")
        assert cookie.get_nonstandard_attr("SameSite", "").lower() == "lax"

    async def test_signed_in_the_navbar_names_the_member_and_opens_the_panel(self, ui_client):
        member = await signed_in(ui_client)
        r = (await ui_client.get("/api/")).text
        assert member.name in r and member.email in r
        assert '"type":"Modal"' in r.replace(" ", "")
        assert '"url":"/logout"' in r.replace(" ", "")

    async def test_a_wrong_password_is_shown_on_the_form(self, ui_client):
        member = demo_members()[0]
        r = await ui_client.post("/api/login", data={"email": member.email, "password": "no"})
        assert r.status_code == 422
        assert r.json()["detail"]["form"][0] == {
            "loc": ["password"],
            "msg": "Wrong email or password",
        }

    async def test_one_click_sign_in_as_a_demo_member(self, ui_client):
        member = demo_members()[-1]
        r = await ui_client.get(f"/api/login/as/{member.id}")
        assert r.status_code == 200
        assert member.name in (await ui_client.get("/api/")).text
        assert (await ui_client.get("/api/login/as/nobody")).status_code == 404

    async def test_only_members_see_the_items_form(self, ui_client):
        assert "ModelForm" not in (await ui_client.get("/api/items")).text
        await signed_in(ui_client)
        assert "ModelForm" in (await ui_client.get("/api/items")).text

    async def test_items_are_added_as_the_signed_in_member(self, ui_client, fake_repo):
        r = await ui_client.post("/api/items", data={"name": "Anhysbys"})
        assert r.json()[0]["event"]["url"] == "/login"  # signed out: sent to sign in
        member = await signed_in(ui_client)
        await ui_client.post("/api/items", data={"name": "Hiraeth"})
        assert [(i.name, i.created_by) for i in fake_repo.items] == [("Hiraeth", member.id)]

    async def test_signing_out_clears_the_cookie(self, ui_client):
        member = await signed_in(ui_client)
        r = await ui_client.get("/api/logout")
        assert r.json()[0]["event"] == {"url": "/welcome", "type": "go-to"}  # no query: see logout
        assert ui.SESSION_COOKIE not in ui_client.cookies
        assert member.name not in (await ui_client.get("/api/")).text
