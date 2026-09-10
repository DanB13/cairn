# Setting up a private instance

This directory is the starting point for a **private** competitive-intelligence
instance. The framework stays public; your data does not.

## 1. Create a private repository

```bash
gh repo create ACME/ci-data --private
```

Do not fork the public framework. GitHub does not allow a fork of a public
repository to be made private, so a fork cannot hold your data safely.

## 2. Copy this directory in

```bash
cp -r instance-template/. /path/to/ci-data/
cd /path/to/ci-data && git init && git add . && git commit -m "Seed instance"
```

## 3. Attach the framework for tooling

```bash
git clone https://github.com/DanB13/cairn .framework
```

`.framework/` is gitignored. Alternatively install the plugin and let the skills
locate the tools.

## 4. Install the guardrail

```bash
cp .framework/hooks/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push
python3 .framework/tools/check_visibility.py .
```

The second command must report that the instance is not public. If it cannot
resolve visibility, fix that before adding any real intel.

## 5. Fill in who you are, then governance and the profile

Edit `config.yaml`. The `organisation` block ships with placeholders that
deliberately fail validation, because an instance that does not know its own
size, stage and buyer criteria cannot tier competitors sensibly. Run
`/competeseed` and it will interview you, or fill it in by hand.

The field worth real thought is `icp.must_have_criteria`. Every vendor page
records gaps against that list, so a vague list produces vague gap sections
across the whole repository.

Then the rest:

- `profile`: pick from the framework's `profiles/`, copy one into this
  repository's own `profiles/` and adapt it, or write your own. Instance
  profiles override framework ones, so you never need to fork the framework to
  get the vocabulary you want.
- `governance.curators`: who owns tiering and structure. Low frequency.
- `governance.reviewers`: who works the pull request queue. Plural, so review
  never depends on one person being available.

Edit `.github/CODEOWNERS` and replace `@CURATOR`, `@CURATOR_DEPUTY`,
`@REVIEWERS` and `@PRODUCT_OWNER` with real handles.

## 6. Turn on branch protection

In repository settings, protect the default branch:

- Require a pull request before merging
- Require review from Code Owners
- Require the `contract` status check to pass

Without this, `CODEOWNERS` is documentation rather than a control, and the
content contract can be bypassed by committing straight to the default branch.

## 7. Own the product reference

Edit `product/our-product.md`. Give it a named owner and a real `reverify_by`
date. Record your own gaps honestly: comparison output is only as good as this
file, and a stale self-description produces confidently wrong comparisons.

## 8. Seed

Run `/competeseed` with your vendor list, or create vendor files by hand from
`.framework/templates/`. Then:

```bash
python3 .framework/tools/validate.py .
python3 .framework/tools/build_index.py .
```
