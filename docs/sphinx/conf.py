"""Sphinx + Furo: the reference manual. Build: uv run task docs   Live: uv run task docs_live_manual

Source pages are docs/content (shared with the Zensical portal, docs/zensical.toml), so
this configuration lives apart from them: sphinx-build -c docs/sphinx docs/content <out>.
"""

import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1] / "src"))  # autodoc imports sgaffald without install

# Import FastAPI before autodoc documents any Pydantic model's members: once it has, FastAPI's
# own models (extra="allow") fail to build, and app.api/ui could not be documented.
import fastapi  # noqa: E402, F401

from app.meta import get_meta  # noqa: E402

meta = get_meta()  # project.toml, plus the version from pyproject.toml
project = meta.name
author = meta.organisation.name
copyright = f"{meta.year}, {meta.organisation.name}"  # noqa: A001 - Sphinx's name for it
release = meta.version

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinxcontrib.mermaid",
]

root_doc = "manual"
# Portal-only pages (Zensical grid-card home, mkdocstrings Python API).
exclude_patterns = ["index.md", "reference/python-api.md"]
source_suffix = {".md": "markdown"}

# MyST: the shared pages use plain Markdown plus `{.class}` on images and mermaid fences.
myst_enable_extensions = ["attrs_inline", "attrs_block", "colon_fence", "deflist"]
myst_heading_anchors = 3
myst_fence_as_directive = ["mermaid"]

# Links to the portal (`/`, `/manual/...`) are absolute site paths, not Sphinx documents.
suppress_warnings = ["myst.xref_missing"]
nitpicky = False

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {"members": True, "show-inheritance": True}

# sphinxcontrib-mermaid follows Furo's light/dark switch itself; a custom init config breaks
# its re-render, so diagrams are branded in _static/furo.css instead.

# ---------------------------------------------------------------- Scallywag Neon on Furo
html_theme = "furo"
html_title = f"{meta.name} manual"
html_static_path = ["_static", "../content/assets/stylesheets"]
html_css_files = ["scallywag.css", "furo.css"]
html_js_files = ["dark-first.js"]
html_logo = "../content/assets/images/csw-mark-128.png"
html_favicon = "../content/assets/images/favicon.png"
templates_path = ["_templates"]
# The manual's home is manual.html (index.md belongs to the portal); /manual/ redirects there.
html_additional_pages = {"index": "redirect-to-manual.html"}
html_copy_source = False
html_show_sourcelink = False

_shared = {
    "font-stack": "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
    "font-stack--monospace": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
}
html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "announcement": " · ".join(
        filter(
            None,
            [
                f'Part of the <a href="/">{meta.name} docs portal</a>',
                meta.organisation.name,
                meta.organisation.motto,
            ],
        )
    ),
    "light_css_variables": {
        **_shared,
        "color-brand-primary": "#00707d",
        "color-brand-content": "#00707d",
        "color-brand-visited": "#c2005f",
        "color-announcement-background": "#161b22",
        "color-announcement-text": "#e6edf3",
    },
    "dark_css_variables": {
        **_shared,
        "color-brand-primary": "#00e5ff",
        "color-brand-content": "#00e5ff",
        "color-brand-visited": "#ff4da6",
        "color-background-primary": "#0b0e14",
        "color-background-secondary": "#161b22",
        "color-background-hover": "#1d242e",
        "color-background-border": "#30363d",
        "color-background-item": "#1d242e",
        "color-foreground-primary": "#e6edf3",
        "color-foreground-secondary": "#cbd5e1",
        "color-foreground-muted": "#94a3b8",
        "color-foreground-border": "#30363d",
        "color-code-background": "#1d242e",
        "color-inline-code-background": "#1d242e",
        "color-card-background": "#161b22",
        "color-card-border": "#30363d",
        "color-announcement-background": "#161b22",
        "color-announcement-text": "#e6edf3",
    },
}
pygments_style = "friendly"
pygments_dark_style = "github-dark"
