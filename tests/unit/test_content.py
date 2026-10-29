import json

import pytest
from pydantic import ValidationError

from app.content import DEFAULT_SITE_FILE, load_site
from app.meta import get_meta
from app.models import Site


def sample() -> dict:
    return json.loads(DEFAULT_SITE_FILE.read_text())


def test_bundled_sample_is_valid():
    site = load_site(DEFAULT_SITE_FILE)
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
    site = load_site(DEFAULT_SITE_FILE)
    first = site.pages[0]
    assert site.page(first.slug) is first
    assert site.page("missing") is None


@pytest.mark.parametrize("slug", ["about", "items", "sign-in", "welcome"])
def test_pages_cannot_shadow_app_routes(slug):
    data = sample()
    data["pages"][0]["slug"] = slug
    with pytest.raises(ValidationError, match="reserved"):
        Site.model_validate(data)


def test_page_slugs_must_be_unique():
    data = sample()
    data["pages"].append(dict(data["pages"][0]))
    with pytest.raises(ValidationError, match="unique"):
        Site.model_validate(data)


@pytest.mark.parametrize("colour", ["red", "#fff", "#12345g"])
def test_theme_colours_are_six_digit_hex(colour):
    data = sample()
    data["theme"]["primary"] = colour
    with pytest.raises(ValidationError):
        Site.model_validate(data)


def test_site_file_setting_overrides_sample(tmp_path, monkeypatch):
    from app import content
    from app.config import get_settings

    data = sample()
    data["brand"]["name"] = "Prosiect"
    custom = tmp_path / "site.json"
    custom.write_text(json.dumps(data))
    monkeypatch.setenv("SITE_FILE", str(custom))
    get_settings.cache_clear()
    content.get_site.cache_clear()
    try:
        assert content.get_site().brand.name == "Prosiect"
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
        content.get_site.cache_clear()
