# The content contract

Each rule exists because of a specific failure mode. The reasoning matters more
than the rule, because a rule whose purpose is forgotten gets disabled the first
time it is inconvenient.

## 1. Descriptive and interpretive layers are separate files

**Rule.** `vendors/<slug>.md` records observations, each with a source and a
date. `assessments/<slug>.md` holds our reading, battlecards, objection handling
and the decision trail.

**Why.** The original design forbade interpretation on vendor pages, then gave
the vendor page template a battlecard section and strengths and weaknesses
sections. A battlecard is definitionally a sales play, and "weakness" is a
judgement relative to someone's evaluation criteria. The contract forbade exactly
what the template required, so the first implementer would have hit the wall on
day one, the phrase scan would have fired constantly, and someone would have
disabled it for that section. Contracts do not die by being wrong; they die by
being unenforceable in one place and therefore ignored everywhere.

Two consequences worth noticing:

- The descriptive sections are named "Capabilities observed" and "Gaps observed
  against stated buyer criteria" rather than strengths and weaknesses, and the
  gap section requires the buyer criterion to be named. That turns a verdict back
  into an observation.
- The interpretive layer is where reasoning survives. Push all interpretation
  into skill output and it evaporates with the chat session, leaving a perfect
  record of what competitors did and none of what you concluded. The `decisions`
  array in assessment frontmatter is the durable decision trail.

## 2. Interpretation detection warns, it does not block

**Rule.** Style checks hard-fail. The interpretation scan emits warnings.

**Why.** Interpretation is semantic, not lexical. A phrase list catches "this
creates a wedge" and sails past "their pricing model will struggle in
mid-market", which is pure interpretation with no flagged phrase. It also
false-positives on quoted vendor copy. A control that is both leaky and annoying
is the worst combination: it trains contributors to route around it while
providing false assurance.

So the scan is honest about what it is. It skips block quotes, because quoting a
vendor is reported speech rather than our reading. It respects
`<!-- policy: interpretive -->` markers, so the assessment layer is never
flagged. And it never blocks a merge, because deciding whether a sentence is an
observation or a reading is the reviewer's actual job.

## 3. Confidence is checked against source kind and independence

**Rule.**

- `confirmed` needs at least one source of kind `vendor-primary`,
  `analyst-tier1` or `first-hand`.
- `likely` needs two or more sources with **distinct `origin` values**.
- `rumour` may exist as a signal, never appears on a vendor page, and never
  passes the collateral gate.

**Why.** "Two or more independent secondary sources" cannot be checked by
counting, because two outlets rewriting the same wire story are not two sources.
The `origin` field records the originating publication rather than the one you
happened to read, which makes independence mechanically checkable. Set it
honestly and the rule works; set it to whichever site you opened and you have
defeated it, which is why the field is documented rather than inferred.

`analyst-tier1` is further constrained by `sources.analyst_tier1` in
`config.yaml`, so "tier one analyst" means a named list rather than a judgement
made in the moment.

## 4. Confidence describes filing time, never current truth

**Rule.** Confidence is always rendered with the claim's age. Freshness is
tracked separately, per signal type.

**Why.** The original design had a careful shelf-life model for data and none for
confidence, treating them as orthogonal. They are not. A `confirmed` pricing
claim from fourteen months ago is not still confirmed: the source was sound and
the world moved. Usable trust is a function of both, so the two are always shown
together and the collateral gate applies both independently.

## 5. Contradictions are recorded, never resolved by overwriting

**Rule.** A conflicting claim names the claim it contradicts. Both dated claims
stand. The conflict goes into the vendor page's open questions. Both sides are
blocked from outbound collateral until a human resolves it.

**Why.** Overwriting destroys the evidence that a change happened and when. And
an unresolved contradiction means we do not know which claim holds, so asserting
either in a customer-facing deck is a guess dressed as a fact. Blocking both
sides is deliberately conservative: the framework's own fixtures demonstrate it,
where a June claim that a module is bundled and a September claim that it is a
paid add-on are both withheld.

## 6. Untaggable claims are reported, never dropped

**Rule.** A claim that cannot be given a confidence and a source is refused with
an explanation of what is missing.

**Why.** Silent dropping loses the intel and the contributor. Someone who files
three things and sees none appear stops filing.

For legacy migration the equivalent rule is that untaggable claims go to the
"Historical and migrated material" section, are never presented as current, and
are reported to the user by name.

## 7. The tier index is the source of truth

**Rule.** `tiers.yaml` is canonical for coverage. A disagreement between it and a
vendor page is an error, and the page is wrong.

**Why.** Coverage is a governance decision, not a content one. Under the git
model there are no page identifiers to drift, so the drift that remains is a
tier disagreement, and the validator names which side wins so nobody has to
adjudicate it.

## 8. Style is mechanical, so it hard-fails

**Rule.** House style violations block. The default rule set forbids en and em
dashes; extend it with `style.forbid_patterns`.

**Why.** This is the one place where a string scan is exactly the right tool. It
is decidable, it has no false positives, and models emit em dashes constantly
regardless of instruction. Enforce it programmatically rather than hoping.

## 9. Read before write, always

**Rule.** Reconstruct from what is on disk now. Pull first.

**Why.** It was correctly identified as the most common source of errors in the
original design. Under git the mechanical risk is largely handled: one signal per
file means contributions do not touch shared lines, and a genuine conflict is
detected rather than silently resolved. The rule survives because the reasoning
risk does not go away: filing a claim that supersedes something you have not read
produces a technically clean commit that is wrong.
