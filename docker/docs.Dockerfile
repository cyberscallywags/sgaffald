# Docs image: generates the reference pages from the code, builds the Zensical portal and the
# Sphinx manual (both strict, so a docs warning fails the build), and serves them with nginx:
# portal at /, manual at /manual/. Build with: docker build -f docker/docs.Dockerfile .

ARG PYTHON_VERSION=3.14

FROM python:${PYTHON_VERSION}-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /bin/uv
ENV UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Dependencies first (cached layer), project and pages second.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --group docs --no-install-project
COPY pyproject.toml uv.lock README.md .env.project .env.test .env.production.example ./
COPY brand ./brand
COPY src ./src
COPY scripts ./scripts
COPY docs ./docs
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --group docs && uv run --no-sync task docs

FROM nginxinc/nginx-unprivileged:1.31-alpine AS runtime
COPY docker/docs.nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/docs/_build/site /usr/share/nginx/html
EXPOSE 8080
