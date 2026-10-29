# One Dockerfile, three images. Build with: --build-arg SERVICE=api|ui|admin
# The SERVICE value selects the pyproject extra to install and the process to run.

ARG PYTHON_VERSION=3.14

FROM python:${PYTHON_VERSION}-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /bin/uv
ARG SERVICE
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
# Dependencies first (cached layer), project second.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project --extra ${SERVICE}
COPY pyproject.toml uv.lock README.md ./
COPY brand ./brand
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable --extra ${SERVICE}

FROM python:${PYTHON_VERSION}-slim AS runtime
ARG SERVICE
ENV SERVICE=${SERVICE} PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1
RUN useradd --system --uid 10001 app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
USER app
# A Python module, not a shell script: no line endings or execute bit to break on Windows
ENTRYPOINT ["python", "-m", "app.serve"]
