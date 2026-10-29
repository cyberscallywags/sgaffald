# Upgrading from the template

A project built from Sgaffald keeps improving when the template does. How you pull fixes in
depends on how the project was created (see [Make it yours](make-it-yours.md)):

| Created with | Pull template changes with |
|---|---|
| Clone and re-point (keeps the template's history) | `git fetch template && git merge template/main` |
| GitHub **Use this template** (fresh history) | add the template as a remote, then cherry-pick or diff the commits you want |

```bash
# Use-this-template projects: add the template once
git remote add template https://github.com/cyberscallywags/sgaffald.git
git fetch template
git log --oneline template/main        # pick what you need
git cherry-pick <commit>               # or: git diff <old>..<new> -- path | git apply
```

Do it on a branch (`task/template-update`) and open a pull request, like any other change.

## Why most updates merge cleanly

The template and the project own different files:

| Owned by | Files |
|---|---|
| The project | `brand/`, `docs/content/project/`, the domain code you replaced `Item` with |
| The template | everything else, including this handbook and `scripts/sync_meta.py` |
| Generated | the copies `uv run task sync` writes; regenerate them instead of merging them |

Conflicts usually mean a project edited a template file. Keep project changes in the files the
project owns where you can. After merging, run `uv run task sync` (to regenerate the copies
from your `brand/`), `uv lock`, and `uv run task verify`.

## What changed

Each template release lists its changes, and what a project must do about them, in the
release notes. The [Decisions](decisions/index.md) explain larger changes.
