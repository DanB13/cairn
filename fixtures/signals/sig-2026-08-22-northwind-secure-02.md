---
schema_version: 1
id: sig-2026-08-22-northwind-secure-02
vendor: northwind-secure
date: 2026-08-22
filed: 2026-08-24
type: funding
confidence: likely
claim: "Northwind Secure raised a Series B of approximately 40 million US dollars."
sources:
  - url: https://press-a.example/northwind-series-b
    title: Northwind raises Series B
    kind: press
    origin: press-a
    accessed: 2026-08-24
  - url: https://press-b.example/funding-roundup
    title: Weekly funding roundup
    kind: secondary
    origin: press-b
    accessed: 2026-08-24
contributor: fixture-reviewer-b
lane: saas-dlp
supersedes: []
contradicts: []
---

Demonstrates the independence rule: two sources with DISTINCT origins. Had both
articles carried origin press-a, the validator would reject the likely tag.
