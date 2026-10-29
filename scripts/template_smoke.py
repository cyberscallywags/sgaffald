"""Prove the "make it yours" promise: copy the template, swap in the neutral brand with new
values, as a new project would, then check that the gate passes and that nothing still names
the old brand.

    uv run task smoke            # in a temporary copy; the working tree is not touched

CI runs it on every pull request. Standard library only; needs git and uv.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# A new project's identity, deliberately unlike the template's.
NEW = {
    'name = "Example Project"': 'name = "Castell Data"',
    'slug = "example-project"': 'slug = "castell-data"',
    'name = "Example Organisation"': 'name = "Criw Castell"',
    'url = "https://example.org"': 'url = "https://castell.example"',
    'owner = "example-org"': 'owner = "criw"',
    'name = "example-project"': 'name = "castell-data"',
    'app_id = "org.example.exampleproject"': 'app_id = "org.example.castelldata"',
    'primary = "#264653"': 'primary = "#3d405b"',
}
# Kept as written, or naming the copyright holder: they may name the template's brand.
EXEMPT = ("examples/", "docs/content/handbook/decisions/", "LICENSE", "CHANGELOG.md", "uv.lock")


def run(*cmd: str, cwd: Path) -> None:
    print(f"$ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)  # noqa: S603 - fixed commands


def copy_template(dest: Path) -> None:
    """Tracked and untracked (not ignored) files, as a fresh clone would have them."""
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    for rel in listed:
        if (ROOT / rel).is_file():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, dest / rel)


def old_brand_words() -> set[str]:
    org = tomllib.loads((ROOT / "brand/brand.toml").read_text())["organisation"]
    host = org.get("url", "").split("//")[-1].split("/")[0]
    return {org["name"].lower(), *([host.lower()] if host else [])}


def leftovers(project: Path, words: set[str]) -> list[str]:
    found = []
    for path in project.rglob("*"):
        rel = path.relative_to(project).as_posix()
        if (
            not path.is_file()
            or rel.startswith((".venv/", ".git/", "docs/_build/", "mobile/node_modules/"))
            or rel.startswith(EXEMPT)
            or path.suffix in {".png", ".webp", ".pyc"}
        ):
            continue
        text = path.read_text(errors="ignore").lower()
        found += [f"{rel}: {word}" for word in words if word in text]
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--keep", action="store_true", help="keep the copy and print its path")
    args = parser.parse_args(argv)
    words = old_brand_words()
    project = Path(tempfile.mkdtemp(prefix="template-smoke-")) / "castell-data"
    try:
        copy_template(project)
        shutil.rmtree(project / "brand")
        shutil.copytree(project / "examples/brands/neutral", project / "brand")
        toml = project / "brand/brand.toml"
        text = toml.read_text()
        for old, new in NEW.items():
            if old not in text:
                raise SystemExit(f"examples/brands/neutral/brand.toml has no {old!r}")
            text = text.replace(old, new, 1)
        toml.write_text(text)

        run(sys.executable, "scripts/sync_meta.py", cwd=project)
        run("uv", "lock", "--quiet", cwd=project)
        # a new project is a git repository; some tests list its files with git
        run("git", "init", "--quiet", cwd=project)
        run("git", "add", "--all", cwd=project)
        run("uv", "run", "--quiet", "task", "lint", cwd=project)
        run("uv", "run", "--quiet", "task", "test", "-q", "--no-cov", cwd=project)
        run(sys.executable, "scripts/sync_meta.py", "--check", cwd=project)

        pyproject = tomllib.loads((project / "pyproject.toml").read_text())
        assert pyproject["project"]["name"] == "castell-data", pyproject["project"]["name"]
        if found := leftovers(project, words):
            print("The old brand is still named in:", *found, sep="\n  ", file=sys.stderr)
            return 1
        print(f"OK: a project built from the template carries no trace of {sorted(words)}")
        return 0
    finally:
        if args.keep:
            print(f"kept: {project}")
        else:
            shutil.rmtree(project.parent, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
