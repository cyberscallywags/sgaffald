"""Real-browser checks of the docs site: the brand's palette and scheme, and images that scale
from a phone to a desktop. Requires `task up` (or `task docs_serve`) and
`playwright install chromium`."""

import os
import tomllib

import pytest
from playwright.sync_api import Page, expect

from app.meta import brand_dir, get_meta

pytestmark = pytest.mark.e2e

DOCS = os.getenv("DOCS_URL", "http://localhost:8200")
PALETTE = tomllib.loads((brand_dir() / "brand.toml").read_text())["theme"].get("docs", {})
DARK_FIRST = PALETTE.get("scheme", "dark") == "dark"
BACKGROUND = PALETTE.get("background", "#0b0e14")  # the default in scripts/sync_meta.py
NIGHT = "rgb({}, {}, {})".format(*(int(BACKGROUND[i : i + 2], 16) for i in (1, 3, 5)))

PAGES = {
    "portal home": "/",
    "portal about": "/about/",
    "manual home": "/manual/manual.html",
    "manual about": "/manual/about.html",
}


def fits_the_screen(page: Page) -> None:
    """No sideways scrolling, and every image inside the viewport width."""
    page.wait_for_load_state("networkidle")
    width = page.evaluate("window.innerWidth")
    assert page.evaluate("document.documentElement.scrollWidth") <= width
    for box in page.locator("article img, .md-content img").evaluate_all(
        "imgs => imgs.map(i => i.getBoundingClientRect().width)"
    ):
        assert 0 < box <= width


@pytest.mark.parametrize("path", PAGES.values(), ids=PAGES.keys())
@pytest.mark.parametrize("viewport", [(390, 844), (1280, 800)], ids=["phone", "desktop"])
def test_images_scale_with_the_page(page: Page, path: str, viewport):
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(f"{DOCS}{path}")
    fits_the_screen(page)


@pytest.mark.skipif(not DARK_FIRST, reason="the brand's docs open in the light scheme")
def test_portal_is_dark_first_with_the_brand_hero(page: Page):
    page.goto(DOCS)
    expect(page.locator(".brand-hero h1")).to_have_text(f"{get_meta().name}¶")
    assert page.evaluate("getComputedStyle(document.body).backgroundColor") == NIGHT
    crest = page.locator(".brand-hero__crest img")
    if crest.count():
        expect(crest).to_be_visible()
        assert "/assets/brand/" in crest.evaluate("img => img.currentSrc")


@pytest.mark.skipif(not DARK_FIRST, reason="the brand's docs open in the light scheme")
def test_manual_is_dark_first_and_links_back_to_the_portal(page: Page):
    page.goto(f"{DOCS}/manual/")
    expect(page).to_have_url(f"{DOCS}/manual/manual.html")
    assert page.evaluate("getComputedStyle(document.body).backgroundColor") == NIGHT
    page.get_by_role("link", name=f"{get_meta().name} docs portal").click()
    expect(page).to_have_url(f"{DOCS}/")
