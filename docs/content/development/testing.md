# Testing

Every layer is tested, from pure functions to a real phone browser against the full stack.

| Layer | Where | Needs | Run with |
|---|---|---|---|
| Unit (Python) | `tests/unit` | nothing; a `FakeRepo` replaces Neo4j | `task test` |
| Unit (mobile) | `mobile/**/*.spec.ts` | Docker | `task test_mobile` |
| Docs (generator, navigation) | `tests/unit/test_docs.py` | nothing | `task test` |
| Project metadata copies | `tests/unit/test_sync.py` | nothing | `task test` (fix with `task sync`) |
| Docs (build) | `docs/` | nothing | `task docs` (strict; also runs in CI and the docs image) |
| Integration | `tests/integration` | the running stack | `task test_int` |
| Browser (e2e) | `tests/e2e` | the stack + Chromium, `uv sync --group e2e` | `task test_e2e` |
| Load | `tests/load/locustfile.py` | the stack, `uv sync --group load` | `task load` / `task load_ui` |

`task verify` runs all of them in order and always tears the stack down, the same gate as CI.
`task watch` re-runs the Python unit tests on every save.

## What each layer proves

- **Unit**: the API, the UI (wired to the real API app in-process), the site manifest
  rules, settings, the docs generator, and that every copy of `project.toml` and the theme
  is current. Assertions read names and colours from `sgaffald.meta` and the manifest, never
  literals, so a renamed fork's tests still pass. Without the `e2e` group, pytest skips
  collecting `tests/e2e`.
- **Mobile unit**: services, the theme maths, the side menu, the content and sign-in pages
  (Vitest, mocked HTTP). Runs inside the image build, so a failing spec fails the build.
- **Integration**: every container against every other, including writes reaching Neo4j,
  the mobile nginx proxy, CORS for native origins, and the docs container serving both sites.
- **Browser**: the FastUI form flow, the admin portal and the mobile app on an emulated
  Pixel 7, reading Neo4j directly so the app cannot fake persistence. The docs are checked at
  phone and desktop widths: no sideways scrolling, every image inside the screen, dark first.
- **Load**: a 20-second Locust smoke against the API.

## Markers

`integration` and `e2e` tests are marked and skipped by `task test`. Unit tests run with
coverage; CI uploads `coverage.xml` to Codecov.

## TODO comments

Mark unfinished work with `TODO`, `FIXME` or `HACK`. In Python, ruff (`task lint`, and so
pre-commit and CI) checks TODOs: the tag in capitals, an author, a colon, then the text.

```python
# TODO(sam): page the results once there are more than a few hundred
```

A TODO need not link an issue. Ruff accepts only `TODO` in Python (it rejects `FIXME`, and
does not check `HACK`); the mobile app and other files can use all three. VS Code offers to install the recommended Todo Tree extension
when you open the repository; its sidebar view lists every tagged comment, grouped by file.
Without the extension, search the workspace (Cmd+Shift+F, or Ctrl+Shift+F) with regex on for
`TODO|FIXME|HACK`.
