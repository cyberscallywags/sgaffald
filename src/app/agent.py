"""Minimal Pydantic AI agent wired to Neo4j through a dependency.

With LLM_MODEL=test it uses the offline TestModel, so CI never needs an API key."""

from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from app.db import ItemRepo


@dataclass
class Deps:
    repo: ItemRepo


def build_agent(model: str) -> Agent[Deps, str]:
    agent = Agent(
        model,
        deps_type=Deps,
        output_type=str,
        instructions="You answer questions about the items stored in the graph. Be brief.",
    )

    @agent.tool
    async def list_item_names(ctx: RunContext[Deps]) -> list[str]:
        """Return the names of the most recent items in the graph."""
        return [i.name for i in await ctx.deps.repo.list(limit=20)]

    return agent
