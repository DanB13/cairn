# Changelog

Schema versions and framework versions move independently. `schema_version` is
what seeded instances depend on; only a breaking schema change bumps it, and a
migration script ships alongside.

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
