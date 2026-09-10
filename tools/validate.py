#!/usr/bin/env python3
"""Enforce the cairn content contract.

Exit codes: 0 clean (warnings permitted), 1 contract violation, 2 bad invocation.

Design notes worth knowing before editing:

  * Style rules are mechanical, so they hard-fail.
  * Interpretation detection is a semantic judgement a phrase list cannot make
    reliably, so it only ever warns. It exists to prompt a reviewer, never to
    gate a merge, and dressing it up as an invariant would be dishonest.
  * Confidence is checked against source KIND and source INDEPENDENCE, not
    source count, because two rewrites of one story are not two sources.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ci_lib as L

SUPPORTED_SCHEMA_VERSION = 1

PRIMARY_KINDS = {"vendor-primary", "analyst-tier1", "first-hand"}

# Phrases that usually signal interpretation leaking into a descriptive page.
INTERPRETATION_PATTERNS = [
    r"\bwhat this means for us\b", r"\bcreates? a wedge\b", r"\bwe should\b",
    r"\bour opportunity\b", r"\bthis is good for us\b", r"\bwe can win\b",
    r"\bplay(?:book)? against\b", r"\bthey(?:'| a)?re vulnerable\b",
    r"\bwill struggle\b", r"\bposes a threat\b", r"\bwe out(?:perform|compete)\b",
    r"\bpitch against\b", r"\bkill sheet\b", r"\bland and expand\b",
]

DEFAULT_SHELF_LIFE = {
    "pricing": 180, "packaging": 180, "m-and-a": 90, "funding": 180,
    "leadership": 180, "headcount": 365, "product-launch": 270,
    "product-change": 270, "positioning": 270, "messaging": 270,
    "partnership": 365, "certification": 545, "customer-win": 365,
    "customer-loss": 365, "analyst": 365, "incident": 365,
    "legal": 365, "other": 365,
}

SECTION_POLICY_RE = re.compile(
    r"<!--\s*policy:\s*(descriptive|interpretive)\s*-->", re.IGNORECASE
)


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")

    def extend(self, where: str, errs: list[str]) -> None:
        for e in errs:
            self.errors.append(f"{where}: {e}")


# ---------------------------------------------------------------- config

def load_config(root: str, rep: Report):
    path = os.path.join(root, "config.yaml")
    if not os.path.exists(path):
        rep.error("config.yaml", "missing; every instance needs one")
        return None
    try:
        cfg, _ = L.parse_frontmatter("---\n" + L.read_text(path) + "\n---\n")
    except L.FrontmatterError as exc:
        rep.error("config.yaml", str(exc))
        return None
    rep.extend("config.yaml", L.validate(cfg, L.load_schema("config.schema.json")))
    return cfg


def profile_search_path(root: str, name: str) -> list[str]:
    """Instance profiles win over framework profiles.

    An instance can define its own market vocabulary without forking the
    framework, which matters because no shipped profile will fit every market.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    return [
        os.path.join(root, "profiles", f"{name}.yaml"),
        os.path.join(here, "..", "profiles", f"{name}.yaml"),
    ]


def load_profile(root: str, name: str, rep: Report):
    for path in profile_search_path(root, name):
        if os.path.exists(path):
            prof, _ = L.parse_frontmatter(
                "---\n" + L.read_text(path) + "\n---\n"
            )
            rep.extend(f"profiles/{name}.yaml",
                       L.validate(prof, L.load_schema("profile.schema.json")))
            return prof
    rep.error("profile", f"unknown profile {name!r}; looked in this instance's "
                         f"profiles/ then the framework's")
    return None


def check_organisation(cfg: dict, prof: dict, vendors: dict, rep: Report) -> None:
    """Organisation context is required, and is checked rather than decorative.

    Size and stage calibrate which vendors are plausibly head to head, ICP
    criteria are the source for gap sections, and both go stale.
    """
    org = (cfg or {}).get("organisation") or {}
    if not org:
        return  # schema validation has already reported the absence

    where = "config.yaml organisation"

    if org.get("reverify_by"):
        try:
            if L.as_date(org["reverify_by"]) < L.today():
                rep.warn(where, f"organisation context is "
                                f"{L.age_days(org['reverify_by'])} days past "
                                f"reverify_by; size and stage change who counts "
                                f"as a competitor")
        except ValueError as exc:
            rep.error(where, f"unparseable reverify_by: {exc}")
    if org.get("reviewed") and org.get("reverify_by"):
        try:
            if L.as_date(org["reverify_by"]) <= L.as_date(org["reviewed"]):
                rep.error(where, "reverify_by must be after reviewed")
        except ValueError:
            pass

    active = {slug: v for slug, v in vendors.items()
              if v.get("status") in ("active", "watch")}

    if org.get("competes_with_platforms"):
        if not any((v.get("flags") or {}).get("platform_native")
                   for v in active.values()):
            rep.warn(where, "competes_with_platforms is true but no vendor "
                            "carries the platform_native flag; bundled "
                            "capability is usually the alternative that never "
                            "reaches a shortlist")

    tier_ids = {t["id"] for t in (prof or {}).get("tiers", [])}
    if "status-quo" in tier_ids and not any(
        (v.get("flags") or {}).get("status_quo") for v in active.values()
    ):
        rep.warn(where, "the profile defines a status-quo tier but nothing is "
                        "tracked in it; doing nothing wins deals and has no "
                        "marketing site to remind you")

    if cfg.get("profile") == "generic" and len(active) > 3:
        rep.warn(where, f"{len(active)} vendors tracked against the generic "
                        f"profile; close the lane vocabulary around your market "
                        f"by copying a profile into this instance's profiles/")


# ---------------------------------------------------------------- style

def check_style(where: str, text: str, cfg: dict, rep: Report) -> None:
    style = (cfg or {}).get("style") or {}
    if style.get("forbid_em_dash", True):
        for n, line in enumerate(text.split("\n"), 1):
            # Written as escapes so the literal characters never appear in
            # this repository, which lets CI grep for them without having to
            # carve out an exception for the code that enforces the rule.
            if "\u2014" in line or "\u2013" in line:
                rep.error(f"{where}:{n}", "en/em dash is forbidden by house style")
    for pat in style.get("forbid_patterns") or []:
        for n, line in enumerate(text.split("\n"), 1):
            if re.search(pat, line, re.IGNORECASE):
                rep.error(f"{where}:{n}", f"matches forbidden pattern {pat!r}")


def check_interpretation(where: str, body: str, rep: Report) -> None:
    """Warn only. Scoped to sections marked descriptive."""
    policy = "descriptive"
    for n, line in enumerate(body.split("\n"), 1):
        marker = SECTION_POLICY_RE.search(line)
        if marker:
            policy = marker.group(1).lower()
            continue
        if policy != "descriptive":
            continue
        if line.lstrip().startswith(">"):
            continue  # quoted vendor copy is reported speech, not our reading
        for pat in INTERPRETATION_PATTERNS:
            m = re.search(pat, line, re.IGNORECASE)
            if m:
                rep.warn(
                    f"{where}:{n}",
                    f"possible interpretation ({m.group(0)!r}) in a descriptive "
                    f"section; move it to the assessment file if it is a reading "
                    f"rather than an observation",
                )


# ---------------------------------------------------------------- vendors

def check_vendors(root: str, cfg: dict, prof: dict, rep: Report):
    vdir = os.path.join(root, (cfg["paths"]["vendors"] if cfg else "vendors"))
    tier_ids = {t["id"] for t in (prof or {}).get("tiers", [])}
    lane_ids = {l["id"] for l in (prof or {}).get("lanes", [])}
    vendors: dict[str, dict] = {}

    for path in sorted(glob.glob(os.path.join(vdir, "*.md"))):
        rel = os.path.relpath(path, root)
        try:
            fm, body = L.load_doc(path)
        except L.FrontmatterError as exc:
            rep.error(rel, str(exc))
            continue

        rep.extend(rel, L.validate(fm, L.load_schema("vendor.schema.json")))
        if fm.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
            rep.error(rel, f"schema_version must be {SUPPORTED_SCHEMA_VERSION}")

        slug = fm.get("slug")
        stem = os.path.splitext(os.path.basename(path))[0]
        if slug and slug != stem:
            rep.error(rel, f"filename stem {stem!r} must equal slug {slug!r}")
        if slug in vendors:
            rep.error(rel, f"duplicate slug {slug!r}")
        if slug:
            vendors[slug] = fm

        if tier_ids and fm.get("tier") not in tier_ids:
            rep.error(rel, f"tier {fm.get('tier')!r} not in profile "
                           f"({sorted(tier_ids)})")
        for lane in fm.get("lanes") or []:
            if lane_ids and lane not in lane_ids:
                rep.error(rel, f"lane {lane!r} not in profile vocabulary")

        flags = fm.get("flags") or {}
        if len(fm.get("lanes") or []) > 1 and not flags.get("convergence"):
            rep.warn(rel, "spans multiple lanes but convergence flag is not set")

        # Dates.
        try:
            if fm.get("data_as_of") and fm.get("last_reviewed"):
                if L.as_date(fm["data_as_of"]) > L.as_date(fm["last_reviewed"]):
                    rep.error(rel, "data_as_of is later than last_reviewed")
            if fm.get("reverify_by") and fm.get("last_reviewed"):
                if L.as_date(fm["reverify_by"]) <= L.as_date(fm["last_reviewed"]):
                    rep.error(rel, "reverify_by must be after last_reviewed")
            for field in ("last_reviewed", "data_as_of"):
                if fm.get(field) and L.as_date(fm[field]) > L.today():
                    rep.error(rel, f"{field} is in the future")
            if fm.get("reverify_by") and L.as_date(fm["reverify_by"]) < L.today():
                rep.warn(rel, f"overdue for re-verification "
                              f"({L.age_days(fm['reverify_by'])} days past reverify_by)")
        except ValueError as exc:
            rep.error(rel, f"unparseable date: {exc}")

        if fm.get("status") == "merged" and not fm.get("merged_into"):
            rep.error(rel, "status is merged but merged_into is empty")

        check_style(rel, body, cfg, rep)
        check_interpretation(rel, body, rep)

        low = body.lower()
        if "confidence: rumour" in low or "| rumour |" in low:
            rep.error(rel, "rumour-tagged claim in a vendor page body; "
                           "rumours belong in signals or open questions only")
    return vendors


# ---------------------------------------------------------------- tier index

def check_tier_index(root: str, vendors: dict, prof: dict, rep: Report) -> None:
    path = os.path.join(root, "tiers.yaml")
    if not os.path.exists(path):
        rep.error("tiers.yaml", "missing; it is the source of truth for coverage")
        return
    idx, _ = L.parse_frontmatter("---\n" + L.read_text(path) + "\n---\n")
    rep.extend("tiers.yaml", L.validate(idx, L.load_schema("tiers.schema.json")))

    listed = {}
    for entry in idx.get("vendors") or []:
        slug = entry.get("slug")
        if slug in listed:
            rep.error("tiers.yaml", f"duplicate entry for {slug!r}")
        listed[slug] = entry.get("tier")

    for slug in listed:
        if slug not in vendors:
            rep.error("tiers.yaml",
                      f"{slug!r} is indexed but has no vendors/{slug}.md")
    for slug in vendors:
        if slug not in listed:
            rep.error("tiers.yaml",
                      f"vendors/{slug}.md exists but is not in the tier index")
    for slug, tier in listed.items():
        if slug in vendors and vendors[slug].get("tier") != tier:
            rep.error(
                "tiers.yaml",
                f"tier disagreement for {slug!r}: index says {tier!r}, page says "
                f"{vendors[slug].get('tier')!r}. The index wins; correct the page.",
            )


# ---------------------------------------------------------------- signals

def check_signals(root: str, cfg: dict, vendors: dict, prof: dict, rep: Report):
    sdirs = [os.path.join(root, cfg["paths"]["signals"] if cfg else "signals")]
    archive = os.path.join(root, (cfg or {}).get("paths", {}).get("archive", "archive"))
    if os.path.isdir(archive):
        sdirs.append(archive)

    signals: dict[str, dict] = {}
    tier1_kinds = set((cfg or {}).get("sources", {}).get("analyst_tier1") or [])

    for sdir in sdirs:
        for path in sorted(glob.glob(os.path.join(sdir, "**", "*.md"), recursive=True)):
            rel = os.path.relpath(path, root)
            try:
                fm, body = L.load_doc(path)
            except L.FrontmatterError as exc:
                rep.error(rel, str(exc))
                continue

            rep.extend(rel, L.validate(fm, L.load_schema("signal.schema.json")))
            if fm.get("confidence") is None:
                rep.error(rel, "untaggable claim: confidence is required. "
                               "Report this back to the contributor rather than "
                               "dropping it silently.")
            sid = fm.get("id")
            stem = os.path.splitext(os.path.basename(path))[0]
            if sid and sid != stem:
                rep.error(rel, f"filename stem {stem!r} must equal id {sid!r}")
            if sid in signals:
                rep.error(rel, f"duplicate signal id {sid!r}")
            if sid:
                signals[sid] = fm

            vendor = fm.get("vendor")
            if vendor and vendor not in vendors:
                rep.error(rel, f"references untracked vendor {vendor!r}; adding a "
                               f"vendor is a Curator decision, not a signal")
            if sid and fm.get("date") and f"-{fm['date']}-" not in f"-{sid}-":
                rep.error(rel, f"id date does not match date field {fm['date']!r}")

            srcs = fm.get("sources") or []
            conf = fm.get("confidence")
            origins = {s.get("origin") for s in srcs if isinstance(s, dict)}
            kinds = {s.get("kind") for s in srcs if isinstance(s, dict)}

            if conf == "confirmed" and not (kinds & PRIMARY_KINDS):
                rep.error(rel, "confirmed requires at least one vendor-primary, "
                               "analyst-tier1 or first-hand source")
            if conf == "likely" and len(origins) < 2:
                rep.error(rel, f"likely requires two or more INDEPENDENT sources; "
                               f"found {len(origins)} distinct origin(s) {sorted(o for o in origins if o)}. "
                               f"Syndicated rewrites share an origin and do not count.")
            if conf == "rumour" and len(origins) > 1:
                rep.warn(rel, "multiple independent origins; this may qualify as likely")
            for s in srcs:
                if not isinstance(s, dict):
                    continue
                if s.get("kind") == "analyst-tier1" and tier1_kinds and \
                        s.get("origin") not in tier1_kinds:
                    rep.error(rel, f"origin {s.get('origin')!r} is not in the "
                                   f"configured analyst_tier1 list")
                if s.get("accessed") and L.as_date(s["accessed"]) > L.today():
                    rep.error(rel, "source accessed date is in the future")

            if fm.get("filed") and fm.get("date"):
                if L.as_date(fm["filed"]) < L.as_date(fm["date"]):
                    rep.error(rel, "filed is earlier than the observation date")

            lane_ids = {l["id"] for l in (prof or {}).get("lanes", [])}
            if fm.get("lane") and lane_ids and fm["lane"] not in lane_ids:
                rep.error(rel, f"lane {fm['lane']!r} not in profile vocabulary")

            check_style(rel, fm.get("claim") or "", cfg, rep)
            check_style(rel, body, cfg, rep)

            words = len((fm.get("claim") or "").split())
            cap = ((cfg or {}).get("style") or {}).get("max_claim_words", 80)
            if words > cap:
                rep.warn(rel, f"claim is {words} words (cap {cap}); "
                              f"consider splitting into separate signals")

    # Cross references resolve.
    for sid, fm in signals.items():
        for field in ("supersedes", "contradicts"):
            for ref in fm.get(field) or []:
                if ref not in signals:
                    rep.error(f"signals/{sid}", f"{field} points at unknown id {ref!r}")
                elif signals[ref].get("vendor") != fm.get("vendor"):
                    rep.error(f"signals/{sid}",
                              f"{field} {ref!r} belongs to a different vendor")
    return signals


# ---------------------------------------------------------------- assessments

def check_assessments(root: str, cfg: dict, vendors: dict, signals: dict, rep: Report):
    adir = os.path.join(root, (cfg or {}).get("paths", {}).get("assessments", "assessments"))
    seen = set()
    for path in sorted(glob.glob(os.path.join(adir, "*.md"))):
        rel = os.path.relpath(path, root)
        try:
            fm, body = L.load_doc(path)
        except L.FrontmatterError as exc:
            rep.error(rel, str(exc))
            continue
        rep.extend(rel, L.validate(fm, L.load_schema("assessment.schema.json")))
        vendor = fm.get("vendor")
        seen.add(vendor)
        if vendor and vendor not in vendors:
            rep.error(rel, f"assessment for untracked vendor {vendor!r}")
        stem = os.path.splitext(os.path.basename(path))[0]
        if vendor and stem != vendor:
            rep.error(rel, f"filename stem {stem!r} must equal vendor {vendor!r}")
        if fm.get("review_by") and L.as_date(fm["review_by"]) < L.today():
            rep.warn(rel, "assessment is past its review_by date")
        for n, dec in enumerate(fm.get("decisions") or []):
            for ref in dec.get("signals") or []:
                if ref not in signals:
                    rep.error(rel, f"decisions[{n}] cites unknown signal {ref!r}")
        check_style(rel, body, cfg, rep)
        # Interpretation is the whole point of this file, so no scan here.
    for slug, fm in vendors.items():
        if fm.get("tier") in ("tier-1",) and slug not in seen:
            rep.warn(f"assessments/{slug}.md",
                     "tier-1 vendor has no assessment; battlecards and collateral "
                     "have nowhere legitimate to live")


# Handles shipped in the instance template. Left unreplaced, GitHub silently
# ignores them: the repository ends up with NO code owners, "require review
# from Code Owners" passes vacuously, and governance is absent while appearing
# configured. Nothing in GitHub warns about this, so the framework must.
CODEOWNER_PLACEHOLDERS = [
    "@CURATOR_DEPUTY", "@CURATOR", "@REVIEWERS", "@PRODUCT_OWNER", "@OWNER",
]

GOVERNANCE_PLACEHOLDERS = {"unassigned", "replace_me", "replace me", "tbd"}


def check_governance_wiring(root: str, cfg: dict, rep: Report) -> None:
    """Confirm governance is wired to real people, not to template placeholders."""
    path = os.path.join(root, ".github", "CODEOWNERS")
    rel = ".github/CODEOWNERS"

    if not os.path.exists(path):
        rep.warn(rel, "no CODEOWNERS file; branch protection has nothing to "
                      "require review from, so the Curator and Reviewer split "
                      "is documentation rather than a control")
    else:
        text = L.read_text(path)
        for n, line in enumerate(text.split("\n"), 1):
            if line.lstrip().startswith("#"):
                continue
            for placeholder in CODEOWNER_PLACEHOLDERS:
                if placeholder in line:
                    rep.error(
                        f"{rel}:{n}",
                        f"unreplaced template placeholder {placeholder!r}. "
                        f"GitHub ignores owners it cannot resolve, so this file "
                        f"currently assigns no owner at all. Replace it with a "
                        f"real handle or team.",
                    )
                    break

    gov = (cfg or {}).get("governance") or {}
    for field in ("curators", "curator_deputy", "reviewers"):
        for who in gov.get(field) or []:
            if str(who).strip().lower() in GOVERNANCE_PLACEHOLDERS:
                rep.error(f"config.yaml governance.{field}",
                          f"{who!r} is a placeholder; name a real person. "
                          f"An unassigned role is an unstaffed one.")

    curators = [c for c in (gov.get("curators") or [])]
    reviewers = [r for r in (gov.get("reviewers") or [])]
    if curators and reviewers and set(curators) == set(reviewers) and len(reviewers) == 1:
        rep.warn("config.yaml governance",
                 "the same single person is Curator and only Reviewer. That is "
                 "the bundled role the split exists to avoid: strategic work "
                 "gets crowded out by queue review, or review rots. Name a "
                 "second Reviewer.")


def check_product(root: str, cfg: dict, rep: Report) -> None:
    pdir = os.path.join(root, (cfg or {}).get("paths", {}).get("product", "product"))
    files = sorted(glob.glob(os.path.join(pdir, "*.md")))
    if not files:
        rep.error("product/", "no own-product reference found; --compare would "
                              "otherwise run against nothing")
        return
    for path in files:
        rel = os.path.relpath(path, root)
        fm, body = L.load_doc(path)
        rep.extend(rel, L.validate(fm, L.load_schema("product.schema.json")))
        if fm.get("reverify_by") and L.as_date(fm["reverify_by"]) < L.today():
            rep.error(rel, "own-product reference is past reverify_by; a stale "
                           "self-description produces confidently wrong comparisons")
        check_style(rel, body, cfg, rep)


# ---------------------------------------------------------------- main

def run(root: str, strict_warnings: bool = False) -> int:
    rep = Report()
    cfg = load_config(root, rep)
    prof = load_profile(root, cfg["profile"], rep) if cfg and cfg.get("profile") else None

    vendors = check_vendors(root, cfg, prof, rep)
    check_organisation(cfg, prof, vendors, rep)
    check_tier_index(root, vendors, prof, rep)
    signals = check_signals(root, cfg, vendors, prof, rep)
    check_assessments(root, cfg, vendors, signals, rep)
    check_product(root, cfg, rep)
    check_governance_wiring(root, cfg, rep)

    for w in rep.warnings:
        print(f"warning  {w}")
    for e in rep.errors:
        print(f"ERROR    {e}")

    print(
        f"\n{len(vendors)} vendor(s), {len(signals)} signal(s) checked. "
        f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)."
    )
    if rep.errors:
        return 1
    if strict_warnings and rep.warnings:
        print("failing because --strict-warnings was set")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".",
                    help="instance root (the directory holding config.yaml)")
    ap.add_argument("--strict-warnings", action="store_true",
                    help="treat warnings as failures")
    args = ap.parse_args()
    if not os.path.isdir(args.root):
        print(f"not a directory: {args.root}", file=sys.stderr)
        return 2
    return run(args.root, args.strict_warnings)


if __name__ == "__main__":
    sys.exit(main())
