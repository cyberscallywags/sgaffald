# CI/CD

GitHub Actions in `.github/workflows`:

| Workflow | Trigger | Does |
|---|---|---|
| `ci.yml` | push to any branch, PR into `main` | branch-name check + pre-commit + unit + mobile → compose build (including the docs image) + integration + Playwright + Locust → `ci-passed` |
| `release.yml` | merge to `main` | re-runs CI, then pushes `ghcr.io/<owner>/<repo>/<service>:main` and `:sha-<commit>` |
| `release.yml` | tag `vX.Y.Z` | promotes the already-tested `:sha-<commit>` images to `:vX.Y.Z` and `:latest`, with no rebuild |
| `issue-to-project.yml` | issue opened | adds it to the GitHub Project |
| `new-issue.yml` | manual (Actions tab) | creates a feature, bug or task issue, its body built from the matching `.github/ISSUE_TEMPLATE/` form, and adds it to the Project |

Branches must be named `feature/`, `bug/`, `task/`, `docs/` or `refactor/` followed by a
lower-case name (`a-z`, `0-9`, `.`, `_`, `-`), e.g. `feature/add-login`. The rule lives in
`scripts/check_branch_name.sh`: a pre-push hook refuses the push locally, and the `branch-name`
job fails anything that gets through (it blocks `ci-passed`). Locally, the hooks also refuse
commits and pushes to `main`: work on a branch and open a PR.

Issue forms for people live in `.github/ISSUE_TEMPLATE/`. Images are published for `api`,
`ui`, `admin`, `mobile` and `docs`.

## One-off repository setup

1. **Make CI mandatory before merging** (Settings → Rules → Rulesets → target `main`):
   require a pull request and the status check **`ci-passed`**. Or:

   ```bash
   gh api repos/{owner}/{repo}/rulesets -X POST --input - <<'JSON'
   {"name":"main","target":"branch","enforcement":"active",
    "conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"],"exclude":[]}},
    "rules":[{"type":"pull_request"},
             {"type":"required_status_checks","parameters":{"strict_required_status_checks_policy":true,
              "required_status_checks":[{"context":"ci-passed"}]}}]}
   JSON
   ```

2. **Projects**: add the repository variable `PROJECT_URL` (e.g.
   `https://github.com/orgs/<org>/projects/1`) and the secret `PROJECT_TOKEN` (a PAT with
   `project` and `repo` scopes).
3. **GHCR** uses the built-in `GITHUB_TOKEN`; nothing to configure.
4. **Coverage badge**: enable the repository on [codecov.io](https://codecov.io) and add its
   upload token as the secret `CODECOV_TOKEN`. A missing token never fails the build.
