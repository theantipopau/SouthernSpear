"""
Tests for Tools/Common/adfrc_reload.py (W5) on a synthetic reload built the way the decoded clips are.

    python Tools/Common/test_adfrc_reload.py      # exit 0 when every check passes
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adfrc_grip as g  # noqa: E402
import adfrc_reload as r  # noqa: E402

FAILURES = []


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name + ("  " + detail if detail else ""))
    if not condition:
        FAILURES.append(name)


def stored(q):
    return [-q[0], -q[1], q[2], q[3]]


def translate(offset):
    """A clip entry that moves a bone by offset without rotating it (p = J - R J + move = move)."""
    return {"q": stored([0, 0, 0, 1]), "p": list(offset)}


def main():
    # A rig where the weapon sits on Spine1 and both wrists hang off Spine1 too, so a wrist's stored
    # translation moves it directly (its rest joint is the fixed point of an identity rotation).
    bones = ["Pelvis", "Spine1", "weapon", "RightHand", "LeftHand"]
    parents = [None, 0, 4, 1, 1]  # the decoder's rule would hang weapon elsewhere; Spine1 is forced
    rest = dict(g.REST_JOINTS)
    # Place the right wrist 0.1 m below the weapon origin and the left wrist on a path: 0.25 m forward at
    # the start, down to the magazine well (0.05 m forward, 0.12 m down) half-way, then back.
    right_target = (0.0, 0.0, -0.1)       # rest space: x left, -y forward, z up
    frames = []
    count = 41
    for k in range(count):
        t = k / (count - 1)
        blend = math.sin(math.pi * t)     # 0 -> 1 -> 0
        forward = 0.25 - 0.20 * blend
        down = 0.12 * blend
        left_target = (0.05, -forward, -0.1 - down)
        frames.append([
            translate((0, 0, 0)),
            translate((0, 0, 0)),
            translate((0, 0, 0)),
            translate(g.sub(right_target, rest["righthand"])),
            translate(g.sub(left_target, rest["lefthand"])),
        ])

    trigger, muzzle = (0.08, 0.0, 0.02), (-0.34, 0.0, 0.07)   # an A88-like MLOD: barrel along -x, z up
    path = r.reload_path("synthetic", trigger, muzzle, samples=5, frames_override=(bones, parents, frames))
    check("five keys from 0 to 1", [k["t"] for k in path["keys"]] == [0.0, 0.25, 0.5, 0.75, 1.0], json.dumps(path["keys"]))
    start, middle = path["keys"][0]["left_cm"], path["keys"][2]["left_cm"]
    check("starts 25 cm forward of the grip", abs(start[0] - 25.0) < 0.01, str(start))
    check("the left hand is to the shooter's left (negative right)", start[1] < 0 and abs(start[1] + 5.0) < 0.01, str(start))
    check("level with the grip at the start", abs(start[2]) < 0.01, str(start))
    check("half-way it is at the magazine well: 5 cm forward, 12 cm down", abs(middle[0] - 5.0) < 0.01 and abs(middle[2] + 12.0) < 0.01, str(middle))
    check("returns to the start", g.norm(g.sub(path["end_cm"], path["start_cm"])) < 0.01)
    check("no jumps between frames", path["max_step_cm"] < 3.0, str(path["max_step_cm"]))

    # The weapon's axes: forward down the barrel, up is up, right is the shooter's right (+y here).
    forward, right, up = r.weapon_axes(trigger, muzzle)
    check("weapon axes", forward == (-1.0, 0.0, 0.0) and up == (0.0, 0.0, 1.0) and right == (0.0, 1.0, 0.0), str((forward, right, up)))

    # A single-frame clip is refused.
    try:
        r.reload_path("one", trigger, muzzle, frames_override=(bones, parents, frames[:1]))
        check("a one-frame clip is refused", False)
    except ValueError:
        check("a one-frame clip is refused", True)

    # The real grip pose, in the same axes, puts the left hand forward and to the left of the right hand.
    with open(os.path.join(g.ROOT, "Art", "Weapons", "A88", "ADFRC", "manifest.json"), encoding="utf-8") as fh:
        grip = json.load(fh)["grip"]
    offset = r.grip_offset("EF88_Vg_static", grip["trigger_mlod"], grip["muzzle_mlod"])
    check("A88 grip pose: left hand forward and to the left", offset[0] > 10.0 and offset[1] < 0.0, str(offset))

    print("{} failure(s)".format(len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
