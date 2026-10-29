# Mobile app

`mobile/`: Ionic 9 + Angular 22 with standalone components, packaged with
Capacitor 8. It talks to the API only, through `ApiService`
(`src/app/core/api.service.ts`), whose types mirror the [data models](../../reference/models.md).

## Structure

```text
src/app/
  app.component.*        shell: split pane + side menu (sign-on, pages, About, Docs)
  app.routes.ts          welcome, about, p/:slug, items, sign-in
  features.ts            code-backed screens listed after the manifest pages
  core/
    api.service.ts       HTTP to the API; types mirror models.py
    site.store.ts        loads GET /site, caches it on the device, applies the theme
    theme.ts             brand colours -> Ionic colour variables
    icons.ts             the registered icon set
    session.service.ts   sign-on placeholder (see below)
  shared/sections.*      renders manifest sections (text, list, steps, cards)
  pages/
    content/             one template for welcome, about and every /p/<slug> page
    items/               the item form and list
    sign-in/             the sign-on form
```

## Adding pages

- **A content page**: add it to `pages` in `brand/content/site.json`. No code change.
- **A screen with behaviour**: create it under `pages/`, add its route in `app.routes.ts`
  and an entry in `features.ts`.

## Sign-on

`SessionService` remembers who is using the device so the menu can greet them. It is not
authentication and the API does not check it. Replace `signIn` and `signOut` with your
identity provider and send its token from `ApiService`.

## Building and running

- **Container**: `docker/mobile.Dockerfile` runs `npm run lint` and the Vitest unit tests,
  then builds. A failing test fails the image build, `task up` and the release. nginx serves
  the result on :8100 and proxies `/api/*` to the API, so the web build needs no CORS.
- **Local dev** (needs Node 24): `cd mobile && npm ci && npm start`;
  `proxy.conf.json` forwards `/api` to the API on :8000. This is the only reason to install
  `node_modules` (about 400 MB) on the host: `task test_mobile` and `task up` lint, test and
  build inside Docker. `task clean` removes it again.
- **Native builds**: `npx cap add ios|android`, set `apiUrl` in
  `src/environments/environment.prod.ts` to the public API URL, and add the app's origin
  (e.g. `capacitor://localhost`) to `CORS_ORIGINS`.

## Tests

Vitest specs with mocked HTTP run in the Docker build (`task test_mobile`).
`tests/integration` covers the nginx proxy to the API and Neo4j, and the CORS preflight for
native origins. `tests/e2e/test_mobile.py` drives a real browser emulating a Pixel 7 and
checks Neo4j directly.
