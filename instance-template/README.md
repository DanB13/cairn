# Competitive intelligence instance

Private data repository built on
[cairn](https://github.com/danboddington/cairn).

**This repository must stay private.** It holds pricing intel, win and loss
patterns and battlecards. See `SETUP.md`.

## Layout

| Path | Layer | Holds |
|---|---|---|
| `tiers.yaml` | governance | Canonical coverage list. Curator-owned. If a vendor page disagrees, this wins. |
| `config.yaml` | governance | Profile, governance, shelf life, style, collateral policy. Curator-owned. |
| `vendors/` | descriptive | One page per competitor. Observed intel only. |
| `signals/` | descriptive | One claim per file, each with confidence, sources and a contributor. |
| `assessments/` | interpretive | Our reading, battlecards, and the dated decision trail. The only vendor-scoped place interpretation is permitted. |
| `product/` | reference | Our own product, the anchor for comparison. Owned, with a shelf life. |
| `archive/` | retention | Aged signals, still valid, out of the live query surface. |
| `brand/` | assets | Brand guidelines and templates for generated collateral. |
| `index.json` | generated | Built by CI. Read this first; it answers most questions without opening files. |

## Daily use

```bash
/compete                        # digest
/compete <vendor>               # deep dive
/compete <vendor> --compare     # against our own product
/compete <vendor> --collateral  # gated source material for outbound content
/competeupdate <vendor> ...     # file intel as a pull request
```

## Checks

```bash
python3 .framework/tools/validate.py .
python3 .framework/tools/build_index.py .
python3 .framework/tools/collateral_gate.py . --vendor <slug>
python3 .framework/tools/archive.py .          # dry run
python3 .framework/tools/check_visibility.py .
```
