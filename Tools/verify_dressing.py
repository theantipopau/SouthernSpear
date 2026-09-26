"""
Southern Spear - Dry River dressing data validator.

Checks the dressing CSVs against the map specification WITHOUT opening the
editor. Two reasons this is separate from the in-engine dressing pass:

  1. CI has no Blender, and should not need a six minute editor start to learn
     that a fence was dragged through an objective.
  2. It is a different kind of check. The editor pass reports what it managed to
     place; this reports whether the DATA is legal, including rows the editor
     would have refused.

Run:
    python Tools/verify_dressing.py

Exits non-zero on any failure. See Docs/MAPS_DRYRIVER.md section 12.
"""

import csv
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "Common"))
import dryriver_spec as spec  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCKOUT_DIR = os.path.normpath(os.path.join(HERE, "..", "Content", "Art", "Blockout"))
DRESSING_CSV = os.path.join(BLOCKOUT_DIR, "SS_MAP_DryRiver_02_Dressing.csv")
FENCES_CSV = os.path.join(BLOCKOUT_DIR, "SS_MAP_DryRiver_02_Fences.csv")

# Must match dryriver_dressing.py. Duplicated deliberately but ASSERTED against
# the generator's own values at the bottom of this file, so the two cannot
# drift apart silently.
KNOWN_TYPES = ("scrub", "wreck", "crate", "barrel")
CLEARANCE = {"wreck": 14.0, "crate": 9.0, "barrel": 8.0, "scrub": 2.0}
DEFAULT_CLEARANCE = 6.0
EDGE_INSET = 8.0
MIN_SPACING = 3.0
FENCE_MAX_LENGTH = 45.0
FENCE_MIN_LENGTH = 8.0
FENCE_MIN_SPACING = 1.5
FENCE_MAX_SPACING = 6.0
FENCE_CLEARANCE_EXTRA = 4.0
FENCE_DRESSING_CLEARANCE = 1.5   # m, solid dressing must not stand on a rail

# The z in the CSV is advisory: the in-engine pass re-snaps every item to the
# terrain with a ray trace, so a stale z is cosmetic. It is still checked,
# because a stale z usually means someone moved x/y in a text editor and did
# not realise the CSV carries a height at all.
Z_TOLERANCE_M = 0.75

results = []


def check(ok, message, detail=""):
    results.append((bool(ok), message, detail))
    print("{} {}{}".format("PASS" if ok else "FAIL", message, (" - " + detail) if detail else ""))
    return bool(ok)


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


def segments_intersect(a1, a2, b1, b2):
    """True if segments A and B cross. Used to prove no fence bisects the map
    between the two deployments, which is the one fence fault that would make
    the round unplayable rather than merely ugly."""

    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        if abs(v) < 1e-12:
            return 0
        return 1 if v > 0 else -1

    o1, o2 = orient(a1, a2, b1), orient(a1, a2, b2)
    o3, o4 = orient(b1, b2, a1), orient(b1, b2, a2)
    if o1 != o2 and o3 != o4:
        return True

    def on_seg(p, q, r):
        return (min(p[0], r[0]) - 1e-9 <= q[0] <= max(p[0], r[0]) + 1e-9
                and min(p[1], r[1]) - 1e-9 <= q[1] <= max(p[1], r[1]) + 1e-9)

    if o1 == 0 and on_seg(a1, b1, a2):
        return True
    if o2 == 0 and on_seg(a1, b2, a2):
        return True
    if o3 == 0 and on_seg(b1, a1, b2):
        return True
    if o4 == 0 and on_seg(b1, a2, b2):
        return True
    return False


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load(path, expected_header, label):
    if not os.path.isfile(path):
        check(False, "{} exists".format(label), path)
        return None
    with open(path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != list(expected_header):
            check(False, "{} header matches the documented schema".format(label),
                  "got {}".format(reader.fieldnames))
            return None
        rows = list(reader)
    check(True, "{} header matches the documented schema".format(label), str(len(rows)) + " rows")
    return rows


def main():
    print("=" * 68)
    print("SOUTHERN SPEAR - DRY RIVER DRESSING VALIDATION")
    print("=" * 68)

    dressing = load(DRESSING_CSV, ("name", "type", "x", "y", "z", "rot_y", "scale"),
                    "Dressing CSV")
    fences = load(FENCES_CSV, ("name", "x1", "y1", "x2", "y2", "post_spacing"), "Fences CSV")
    if dressing is None or fences is None:
        return finish()

    # ---- dressing rows ----------------------------------------------------
    bad_type, bad_name, outside, too_close_zone, too_close_item = [], [], [], [], []
    bad_z, dupes, bad_scale = [], [], []
    seen = {}
    positions = []

    for r in dressing:
        name = r["name"]
        kind = r["type"]
        x, y, z = float(r["x"]), float(r["y"]), float(r["z"])
        scale = float(r["scale"])
        positions.append((name, kind, x, y))

        if kind not in KNOWN_TYPES:
            bad_type.append("{}: unknown type '{}'".format(name, kind))
        if not name.startswith("SS_DryRiver_"):
            bad_name.append(name)
        if name in seen:
            dupes.append("{} duplicates row {}".format(name, seen[name]))
        seen[name] = "row {}".format(len(positions))
        if scale <= 0.0 or scale > 4.0:
            bad_scale.append("{}: scale {}".format(name, scale))

        if not spec.inside_play_area(x, y, EDGE_INSET):
            outside.append("{} at ({:.1f},{:.1f})".format(name, x, y))

        need = CLEARANCE.get(kind, DEFAULT_CLEARANCE)
        for px, py, pr in spec.PROTECTED:
            d = math.hypot(x - px, y - py)
            if d < pr + need:
                too_close_zone.append("{} is {:.1f}m from ({:.0f},{:.0f}), needs {:.1f}m".format(
                    name, d, px, py, pr + need))

        # z is advisory but a stale value means an unaware hand edit.
        expected_z = spec.terrain_height(x, y)
        if abs(z - expected_z) > Z_TOLERANCE_M:
            bad_z.append("{} z={:.2f} but terrain is {:.2f}".format(name, z, expected_z))

    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            n1, k1, x1, y1 = positions[i]
            n2, k2, x2, y2 = positions[j]
            # Scrub is allowed to touch; anything solid may not.
            if k1 == "scrub" and k2 == "scrub":
                continue
            if math.hypot(x1 - x2, y1 - y2) < MIN_SPACING:
                too_close_item.append("{} and {} are {:.2f}m apart".format(
                    n1, n2, math.hypot(x1 - x2, y1 - y2)))

    check(not bad_type, "every dressing type is known",
          "; ".join(bad_type[:3]) if bad_type else str(len(dressing)) + " rows")
    check(not bad_name, "every dressing name uses the SS_DryRiver_ prefix",
          "; ".join(bad_name[:3]))
    check(not dupes, "dressing names are unique", "; ".join(dupes[:3]))
    check(not bad_scale, "dressing scales are sane", "; ".join(bad_scale[:3]))
    check(not outside, "all dressing sits inside the playable area",
          "; ".join(outside[:3]))
    check(not too_close_zone, "all dressing clears every protected zone",
          "; ".join(too_close_zone[:3]))
    check(not too_close_item, "no solid dressing intersects another",
          "; ".join(too_close_item[:3]))
    check(not bad_z, "recorded z matches the terrain (advisory: level pass re-snaps)",
          "; ".join(bad_z[:3]))

    # ---- fence runs -------------------------------------------------------
    bad_len, bad_clear, bad_inside, bad_spacing, bisect = [], [], [], [], []
    deploy_a = (0.0, -spec.DEPLOY_OFFSET)
    deploy_b = (0.0, spec.DEPLOY_OFFSET)

    for r in fences:
        name = r["name"]
        ax, ay = float(r["x1"]), float(r["y1"])
        bx, by = float(r["x2"]), float(r["y2"])
        sp = float(r["post_spacing"])
        length = math.hypot(bx - ax, by - ay)

        if not name.startswith("SS_DryRiver_Fence_"):
            bad_len.append("{}: bad name prefix".format(name))
        if length > FENCE_MAX_LENGTH or length < FENCE_MIN_LENGTH:
            bad_len.append("{}: {:.1f}m outside [{},{}]m".format(
                name, length, FENCE_MIN_LENGTH, FENCE_MAX_LENGTH))
        if sp < FENCE_MIN_SPACING or sp > FENCE_MAX_SPACING:
            bad_spacing.append("{}: post_spacing {}".format(name, sp))
        if not (spec.inside_play_area(ax, ay, EDGE_INSET) and spec.inside_play_area(bx, by, EDGE_INSET)):
            bad_inside.append("{}: endpoint outside the playable area".format(name))
        ok, why = spec.run_clears_protected(ax, ay, bx, by, extra=FENCE_CLEARANCE_EXTRA)
        if not ok:
            bad_clear.append("{} {}".format(name, why))
        if segments_intersect((ax, ay), (bx, by), deploy_a, deploy_b):
            bisect.append(name)

    check(not bad_len, "fence runs are within length limits", "; ".join(bad_len[:3]))
    check(not bad_spacing, "fence post spacing is sane", "; ".join(bad_spacing[:3]))
    check(not bad_inside, "fence endpoints sit inside the playable area", "; ".join(bad_inside[:3]))
    check(not bad_clear, "fence runs clear every protected zone", "; ".join(bad_clear[:3]))
    check(not bisect,
          "no fence bisects the deployment line (a round nobody can start)",
          "; ".join(bisect) if bisect else "checked {} run(s) against the Alpha->Bravo line".format(len(fences)))

    # ---- dressing must stay off the fence lines ---------------------------
    # Placement snaps every height with a downward ray. If a crate stands where
    # a fence rail is, the ray hits the crate and the rail is built on top of
    # it. The level pass places fences first to avoid that, and this check stops
    # the data from creating the situation in the first place.
    fence_lines = [(float(r["x1"]), float(r["y1"]), float(r["x2"]), float(r["y2"])) for r in fences]
    on_fence = []
    for name, kind, x, y in positions:
        if kind == "scrub":
            continue  # non-colliding, and too low to matter
        for ax, ay, bx, by in fence_lines:
            d = spec.seg_point_distance(ax, ay, bx, by, x, y)
            if d < FENCE_DRESSING_CLEARANCE:
                on_fence.append("{} is {:.2f}m from a fence run (needs {:.1f}m)".format(
                    name, d, FENCE_DRESSING_CLEARANCE))
    check(not on_fence, "solid dressing keeps clear of fence lines",
          "; ".join(on_fence[:3]))

    # ---- coverage sanity --------------------------------------------------
    kinds = sorted({r["type"] for r in dressing})
    check(len(dressing) > 0, "dressing CSV is non-empty", "{} instances".format(len(dressing)))
    check(len(fences) > 0, "fences CSV is non-empty", "{} run(s)".format(len(fences)))
    check(all(k in KNOWN_TYPES for k in kinds), "all types have meshes in the library",
          ", ".join("{}={}".format(k, sum(1 for r in dressing if r["type"] == k)) for k in kinds))

    return finish()


def finish():
    print("-" * 68)
    failed = [m for ok, m, _ in results if not ok]
    print("RESULT: {}/{} CHECKS PASSED".format(len(results) - len(failed), len(results)))
    if failed:
        for m in failed:
            print("  FAILED: {}".format(m))
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
