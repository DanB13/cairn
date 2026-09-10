#!/usr/bin/env python3
"""Retention: move aged signals into the archive tree.

Nothing left the original design, so the signals log grew without bound. Under
the git model that cost is paid on every query rather than only on write, so
retention is enforced rather than suggested. Archived signals stay validated and
readable, and drop out of the live query surface.
"""

from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ci_lib as L  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--apply", action="store_true",
                    help="perform the moves (default is a dry run)")
    args = ap.parse_args()

    cfg, _ = L.parse_frontmatter(
        "---\n" + L.read_text(os.path.join(args.root, "config.yaml")) + "\n---\n"
    )
    cutoff = (cfg.get("retention") or {}).get("archive_after_days", 730)
    sdir = os.path.join(args.root, cfg["paths"]["signals"])
    adir = os.path.join(args.root, cfg["paths"].get("archive", "archive"))

    moves = []
    for path in sorted(glob.glob(os.path.join(sdir, "**", "*.md"), recursive=True)):
        fm, _ = L.load_doc(path)
        age = L.age_days(fm["date"])
        if age > cutoff:
            year = str(fm["date"])[:4]
            moves.append((path, os.path.join(adir, year, os.path.basename(path)), age))

    if not moves:
        print(f"nothing older than {cutoff} days; archive is current")
        return 0

    for src, dst, age in moves:
        rel_src = os.path.relpath(src, args.root)
        rel_dst = os.path.relpath(dst, args.root)
        print(f"{'move' if args.apply else 'would move'}  {rel_src} -> {rel_dst} "
              f"({age}d)")
        if args.apply:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            try:
                subprocess.run(["git", "mv", src, dst], cwd=args.root,
                               check=True, capture_output=True)
            except (OSError, subprocess.SubprocessError):
                shutil.move(src, dst)

    if not args.apply:
        print(f"\n{len(moves)} file(s) would move. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
