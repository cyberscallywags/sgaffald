# Getting started

This project is built on Sgaffald, a base template: the smallest stack that connects every part
and is ready to be renamed, re-branded and grown into a real project. This handbook belongs to
the template; the project's own pages are under [Project](../project/overview.md).

## What you need

| Tool | Why |
|---|---|
| [uv](https://docs.astral.sh/uv/) | Installs Python 3.14 and every Python tool |
| Docker with compose | Runs the full stack, the mobile build and the docs build |
| Node 24 (optional) | Only for live-reloading the mobile app outside Docker |

## Quick start

```bash
uv sync                               # Python 3.14 + the dev and docs tools
uv run pre-commit install
uv run task --list                    # every task (see Reference → Tasks)
uv sync --all-groups                  # + Playwright, Locust and Streamlit, for the full gate
uv run playwright install chromium    # the only browser the e2e tests use
uv run task verify                    # lint → unit → stack → integration → browser → Locust → teardown
```

`task verify` is the same gate CI runs. To just start everything and look around:

```bash
uv run task up        # build + start the test stack, wait until healthy
uv run task down      # stop it and drop the volumes
```

## Where everything lives

| Service | Tech | Local URL |
|---|---|---|
| `api` | FastAPI + Pydantic AI | <http://localhost:8000/docs> |
| `ui` | FastUI (Pydantic-declared React UI) | <http://localhost:8080> |
| `admin` | Streamlit | <http://localhost:8501> |
| `mobile` | Ionic + Angular, served by nginx, proxies `/api` | <http://localhost:8100> |
| `docs` | Zensical portal + Sphinx manual | <http://localhost:8200> |
| `neo4j` | Neo4j Enterprise, evaluation licence | <http://localhost:7474> |

The agent behind `POST /ask` uses Pydantic AI's offline `TestModel` when `LLM_MODEL=test`,
so tests and CI need no API keys.

## Writing the docs

```bash
uv run task docs          # generate the reference pages, build both sites into docs/_build
uv run task docs_serve    # build, then serve both sites together on http://localhost:8200
uv run task docs_live     # live-reload the Zensical portal while you write
uv run task docs_live_manual   # live-reload the Sphinx manual
```

See [The docs site](services/docs.md) for how the two engines share one set of pages.

## Dependency groups

`uv sync` installs the `dev` and `docs` groups, enough for linting, unit tests and the docs.
The heavier tools are separate groups, installed when you need them:

| Group | Adds | Needed for |
|---|---|---|
| `e2e` | Playwright | `task test_e2e` |
| `load` | Locust | `task load`, `task load_ui` |
| `admin` | Streamlit (with pyarrow and pandas) | running the admin portal outside Docker |

`uv sync --group e2e` adds one; `uv sync --all-groups` adds them all, and `task verify` does
that itself.

## Reclaiming disk space

Almost everything in a working copy can be rebuilt. `uv run task clean` deletes `.venv`,
the test and lint caches, the docs build and the mobile app's `node_modules`, `.angular`
and `www`; `uv sync` brings the virtualenv back. Two caches outside the project also grow
over time, and are shared with your other projects:

```bash
uv cache prune                         # drop unused entries from uv's cache
uv run playwright uninstall --all      # remove every downloaded browser...
uv run playwright install chromium     # ...and fetch back the one the tests use
```

To share or archive the project, use `git archive HEAD -o project.zip` rather than zipping
the folder, so only tracked files go in.
