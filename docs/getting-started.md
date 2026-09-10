# Getting started

## Try the framework without seeding anything

```bash
git clone https://github.com/DanB13/cairn
cd cairn

python3 tools/selftest.py
python3 tools/validate.py fixtures
python3 tools/build_index.py fixtures
python3 tools/collateral_gate.py fixtures --vendor northwind-secure
```

Nothing here needs installing, and every vendor in `fixtures/` is invented.

Worth reading the fixture instance directly. It is deliberately built to
demonstrate the awkward cases rather than the easy ones:

| Fixture | Demonstrates |
|---|---|
| `northwind-secure` | Convergence across two lanes, a supersession chain, an unresolved contradiction, and a rumour that cannot escape |
| `helios-platform` | Platform-native competition and the dual-role flag, where the competitor is also an integration partner |
| `veridian-labs` | A deliberately thin tier 3 page |
| `status-quo` | Doing nothing, tracked as a competitor because it wins deals |

## Set up a real instance

Follow [instance-template/SETUP.md](../instance-template/SETUP.md). The order
matters: create the private repository and confirm the visibility check passes
**before** adding any real intel.

## The first week

1. **Answer the organisation interview.** `/competeseed` asks who you are: size,
   stage, segments, and the criteria buyers state as must-haves. The config will
   not validate until it is filled in, and that is deliberate: you cannot tier
   competitors sensibly without knowing your own size and stage.

   Spend the time on `icp.must_have_criteria`. Every vendor page records gaps
   against that list, so a vague list produces vague gap sections everywhere.
   Use the criteria buyers actually say out loud, not the ones you wish they
   cared about.
2. **Lock the profile.** Pick or adapt one from `profiles/`, or generate one into
   your instance's own `profiles/` directory. Lane vocabulary is the thing you
   will regret leaving loose. Start coarse: too few lanes hide overlap, too many
   make every vendor look unique.
3. **Name the roles.** Curator, deputy, Reviewers, product owner. Put real
   handles in `CODEOWNERS`.
4. **Turn on branch protection.** Until this is done, the contract is advisory.
5. **Write the own-product reference before any competitor page.** Comparison
   output is only as good as this file, and writing it first forces you to state
   your own gaps honestly while nothing is at stake.
6. **Seed tier 1 only.** Four or five vendors. Resist seeding the long tail: a
   thin page nobody maintains is worse than no page, because it reads as current.
7. **File ten signals by hand** before relying on `/competeupdate`. It is the
   fastest way to find out whether your confidence rules and shelf lives are set
   sensibly.

## Common mistakes

- **Seeding the long tail first.** Coverage feels like progress and is not. Tier 3
  pages are meant to be thin.
- **Skipping the assessment file.** Then interpretation has nowhere legitimate to
  live, and it ends up on vendor pages where the next reader mistakes it for
  observation.
- **Setting `origin` to the site you read.** It must be the originating
  publication, or the independence rule for `likely` is defeated silently.
- **Leaving the product reference unowned.** It goes stale, and `--compare` then
  produces confidently wrong output in the one mode that invites recommendation.
- **Treating warnings as noise.** They are the decay signal. If the weekly
  freshness summary is permanently amber, the repository is dying quietly.
