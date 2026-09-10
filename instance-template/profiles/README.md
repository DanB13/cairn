# Instance profiles

A profile closes the tier and lane vocabularies so the validator can reject
invented lanes and typos. It is **vocabulary, not identity**: who your
organisation is lives in `config.yaml` under `organisation`.

Profiles resolve from this directory first, then from the framework's
`profiles/`. So you can:

- **Use a shipped profile.** Set `profile: data-security` in `config.yaml` and
  add nothing here.
- **Adapt one.** Copy `.framework/profiles/data-security.yaml` here, edit the
  lanes, and point `config.yaml` at your copy. A file here with the same name as
  a shipped one wins, so you can override without forking the framework.
- **Write your own.** Start from `.framework/profiles/generic.yaml`.

Getting the lane vocabulary right matters more than it looks. Lanes are how
convergence is detected and how vendors surface in more than one place, so a
vocabulary that is too coarse hides overlap and one that is too fine makes every
vendor look unique. Start coarse, split a lane when two vendors in it stop being
comparable.

`/competeseed` will interview you and can generate a profile here from your
answers.
