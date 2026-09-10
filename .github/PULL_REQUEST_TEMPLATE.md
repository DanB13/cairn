## What this changes

<!-- One line. -->

## Type

- [ ] New signal (intel filed via `/competeupdate`)
- [ ] Assessment update (interpretation layer)
- [ ] Vendor page correction (descriptive layer)
- [ ] Structure or tiering (Curator only)
- [ ] Framework change (schema, tools, skills)

## Contract checks

- [ ] Every claim carries a confidence tag, a source and a date
- [ ] `likely` claims have two or more sources with **distinct** origins
- [ ] No interpretation added to a descriptive section
- [ ] Contradictions recorded, not overwritten; conflict raised in open questions
- [ ] `python3 tools/validate.py <root>` passes
- [ ] Index regenerated if content changed

## For schema changes only

- [ ] `schema_version` bumped
- [ ] Migration script added under `tools/migrate/`
- [ ] `docs/migrations.md` updated
