# CI/CD

GitHub Actions in `.github/workflows`:

| Workflow | Trigger | Does |
|---|---|---|
| `ci.yml` | push to any branch, PR into `main` | branch-name check + pre-commit + unit + mobile + docs + template smoke test → compose build (including the docs image) + integration + Playwright + Locust → `ci-passed` |
| `release.yml` | merge to `main` | re-runs CI, then pushes `ghcr.io/<owner>/<repo>/<service>:main` and `:sha-<commit>`, each with an SBOM and build provenance, signed with cosign |
| `release.yml` | tag `vX.Y.Z` | promotes the already-tested `:sha-<commit>` images to `:vX.Y.Z` and `:latest`, with no rebuild, and publishes a GitHub release with notes from the commit prefixes |
| `codeql.yml` | push to `main`, PR, weekly | CodeQL code scanning of the Python, TypeScript and workflow code |
| `scorecard.yml` | push to `main`, weekly | OpenSSF Scorecard: the repository's security practices, published as a score |
| `issue-to-project.yml` | issue opened | adds it to the GitHub Project |
| `new-issue.yml` | manual (Actions tab) | creates a feature, bug or task issue, its body built from the matching `.github/ISSUE_TEMPLATE/` form, and adds it to the Project |

Branches must be named `feature/`, `bug/`, `task/`, `docs/` or `refactor/` followed by a
lower-case name (`a-z`, `0-9`, `.`, `_`, `-`), e.g. `feature/add-login`. The rule lives in
`scripts/check_branch_name.sh`: a pre-push hook refuses the push locally, and the `branch-name`
job fails anything that gets through (it blocks `ci-passed`). Locally, the hooks also refuse
commits and pushes to `main`: work on a branch and open a PR.

Issue forms for people live in `.github/ISSUE_TEMPLATE/`, and the pull request template in
`.github/pull_request_template.md`. Images are published for `api`, `ui`, `admin`, `mobile` and
`docs`. Dependabot (`.github/dependabot.yml`) opens weekly, grouped update pull requests for
uv, npm, GitHub Actions and the Docker base images, from `dependabot/…` branches with `TASK:`
commit messages.

## The template smoke test

`uv run task smoke` (`scripts/template_smoke.py`, the `smoke` job) copies the repository,
makes it a new project with `scripts/new_project.py` (what `copier copy` runs: the neutral
brand with a new name, organisation and colour), adds an entity with
`scripts/new_entity.py Volunteer`, and runs `uv lock`, `task lint` and `task test` in the
copy. It then fails if the copy still names the original brand's organisation anywhere
outside the decision records, the licence and the changelog. It proves on every pull request
that a project can be made from the template, and keeps the tests free of any one brand's
values.

## Verifying a release image

Each image is signed keylessly, so a signature proves it was built by this repository's
release workflow:

```bash
cosign verify ghcr.io/<owner>/<repo>/api:latest \
  --certificate-identity-regexp 'https://github.com/<owner>/<repo>/.github/workflows/release.yml@.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
docker buildx imagetools inspect ghcr.io/<owner>/<repo>/api:latest --format '{{ json .SBOM }}'
```

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
5. **Security**: turn on private vulnerability reporting (Settings → Code security), which
   `SECURITY.md` and the code of conduct point to, and Dependabot alerts. Code scanning
   results from `codeql.yml` and `scorecard.yml` appear under Security → Code scanning.
6. **Template repository**: tick Settings → General → Template repository, so people can press
   **Use this template**.
