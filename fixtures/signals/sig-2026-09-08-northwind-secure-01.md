---
schema_version: 1
id: sig-2026-09-08-northwind-secure-01
vendor: northwind-secure
date: 2026-09-08
filed: 2026-09-09
type: packaging
confidence: confirmed
claim: "The Northwind Secure posture module is listed as a paid add-on priced separately from the Business tier."
sources:
  - url: https://northwind.example/pricing
    title: Northwind Secure pricing page
    kind: vendor-primary
    origin: northwind
    accessed: 2026-09-08
contributor: fixture-reviewer-a
lane: dspm
supersedes: []
contradicts:
  - sig-2026-06-18-northwind-secure-01
---

Demonstrates contradiction. Nothing is overwritten: both dated claims stand, and
the conflict is raised in the vendor page's open questions for a human to
resolve.
