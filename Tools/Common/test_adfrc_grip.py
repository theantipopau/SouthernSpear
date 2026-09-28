"""
Tests for Tools/Common/adfrc_grip.py: a synthetic rig built the way the decoded clips are (each bone a
rotation about its own rest joint, relative to its parent, quaternions stored as (-x, -y, z, w)), then
the committed real clips (Docs/evidence/w2_grip_clips) and weapon manifests as a regression.

    python Tools/Common/test_adfrc_grip.py      # exit 0 when every check passes
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adfrc_grip as g  # noqa: E402

FAILURES = []


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name + ("  " + detail if detail else ""))
    if not condition:
        FAILURES.append(name)


def close(a, b, tol=1e-6):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def quat(axis, angle):
    n = math.sqrt(sum(c * c for c in axis))
    s = math.sin(angle / 2)
    return [axis[0] / n * s, axis[1] / n * s, axis[2] / n * s, math.cos(angle / 2)]


def stored(q):
    """What the decoded clips store for the standard quaternion q."""
    return [-q[0], -q[1], q[2], q[3]]


def about(pivot, q):
    """A clip entry rotating by q about pivot: p = pivot - R pivot."""
    r = g.clip_rotation(stored(q))
    return {"q": stored(q), "p": list(g.sub(pivot, g.mat_vec(r, pivot)))}


def det(m):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def synthetic(left_angle, axis=(0, 0, 1)):
    """Pelvis, Spine1, RightHand, LeftHand, weapon. Decoded parents put weapon under RightHand."""
    bones = ["Pelvis", "Spine1", "RightHand", "LeftHand", "weapon"]
    parents = [None, 0, 1, 1, 2]
    rest = {"righthand": (-0.58, 0.07, 0.07), "lefthand": (0.58, 0.07, 0.07)}
    frame = [
        {"q": stored([0, 0, 0, 1]), "p": [0.0, 0.0, 0.9]},              # pelvis raised to hip height
        about((0.0, 0.0, 0.14), quat((1, 0, 0), math.radians(-8))),    # spine1 leans
        about(rest["righthand"], quat(axis, math.radians(40))),
        about(rest["lefthand"], quat(axis, math.radians(left_angle))),
        {"q": stored(quat((0, 0, 1), math.radians(5))), "p": [0.9, 0.03, 0.48]},  # weapon, fixed
    ]
    return bones, parents, frame, rest


def main():
    # Rest joints are the fixed points of each bone's own transform, recovered over several poses.
    clips = []
    for angle, axis in ((-30, (0, 0, 1)), (-45, (1, 0, 0)), (-60, (0, 1, 1))):
        bones, parents, frame, rest = synthetic(angle, axis)
        clips.append((bones, [frame]))
    solved = g.solve_rest_joints(clips)
    check("rest joints recovered as fixed points",
          close(solved["lefthand"][0], rest["lefthand"], 1e-6) and close(solved["righthand"][0], rest["righthand"], 1e-6),
          str(solved))

    # Hands in weapon space: weapon re-parented to Spine1 (the rig file says RightHand).
    bones, parents, frame, rest = synthetic(-45)
    left, right = g.hands_in_weapon_space(bones, parents, frame, rest)
    posed = g.compose(bones, parents, frame)
    wr, wp = posed["weapon"]
    lj = g.add(g.mat_vec(posed["lefthand"][0], rest["lefthand"]), posed["lefthand"][1])
    check("weapon composes under Spine1, not the hand",
          close(g.add(g.mat_vec(wr, left), wp), lj, 1e-9)
          and close(sum(wr, ()), sum(g.compose(bones, [None, 0, 1, 1, 1], frame, None)["weapon"][0], ()), 1e-9))
    left_rh, _ = g.hands_in_weapon_space(bones, parents, frame, rest, weapon_parent=None)
    check("the decoder's hierarchy gives a different answer", not close(left, left_rh, 1e-3))
    check("case-insensitive bone names", "lefthand" in posed and "weapon" in posed)

    # The rest-to-MLOD rotation is proper and puts rest forward (-y) down the barrel.
    for muzzle in ((-0.5, 0.0, 0.05), (0.5, 0.0, 0.05), (0.0, 0.6, 0.05)):
        m = g.rest_to_mlod((0.0, 0.0, 0.0), muzzle)
        fwd = g.mat_vec(m, (0, -1, 0))
        check("rest_to_mlod proper, forward along barrel {}".format(muzzle),
              abs(det(m) - 1) < 1e-9 and g.dot(fwd, muzzle) > 0 and close(g.mat_vec(m, (0, 0, 1)), (0, 0, 1)))

    # A left wrist behind the trigger is refused, with numbers.
    l2, r2, rep = g.place_hands((0.0, 0.3, 0.0), (0.0, 0.0, 0.0), (0.08, 0.0, 0.02), (-0.4, 0.0, 0.06))
    check("a left hand behind the trigger is refused", l2 is None and "reason" in rep, rep.get("reason", ""))

    # Real data: the committed clips reproduce the rest joints, and every weapon fits.
    real = g.solve_rest_joints(g.evidence_clips())
    for name in ("lefthand", "righthand"):
        x, rms = real[name]
        check("real rest joint {} reproduced (rms {:.5f} m)".format(name, rms),
              close(x, g.REST_JOINTS[name], 1e-3) and rms < 0.002)
    check("the real rest skeleton is mirror-symmetric",
          abs(real["lefthand"][0][0] + real["righthand"][0][0]) < 0.005)
    pose_of = {"A88": "EF88_Vg_static", "A88G": "AUG_GL", "A4": "ar15_8in_cgrip_static", "A416": "hk416_cgrip_static",
               "A25": "ar15_10in_cgrip_static", "A89": "Minimi_Standard"}
    spans = {}
    for weapon, clip in pose_of.items():
        path = os.path.join(g.ROOT, "Art", "Weapons", weapon, "ADFRC", "manifest.json")
        with open(path, encoding="utf-8") as fh:
            grip = json.load(fh)["grip"]
        l3, r3, rep = g.grip_points(clip, grip["trigger_mlod"], grip["muzzle_mlod"])
        spans[weapon] = rep["hand_span_m"]
        check("{} fits ({})".format(weapon, clip), l3 is not None, json.dumps(
            {k: rep[k] for k in ("left_hand_forward_m", "left_hand_to_bore_m", "left_hand_along_barrel")}))
    check("an 8-inch handguard puts the hands closer than a 10-inch", spans["A4"] < spans["A25"], str(spans))

    # A standard-quaternion (schema adfrc-anim-local/2) copy of a real clip gives the same hands as the
    # stored-convention evidence: the decoder's R-64 output must not be flipped twice.
    bones_e, parents_e, frame_e = g.load_clip("hk416_cgrip_static")
    standard = [{"q": [-e["q"][0], -e["q"][1], e["q"][2], e["q"][3]], "p": e["p"]} for e in frame_e]
    converted = g.to_stored_convention([standard], "adfrc-anim-local/2")[0]
    l_old, r_old = g.hands_in_weapon_space(bones_e, parents_e, frame_e)
    l_new, r_new = g.hands_in_weapon_space(bones_e, parents_e, converted)
    check("schema /2 files read the same as the stored evidence", close(l_old, l_new, 1e-9) and close(r_old, r_new, 1e-9))
    check("schema /1 and unlabelled files are left as stored",
          g.to_stored_convention([frame_e], "adfrc-anim-local/1")[0] is frame_e and g.to_stored_convention([frame_e], "")[0] is frame_e)

    # The shipped manifest names every grip clip the weapon build uses.
    with open(g.MANIFEST, encoding="utf-8") as fh:
        names = {k.replace("\\", "/").split("/")[-1] for k in json.load(fh)["clips"]}
    for stem in pose_of.values():
        check("manifest has " + stem, stem + ".json" in names)

    print("{} failure(s)".format(len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
