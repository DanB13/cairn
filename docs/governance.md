# Governance

## Two roles, not one

The original design gated seeding, tiering, vendor addition, spec changes and
queue review all behind a single unnamed "owner". That bundles two genuinely
different jobs:

- **Tiering and structure** is quarterly, strategic, and needs one decisive
  person.
- **Queue review** is daily, clerical, and needs whoever is available.

Bundled, one of two things happens: the clerical work crowds out the strategic,
or the strategic person refuses the clerical load and review rots. So the roles
are split.

| Role | Owns | Frequency | Count |
|---|---|---|---|
| Curator | `tiers.yaml`, `config.yaml`, structure, schema upgrades | Low | One, plus a named deputy |
| Reviewer | The intel pull request queue | High | Plural |
| Product owner | `product/` own-product reference | Quarterly | One |

Declared in `config.yaml` under `governance`, enforced by
`.github/CODEOWNERS`.

## Making it mechanical

`CODEOWNERS` alone is documentation. It becomes a control only with branch
protection on the instance repository:

- Require a pull request before merging
- Require review from Code Owners
- Require the `contract` status check to pass

Without this, anyone can commit to the default branch and bypass both review and
the content contract. This is step 6 of `SETUP.md` and it is the step people
skip.

## Two rules that close the obvious gaps

- **Nobody merges their own submission.** Including Curators. The audit trail is
  the point, and a self-merged change has none.
- **The deputy is named in advance.** Not "ask around when the Curator is on
  leave". An unavailable singleton is how a queue silently stops moving.

## Queue triage

Default `triage_order` is `tier-weighted`, not oldest-first.

Oldest-first is backwards for competitive intelligence: a three-week-old pricing
tweak matters less than yesterday's acquisition. And notification does not add
reviewer capacity, it only makes the backlog louder, which is why capacity is
addressed by making Reviewers plural instead.

Pull requests older than `governance.queue_ttl_days` (default 30) auto-close with
a note. Stale intel should expire rather than accumulate: a queue nobody can
clear stops being read at all.

## What "open to everyone" does and does not mean

Filing intel is open to everyone. Reading is open to everyone with repository
access, and that access is the read tier: there is no per-page permission model,
because the private repository boundary is the control.

Decide deliberately whether everyone in the organisation should have it. A store
of pricing intelligence, win and loss patterns and battlecards is among the more
damaging things to leak, and treating broad access as an unexamined default is
the choice the original design made silently.

## Success metrics

Nothing in the original design said what working looked like, and this system's
failure mode is quiet decay rather than loud breakage. Track at least:

- Signals filed per month, by contributor
- Percentage of vendors inside their freshness window (`attention.overdue_vendors`
  in `index.json`)
- Median review latency, and open pull request age
- Open contradictions outstanding
- Tier 1 vendors without a current assessment
- Collateral generated, and claims blocked by the gate

The first four come straight out of `index.json` and the pull request list.
