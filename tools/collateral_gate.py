#!/usr/bin/env python3
"""Provenance gate for outbound collateral.

Generated decks and customer-facing content are the highest-consequence output
in this system: interpretation, leaving the building, in front of buyers. A
rumour on an internal page is untidy; the same rumour in a customer deck is a
credibility problem. So this gate is a HARD FAIL, not a warning.

Rules, in order:
  1. Rumour-tagged claims never pass. This is not configurable.
  2. Confidence must meet collateral.min_confidence.
  3. Claim age must be within collateral.max_claim_age_days.
  4. Claim age must be within the shelf life for its signal type.
  5. Superseded claims never pass.
  6. Both sides of an unresolved contradiction are blocked. Until a human picks
     a side we do not know which claim holds, and asserting either is a guess.
  7. collateral_safe: false is an explicit veto.

Every run emits a provenance appendix so any figure in a deck can be traced to
a source and a date before anybody says it out loud.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ci_lib as L  # noqa: E402
import build_index  # noqa: E402

CONFIDENCE_RANK = {"rumour": 0, "likely": 1, "confirmed": 2}


def gate(index: dict, cfg: dict, vendors: list[str] | None):
    col = cfg.get("collateral") or {}
    floor = CONFIDENCE_RANK[col.get("min_confidence", "likely")]
    max_age = col.get("max_claim_age_days", 180)

    approved, excluded = [], []
    for s in index["signals"]:
        if vendors and s["vendor"] not in vendors:
            continue
        reasons = []
        if s["confidence"] == "rumour":
            reasons.append("rumour claims can never reach outbound collateral")
        if CONFIDENCE_RANK[s["confidence"]] < floor:
            reasons.append(
                f"confidence {s['confidence']!r} is below the configured floor "
                f"{col.get('min_confidence', 'likely')!r}"
            )
        if s["age_days"] > max_age:
            reasons.append(
                f"claim is {s['age_days']} days old, above the collateral cap "
                f"of {max_age}"
            )
        if s["stale"]:
            reasons.append(
                f"past shelf life for type {s['type']!r} "
                f"({s['age_days']} > {s['shelf_life_days']} days)"
            )
        if s.get("superseded"):
            reasons.append("superseded by a later claim")
        if s.get("in_conflict"):
            others = s.get("contradicted_by") or s.get("contradicts") or []
            reasons.append(
                "unresolved contradiction with "
                + ", ".join(others)
                + "; both sides are blocked until a human resolves it"
            )
        if s.get("collateral_safe") is False:
            reasons.append("explicitly vetoed with collateral_safe: false")

        (excluded if reasons else approved).append(
            dict(s, exclusion_reasons=reasons) if reasons else s
        )
    return approved, excluded


def appendix(approved: list[dict], instance: str) -> str:
    lines = [
        "# Provenance appendix",
        "",
        f"Instance: {instance}. Generated {L.today().isoformat()}.",
        "",
        "Every claim used in the accompanying material, with its confidence at "
        "filing time, the date it was observed, and its sources. Confidence "
        "describes the claim when it was filed and never asserts current truth: "
        "read it alongside the date.",
        "",
        "| Signal | Vendor | Date | Age (days) | Confidence | Sources | Claim |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in sorted(approved, key=lambda x: (x["vendor"], x["date"])):
        origins = ", ".join(s["origins"]) or "n/a"
        claim = s["claim"].replace("|", "\\|")
        lines.append(
            f"| `{s['id']}` | {s['vendor']} | {s['date']} | {s['age_days']} | "
            f"{s['confidence']} | {origins} | {claim} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--vendor", action="append", default=None,
                    help="restrict to a vendor slug (repeatable)")
    ap.add_argument("--require", action="append", default=[],
                    help="signal id that MUST pass; exit 1 if it is excluded")
    ap.add_argument("--appendix", default=None,
                    help="write the provenance appendix here (default stdout summary only)")
    ap.add_argument("--json", dest="as_json", action="store_true",
                    help="emit the full gate result as JSON")
    args = ap.parse_args()

    cfg, _ = L.parse_frontmatter(
        "---\n" + L.read_text(os.path.join(args.root, "config.yaml")) + "\n---\n"
    )
    index = build_index.build(args.root)
    approved, excluded = gate(index, cfg, args.vendor)

    if args.as_json:
        print(json.dumps({"approved": approved, "excluded": excluded}, indent=2))
    else:
        print(f"collateral gate: {len(approved)} approved, {len(excluded)} excluded")
        for s in excluded:
            print(f"\n  BLOCKED {s['id']} ({s['vendor']}, {s['confidence']}, "
                  f"{s['age_days']}d)")
            for r in s["exclusion_reasons"]:
                print(f"          - {r}")
        if approved:
            print("\n  approved:")
            for s in approved:
                print(f"    {s['id']}  {s['vendor']:<18} {s['confidence']:<9} "
                      f"{s['age_days']:>4}d")

    text = appendix(approved, index.get("instance") or "unnamed")
    if args.appendix:
        with open(args.appendix, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"\nprovenance appendix written to {args.appendix}")
    elif (cfg.get("collateral") or {}).get("require_provenance_appendix", True):
        print("\n" + text)

    failed = [r for r in args.require
              if r in {s["id"] for s in excluded}]
    if failed:
        print("\nFAILED: required claims did not pass the gate:", file=sys.stderr)
        for f in failed:
            print(f"  {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
