# CAIRN

**C**ompetitive **A**nalysis: **I**ncremental **R**ecords, **N**otarised

A git-native framework for running competitive intelligence as a governed
repository rather than a wiki page that rots.

A cairn is a trail marker built one stone at a time by everyone who passes it.
That is the contribution model here: every piece of intel is exactly one signal
file, added and never edited in place, so contributions never collide and the
trail stays legible for whoever comes next. Each stone is notarised, carrying the
source, the date, the contributor and a confidence grade that is checked rather
than asserted.

Two ideas do most of the work:

1. **Observed intel and interpretation are separate layers.** Vendor pages record
   what was observed, with a source and a date. Battlecards, threat readings and
   decisions live in a paired assessment file. Neither layer contaminates the
   other, so facts stay durable while opinions churn.
2. **The contract is executable.** Confidence tags, source independence, freshness,
   coverage and style are checked in CI, not asked for in a style guide. A claim
   that cannot be tagged and sourced does not merge.

Everything else follows from putting the data in git: review is a pull request,
governance is `CODEOWNERS`, the audit trail is the commit history, rollback is
`git revert`, and concurrent edits conflict loudly instead of silently
overwriting each other.

## Public framework, private data

This repository is the **framework**. It contains no competitive intelligence:
the only vendors here are invented, and they exist to test the validators.

Your seeded instance is a **separate private repository**. The framework refuses
to seed into a public one.

```
public   cairn/   schemas, validators, skills, profiles, docs
private  your-ci-data/              vendors, signals, assessments, config, brand
```

Do not fork this repository to hold your data. GitHub does not permit a fork of a
public repository to be made private, so a fork cannot hold it safely. Follow
[instance-template/SETUP.md](instance-template/SETUP.md) instead.

## Two ways to use it

**As a Claude Code plugin**, for the everyday path:

```bash
/plugin install cairn
```

**As a clonable framework**, if you want to adapt it or drive it with your own
tooling. Everything here is plain markdown, JSON Schema and dependency-free
Python 3:

```bash
git clone https://github.com/danboddington/cairn
python3 tools/validate.py fixtures
```

Both modes ship from this repository, so there is one source of truth and
adopters are never stranded on an old copy.

## Quick start

```bash
git clone https://github.com/danboddington/cairn
cd cairn

python3 tools/selftest.py                  # 18 contract checks, proven to fire
python3 tools/validate.py fixtures         # the synthetic instance validates
python3 tools/build_index.py fixtures      # generate the query index
python3 tools/collateral_gate.py fixtures --vendor northwind-secure
```

The last command is the one worth watching. It blocks a rumour, a claim past its
shelf life, a superseded claim, and both sides of an unresolved contradiction,
then prints a provenance appendix for what survived.

## The three skills

Split by write risk, so permissions fall on natural boundaries.

| Skill | Job | Writes | Who |
|---|---|---|---|
| `/compete` | Digests, deep dives, comparisons, gated collateral source material | No | Everyone |
| `/competeupdate` | File intel as a reviewed pull request | Via pull request | Everyone, reviewed |
| `/competeseed` | Stand up an instance, migrate legacy material | Bulk, to a branch | Curators |

## Repository layout

| Path | What it is |
|---|---|
| `schema/` | JSON Schema for every file type. The interface instances depend on. |
| `templates/` | Starting files for vendors, signals, assessments, product, config. |
| `profiles/` | Tier and lane vocabularies per market. Keeps market specifics out of the schema. |
| `skills/` | The three skill definitions. |
| `tools/` | Validators and generators. Dependency-free Python 3. |
| `fixtures/` | Synthetic instance. Invented vendors only. Doubles as the test suite. |
| `instance-template/` | Copy this into your private repository. |
| `docs/` | Content contract, schema reference, governance, collateral, migrations. |

## The content contract

Enforced by `tools/validate.py`, proven by `tools/selftest.py`.

1. **Descriptive pages hold observations only.** Interpretation belongs in
   `assessments/<slug>.md`. The check warns rather than blocks, because
   interpretation is a semantic property a phrase list cannot judge reliably; it
   exists to prompt a reviewer, not to gate a merge.
2. **Every claim carries a confidence tag, sources and a date.** `confirmed`
   needs a vendor-primary, tier-one analyst or first-hand source. `likely` needs
   two or more sources with **distinct origins**, so two rewrites of one wire
   story do not qualify. `rumour` may exist as a signal, never on a vendor page,
   and never in outbound collateral.
3. **Confidence never asserts current truth.** It describes the claim at filing
   time and is always rendered with the claim's age.
4. **Contradictions are never overwritten.** Both dated claims stand, the conflict
   is raised in open questions, and both sides are blocked from collateral until
   a human resolves it.
5. **Untaggable claims are reported, never dropped silently.** Losing someone's
   intel without telling them is how you lose the contributor too.
6. **The tier index wins.** `tiers.yaml` is the source of truth for coverage. If a
   vendor page disagrees, the page is wrong.
7. **Style is mechanical, so it hard-fails.** Everything semantic warns instead.

Read [docs/content-contract.md](docs/content-contract.md) for the reasoning
behind each rule.

## Design decisions

The two choices everything else rests on are recorded as decision records:

- [ADR 001: git as the substrate](docs/adr/001-git-as-substrate.md)
- [ADR 002: schema shape and what is locked](docs/adr/002-schema-shape.md)

## Adapting it to your market

Two things are separate here, and blurring them is the usual mistake.

**Who you are** lives in `config.yaml` under `organisation`: industry, size,
funding stage, segments, and the criteria your buyers state as must-haves. It is
private to your instance, it is required, and `/competeseed` interviews you for
it on first run. Three of those fields do real work rather than sitting there as
metadata: `size` and `stage` calibrate which vendors are plausibly head to head,
and `icp.must_have_criteria` is the source for every vendor page's "Gaps observed
against stated buyer criteria" section, so gaps are recorded against a stable
list instead of whatever the writer remembered.

**What vocabulary you use** is the profile: a tier and lane vocabulary, closed so
the validator can reject invented lanes. Profiles are deliberately market-level
and reusable, which means your competitors could use the same one. Copy
`profiles/generic.yaml`, close the lanes around your market, and point
`config.yaml` at it. Profiles resolve from your instance's own `profiles/`
directory first, so adapting one never requires forking this repository. Two
worked examples ship here: `data-security.yaml` and `devtools.yaml`.

Three things are first-class rather than optional, because in most markets they
are structural:

- **Platform-native competition.** Capability bundled into a suite the buyer
  already pays for. Frequently the real alternative in a deal, and it never
  appears on a vendor shortlist.
- **Dual-role vendors.** Simultaneously a competitor and a platform you integrate
  with. Partner goodwill is a real asset and competitive positioning can damage
  it, so the flag exists to keep the two tracks separate.
- **The status quo.** Doing nothing wins deals. It has a tier, a page and signals,
  because a framework that cannot hold the alternative with no marketing site is
  missing the most common competitor.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
