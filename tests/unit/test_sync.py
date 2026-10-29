"""scripts/sync_meta.py: the copies of brand/ are current and follow edits; the brand is checked."""

import importlib.util
import json
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
_spec = importlib.util.spec_from_file_location("sync_meta", ROOT / "scripts/sync_meta.py")
sync_meta = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_meta)


def brand_words(root: Path = ROOT) -> set[str]:
    """Words that only the brand may use: its organisation name and GitHub owner."""
    meta = tomllib.loads((root / "brand/brand.toml").read_text())
    return {meta["organisation"]["name"].lower(), meta["repository"]["owner"].lower()}


def test_template_files_never_name_the_brand():
    # Markdown pages are checked once the handbook names the project through placeholders.
    generated = {path.as_posix() for path in sync_meta.output_paths(ROOT)}
    if not (git := shutil.which("git")):
        pytest.skip("git is not installed")
    listed = subprocess.run(  # noqa: S603 - fixed arguments, no user input
        [git, "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    named = []
    for rel in listed:
        path = ROOT / rel
        if (
            rel.startswith(("brand/", "examples/", "reports/"))
            or rel in generated
            or rel == "uv.lock"
            or path.suffix in {".md", ".png", ".webp", ".svg"}
            or not path.is_file()
        ):
            continue
        text = path.read_text(errors="ignore").lower()
        named += [f"{rel}: {word}" for word in brand_words() if word in text]
    assert not named, named


def test_generated_copies_are_current():
    stale = sync_meta.stale(ROOT)
    assert not stale, f"run `uv run task sync`: {sorted(map(str, stale))}"


@pytest.fixture
def fork(tmp_path) -> Path:
    """A copy of every file sync_meta reads or writes, as if the template had just been forked."""
    shutil.copytree(ROOT / "brand", tmp_path / "brand")
    shutil.copytree(ROOT / "examples", tmp_path / "examples")
    rels = ["pyproject.toml", *map(str, sync_meta.output_paths(ROOT))]
    for rel in rels:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    return tmp_path


def edit_brand(fork: Path, old: str, new: str) -> None:
    path = fork / "brand/brand.toml"
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new))


def test_renaming_the_project_updates_every_copy(fork):
    project = fork / "brand/brand.toml"
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
    edit_brand(fork, 'primary = "#1b4965"', 'primary = "#112233"')
    assert sync_meta.main(["--root", str(fork), "--check"]) == 1
    out = capsys.readouterr().out
    assert "stale: mobile/src/theme/_brand.scss" in out
    assert "stale: mobile/src/app/core/meta.json" in out
    assert "stale: docs/content/assets/stylesheets/brand.css" in out


def test_a_changed_image_is_copied_to_every_folder(fork, capsys):
    (fork / "brand/images/favicon.png").write_bytes(
        (fork / "examples/brands/neutral/images/favicon.png").read_bytes()
    )
    assert sync_meta.main(["--root", str(fork), "--check"]) == 1
    out = capsys.readouterr().out
    for folder in ["docs/content/assets/brand", "mobile/src/assets/brand", "src/app/ui/static"]:
        assert f"stale: {folder}/favicon.png" in out
    assert sync_meta.main(["--root", str(fork)]) == 0
    assert sync_meta.main(["--root", str(fork), "--check"]) == 0


def test_a_dropped_image_is_removed_from_the_copies(fork):
    edit_brand(fork, 'crest = "crest.webp"', "")
    assert sync_meta.main(["--root", str(fork)]) == 0
    assert not (fork / "docs/content/assets/brand/crest.webp").exists()
    assert "{image}" not in (fork / "docs/content/manual.md").read_text()


@pytest.mark.parametrize(
    ("old", "new", "problem"),
    [
        ('favicon = "favicon.png"', "", "favicon is required"),
        ('favicon = "favicon.png"', 'favicon = "missing.png"', "does not exist"),
        ('mark = "mark.png"', 'mark = "favicon.png"', "mark: 64x64, needs at least 128x128"),
        ("hero_alt = ", "# hero_alt = ", "hero_alt is required"),
        ('accent_ink = "#00707d"', 'accent_ink = "#7fd4dd"', "accent_ink on white: contrast"),
        ('logo = "logo.svg"', 'logo = "logo.svg"\nbanner = "x.png"', "unknown key 'banner'"),
    ],
)
def test_brand_problems_stop_the_sync(fork, capsys, old, new, problem):
    edit_brand(fork, old, new)
    assert sync_meta.main(["--root", str(fork), "--check"]) == 2
    assert problem in capsys.readouterr().err


def test_a_brand_page_cannot_overwrite_a_template_page(fork, capsys):
    (fork / "docs/content/architecture.md").write_text("# Architecture\n")
    (fork / "brand/docs/architecture.md").write_text("# Ours\n")
    assert sync_meta.main(["--root", str(fork), "--check"]) == 2
    assert "would overwrite the template page" in capsys.readouterr().err


def test_light_first_brands_reorder_the_docs_palette(fork):
    edit_brand(fork, 'scheme = "dark"', 'scheme = "light"')
    assert sync_meta.main(["--root", str(fork)]) == 0
    palette = tomllib.loads((fork / "docs/zensical.toml").read_text())["project"]["theme"]
    assert [p["scheme"] for p in palette["palette"]] == ["default", "slate"]


def test_swapping_in_the_neutral_brand_rebrands_every_copy(fork):
    words = brand_words(fork)
    shutil.rmtree(fork / "brand")
    shutil.copytree(fork / "examples/brands/neutral", fork / "brand")
    assert sync_meta.main(["--root", str(fork)]) == 0
    assert sync_meta.main(["--root", str(fork), "--check"]) == 0
    # Wholly generated files; README, zensical.toml and pyproject.toml are only partly.
    partly = {"README.md", "docs/zensical.toml", "pyproject.toml"}
    for rel in sync_meta.output_paths(fork):
        if rel.as_posix() not in partly and rel.suffix not in {".png", ".svg", ".webp"}:
            text = (fork / rel).read_text().lower()
            assert not [word for word in words if word in text], rel
    zensical = tomllib.loads((fork / "docs/zensical.toml").read_text())["project"]
    assert zensical["site_author"] == "Example Organisation"
    assert zensical["theme"]["logo"] == "assets/brand/mark.svg"
    readme = (fork / "README.md").read_text()
    assert 'src="docs/content/assets/brand/hero.svg"' in readme
    assert "github.com/example-org/example-project/actions" in readme
    assert not (fork / "docs/content/assets/brand/crest.webp").exists()
    assert (fork / "src/app/ui/static/mark.svg").exists()
    assert not (fork / "src/app/ui/static/mark.png").exists()
    assert (
        "--brand-accent: #2a9d8f;"
        in (fork / "docs/content/assets/stylesheets/brand.css").read_text()
    )


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
