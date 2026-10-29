# Web UI

`src/app/ui/main.py`: a [FastUI](https://github.com/pydantic/FastUI) frontend. Pages are
declared in Python as components; FastUI's React bundle renders them in the browser. It
talks to the API over HTTP only, never to Neo4j.

| Route | Page |
|---|---|
| `/`, `/welcome` | Welcome, from the site manifest |
| `/p/<slug>` | A sidebar page from the manifest |
| `/items` | The item form and table |
| `/about` | The about page from the site manifest |
| `/login` | Sign in: the email and password form, and one-click "Sign in as…" demo members |
| `/login/as/<id>` | One-click sign-in as a demo member (mock sign-on only) |
| `/logout` | Sign out |

The navbar mirrors the mobile side menu: welcome, the manifest's pages, Items, then About and
Docs on the right. `render_section` turns each manifest section into FastUI components, the
twin of the mobile `SectionsComponent`.

## Sign-on

`/login` posts to the API's `/auth/login` and keeps the token in an `HttpOnly`,
`SameSite=Lax` cookie (`Secure` in production), so the browser's scripts never see it. Every
API call this server makes forwards it as `Authorization: Bearer`. The navbar's right-hand end
shows **Sign in**, or the member's name, which opens an account panel with their email, role
and **Sign out**: FastUI has no dropdown component, so the panel is a `Modal` opened by a
`PageEvent`. The items form appears only to members. With sign-on off, none of this shows and
everyone can add items. See [Sign-on](../sign-on.md).

FastUI's `GoToEvent` applies a `query` to the current path and ignores its `url`, so the
sign-in and sign-out redirects go to `/welcome` with no query.

## Theme

The landing HTML gets a `<style>` block built from the manifest's theme (`theme_css`), which
overrides Bootstrap's navbar, buttons and headings with the brand colours.

## Routing note

FastUI's prebuilt app fetches `/api<path>` for every page, so `/about` is served by the
`GET /api/about` handler. Any other path returns the HTML shell.
