"""scripts/sync_meta.py: the copies of brand/ are current and follow edits; the brand is checked."""

import importlib.util
import json
import re
import shutil
import struct
import subprocess
import tomllib
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
_spec = importlib.util.spec_from_file_location("sync_meta", ROOT / "scripts/sync_meta.py")
sync_meta = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_meta)


def brand_words(brand_toml: Path = ROOT / "brand/brand.toml") -> set[str]:
    """Words that only the brand may use: its organisation's name and web address. (The GitHub
    owner is not one: the template's own repository lives there.)"""
    org = tomllib.loads(brand_toml.read_text())["organisation"]
    host = org.get("url", "").split("//")[-1].split("/")[0]
    return {org["name"].lower(), *([host.lower()] if host else [])}


def test_template_files_never_name_the_brand():
    # Decision records are kept as written, so they may name the brand of their day.
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
            rel.startswith(("brand/", "examples/", "docs/content/handbook/decisions/"))
            or rel in generated
            # the licence names its copyright holder; the smoke test holds a test project's
            # identity, which is the brand inside the copy it builds
            or rel in {"uv.lock", "LICENSE", "scripts/template_smoke.py"}
            or path.suffix in {".png", ".webp", ".svg"}
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
    if (ROOT / "examples").is_dir():
        shutil.copytree(ROOT / "examples", tmp_path / "examples")
    rels = ["pyproject.toml", *map(str, sync_meta.output_paths(ROOT))]
    for rel in rels:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    return tmp_path


def set_brand(fork: Path, table: str, key: str, value: str | None) -> None:
    """Set `key` in `[table]` of the fork's brand.toml to the TOML `value` (None removes it),
    whatever brand the project has, so these tests pass in any project built from the
    template."""
    path = fork / "brand/brand.toml"
    lines = path.read_text().splitlines()
    if f"[{table}]" not in lines:
        lines += ["", f"[{table}]"]
    start = lines.index(f"[{table}]") + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("[")), len(lines))
    found = next((i for i in range(start, end) if re.match(rf"{key}\s*=", lines[i])), None)
    if found is not None:
        lines[found : found + 1] = [] if value is None else [f"{key} = {value}"]
    elif value is not None:
        lines.insert(end, f"{key} = {value}")
    path.write_text("\n".join(lines) + "\n")


def brand_toml(fork: Path) -> dict:
    return tomllib.loads((fork / "brand/brand.toml").read_text())


def png(width: int, height: int) -> bytes:
    """A blank PNG of the given size; sync_meta reads only its header."""
    raw = (b"\x00" + b"\x00\x00\x00\x00" * width) * height

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def test_renaming_the_project_updates_every_copy(fork):
    set_brand(fork, "project", "name", '"Castell"')
    set_brand(fork, "project", "slug", '"castell"')
    set_brand(fork, "repository", "owner", '"Criw"')
    set_brand(fork, "repository", "name", '"Castell"')

    assert sync_meta.main(["--root", str(fork)]) == 0
    assert sync_meta.main(["--root", str(fork), "--check"]) == 0  # idempotent

    zensical = tomllib.loads((fork / "docs/zensical.toml").read_text())["project"]
    assert zensical["site_name"] == "Castell"
    assert "nav" in zensical  # hand-written parts survive
    assert "github.com/Criw/Castell/actions" in (fork / "README.md").read_text()
    assert "RELEASE_IMAGE_PREFIX=ghcr.io/criw/castell" in (fork / ".env.project").read_text()
    assert "COMPOSE_PROJECT_NAME=castell" in (fork / ".env.project").read_text()
    meta = json.loads((fork / "mobile/src/app/core/meta.json").read_text())
    site_name = json.loads((fork / "brand/content/site.json").read_text())["brand"].get("name")
    assert (meta["slug"], meta["brand"]["name"]) == ("castell", site_name or "Castell")
    assert json.loads((fork / "mobile/package.json").read_text())["name"] == "castell-mobile"
    assert (
        f"<title>{site_name or 'Castell'}</title>" in (fork / "mobile/src/index.html").read_text()
    )
    pyproject = tomllib.loads((fork / "pyproject.toml").read_text())
    assert pyproject["project"]["name"] == "castell"  # the distribution; the package stays app
    assert "castell[api,ui]" in pyproject["dependency-groups"]["dev"]


def test_check_reports_a_stale_copy(fork, capsys):
    set_brand(fork, "theme", "primary", '"#112233"')
    assert sync_meta.main(["--root", str(fork), "--check"]) == 1
    out = capsys.readouterr().out
    assert "stale: mobile/src/theme/_brand.scss" in out
    assert "stale: mobile/src/app/core/meta.json" in out
    assert "stale: docs/content/assets/stylesheets/brand.css" in out


def test_a_changed_image_is_copied_to_every_folder(fork, capsys):
    favicon = fork / "brand/images" / brand_toml(fork)["images"]["favicon"]
    favicon.write_bytes(favicon.read_bytes() + b"\x00")
    copied = f"favicon{favicon.suffix}"
    assert sync_meta.main(["--root", str(fork), "--check"]) == 1
    out = capsys.readouterr().out
    for folder in ["docs/content/assets/brand", "mobile/src/assets/brand", "src/app/ui/static"]:
        assert f"stale: {folder}/{copied}" in out
    assert sync_meta.main(["--root", str(fork)]) == 0
    assert sync_meta.main(["--root", str(fork), "--check"]) == 0


def test_a_dropped_image_is_removed_from_the_copies(fork):
    set_brand(fork, "images", "logo", None)
    assert sync_meta.main(["--root", str(fork)]) == 0
    assert not list((fork / "docs/content/assets/brand").glob("logo.*"))
    assert not list((fork / "mobile/src/assets/brand").glob("logo.*"))


def test_the_manual_shows_the_crest_only_when_the_brand_has_one(fork):
    (fork / "brand/images/test-crest.png").write_bytes(png(64, 64))
    set_brand(fork, "images", "crest", '"test-crest.png"')
    set_brand(fork, "images", "crest_alt", '"A test crest"')
    assert sync_meta.main(["--root", str(fork)]) == 0
    assert "{image} assets/brand/crest.png" in (fork / "docs/content/manual.md").read_text()
    set_brand(fork, "images", "crest", None)
    assert sync_meta.main(["--root", str(fork)]) == 0
    assert "{image}" not in (fork / "docs/content/manual.md").read_text()
    assert not (fork / "docs/content/assets/brand/crest.png").exists()


@pytest.mark.parametrize(
    ("edits", "problem"),
    [
        ([("images", "favicon", None)], "favicon is required"),
        ([("images", "favicon", '"missing.png"')], "does not exist"),
        ([("images", "mark", '"small.png"')], "mark: 16x16, needs at least 128x128"),
        ([("images", "hero", '"small.png"'), ("images", "hero_alt", None)], "hero_alt is required"),
        ([("theme.docs", "accent_ink", '"#7fd4dd"')], "accent_ink on white: contrast"),
        ([("images", "banner", '"small.png"')], "unknown key 'banner'"),
    ],
)
def test_brand_problems_stop_the_sync(fork, capsys, edits, problem):
    (fork / "brand/images/small.png").write_bytes(png(16, 16))
    for edit in edits:
        set_brand(fork, *edit)
    assert sync_meta.main(["--root", str(fork), "--check"]) == 2
    assert problem in capsys.readouterr().err


def test_a_brand_page_cannot_overwrite_a_template_page(fork, capsys):
    (fork / "docs/content/architecture.md").write_text("# Architecture\n")
    (fork / "brand/docs/architecture.md").write_text("# Ours\n")
    assert sync_meta.main(["--root", str(fork), "--check"]) == 2
    assert "would overwrite the template page" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("scheme", "order"), [("light", ["default", "slate"]), ("dark", ["slate", "default"])]
)
def test_the_docs_open_in_the_brands_scheme(fork, scheme, order):
    set_brand(fork, "theme.docs", "scheme", f'"{scheme}"')
    assert sync_meta.main(["--root", str(fork)]) == 0
    palette = tomllib.loads((fork / "docs/zensical.toml").read_text())["project"]["theme"]
    assert [p["scheme"] for p in palette["palette"]] == order


def test_a_brand_can_leave_the_handbook_out_of_its_docs(fork):
    set_brand(fork, "docs", "include_handbook", "false")
    assert sync_meta.main(["--root", str(fork)]) == 0
    config = (fork / "docs/zensical.toml").read_text()
    assert '"handbook/' not in config.split("# sync:exclude")[0] + config.split("nav = [")[1]
    assert "handbook/" in tomllib.loads(config)["project"]["exclude_docs"]
    manual = (fork / "docs/content/manual.md").read_text()
    assert "handbook/" not in manual
    assert "project/overview" in manual  # the project's own pages stay


@pytest.mark.skipif(not (ROOT / "examples/brands/neutral").is_dir(), reason="no neutral brand")
def test_swapping_in_the_neutral_brand_rebrands_every_copy(fork):
    # the words of the brand in use, unless that is the neutral brand itself
    neutral = fork / "examples/brands/neutral/brand.toml"
    words = brand_words(fork / "brand/brand.toml") - brand_words(neutral)
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
