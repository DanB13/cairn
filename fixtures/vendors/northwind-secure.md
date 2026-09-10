---
schema_version: 1
slug: northwind-secure
name: Northwind Secure
aliases: [Northwind, NWS]
tier: tier-1
lanes:
  - saas-dlp
  - dspm
flags:
  dual_role: false
  convergence: true
  platform_native: false
  status_quo: false
parent_vendor: null
cadence: weekly
last_reviewed: 2026-09-01
data_as_of: 2026-08-28
reverify_by: 2026-12-01
owner: fixture-curator
status: active
---

# Northwind Secure

<!-- policy: descriptive -->

## Snapshot

Invented vendor selling SaaS data loss prevention with a posture management
module added in 2025. Sells mid-market and lower enterprise, direct and through
two regional resellers.

## Capabilities observed

- Connectors for six major SaaS applications, listed on their integrations page
  (vendor-primary, 2026-08-28).
- Posture dashboard covering misconfiguration and public-share detection
  (vendor-primary, 2026-08-28).

## Gaps observed against stated buyer criteria

Every criterion in `organisation.icp.must_have_criteria` is addressed, including
where it is not a gap. An unaddressed criterion means the vendor was never
assessed on it.

- **endpoint coverage**: absent. Buyers in two observed evaluations named
  endpoint DLP as a requirement (first-hand, 2026-07-14).
- **eu data residency**: no published option. Criterion raised by one regulated
  buyer (first-hand, 2026-06-30).
- **cross-vendor SaaS coverage**: not a gap. Six connectors observed across
  major SaaS applications (vendor-primary, 2026-08-28).
- **remediation workflow**: unresolved. The posture dashboard surfaces findings;
  whether it acts on them is not established (vendor-primary, 2026-08-28).

## Open questions

- Whether the posture module is sold separately or bundled. Signals conflict.
- Headcount trajectory after the 2026 funding round.

## Positioning and messaging

> "Find and fix SaaS data exposure in an afternoon."

Their language centres on time to value rather than coverage depth
(vendor-primary, 2026-08-28).

## Product surface

Six SaaS connectors, a posture dashboard, and a reporting API. No endpoint or
network component observed.

## Pricing and packaging

Published list pricing, per seat, with the posture module as a paid add-on. See
signals for the current figure and its date before repeating it.

## Partner intel

Two regional resellers named on their partner page. No OEM relationships
observed.

## Recent moves

Maintained as signal files under signals/, not by hand. Read index.json or run
`/compete northwind-secure`.

## Historical and migrated material

None.
