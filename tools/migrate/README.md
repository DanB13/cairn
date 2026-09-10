# Migration scripts

One script per major schema version step, named `v<from>_to_v<to>.py`.

Requirements, all three enforced by review rather than by tooling:

- **Idempotent.** Running it twice must be safe. Instances will run it twice.
- **In place, on a branch.** Never rewrite history. The migration is a pull
  request like anything else, and the diff is the review.
- **Reporting.** Print every file changed and every file that could not be, with
  the reason. A migration that silently skips files is worse than one that fails.

Instances pin the framework at a major branch (`ref: v1` in the instance
workflow), so a breaking change never reaches anybody's CI until they move the
pin deliberately. See [../../docs/migrations.md](../../docs/migrations.md).

No migrations exist yet: the current schema is version 1.
