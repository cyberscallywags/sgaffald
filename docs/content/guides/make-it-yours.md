# Make it yours

Sgaffald is a template. To turn it into a real project:

1. **Set the brand**: replace `brand/` with `examples/brands/neutral/` and edit it: identity,
   palette and images in `brand.toml`, pages in `content/site.json`, the docs home and about
   pages in `docs/`. Then run `uv run task sync`, which checks the brand and rewrites every
   copy the code cannot read directly; `uv run task test` fails if one is missed. See
   [Brand kit](brand-kit.md). Set the version in `pyproject.toml`.
2. **Keep the Python package name**: the code lives in `src/app` in every project, so there is
   nothing to rename. `uv run task sync` names the distribution after `project.slug` (the
   `[project] name` in `pyproject.toml`); run `uv lock` afterwards.
3. **Model your domain**: replace `Item` in `models.py` and `ItemRepo` in `db.py`. The tests
   show the pattern for each layer, and the [data models](../reference/models.md) page
   regenerates itself.
4. **Shape the content**: the pages live in `brand/content/site.json`; see
   [Site manifest](../site-manifest.md).
5. **Pick a real model**: set `LLM_MODEL` for production and add the provider extra, e.g.
   `pydantic-ai-slim[anthropic]`.
6. **Connect sign-on**: replace the mobile `SessionService` placeholder with your identity
   provider and protect the write endpoints.
7. **Write the docs**: add pages under `docs/content`; see [The docs site](../services/docs.md).
8. **Refresh the tooling**: `uv run pre-commit autoupdate`, and pin `NEO4J_IMAGE` to the
   release you want.
