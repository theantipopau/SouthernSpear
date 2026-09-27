#!/usr/bin/env python3
"""Map every model in the ADFRC extraction to its declared author (L-0021 intake gate).

The written authorisation in Docs/evidence/L0021_adfrc_authorisation_email.txt
is a personal grant from one author. ADF Re-Cut is a multi-author pack, so the
grant only reaches what that author made. This script reads the `author = "..."`
strings out of each addon's config, resolves the shared stringtable variables,
and reports which models the grant actually covers.

Read-only. Touches nothing. Writes a report to Build/.

    python Tools/Common/adfrc_authorship.py [--json]
"""

import argparse
import collections
import json
import os
import re
import sys

EXTRACTED = os.path.join("Content", "Sourced", "ADF_Extracted")
SOURCE_DIR = os.path.join(EXTRACTED, "Source")
MODELS_DIR = os.path.join(EXTRACTED, "Models")
WORKSHOP = os.path.join(EXTRACTED, "Workshop")

# The grantor, per the producer: "tonnie is brucey".
GRANTOR = "brucey"

# Addon author strings that name no individual, i.e. team/catch-all credits.
# These cannot be attributed to the grantor and are reported separately.
NON_INDIVIDUAL = re.compile(
    r"^(adf\s*-?\s*(re-?cut|recut|rc|u)?\s*(team)?|adfrecut|adfu\s+team|"
    r"adf\s*re-?cut\s*team|\s*)$",
    re.I,
)

AUTHOR_RE = re.compile('author\\s*=\\s*"([^"]*)"', re.I)
STRINGTABLE_KEY_RE = re.compile(r'<Key\s+ID="([^"]*AUTHOR[^"]*)"\s*>(.*?)</Key>',
                                re.S | re.I)
STRINGTABLE_VAL_RE = re.compile(r"<(?:Original|English)>(.*?)</(?:Original|English)>",
                                re.S | re.I)


def resolve_stringtables():
    """Map $STR_ADF*_AUTHOR -> its literal value, from the unpacked stringtables."""
    out = {}
    if not os.path.isdir(WORKSHOP):
        return out
    for root, _dirs, files in os.walk(WORKSHOP):
        for name in files:
            if name.lower() != "stringtable.xml":
                continue
            try:
                text = open(os.path.join(root, name), encoding="utf-8",
                            errors="replace").read()
            except OSError:
                continue
            for key, body in STRINGTABLE_KEY_RE.findall(text):
                val = STRINGTABLE_VAL_RE.search(body)
                if val:
                    out.setdefault(key.upper(), val.group(1).strip())
    return out


def addon_authors(variables):
    """addon folder name (lower) -> set of author strings, variables resolved."""
    result = {}
    if not os.path.isdir(SOURCE_DIR):
        return result
    for entry in sorted(os.listdir(SOURCE_DIR)):
        path = os.path.join(SOURCE_DIR, entry)
        if not os.path.isdir(path):
            continue
        names = set()
        for root, _dirs, files in os.walk(path):
            for name in files:
                if not name.lower().endswith((".cpp", ".hpp", ".cfg")):
                    continue
                try:
                    text = open(os.path.join(root, name), encoding="utf-8",
                                errors="replace").read()
                except OSError:
                    continue
                for raw in AUTHOR_RE.findall(text):
                    value = raw.strip()
                    # Resolve "$STR_ADF_AUTHOR" style indirection.
                    if value.startswith("$"):
                        value = variables.get(value[1:].upper(), value)
                    if value:
                        names.add(value)
        result[entry.lower()] = names
    return result


def model_groups():
    """model group folder name (lower) -> count of .p3d files."""
    counts = collections.Counter()
    if not os.path.isdir(MODELS_DIR):
        return counts
    for root, _dirs, files in os.walk(MODELS_DIR):
        n = sum(1 for f in files if f.lower().endswith(".p3d"))
        if n:
            counts[os.path.basename(root).lower()] = n
    return counts


def classify(group, authors):
    """-> one of: grantor / shared / other_author / team_credit / unmapped."""
    if not authors:
        return "unmapped"
    low = {a.lower() for a in authors}
    if GRANTOR in low:
        others = {a for a in low
                  if GRANTOR not in a and not NON_INDIVIDUAL.match(a)}
        return "grantor" if not others else "shared"
    if all(NON_INDIVIDUAL.match(a) for a in low):
        return "team_credit"
    return "other_author"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true",
                    help="emit JSON instead of a text table")
    args = ap.parse_args()

    if not os.path.isdir(EXTRACTED):
        sys.exit(f"not found: {EXTRACTED}")

    variables = resolve_stringtables()
    authors = addon_authors(variables)
    groups = model_groups()

    buckets = collections.defaultdict(list)
    for group, count in groups.items():
        bucket = classify(group, authors.get(group, set()))
        buckets[bucket].append({
            "group": group,
            "models": count,
            "authors": sorted(authors.get(group, set())),
        })

    total = sum(groups.values())
    summary = {k: sum(i["models"] for i in v) for k, v in buckets.items()}
    report = {
        "total_models": total,
        "grantor": GRANTOR,
        "stringtable_variables": variables,
        "covered_by_grant": summary.get("grantor", 0),
        "shared_with_grantor": summary.get("shared", 0),
        "not_covered": (summary.get("other_author", 0)
                        + summary.get("team_credit", 0)),
        "unattributed": summary.get("unmapped", 0),
        "buckets": {k: sorted(v, key=lambda i: -i["models"])
                    for k, v in buckets.items()},
    }

    os.makedirs("Build", exist_ok=True)
    with open("Build/adfrc_authorship.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"ADFRC authorship map  (grantor: {GRANTOR})")
    print(f"total unique .p3d: {total}\n")
    labels = [
        ("grantor", "COVERED by grant (authored solely by grantor)"),
        ("shared", "SHARED  (co-credited; scope per component)"),
        ("other_author", "NOT covered (other named authors)"),
        ("team_credit", "NOT covered (team / catch-all credit)"),
        ("unmapped", "NOT covered (no addon config; vanilla Arma re-dress)"),
    ]
    for key, label in labels:
        items = buckets.get(key, [])
        count = sum(i["models"] for i in items)
        pct = (100.0 * count / total) if total else 0.0
        print(f"--- {label}: {count} models ({pct:.0f}%)")
        for item in sorted(items, key=lambda i: -i["models"])[:20]:
            who = ", ".join(item["authors"]) or "-"
            print(f"      {item['models']:3d}  {item['group']:26s} {who}")
        print()
    print("wrote Build/adfrc_authorship.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
