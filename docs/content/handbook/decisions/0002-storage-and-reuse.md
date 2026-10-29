# Sgaffald: storage and reuse review

Status: **accepted**, partly carried out (the dependency-group split is still open).
Recorded 23 October 2026; paths below are as they were then.

Reviewed 2026-10-23. Scope: the whole working tree at `~/Desktop/sgaffald`. I only looked; nothing
in the project was changed.

## Summary

| Area | Finding | Impact |
|---|---|---|
| Storage | **1.2 GB** on disk, of which about **2.5 MB** is source. The rest can all be regenerated. | High |
| Storage | The `dev` group installs Playwright, Locust, Streamlit/pyarrow and the docs toolchain for every developer. | Medium |
| Storage | The uv cache is 12 GB and the Playwright browser cache is 2.1 GB, both outside the repo. | Medium (machine-wide) |
| Reuse | Project identity (name, org, repo, version, colours, app id, year) is hard-coded in **~60 files**. | High |
| Reuse | Brand colours are copied into 4 places, and the version into 4 places, which have already drifted. | High |
| Reuse | The Ionic app sits inside the Python package (`src/sgaffald/mobile`). | Medium |
| Reuse | The project is not a git repository, and there is no template engine to start new projects from it. | High |

The main recommendation is to add a **`project.toml` metadata file** for identity, keep
**`site.json`** for content, and add one **`task sync`** command (with a test that checks for
drift) that copies both into the few places that cannot read them directly. See §3.

---

## 1. Where the storage goes

```
1.2G  sgaffald/
├── 754M  .venv/                         regenerable (uv sync)
├── 408M  src/sgaffald/mobile/node_modules/   regenerable (npm ci)
├──  11M  src/sgaffald/mobile/.angular/   build cache
├── 4.7M  docs/_build/                    build output
├── 1.1M  docs/.cache/                    Zensical/mkdocstrings cache
├── 984K  src/sgaffald/mobile/www/        build output
├── 440K  uv.lock                         keep
├── 324K  mobile/package-lock.json        keep
├── 612K  docs/content/  (≈500K images)   keep
└── ~150K Python, TS, config, tests       keep
```

Outside the project: `~/.cache/uv` is **12 GB** and `~/Library/Caches/ms-playwright` is **2.1 GB**.

### Recommendations

**S1. Add a `clean` task.** About 1.18 GB of the tree can be rebuilt, so a single command should
reclaim it:

```toml
clean = { cmd = "rm -rf .venv .pytest_cache .ruff_cache .coverage docs/_build docs/.cache src/sgaffald/mobile/{node_modules,.angular,www} && find . -name __pycache__ -type d -prune -exec rm -rf {} +", help = "Delete every regenerable directory" }
```

When archiving or sharing the template, use `git archive` (see R1) rather than zipping the folder.

**S2. Split the `dev` dependency group.** Most day-to-day work (lint, unit tests, docs) does not
need a browser driver or a load-test tool. Install them only when needed:

```text
[dependency-groups]
dev  = ["sgaffald[api,ui,admin]", "pytest>=8.4", "pytest-asyncio>=1.2", "pytest-cov>=7.0",
        "ruff>=0.14", "pre-commit>=4.3", "taskipy>=1.14", "watchfiles>=1.1"]
e2e  = ["pytest-playwright>=0.10.0"]
load = ["locust>=2.42"]
docs = [...]   # unchanged

[tool.uv]
default-groups = ["dev", "docs"]
```

`task verify` then runs `uv sync --all-groups` first. This saves about 140 MB of Playwright and
its dependencies, plus Locust's gevent stack, for anyone who doesn't run e2e or load tests.
Streamlit pulls in pyarrow and pandas (about 200 MB), so moving `admin` out of `dev` and into
its own group gives the same kind of saving.

**S3. Don't install `node_modules` on the host unless you work on mobile.** `task test_mobile`
already runs lint and tests inside Docker, so the 408 MB on the host is only needed for
`ng serve`. Note this in `docs/content/services/mobile.md`, and S1 removes it.

**S4. Prune the machine-wide caches** from time to time: `uv cache prune` (12 GB now), and
`playwright uninstall --all` followed by reinstalling only Chromium (2.1 GB now; the tests only use
Chromium).

**S5. Remove the unused image and compress the rest.** Nothing references
`docs/content/assets/images/csw-crest-256.png` (136 KB), since the 256w source is served as WebP.
Running `oxipng -o max --strip safe` on the remaining PNGs usually saves another 20–40%.

**S6. Keep mobile files out of the Python images' build context and cache key.**
`docker/Dockerfile` and `docker/docs.Dockerfile` both run `COPY src ./src`, which includes the
mobile sources and `package-lock.json`. Any mobile edit then invalidates the Python layers of the
`api`, `ui`, `admin` and `docs` images. R3 fixes this properly. In the meantime, add a
`.dockerignore` rule for the Python images or use `COPY --exclude=src/sgaffald/mobile` (BuildKit
1.7+).

---

## 2. What makes reuse hard today

Counted outside generated and vendored files:

| Value | Where it appears |
|---|---|
| `sgaffald` (package / slug) | ~50 files: Python imports, compose, Dockerfiles, entrypoint, tests, docs, mobile `CACHE_KEY`, `ionic.config.json`, `package.json` |
| `Sgaffald` (display name) | API title, UI `<title>` (twice), admin title (twice), `zensical.toml`, `sphinx/conf.py` (×3), `capacitor.config.ts`, mobile `index.html`, `site.fallback.ts`, `site.json`, tests |
| `Cyber Scallywags` / URL | `pyproject.toml`, `zensical.toml` (×4), `sphinx/conf.py` (×4), `package.json` author, `capacitor.config.ts` appId, `site.json`, `site.fallback.ts`, docs pages |
| `OWNER/REPO` | README (11 badges), `.env.production.example`, the docs guide |
| Version | `pyproject.toml` `0.1.0`, `api/main.py` `0.1.0`, `sphinx/conf.py` `0.1.0`, `package.json` **`0.0.1`** (already drifted) |
| Brand colours | `site.json`, `theme/variables.scss` (plus hand-computed shade/tint/rgb), `site.fallback.ts`, tests |
| Copyright year | `zensical.toml`, `sphinx/conf.py` |

The "Make it yours" guide currently says "search and replace `sgaffald`". That step is the one
most likely to go wrong when the template is reused.

---

## 3. Proposal: one metadata file for project identity

### 3.1 Two files, two jobs

There is already a good runtime metadata file: `site.json` is validated by `models.Site`, served at
`GET /site`, can be swapped with `SITE_FILE` without a rebuild, and is cached by the mobile app.
Keep that. What's missing is a **build-time** file for identity, which changes when the project
is created or renamed, not when content changes.

| File | Owns | Read when | Edited by |
|---|---|---|---|
| **`project.toml`** (new, repo root) | Name, slug, description, organisation, repo, app id, docs URL, copyright | Build / docs / start-up | Whoever forks the template, rarely |
| **`src/<pkg>/content/site.json`** (existing) | Brand tagline, theme colours, pages and sections | Runtime (`GET /site`) | Content editors, often |
| `pyproject.toml` (existing) | **Version**, dependencies, tooling | Build | Release process |

I chose TOML because Python reads it with the standard library (`tomllib`), the project already
uses TOML everywhere (`pyproject`, `zensical`), and it allows comments, unlike JSON. Keep the
version in `pyproject.toml` because uv and hatch own it there; everything else reads it via
`importlib.metadata`.

### 3.2 Proposed `project.toml`

```toml
# Project identity. Edit this file, then run `uv run task sync`.
# Content (pages, theme colours, tagline) lives in src/<pkg>/content/site.json.
# The version lives in pyproject.toml.

[project]
name        = "Sgaffald"                 # display name: titles, app name, docs
slug        = "sgaffald"                 # lower-case: images, compose project, cache keys
description = "Scaffolding for the next project, ready to be renamed and grown."
year        = 2026

[organisation]
name = "Cyber Scallywags"
url  = "https://cyberscallywags.com"
motto = "Play • Learn • Share • Grow"

[repository]
owner = "OWNER"
name  = "REPO"
# derived: https://github.com/{owner}/{name}, ghcr.io/{owner}/{name} (lower-cased)

[mobile]
app_id = "com.cyberscallywags.sgaffald"

[docs]
url  = "http://localhost:8200"           # default for DOCS_URL
logo = "assets/images/csw-mark-64.png"
```

### 3.3 How each consumer picks it up

You change the integral structure **once**, when each consumer starts reading the file. After
that, editing `project.toml` never touches code.

| Consumer | How it reads `project.toml` | Edit needed once |
|---|---|---|
| Python services (API, UI, admin) | New `sgaffald/meta.py`: `tomllib` load plus `importlib.metadata.version()`, behind `@lru_cache` like `get_settings` | `api/main.py` title/version/description, `ui/main.py` titles, `admin/app.py` titles |
| Sphinx | `conf.py` already runs Python, so read it directly | `project`, `author`, `copyright`, `release`, `html_title` |
| Zensical | Can't run code → **generated** by `task sync` | Template the `[project]` header and `extra.social` |
| Mobile | `capacitor.config.ts` and `site.fallback.ts` import a generated `meta.json`/`site.json` copy (`resolveJsonModule`) | Delete hand-written `FALLBACK_SITE` values |
| Mobile SCSS | Can't import JSON → **generated** `theme/_brand.scss` (shade/tint/rgb computed by the script) | `variables.scss` `@use`s it |
| Compose / env | `COMPOSE_PROJECT_NAME`, `IMAGE_PREFIX` defaults → generated `.env.project`, loaded with `--env-file .env.project --env-file .env.test` | Two `compose_*` variables in `pyproject.toml` |
| README badges | Generated between `<!-- sync:badges -->` markers | None |
| Tests | Assert against `meta.load()` / `get_site()`, not literal `"Sgaffald"` or `"#1b4965"` | ~10 assertions |

Sketch of `meta.py`:

```python
"""Project identity from project.toml; see docs/content/site-manifest.md."""

import tomllib
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path

from pydantic import BaseModel

PROJECT_FILE = Path(__file__).parents[2] / "project.toml"


class Meta(BaseModel):
    name: str
    slug: str
    description: str
    year: int
    organisation: str
    organisation_url: str | None = None
    version: str


@lru_cache
def get_meta() -> Meta:
    raw = tomllib.loads(PROJECT_FILE.read_text())
    return Meta(
        **raw["project"],
        organisation=raw["organisation"]["name"],
        organisation_url=raw["organisation"].get("url"),
        version=version(__package__),
    )
```

In the Docker images, `project.toml` sits outside `src/`, so add `COPY project.toml ./` to
`docker/Dockerfile`. Alternatively, ship it as package data under `src/<pkg>/project.toml` and
symlink it at the root for visibility.

### 3.4 `task sync` plus a drift test

Add `scripts/sync_meta.py` (stdlib only, idempotent). It reads `project.toml` and `site.json` and
writes these generated files, each marked `GENERATED, edit project.toml`:

- `docs/zensical.toml` header (or a full render from `docs/zensical.toml.in`)
- `src/sgaffald/mobile/src/theme/_brand.scss`
- `src/sgaffald/mobile/src/app/core/meta.json`
- `.env.project`
- the README badge block

Wire it in as a task and a pre-commit hook. Add a unit test that runs it with `--check` and fails if
any output is stale. `test_docs.py` already does this for the Zensical nav, so the pattern fits the
codebase. `docgen.py` should also render a "Project metadata" reference page, so the docs show
the current values.

### 3.5 Deduplicate between `site.json` and `project.toml`

Once `project.toml` exists, `site.json` → `brand.name` and `brand.collective` repeat it. Make them
optional in `models.Brand`, and have `get_site()` fill them from `get_meta()` when they're
missing. A deployment can still override the brand at runtime through `SITE_FILE`, but the default
has only one source.

---

## 4. Structural changes for reuse

**R1. Turn the project into a git repository, then a Copier template.** It isn't a git repo
today, so `.gitignore` has no effect and there is nothing to version or diff. After `git init`,
convert it into a **[Copier](https://copier.readthedocs.io) template**. `copier.yml` asks the same
questions as `project.toml` (name, slug, org, repo), renders the package directory as
`src/{{ slug }}`, and writes the answers into `project.toml`. The main benefit over
search-and-replace is that **`copier update` pulls later template improvements into projects
already created from it**. With this in place, step 1 of "Make it yours" becomes
`copier copy gh:OWNER/sgaffald my-app`.

**R2. Or avoid renaming the package at all.** If Copier is too much, give the Python package a
neutral, permanent name (`src/app/` or `src/core/`). Each project's identity then lives only in
`project.toml` plus the distribution name in `pyproject.toml`, and nothing is renamed. This loses
a distinctive import name, but removes about 50 edits per new project.

**R3. Move the mobile app out of the Python package.** Change `src/sgaffald/mobile/` to `mobile/`
(or `apps/mobile/`) at the root, and delete the empty `mobile/__init__.py`. Then:
- the `[tool.hatch.build.targets.wheel] exclude` line can go
- the Python images stop copying Node files (S6)
- a package rename (R2) no longer moves the Angular project
- `.dockerignore` paths become shorter

Update `docker/mobile.Dockerfile`, `.dockerignore`, `test_mobile.py` and `services/mobile.md`.

**R4. Generate the duplicate issue templates.** `.github/ISSUE_TEMPLATE/*.yml` (for the web form)
and `.github/issue-templates/*.md` (used by `new-issue.yml`) describe the same three kinds of issue
twice. Either have `new-issue.yml` build the body from the YAML form's `body[].attributes.label`
fields, or have `task sync` generate the `.md` files.

**R5. Derive the theme shades instead of hand-typing them.** `variables.scss` contains
`-shade`, `-tint` and `-rgb` values worked out by hand from the primary colour. `theme.ts` already
computes these at runtime for `GET /site`. The sync script should compute them the same way (shade
= mix with black 12%, tint = mix with white 10%), so changing a colour in `site.json` updates
everything.

**R6. Separate the throwaway test values from the environment files.** `.env.test` mixes compose
variables (identity and secrets) with host test URLs. Once identity moves to `.env.project`, this
file holds only test-specific values, which makes its purpose clearer.

---

## 5. Suggested order

1. `git init` and a first commit (R1, first half). Add `task clean` (S1).
2. Split the dependency groups (S2) and delete the unused PNG (S5). These are quick wins with no
   behaviour change.
3. Add `project.toml` and `meta.py`, and switch the Python services and Sphinx to read them
   (§3.2–3.3).
4. Add `task sync` and the drift test, then remove the hand-copied values in Zensical, mobile,
   README and compose (§3.4, R5).
5. Move the mobile app to the root (R3, S6).
6. Choose R1 (Copier) or R2 (neutral package name), then rewrite "Make it yours" to match.

After step 4, rebranding a fork comes down to editing `project.toml` and `site.json` and running
`uv run task sync`. The existing `task verify` gate confirms that nothing else needed to change.
