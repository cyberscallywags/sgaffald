"""Entities added with `uv run task new_entity <Name>`: one module each, holding the entity's
models, storage and routes. The API includes every module's `router`, the web UI gives each a
page (`TITLE`, `PATH`, `MODEL`, `MODEL_IN`), and the docs and the mobile app's types include its
models. The sample `Item` predates this package and lives in app.models, app.db and the API."""

import importlib
import pkgutil
from functools import cache
from types import ModuleType


@cache
def modules() -> list[ModuleType]:
    """Every entity module, in name order."""
    return [
        importlib.import_module(f"{__name__}.{info.name}")
        for info in sorted(pkgutil.iter_modules(__path__), key=lambda i: i.name)
        if not info.name.startswith("_")
    ]
