"""Mock sign-on: login, tokens, the protected writes, and the production guard."""

from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest

from app.agent import build_agent
from app.api import auth
from app.api.main import app
from app.config import DEFAULT_AUTH_SECRET, Settings, get_settings


@pytest.fixture
async def client(fake_repo):
    app.state.repo = fake_repo
    app.state.agent = build_agent("test")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://api") as c:
        yield c


def first_member():
    return auth.demo_members()[0]


async def sign_in(client, email=None, password=None):
    password = password or get_settings().auth_demo_password.get_secret_value()
    return await client.post(
        "/auth/login", json={"email": email or first_member().email, "password": password}
    )


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.usefixtures("mock_sign_on")
class TestMockSignOn:
    async def test_a_demo_member_signs_in_with_the_demo_password(self, client):
        r = await sign_in(client)
        assert r.status_code == 200
        session = r.json()
        assert session["member"] == first_member().model_dump()
        me = await client.get("/auth/me", headers=bearer(session["token"]))
        assert me.json()["id"] == first_member().id

    async def test_email_is_case_insensitive(self, client):
        assert (await sign_in(client, first_member().email.upper())).status_code == 200

    @pytest.mark.parametrize(
        ("email", "password"), [("ada@example.org", "wrong"), ("nobody@example.org", "demo")]
    )
    async def test_wrong_credentials_are_refused(self, client, email, password):
        r = await sign_in(client, email, password)
        assert r.status_code == 401
        assert r.json()["detail"] == "Wrong email or password"

    async def test_writes_need_a_token(self, client):
        assert (await client.post("/items", json={"name": "Castell"})).status_code == 401
        assert (await client.post("/ask", json={"question": "?"})).status_code == 401
        assert (await client.get("/items")).status_code == 200  # reads stay public

    async def test_items_record_who_added_them(self, client):
        token = (await sign_in(client)).json()["token"]
        r = await client.post("/items", json={"name": "Castell"}, headers=bearer(token))
        assert r.status_code == 201
        assert r.json()["created_by"] == first_member().id

    async def test_a_tampered_token_is_refused(self, client):
        token = (await sign_in(client)).json()["token"]
        forged = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
        r = await client.get("/auth/me", headers=bearer(forged))
        assert r.status_code == 401
        assert r.headers["www-authenticate"] == "Bearer"

    async def test_an_expired_token_is_refused(self, client):
        claims = {**first_member().model_dump(exclude={"id"}), "sub": first_member().id}
        claims["exp"] = datetime.now(UTC) - timedelta(minutes=1)
        key = get_settings().auth_secret.get_secret_value()
        token = jwt.encode(claims, key, algorithm=auth.ALGORITHM)
        r = await client.get("/auth/me", headers=bearer(token))
        assert (r.status_code, r.json()["detail"]) == (401, "Session expired; sign in again")

    async def test_site_lists_the_demo_members_but_never_the_password(self, client):
        site = (await client.get("/site")).json()
        assert site["auth"]["mode"] == "mock"
        assert [u["email"] for u in site["auth"]["demo_users"]] == [
            m.email for m in auth.demo_members()
        ]
        assert "demo" not in str(site["auth"]).replace("demo_users", "")

    async def test_require_role_admits_only_that_role(self, client):
        check = auth.require_role("admin").dependency
        admin = next(m for m in auth.demo_members() if m.role == "admin")
        member = next(m for m in auth.demo_members() if m.role == "member")
        assert await check(admin) == admin
        with pytest.raises(auth.HTTPException) as refused:
            await check(member)
        assert refused.value.status_code == 403


async def test_with_sign_on_off_every_request_is_the_local_member(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_mode", "off")
    r = await client.post("/items", json={"name": "Castell"})
    assert (r.status_code, r.json()["created_by"]) == (201, auth.LOCAL_MEMBER.id)
    assert (
        await client.post("/auth/login", json={"email": "a@b.c", "password": "x"})
    ).status_code == 404
    assert (await client.get("/site")).json()["auth"] == {"mode": "off", "demo_users": []}


@pytest.mark.parametrize(
    ("allow_mock", "error"),
    [(False, "AUTH_MODE=mock is a demo"), (True, "AUTH_SECRET is the default")],
)
def test_production_refuses_demo_sign_on_and_the_default_key(monkeypatch, allow_mock, error):
    monkeypatch.setattr(get_settings(), "auth_mode", "mock")
    settings = Settings(app_env="production", auth_mode="mock", auth_allow_mock=allow_mock)
    with pytest.raises(RuntimeError, match=error):
        auth.check_settings(settings)


def test_production_with_sign_on_off_needs_no_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_mode", "off")
    auth.check_settings(Settings(app_env="production", auth_mode="off"))  # no error


def test_production_accepts_an_explicit_public_demo(monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_mode", "mock")
    settings = Settings(
        app_env="production", auth_mode="mock", auth_allow_mock=True, auth_secret="x" * 40
    )
    auth.check_settings(settings)  # no error
    assert settings.auth_secret.get_secret_value() != DEFAULT_AUTH_SECRET
