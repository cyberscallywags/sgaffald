# brand/

Everything that makes this project *this* project. The rest of the repository is the template
and never names the brand. To re-brand, edit this folder (or replace it with
`examples/brands/neutral/`) and run `uv run task sync`; `uv run task test` fails until every
copy is current. The full reference is the brand kit page of the docs
(`docs/content/guides/brand-kit.md`).

| File | What it holds | Read by |
|---|---|---|
| `brand.toml` | Identity, app palette (`[theme]`), docs palette (`[theme.docs]`), images (`[images]`), docs kicker | Every service at start-up; `task sync` for the files that cannot read it |
| `content/site.json` | Tagline, welcome, about and sidebar pages | The API, served at `GET /site` to the web UI and the mobile app |
| `images/` | Logo, mark, favicon, hero, crest, native icon and splash | `task sync` copies them to `assets/brand/<key>.<ext>` in the docs, web UI and mobile app |
| `styles/docs.css` | Optional extra docs styles the palette cannot express | Copied to the docs as `brand-extra.css` |
| `docs/*.md` | The docs portal's home (`home.md`) and about page, plus any other project pages | Copied into `docs/content/` |

`task sync` refuses a brand with a missing or undersized image, an image without its alt text,
a colour that fails WCAG AA contrast, or a page that would overwrite a template page.

To deploy one built image under another brand, mount a brand folder into the containers and set
`BRAND_DIR` to it; the API serves that brand's identity, theme and pages without a rebuild.
