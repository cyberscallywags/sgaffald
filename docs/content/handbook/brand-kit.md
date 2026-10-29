# Brand kit

Everything that makes a project *this* project lives in one folder, `brand/`. The rest of the
repository is the template: it reads the brand, and never names it. To re-brand, edit the
folder (or replace it), run `uv run task sync`, and commit.

```text
brand/
├── README.md               what every file is for
├── brand.toml              identity, app palette, docs palette, images, docs kicker
├── content/
│   └── site.json           tagline, welcome, about and sidebar pages (see Site manifest)
├── images/                 logo, mark, favicon, hero, crest, native icon and splash
├── styles/docs.css         optional extra docs styles
└── docs/
    ├── home.md             the docs portal's home page
    └── about.md            the about page, in both docs sites
```

`examples/brands/neutral/` is a complete, neutral brand under CC0. Copy it over `brand/` to
start a project of your own, since the default brand's artwork is not licensed for reuse:

```bash
rm -r brand && cp -r examples/brands/neutral brand
# edit brand/brand.toml, brand/content/site.json, brand/docs/*.md and brand/images/
uv run task sync && uv lock && uv run task test
```

## `brand.toml`

| Table | Keys | Used for |
|---|---|---|
| `[project]` | `name`, `slug`, `description`, `year` | Titles, the distribution and image names, the compose project, copyright notices |
| `[organisation]` | `name`, `url`, `motto` | Author, footers, the default collective, the docs' social link |
| `[repository]` | `owner`, `name` | README badges and the release image prefix |
| `[mobile]` | `app_id` | The Capacitor app id (reverse-DNS, no hyphens) |
| `[theme]` | `primary`, `secondary`, `tertiary`, optional `font_family` | The web UI (Bootstrap) and the mobile app (Ionic), served by `GET /site` |
| `[theme.docs]` | `scheme`, `accent`, `accent_2`, `accent_ink`, `accent_2_ink`, `background`, `surface`, `card`, `border`, `text`, `text_muted`, `text_subtle`, `font_mono` | Both docs sites; every key is optional |
| `[images]` | see below | Every surface that shows an image |
| `[docs]` | `kicker` | The small label above the docs titles; defaults to the organisation name |

### The docs palette

Leave `[theme.docs]` out and the docs use the app palette: `secondary` for links in dark mode,
`tertiary` for highlights, `primary` for links in light mode, on neutral dark surfaces.
`scheme` picks the scheme the docs open in (`dark` or `light`); readers can switch.

`task sync` turns the palette into `--brand-*` CSS custom properties in
`docs/content/assets/stylesheets/brand.css`. The template's own stylesheets
(`template.css`, `zensical.css` and `docs/sphinx/_static/furo.css`) and the Furo colour
variables in `docs/sphinx/conf.py` use only those properties, so they hold no colours of their
own.

## Images

Put the files in `brand/images` and name them in `[images]`. `task sync` copies each one,
byte for byte, to a fixed name, `assets/brand/<key>.<ext>`, in each place that shows it:

| Key | Required | Rules | Copied to |
|---|---|---|---|
| `mark` | yes | square; PNG at least 128×128, or SVG | docs (logo), web UI navbar, mobile |
| `favicon` | yes | PNG at least 32×32, or SVG | docs, web UI, mobile |
| `logo` | no | any size | docs, mobile |
| `hero` | no | needs `hero_alt` | README banner, docs |
| `crest` | no | needs `crest_alt` | docs home, manual, about page |
| `app_icon` | no | PNG exactly 1024×1024 | mobile (`@capacitor/assets` source) |
| `splash` | no | PNG exactly 2732×2732 | mobile (`@capacitor/assets` source) |

Pages in `brand/docs` refer to the copies, for example `assets/brand/crest.webp`. Drop a key
and the next sync removes its copies; the folders `docs/content/assets/brand`,
`mobile/src/assets/brand` and `src/app/ui/static` belong to `task sync`.

## Docs pages

Every Markdown file in `brand/docs` is copied into `docs/content`, with `home.md` becoming the
portal's `index.md`. Each copy starts with a GENERATED note, so edit the file in `brand/docs`.
A brand page may not take the name of a template page.

## What `task sync` checks

`uv run task sync` (and the pre-commit hook, which runs it with `--check`) refuses a brand
with any of these, before it writes anything:

- a required image missing, or a named image whose file does not exist;
- a PNG smaller than its rule, or a native icon or splash of the wrong size;
- a hero or crest without its alt text;
- an unknown `[images]` key;
- a docs colour that fails WCAG AA (4.5:1): `accent` and `text` on `background`, and
  `accent_ink` and `accent_2_ink` on white;
- a page in `brand/docs` that would overwrite a template page.

The app colours need no check: the web UI and mobile app put black or white text on them,
whichever reads better, and the better of the two always reaches 4.5:1.

Try another brand without touching `brand/`:

```bash
uv run python scripts/sync_meta.py --check --brand examples/brands/neutral
```

## Re-branding a running deployment

The Python services read `brand.toml` and `content/site.json` when they start. Mount another
brand folder into the containers and set `BRAND_DIR` to it to change the identity, theme and
pages of a built image without rebuilding it. Images and the docs sites are built in, so they
change with `task sync` and a new image.
