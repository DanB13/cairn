---
schema_version: 1
vendor: example-vendor
updated: 1970-01-01
author: unassigned
review_by: 1970-01-02
threat_level: moderate
decisions: []
---

# Example Vendor: assessment

<!-- policy: interpretive -->
<!--
  This is the ONLY vendor-scoped file where interpretation is permitted, and it
  is the only file collateral generation reads. Be explicitly opinionated, date
  everything, and cite the signal ids your reading rests on.
-->

## Where they threaten us

Our reading, with the signal ids it rests on. Say what would change our mind.

## Where we win

Observed wins and the pattern behind them. Cite deals or signals.

## Where we lose

Observed losses and the pattern behind them. Being honest here is the whole
value of the file.

## Battlecard

Positioning against them, and objection handling. This lives here rather than on
the vendor page because it is a sales play, not an observation.

**Objection:** "..."
**Response:** "..."

## Decision trail

Recorded in frontmatter under `decisions`, so it survives beyond chat output.
Each entry carries a date, the decision, the rationale and the signals cited.
