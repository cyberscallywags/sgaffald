# Web UI

`src/app/ui/main.py`: a [FastUI](https://github.com/pydantic/FastUI) frontend. Pages are
declared in Python as components; FastUI's React bundle renders them in the browser. It
talks to the API over HTTP only, never to Neo4j.

| Route | Page |
|---|---|
| `/` | Welcome, from the site manifest |
| `/p/<slug>` | A sidebar page from the manifest |
| `/items` | The item form and table |
| `/about` | About Cyber Scallywags |

The navbar mirrors the mobile side menu: welcome, the manifest's pages, Items, then About and
Docs on the right. `render_section` turns each manifest section into FastUI components, the
twin of the mobile `SectionsComponent`.

## Theme

The landing HTML gets a `<style>` block built from the manifest's theme (`theme_css`), which
overrides Bootstrap's navbar, buttons and headings with the brand colours.

## Routing note

FastUI's prebuilt app fetches `/api<path>` for every page, so `/about` is served by the
`GET /api/about` handler. Any other path returns the HTML shell.
