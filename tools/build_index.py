#!/usr/bin/env python3
"""Generate index.json from frontmatter.

Exists so a digest across the whole vendor set does not require reading every
file. Consumers (the skills today, an MCP server later) read this first and
open individual files only when they need the prose.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ci_lib as L  # noqa: E402
from validate import DEFAULT_SHELF_LIFE  # noqa: E402


def shelf_life(cfg: dict, signal_type: str) -> int:
    table = (cfg.get("shelf_life_days") or {})
    return table.get(signal_type,
                     cfg.get("default_shelf_life_days",
                             DEFAULT_SHELF_LIFE.get(signal_type, 365)))


def build(root: str) -> dict:
    cfg, _ = L.parse_frontmatter("---\n" + L.read_text(os.path.join(root, "config.yaml")) + "\n---\n")
    paths = cfg["paths"]

    vendors = {}
    for path in sorted(glob.glob(os.path.join(root, paths["vendors"], "*.md"))):
        fm, _ = L.load_doc(path)
        vendors[fm["slug"]] = fm

    assessments = {}
    for path in sorted(glob.glob(os.path.join(root, paths["assessments"], "*.md"))):
        fm, _ = L.load_doc(path)
        assessments[fm["vendor"]] = fm

    signals = []
    search = [os.path.join(root, paths["signals"])]
    if os.path.isdir(os.path.join(root, paths.get("archive", "archive"))):
        search.append(os.path.join(root, paths["archive"]))
    for sdir in search:
        archived = os.path.basename(sdir) == os.path.basename(paths.get("archive", "archive"))
        for path in sorted(glob.glob(os.path.join(sdir, "**", "*.md"), recursive=True)):
            fm, _ = L.load_doc(path)
            age = L.age_days(fm["date"])
            life = shelf_life(cfg, fm["type"])
            signals.append({
                "id": fm["id"],
                "vendor": fm["vendor"],
                "date": fm["date"],
                "type": fm["type"],
                "confidence": fm["confidence"],
                "claim": fm["claim"],
                "lane": fm.get("lane"),
                "origins": sorted({s.get("origin") for s in fm.get("sources") or []
                                   if isinstance(s, dict) and s.get("origin")}),
                "source_kinds": sorted({s.get("kind") for s in fm.get("sources") or []
                                        if isinstance(s, dict) and s.get("kind")}),
                "contributor": fm.get("contributor"),
                "supersedes": fm.get("supersedes") or [],
                "contradicts": fm.get("contradicts") or [],
                "age_days": age,
                "shelf_life_days": life,
                "stale": age > life,
                "archived": archived,
                "path": os.path.relpath(path, root),
            })

    superseded = {ref for s in signals for ref in s["supersedes"]}
    # Reverse the contradicts links. An unresolved contradiction taints BOTH
    # sides: until a human resolves it we do not know which claim holds, so
    # neither may be asserted in outbound material.
    contradicted = {ref for s in signals for ref in s["contradicts"]}
    for s in signals:
        s["superseded"] = s["id"] in superseded
        s["in_conflict"] = bool(s["contradicts"]) or s["id"] in contradicted
        s["contradicted_by"] = sorted(
            o["id"] for o in signals if s["id"] in o["contradicts"]
        )

    vendor_rows = []
    for slug, fm in sorted(vendors.items()):
        mine = [s for s in signals if s["vendor"] == slug]
        live = [s for s in mine if not s["superseded"] and not s["archived"]]
        contradictions = [
            {"claim": s["id"], "conflicts_with": s["contradicts"]}
            for s in mine if s["contradicts"]
        ]
        a = assessments.get(slug)
        overdue = L.age_days(fm["reverify_by"])
        vendor_rows.append({
            "slug": slug,
            "name": fm["name"],
            "aliases": fm.get("aliases") or [],
            "tier": fm["tier"],
            "lanes": fm.get("lanes") or [],
            "flags": fm.get("flags") or {},
            "cadence": fm["cadence"],
            "status": fm["status"],
            "last_reviewed": fm["last_reviewed"],
            "data_as_of": fm["data_as_of"],
            "reverify_by": fm["reverify_by"],
            "overdue_days": overdue if overdue > 0 else 0,
            "signal_count": len(mine),
            "live_signal_count": len(live),
            "stale_signal_count": sum(1 for s in live if s["stale"]),
            "latest_signal": max((s["date"] for s in mine), default=None),
            "open_contradictions": contradictions,
            "has_assessment": a is not None,
            "assessment_updated": (a or {}).get("updated"),
            "threat_level": (a or {}).get("threat_level"),
            "path": os.path.join(paths["vendors"], f"{slug}.md"),
        })

    product = []
    for path in sorted(glob.glob(os.path.join(root, paths.get("product", "product"), "*.md"))):
        fm, _ = L.load_doc(path)
        product.append({
            "name": fm["name"], "owner": fm["owner"],
            "last_reviewed": fm["last_reviewed"], "reverify_by": fm["reverify_by"],
            "overdue_days": max(0, L.age_days(fm["reverify_by"])),
            "path": os.path.relpath(path, root),
        })

    return {
        "generated": L.today().isoformat(),
        "schema_version": 1,
        "instance": cfg.get("instance_name"),
        "profile": cfg.get("profile"),
        # Carried through so consumers get organisation context without parsing
        # config.yaml. Collateral generation needs size and stage to avoid
        # claims the company cannot support, and gap sections are written
        # against icp.must_have_criteria.
        "organisation": cfg.get("organisation") or {},
        "counts": {
            "vendors": len(vendor_rows),
            "signals": len(signals),
            "assessments": len(assessments),
        },
        "attention": {
            "overdue_vendors": [v["slug"] for v in vendor_rows if v["overdue_days"] > 0],
            "vendors_without_assessment": [
                v["slug"] for v in vendor_rows if not v["has_assessment"]
            ],
            "open_contradictions": [
                c for v in vendor_rows for c in v["open_contradictions"]
            ],
            "stale_product_refs": [p["path"] for p in product if p["overdue_days"] > 0],
        },
        "product": product,
        "vendors": vendor_rows,
        "signals": sorted(signals, key=lambda s: s["date"], reverse=True),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("-o", "--out", default=None,
                    help="output path (default <root>/index.json; '-' for stdout)")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the committed index.json is out of date")
    args = ap.parse_args()

    index = build(args.root)
    text = json.dumps(index, indent=2, sort_keys=False) + "\n"

    if args.check:
        target = os.path.join(args.root, "index.json")
        current = L.read_text(target) if os.path.exists(target) else ""
        if current != text:
            print("index.json is stale; run tools/build_index.py", file=sys.stderr)
            return 1
        print("index.json is current")
        return 0

    if args.out == "-":
        sys.stdout.write(text)
    else:
        path = args.out or os.path.join(args.root, "index.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        c = index["counts"]
        print(f"wrote {path}: {c['vendors']} vendors, {c['signals']} signals")
    return 0


if __name__ == "__main__":
    sys.exit(main())
