"""scripts/sync_meta.py: the copies of project.toml and site.json are current, and follow edits."""

import importlib.util
import json
import re
import shutil
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
_spec = importlib.util.spec_from_file_location("sync_meta", ROOT / "scripts/sync_meta.py")
sync_meta = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_meta)


def test_generated_copies_are_current():
    stale = sync_meta.stale(ROOT)
    assert not stale, f"run `uv run task sync`: {sorted(map(str, stale))}"


@pytest.fixture
def fork(tmp_path) -> Path:
    """A copy of every file sync_meta reads or writes, as if the template had just been forked."""
    files = ["project.toml", "pyproject.toml", "src/app/content/site.json"]
    for rel in [*files, *map(str, sync_meta.OUTPUTS)]:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    return tmp_path


def test_renaming_the_project_updates_every_copy(fork):
    project = fork / "project.toml"
    text = project.read_text()
    # [repository] first, whatever it holds, so the slug swap below cannot touch it
    text = re.sub(r'^owner = ".*"', 'owner = "Criw"', text, flags=re.M)
    text = re.sub(r'(\[repository\][^\[]*?^name = )"[^"]*"', r'\1"Castell"', text, flags=re.M)
    for old, new in [('"Sgaffald"', '"Castell"'), ('"sgaffald"', '"castell"')]:
        text = text.replace(old, new)
    project.write_text(text)

    assert sync_meta.main(["--root", str(fork)]) == 0
    assert sync_meta.main(["--root", str(fork), "--check"]) == 0  # idempotent

    zensical = tomllib.loads((fork / "docs/zensical.toml").read_text())["project"]
    assert zensical["site_name"] == "Castell"
    assert "nav" in zensical  # hand-written parts survive
    assert "github.com/Criw/Castell/actions" in (fork / "README.md").read_text()
    assert "RELEASE_IMAGE_PREFIX=ghcr.io/criw/castell" in (fork / ".env.project").read_text()
    assert "COMPOSE_PROJECT_NAME=castell" in (fork / ".env.project").read_text()
    meta = json.loads((fork / "mobile/src/app/core/meta.json").read_text())
    assert (meta["slug"], meta["brand"]["name"]) == ("castell", "Castell")
    assert json.loads((fork / "mobile/package.json").read_text())["name"] == "castell-mobile"
    assert "<title>Castell</title>" in (fork / "mobile/src/index.html").read_text()
    pyproject = tomllib.loads((fork / "pyproject.toml").read_text())
    assert pyproject["project"]["name"] == "castell"  # the distribution; the package stays app
    assert "castell[api,ui]" in pyproject["dependency-groups"]["dev"]


def test_check_reports_a_stale_copy(fork, capsys):
    site = fork / "src/app/content/site.json"
    data = json.loads(site.read_text())
    data["theme"]["primary"] = "#112233"
    site.write_text(json.dumps(data))
    assert sync_meta.main(["--root", str(fork), "--check"]) == 1
    out = capsys.readouterr().out
    assert "stale: mobile/src/theme/_brand.scss" in out
    assert "stale: mobile/src/app/core/meta.json" in out


def test_ionic_colours_match_the_mobile_runtime():
    # The same expectations as mobile/src/app/core/theme.spec.ts, so first paint == runtime.
    assert sync_meta.ion_colour("primary", "#1b4965") == {
        "--ion-color-primary": "#1b4965",
        "--ion-color-primary-rgb": "27, 73, 101",
        "--ion-color-primary-contrast": "#ffffff",
        "--ion-color-primary-contrast-rgb": "255, 255, 255",
        "--ion-color-primary-shade": "#184059",
        "--ion-color-primary-tint": "#325b74",
    }
    assert sync_meta.contrast_for("#ffd166") == "#000000"


def test_missing_markers_are_an_error():
    with pytest.raises(ValueError, match="sync:header"):
        sync_meta.splice("no markers here", "header", "x", ("<!-- ", " -->"))
