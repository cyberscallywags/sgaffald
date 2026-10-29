"""Site manifest loading: brand, theme and pages for every frontend, validated by models.Site."""

from functools import lru_cache
from pathlib import Path

from app.config import get_settings
from app.meta import get_meta
from app.models import Site

DEFAULT_SITE_FILE = Path(__file__).with_name("site.json")


def load_site(path: Path) -> Site:
    """Validate a manifest, filling the brand name and collective from project.toml."""
    site = Site.model_validate_json(path.read_bytes())
    meta = get_meta()
    site.brand.name = site.brand.name or meta.name
    site.brand.collective = site.brand.collective or meta.organisation.name
    return site


@lru_cache
def get_site() -> Site:
    """The manifest named by SITE_FILE, or the bundled sample. Read once per process."""
    return load_site(get_settings().site_file or DEFAULT_SITE_FILE)
