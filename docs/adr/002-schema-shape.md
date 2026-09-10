# ADR 002: Schema shape and what is locked

**Status.** Accepted. `schema_version: 1`.

## Context

Once the consumption path is "clone it and point Claude at it, later wrap an MCP
server", the frontmatter stops being metadata and becomes the interface contract.
It is also the only thing that is expensive to change after adopters have seeded
instances.

## The tension

Thin frontmatter with everything else as prose is pleasant to write and destroys
the contract: if a claim's confidence and date live inside a paragraph, CI cannot
validate them, freshness cannot be computed per data type, and the collateral
gate is impossible, because you cannot filter out rumours when "rumour" is a word
in a sentence.

Fully structured intel makes files unreadable, filing tedious enough that people
stop, and forces a migration every time the market shifts.

## Decision

Structure exactly what a check or a filter depends on. Leave the rest as prose.

**Structured:** vendor identity and aliases, tier, lanes, flags, the three dates,
and every claim as a record carrying id, type, claim, confidence, sources,
origins, contributor and cross-references.

**Prose:** snapshot, positioning, product surface, open questions, and all
assessment reasoning.

### One signal per file

Claims live in `signals/sig-<date>-<vendor>-<nn>.md`, one per file, rather than
as a growing array in vendor frontmatter.

An array bloats, and every contribution touches the same lines, so pull requests
conflict constantly. One file per claim gives three properties: contributions
never conflict, retention is a file move, and each claim validates independently.

### No generated content inside vendor pages

The usual objection to signal files is that someone browsing the vendor page on
GitHub cannot see recent moves inline, which pushes toward generating that
section in CI: a bot with write access, committed generated content, and a class
of "somebody hand-edited the generated block" bugs.

Since browsing happens through Claude and later MCP rather than GitHub's file
view, none of that is needed. Signal files plus a generated `index.json` serve
every query, and vendor pages stay prose and frontmatter. A consumption decision
avoided real complexity.

## Locked in version 1

Changing any of these means migrating every seeded instance:

- `slug` as permanent vendor identity. A rename is a new slug plus `status:
  merged` and `merged_into` on the old one.
- The three dates: `last_reviewed`, `data_as_of`, `reverify_by`.
- The signal record shape, including `sources[].origin` for independence checking.
- The `confidence` enum: `confirmed`, `likely`, `rumour`.
- `schema_version` itself.

## Deliberately deferred

These are additive and safe to change later:

- Lane vocabulary, which is profile-driven rather than schema-driven.
- Assessment body structure.
- Collateral metadata beyond `collateral_safe`.

## Why the lane vocabulary is open in the schema and closed in the profile

`lanes` is a free array in `vendor.schema.json` and validated against the active
profile at check time. Markets differ too much for one enum, and hardcoding a
market's lanes into the schema would make every adopter in a different market
either fight the schema or fork it. The profile is the extension point.
