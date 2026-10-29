from importlib.util import find_spec

import pytest

from app.db import MemoryItemRepo

# The browser tests import Playwright, which only the `e2e` dependency group installs.
if find_spec("playwright") is None:
    collect_ignore = ["e2e"]


class FakeRepo(MemoryItemRepo):
    """The in-memory repository, plus a switch to make Neo4j look unreachable."""

    def __init__(self, healthy: bool = True) -> None:
        super().__init__()
        self.healthy = healthy

    async def ping(self) -> bool:
        return self.healthy


@pytest.fixture
def fake_repo() -> FakeRepo:
    return FakeRepo()


@pytest.fixture
def mock_sign_on(monkeypatch):
    """Turn mock sign-on on for one test, whatever brand.toml says."""
    from app.api.auth import demo_members
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "auth_mode", "mock")
    demo_members.cache_clear()
    yield
    demo_members.cache_clear()
