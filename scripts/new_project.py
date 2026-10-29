"""Turn a fresh copy of the template into a new project: the neutral brand with your identity
and colour, version 0.1.0, and every generated copy rewritten. `copier copy` runs it with your
answers (copier.yml); in a plain clone, run it by hand:

    python scripts/new_project.py --name "Data Volunteer Network" \\
        --organisation "Data Volunteers" --organisation-url https://datavolunteers.example \\
        --owner data-volunteers --primary "#3d405b"

Then `uv lock` and `uv run task verify`. Standard library only.
"""

import argparse
import re
import shutil
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

NEUTRAL = Path("examples/brands/neutral")


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def set_key(path: Path, table: str, key: str, value: str | None) -> None:
    """Set `key` in `[table]` of a TOML file to the TOML `value`, keeping every comment and the
    rest of the file as it is; None removes the key."""
    lines = path.read_text().splitlines()
    if f"[{table}]" not in lines:
        lines += ["", f"[{table}]"]
    start = lines.index(f"[{table}]") + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("[")), len(lines))
    found = next((i for i in range(start, end) if re.match(rf"{key}\s*=", lines[i])), None)
    if found is not None:
        comment = re.search(r"\s+#.*$", lines[found])
        new = f"{key} = {value}" + (comment[0] if comment else "")
        lines[found : found + 1] = [] if value is None else [new]
    elif value is not None:
        lines.insert(end, f"{key} = {value}")
    path.write_text("\n".join(lines) + "\n")


def toml_str(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--name", required=True, help="display name, e.g. 'Castell Data'")
    parser.add_argument("--slug", help="lower-case, hyphens; default: from the name")
    parser.add_argument("--description", help="one line; default: a generic description")
    parser.add_argument("--organisation", help="who is behind it; default: the name")
    parser.add_argument("--organisation-url", default="", help="its website")
    parser.add_argument("--owner", help="GitHub owner; default: from the organisation")
    parser.add_argument("--repository", help="GitHub repository; default: the slug")
    parser.add_argument("--app-id", help="reverse-DNS app id; default: org.example.<slug>")
    parser.add_argument("--primary", help="primary colour, #rrggbb; default: the neutral one")
    parser.add_argument("--year", type=int, help="copyright year; default: the brand's")
    parser.add_argument("--root", type=Path, default=Path("."), help="the new project")
    parser.add_argument(
        "--keep-brand", action="store_true", help="edit the current brand/ instead of replacing it"
    )
    args = parser.parse_args(argv)
    args.slug = args.slug or slugify(args.name)
    args.organisation = args.organisation or args.name
    args.owner = args.owner or slugify(args.organisation)
    args.repository = args.repository or args.slug
    args.app_id = args.app_id or f"org.example.{args.slug.replace('-', '')}"
    if not re.fullmatch(r"[a-z][a-z0-9-]*", args.slug):
        parser.error(f"--slug {args.slug!r}: lower-case letters, digits and hyphens")
    if args.primary and not re.fullmatch(r"#[0-9a-fA-F]{6}", args.primary):
        parser.error(f"--primary {args.primary!r}: six-digit hex, e.g. #3d405b")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse(argv)
    root = args.root
    if not args.keep_brand:
        if not (root / NEUTRAL).is_dir():
            print(f"{NEUTRAL} is missing; use --keep-brand to edit brand/ instead", file=sys.stderr)
            return 1
        shutil.rmtree(root / "brand")
        shutil.copytree(root / NEUTRAL, root / "brand")

    toml = root / "brand/brand.toml"
    values = {
        ("project", "name"): toml_str(args.name),
        ("project", "slug"): toml_str(args.slug),
        ("organisation", "name"): toml_str(args.organisation),
        ("organisation", "url"): toml_str(args.organisation_url),
        ("repository", "owner"): toml_str(args.owner),
        ("repository", "name"): toml_str(args.repository),
        ("mobile", "app_id"): toml_str(args.app_id),
        ("docs", "kicker"): toml_str(args.organisation),
    }
    if args.description:
        values["project", "description"] = toml_str(args.description)
    if args.primary:
        values["theme", "primary"] = toml_str(args.primary.lower())
    if args.year:
        values["project", "year"] = str(args.year)
    for (table, key), value in values.items():
        set_key(toml, table, key, value)

    # The template's history is not the project's: start an empty changelog.
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\nGenerated from the commit messages by `uv run task changelog` "
        "(git-cliff, cliff.toml).\n"
    )

    pyproject = root / "pyproject.toml"
    text = pyproject.read_text()
    text = re.sub(r'^version = ".*"$', 'version = "0.1.0"', text, count=1, flags=re.M)
    pyproject.write_text(text)

    spec = spec_from_file_location("sync_meta", root / "scripts/sync_meta.py")
    sync_meta = module_from_spec(spec)
    spec.loader.exec_module(sync_meta)
    if (status := sync_meta.main(["--root", str(root)])) != 0:
        return status
    print(
        f"\n{args.name} is ready. Next: replace the placeholder pages in brand/content/site.json "
        "and brand/docs/, then `uv lock` and `uv run task verify`."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
