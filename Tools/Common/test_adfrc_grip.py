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

    # W2b: the authored hold. The socket's basis is the hand on every weapon, and it is a proper
    # rotation, so the one HandRotationOffset the game solves from SK_FP_Arms_Rifle's finger bones
    # fits every weapon. A hold is a rotation in the weapon's own axes, not a borrowed pose.
    #
    # `report` rounds its vectors to 4 dp, so a value compared against it is compared at 1e-3; the
    # rotation itself is checked at 1e-9.
    trig, muz = (0.0, 0.0, 0.0), (0.42, 0.0, 0.049)          # the A88's own trigger -> muzzle
    world_up = (0.0, 0.0, 1.0)
    fwd = g.unit(g.sub(muz, trig))
    up = g.unit(g.sub(world_up, tuple(fwd[i] * g.dot(fwd, world_up) for i in range(3))))
    basis = (fwd, g.cross(fwd, up), up)                      # as adfrc_reload.weapon_axes defines it
    check("the test basis is orthonormal, like weapon_axes",
          all(abs(g.norm(b) - 1.0) < 1e-9 for b in basis) and abs(g.dot(basis[0], basis[1])) < 1e-9
          and abs(g.dot(basis[0], basis[2])) < 1e-9 and abs(g.dot(basis[1], basis[2])) < 1e-9
          and g.dot(g.cross(basis[0], basis[1]), basis[2]) < -0.999,
          str([round(g.norm(b), 9) for b in basis]))

    # The change of coordinates itself, checked against the basis it is given. Written out longhand
    # here on purpose: a test that recomputes the expression it is testing agrees with its bugs.
    for j, name in enumerate(("forward", "right", "up")):
        unit_fru = [0.0, 0.0, 0.0]
        unit_fru[j] = 1.0
        check("+{} in the hold's axes is the weapon's {}".format(name, name),
              close(g.hold_axis(tuple(unit_fru), basis), basis[j], 1e-12),
              "{} vs {}".format([round(c, 6) for c in g.hold_axis(tuple(unit_fru), basis)],
                                [round(c, 6) for c in basis[j]]))
    # A tilt rotates inside the plane its two axes span, so the result stays perpendicular to the
    # remaining axis (forward), and lands 30 deg from the base towards the target.
    tilted = g.hold_axis(("tilt", (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), 30.0), basis)
    check("a tilt rotates inside its own plane, 30 deg from base towards target",
          abs(g.dot(tilted, fwd)) < 1e-12
          and abs(math.degrees(math.acos(max(-1.0, min(1.0, g.dot(tilted, up))))) - 30.0) < 1e-9
          and abs(g.dot(tilted, basis[1]) - math.sin(math.radians(30.0))) < 1e-9,
          str([round(c, 6) for c in tilted]))

    def col_of(m, k):
        return (m[0][k], m[1][k], m[2][k])

    for name in ("plain_handguard", "vertical_grip"):
        rot, rep = g.resolve_hold(name, trig, muz)
        cols = [col_of(rot, k) for k in range(3)]
        check("{} is orthonormal".format(name),
              all(abs(g.norm(c) - 1.0) < 1e-9 for c in cols) and
              all(abs(g.dot(cols[a], cols[b])) < 1e-9 for a in range(3) for b in range(3) if a != b),
              str([round(g.dot(cols[0], cols[1]), 9), round(g.dot(cols[0], cols[2]), 9)]))
        check("{} is right-handed (det +1)".format(name),
              abs(g.dot(cols[0], g.cross(cols[1], cols[2])) - 1.0) < 1e-9)
        check("{}: the socket's axes are +X palm, +Y finger, +Z thumb".format(name),
              close(cols[0], rep["palm"], 1e-3) and close(cols[1], rep["finger"], 1e-3)
              and close(cols[2], rep["thumb_derived"], 1e-3),
              "X={} Y={} Z={}".format([round(c, 4) for c in cols[0]], [round(c, 4) for c in cols[1]],
                                       [round(c, 4) for c in cols[2]]))
        # The palm normal, measured against the weapon's own axes rather than recomputed from them.
        tilt = 30.0 if name == "plain_handguard" else 90.0
        check("{}: the palm normal is {:.0f} deg off the bore's up, towards +right".format(name, tilt),
              abs(math.degrees(math.acos(max(-1.0, min(1.0, g.dot(rep["palm"], up))))) - tilt) < 0.05
              and abs(g.dot(rep["palm"], basis[1]) - math.sin(math.radians(tilt))) < 0.001,
              "palm.up={:.4f} palm.right={:.4f}".format(g.dot(rep["palm"], up), g.dot(rep["palm"], basis[1])))
        # A left hand obeys palm x finger = thumb, so a self-consistent hold needs no correction;
        # the vertical grip's 30 deg finger tilt is an authored deviation and is reported, not hidden.
        expect = 0.0 if name == "plain_handguard" else 30.0
        check("{}: thumb deviation is the authored {}".format(name, expect),
              abs(rep["thumb_deviation_deg"] - expect) < 0.05,
              "thumb_deviation_deg={}".format(rep["thumb_deviation_deg"]))

    # The A88's hold specifically: palm under-left of the tube, fingers wrapping over, thumb at the muzzle.
    rot, rep = g.resolve_hold("plain_handguard", trig, muz)
    check("the A88's thumb points at the muzzle", close(rep["thumb_derived"], fwd, 1e-3),
          "thumb={} muzzle_dir={}".format([round(c, 4) for c in rep["thumb_derived"]],
                                           [round(c, 4) for c in fwd]))
    check("the A88's fingers wrap towards +right, rolled 30 deg by the palm tilt",
          abs(g.dot(rep["finger"], basis[1]) - math.cos(math.radians(30.0))) < 0.001,
          "finger.right={:.4f} (cos30={:.4f})".format(g.dot(rep["finger"], basis[1]),
                                                        math.cos(math.radians(30.0))))
    finger_vs_palm = math.degrees(math.acos(max(-1.0, min(1.0, g.dot(rep["finger"], rep["palm"])))))
    check("the A88's fingers are square to the palm, as a hand's are", abs(finger_vs_palm - 90.0) < 0.05,
          "finger.palm={:.2f} deg".format(finger_vs_palm))

    # A weapon with no row gets no rotation and a reason, not a bare socket.
    nothing = g.resolve_hold(None, trig, muz)
    check("an unauthored hold is refused, with a reason", nothing[0] is None and "reason" in nothing[1],
          json.dumps(nothing[1]))
    try:
        g.resolve_hold("no_such_hold", trig, muz)
        check("an unknown profile name is refused", False)
    except ValueError as error:
        check("an unknown profile name is refused", "plain_handguard" in str(error), str(error))

    # Per-weapon choices and angles are data, and they beat the profile.
    _, rep = g.resolve_hold({"profile": "plain_handguard", "palm": (0.0, 0.0, 1.0)}, trig, muz)
    check("a per-weapon palm override is honoured",
              rep["thumb_deviation_deg"] < 0.05 and abs(g.dot(rep["palm"], basis[1])) < 0.001,
              "palm={} thumb_deviation_deg={}".format([round(c, 4) for c in rep["palm"]],
                                                      rep["thumb_deviation_deg"]))
    _, rep = g.resolve_hold({"profile": "plain_handguard",
                             "palm": ("tilt", (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), 45.0)}, trig, muz)
    check("a per-weapon tilt is honoured",
              abs(g.dot(rep["palm"], basis[1]) - math.sin(math.radians(45.0))) < 0.001,
              "palm.right={:.4f} (sin45={:.4f})".format(g.dot(rep["palm"], basis[1]),
                                                         math.sin(math.radians(45.0))))

    # A folded hold (the finger onto the palm normal) is an error, not a NaN rotation.
    try:
        g.resolve_hold({"profile": "plain_handguard", "palm": (0.0, 0.0, 1.0), "finger": (0.0, 0.0, 1.0)},
                       trig, muz)
        check("a folded hold is refused", False)
    except ValueError as error:
        check("a folded hold is refused", "parallel" in str(error), str(error))

    # The shipped A88 manifest carries the hold, and the socket's position is untouched by it.
    with open(os.path.join(g.ROOT, "Art", "Weapons", "A88", "ADFRC", "manifest.json"), encoding="utf-8") as fh:
        a88 = json.load(fh)
    check("the A88 manifest records the hold", a88.get("hold", {}).get("hold") == "plain_handguard",
          json.dumps(a88.get("hold", {}).get("hold")))
    check("the A88 manifest records the socket axes the offset is solved against",
          a88.get("hold", {}).get("socket_axes") == {"x": "palm normal", "y": "finger direction",
                                                      "z": "thumb direction"},
          json.dumps(a88.get("hold", {}).get("socket_axes")))
    check("the hold did not move the socket: the wrist is where the clip put it",
          close(a88["grip"]["left_m"], [0.2223, 0.094, -0.0151], 1e-4)
          and abs(a88["grip"]["left_hand_forward_m"] - 0.2187) < 1e-4,
          "left_m={} forward={}".format(a88["grip"]["left_m"], a88["grip"]["left_hand_forward_m"]))

    print("{} failure(s)".format(len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())


