import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.content import load_site, site_file
from app.meta import get_meta
from app.models import Site

ROOT = Path(__file__).parents[2]


def sample() -> dict:
    """The bundled manifest, as GET /site serves it: with the theme from brand.toml."""
    return json.loads(site_file().read_text())


def served() -> dict:
    return sample() | {"theme": get_meta().theme.model_dump()}


def test_bundled_sample_is_valid():
    site = load_site(site_file())
    assert site.brand.name == get_meta().name
    assert site.pages, "the sample should show at least one sidebar page"


def test_a_manifest_can_override_the_project_identity(tmp_path):
    data = sample()
    data["brand"] |= {"name": "Prosiect", "collective": "Criw"}
    custom = tmp_path / "site.json"
    custom.write_text(json.dumps(data))
    brand = load_site(custom).brand
    assert (brand.name, brand.collective) == ("Prosiect", "Criw")


def test_page_lookup_by_slug():
    site = load_site(site_file())
    first = site.pages[0]
    assert site.page(first.slug) is first
    assert site.page("missing") is None


@pytest.mark.parametrize("slug", ["about", "items", "sign-in", "welcome"])
def test_pages_cannot_shadow_app_routes(slug):
    data = served()
    data["pages"][0]["slug"] = slug
    with pytest.raises(ValidationError, match="reserved"):
        Site.model_validate(data)


def test_page_slugs_must_be_unique():
    data = served()
    data["pages"].append(dict(data["pages"][0]))
    with pytest.raises(ValidationError, match="unique"):
        Site.model_validate(data)


@pytest.mark.parametrize("colour", ["red", "#fff", "#12345g"])
def test_theme_colours_are_six_digit_hex(colour):
    data = sample() | {"theme": {"primary": colour, "secondary": "#000000", "tertiary": "#000000"}}
    with pytest.raises(ValidationError):
        Site.model_validate(data)


def test_the_theme_comes_from_brand_toml():
    site = load_site(site_file())
    assert site.theme == get_meta().theme
    assert "theme" not in sample(), "the theme lives in brand.toml, not site.json"


def test_a_theme_left_in_site_json_is_an_error(tmp_path):
    custom = tmp_path / "site.json"
    custom.write_text(json.dumps(sample() | {"theme": {"primary": "#000000"}}))
    with pytest.raises(ValueError, match="brand.toml"):
        load_site(custom)


@pytest.fixture
def brand(monkeypatch):
    """Point BRAND_DIR at another brand for one test, then put everything back."""
    from app import content, meta
    from app.config import get_settings

    def use(path):
        monkeypatch.setenv("BRAND_DIR", str(path))
        for cached in (get_settings, meta.get_meta, content.get_site):
            cached.cache_clear()

    yield use
    monkeypatch.undo()
    for cached in (get_settings, meta.get_meta, content.get_site):
        cached.cache_clear()


def test_brand_dir_setting_swaps_identity_theme_and_pages(brand):
    from app.content import get_site
    from app.meta import get_meta as current_meta

    brand(ROOT / "examples/brands/neutral")
    site = get_site()
    assert current_meta().name == "Example Project"
    assert site.brand.name == "Example Project"
    assert site.theme.primary == "#264653"
    assert site.about.title == "About"


def test_a_brand_folder_can_be_copied_and_edited(brand, tmp_path):
    import shutil

    shutil.copytree(ROOT / "examples/brands/neutral", tmp_path / "ours")
    page = tmp_path / "ours/content/site.json"
    data = json.loads(page.read_text())
    data["brand"]["name"] = "Prosiect"
    page.write_text(json.dumps(data))
    brand(tmp_path / "ours")
    from app.content import get_site

    assert get_site().brand.name == "Prosiect"
