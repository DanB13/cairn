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
