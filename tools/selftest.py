#!/usr/bin/env python3
"""Negative tests for the content contract.

A validator that passes everything is worthless. Each case below copies the
synthetic fixture instance, breaks exactly one thing, and asserts the expected
message appears. Run with: python3 tools/selftest.py
"""

from __future__ import annotations

import contextlib
import io
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

import validate  # noqa: E402

FIXTURES = os.path.join(ROOT, "fixtures")

V = os.path.join("vendors", "northwind-secure.md")
S = os.path.join("signals", "sig-2026-08-22-northwind-secure-02.md")


def edit(root, rel, old, new, count=1):
    path = os.path.join(root, rel)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if old not in text:
        raise AssertionError(f"setup failure: {old!r} not found in {rel}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text.replace(old, new, count))


def append(root, rel, text):
    with open(os.path.join(root, rel), "a", encoding="utf-8") as fh:
        fh.write(text)


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def instance_profile(root, name, extra_lane):
    """Copy a framework profile into the instance and add a lane to it."""
    src = os.path.join(ROOT, "profiles", f"{name}.yaml")
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    text += f"  - id: {extra_lane}\n    label: Instance only lane\n"
    write(root, os.path.join("profiles", f"{name}.yaml"), text)


# Each case: (name, mutation, expected regex, expected_level)
CASES = [
    (
        "em dash is a hard failure",
        lambda r: append(r, V, "\nA line with an em dash \u2014 like this.\n"),
        r"ERROR.*en/em dash is forbidden",
        "error",
    ),
    (
        "rumour is barred from vendor page bodies",
        lambda r: append(r, V, "\n| 2026-09-05 | Rumour | leadership | something |\n"),
        r"ERROR.*rumour-tagged claim in a vendor page body",
        "error",
    ),
    (
        "likely needs independent origins, not just two sources",
        lambda r: edit(r, S, "origin: press-b", "origin: press-a"),
        r"ERROR.*likely requires two or more INDEPENDENT sources",
        "error",
    ),
    (
        "confirmed needs a primary source kind",
        lambda r: edit(
            r,
            os.path.join("signals", "sig-2026-08-15-northwind-secure-01.md"),
            "kind: vendor-primary",
            "kind: press",
        ),
        r"ERROR.*confirmed requires at least one vendor-primary",
        "error",
    ),
    (
        "vendor page missing from the tier index",
        lambda r: edit(
            r, "tiers.yaml",
            "  - slug: veridian-labs\n    tier: tier-3\n", "",
        ),
        r"ERROR.*veridian-labs\.md exists but is not in the tier index",
        "error",
    ),
    (
        "tier index wins a disagreement with the page",
        lambda r: edit(r, "tiers.yaml",
                       "  - slug: northwind-secure\n    tier: tier-1",
                       "  - slug: northwind-secure\n    tier: tier-2"),
        r"ERROR.*tier disagreement for 'northwind-secure'.*index wins",
        "error",
    ),
    (
        "filename must match slug",
        lambda r: shutil.move(os.path.join(r, V),
                              os.path.join(r, "vendors", "northwind.md")),
        r"ERROR.*filename stem 'northwind' must equal slug 'northwind-secure'",
        "error",
    ),
    (
        "untaggable claim is reported, never dropped silently",
        lambda r: edit(r, S, "confidence: likely", "confidence:"),
        r"ERROR.*untaggable claim: confidence is required",
        "error",
    ),
    (
        "supersedes must resolve to a real signal",
        lambda r: edit(
            r, os.path.join("signals", "sig-2026-08-15-northwind-secure-01.md"),
            "  - sig-2026-03-02-northwind-secure-01",
            "  - sig-2026-01-01-northwind-secure-99",
        ),
        r"ERROR.*supersedes points at unknown id",
        "error",
    ),
    (
        "reverify_by must be after last_reviewed",
        lambda r: edit(r, V, "reverify_by: 2026-12-01", "reverify_by: 2026-08-01"),
        r"ERROR.*reverify_by must be after last_reviewed",
        "error",
    ),
    (
        "unrecognised frontmatter field is rejected",
        lambda r: edit(r, V, "status: active", "status: active\nwhat_this_means: bad"),
        r"ERROR.*unrecognised field",
        "error",
    ),
    (
        "lane must exist in the active profile",
        lambda r: edit(r, V, "  - saas-dlp", "  - invented-lane"),
        r"ERROR.*lane 'invented-lane' not in profile",
        "error",
    ),
    (
        "own product reference cannot be stale",
        lambda r: edit(r, os.path.join("product", "our-product.md"),
                       "reverify_by: 2026-12-01", "reverify_by: 2026-01-01"),
        r"ERROR.*own-product reference is past reverify_by",
        "error",
    ),
    (
        "signal cannot reference an untracked vendor",
        lambda r: edit(r, S, "vendor: northwind-secure", "vendor: ghost-vendor"),
        r"ERROR.*references untracked vendor 'ghost-vendor'",
        "error",
    ),
    (
        "future dates are rejected",
        lambda r: edit(r, V, "last_reviewed: 2026-09-01", "last_reviewed: 2027-01-01"),
        r"ERROR.*last_reviewed is in the future",
        "error",
    ),
    (
        "interpretation in a descriptive section warns but does not block",
        lambda r: append(r, V, "\nThis creates a wedge for us in the mid-market.\n"),
        r"warning.*possible interpretation",
        "warning",
    ),
    (
        "quoted vendor copy is not flagged as our interpretation",
        lambda r: append(r, V, "\n> We should be your first call.\n"),
        None,
        "clean",
    ),
    (
        "interpretation in the assessment layer is never flagged",
        lambda r: append(r, os.path.join("assessments", "northwind-secure.md"),
                         "\nWe should pitch against them on coverage.\n"),
        None,
        "clean",
    ),
    # Organisation context: required, and checked rather than decorative.
    (
        "organisation block is required",
        lambda r: edit(r, "config.yaml", "organisation:", "organisation_disabled:"),
        r"ERROR.*missing required field 'organisation'",
        "error",
    ),
    (
        "organisation size must be a known band",
        lambda r: edit(r, "config.yaml", "size: 51-200", "size: medium-ish"),
        r"ERROR.*organisation\.size: 'medium-ish' is not one of",
        "error",
    ),
    (
        "organisation stage must be a known stage",
        lambda r: edit(r, "config.yaml", "stage: series-a", "stage: unicorn"),
        r"ERROR.*organisation\.stage: 'unicorn' is not one of",
        "error",
    ),
    (
        "buyer criteria cannot be an empty list",
        lambda r: edit(
            r, "config.yaml",
            "    must_have_criteria:\n"
            "      - endpoint coverage\n"
            "      - eu data residency\n"
            "      - cross-vendor SaaS coverage\n"
            "      - remediation workflow\n",
            "    must_have_criteria: []\n",
        ),
        r"ERROR.*must_have_criteria: needs at least 1 item",
        "error",
    ),
    (
        "stale organisation context warns",
        lambda r: edit(r, "config.yaml", "reverify_by: 2027-03-01",
                       "reverify_by: 2026-09-05"),
        r"warning.*organisation context is \d+ days past reverify_by",
        "warning",
    ),
    (
        "organisation reverify_by must follow reviewed",
        lambda r: edit(r, "config.yaml", "reverify_by: 2027-03-01",
                       "reverify_by: 2026-08-01"),
        r"ERROR.*reverify_by must be after reviewed",
        "error",
    ),
    (
        "claiming platform competition without tracking any warns",
        lambda r: edit(r, os.path.join("vendors", "helios-platform.md"),
                       "  platform_native: true", "  platform_native: false"),
        r"warning.*no vendor carries the platform_native flag",
        "warning",
    ),
    (
        "an untracked status quo warns",
        lambda r: edit(r, os.path.join("vendors", "status-quo.md"),
                       "  status_quo: true", "  status_quo: false"),
        r"warning.*nothing is tracked in it",
        "warning",
    ),
    (
        "unknown profile is an error",
        lambda r: edit(r, "config.yaml", "profile: data-security",
                       "profile: no-such-market"),
        r"ERROR.*unknown profile 'no-such-market'",
        "error",
    ),
    # Governance wiring: the template placeholders must not survive into a
    # real instance, because GitHub ignores owners it cannot resolve.
    (
        "unreplaced CODEOWNERS placeholder is an error",
        lambda r: edit(r, os.path.join(".github", "CODEOWNERS"),
                       "@fixture-curator @fixture-deputy",
                       "@CURATOR @CURATOR_DEPUTY"),
        r"ERROR.*unreplaced template placeholder '\@CURATOR",
        "error",
    ),
    (
        "generic OWNER placeholder is caught too",
        lambda r: edit(r, os.path.join(".github", "CODEOWNERS"),
                       "@fixture-reviewer-a @fixture-reviewer-b", "@REVIEWERS"),
        r"ERROR.*unreplaced template placeholder '\@REVIEWERS'",
        "error",
    ),
    (
        "missing CODEOWNERS warns that governance is unenforced",
        lambda r: os.remove(os.path.join(r, ".github", "CODEOWNERS")),
        r"warning.*no CODEOWNERS file",
        "warning",
    ),
    (
        "unassigned curator is an error",
        lambda r: edit(r, "config.yaml", "    - fixture-curator", "    - unassigned"),
        r"ERROR.*governance\.curators: 'unassigned' is a placeholder",
        "error",
    ),
    (
        "one person as both Curator and sole Reviewer warns",
        lambda r: edit(
            r, "config.yaml",
            "  reviewers:\n    - fixture-reviewer-a\n    - fixture-reviewer-b",
            "  reviewers:\n    - fixture-curator",
        ),
        r"warning.*same single person is Curator and only Reviewer",
        "warning",
    ),
    # Lead entries: coverage in the index without a page, so an unverified
    # lead is never dressed up as a maintained page.
    (
        "a lead needs no vendor page",
        lambda r: edit(r, "tiers.yaml",
                       "  - slug: veridian-labs\n    tier: tier-3",
                       "  - slug: newcomer-labs\n    tier: tier-3\n    lead: true\n"
                       "  - slug: veridian-labs\n    tier: tier-3"),
        None,
        "clean",
    ),
    (
        "a non-lead index entry still requires a page",
        lambda r: edit(r, "tiers.yaml",
                       "  - slug: veridian-labs\n    tier: tier-3",
                       "  - slug: newcomer-labs\n    tier: tier-3\n"
                       "  - slug: veridian-labs\n    tier: tier-3"),
        r"ERROR.*'newcomer-labs' is indexed but has no vendors/newcomer-labs\.md",
        "error",
    ),
    (
        "a lead that has grown a page must lose the flag",
        lambda r: edit(r, "tiers.yaml",
                       "  - slug: veridian-labs\n    tier: tier-3",
                       "  - slug: veridian-labs\n    tier: tier-3\n    lead: true"),
        r"ERROR.*marked lead but vendors/veridian-labs\.md exists",
        "error",
    ),
    (
        "filing intel against a lead warns that it should be promoted",
        lambda r: (
            edit(r, "tiers.yaml",
                 "  - slug: veridian-labs\n    tier: tier-3",
                 "  - slug: newcomer-labs\n    tier: tier-3\n    lead: true\n"
                 "  - slug: veridian-labs\n    tier: tier-3"),
            edit(r, os.path.join("signals", "sig-2026-07-30-veridian-labs-01.md"),
                 "vendor: veridian-labs", "vendor: newcomer-labs"),
        ),
        r"warning.*'newcomer-labs' is still an unverified lead",
        "warning",
    ),
    (
        "instance profiles override framework profiles",
        lambda r: (
            instance_profile(r, "data-security", "instance-only-lane"),
            edit(r, os.path.join("vendors", "veridian-labs.md"),
                 "  - ai-data-governance", "  - instance-only-lane"),
            edit(r, os.path.join("signals", "sig-2026-07-30-veridian-labs-01.md"),
                 "lane: ai-data-governance", "lane: instance-only-lane"),
        ),
        None,
        "clean",
    ),
]


def run_case(name, mutate, expected, level):
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, "instance")
        shutil.copytree(FIXTURES, root)
        mutate(root)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = validate.run(root)
        out = buf.getvalue()

    counts = re.search(r"(\d+) error\(s\), (\d+) warning\(s\)", out)
    n_err = int(counts.group(1)) if counts else -1
    n_warn = int(counts.group(2)) if counts else -1

    if level == "clean":
        ok = code == 0 and n_err == 0 and n_warn == 0
        detail = "expected a clean run"
    elif level == "warning":
        ok = code == 0 and n_err == 0 and n_warn > 0 \
            and re.search(expected, out) is not None
        detail = "expected a warning, no errors, and exit 0"
    else:
        ok = code == 1 and re.search(expected, out) is not None
        detail = "expected an error and exit 1"

    print(f"{'pass' if ok else 'FAIL'}  {name}")
    if not ok:
        print(f"      {detail}; exit={code}")
        for line in out.strip().split("\n"):
            print(f"      | {line}")
    return ok


def main() -> int:
    # The PyYAML cross-check in ci_lib only runs when PyYAML is installed, so a
    # local run without it is strictly weaker than CI. Say so rather than
    # letting a green local run imply a green pipeline.
    try:
        import yaml  # noqa: F401
        print("PyYAML present: frontmatter cross-check is ACTIVE.\n")
    except ImportError:
        print("WARNING: PyYAML is not installed, so the frontmatter "
              "cross-check is SKIPPED.")
        print("         This run is weaker than CI. Install it with:")
        print("         python3 -m pip install -r tools/requirements-dev.txt\n")

    print("Baseline: unmodified fixtures must validate clean.")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        base = validate.run(FIXTURES)
    if base != 0:
        print("FAIL  baseline fixtures do not validate")
        print(buf.getvalue())
        return 1
    print("pass  baseline fixtures validate clean\n")

    results = [run_case(*c) for c in CASES]
    passed, total = sum(results), len(results)
    print(f"\n{passed}/{total} contract checks behave as specified.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
