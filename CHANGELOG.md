# Changelog

Schema versions and framework versions move independently. `schema_version` is
what seeded instances depend on; only a breaking schema change bumps it, and a
migration script ships alongside.

## 1.1.0

New checks. No schema change; `schema_version` remains 1, so no migration is
needed. Existing instances may see new errors, which is the intent.

- Governance wiring is now validated. An unreplaced `CODEOWNERS` placeholder is
  an error, because GitHub silently ignores owners it cannot resolve: an
  instance with `@CURATOR` still in place has no code owners at all, branch
  protection passes vacuously, and the whole governance model is unenforced
  while appearing configured. Nothing in GitHub warns about this.
- `unassigned` in `governance.curators`, `curator_deputy` or `reviewers` is an
  error. An unassigned role is an unstaffed one.
- Warns when one person is both Curator and the only Reviewer, which is the
  bundled role the split exists to avoid.
- Warns when an instance has no `CODEOWNERS` file at all.
- Bumped `actions/checkout` and `actions/setup-python` to v7 in both the
  framework workflow and the instance template, clearing the Node 20
  deprecation.
- Contract checks: 33, up from 28.

## 1.0.1

Bug fix. No schema change; `schema_version` remains 1.

- The strict frontmatter parser did not implement YAML chomping, so `|` and `>`
  block scalars lost the trailing newline PyYAML produces. Any profile or config
  using a folded description therefore failed the PyYAML cross-check. Clip and
  strip chomping are now both handled, and `|+` / `>+` are rejected with a clear
  message rather than mis-parsed.
- `tools/selftest.py` now says out loud when PyYAML is absent, because the
  cross-check silently skips in that case and a local run is then weaker than
  CI. That gap is how the chomping bug reached the pipeline.
- Added `tools/requirements-dev.txt` for the cross-check dependency.

`v1.0.0` is left in place rather than retagged. It has failing CI and is
superseded by this release: both tags stand, dated, which is the same rule the
content contract applies to contradictory claims.

## 1.0.0

Initial release as CAIRN (Competitive Analysis: Incremental Records,
Notarised). `schema_version: 1`.

- Three skills split by write risk: `/compete` (read), `/competeupdate`
  (incremental, reviewed), `/competeseed` (bulk, Curator-only).
- Git-native data model. Review is a pull request; governance is `CODEOWNERS`;
  the audit trail is commit history.
- Two-layer content model: descriptive vendor pages, interpretive assessment
  files. Battlecards and threat readings live in the interpretive layer, which
  resolves the contradiction between forbidding interpretation on pages and
  requiring a battlecard section on them.
- One signal per file, so contributions never conflict.
- Confidence checked against source kind and source **independence** rather than
  source count.
- Freshness per signal type. Confidence explicitly describes filing time only.
- Contradictions recorded, never overwritten, and both sides blocked from
  outbound collateral until resolved.
- Collateral provenance gate with a generated appendix.
- Retention: aged signals move to `archive/`, keeping the live query surface and
  token cost bounded.
- Visibility guardrail: refuses to seed or push a private instance to a public
  repository, enforced in three places.
- Dependency-free validators, plus 18 negative tests proving each check fires.
- Market profiles for `generic`, `data-security` and `devtools`, resolved from
  the instance's own `profiles/` directory before the framework's, so adapting a
  vocabulary never requires forking.
- Required `organisation` block in instance config, gathered by the
  `/competeseed` interview. Kept distinct from the profile: `organisation` is
  identity, a profile is vocabulary. Checked rather than decorative, and carried
  into `index.json` for consumers.
