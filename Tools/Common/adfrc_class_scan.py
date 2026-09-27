#!/usr/bin/env python3
"""Report the declared P3D `class` of every converted ADFRC model.

Why this exists: the Arma 3 Object Builder Blender addon hangs indefinitely on
some models. Those turn out to be declared `class = man` (character geometry)
rather than `class = ObjectProp` (rigid prop) -- the addon tries to build a
skeleton and never returns. This script finds them so they can be skipped or
handled separately.

Read-only. Writes Build/adfrc_model_classes.tsv.

    python Tools/Common/adfrc_class_scan.py
"""

import collections
import os
import re
import subprocess
import sys

CLI = r"E:\_tools\UKSFTA-P3D\libs\BIS.CLI\bin\Release\net10.0\BIS.CLI.exe"
MLOD = os.path.join("Art", "ADFRC_MLOD")
REPORT = os.path.join("Build", "adfrc_model_classes.tsv")

CLASS_RE = re.compile(r"Class:\s*([A-Za-z_]+)")

RIGID = "objectprop"


def probe(path):
    """-> declared class string, or '?' if it could not be read."""
    try:
        proc = subprocess.run(
            [CLI, "p3d", "info", path],
            capture_output=True, timeout=60,
        )
    except (subprocess.TimeoutExpired, OSError):
        return "?"
    blob = (proc.stdout or b"") + (proc.stderr or b"")
    text = blob.decode("latin1", "replace")
    match = CLASS_RE.search(text)
    return match.group(1) if match else "?"


def main():
    if not os.path.isdir(MLOD):
        sys.exit(f"not found: {MLOD} (run the conversion first)")

    tally = collections.Counter()
    rows = []
    for addon in sorted(os.listdir(MLOD)):
        folder = os.path.join(MLOD, addon)
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if not name.lower().endswith(".p3d"):
                continue
            cls = probe(os.path.join(folder, name))
            tally[cls.lower()] += 1
            rows.append((cls, addon, name))

    os.makedirs("Build", exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        for cls, addon, name in rows:
            fh.write(f"{cls}\t{addon}\t{name}\n")

    total = len(rows)
    print(f"scanned {total} models -> {REPORT}\n")
    print("=== declared class ===")
    for cls, count in tally.most_common():
        print(f"  {cls:14s} {count}")

    stuck = [r for r in rows if r[0].lower() != RIGID and r[0] != "?"]
    print(f"\n=== {len(stuck)} NOT class=ObjectProp (addon will hang) ===")
    by_addon = collections.Counter(a for _c, a, _n in stuck)
    for addon, count in by_addon.most_common():
        print(f"  {addon:22s} {count}")
    for cls, addon, name in stuck[:25]:
        print(f"    {cls:10s} {addon}/{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
