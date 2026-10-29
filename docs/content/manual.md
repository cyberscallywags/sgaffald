# Sgaffald reference manual

```{image} assets/images/csw-crest-512.png
:alt: The Cyber Scallywags crest
:class: csw-crest csw-crest--float
```

{.csw-kicker}
Cyber Scallywags · Reference manual

The Sphinx edition of the Sgaffald docs: the same pages as the [portal](/), plus the
[Python API](reference/python-api-sphinx.md) generated from docstrings.

::::{grid} 1 2 2 3
:gutter: 3

:::{grid-item-card} Get started
:link: getting-started
:link-type: doc

Install the tools, start the stack, find every service.
:::

:::{grid-item-card} Architecture
:link: architecture
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
:caption: Guide
:maxdepth: 2

getting-started
architecture
site-manifest
guides/make-it-yours
```

```{toctree}
:caption: Services
:maxdepth: 1

services/api
services/web-ui
services/admin
services/mobile
services/docs
```

```{toctree}
:caption: Development
:maxdepth: 1

development/ways-of-working
development/testing
development/environments
development/ci-cd
```

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
:caption: Community
:maxdepth: 1

about
```
