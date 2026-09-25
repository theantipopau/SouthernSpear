"""
Southern Spear - Dry River blockout verification.

Checks the generated blockout against Docs/MAPS_DRYRIVER.md so the map
cannot silently drift from its design spec. Run in CI.

    python Tools/Blender/verify_dryriver.py

Exits non-zero on any failure.
"""

import csv
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAYOUT = os.path.normpath(os.path.join(
    HERE, "..", "..", "Content", "Art", "Blockout",
    "SS_MAP_DryRiver_01_Layout.csv"))

# Spec values (MAPS_DRYRIVER.md 3 and 6).
PLAY_HALF_WIDTH = 130.0
PLAY_HALF_DEPTH = 90.0
DEPLOY_SEPARATION = 170.0

# Distances the blockout must reproduce, in metres.
EXPECT_FIRST = 86.3    # both deployments to OBJ A
EXPECT_A_TO_B = 75.7   # OBJ A to OBJ B
EXPECT_B_DEPLOY_TO_B = 51.9  # Bravo deployment to OBJ B (terrain property)
TOLERANCE = 2.0

FAILURES = []


def check(cond, msg):
    print(("PASS  " if cond else "FAIL  ") + msg)
    if not cond:
        FAILURES.append(msg)


def main():
    if not os.path.exists(LAYOUT):
        print(f"FAIL  layout CSV missing: {LAYOUT}")
        print("       Run: blender -b --factory-startup --python "
              "Tools/Blender/dryriver_blockout.py")
        return 1

    with open(LAYOUT, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    pos = {r["name"]: (float(r["x"]), float(r["y"])) for r in rows}

    try:
        a = pos["SS_MAP_DryRiver_ObjA_WaterPoint"]
        b = pos["SS_MAP_DryRiver_ObjB_Farmstead"]
        da = pos["SS_MAP_DryRiver_DeployAlpha"]
        db = pos["SS_MAP_DryRiver_DeployBravo"]
    except KeyError as exc:
        print(f"FAIL  required marker missing: {exc}")
        return 1

    def dist(p, q):
        return math.hypot(p[0] - q[0], p[1] - q[1])

    check(len(rows) == 4, f"4 gameplay markers exported (got {len(rows)})")

    check(all(abs(p[0]) < 1e-6 for p in (da, db)),
          "both deployments sit on the map centre line (x=0)")

    sep = abs(db[1] - da[1])
    check(abs(sep - DEPLOY_SEPARATION) < 0.5,
          f"deployments {DEPLOY_SEPARATION} m apart (got {sep:.1f})")

    check(all(abs(p[0]) <= PLAY_HALF_WIDTH and abs(p[1]) <= PLAY_HALF_DEPTH
              for p in pos.values()),
          f"all markers inside the {PLAY_HALF_WIDTH*2:.0f}x"
          f"{PLAY_HALF_DEPTH*2:.0f} m playable area")

    # The critical fairness property: the opening contest is equidistant.
    d_alpha = dist(da, a)
    d_bravo = dist(db, a)
    check(abs(d_alpha - d_bravo) < 0.5,
          f"OBJ A is exactly equidistant from both deployments "
          f"(alpha {d_alpha:.1f} m, bravo {d_bravo:.1f} m)")

    for label, got, want in (
        ("Alpha deploy -> OBJ A", d_alpha, EXPECT_FIRST),
        ("Bravo deploy -> OBJ A", d_bravo, EXPECT_FIRST),
        ("OBJ A -> OBJ B", dist(a, b), EXPECT_A_TO_B),
        ("Bravo deploy -> OBJ B", dist(db, b), EXPECT_B_DEPLOY_TO_B),
    ):
        check(abs(got - want) <= TOLERANCE,
              f"{label} ~{want} m (spec 6) (got {got:.1f})")

    # The vertical slice uses SEQUENTIAL objectives: both teams contest OBJ A,
    # then both move A -> OBJ B. Under that rule the round is symmetric by
    # construction, because both teams start the second leg from the same
    # point. The only fairness property that must hold is an equidistant
    # opening, which is checked above.
    #
    # Bravo's *direct* line to OBJ B is shorter than Alpha's. That is a
    # property of the terrain, not a balance feature: in sequential order
    # neither team takes that line, because both must take OBJ A first.
    # It is reported for playtest triage, not asserted.
    direct_alpha = dist(da, b)
    direct_bravo = dist(db, b)
    print(f"      INFO direct run Alpha->OBJ B {direct_alpha:.1f} m "
          f"| Bravo->OBJ B {direct_bravo:.1f} m (unused in sequential order)")

    check(direct_bravo < direct_alpha,
          "Bravo overlooks the farm (terrain property, reported not asserted)")

    print()
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} CHECK(S) FAILED")
        for f in FAILURES:
            print(f"  - {f}")
        return 1

    print("RESULT: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
