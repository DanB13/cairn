---
schema_version: 1
slug: example-vendor
name: Example Vendor
aliases: []
tier: tier-2
lanes:
  - core
flags:
  dual_role: false
  convergence: false
  platform_native: false
  status_quo: false
parent_vendor: null
cadence: monthly
last_reviewed: 1970-01-01
data_as_of: 1970-01-01
reverify_by: 1970-01-02
owner: unassigned
status: active
---

# Example Vendor

<!-- policy: descriptive -->
<!--
  EVERY section below is descriptive. Record what was observed, with a source.
  Strategic reading, battlecards, objection handling and win themes belong in
  assessments/<slug>.md, which is the interpretation layer. The validator warns
  when interpretation appears here; a reviewer makes the final call.
-->

## Snapshot

One paragraph of observed fact. What the company sells, to whom, at what scale.
No assessment of how dangerous they are.

## Capabilities observed

What the product demonstrably does, each line sourced. Note that this section is
deliberately not called "strengths": a strength is a judgement relative to a
frame, and that judgement lives in the assessment.

## Gaps observed against stated buyer criteria

Absences and limits observed against criteria buyers actually stated, with the
criterion named. Not "weaknesses", for the same reason as above.

## Open questions

Things we do not know, and contradictions raised by conflicting signals. A
contradiction never overwrites an earlier claim; it is recorded here and both
dated claims stand.

## Positioning and messaging

Their words, quoted and dated. Use block quotes for vendor copy so the
interpretation scan does not flag their language as ours.

## Product surface

Modules, integrations, platform coverage, deployment model.

## Pricing and packaging

List pricing, tiers, packaging shape, discount behaviour observed in deals.
Shelf life is short here: check the date before repeating any figure.

## Partner intel

Channel, OEM and technology relationships. Set the dual_role flag if they are
also an integration partner.

## Recent moves

Not maintained by hand. Signals live one-per-file under signals/ and are keyed
to this vendor; run `/compete <slug>` or read index.json for the current list.

## Historical and migrated material

Legacy content whose claims could not be tagged or sourced. Kept for context,
never presented as current.
