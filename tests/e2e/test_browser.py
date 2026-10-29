"""Real-browser checks of the UI and admin portal. Requires `task up` and
`playwright install chromium`."""

import os
import re
from uuid import uuid4

import pytest
from neo4j import GraphDatabase
from playwright.sync_api import Page, expect

from app.content import get_site
from app.meta import get_meta

pytestmark = pytest.mark.e2e

UI = os.getenv("UI_URL", "http://localhost:8080")
ADMIN = os.getenv("ADMIN_URL", "http://localhost:8501")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "sgaffald-test-only")


def items_named(name: str) -> list[dict]:
    """Read straight from Neo4j, bypassing the API, so the UI cannot fake persistence."""
    with GraphDatabase.driver(NEO4J_URI, auth=("neo4j", NEO4J_PASSWORD)) as driver:
        records, _, _ = driver.execute_query(
            "MATCH (i:Item {name: $name}) RETURN i.id AS id, i.created_at AS created_at",
            name=name,
        )
    return [r.data() for r in records]


@pytest.fixture
def page_errors(page: Page) -> list[str]:
    """JS exceptions and console errors raised while the test runs."""
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on("console", lambda msg: msg.type == "error" and errors.append(msg.text))
    return errors


def test_ui_welcome_renders_the_site_manifest(page: Page, page_errors):
    site = get_site()
    page.goto(UI)
    expect(page).to_have_title(re.compile(re.escape(site.brand.name)))
    expect(page.get_by_role("heading", name=site.brand.name)).to_be_visible()
    expect(page.get_by_role("heading", name="Planning the application")).to_be_visible()
    page.get_by_role("link", name="About").click()
    expect(page.get_by_role("heading", name=site.about.title)).to_be_visible()
    assert page_errors == []


def test_ui_items_page_renders(page: Page, page_errors):
    page.goto(f"{UI}/items")
    expect(page.get_by_label("Name")).to_be_visible()
    expect(page.get_by_role("columnheader", name="Name")).to_be_visible()
    expect(page.get_by_role("columnheader", name="Created At")).to_be_visible()
    assert page_errors == []


def test_ui_form_adds_item_to_table(page: Page, page_errors):
    name = f"e2e-{uuid4().hex[:8]}"
    assert items_named(name) == []
    page.goto(f"{UI}/items")
    page.get_by_label("Name").fill(name)
    page.get_by_role("button", name="Submit").click()
    expect(page.get_by_role("cell", name=name)).to_be_visible()
    # Exactly one node, with the server-generated id the UI redirected to
    [node] = items_named(name)
    assert node["id"] and node["created_at"] is not None
    expect(page).to_have_url(re.compile(rf"added={node['id']}"))
    page.reload()
    expect(page.get_by_role("cell", name=name)).to_be_visible()
    assert page_errors == []


def test_ui_rejected_submit_writes_nothing(page: Page):
    name = "x" * 201
    page.goto(f"{UI}/items")
    page.get_by_label("Name").fill(name)
    page.get_by_role("button", name="Submit").click()
    expect(page.get_by_text(re.compile("at most 200 characters"))).to_be_visible()
    assert items_named(name) == []


def test_ui_requires_name(page: Page):
    page.goto(f"{UI}/items")
    rows = page.get_by_role("row")
    expect(rows.first).to_be_visible()
    before = rows.count()
    page.get_by_role("button", name="Submit").click()
    assert page.get_by_label("Name").evaluate("el => !el.validity.valid")
    expect(rows).to_have_count(before)


def test_admin_shows_healthy_stack(page: Page):
    page.goto(ADMIN)
    main = page.get_by_test_id("stMain")
    expect(main.get_by_role("heading", name=f"{get_meta().name} admin")).to_be_visible(
        timeout=30_000
    )
    expect(main.get_by_text('"neo4j":true')).to_be_visible()
    expect(main.get_by_text('"edition":"enterprise"')).to_be_visible()
    expect(page.get_by_test_id("stDataFrame")).to_be_visible()
    expect(page.get_by_test_id("stAlert")).to_have_count(0)
