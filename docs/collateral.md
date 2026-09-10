# Generating collateral

Outbound content is the highest-consequence output in this system: interpretation,
leaving the building, in front of buyers. Two rules follow.

## Source from the assessment layer

Collateral reads positioning and battlecard language from
`assessments/<slug>.md`, never from vendor pages. Vendor pages are descriptive by
contract, and generating persuasive content from raw observations produces
unpredictable editorialising that nobody reviewed.

This is the main practical reason the interpretive layer exists. Without it, deck
generation reaches straight into observed intel and invents the argument as it
goes.

## The gate is a hard fail

```bash
python3 tools/collateral_gate.py <root> --vendor <slug> --appendix out/provenance.md
```

Blocked, in order:

1. **Rumour.** Not configurable. A rumour on an internal page is untidy; the same
   rumour in a customer deck is a credibility problem.
2. **Below `collateral.min_confidence`.** Default `likely`.
3. **Older than `collateral.max_claim_age_days`.** Default 180.
4. **Past the shelf life for its signal type.**
5. **Superseded.**
6. **Either side of an unresolved contradiction.** Until a human picks a side we
   do not know which claim holds, and asserting either is a guess.
7. **`collateral_safe: false`.** An explicit veto on an otherwise passing claim.

There is no override flag, by design. If a claim you need is blocked, the fix is
to resolve the underlying problem: re-verify the pricing, resolve the
contradiction, find a second independent source. Not to bypass the check.

`--require <id>` exits non-zero if a named claim is blocked, which is what you
want in a pipeline that must not silently ship a thinner deck than intended.

## Ship the appendix

Every run emits a provenance appendix: claim, confidence, observation date, age
and sources. Keep it with whatever you generate even when the artefact does not
display it, so any figure can be traced before somebody says it on a call.

This is also where the confidence-decay rule earns its keep. Internally, a stale
`confirmed` claim is a minor annoyance. In a deck, it is the thing that gets you
contradicted live by a buyer who checked the pricing page that morning.

## Brand assets

Brand guidelines and templates live in the instance under `brand/`, not in the
public framework, because they are company-specific. They govern presentation
only. Nothing in `brand/` changes which claims are permitted.

## Do not commit generated decks

The instance `.gitignore` excludes `out/` and `*.pptx`. A committed deck outlives
the gate that approved it: six months later it is a stale artefact with no
freshness check, and someone will send it. Regenerate instead.
