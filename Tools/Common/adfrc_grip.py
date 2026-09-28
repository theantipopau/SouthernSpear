"""
Southern Spear - where the hands go on each weapon, from the ADF Re-Cut handAnim poses (W2).

Each ADFRC weapon names a static hand pose (handAnim[], e.g. EF88_Vg_static): the Arma soldier's
bones with the hands on that weapon. The `weapon` bone is where the weapon model's origin sits, so
each hand expressed in the weapon bone's space is that hand's place on the weapon model. No rest pose
is needed (unlike a retarget, R-32): only two bones of the same frame.

Which parent the `weapon` bone composes under is the second unknown. The decoder's rig files
(rtm_rigs.py) hang it off `righthand` by naming rule; the clips list their bones in Arma's own
skeleton order (pelvis, spine..spine3, camera, weapon, launcher), where `weapon` and `launcher` are
children of `Spine1` and `Camera` of `Pelvis`. Both hierarchies are tried (HIERARCHIES) and the one
that fits is reported, so the first real run decides it (Session 054: all seven weapons failed with
the decoder's hierarchy alone). Bone names are matched case-insensitively (AUG_GL's rig uses
`LeftHand`).

The first unknown is the axis convention between the rtm's weapon space and the converted MLOD in
Blender. It is not assumed: `choose_axis_map` tries all 48 signed axis permutations and keeps the
one that puts the right hand on the weapon's own `trigger_axis` memory point with the left hand
forward along the barrel. A weapon where no mapping fits within tolerance gets no sockets and says
why, rather than sockets in the wrong place.

Pure Python (no bpy), so it is unit-tested outside Blender: python Tools/Common/test_adfrc_grip.py
Used by Tools/Blender/adfrc_weapon.py (SS_GRIP_CLIP).
"""

import itertools
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(ROOT, "Docs", "Sourced", "ADFRC", "ASSET_MANIFEST.json")
# Where the decoded Animations/ tree lives on the producer's machine (git-ignored).
ANIM_ROOTS = [
    os.path.join(ROOT, "Content", "Sourced", "ADF_Extracted", "Animations"),
    os.path.join(ROOT, "Art", "ADFRC", "Animations"),
]
RIGHT_HAND_TOLERANCE_M = 0.12   # right hand (wrist) to the trigger memory point
LEFT_HAND_BORE_M = 0.20         # left hand (wrist) to the bore line

# Arma3ObjectBuilder imports Arma's Y-up space as (x, z, y); tried first, so a tie goes to it.
A3OB = ((1, 0, 0), (0, 0, 1), (0, 1, 0))


# --------------------------------------------------------------------------- vector maths

def sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def norm(a):
    return math.sqrt(dot(a, a))


def mat_vec(m, v):
    return tuple(sum(m[r][c] * v[c] for c in range(3)) for r in range(3))


def mat_mul(a, b):
    return tuple(tuple(sum(a[r][k] * b[k][c] for k in range(3)) for c in range(3)) for r in range(3))


def transpose(m):
    return tuple(tuple(m[c][r] for c in range(3)) for r in range(3))


def quat_to_mat(q):
    """[x, y, z, w] (the decoded rtm order) to a 3x3 rotation."""
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


# --------------------------------------------------------------------------- pose

def world_transforms(bones, parents, frame):
    """Parent-relative {"q","p"} per bone -> {name: (rotation, position)} in the clip's space."""
    world = [None] * len(bones)

    def solve(i, depth=0):
        if world[i] is not None:
            return world[i]
        local_r, local_p = quat_to_mat(frame[i]["q"]), tuple(frame[i]["p"])
        p = parents[i]
        if p is None or depth > len(bones):
            world[i] = (local_r, local_p)
        else:
            pr, pp = solve(p, depth + 1)
            world[i] = (mat_mul(pr, local_r), tuple(a + b for a, b in zip(mat_vec(pr, local_p), pp)))
        return world[i]

    for i in range(len(bones)):
        solve(i)
    return {name: world[i] for i, name in enumerate(bones)}


# Arma's OFP2_ManSkeleton parents for the attachment bones, which the decoder's naming rules put
# elsewhere (weapon -> righthand, launcher -> lefthand, camera -> head).
ARMA_ATTACHMENT_PARENTS = {"weapon": "spine1", "launcher": "spine1", "camera": "pelvis"}
HIERARCHIES = ("arma", "decoded")


def parents_for(bones, parents, hierarchy):
    """The rig's parent list, or with Arma's attachment parents substituted ("arma")."""
    if hierarchy == "decoded":
        return list(parents)
    index = {b.lower(): i for i, b in enumerate(bones)}
    out = list(parents)
    for child, parent in ARMA_ATTACHMENT_PARENTS.items():
        if child in index and parent in index:
            out[index[child]] = index[parent]
    return out


def hands_in_weapon_space(bones, parents, frame):
    """(left, right) wrist positions in the `weapon` bone's space, metres."""
    world = {name.lower(): value for name, value in world_transforms(bones, parents, frame).items()}
    missing = [b for b in ("weapon", "lefthand", "righthand") if b not in world]
    if missing:
        raise ValueError("pose has no bone(s): " + ", ".join(missing))
    wr, wp = world["weapon"]
    inv = transpose(wr)
    return tuple(mat_vec(inv, sub(world[h][1], wp)) for h in ("lefthand", "righthand"))


# --------------------------------------------------------------------------- calibration

def signed_permutations():
    """All 48 axis maps (permutations with signs), A3OB's first."""
    maps = [A3OB]
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            m = tuple(tuple(signs[r] if c == perm[r] else 0 for c in range(3)) for r in range(3))
            if m not in maps:
                maps.append(m)
    return maps


def distance_to_line(point, a, b):
    ab = sub(b, a)
    length = norm(ab) or 1.0
    t = dot(sub(point, a), ab) / (length * length)
    closest = tuple(a[i] + ab[i] * t for i in range(3))
    return norm(sub(point, closest)), t


def choose_axis_map(left, right, trigger, muzzle):
    """
    The axis map that puts the right hand on the trigger and the left hand on the barrel side of it.
    Returns (map, report); map is None when nothing fits within tolerance.
    """
    best = None
    nearest = None  # the closest map that fails the left-hand test, for the report
    for m in signed_permutations():
        l, r = mat_vec(m, left), mat_vec(m, right)
        right_error = norm(sub(r, trigger))
        bore, along = distance_to_line(l, trigger, muzzle)
        if along <= 0.05 or along >= 1.0 or bore > LEFT_HAND_BORE_M:
            # left hand behind the trigger, past the muzzle, or off the barrel
            miss = right_error + max(0.0, bore - LEFT_HAND_BORE_M) + max(0.0, 0.05 - along) + max(0.0, along - 1.0)
            if nearest is None or miss < nearest[0]:
                nearest = (miss, m, right_error, bore, along)
            continue
        score = right_error + 0.001 * (m != A3OB)  # a tie goes to the known A3OB convention
        if best is None or score < best[0]:
            best = (score, m, right_error, bore, along)
    if best is None:
        report = {"fit": False, "reason": "no axis map puts the left hand on the barrel ahead of the trigger",
                  "hand_span_m": round(norm(sub(left, right)), 4),
                  "barrel_m": round(norm(sub(muzzle, trigger)), 4)}
        if nearest is not None:
            _, m, right_error, bore, along = nearest
            report["nearest"] = {"axis_map": [list(row) for row in m], "right_hand_to_trigger_m": round(right_error, 4),
                                 "left_hand_to_bore_m": round(bore, 4), "left_hand_along_barrel": round(along, 3)}
        return None, report
    _, m, right_error, bore, along = best
    report = {"fit": right_error <= RIGHT_HAND_TOLERANCE_M, "axis_map": [list(row) for row in m],
              "a3ob_convention": m == A3OB, "right_hand_to_trigger_m": round(right_error, 4),
              "left_hand_to_bore_m": round(bore, 4), "left_hand_along_barrel": round(along, 3)}
    if not report["fit"]:
        report["reason"] = "right hand {:.3f} m from the trigger (> {} m)".format(right_error, RIGHT_HAND_TOLERANCE_M)
        return None, report
    return m, report


# --------------------------------------------------------------------------- files

def load_clip(stem, manifest_path=MANIFEST, roots=None):
    """(bones, parents, first frame) of the decoded clip named <stem> (e.g. EF88_Vg_static)."""
    with open(manifest_path, encoding="utf-8") as fh:
        clips = json.load(fh)["clips"]
    entry = None
    for key, value in clips.items():
        name = key.replace("\\", "/").split("/")[-1]
        if name.lower() == (stem + ".json").lower() and value.get("local_anim"):
            entry = value
            break
    if not entry:
        raise FileNotFoundError("clip {} is not in {}".format(stem, manifest_path))
    for root in roots or ANIM_ROOTS:
        rig_path = os.path.join(root, entry["rig_file"])
        clip_path = os.path.join(root, entry["local_anim"])
        if os.path.exists(rig_path) and os.path.exists(clip_path):
            with open(rig_path, encoding="utf-8") as fh:
                rig = json.load(fh)
            with open(clip_path, encoding="utf-8") as fh:
                clip = json.load(fh)
            return rig["bones"], rig["parents"], clip["frames"][0]
    raise FileNotFoundError("decoded clip {} not found under {}".format(entry["local_anim"], roots or ANIM_ROOTS))


def grip_points(stem, trigger, muzzle, manifest_path=MANIFEST, roots=None):
    """
    Left and right wrist positions in the MLOD's (pre-transform) space for weapon pose <stem>, or
    (None, None, report) when the pose does not fit the weapon. Each hierarchy in HIERARCHIES is
    tried; the report names the one used and carries every attempt's numbers.
    """
    bones, parents, frame = load_clip(stem, manifest_path, roots)
    trigger, muzzle = tuple(trigger), tuple(muzzle)
    attempts = {}
    chosen = None
    for hierarchy in HIERARCHIES:
        left, right = hands_in_weapon_space(bones, parents_for(bones, parents, hierarchy), frame)
        m, report = choose_axis_map(left, right, trigger, muzzle)
        report["left_weapon_space"] = [round(c, 4) for c in left]
        report["right_weapon_space"] = [round(c, 4) for c in right]
        attempts[hierarchy] = report
        if m is not None and (chosen is None or report["right_hand_to_trigger_m"] < chosen[3]["right_hand_to_trigger_m"]):
            chosen = (hierarchy, left, right, report, m)
    result = {"clip": stem, "trigger_mlod": [round(c, 4) for c in trigger],
              "muzzle_mlod": [round(c, 4) for c in muzzle], "attempts": attempts}
    if chosen is None:
        result.update({"fit": False, "reason": "no hierarchy fits: " + "; ".join(
            "{}: {}".format(h, r.get("reason", "")) for h, r in attempts.items())})
        return None, None, result
    hierarchy, left, right, report, m = chosen
    result.update({k: v for k, v in report.items() if k not in ("left_weapon_space", "right_weapon_space")})
    result["hierarchy"] = hierarchy
    return mat_vec(m, left), mat_vec(m, right), result


# --------------------------------------------------------------------------- evidence export

GRIP_CLIPS = ("EF88_Vg_static", "AUG_GL", "AUG", "ar15_8in_cgrip_static", "hk416_cgrip_static",
              "ar15_10in_cgrip_static", "Minimi_Standard", "hk417_static")


def export(out_dir, stems=GRIP_CLIPS, manifest_path=MANIFEST, roots=None):
    """Copy each grip clip's first frame and its rig (bones, parents, rest) to out_dir, so the pose
    maths can be checked without the git-ignored Animations/ tree. Small JSON, ADFRC (ADR-035)."""
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for stem in stems:
        try:
            bones, parents, frame = load_clip(stem, manifest_path, roots)
        except FileNotFoundError as error:
            print("skip", stem, error)
            continue
        path = os.path.join(out_dir, stem + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"clip": stem, "bones": bones, "parents": parents, "frame": frame}, fh)
        written.append(path)
        for hierarchy in HIERARCHIES:
            try:
                left, right = hands_in_weapon_space(bones, parents_for(bones, parents, hierarchy), frame)
                print("{:24s} {:8s} left {} right {} span {:.3f} m".format(
                    stem, hierarchy, [round(c, 3) for c in left], [round(c, 3) for c in right], norm(sub(left, right))))
            except ValueError as error:
                print("{:24s} {:8s} {}".format(stem, hierarchy, error))
    return written


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "--export":
        print("{} clip(s) written".format(len(export(sys.argv[2]))))
    else:
        print("usage: python Tools/Common/adfrc_grip.py --export Docs/evidence/w2_grip_clips")
