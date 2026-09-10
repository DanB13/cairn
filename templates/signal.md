---
schema_version: 1
id: sig-1970-01-01-example-vendor-01
vendor: example-vendor
date: 1970-01-01
filed: 1970-01-01
type: other
confidence: likely
claim: "Replace with one observed fact, stated descriptively and without implication."
sources:
  - url: https://example.com/announcement
    title: Source title
    kind: press
    origin: example-press
    accessed: 1970-01-01
  - url: https://other.example.com/coverage
    title: Independent coverage
    kind: secondary
    origin: other-press
    accessed: 1970-01-01
contributor: unassigned
lane: core
supersedes: []
contradicts: []
---

Optional context. The claim itself lives in frontmatter so it can be validated,
filtered by confidence and age, and safely gated out of outbound collateral.

Confidence rules the validator enforces:

- `confirmed` needs at least one vendor-primary, analyst-tier1 or first-hand source.
- `likely` needs two or more sources with DISTINCT origins. Two outlets rewriting
  the same wire story share an origin and do not qualify.
- `rumour` is permitted here but can never reach a vendor page or collateral.
