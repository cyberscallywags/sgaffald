"""Item storage: Neo4j for real, or in memory for `uv run task dev` and the unit tests. Both
have the same methods, so the API does not care which it has. Swap/extend these when the real
domain arrives."""

from typing import Protocol

from neo4j import AsyncDriver, AsyncGraphDatabase

from app.config import Settings
from app.models import Item, ItemIn


def make_driver(settings: Settings) -> AsyncDriver:
    return AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password.get_secret_value()),
    )


class ItemStore(Protocol):
    """What the API needs from item storage."""

    async def ping(self) -> bool: ...
    async def ensure_schema(self) -> None: ...
    async def create(self, data: ItemIn, created_by: str | None = None) -> Item: ...
    async def list(self, limit: int = 100) -> list[Item]: ...


class MemoryItemRepo:
    """Items in a list: no database, gone on restart (STORAGE=memory)."""

    def __init__(self) -> None:
        self.items: list[Item] = []

    async def ping(self) -> bool:
        return True

    async def ensure_schema(self) -> None:
        return None

    async def create(self, data: ItemIn, created_by: str | None = None) -> Item:
        item = Item(**data.model_dump(), created_by=created_by)
        self.items.insert(0, item)
        return item

    async def list(self, limit: int = 100) -> list[Item]:
        return self.items[:limit]


class ItemRepo:
    """Items in Neo4j (STORAGE=neo4j, the default)."""

    def __init__(self, driver: AsyncDriver, database: str = "neo4j") -> None:
        self.driver = driver
        self.database = database

    async def ping(self) -> bool:
        try:
            await self.driver.verify_connectivity()
        except Exception:
            return False
        return True

    async def ensure_schema(self) -> None:
        await self.driver.execute_query(
            "CREATE CONSTRAINT item_id IF NOT EXISTS FOR (i:Item) REQUIRE i.id IS UNIQUE",
            database_=self.database,
        )

    async def create(self, data: ItemIn, created_by: str | None = None) -> Item:
        item = Item(**data.model_dump(), created_by=created_by)
        await self.driver.execute_query(
            "CREATE (i:Item {id: $id, name: $name, created_at: $created_at, "
            "created_by: $created_by})",
            item.model_dump(),
            database_=self.database,
        )
        return item

    async def list(self, limit: int = 100) -> list[Item]:
        records, _, _ = await self.driver.execute_query(
            "MATCH (i:Item) RETURN i ORDER BY i.created_at DESC LIMIT $limit",
            limit=limit,
            database_=self.database,
        )
        return [
            Item(
                id=r["i"]["id"],
                name=r["i"]["name"],
                created_at=r["i"]["created_at"].to_native(),
                created_by=r["i"].get("created_by"),
            )
            for r in records
        ]
