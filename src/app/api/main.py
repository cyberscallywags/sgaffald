"""FastAPI service: the only thing that writes to the graph (besides admin).

Endpoint docstrings become the OpenAPI descriptions, which feed both the live Swagger UI
at /docs and the generated HTTP reference in the documentation site."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.agent import Deps, build_agent
from app.api import auth
from app.api.auth import CurrentMember
from app.config import get_settings
from app.content import get_site
from app.db import ItemRepo, make_driver
from app.meta import get_meta
from app.models import AskIn, AskOut, Health, Item, ItemIn, Site


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    auth.check_settings(settings)
    driver = make_driver(settings)
    repo = ItemRepo(driver, settings.neo4j_database)
    if await repo.ping():
        await repo.ensure_schema()
    app.state.repo = repo
    app.state.agent = build_agent(settings.llm_model)
    yield
    await driver.close()


meta = get_meta()
app = FastAPI(
    title=f"{meta.slug}-api",
    version=meta.version,
    description=f"Data, content and AI for every {meta.name} frontend. Talks to Neo4j.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(auth.router)


def get_repo(request: Request) -> ItemRepo:
    return request.app.state.repo


Repo = Annotated[ItemRepo, Depends(get_repo)]


@app.get("/health", response_model=Health, tags=["system"])
async def health(repo: Repo) -> Health:
    """Liveness plus Neo4j reachability. `degraded` means the API is up but the graph is not."""
    ok = await repo.ping()
    return Health(status="ok" if ok else "degraded", env=get_settings().app_env, neo4j=ok)


@app.get("/site", response_model=Site, tags=["content"])
async def site() -> Site:
    """Brand, theme and pages shared by the web and mobile frontends, plus the docs link and how
    to sign on."""
    return get_site().model_copy(
        update={"docs_url": get_settings().docs_url or None, "auth": auth.auth_info()}
    )


@app.post("/items", response_model=Item, status_code=201, tags=["items"])
async def create_item(data: ItemIn, repo: Repo, member: CurrentMember) -> Item:
    """Store a new item in Neo4j for the signed-in member; the server assigns `id`,
    `created_at` and `created_by`. Needs a bearer token unless sign-on is off."""
    return await repo.create(data, created_by=member.id)


@app.get("/items", response_model=list[Item], tags=["items"])
async def list_items(repo: Repo, limit: int = 100) -> list[Item]:
    """The most recent items first, at most `limit` of them."""
    return await repo.list(limit=limit)


@app.post("/ask", response_model=AskOut, tags=["ai"], dependencies=[Depends(auth.current_member)])
async def ask(body: AskIn, request: Request, repo: Repo) -> AskOut:
    """Answer a question with the Pydantic AI agent, which can read items from the graph.
    Needs a bearer token unless sign-on is off."""
    result = await request.app.state.agent.run(body.question, deps=Deps(repo=repo))
    return AskOut(answer=result.output)
