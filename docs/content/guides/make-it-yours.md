# Make it yours

Sgaffald is a template. To turn it into a real project:

1. **Set the identity**: edit `project.toml` (name, slug, description, organisation,
   GitHub owner and repository, mobile app id), then run `uv run task sync`. That rewrites
   every copy the code cannot read directly: the Zensical config, the README title and
   badges, the compose variables, and the mobile app's metadata, title and first-paint
   theme. `uv run task test` fails if one is missed. Set the version in `pyproject.toml`.
2. **Keep the Python package name**: the code lives in `src/app` in every project, so there is
   nothing to rename. `uv run task sync` names the distribution after `project.slug` (the
   `[project] name` in `pyproject.toml`); run `uv lock` afterwards.
3. **Model your domain**: replace `Item` in `models.py` and `ItemRepo` in `db.py`. The tests
   show the pattern for each layer, and the [data models](../reference/models.md) page
   regenerates itself.
4. **Shape the content**: edit `src/app/content/site.json` (tagline, theme, pages), then
   run `uv run task sync` again so the mobile app's first paint uses the new colours. See
   [Site manifest](../site-manifest.md).
5. **Pick a real model**: set `LLM_MODEL` for production and add the provider extra, e.g.
   `pydantic-ai-slim[anthropic]`.
6. **Connect sign-on**: replace the mobile `SessionService` placeholder with your identity
   provider and protect the write endpoints.
7. **Write the docs**: add pages under `docs/content`; see [The docs site](../services/docs.md).
8. **Refresh the tooling**: `uv run pre-commit autoupdate`, and pin `NEO4J_IMAGE` to the
   release you want.
