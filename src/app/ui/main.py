"""FastUI web frontend: Python-declared components, React rendering in the browser.
Talks to the API over HTTP only, never to Neo4j. Brand, theme and pages come from GET /site,
the same manifest the mobile app renders, so both frontends stay in step."""

from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastui import AnyComponent, FastUI, prebuilt_html
from fastui import components as c
from fastui.components.display import DisplayLookup
from fastui.events import GoToEvent
from fastui.forms import fastui_form

from app.config import get_settings
from app.meta import get_meta
from app.models import Brand, ContentPage, Item, ItemIn, Section, Site, Theme

app = FastAPI(title=f"{get_meta().slug}-ui")


def api() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=get_settings().api_url, timeout=10)


async def fetch_site() -> Site:
    async with api() as client:
        resp = await client.get("/site")
        resp.raise_for_status()
    return Site.model_validate(resp.json())


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


def shell(site: Site, title: str, components: list[AnyComponent]) -> list[AnyComponent]:
    """Navbar, page and footer around the content; the web twin of the mobile side menu."""
    links = [nav_link(site.welcome.title, "/")]
    links += [nav_link(p.title, f"/p/{p.slug}") for p in site.pages]
    links.append(nav_link("Items", "/items"))
    return [
        c.PageTitle(text=f"{title} · {site.brand.name}"),
        c.Navbar(
            title=site.brand.name,
            title_event=GoToEvent(url="/"),
            start_links=links,
            end_links=[nav_link("About", "/about"), *docs_link(site)],
        ),
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
async def welcome() -> list[AnyComponent]:
    site = await fetch_site()
    return shell(site, site.welcome.title, render_page(site.welcome, site.brand))


@app.get("/api/about", response_model=FastUI, response_model_exclude_none=True)
async def about() -> list[AnyComponent]:
    site = await fetch_site()
    return shell(site, site.about.title, render_page(site.about))


@app.get("/api/p/{slug}", response_model=FastUI, response_model_exclude_none=True)
async def content_page(slug: str) -> list[AnyComponent]:
    site = await fetch_site()
    if (page := site.page(slug)) is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return shell(site, page.title, render_page(page))


@app.get("/api/items", response_model=FastUI, response_model_exclude_none=True)
async def items_page() -> list[AnyComponent]:
    site = await fetch_site()
    async with api() as client:
        resp = await client.get("/items")
        resp.raise_for_status()
    items = [Item.model_validate(i) for i in resp.json()]
    return shell(
        site,
        "Items",
        [
            c.Heading(text="Items", level=2),
            c.Paragraph(text="Add an item; it is stored in Neo4j via the API."),
            c.ModelForm(model=ItemIn, submit_url="/api/items"),
            c.Table(
                data=items,
                data_model=Item,
                columns=[DisplayLookup(field="name"), DisplayLookup(field="created_at")],
            ),
        ],
    )


@app.post("/api/items", response_model=FastUI, response_model_exclude_none=True)
async def create_item(form: Annotated[ItemIn, fastui_form(ItemIn)]) -> list[AnyComponent]:
    async with api() as client:
        resp = await client.post("/items", json=form.model_dump())
        resp.raise_for_status()
    # A unique query string makes FastUI refetch the page; GoToEvent to the current URL is a no-op.
    return [c.FireEvent(event=GoToEvent(url="/items", query={"added": resp.json()["id"]}))]


@app.get("/{path:path}")
async def html_landing() -> HTMLResponse:
    name = get_meta().name
    html = prebuilt_html(title=name)
    try:
        site = await fetch_site()
    except httpx.HTTPError:
        return HTMLResponse(html)  # unthemed shell; the page itself reports the API error
    return HTMLResponse(
        html.replace("</head>", f"{theme_css(site.theme)}</head>", 1).replace(
            f"<title>{name}</title>", f"<title>{site.brand.name}</title>", 1
        )
    )
