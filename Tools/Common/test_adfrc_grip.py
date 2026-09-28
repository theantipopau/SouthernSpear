"""
Tests for Tools/Common/adfrc_grip.py on a synthetic rig (no Blender, no ADFRC files needed).

    python Tools/Common/test_adfrc_grip.py      # exit 0 when every check passes

The synthetic soldier holds a rifle whose weapon bone is rotated and offset away from the pelvis, in
the A3OB (x, z, y) convention, so a pass shows the maths recovers hand positions in weapon space,
calibrates the axis map from the trigger and muzzle alone, and rejects a pose that does not fit.
"""

import json
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adfrc_grip as g  # noqa: E402

FAILURES = []


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name + ("  " + detail if detail else ""))
    if not condition:
        FAILURES.append(name)


def quat_about_y(angle):
    return [0.0, math.sin(angle / 2), 0.0, math.cos(angle / 2)]


def sub3(a, b):
    return tuple(x - y for x, y in zip(a, b))


def close(a, b, tol=1e-6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def main():
    # Weapon-local truth (Arma space: y up, z forward along the barrel): right wrist at the grip,
    # left wrist on the handguard 0.30 m forward and a little lower.
    right_local = (0.0, -0.02, 0.0)
    left_local = (0.01, -0.04, 0.30)

    # A rig: pelvis -> spine -> weapon, and hands hung off the spine. The weapon is turned 35 degrees
    # about Y and offset, so a wrong inverse would show.
    bones = ["pelvis", "spine", "weapon", "lefthand", "righthand"]
    parents = [None, 0, 1, 1, 1]
    wr = g.quat_to_mat(quat_about_y(math.radians(35)))
    wp = (0.2, 1.3, 0.4)  # weapon bone, in spine space (spine is at the origin with no rotation)
    left_world = tuple(a + b for a, b in zip(g.mat_vec(wr, left_local), wp))
    right_world = tuple(a + b for a, b in zip(g.mat_vec(wr, right_local), wp))
    frame = [
        {"q": [0, 0, 0, 1], "p": [0, 0, 0]},
        {"q": [0, 0, 0, 1], "p": [0, 0, 0]},
        {"q": quat_about_y(math.radians(35)), "p": list(wp)},
        {"q": [0, 0, 0, 1], "p": list(left_world)},
        {"q": [0, 0, 0, 1], "p": list(right_world)},
    ]

    left, right = g.hands_in_weapon_space(bones, parents, frame)
    check("left hand recovered in weapon space", close(left, left_local), str(left))
    check("right hand recovered in weapon space", close(right, right_local), str(right))

    # The MLOD in Blender is A3OB's (x, z, y): trigger at the grip, muzzle 0.7 m forward.
    trigger = g.mat_vec(g.A3OB, (0.0, -0.01, 0.02))
    muzzle = g.mat_vec(g.A3OB, (0.0, 0.03, 0.70))
    m, report = g.choose_axis_map(left, right, trigger, muzzle)
    check("an axis map fits", m is not None, json.dumps(report))
    check("the A3OB convention is chosen", report.get("a3ob_convention") is True)
    check("right hand within tolerance", report.get("right_hand_to_trigger_m", 1) < g.RIGHT_HAND_TOLERANCE_M)

    # A pose that does not fit this weapon (hands 1 m away) is refused, not placed.
    far = tuple(c + 1.0 for c in right)
    m2, report2 = g.choose_axis_map(left, far, trigger, muzzle)
    check("an unfitting pose is refused", m2 is None, report2.get("reason", ""))

    check("48 axis maps, A3OB first", len(g.signed_permutations()) == 48 and g.signed_permutations()[0] == g.A3OB)

    # load_clip / grip_points through the manifest layout (Rig/<rig>.json + Rig/<rig>/<clip>.json).
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "Rig", "r"))
        with open(os.path.join(tmp, "Rig", "r.json"), "w") as fh:
            json.dump({"bones": bones, "parents": parents}, fh)
        with open(os.path.join(tmp, "Rig", "r", "Test_static__1.json"), "w") as fh:
            json.dump({"frames": [frame, frame]}, fh)
        manifest = os.path.join(tmp, "manifest.json")
        with open(manifest, "w") as fh:
            json.dump({"clips": {"Workshop/x/Test_static.json": {"rig_file": "Rig/r.json",
                                                                 "local_anim": "Rig/r/Test_static__1.json"}}}, fh)
        gl, gr, rep = g.grip_points("Test_static", trigger, muzzle, manifest, [tmp])
        check("grip_points through files", gl is not None and close(gr, g.mat_vec(g.A3OB, right_local)), json.dumps(rep))
        try:
            g.load_clip("Missing_static", manifest, [tmp])
            check("missing clip raises", False)
        except FileNotFoundError:
            check("missing clip raises", True)

    # Arma hierarchy: the clip stores `weapon` relative to Spine1 (Arma's parent), but the decoder's rig
    # file says righthand. Capitalised names, as in AUG_GL's rig. grip_points must pick "arma".
    abones = ["Pelvis", "Spine", "Spine1", "weapon", "RightHand", "LeftHand"]
    decoded_parents = [None, 0, 1, 4, 2, 2]  # weapon under RightHand, as rtm_rigs.py writes it
    spine1_p = (0.0, 0.3, 0.0)
    wp_arma = (0.2, 1.0, 0.4)               # weapon, relative to Spine1
    hand_off = tuple(a + b for a, b in zip(spine1_p, wp_arma))
    aframe = [
        {"q": [0, 0, 0, 1], "p": [0, 0, 0]},
        {"q": [0, 0, 0, 1], "p": [0, 0, 0]},
        {"q": [0, 0, 0, 1], "p": list(spine1_p)},
        {"q": quat_about_y(math.radians(35)), "p": list(wp_arma)},
        # hands relative to Spine1, placed where the weapon-local truth says
        {"q": [0, 0, 0, 1], "p": list(sub3(tuple(a + b for a, b in zip(g.mat_vec(wr, right_local), hand_off)), spine1_p))},
        {"q": [0, 0, 0, 1], "p": list(sub3(tuple(a + b for a, b in zip(g.mat_vec(wr, left_local), hand_off)), spine1_p))},
    ]
    check("arma hierarchy re-parents weapon to Spine1", g.parents_for(abones, decoded_parents, "arma")[3] == 2)
    l_a, r_a = g.hands_in_weapon_space(abones, g.parents_for(abones, decoded_parents, "arma"), aframe)
    check("capitalised bone names are found", close(l_a, left_local) and close(r_a, right_local), str((l_a, r_a)))
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "Rig", "a"))
        with open(os.path.join(tmp, "Rig", "a.json"), "w") as fh:
            json.dump({"bones": abones, "parents": decoded_parents}, fh)
        with open(os.path.join(tmp, "Rig", "a", "AUG_GL__1.json"), "w") as fh:
            json.dump({"frames": [aframe]}, fh)
        manifest = os.path.join(tmp, "manifest.json")
        with open(manifest, "w") as fh:
            json.dump({"clips": {"x/AUG_GL.json": {"rig_file": "Rig/a.json", "local_anim": "Rig/a/AUG_GL__1.json"}}}, fh)
        gl, gr, rep = g.grip_points("AUG_GL", trigger, muzzle, manifest, [tmp])
        check("grip_points picks the arma hierarchy", rep.get("hierarchy") == "arma" and gl is not None, json.dumps(rep)[:300])
        check("the failed hierarchy is reported with numbers",
              "decoded" in rep["attempts"] and "left_weapon_space" in rep["attempts"]["decoded"])

    # A refused fit carries its nearest miss, so a failure on real data comes back with numbers.
    _, miss = g.choose_axis_map(left, tuple(c + 5.0 for c in left), trigger, trigger)
    check("a refusal reports hand span and barrel length", "hand_span_m" in miss and "barrel_m" in miss, json.dumps(miss))

    # The shipped manifest names every grip clip the weapon build uses.
    with open(g.MANIFEST, encoding="utf-8") as fh:
        names = {k.replace("\\", "/").split("/")[-1] for k in json.load(fh)["clips"]}
    for stem in ("EF88_Vg_static", "AUG_GL", "ar15_8in_cgrip_static", "hk416_cgrip_static",
                 "ar15_10in_cgrip_static", "Minimi_Standard", "hk417_static"):
        check("manifest has " + stem, stem + ".json" in names)

    print("{} failure(s)".format(len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
