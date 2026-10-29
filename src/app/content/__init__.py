"""Site manifest loading: brand, theme and pages for every frontend, validated by models.Site."""

import json
from functools import lru_cache
from pathlib import Path

from app.meta import brand_dir, get_meta
from app.models import Site


def site_file() -> Path:
    """content/site.json in the brand in use (BRAND_DIR, or the bundled brand)."""
    return brand_dir() / "content" / "site.json"


def load_site(path: Path) -> Site:
    """Validate a manifest, adding the theme from brand.toml and filling the brand name and
    collective from it when the manifest leaves them out."""
    data = json.loads(path.read_bytes())
    if "theme" in data:
        raise ValueError(f"{path}: the theme lives in brand.toml's [theme] table, not site.json")
    meta = get_meta()
    site = Site.model_validate({**data, "theme": meta.theme.model_dump()})
    site.brand.name = site.brand.name or meta.name
    site.brand.collective = site.brand.collective or meta.organisation.name
    return site


@lru_cache
def get_site() -> Site:
    """The manifest of the brand in use. Read once per process."""
    return load_site(site_file())
