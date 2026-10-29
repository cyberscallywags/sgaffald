<!-- The hero and badges are generated from brand/ by `uv run task sync`. -->
<!-- sync:hero -->
<p align="center">
  <img src="docs/content/assets/brand/hero.webp" alt="Sgaffald: scaffolding for the next project, ready to be renamed and grown" width="100%">
</p>
<!-- /sync:hero -->

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

**A full-stack base template:** the smallest stack that connects every part and is ready to
be renamed, re-branded and grown into a real project.

| Service | Tech | Local URL |
|---|---|---|
| `api` | FastAPI + Pydantic AI | http://localhost:8000/docs |
| `ui` | FastUI (Pydantic-declared React UI) | http://localhost:8080 |
| `admin` | Streamlit | http://localhost:8501 |
| `mobile` | Ionic + Angular (served by nginx, proxies `/api`) | http://localhost:8100 |
| `docs` | Zensical portal + Sphinx/Furo manual | http://localhost:8200 |
| `neo4j` | Neo4j Community (Enterprise optional) | http://localhost:7474 |

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

```bash
gh repo create <owner>/<name> --template cyberscallywags/sgaffald --public --clone
cd <name>
rm -r brand && cp -r examples/brands/neutral brand   # then edit brand/
uv run task sync && uv lock                            # check the brand, rewrite every copy
uv run task verify
```

`brand/` holds everything project-specific: identity, colours, images, pages and the docs home
page. The default brand's artwork is not licensed for reuse (see TRADEMARKS.md), so start from
the neutral example. [Make it yours](docs/content/handbook/make-it-yours.md) walks through every
step, from creating the repository to replacing the sample domain.

## Contributing and licence

Contributions are welcome: read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of conduct](CODE_OF_CONDUCT.md), and report security problems as described in
[SECURITY.md](SECURITY.md). The code is released under the [MIT licence](LICENSE); the default
brand in `brand/` is not (see [TRADEMARKS.md](TRADEMARKS.md)). Changes are listed in the
[changelog](CHANGELOG.md).

## Documentation

Everything else lives in the docs, built from [`docs/content`](docs/content): the template
handbook (architecture, the brand kit, each service, ways of working, testing, CI/CD, decision
records), the project's own pages, and the generated HTTP API, data model, configuration and
task references:

```bash
uv run task docs_serve     # build both sites, serve on http://localhost:8200
```

- **Portal** (Zensical) at `/`: start here.
- **Reference manual** (Sphinx + Furo) at `/manual/`: the same pages plus the Python API from docstrings.

With the stack running (`uv run task up`) the `docs` container serves both on
http://localhost:8200, and the web UI and mobile app link to it. Reference pages are generated
from the code by `python -m app.docgen`, so they cannot drift; see
[The docs site](docs/content/handbook/services/docs.md).
