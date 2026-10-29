# Environments

Docker compose reads two env files: `.env.project`, then one per environment. Every variable
is listed, with its values, in [Configuration](../../reference/configuration.md).

## Project

`.env.project` holds the project identity: `PROJECT_SLUG`, `COMPOSE_PROJECT_NAME`,
`IMAGE_PREFIX` (local builds) and `RELEASE_IMAGE_PREFIX` (`ghcr.io/<owner>/<repo>`).
`uv run task sync` generates it from `brand/brand.toml`, so do not edit it by hand. The
environment files build on it: `.env.test` names its compose project `${PROJECT_SLUG}-test`,
so `task down -v` never touches a production stack's volumes on the same machine.

## Test

`.env.test` is committed on purpose with throwaway values only:

- Neo4j Enterprise with `NEO4J_LICENSE=eval` (evaluation licence).
- `LLM_MODEL=test`, the offline model, so no API keys.
- Images built locally (`IMAGE_PREFIX` from `.env.project`, `IMAGE_TAG=local`).
- All ports bound to `127.0.0.1`.

```bash
uv run task up      # build + start, wait for healthchecks
uv run task logs    # follow the logs
uv run task down    # stop and drop volumes
```

## Production

Copy `.env.production.example` to `.env.production` (git-ignored) and fill it in.
`docker-compose.prod.yml` then:

- switches every service to the released GHCR images (`IMAGE_PREFIX=${RELEASE_IMAGE_PREFIX}`,
  `IMAGE_TAG`), with no
  local builds;
- requires `NEO4J_LICENSE=yes`, a commercial Neo4j Enterprise licence;
- hides the database and API ports;
- adds restart policies.

```bash
uv run task prod_check   # validate compose + .env.production
uv run task prod_up      # start with released images
uv run task prod_down    # stop, keeping data
```

Put a reverse proxy with TLS in front of the UI, the mobile web app and the docs, and set
`DOCS_URL` to the docs' public address so the apps link to it.
