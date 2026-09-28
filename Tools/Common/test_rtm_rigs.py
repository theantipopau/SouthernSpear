"""
Tests for the ADFRC animation decoder's pose model (Docs/Sourced/ADFRC/rtm_rigs.py).

Session 057 found two errors in how the decoder read BMTR data, and this checks both fixes against
the committed evidence clips (Docs/evidence/w2_grip_clips), without Unreal or Blender:

  1. a stored quaternion means the rotation (-x, -y, z, w), not (x, y, z, w);
  2. a stored transform is a rotation of the bone about its own rest joint, relative to its parent,
     so p = J - R J for the rest joint J, and J is recovered as the fixed point - it is *not* a
     parent-relative bone offset.

The check that catches both is the one Session 057 used: solve each bone's joint as the fixed point
of its transforms across the clips, and require the residual to be sub-millimetre.  Read the data
the naive way and no bone has a consistent fixed point at all; treat p as a bone offset and its
length changes from pose to pose, which a fixed offset could never do.

The clips are grouped by rig, because two of the eight (the AUG family) order their bones
differently and are a separate, two-pose rig.  The rig with the most poses is the reference
skeleton: on it the recovered arm chain is also mirror-symmetric and the decoder agrees with
Tools/Common/adfrc_grip.py, which the W2 grip fit already relies on.

    python Tools/Common/test_rtm_rigs.py      # exit 0 when every check passes
"""

import importlib.util
import json
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import adfrc_grip as g  # noqa: E402

EVIDENCE = os.path.join(ROOT, "Docs", "evidence", "w2_grip_clips")
DECODER = os.path.join(ROOT, "Docs", "Sourced", "ADFRC", "rtm_rigs.py")

# The arm chain, the only part of these static hold poses that moves between clips.
ARM_CHAIN = (
    "leftshoulder", "rightshoulder", "leftarm", "rightarm", "leftarmroll", "rightarmroll",
    "leftforearm", "rightforearm", "leftforearmroll", "rightforearmroll", "lefthand", "righthand",
)
# Joints every one of these clips pins down: the upper arm, the elbow and the wrist.
PINNED = ("leftarm", "rightarm", "leftforearm", "rightforearm", "lefthand", "righthand")

FAILURES = []


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name + ("  " + detail if detail else ""))
    if not condition:
        FAILURES.append(name)


def load_decoder():
    spec = importlib.util.spec_from_file_location("rtm_rigs", DECODER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clips_by_rig():
    """{bones tuple: [(clip name, frame)]} - a rig is a bone list, exactly as the decoder groups."""
    groups = {}
    for name in sorted(os.listdir(EVIDENCE)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(EVIDENCE, name), encoding="utf-8") as handle:
            data = json.load(handle)
        groups.setdefault(tuple(data["bones"]), []).append((name, data["frame"]))
    return groups


def fixed_point(rtm, frames, i, rotation):
    """(joint, rms) for bone i of these frames under an arbitrary rotation reading."""
    ata = [[0.0] * 3 for _ in range(3)]
    aty = [0.0] * 3
    rows = []
    for frame in frames:
        r = rotation(frame[i]["q"])
        a = tuple(tuple((1.0 if r2 == c else 0.0) - r[r2][c] for c in range(3)) for r2 in range(3))
        y = tuple(frame[i]["p"])
        rows.append((a, y))
        for r2 in range(3):
            for c in range(3):
                ata[r2][c] += sum(a[k][r2] * a[k][c] for k in range(3))
            aty[r2] += sum(a[k][r2] * y[k] for k in range(3))
    x = rtm.solve3(ata, aty)
    if x is None:
        return None, None
    err = [rtm.mat_apply(a, x)[k] - y[k] for a, y in rows for k in range(3)]
    return x, math.sqrt(sum(e * e for e in err) / len(err))


def writer_round_trip(rtm, bones, frames):
    """Run the decoder's main() on a small on-disk tree and read the rig JSON back.

    This exercises the part the committed evidence cannot: `main()` solves each rig's rest joints
    and writes them.  It runs in a temporary directory, so it never touches Content/Sourced/.
    """
    with tempfile.TemporaryDirectory() as tmp:
        source = os.path.join(tmp, "Source", "handanim")
        os.makedirs(source)
        for number, (_clip, frame) in enumerate(frames):
            with open(os.path.join(source, "clip{0}.json".format(number)), "w", encoding="utf-8") as handle:
                json.dump({"bones": list(bones), "frames": [frame], "format": "BMTR v4",
                           "phases": [0.0, 1.0]}, handle)
        rtm.EX = tmp
        rtm.RIG_DIR = os.path.join(tmp, "Rig")
        rtm.main()
        rig_dir = os.path.join(tmp, "Rig")
        rigs = [f for f in os.listdir(rig_dir) if f.endswith(".json") and not f.startswith("_")]
        assert len(rigs) == 1, rigs
        with open(os.path.join(rig_dir, rigs[0]), encoding="utf-8") as handle:
            return json.load(handle)


def main():
    rtm = load_decoder()
    groups = clips_by_rig()
    multi = {bones: frames for bones, frames in groups.items() if len(frames) > 1}

    check("the evidence holds more than one rig, with several poses each",
          len(multi) >= 1 and all(len(f) >= 2 for f in multi.values()),
          "{0} rig(s), sizes {1}".format(len(multi), sorted(len(f) for f in multi.values())))

    reference_bones = max(multi, key=lambda b: len(multi[b]))

    for bones, frames in sorted(multi.items(), key=lambda kv: -len(kv[1])):
        n = len(bones)
        label = "rig of {0} clips".format(len(frames))
        lookup = {b.lower(): i for i, b in enumerate(bones)}
        joints, rms = rtm.solve_rest_joints([f for _name, f in frames], n)
        naive = {name: fixed_point(rtm, [f for _name, f in frames], lookup[name], rtm.mat_from_quat)
                 for name in ARM_CHAIN if name in lookup}

        solved = [name for name in ARM_CHAIN if lookup.get(name) is not None
                  and joints[lookup[name]] is not None]
        worst = max([(rms[lookup[name]], name) for name in solved] or [(0.0, "-")])
        check("{}: every solved arm joint is consistent under 1 mm".format(label),
              bool(solved) and worst[0] < 0.001,
              "worst {0} {1:.6f} m".format(worst[1], worst[0]))

        check("{}: the wrist, elbow and upper arm are pinned down".format(label),
              all(name in solved for name in PINNED), "solved: " + ", ".join(solved))

        # Error 1: reading the quaternion as stored leaves the same bones without a fixed point.
        naive_worst = max([(naive[name][1], name) for name in solved if naive[name][1] is not None]
                          or [(0.0, "-")])
        check("{}: the stored (x,y,z,w) reading finds no consistent joint".format(label),
              all(naive[name][1] is None or naive[name][1] > 0.001 for name in solved)
              and naive_worst[0] > 0.001,
              "worst {0} {1:.6f} m".format(naive_worst[1], naive_worst[0]))

        # Error 2: the stored translation is not a bone offset - that would be the same length in
        # every pose, but this one moves by tens of centimetres.
        if "lefthand" in lookup:
            lengths = [math.sqrt(sum(c * c for c in frame[lookup["lefthand"]]["p"]))
                       for _name, frame in frames]
            check("{}: the stored translation is not a constant bone offset".format(label),
                  (max(lengths) - min(lengths)) > 0.1,
                  "|p| {0:.3f}-{1:.3f} m".format(min(lengths), max(lengths)))

        # On the reference skeleton: the transform model, the mirror, and agreement with adfrc_grip.
        if bones == reference_bones:
            worst_recon = 0.0
            for name in solved:
                joint = joints[lookup[name]]
                for _clip, frame in frames:
                    r = rtm.rotation_from_stored(frame[lookup[name]]["q"])
                    worst_recon = max(worst_recon, math.dist(rtm.posed_joint(r, tuple(frame[lookup[name]]["p"]), joint), joint))
            check("{}: each stored transform fixes its joint (R J + p = J)".format(label),
                  worst_recon < 0.001, "worst {0:.6f} m".format(worst_recon))

            # The wrist and the upper arm rotate about more than one axis across these clips, so
            # all three coordinates are pinned and must mirror.  The elbow and the roll bones are
            # hinges: their rotation axis is their length, so their position along that axis is
            # only weakly determined and is not asserted here.
            for left, right in (("lefthand", "righthand"), ("leftarm", "rightarm")):
                if left not in solved or right not in solved:
                    continue
                a, b = joints[lookup[left]], joints[lookup[right]]
                check("{}: {} / {} mirror".format(label, left, right),
                      abs(a[0] + b[0]) < 0.002 and abs(a[1] - b[1]) < 0.005 and abs(a[2] - b[2]) < 0.005,
                      "{0} vs {1}".format([round(c, 4) for c in a], [round(c, 4) for c in b]))

            theirs = g.solve_rest_joints([(bones, [f]) for _name, f in frames],
                                         names=("lefthand", "righthand"))
            for name in ("lefthand", "righthand"):
                delta = math.dist(joints[lookup[name]], theirs[name][0]) if name in theirs else 9.9
                check("{}: the decoder and adfrc_grip agree on {}".format(label, name),
                      delta < 0.002, "delta {0:.6f} m".format(delta))

    # The decoder's writer: a rig JSON carries the solved rest joints, and the wrists land where
    # the evidence clips put them.
    try:
        rig = writer_round_trip(rtm, reference_bones, groups[reference_bones])
        lookup = {b.lower(): i for i, b in enumerate(rig["bones"])}
        get = lambda name: rig["rest_joints"][lookup[name]]
        check("the rig JSON carries solved rest joints",
              rig.get("schema") == "adfrc-rig/2" and rig.get("rest_joints_solved", 0) > 0,
              "schema {0}, {1} of {2} solved".format(rig.get("schema"), rig.get("rest_joints_solved"),
                                                     rig["bone_count"]))
        arm_rms = [rig["rest_joint_rms_m"][lookup[name]] for name in ARM_CHAIN if name in lookup]
        check("the written arm joints are fixed points, sub-millimetre",
              all(v is None or v < 0.001 for v in arm_rms),
              "worst {0:.6f} m".format(max(v for v in arm_rms if v is not None)))
        left, right = get("lefthand"), get("righthand")
        check("the written wrists mirror",
              left is not None and right is not None and abs(left[0] + right[0]) < 0.002,
              "{0} vs {1}".format(left, right))
        check("rest_world uses the solved joint, not the accumulated translation",
              rig["rest_world"][lookup["lefthand"]] == left)
    except Exception as error:  # noqa: BLE001
        check("the decoder writer round-trips", False, repr(error))

    print("{0} failure(s)".format(len(FAILURES)))
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
