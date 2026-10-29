# Contributing

Thank you for helping. Every change follows the same path, and most of it is checked by the
hooks and CI, so you find out about a missed step before a reviewer does. The full version is
[Ways of working](docs/content/handbook/development/ways-of-working.md).

## Set up once

```bash
uv sync
uv run pre-commit install    # pre-commit, commit-msg and pre-push hooks
```

[Getting started](docs/content/handbook/getting-started.md) lists the tools (uv and Docker;
Node only for live-reloading the mobile app).

## Make a change

1. **Start from an issue**: pick or open one with the Feature, Bug or Task form, so the work
   is discussed before it is written.
2. **Branch** from `main`, named after the kind of work: `feature/…`, `bug/…`, `task/…`,
   `docs/…` or `refactor/…`. The hooks refuse commits to `main` and badly named branches.
3. **Commit** with a prefix: `ADDED:`, `FIXED:`, `TASK:`, `DOCS:` or `REFACTOR:`, then what
   changed, in the present tense. The `commit-msg` hook checks the prefix, and the changelog
   is generated from it.
4. **Check** with `uv run task test` while you work and `uv run task verify` (the same gate as
   CI) before asking for review on anything that touches more than one service.
5. **Open a pull request** into `main` linking the issue; fill in the template's checklist.
   `ci-passed` must be green before it merges.

## Where things go

- **Template code and the handbook** (`docs/content/handbook/`) belong to the template. Keep
  them free of any one project's name: the brand lives in `brand/`, and a unit test fails if
  its organisation's name appears anywhere else.
- **A decision that changes how the template is structured, built or used** gets a record in
  [`docs/content/handbook/decisions/`](docs/content/handbook/decisions/index.md).

## Conduct and security

Everyone taking part follows the [Code of conduct](CODE_OF_CONDUCT.md). Report security
problems privately, as described in [SECURITY.md](SECURITY.md), never in a public issue.

By contributing you agree that your contribution is released under the [MIT licence](LICENSE).
