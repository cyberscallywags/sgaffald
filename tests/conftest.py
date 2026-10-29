from importlib.util import find_spec

import pytest

from app.models import Item, ItemIn

# The browser tests import Playwright, which only the `e2e` dependency group installs.
if find_spec("playwright") is None:
    collect_ignore = ["e2e"]


class FakeRepo:
    """In-memory stand-in for ItemRepo so unit tests never touch Neo4j."""

    def __init__(self, healthy: bool = True) -> None:
        self.items: list[Item] = []
        self.healthy = healthy

    async def ping(self) -> bool:
        return self.healthy

    async def ensure_schema(self) -> None:
        return None

    async def create(self, data: ItemIn) -> Item:
        item = Item(**data.model_dump())
        self.items.insert(0, item)
        return item

    async def list(self, limit: int = 100) -> list[Item]:
        return self.items[:limit]


@pytest.fixture
def fake_repo() -> FakeRepo:
    return FakeRepo()
