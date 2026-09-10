---
name: competeseed
description: >
  Stand up a new competitive-intelligence instance, or migrate scattered legacy
  material into one. Curator-only, writes in bulk to a branch for review. Use
  when asked to set up, seed, bootstrap or initialise a competitor tracking
  repository, or to migrate existing competitor spreadsheets, decks or wiki
  pages into the framework.
---

# competeseed: stand up an instance

Curator-only. Creates structure and tiering, both of which are governance
decisions rather than content edits.

## Refuse-first checks, in this order

Run these before writing anything. Each is a stop, not a warning.

1. **Visibility.** Run `python3 tools/check_visibility.py <root>`. If it refuses,
   stop and relay its output verbatim. A seeded instance in a public repository
   exposes competitive intel permanently, and no amount of user insistence makes
   that safe to proceed with. Offer to help create a private repository instead.
2. **Curator identity.** Confirm the caller is listed in
   `config.yaml` under `governance.curators`. If `config.yaml` does not exist
   yet, confirm explicitly with the user who the Curator will be and write it.
3. **Target root.** Confirm the instance root with the user. Never infer it from
   a partial match.
4. **Profile.** Confirm which profile in `profiles/` closes the tier and lane
   vocabulary. If none fits, copy `generic.yaml` and adapt it; do not invent
   lanes inline in vendor files, because the validator will reject them.

## Seeding

Write to a branch and open a pull request. Never commit seed output straight to
the default branch: the diff IS the preview, and it is a better one than any
dry-run flag.

1. `git switch -c seed/<date>-<instance>`.
2. Copy `templates/config.yaml` and `templates/tiers.yaml` to the root, filled in.
3. For each vendor on the supplied list, create `vendors/<slug>.md` from
   `templates/vendor.md`. The slug is permanent identity: lower-case, hyphenated,
   and never changed afterwards. A rename is a new slug plus `status: merged` and
   `merged_into` on the old one.
4. Populate only sections the source material actually supports. **Leave sections
   empty rather than inventing content.** An empty section is honest; a plausible
   invented one is a lie the validator cannot catch.
5. Create `assessments/<slug>.md` for every tier-1 vendor, even if it only holds
   open questions. Battlecards and interpretation have nowhere legitimate to live
   without it.
6. Create the own-product reference in `product/` and assign it a named owner and
   a `reverify_by`. Do not leave it unowned; `--compare` depends on it.
7. Convert every legacy claim into a signal file under `signals/`, one claim per
   file, each with confidence, sources and a contributor.
8. Run `python3 tools/validate.py <root>`, then `python3 tools/build_index.py
   <root>`. Fix every error before opening the pull request.
9. Open the pull request and report what was created, what was skipped, and every
   claim that could not be tagged.

## Migrating legacy material

- **Untaggable claims.** If a legacy claim cannot be given a confidence and a
  source, it goes in the vendor page's "Historical and migrated material" section
  and is never presented as current. Report each one to the user by name. Do not
  drop it silently, and do not guess a confidence to make it fit.
- **Fully migrated source.** Banner the original, copy the content down, link back
  from the vendor page.
- **Still-active source.** Mirror the competitive content, leave the original
  alone, and note the mirror on the original.
- **Cross-vendor matrix.** Keep it whole as a cross-vendor document, then extract
  per-vendor rows onto individual pages.

## Guardrails

- **Idempotent by slug.** Before creating `vendors/<slug>.md`, check whether it
  exists. Match on slug, never on title: titles get renamed and near-duplicates
  ("Acme" against "Acme Corp") are indistinguishable by name.
- **Never overwrite a populated file.** Report it as skipped and move on.
- Bulk creation only. Updating existing intel is `/competeupdate`.
- Tiering changes are Curator decisions and belong in `tiers.yaml`, which is
  CODEOWNERS-gated. If the user asks you to retier a vendor mid-seed, confirm they
  are the Curator.
