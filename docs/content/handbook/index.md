# Template handbook

How the template works and how to work with it. Every project built from Sgaffald carries the
same handbook, so nothing here names the project: its name, organisation and colours are on
[Project metadata](../reference/project-metadata.md), and its own pages are under
[Project](../project/overview.md).

**Don't edit these pages in a project.** They are the template's, and keeping them untouched
means template fixes merge without conflicts; see [Upgrading](upgrade.md). To change how the
template itself works, change it in the template repository. A project that does not want the
handbook in its published docs sets `include_handbook = false` under `[docs]` in
`brand/brand.toml`.

| Read | When you want to |
|---|---|
| [Getting started](getting-started.md) | install the tools and run the stack |
| [Architecture](architecture.md) | see how the services fit together |
| [Brand kit](brand-kit.md) and [Make it yours](make-it-yours.md) | turn the template into a project |
| [Site manifest](site-manifest.md) | change the pages the web UI and mobile app show |
| [Build it from scratch](from-scratch.md) | understand why each piece exists, in the order it was added |
| [Upgrading](upgrade.md) | pull template fixes into a project |
| [Ways of working](development/ways-of-working.md) | take a change from an issue to a release |
| [Decisions](decisions/index.md) | read why the template is shaped the way it is |
