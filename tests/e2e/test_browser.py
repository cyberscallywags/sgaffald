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
            "MATCH (i:Item {name: $name}) "
            "RETURN i.id AS id, i.created_at AS created_at, i.created_by AS created_by",
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


@pytest.fixture
def signed_in(page: Page, demo_member, demo_password):
    """Signed in through the web UI's login form; the member's name is in the navbar."""
    page.goto(f"{UI}/login")
    page.get_by_label("Email").fill(demo_member.email)
    page.get_by_label("Password").fill(demo_password)
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_role("link", name=demo_member.name)).to_be_visible()
    return demo_member


def test_ui_welcome_renders_the_site_manifest(page: Page, page_errors):
    site = get_site()
    page.goto(UI)
    expect(page).to_have_title(re.compile(re.escape(site.brand.name)))
    expect(page.get_by_role("heading", name=site.brand.name)).to_be_visible()
    expect(page.get_by_role("heading", name="Planning the application")).to_be_visible()
    page.get_by_role("link", name="About").click()
    expect(page.get_by_role("heading", name=site.about.title)).to_be_visible()
    assert page_errors == []


def test_ui_signed_out_items_page_asks_to_sign_in(page: Page, page_errors):
    page.goto(f"{UI}/items")
    expect(page.get_by_text("Sign in to add an item.")).to_be_visible()
    expect(page.get_by_label("Name")).to_have_count(0)
    page.get_by_role("button", name="Sign in").click()
    expect(page).to_have_url(f"{UI}/login")
    assert page_errors == []


def test_ui_wrong_password_is_shown(page: Page, demo_member):
    page.goto(f"{UI}/login")
    page.get_by_label("Email").fill(demo_member.email)
    page.get_by_label("Password").fill("not-the-password")
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_text("Wrong email or password")).to_be_visible()


def test_ui_account_panel_shows_the_member_and_signs_out(page: Page, signed_in, page_errors):
    page.get_by_role("link", name=signed_in.name).click()
    panel = page.get_by_role("dialog")
    expect(panel).to_contain_text(signed_in.email)
    expect(panel).to_contain_text(f"Role: {signed_in.role}")
    panel.get_by_role("button", name="Sign out").click()
    expect(page.get_by_role("link", name="Sign in")).to_be_visible()
    assert page_errors == []


def test_ui_one_click_demo_sign_in(page: Page, demo_admin):
    page.goto(f"{UI}/login")
    page.get_by_role("button", name=f"{demo_admin.name} ({demo_admin.role})").click()
    expect(page.get_by_role("link", name=demo_admin.name)).to_be_visible()


@pytest.mark.usefixtures("signed_in")
def test_ui_items_page_renders(page: Page, page_errors):
    page.goto(f"{UI}/items")
    expect(page.get_by_label("Name")).to_be_visible()
    expect(page.get_by_role("columnheader", name="Name")).to_be_visible()
    expect(page.get_by_role("columnheader", name="Created At")).to_be_visible()
    assert page_errors == []


def test_ui_form_adds_item_to_table(page: Page, signed_in, page_errors):
    name = f"e2e-{uuid4().hex[:8]}"
    assert items_named(name) == []
    page.goto(f"{UI}/items")
    page.get_by_label("Name").fill(name)
    page.get_by_role("button", name="Submit").click()
    expect(page.get_by_role("cell", name=name)).to_be_visible()
    # Exactly one node, with the server-generated id the UI redirected to
    [node] = items_named(name)
    assert node["id"] and node["created_at"] is not None
    assert node["created_by"] == signed_in.id
    expect(page).to_have_url(re.compile(rf"added={node['id']}"))
    page.reload()
    expect(page.get_by_role("cell", name=name)).to_be_visible()
    assert page_errors == []


@pytest.mark.usefixtures("signed_in")
def test_ui_rejected_submit_writes_nothing(page: Page):
    name = "x" * 201
    page.goto(f"{UI}/items")
    page.get_by_label("Name").fill(name)
    page.get_by_role("button", name="Submit").click()
    expect(page.get_by_text(re.compile("at most 200 characters"))).to_be_visible()
    assert items_named(name) == []


@pytest.mark.usefixtures("signed_in")
def test_ui_requires_name(page: Page):
    page.goto(f"{UI}/items")
    rows = page.get_by_role("row")
    expect(rows.first).to_be_visible()
    before = rows.count()
    page.get_by_role("button", name="Submit").click()
    assert page.get_by_label("Name").evaluate("el => !el.validity.valid")
    expect(rows).to_have_count(before)


def sign_in_to_admin(page: Page, email: str, password: str) -> None:
    page.goto(ADMIN)
    main = page.get_by_test_id("stMain")
    main.get_by_label("Email").fill(email)
    main.get_by_role("textbox", name="Password").fill(password)
    main.get_by_role("button", name="Sign in").click()


def test_admin_turns_away_members_who_are_not_admins(page: Page, demo_member, demo_password):
    sign_in_to_admin(page, demo_member.email, demo_password)
    expect(page.get_by_text("for admin members only")).to_be_visible(timeout=30_000)
    expect(page.get_by_test_id("stDataFrame")).to_have_count(0)


def test_admin_shows_healthy_stack(page: Page, demo_admin, demo_password):
    sign_in_to_admin(page, demo_admin.email, demo_password)
    main = page.get_by_test_id("stMain")
    expect(main.get_by_role("heading", name=f"{get_meta().name} admin")).to_be_visible(
        timeout=30_000
    )
    expect(main.get_by_text('"neo4j":true')).to_be_visible()
    expect(main.get_by_text('"edition":"')).to_be_visible()  # community or enterprise
    expect(page.get_by_test_id("stDataFrame")).to_be_visible()
    expect(page.get_by_test_id("stAlert")).to_have_count(0)
