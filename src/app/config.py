"""Single source of configuration for every service. Values come from env vars
(set by docker compose from .env.test or .env.production). Each field's description is
published in the docs' configuration reference (app.docgen)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["test", "production"] = Field(
        "test", description="Which environment the services run in; shown by `GET /health`."
    )

    neo4j_uri: str = Field("bolt://localhost:7687", description="Bolt URI of the Neo4j server.")
    neo4j_user: str = Field("neo4j", description="Neo4j user for the API and admin.")
    neo4j_password: SecretStr = Field(
        SecretStr("change-me-please"), description="Neo4j password. Never commit a real one."
    )
    neo4j_database: str = Field("neo4j", description="Neo4j database name.")

    llm_model: str = Field(
        "test",
        description=(
            "Pydantic AI model behind `POST /ask`. `test` is the offline TestModel; in "
            "production use e.g. `anthropic:claude-sonnet-4-5` and add the matching "
            "`pydantic-ai-slim` extra."
        ),
    )

    api_url: str = Field(
        "http://localhost:8000", description="Where the UI and admin reach the API."
    )

    cors_origins: list[str] = Field(
        [],
        description=(
            "JSON list of browser origins allowed to call the API directly, e.g. a native "
            'Capacitor build (`["capacitor://localhost"]`). The UI and mobile web image reach '
            "the API server-side and need none."
        ),
    )

    site_file: Path | None = Field(
        None,
        description=(
            "Site manifest (brand, theme, pages) served at `GET /site`. Unset means the "
            "bundled sample, `src/app/content/site.json`."
        ),
    )

    docs_url: str | None = Field(
        "http://localhost:8200",
        description=(
            "Public URL of the documentation portal. Sent to the frontends in `GET /site` "
            "so the web navbar and mobile menu can link to it; empty hides the link."
        ),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
