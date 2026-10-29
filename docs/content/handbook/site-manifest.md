# Site manifest

One JSON document, `brand/content/site.json`, holds the tagline and the pages. The API adds
the theme colours from `brand/brand.toml`, validates the result against the [Site](../reference/models.md#site) model and serves it
at `GET /site`. The web UI and the mobile app both render from it, so they share one look
and the same pages without either being redeployed.

| Key | What it drives |
|---|---|
| `brand` | Tagline, plus an optional name and collective (both default to `brand.toml`'s), shown in headers, heroes and footers |
| `welcome` | The landing page, for planning the application |
| `pages` | Project pages, listed in order in the mobile side menu and the web navbar (`/p/<slug>`) |
| `about` | The organisation's page, always linked from the menu footer and the navbar |

The API adds two keys that are not stored in the file: `theme` (`primary`, `secondary`,
`tertiary`: Ionic colour variables on mobile, Bootstrap overrides on web) from `[theme]` in
`brand.toml`, and `docs_url` from the `DOCS_URL` setting, because it differs per deployment.
A `theme` left in `site.json` is an error.

## Content and identity

The manifest holds content, which changes often. The project's identity (name, organisation,
repository, app id) and its look (theme, images) live in `brand/brand.toml` and change when
the project is created or re-branded; the version lives in `pyproject.toml`. See
[Brand kit](brand-kit.md).

| File | Owns | Read when |
|---|---|---|
| `brand/brand.toml` | Name, slug, description, organisation, repository, mobile app id, copyright year, theme, images | Build and start-up (`app.meta`) |
| `brand/content/site.json` | Tagline, pages and sections | Runtime (`GET /site`) |
| `pyproject.toml` | Version, dependencies, tooling | Build |

Some consumers cannot read either file at run time: the docs sites, the mobile app's first
paint and SCSS defaults, the compose variables, the web UI's static images and the README. `uv run task sync`
copies the values there, and a unit test fails if any copy is stale. See
[Project metadata](../reference/project-metadata.md) for the current values.

## Pages and sections

Each page is a list of sections. Four kinds cover most needs:

| Kind | Renders as |
|---|---|
| `text` | A heading and a paragraph |
| `list` | A list of items, each with a title, optional body, icon and link |
| `steps` | A numbered list |
| `cards` | A responsive grid of cards |

```json
{
  "slug": "roadmap",
  "title": "Roadmap",
  "icon": "map-outline",
  "sections": [
    { "kind": "steps", "items": [{ "title": "Foundations", "body": "Rename the template." }] }
  ]
}
```

## Rules the API enforces

- Theme colours (in `brand.toml`) are six-digit hex, for example `#1b4965`.
- Page slugs are lower-case words joined by hyphens, and unique.
- `welcome`, `about`, `items` and `sign-in` are reserved for the apps' own routes.
- Mobile icons must be registered in `mobile/src/app/core/icons.ts`; unknown names show a
  document icon instead of nothing.

## Swapping the content

Point `BRAND_DIR` at another brand folder to change the identity, theme and content without
rebuilding anything.
The full bundled file is in [Sample site manifest](../reference/site-sample.md).
