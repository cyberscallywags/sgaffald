"""Shared Pydantic models: the contract between API, UI, admin and tests."""

from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class ItemIn(BaseModel):
    """What a client sends to create an item."""

    name: str = Field(min_length=1, max_length=200, examples=["Castell"])


class Item(ItemIn):
    """A stored item, as returned by the API."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str | None = Field(None, description="`id` of the member who added it.")


class Health(BaseModel):
    """API status, where items are stored, and whether Neo4j is reachable."""

    status: str
    env: str
    storage: Literal["neo4j", "memory"] = "neo4j"
    neo4j: bool


# ---------------------------------------------------------------- sign-on
# Mock sign-on (app.api.auth) issues these; a real identity provider would issue the same shapes.

Role = Literal["member", "admin"]
Email = Annotated[str, Field(pattern=r"^[^@\s]+@[^@\s]+$", examples=["ada@example.org"])]


class Member(BaseModel):
    """A signed-in person, as the API and both frontends see them."""

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]*$", examples=["ada"])
    name: str
    email: Email
    role: Role = "member"


class LoginIn(BaseModel):
    """Credentials for `POST /auth/login`. In mock mode every demo member shares one password."""

    email: Email
    password: str = Field(min_length=1, examples=["demo"], json_schema_extra={"format": "password"})


class Session(BaseModel):
    """What `POST /auth/login` returns: send `token` as `Authorization: Bearer <token>`."""

    token: str
    member: Member
    expires_at: datetime


class AuthInfo(BaseModel):
    """How the frontends should offer sign-on, added to `GET /site` by the API."""

    mode: Literal["off", "mock"]
    demo_users: list[Member] = []  # mock mode only: the "Sign in as…" shortcuts


class AskIn(BaseModel):
    """A natural-language question for the agent."""

    question: str = Field(min_length=1, max_length=2000, examples=["What items exist?"])


class AskOut(BaseModel):
    """The agent's answer."""

    answer: str


# ---------------------------------------------------------------- site manifest
# One JSON document (content/site.json) describes the brand, theme and pages. The API serves
# it at GET /site; the FastUI frontend and the mobile app both render from it.

HexColour = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]
Slug = Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]

# Routes the frontends own; a content page may not shadow them.
RESERVED_SLUGS = frozenset({"welcome", "about", "items", "sign-in", "login", "logout", "account"})


class Theme(BaseModel):
    """Brand colours; Ionic colour variables on mobile, Bootstrap overrides on web."""

    primary: HexColour
    secondary: HexColour
    tertiary: HexColour
    font_family: str = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"


class Brand(BaseModel):
    """Project name and tagline, and the collective behind it. Name and collective default to
    brand.toml's when the manifest leaves them out."""

    name: str | None = None
    tagline: str
    collective: str | None = None
    collective_url: str | None = None


class SectionItem(BaseModel):
    """One entry in a list, steps or cards section."""

    title: str
    body: str | None = None
    icon: str | None = None
    url: str | None = None


class Section(BaseModel):
    """A block of a page, rendered the same way on web and mobile."""

    # text: heading + body. list/steps: bullet or numbered items. cards: a grid of items.
    kind: Literal["text", "list", "steps", "cards"] = "text"
    heading: str | None = None
    body: str | None = None
    items: list[SectionItem] = []


class ContentPage(BaseModel):
    """A page built from sections: welcome, about, or a sidebar page at /p/<slug>."""

    slug: Slug
    title: str
    icon: str = "document-text-outline"
    summary: str | None = None
    sections: list[Section] = []


class Site(BaseModel):
    """The site manifest served at GET /site: everything the frontends render."""

    brand: Brand
    theme: Theme
    welcome: ContentPage
    about: ContentPage
    pages: list[ContentPage] = []  # project pages listed in the sidebar, in order
    # Deployment-specific, so it comes from the DOCS_URL setting, not site.json.
    docs_url: str | None = None
    # Added by the API from the sign-on settings; never stored in site.json.
    auth: AuthInfo | None = None

    @model_validator(mode="after")
    def _unique_page_slugs(self) -> Site:
        slugs = [p.slug for p in self.pages]
        if clash := RESERVED_SLUGS.intersection(slugs):
            raise ValueError(f"page slugs are reserved: {sorted(clash)}")
        if len(slugs) != len(set(slugs)):
            raise ValueError("page slugs must be unique")
        return self

    def page(self, slug: str) -> ContentPage | None:
        return next((p for p in self.pages if p.slug == slug), None)
