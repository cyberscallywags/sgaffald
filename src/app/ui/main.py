"""FastUI web frontend: Python-declared components, React rendering in the browser.
Talks to the API over HTTP only, never to Neo4j. Brand, theme and pages come from GET /site,
the same manifest the mobile app renders, so both frontends stay in step.

Sign-on: /login posts to the API's /auth/login and keeps the token in an HttpOnly cookie, so
the browser's scripts never see it; every API call this server makes forwards it as a bearer
token. The navbar shows who is signed in and opens an account panel (FastUI has no dropdown,
so the panel is a Modal opened by a PageEvent)."""

from pathlib import Path
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastui import AnyComponent, FastUI, prebuilt_html
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent, PageEvent
from fastui.forms import fastui_form

from app import domain
from app.config import get_settings
from app.meta import get_meta
from app.models import Brand, ContentPage, Item, ItemIn, LoginIn, Member, Section, Site, Theme

app = FastAPI(title=f"{get_meta().slug}-ui")

# The brand's favicon and mark, copied here from brand/images by `uv run task sync`.
STATIC = Path(__file__).with_name("static")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def static_file(stem: str) -> str | None:
    """URL of the brand image copied as static/<stem>.<ext>, if the brand has one."""
    return next((f"/static/{p.name}" for p in sorted(STATIC.glob(f"{stem}.*"))), None)


SESSION_COOKIE = f"{get_meta().slug}_session"


def api(token: str | None = None) -> httpx.AsyncClient:
    """A client for the API, sending the member's token when there is one."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.AsyncClient(base_url=get_settings().api_url, timeout=10, headers=headers)


def session_token(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE)


Token = Annotated[str | None, Depends(session_token)]


async def fetch_site() -> Site:
    async with api() as client:
        resp = await client.get("/site")
        resp.raise_for_status()
    return Site.model_validate(resp.json())


async def fetch_member(site: Site, token: str | None) -> Member | None:
    """Who the session cookie belongs to; None when signed out, expired, or sign-on is off."""
    if not token or not site.auth or site.auth.mode != "mock":
        return None
    async with api(token) as client:
        resp = await client.get("/auth/me")
    return Member.model_validate(resp.json()) if resp.status_code == 200 else None


def can_write(site: Site, member: Member | None) -> bool:
    return member is not None or not site.auth or site.auth.mode == "off"


def account_link(site: Site, member: Member | None) -> list[c.Link]:
    """Signed in: the member's name, which opens the account panel. Signed out: Sign in."""
    if not site.auth or site.auth.mode == "off":
        return []
    if member:
        return [c.Link(components=[c.Text(text=member.name)], on_click=PageEvent(name="account"))]
    return [nav_link("Sign in", "/login")]


def account_panel(member: Member | None) -> list[AnyComponent]:
    if member is None:
        return []
    return [
        c.Modal(
            title=member.name,
            body=[c.Paragraph(text=member.email), c.Paragraph(text=f"Role: {member.role}")],
            footer=[c.Button(text="Sign out", on_click=GoToEvent(url="/logout"))],
            open_trigger=PageEvent(name="account"),
        )
    ]


def nav_link(text: str, url: str) -> c.Link:
    active = "/" if url == "/" else f"startswith:{url}"
    return c.Link(components=[c.Text(text=text)], on_click=GoToEvent(url=url), active=active)


def docs_link(site: Site) -> list[c.Link]:
    """The docs portal opens in a new tab; no link when DOCS_URL is empty."""
    if not site.docs_url:
        return []
    return [
        c.Link(
            components=[c.Text(text="Docs")],
            on_click=GoToEvent(url=site.docs_url, target="_blank"),
        )
    ]


def shell(
    site: Site, title: str, components: list[AnyComponent], member: Member | None = None
) -> list[AnyComponent]:
    """Navbar, page and footer around the content; the web twin of the mobile side menu."""
    links = [nav_link(site.welcome.title, "/")]
    links += [nav_link(p.title, f"/p/{p.slug}") for p in site.pages]
    links.append(nav_link("Items", "/items"))
    links += [nav_link(module.TITLE, module.PATH) for module in domain.modules()]
    return [
        c.PageTitle(text=f"{title} · {site.brand.name}"),
        c.Navbar(
            title=site.brand.name,
            title_event=GoToEvent(url="/"),
            start_links=links,
            end_links=[nav_link("About", "/about"), *docs_link(site), *account_link(site, member)],
        ),
        *account_panel(member),
        c.Page(components=components),
        c.Footer(links=[], extra_text=f"{site.brand.name} · a {site.brand.collective} project"),
    ]


def render_section(section: Section) -> list[AnyComponent]:
    out: list[AnyComponent] = []
    if section.heading:
        out.append(c.Heading(text=section.heading, level=3, class_name="mt-4"))
    if section.body:
        out.append(c.Paragraph(text=section.body))
    match section.kind:
        case "list" | "steps":
            marker = "1." if section.kind == "steps" else "-"
            lines = [
                f"{marker} **{i.title}**" + (f" — {i.body}" if i.body else "")
                for i in section.items
            ]
            out.append(c.Markdown(text="\n".join(lines)))
        case "cards":
            cards = [
                c.Div(
                    class_name="col-md-6 col-lg-4",
                    components=[
                        c.Div(
                            class_name="card card-body h-100 brand-card",
                            components=[
                                c.Heading(text=i.title, level=5),
                                *([c.Paragraph(text=i.body)] if i.body else []),
                            ],
                        )
                    ],
                )
                for i in section.items
            ]
            out.append(c.Div(class_name="row g-3", components=cards))
    return out


def render_page(page: ContentPage, brand: Brand | None = None) -> list[AnyComponent]:
    """With a brand, opens on its name and tagline, like the mobile welcome hero."""
    out: list[AnyComponent] = [c.Heading(text=brand.name if brand else page.title, level=2)]
    if brand and brand.tagline:
        out.append(c.Paragraph(text=brand.tagline, class_name="lead fw-semibold"))
    if page.summary:
        out.append(c.Paragraph(text=page.summary, class_name="lead"))
    for section in page.sections:
        out.extend(render_section(section))
    return out


def brand_head(theme: Theme) -> str:
    """Favicon link, and brand colours as Bootstrap overrides (the mobile app maps the same
    values to Ionic). The navbar title gets the brand mark as a CSS background, because
    FastUI's Navbar title is text only."""
    icon = static_file("favicon")
    mark = static_file("mark")
    link = f'<link rel="icon" href="{icon}">' if icon else ""
    logo = (
        f".navbar-brand {{ padding-left: 2.25rem; background: url('{mark}') left center / "
        "1.75rem no-repeat; }}"
        if mark
        else ""
    )
    return link + theme_css(theme).replace("</style>", f"{logo}\n</style>")


def theme_css(theme: Theme) -> str:
    """Brand colours as Bootstrap overrides; the mobile app maps the same values to Ionic."""
    return f"""<style>
:root {{ --brand-primary: {theme.primary}; --brand-secondary: {theme.secondary};
  --brand-tertiary: {theme.tertiary}; --bs-link-color: {theme.primary};
  --bs-body-font-family: {theme.font_family}; }}
.navbar {{ background: var(--brand-primary) !important; }}
.navbar, .navbar a, .navbar .navbar-brand {{ color: #fff !important; }}
.navbar .nav-link.active {{ border-bottom: 2px solid var(--brand-tertiary); }}
.btn-primary {{ --bs-btn-bg: var(--brand-primary); --bs-btn-border-color: var(--brand-primary);
  --bs-btn-hover-bg: var(--brand-secondary); --bs-btn-hover-border-color: var(--brand-secondary); }}
h2, h3 {{ color: var(--brand-primary); }}
.brand-card {{ border-top: 4px solid var(--brand-tertiary); }}
</style>"""


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/", response_model=FastUI, response_model_exclude_none=True)
@app.get("/api/welcome", response_model=FastUI, response_model_exclude_none=True)
async def welcome(token: Token) -> list[AnyComponent]:
    site = await fetch_site()
    member = await fetch_member(site, token)
    return shell(site, site.welcome.title, render_page(site.welcome, site.brand), member)


@app.get("/api/about", response_model=FastUI, response_model_exclude_none=True)
async def about(token: Token) -> list[AnyComponent]:
    site = await fetch_site()
    return shell(site, site.about.title, render_page(site.about), await fetch_member(site, token))


@app.get("/api/p/{slug}", response_model=FastUI, response_model_exclude_none=True)
async def content_page(slug: str, token: Token) -> list[AnyComponent]:
    site = await fetch_site()
    if (page := site.page(slug)) is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return shell(site, page.title, render_page(page), await fetch_member(site, token))


@app.get("/api/items", response_model=FastUI, response_model_exclude_none=True)
async def items_page(token: Token) -> list[AnyComponent]:
    site = await fetch_site()
    member = await fetch_member(site, token)
    async with api() as client:
        resp = await client.get("/items")
        resp.raise_for_status()
    items = [Item.model_validate(i) for i in resp.json()]
    if can_write(site, member):
        add: list[AnyComponent] = [
            c.Paragraph(text="Add an item; it is stored in Neo4j via the API."),
            c.ModelForm(model=ItemIn, submit_url="/api/items"),
        ]
    else:
        add = [
            c.Paragraph(text="Sign in to add an item."),
            c.Button(text="Sign in", on_click=GoToEvent(url="/login")),
        ]
    return shell(
        site,
        "Items",
        [
            c.Heading(text="Items", level=2),
            *add,
            c.Table(
                data=items,
                data_model=Item,
                columns=[DisplayLookup(field="name"), DisplayLookup(field="created_at")],
            ),
        ],
        member,
    )


@app.post("/api/items", response_model=FastUI, response_model_exclude_none=True)
async def create_item(
    form: Annotated[ItemIn, fastui_form(ItemIn)], token: Token
) -> list[AnyComponent]:
    async with api(token) as client:
        resp = await client.post("/items", json=form.model_dump())
    if resp.status_code == 401:
        return [c.FireEvent(event=GoToEvent(url="/login"))]
    resp.raise_for_status()
    # A unique query string makes FastUI refetch the page; GoToEvent to the current URL is a no-op.
    return [c.FireEvent(event=GoToEvent(url="/items", query={"added": resp.json()["id"]}))]


# ---------------------------------------------------------------- sign-on


def form_error(field: str, message: str) -> HTTPException:
    """The 422 shape FastUI forms show next to the field."""
    return HTTPException(422, detail={"form": [{"loc": [field], "msg": message}]})


def start_session(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.auth_ttl_minutes * 60,
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
    )


async def sign_in(response: Response, email: str, password: str) -> list[AnyComponent]:
    async with api() as client:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
    if resp.status_code == 404:
        raise form_error("email", "Sign-on is off")
    if resp.status_code == 401:
        raise form_error("password", "Wrong email or password")
    resp.raise_for_status()
    start_session(response, resp.json()["token"])
    return [c.FireEvent(event=GoToEvent(url="/welcome"))]


@app.get("/api/login", response_model=FastUI, response_model_exclude_none=True)
async def login_page(token: Token) -> list[AnyComponent]:
    site = await fetch_site()
    if not site.auth or site.auth.mode != "mock":
        body: list[AnyComponent] = [c.Paragraph(text="Sign-on is off: everyone can add items.")]
    else:
        demo = [
            c.Button(
                text=f"{u.name} ({u.role})",
                on_click=GoToEvent(url=f"/login/as/{u.id}"),
                named_style="secondary",
                class_name="me-2 mb-2",
            )
            for u in site.auth.demo_users
        ]
        body = [
            c.Paragraph(
                text="This is a demo sign-on: every demo member's password is the same "
                "(`demo` unless AUTH_DEMO_PASSWORD says otherwise)."
            ),
            c.ModelForm(
                model=LoginIn,
                submit_url="/api/login",
                footer=[c.Button(text="Sign in", html_type="submit")],
            ),
            *([c.Heading(text="Sign in as…", level=4, class_name="mt-4"), *demo] if demo else []),
        ]
    return shell(
        site,
        "Sign in",
        [c.Heading(text="Sign in", level=2), *body],
        await fetch_member(site, token),
    )


@app.post("/api/login", response_model=FastUI, response_model_exclude_none=True)
async def login(
    form: Annotated[LoginIn, fastui_form(LoginIn)], response: Response
) -> list[AnyComponent]:
    return await sign_in(response, form.email, form.password)


@app.get("/api/login/as/{member_id}", response_model=FastUI, response_model_exclude_none=True)
async def login_as(member_id: str, response: Response) -> list[AnyComponent]:
    """One-click sign-in as a demo member: mock sign-on only, with the shared demo password."""
    site = await fetch_site()
    users = site.auth.demo_users if site.auth else []
    if (member := next((u for u in users if u.id == member_id), None)) is None:
        raise HTTPException(status_code=404, detail="No such demo member")
    password = get_settings().auth_demo_password.get_secret_value()
    return await sign_in(response, member.email, password)


@app.get("/api/logout", response_model=FastUI, response_model_exclude_none=True)
async def logout(response: Response) -> list[AnyComponent]:
    response.delete_cookie(SESSION_COOKIE)
    # FastUI's GoToEvent applies `query` to the current path and ignores `url`, so a query
    # here would log out again; /welcome is a different path from /logout and /login.
    return [c.FireEvent(event=GoToEvent(url="/welcome"))]


# ---------------------------------------------------------------- app.domain entities
# One list-and-add page per module added with `uv run task new_entity`, before the catch-all.


def add_entity_pages(module) -> None:
    model, model_in, title, path = module.MODEL, module.MODEL_IN, module.TITLE, module.PATH

    async def page(token: Token) -> list[AnyComponent]:
        site = await fetch_site()
        member = await fetch_member(site, token)
        async with api() as client:
            resp = await client.get(path)
            resp.raise_for_status()
        rows = [model.model_validate(row) for row in resp.json()]
        if can_write(site, member):
            add: list[AnyComponent] = [c.ModelForm(model=model_in, submit_url=f"/api{path}")]
        else:
            add = [c.Button(text="Sign in to add one", on_click=GoToEvent(url="/login"))]
        columns = [DisplayLookup(field=name) for name in model_in.model_fields]
        table = c.Table(data=rows, data_model=model, columns=columns) if rows else None
        empty = c.Paragraph(text=f"No {title.lower()} yet.")
        return shell(site, title, [c.Heading(text=title, level=2), *add, table or empty], member)

    async def create(
        form: Annotated[model_in, fastui_form(model_in)], token: Token
    ) -> list[AnyComponent]:
        async with api(token) as client:
            resp = await client.post(path, json=form.model_dump(mode="json"))
        if resp.status_code == 401:
            return [c.FireEvent(event=GoToEvent(url="/login"))]
        resp.raise_for_status()
        return [c.FireEvent(event=GoToEvent(url=path, query={"added": resp.json()["id"]}))]

    options = {"response_model": FastUI, "response_model_exclude_none": True}
    app.add_api_route(f"/api{path}", page, methods=["GET"], **options)
    app.add_api_route(f"/api{path}", create, methods=["POST"], **options)


for _module in domain.modules():
    add_entity_pages(_module)


@app.get("/{path:path}")
async def html_landing() -> HTMLResponse:
    name = get_meta().name
    html = prebuilt_html(title=name)
    try:
        site = await fetch_site()
    except httpx.HTTPError:
        return HTMLResponse(html)  # unthemed shell; the page itself reports the API error
    return HTMLResponse(
        html.replace("</head>", f"{brand_head(site.theme)}</head>", 1).replace(
            f"<title>{name}</title>", f"<title>{site.brand.name}</title>", 1
        )
    )
