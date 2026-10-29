"""Mock sign-on: demo members from the brand's content/users.json, HS256 bearer tokens, and the
dependencies that protect the write endpoints.

It has the shape of a real identity provider, so replacing it changes only `issue`, `verify`
and the login route: the frontends send `Authorization: Bearer <token>` either way, and every
route asks for a `CurrentMember`. See the handbook's Sign-on page for the move to OIDC."""

import hmac
import json
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Annotated, Literal

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import TypeAdapter

from app.config import DEFAULT_AUTH_SECRET, Settings, get_settings
from app.meta import brand_dir, get_meta
from app.models import AuthInfo, LoginIn, Member, Session

ALGORITHM = "HS256"
# Who every request is when sign-on is off: local development, the load test.
LOCAL_MEMBER = Member(id="local", name="Local developer", email="local@localhost", role="admin")

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False, description="A token from `POST /auth/login`.")


def auth_mode() -> Literal["off", "mock"]:
    """The AUTH_MODE setting, or `[auth] mode` in brand.toml."""
    return get_settings().auth_mode or get_meta().auth.mode


def check_settings(settings: Settings) -> None:
    """Refuse to run a production API with demo sign-on or, when tokens are issued, the default
    signing key. With sign-on off there are no tokens, and every request may write."""
    if settings.app_env != "production" or auth_mode() == "off":
        return
    if not settings.auth_allow_mock:
        raise RuntimeError(
            "AUTH_MODE=mock is a demo, not security: set a real AUTH_MODE for production, "
            "or AUTH_ALLOW_MOCK=true for a public demo."
        )
    if settings.auth_secret.get_secret_value() == DEFAULT_AUTH_SECRET:
        raise RuntimeError("AUTH_SECRET is the default; set a long random value for production.")


@lru_cache
def demo_members() -> list[Member]:
    """The brand's demo members, read once per process."""
    path = brand_dir() / "content" / "users.json"
    if not path.exists():
        return []
    return TypeAdapter(list[Member]).validate_python(json.loads(path.read_text()))


def auth_info() -> AuthInfo:
    """What `GET /site` tells the frontends about signing on. Never includes the password."""
    mode = auth_mode()
    return AuthInfo(mode=mode, demo_users=demo_members() if mode == "mock" else [])


def issue(member: Member) -> Session:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.auth_ttl_minutes)
    claims = {**member.model_dump(exclude={"id"}), "sub": member.id, "exp": expires_at}
    token = jwt.encode(claims, settings.auth_secret.get_secret_value(), algorithm=ALGORITHM)
    return Session(token=token, member=member, expires_at=expires_at)


def unauthorised(detail: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"}
    )


def verify(token: str) -> Member:
    """The member a token was issued to; 401 if it is expired, tampered with or malformed."""
    key = get_settings().auth_secret.get_secret_value()
    try:
        claims = jwt.decode(token, key, algorithms=[ALGORITHM], options={"require": ["exp"]})
        return Member(id=claims["sub"], **{k: claims[k] for k in ("name", "email", "role")})
    except jwt.ExpiredSignatureError as exc:
        raise unauthorised("Session expired; sign in again") from exc
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise unauthorised("Invalid token") from exc


async def optional_member(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Member | None:
    """The signed-in member, or None. With sign-on off, always the local member."""
    if auth_mode() == "off":
        return LOCAL_MEMBER
    return verify(credentials.credentials) if credentials else None


async def current_member(member: Annotated[Member | None, Depends(optional_member)]) -> Member:
    """The signed-in member; 401 without one."""
    if member is None:
        raise unauthorised("Sign in first")
    return member


OptionalMember = Annotated[Member | None, Depends(optional_member)]
CurrentMember = Annotated[Member, Depends(current_member)]


def require_role(role: str):
    """A dependency that admits only members with `role`, for admin-only routes."""

    async def check(member: CurrentMember) -> Member:
        if member.role != role:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"Needs the {role} role")
        return member

    return Depends(check)


@router.post("/login", response_model=Session)
async def login(body: LoginIn) -> Session:
    """Sign in as a demo member (mock mode only). Every demo member shares the
    `AUTH_DEMO_PASSWORD`; the response's `token` goes in `Authorization: Bearer <token>`."""
    if auth_mode() != "mock":
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sign-on is off")
    password = get_settings().auth_demo_password.get_secret_value()
    member = next((m for m in demo_members() if m.email.lower() == body.email.lower()), None)
    if member is None or not hmac.compare_digest(body.password.encode(), password.encode()):
        raise unauthorised("Wrong email or password")
    return issue(member)


@router.get("/me", response_model=Member)
async def me(member: CurrentMember) -> Member:
    """The member the bearer token belongs to; 401 without a valid token."""
    return member
