"""Demo members for the browser tests, from the brand's content/users.json."""

import os

import pytest

from app.api.auth import demo_members
from app.models import Member


@pytest.fixture(scope="session")
def demo_password() -> str:
    return os.getenv("AUTH_DEMO_PASSWORD", "demo")


@pytest.fixture(scope="session")
def demo_admin() -> Member:
    return next(m for m in demo_members() if m.role == "admin")


@pytest.fixture(scope="session")
def demo_member() -> Member:
    return next(m for m in demo_members() if m.role == "member")
