#!/usr/bin/env python3
"""Refuse to let a seeded instance live in a public repository.

This is the cheapest and strongest control in the framework. A public template
that people seed with real competitive intel will, sooner or later, produce
somebody pushing pricing data to a public repo. Run this from a pre-push hook
and from CI, so deleting the hook does not remove the control.

Detection: an INSTANCE is a checkout with config.yaml at its root. The public
framework has no root config.yaml (its synthetic data lives under fixtures/),
so the framework repo is correctly ignored.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys


def repo_root(start: str) -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start,
                             capture_output=True, text=True, timeout=15)
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return os.path.abspath(start)


def is_instance(root: str) -> bool:
    return os.path.exists(os.path.join(root, "config.yaml"))


def data_files(root: str) -> list[str]:
    hits: list[str] = []
    for sub in ("vendors", "signals", "assessments", "archive", "product"):
        hits += glob.glob(os.path.join(root, sub, "**", "*.md"), recursive=True)
    for name in ("config.yaml", "tiers.yaml", "index.json"):
        p = os.path.join(root, name)
        if os.path.exists(p):
            hits.append(p)
    return [os.path.relpath(h, root) for h in sorted(hits)]


def visibility(root: str) -> tuple[str, str]:
    """Return (visibility, how_we_know). 'unknown' when it cannot be resolved."""
    try:
        out = subprocess.run(
            ["gh", "repo", "view", "--json", "visibility,nameWithOwner"],
            cwd=root, capture_output=True, text=True, timeout=30,
        )
        if out.returncode == 0:
            data = json.loads(out.stdout)
            return data["visibility"].lower(), f"gh: {data.get('nameWithOwner')}"
    except (OSError, subprocess.SubprocessError, ValueError, KeyError):
        pass
    return "unknown", "could not resolve (gh unavailable or not authenticated)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--allow-unknown", action="store_true",
                    help="pass when visibility cannot be resolved (CI default is to fail)")
    args = ap.parse_args()

    root = repo_root(args.path)

    if not is_instance(root):
        print(f"ok: {root} is not a seeded instance (no root config.yaml); "
              f"nothing to protect")
        return 0

    files = data_files(root)
    vis, how = visibility(root)
    print(f"instance root : {root}")
    print(f"data files    : {len(files)}")
    print(f"visibility    : {vis} ({how})")

    if vis == "public":
        print("\nREFUSED: this is a seeded competitive-intelligence instance in a "
              "PUBLIC repository.")
        print("Seeded instances must be private. Nothing has been changed.")
        print("\nFiles that would be exposed:")
        for f in files[:20]:
            print(f"  {f}")
        if len(files) > 20:
            print(f"  ... and {len(files) - 20} more")
        print("\nTo fix: move this data to a private repository, or run")
        print("  gh repo edit --visibility private --accept-visibility-change-consequences")
        return 1

    if vis == "unknown" and not args.allow_unknown:
        print("\nREFUSED: cannot confirm this repository is private.")
        print("Authenticate gh, or pass --allow-unknown if you have verified it "
              "another way.")
        return 1

    print("\nok: instance is not public")
    return 0


if __name__ == "__main__":
    sys.exit(main())
