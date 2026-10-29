# Security policy

## Reporting a vulnerability

Please report security problems privately, never in a public issue or pull request: use the
repository's **Security → Report a vulnerability** form, which only maintainers can read.
Include what is affected, how to reproduce it and what an attacker could do. You should hear
back within a week; once a fix is released, the advisory is published with credit to you, if
you want it.

## Supported versions

Fixes go into `main` and the next release. Projects built from the template pull them in as
described in [Upgrading](docs/content/handbook/upgrade.md).

## What is not a vulnerability

The template's **mock sign-on** is a demo: one shared password, accounts in a committed file.
That it is weak is documented, and the API refuses to run it in production unless told to
(see [Sign-on](docs/content/handbook/sign-on.md)). The committed `.env.test` holds throwaway
values on purpose. Reports about either are welcome as ordinary issues.
