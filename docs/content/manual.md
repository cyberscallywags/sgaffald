% sync:brand
# Sgaffald reference manual

```{image} assets/brand/crest.webp
:alt: The Cyber Scallywags crest: a wolf in a flat cap above the words Play, Learn, Share, Grow
:class: brand-crest brand-crest--float
```

{.brand-kicker}
Cyber Scallywags · Reference manual
% /sync:brand

The Sphinx edition of these docs: the same pages as the [portal](/), plus the
[Python API](reference/python-api-sphinx.md) generated from docstrings.

```{toctree}
:caption: Project
:maxdepth: 1

project/overview
```

% The handbook's cards and toctrees are generated from HANDBOOK in scripts/sync_meta.py.
% sync:handbook
::::{grid} 1 2 2 3
:gutter: 3

:::{grid-item-card} Get started
:link: handbook/getting-started
:link-type: doc

Install the tools, start the stack, find every service.
:::

:::{grid-item-card} Architecture
:link: handbook/architecture
:link-type: doc

How every service fits together.
:::

:::{grid-item-card} HTTP API
:link: reference/http-api
:link-type: doc

Endpoints, bodies and `curl`, generated from the code.
:::
::::

```{toctree}
:caption: Handbook
:maxdepth: 2

handbook/index
handbook/getting-started
handbook/architecture
handbook/site-manifest
handbook/brand-kit
handbook/make-it-yours
handbook/upgrade
handbook/from-scratch
```

```{toctree}
:caption: Services
:maxdepth: 1

handbook/services/api
handbook/services/web-ui
handbook/services/admin
handbook/services/mobile
handbook/services/docs
```

```{toctree}
:caption: Development
:maxdepth: 1

handbook/development/ways-of-working
handbook/development/testing
handbook/development/environments
handbook/development/ci-cd
```

```{toctree}
:caption: Decisions
:maxdepth: 1

handbook/decisions/index
handbook/decisions/0001-structure-and-reuse
handbook/decisions/0002-storage-and-reuse
handbook/decisions/0003-brand-kit-and-sign-on
```
% /sync:handbook

```{toctree}
:caption: Reference
:maxdepth: 1

reference/http-api
reference/models
reference/configuration
reference/tasks
reference/site-sample
reference/project-metadata
reference/python-api-sphinx
```

```{toctree}
:caption: About
:maxdepth: 1

about
```
