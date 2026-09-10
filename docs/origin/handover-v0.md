> **Historical document. Superseded by this repository.**
>
> This is the original design handover that the framework was built from. It is
> kept for provenance: the reasoning behind what changed is recorded in
> [ADR 001](../adr/001-git-as-substrate.md), [ADR 002](../adr/002-schema-shape.md)
> and [the content contract](../content-contract.md).
>
> Do not implement from this document. Three things in it are known to be wrong:
> the vendor page template contradicts its own rule 1 by requiring a battlecard
> section on a descriptive page; full-body writes have no concurrency control, so
> concurrent edits are silently destroyed; and governance rests on a single
> unnamed person. All three are resolved in the current design.

---

# Competitor Intelligence Skill: Handover

A generic, SaaS-neutral design for a competitive-intelligence (CI) skill set backed by a wiki/knowledge base (e.g. Confluence, Notion). The work is split into three skills with one shared content contract.

---

## Why three skills

A single CI skill conflates three different jobs with different risk profiles: bulk-creating the repository, reading it, and changing it. Splitting them keeps each surface simple and lets you lock down the destructive ones.

| Skill | Trigger | Job | Writes? |
|---|---|---|---|
| Seed | `/competeseed` | Stand up the repository: hub, tier index, vendor page scaffolds, logs, templates | Yes (bulk, one-off) |
| Query | `/compete` | Read and synthesise: digests, deep dives, comparisons | No |
| Update | `/competeupdate` | File new intel into existing pages and logs | Yes (incremental) |

The split also clarifies governance: `/competeseed` and structural edits are an admin/owner job; `/compete` is open to everyone; `/competeupdate` is open to contribute but gated by review before anything lands.

---

## Shared content contract (applies to all three)

These rules are the reason the data stays trustworthy. Enforce them at write time, not just by convention.

1. **Descriptive pages hold observed intel only.** Vendor pages record what was observed, never strategic interpretation. No "what this means for us", "this creates a wedge", sales plays, or win/loss theses in the page body. Interpretation lives in skill *output* (digests, comparisons) and in dedicated cross-vendor pages or comments.
2. **Confidence tag on every claim.** Confirmed (vendor's own source / first-hand / tier-1 analyst), Likely (two-plus independent secondary sources), Rumour (single unverified source). Untaggable claims are dropped.
3. **Source and contributor attribution on every entry.** Which source, what date, who filed it.
4. **Read before write, always.** Reconstruct from the live page, never from memory or a prior session summary. This is the single most common source of errors.
5. **House style enforced programmatically.** Whatever your style rules are (e.g. no em-dashes), scan the rendered body string before any write call and fix violations rather than relying on the model to never emit them.
6. **Governance is locked to the owner.** Tier changes, adding/removing vendors, and changing the skill spec are owner-only. Contributors can file intel and suggest changes; suggestions get routed to the owner, not executed.

A useful enforcement pattern across all writes: render the full page body to a local file, run string-level validation (style scan, interpretation-phrase scan, row-count check), then call the update API. Partial updates are not assumed to be supported; send the full body.

---

## Repository structure (created by seed, read by all)

- **Hub / parent page**: entry point and navigation.
- **Tier index**: the canonical vendor list and their tiers. This is the source of truth for "what do we track"; if a page ID elsewhere disagrees, the tier index wins.
- **Vendor pages**: one per tracked competitor, following a fixed template.
- **Signals log**: chronological master feed of every filed signal across all vendors.
- **Market shifts / cross-vendor page**: where multi-vendor themes and interpretation are allowed to live.
- **Usage/analytics log** (optional): one row per skill invocation for auditability.
- **Review queue** (optional): a task tracker (e.g. Jira/Asana) project where pending updates are staged before commit.

### Vendor page template (fixed section order)

1. Snapshot (one descriptive paragraph)
2. Classification table: tier, parent vendor if a sub-brand, product lanes, tracking cadence, last reviewed, data-as-of, re-verify-by
3. Strengths (observed, tagged, sourced)
4. Weaknesses (observed, tagged, sourced)
5. Open questions
6. Positioning and messaging
7. Product surface
8. Pricing and packaging
9. Battlecards / objection handling
10. Partner intel
11. Recent moves (rolling log, newest first): Date, Confidence, Type, Claim, Source, Contributor
12. Historical / migrated material

### Tiering model (generic)

- **Tier 1 Direct**: head-to-head platform competitors. Highest cadence, full pages, deep-dive enabled.
- **Tier 2 Specialists**: single-lane competitors, grouped by product lane. Medium cadence.
- **Tier 3 Emerging / Watch**: thin pages, low cadence, escalate on signal.
- **Platform / Native** and **OEM / Partner** buckets as needed.

Optional refinements worth carrying over: a **dual-role** flag (a vendor that is both competitor and integration partner) and a **convergence** flag (a vendor competing across two or more lanes, surfaced under each lane rather than only its home lane).

---

## Skill 1: `/competeseed` (seed the repository)

**Purpose**: one-off (or occasional) bulk creation of the CI repository from existing scattered material: spreadsheets, old strategy docs, decks, analyst exports, a list of vendors.

**Owner-only.** This skill creates structure and tiering, both of which are governance decisions.

**Inputs it should accept**: a vendor list with proposed tiers, the target wiki space, and any legacy source material to migrate.

**Steps**:
1. Confirm the owner identity and the target space.
2. Create the hub, tier index, signals log, and cross-vendor page if absent.
3. For each vendor on the list, create a vendor page from the template, populated only with whatever observed intel the seed sources contain. Leave sections empty rather than inventing content.
4. Apply the content contract to all generated bodies (tag every migrated claim; if a legacy claim cannot be tagged or sourced, move it to a "historical / unverified" section rather than presenting it as current).
5. Record page IDs back into the tier index.
6. Report what was created and what was skipped.

**Migration patterns for legacy sources**:
- *Historical page, fully migrated*: banner the original, copy content down, link from the vendor page.
- *Still-active doc*: mirror the competitive content to the vendor page, leave the original alone, drop a comment noting the mirror.
- *Cross-vendor matrix*: preserve it as one cross-vendor page, then extract per-vendor rows onto individual pages.

**Guardrails**: idempotent (re-running must not duplicate pages; check for existing pages first). Never overwrites a populated page. Bulk creation is the only mode; it does not update existing intel (that is `/competeupdate`).

---

## Skill 2: `/compete` (query the repository)

**Purpose**: read and synthesise. This is the everyday, open-to-everyone skill. It reads the repository and configured external sources, and produces interpretation in its *output*. It does not write to vendor pages.

**Modes**:

- **`/compete` (digest)**: cross-tier summary of what changed in the period. TL;DR, per-tier activity, cross-vendor themes, open questions, and a freshness check (vendors whose "last reviewed" exceeds a threshold).
- **`/compete [vendor]` (deep dive)**: single-vendor teardown. Snapshot refresh, what changed since last review, positioning, product surface, pricing, recent moves, battlecard, strengths/weaknesses, open questions. A pre-flight staleness check flags old data at the top.
- **`/compete [vendor] --compare` (comparison)**: side-by-side against your own product, pulling an internal reference page. This is the one place strategic recommendation is explicitly welcome, because it is output only.
- **`/compete --help`**: brief in-chat summary and a link to the repository README.

**Sources to scan per invocation** (configurable per user): the wiki hub first, then the user's own intel sources (newsletters, inbox threads, granted file/chat locations), then web search and analyst sites for sparse vendors.

**Staleness handling**: apply shelf-life thresholds per data type (e.g. pricing 6 months, M&A 3 months, headcount 12 months). Flag stale data *in output only*; never silently rewrite a page during a read.

**Key boundary**: `/compete` is read-only. If a digest or deep dive surfaces something worth filing, it hands off to `/competeupdate` (or stages a review item), it does not commit directly.

---

## Skill 3: `/competeupdate` (update the repository)

**Purpose**: file new or newer intel into existing vendor pages and the signals log. Open to all contributors, but gated by review before anything lands.

**Submit flow** (`/competeupdate [vendor] <intel>`):
1. Identify the contributor (no submission without attribution).
2. Confirm the vendor is tracked. If not, it is a tier-level matter: route a request to the owner, do not create the page.
3. Read the live vendor page (read before write).
4. Parse the intel into the standard shape: signal type, claim, confidence, source. If confidence or source is unclear, ask; do not guess.
5. Compute the diff against the live page: net-new, supersedes (name the dated claim), or contradicts (name the conflicting claim).
6. Show the contributor the drafted entry and diff for confirmation, and run the content-contract checks.
7. On confirmation, stage as a review item (a task in the review queue) rather than committing immediately. Return the reference.

**Review flow** (`/competeupdate --review`, owner-only):
1. Walk the open queue oldest-first.
2. Present each item with its proposed entry and diff.
3. Owner approves (commit to vendor page recent-moves log + signals log, with the original contributor attributed), edits (amend then commit), or rejects (commit nothing). Record the decision on the review item as the audit trail.
4. Contradictions never silently overwrite: add the new dated entry and raise the conflict in the vendor's open questions instead.
5. Update "last reviewed" / "data-as-of" when the change is substantive.

**Why staged review**: it keeps fast-moving or unverified intel out of the descriptive pages until a human has checked it, while preserving the contributor's wording and a full audit trail. If review latency becomes a problem, add a push notification on submission; pull-based review is fine to start.

---

## Cross-cutting concerns

- **Identity and attribution**: resolve the calling user once per invocation (from memory; prompt and persist on first run). Every filed signal and every write carries the contributor's name.
- **Per-user configuration**: store each user's intel sources and digest preferences in their own memory, not in the shared repository.
- **Versioning the skills**: keep a single integer version per skill, mirrored in the skill frontmatter and any on-wiki spec page, with a change-history table. Log the running version on each invocation so any action is traceable to a skill version.
- **API/tooling notes to capture in each spec**: the wiki cloud/space IDs, the exact write tool and whether it needs the full page body, the preferred content format for reliable round-tripping, and any known connector quirks (e.g. tool definitions not reloading until a new turn after reconnecting).

---

## Suggested build order

1. Lock the **shared content contract** and the **vendor page template** first; everything else depends on them.
2. Build **`/competeseed`** to stand up the structure.
3. Build **`/compete`** read modes against the seeded structure.
4. Build **`/competeupdate`** last, since it needs the template, the contract checks, and the review queue all in place.

---

## Open questions for whoever picks this up

- Which wiki and which task tracker are the targets, and what are their IDs?
- What is the house-style rule set to enforce programmatically?
- Is staged review required from day one, or is direct-commit-with-audit acceptable for trusted contributors?
- Who is the governance owner, and what exactly is owner-only versus open?