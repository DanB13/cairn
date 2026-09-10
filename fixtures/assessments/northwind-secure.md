---
schema_version: 1
vendor: northwind-secure
updated: 2026-09-09
author: fixture-curator
review_by: 2026-12-09
threat_level: high
decisions:
  - date: 2026-08-18
    decision: Lead with endpoint coverage in any deal where Northwind is present.
    rationale: Two observed evaluations named endpoint DLP as a requirement Northwind cannot meet.
    author: fixture-curator
    signals:
      - sig-2026-08-15-northwind-secure-01
  - date: 2026-09-09
    decision: Stop quoting Northwind posture bundling until the conflict resolves.
    rationale: The June and September packaging signals contradict each other and both stand.
    author: fixture-curator
    signals:
      - sig-2026-06-18-northwind-secure-01
      - sig-2026-09-08-northwind-secure-01
---

# Northwind Secure: assessment

<!-- policy: interpretive -->

## Where they threaten us

Converged coverage across two lanes lets them run a single-vendor story we
cannot match in the mid-market. What would change our mind: sustained evidence
that the posture module is shallow enough that buyers treat it as a checkbox.

## Where we win

Regulated buyers with mixed estates and an endpoint requirement. This is a
pattern across two observed evaluations, not a single anecdote.

## Where we lose

Time-to-value bake-offs where the buyer scopes to SaaS only. Their positioning
is built for exactly this and ours is not.

## Battlecard

**Objection:** "Northwind covers both DLP and posture in one product."
**Response:** Ask which posture findings the buyer intends to act on, then ask
how those are remediated. Coverage breadth and remediation depth are different
questions.

**Objection:** "Northwind is cheaper."
**Response:** As of 2026-08-15 their Business tier lists at 22 dollars per seat
per month, up from 18. Confirm whether the posture module is quoted separately,
because the September signal lists it as a paid add-on.

## Decision trail

See frontmatter. This is why the interpretation layer exists: the reasoning
survives past the chat session that produced it.
