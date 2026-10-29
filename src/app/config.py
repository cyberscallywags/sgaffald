"""Single source of configuration for every service. Values come from env vars
(set by docker compose from .env.test or .env.production). Each field's description is
published in the docs' configuration reference (app.docgen)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_core import PydanticUseDefault
from pydantic_settings import BaseSettings, SettingsConfigDict

# A throwaway default; the API refuses it in production (app.api.auth.check_settings).
DEFAULT_AUTH_SECRET = "test-only-signing-key-change-me-in-production"  # noqa: S105


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

    brand_dir: Path | None = Field(
        None,
        description=(
            "Brand folder: `brand.toml` (identity, theme) and `content/site.json` (pages), "
            "served at `GET /site`. Unset means the brand bundled with the package, `brand/`. "
            "Mount another folder and point this at it to re-brand a built image."
        ),
    )

    auth_mode: Literal["off", "mock"] | None = Field(
        None,
        description=(
            "Sign-on. `mock`: demo members from the brand's `content/users.json` sign in with "
            "`AUTH_DEMO_PASSWORD` and get a signed token; writes need one. `off`: every request "
            "is a fixed local member. Unset means `[auth] mode` in `brand.toml`."
        ),
    )
    auth_secret: SecretStr = Field(
        SecretStr(DEFAULT_AUTH_SECRET),
        description="Key that signs sign-on tokens (HS256). Must be changed in production.",
    )
    auth_demo_password: SecretStr = Field(
        SecretStr("demo"), description="The one password every demo member signs in with."
    )
    auth_ttl_minutes: int = Field(480, description="How long a sign-on token lasts.")
    auth_allow_mock: bool = Field(
        False,
        description=(
            "Allow mock sign-on when `APP_ENV=production`, e.g. for a public demo. Without it "
            "the API refuses to start in production with mock sign-on."
        ),
    )

    @field_validator(
        "auth_mode",
        "auth_secret",
        "auth_demo_password",
        "auth_ttl_minutes",
        "auth_allow_mock",
        mode="before",
    )
    @classmethod
    def _empty_means_default(cls, value: object) -> object:
        # docker compose passes an unset variable as "", which should not override a default.
        if value == "":
            raise PydanticUseDefault
        return value

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
