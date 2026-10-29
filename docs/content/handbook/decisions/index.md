# Decisions

Architecture decision records: why the template is shaped the way it is. Each one is kept as
it was written, with a status line on top, so later readers can see what was known at the
time. Add a record when a change alters how the template is structured, built or used.

| Record | Decision | Status |
|---|---|---|
| [0001](0001-structure-and-reuse.md) | Application structure, storage and reuse | Accepted, partly carried out |
| [0002](0002-storage-and-reuse.md) | Storage footprint and dependency groups | Accepted, partly carried out |
| [0003](0003-brand-kit-and-sign-on.md) | Brand kit, template handbook, mock sign-on and open-source readiness | Accepted, in progress |

To add one, copy the shape of an existing record (context, options, decision, consequences),
number it `NNNN-short-name.md`, and add it to the table above and to `HANDBOOK` in
`scripts/sync_meta.py`, which lists the handbook's pages for both docs sites.
