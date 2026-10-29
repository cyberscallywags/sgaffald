# Make it yours

Sgaffald is a template. The steps below turn it into a real project; the worked example turns
it into **Data Volunteer Network**. Make the changes on a branch and open a pull request, like
any other change (see [Ways of working](development/ways-of-working.md)).

## 1. Create the repository (don't copy and paste the folders)

Copying folders by hand drops dotfiles (`.github/`, `.env.*`, `.pre-commit-config.yaml`,
`.python-version`) and loses the link back to the template. Pick one of these instead:

- **With Copier (does steps 1–4 for you, and can apply template updates later).** It asks for
  the name, organisation, GitHub owner and repository, app id and primary colour, then runs
  `scripts/new_project.py`, which swaps in the neutral brand with your answers, resets the
  version and runs `task sync`. Then continue at step 5.

  ```bash
  uvx copier copy --trust gh:cyberscallywags/sgaffald data-volunteer-network
  cd data-volunteer-network && git init && uv lock && uv run task verify
  ```

  `--trust` lets Copier run that script. The answers are kept in `.copier-answers.yml`, which
  `copier update` uses; see [Upgrading](upgrade.md).

- **From a GitHub template (clean history).** Tick *Settings → General →
  Template repository* on `sgaffald` once, then either press **Use this template** or run:

  ```bash
  gh repo create <owner>/data-volunteer-network \
    --template cyberscallywags/sgaffald --public --clone
  ```

- **Clone and re-point (keeps the template's history, so later template fixes can be merged in).**

  ```bash
  git clone https://github.com/cyberscallywags/sgaffald.git data-volunteer-network
  cd data-volunteer-network
  git remote rename origin template
  gh repo create <owner>/data-volunteer-network --public --source . --push
  # later, to pick up template improvements:
  git fetch template && git merge template/main
  ```

Make the renaming changes below on a branch (for example `task/rename-from-template`) and open a
PR. After `uv run pre-commit install`, the pre-push hook blocks pushes to `main`.

## 2. Set the brand: `brand/`, then `uv run task sync`

Everything project-specific lives in `brand/` (its `README.md` lists every file). Start from the neutral
example (the default brand's artwork is not licensed for reuse), then edit it:

```bash
python scripts/new_project.py --name "Data Volunteer Network" \
  --organisation "Data Volunteers" --owner data-volunteers --primary "#3d405b"
# or by hand: rm -r brand && cp -r examples/brands/neutral brand, then edit brand/brand.toml
```

| File | Change |
|---|---|
| `brand/brand.toml` `[project]` | `name` (`Data Volunteer Network`), `slug` (`data-volunteer-network`), `description`, `year` |
| `brand/brand.toml` `[organisation]`, `[repository]`, `[mobile]` | the owning organisation, the GitHub owner and repository, the reverse-DNS app id (no hyphens) |
| `brand/brand.toml` `[theme]`, `[theme.docs]` | the app colours, and optionally the docs palette |
| `brand/images/` and `[images]` | mark and favicon (required); logo, hero, crest, app icon, splash (optional) |
| `brand/content/site.json` | the tagline, welcome page, about page and sidebar pages |
| `brand/docs/home.md`, `about.md` | the docs portal's home and about pages |

`uv run task sync` checks the brand (images present and large enough, alt text, WCAG AA
contrast) and then rewrites every copy the code cannot read directly: the README hero and
badges, both docs sites' names, logos, palettes and brand pages, the compose variables, the
distribution name, the mobile app's metadata, favicon and first-paint theme, and the web UI's
static images. Don't edit those by hand; `uv run task test` fails if any is stale. Run
`uv lock` afterwards so `uv.lock` agrees with the new distribution name. The full reference is
the [Brand kit](brand-kit.md).

## 3. Set the version: `pyproject.toml`

- `version`: reset to `0.1.0` for the new project.

## 4. The Python package stays `app`

The import package is `src/app` in every project built from this template, so there is nothing to
rename. `uv run task sync` names the distribution after `project.slug` (`[project] name` and the
`<slug>[api,ui]` extras in `pyproject.toml`).

## 5. Model the domain

Replace the sample `Item` with your own models, for example `Volunteer` and `Opportunity`:

- `models.py`: `Item` / `ItemIn`
- `db.py`: `ItemRepo`
- `api/main.py`: the `/items` routes
- `admin/main.py`
- `ui/main.py`
- `mobile/src/app/core/api.service.ts` (its methods), `mobile/src/app/pages/items/` and
  `mobile/src/app/features.ts`

Run `uv run task types` after changing the models: it regenerates the mobile app's types
(`api.types.ts`), and the pre-commit hook refuses a stale copy. The tests show the pattern for
each layer.

## 6. Environments

- `.env.test`: `NEO4J_PASSWORD` (a throwaway value; the tests read the same one).
- `.env.production`: copy it from `.env.production.example` and fill it in. It is never
  committed. Set a real `LLM_MODEL` and add its provider extra, e.g. `pydantic-ai-slim[anthropic]`.

## 7. GitHub repository settings (not copied by a template)

- Secrets and variables:
  - `CODECOV_TOKEN` secret
  - `PROJECT_URL` variable and `PROJECT_TOKEN` secret, for the issue → project workflows
- Branch rules on `main` and the GHCR package visibility. See
  [One-off repository setup](development/ci-cd.md#one-off-repository-setup).

## 8. Clean up and check

- Rewrite the project's own pages: `brand/docs/home.md` and `about.md` (the docs home and
  about pages) and `docs/content/project/overview.md`, then `uv run task sync`.
- `git grep -i -e "example project" -e example-org -e example.org` lists placeholders left
  over from the neutral brand.
- `uv run task verify` runs the full gate.

## Then

- **Pick a real model**: set `LLM_MODEL` for production and add the provider extra, e.g.
  `pydantic-ai-slim[anthropic]`.
- **Connect sign-on**: replace the mock with your identity provider; see
  [Sign-on](sign-on.md#replacing-it-with-a-real-provider).
- **Write the docs**: add project pages under `docs/content/project/`; see
  [The docs site](services/docs.md).
- **Refresh the tooling**: `uv run pre-commit autoupdate`, and pin `NEO4J_IMAGE` to the
  release you want.
- **Keep up with the template**: see [Upgrading](upgrade.md).
