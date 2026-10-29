"""Project identity from brand/brand.toml: name, organisation, repository, app id and theme. The
version comes from the installed distribution (pyproject.toml). Pages and copy are
content/site.json's job; see app.content."""

import tomllib
from functools import lru_cache
from importlib.metadata import packages_distributions, version
from pathlib import Path

from pydantic import BaseModel, Field

from app.config import get_settings
from app.models import Theme

# Wheels carry a copy of the brand (pyproject.toml force-include); a checkout reads brand/.
_PACKAGED = Path(__file__).with_name("brand")
DEFAULT_BRAND_DIR = _PACKAGED if _PACKAGED.exists() else Path(__file__).parents[2] / "brand"


def brand_dir() -> Path:
    """The brand in use: the BRAND_DIR setting, or the bundled one."""
    return get_settings().brand_dir or DEFAULT_BRAND_DIR


class Organisation(BaseModel):
    """The collective behind the project."""

    name: str
    url: str | None = None
    motto: str | None = None


class Repository(BaseModel):
    """Where the code lives on GitHub."""

    owner: str
    name: str

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.name}"

    @property
    def image_prefix(self) -> str:
        """Release images, as published by .github/workflows/release.yml."""
        return f"ghcr.io/{self.owner}/{self.name}".lower()


class Mobile(BaseModel):
    """Native app identity."""

    app_id: str


class Meta(BaseModel):
    """Everything in brand.toml that the services use, plus the package version."""

    name: str
    slug: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    description: str
    year: int
    version: str
    organisation: Organisation
    repository: Repository
    mobile: Mobile
    theme: Theme  # [theme.docs] is for the docs build only (scripts/sync_meta.py)


def package_version() -> str:
    """The installed distribution's version. The import package is always `app`; the
    distribution is named after the slug, so look it up rather than assume the name."""
    (dist, *_) = packages_distributions().get(__package__, [__package__])
    return version(dist)


def load_meta(path: Path) -> Meta:
    raw = tomllib.loads(path.read_text())
    return Meta(**raw.pop("project"), **raw, version=package_version())


@lru_cache
def get_meta() -> Meta:
    """brand.toml, read once per process."""
    return load_meta(brand_dir() / "brand.toml")
