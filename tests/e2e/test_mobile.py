"""Real-browser checks of the Ionic mobile app on an emulated phone. Requires `task up`
and `playwright install chromium`."""

import os
import re
from uuid import uuid4

import pytest
from neo4j import GraphDatabase
from playwright.sync_api import Page, Playwright, expect

from app.content import get_site

pytestmark = pytest.mark.e2e

MOBILE = os.getenv("MOBILE_URL", "http://localhost:8100")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "sgaffald-test-only")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, playwright: Playwright) -> dict:
    """Every test in this module runs as a touch-screen Android phone."""
    return {**browser_context_args, **playwright.devices["Pixel 7"]}


def count_named(name: str) -> int:
    """Read straight from Neo4j, bypassing the API, so the app cannot fake persistence."""
    with GraphDatabase.driver(NEO4J_URI, auth=("neo4j", NEO4J_PASSWORD)) as driver:
        records, _, _ = driver.execute_query(
            "MATCH (i:Item {name: $name}) RETURN count(i) AS n", name=name
        )
    return records[0]["n"]


@pytest.fixture
def page_errors(page: Page) -> list[str]:
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on("console", lambda msg: msg.type == "error" and errors.append(msg.text))
    return errors


def test_mobile_opens_on_welcome_from_the_site_manifest(page: Page, page_errors):
    site = get_site()
    page.goto(MOBILE)
    expect(page).to_have_title(f"{site.welcome.title} · {site.brand.name}")
    expect(page).to_have_url(re.compile(r"/welcome$"))
    expect(page.get_by_test_id("page-welcome")).to_contain_text(site.brand.name)
    expect(page.get_by_text("Planning the application")).to_be_visible()
    # brand colour from GET /site is applied to Ionic's theme
    primary = page.evaluate(
        "getComputedStyle(document.documentElement).getPropertyValue('--ion-color-primary')"
    )
    assert primary.strip() == site.theme.primary
    assert page_errors == []


def test_mobile_side_menu_reaches_project_pages_and_about(page: Page, page_errors):
    page.goto(f"{MOBILE}/welcome")
    page.locator("ion-menu-button").first.tap()
    page.get_by_test_id("menu").get_by_text("Roadmap").tap()
    expect(page.get_by_test_id("page-roadmap")).to_be_visible()
    page.locator("ion-menu-button").last.tap()
    site = get_site()
    page.locator("ion-menu ion-footer").get_by_text(site.about.title).tap()
    expect(page.get_by_test_id("page-about")).to_contain_text(site.brand.collective)
    assert page_errors == []


def test_mobile_items_shows_healthy_api(page: Page, page_errors):
    page.goto(f"{MOBILE}/items")
    expect(page).to_have_title(f"Items · {get_site().brand.name}")
    expect(page.get_by_test_id("health")).to_contain_text("ok · test")
    assert page.evaluate("matchMedia('(pointer: coarse)').matches")
    assert page_errors == []


def test_mobile_adds_item_through_api(page: Page, page_errors):
    name = f"mobile-{uuid4().hex[:8]}"
    page.goto(f"{MOBILE}/items")
    page.get_by_label("Name").fill(name)
    page.get_by_role("button", name="Add").tap()
    expect(page.get_by_test_id("items")).to_contain_text(name)
    assert count_named(name) == 1
    page.reload()
    expect(page.get_by_test_id("items")).to_contain_text(name)
    assert page_errors == []


def test_mobile_blank_submit_writes_nothing(page: Page):
    posts: list[str] = []
    page.on("request", lambda r: r.method == "POST" and posts.append(r.url))
    page.goto(f"{MOBILE}/items")
    expect(page.get_by_test_id("health")).to_contain_text("ok")
    page.get_by_role("button", name="Add").tap()
    expect(page.locator("ion-input")).to_have_class(re.compile(r"\bion-touched\b"))
    assert posts == []
