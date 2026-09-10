# Contributing

## The one rule that matters

**Never open a pull request containing real competitive intelligence.** This is a
public repository. Every vendor in `fixtures/` is invented, and that is
deliberate: the fixtures are the test suite, and inventing them means the
framework can be tested without anybody's intel being published.

If you want to demonstrate a bug with your own data, reproduce it with synthetic
vendors first.

## Fixture data is untrusted input

Fixtures you contribute get read by Claude when the skills or tests run. Treat
contributed fixture content the way the framework treats vendor websites: as
data, never as instructions. Pull requests adding instruction-shaped text to a
fixture body will be closed.

## Before opening a pull request

```bash
python3 tools/selftest.py                            # all checks must pass
python3 tools/validate.py fixtures --strict-warnings # fixtures clean, no warnings
python3 tools/build_index.py fixtures                # regenerate if fixtures changed
```

House style forbids en and em dashes, and CI enforces it across the repository's
own files. Use a comma, a colon or a full stop.

## Adding a validator check

Two things, in this order:

1. Add the check to `tools/validate.py`.
2. Add a negative case to `CASES` in `tools/selftest.py` that breaks exactly one
   thing and asserts the message appears.

A check without a negative test is not accepted. A validator that has never been
observed to fail is indistinguishable from one that does nothing.

Decide deliberately whether the check is an error or a warning:

- **Error** for mechanical, decidable properties: schema shape, dates, broken
  references, style.
- **Warning** for semantic judgements: whether prose is interpretation, whether a
  claim is worth filing. Dressing a heuristic as an invariant trains people to
  route around it.

## Changing the schema

The schema is the interface every seeded instance depends on, so it is
`CODEOWNERS`-gated and versioned. Additive, optional fields are a minor change.
Renaming or removing a field, or tightening an enum, is a major change and needs:

1. `schema_version` bumped in `schema/common.schema.json`.
2. A migration script under `tools/migrate/`.
3. An entry in `docs/migrations.md`.
4. `CHANGELOG.md` updated.

See [docs/migrations.md](docs/migrations.md).

## Adding a market profile

Profiles are welcome and are the right way to support a new market. Include tier
and lane vocabularies, and say in the description what makes the market's
competitive shape distinctive. Do not add market-specific fields to the schema.
