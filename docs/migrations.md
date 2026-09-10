# Schema migrations

`schema_version` is what seeded instances depend on. Getting migration wrong is
the failure that strands adopters on version 1 forever, which is the specific way
distributed frameworks die.

## What needs a migration

| Change | Version | Migration |
|---|---|---|
| New optional field | None | No |
| New enum member | None | No |
| New profile | None | No |
| Field made required | Major | Yes |
| Field renamed or removed | Major | Yes |
| Enum member removed or renamed | Major | Yes |
| Semantics of a field changed | Major | Yes |

That last row is the one people miss. If `data_as_of` starts meaning something
different, every existing file is silently wrong even though it still validates.
Treat it as breaking.

## Shipping a major change

1. Bump the `maximum` in `common.schema.json#/$defs/schema_version` and
   `SUPPORTED_SCHEMA_VERSION` in `tools/validate.py`.
2. Write `tools/migrate/v<from>_to_v<to>.py`. It must be:
   - **idempotent**, so running it twice is safe
   - **in-place on a branch**, never a rewrite of history
   - **reporting**, printing every file it changed and every file it could not
3. Update the fixtures to the new version, and confirm `tools/selftest.py` still
   passes.
4. Add a row to the table below.
5. Tag the framework, and move the `v<major>` branch that instance CI pins.

## Instances pin a major branch

The instance workflow checks the framework out at `ref: v1`, not at `main`. A
patch to the validators reaches every instance automatically; a breaking schema
change does not, and cannot break anyone's CI overnight. Upgrading is deliberate:
run the migration, then move the pin.

## Migration log

| From | To | Date | Script | Notes |
|---|---|---|---|---|
| n/a | 1 | 2026-09-10 | n/a | Initial release. |
