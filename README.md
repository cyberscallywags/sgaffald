<!-- Badges are generated from project.toml by `uv run task sync`. -->
<p align="center">
  <img src="docs/content/assets/images/sgaffald-hero.webp" alt="Sgaffald: scaffolding for the next project, ready to be renamed and grown" width="100%">
</p>

<!-- sync:header -->
---

[![CI](https://img.shields.io/github/actions/workflow/status/cyberscallywags/sgaffald/ci.yml?event=pull_request&label=ci&logo=githubactions&logoColor=white)](https://github.com/cyberscallywags/sgaffald/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/actions/workflow/status/cyberscallywags/sgaffald/release.yml?label=release&logo=githubactions&logoColor=white)](https://github.com/cyberscallywags/sgaffald/actions/workflows/release.yml)
[![Coverage](https://img.shields.io/codecov/c/github/cyberscallywags/sgaffald?logo=codecov&logoColor=white)](https://codecov.io/gh/cyberscallywags/sgaffald)
[![Python](https://img.shields.io/badge/python-3.14-3776AB?logo=python&logoColor=white)](.python-version)
[![Top language](https://img.shields.io/github/languages/top/cyberscallywags/sgaffald?logo=github&logoColor=white)](https://github.com/cyberscallywags/sgaffald)
[![Languages](https://img.shields.io/github/languages/count/cyberscallywags/sgaffald?logo=github&logoColor=white)](https://github.com/cyberscallywags/sgaffald)
[![Open issues](https://img.shields.io/github/issues/cyberscallywags/sgaffald?logo=github&logoColor=white)](https://github.com/cyberscallywags/sgaffald/issues)
[![Open PRs](https://img.shields.io/github/issues-pr/cyberscallywags/sgaffald?logo=github&logoColor=white)](https://github.com/cyberscallywags/sgaffald/pulls)
[![Stars](https://img.shields.io/github/stars/cyberscallywags/sgaffald?logo=github&logoColor=white)](https://github.com/cyberscallywags/sgaffald/stargazers)
[![Forks](https://img.shields.io/github/forks/cyberscallywags/sgaffald?logo=github&logoColor=white)](https://github.com/cyberscallywags/sgaffald/network/members)
[![Last commit](https://img.shields.io/github/last-commit/cyberscallywags/sgaffald?logo=github&logoColor=white)](https://github.com/cyberscallywags/sgaffald/commits)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](.pre-commit-config.yaml)
<!-- /sync:header -->

<b>This Cyber Scallywags base template.</b> </br>
The smallest stack that connects every part and is ready to
be renamed and grown into a real project.

| Service | Tech | Local URL |
|---|---|---|
| `api` | FastAPI + Pydantic AI | http://localhost:8000/docs |
| `ui` | FastUI (Pydantic-declared React UI) | http://localhost:8080 |
| `admin` | Streamlit | http://localhost:8501 |
| `mobile` | Ionic + Angular (served by nginx, proxies `/api`) | http://localhost:8100 |
| `docs` | Zensical portal + Sphinx/Furo manual | http://localhost:8200 |
| `neo4j` | Neo4j Enterprise, evaluation licence | http://localhost:7474 |

## Quick start

```bash
uv sync                    # Python 3.14 + the dev and docs tools
uv run pre-commit install
uv run task --list         # every task
uv sync --all-groups       # + Playwright, Locust and Streamlit, for the full gate
uv run playwright install chromium   # the only browser the e2e tests use
uv run task verify         # lint → unit → build+start stack → integration → browser → Locust → teardown
```

## Start a new project from this template

The worked example below turns Sgaffald into **Data Volunteer Network**.

### 1. Create the repository (don't copy and paste the folders)

Copying folders by hand drops dotfiles (`.github/`, `.env.*`, `.pre-commit-config.yaml`,
`.python-version`) and loses the link back to the template. Pick one of these instead:

- **From a GitHub template (recommended, clean history).** Tick *Settings → General →
  Template repository* on `sgaffald` once, then either press **Use this template** or run:

  ```bash
  gh repo create cyberscallywags/data-volunteer-network \
    --template cyberscallywags/sgaffald --public --clone
  ```

- **Clone and re-point (keeps the template's history, so later template fixes can be merged in).**

  ```bash
  git clone https://github.com/cyberscallywags/sgaffald.git data-volunteer-network
  cd data-volunteer-network
  git remote rename origin template
  gh repo create cyberscallywags/data-volunteer-network --public --source . --push
  # later, to pick up template improvements:
  git fetch template && git merge template/main
  ```

Make the renaming changes below on a branch (for example `task/rename-from-template`) and open a
PR. After `uv run pre-commit install`, the pre-push hook blocks pushes to `main`.

### 2. Set the identity: `project.toml`, then `uv run task sync`

| Field | Sgaffald | Data Volunteer Network |
|---|---|---|
| `project.name` | `Sgaffald` | `Data Volunteer Network` |
| `project.slug` (lower-case; images, compose project) | `sgaffald` | `data-volunteer-network` |
| `project.description` | `Cyber Scallywags base template: …` | `Connects volunteers with organisations that need their data skills` |
| `project.year` | `2026` | the copyright year |
| `organisation.name` / `url` / `motto` | Cyber Scallywags | keep, or the owning organisation |
| `repository.owner` | `cyberscallywags` | `cyberscallywags` |
| `repository.name` | `sgaffald` | `data-volunteer-network` |
| `mobile.app_id` (reverse-DNS, no hyphens) | `com.cyberscallywags.sgaffald` | `com.cyberscallywags.datavolunteernetwork` |

`uv run task sync` then rewrites every copy that the code cannot read directly. Don't edit these
by hand:

- `README.md` badges
- `docs/zensical.toml` site name and footer
- `.env.project` compose project and image prefixes
- `pyproject.toml` description
- `mobile/package.json`, `package-lock.json`, `ionic.config.json`, `src/index.html` title,
  `src/app/core/meta.json` and `src/theme/_brand.scss`

`uv run task test` fails if any of them are stale.

### 3. Set the version: `pyproject.toml`

- `version`: reset to `0.1.0` for the new project.

### 4. Set the brand and content: `src/app/content/site.json`

| Field | Change to |
|---|---|
| `brand.tagline` | e.g. `Data skills, where they're needed.` |
| `brand.name`, `brand.collective`, `brand.collective_url` | optional; default to `project.name` and `organisation.name` |
| `theme.primary` / `secondary` / `tertiary` | the new brand colours |
| `welcome` and the pages | the project's own welcome page and sidebar pages |

Run `uv run task sync` again afterwards so the mobile app's first paint uses the new colours. See
[Site manifest](docs/content/site-manifest.md).

### 5. The Python package stays `app`

The import package is `src/app` in every project built from this template, so there is nothing to
rename. `uv run task sync` names the distribution after `project.slug` (`[project] name` and the
`<slug>[api,ui]` extras in `pyproject.toml`); run `uv lock` afterwards so `uv.lock` agrees.

### 6. Model the domain

Replace the sample `Item` with your own models, for example `Volunteer` and `Opportunity`:

- `models.py`: `Item` / `ItemIn`
- `db.py`: `ItemRepo`
- `api/main.py`: the `/items` routes
- `admin/main.py`
- `ui/main.py`
- `mobile/src/app/core/api.service.ts`, `mobile/src/app/pages/items/` and
  `mobile/src/app/features.ts`

The tests show the pattern for each layer.

### 7. Replace images and styling

- `docs/content/assets/images/`: hero, logo, crest and favicon. Update the hero path at the top
  of this README and `logo` in `docs/zensical.toml`.
- `mobile/src/assets/icon/favicon.png`
- `docs/content/assets/stylesheets/scallywag.css`

### 8. Environments

- `.env.test`: `NEO4J_PASSWORD` (a throwaway value; the tests read the same one).
- `.env.production`: copy it from `.env.production.example` and fill it in. It is never
  committed. Set a real `LLM_MODEL` and add its provider extra, e.g. `pydantic-ai-slim[anthropic]`.

### 9. GitHub repository settings (not copied by a template)

- Secrets and variables:
  - `CODECOV_TOKEN` secret
  - `PROJECT_URL` variable and `PROJECT_TOKEN` secret, for the issue → project workflows
- Branch rules on `main` and the GHCR package visibility. See
  [One-off repository setup](docs/content/development/ci-cd.md#one-off-repository-setup).

### 10. Clean up and check

- Delete `reports/`.
- Rewrite the intro above and the pages in `docs/content`: `index.md`, `about.md` and
  `getting-started.md`.
- `git grep -i sgaffald` lists anything left over.
- `uv run task verify` runs the full gate.

The fuller guide is [Make it yours](docs/content/guides/make-it-yours.md).

## Documentation

Everything else (architecture, the site manifest, each service, testing, environments, CI/CD,
repository setup, and the generated HTTP API, data model, configuration and task references)
lives in the docs, built from [`docs/content`](docs/content):

```bash
uv run task docs_serve     # build both sites, serve on http://localhost:8200
```

- **Portal** (Zensical) at `/`: start here.
- **Reference manual** (Sphinx + Furo) at `/manual/`: the same pages plus the Python API from docstrings.

With the stack running (`uv run task up`) the `docs` container serves both on
http://localhost:8200, and the web UI and mobile app link to it. Reference pages are generated
from the code by `python -m app.docgen`, so they cannot drift; see
[The docs site](docs/content/services/docs.md).
