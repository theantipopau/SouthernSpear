"""
Southern Spear - where the hands go on each weapon, from the ADF Re-Cut handAnim poses (W2).

Each ADFRC weapon names a static hand pose (handAnim[], e.g. EF88_Vg_static): the Arma soldier's
bones with the hands on that weapon. The `weapon` bone is where the weapon model's origin sits, so
each hand expressed in the weapon bone's space is that hand's place on the weapon model. No rest pose
is needed (unlike a retarget, R-32): only two bones of the same frame.

The one unknown is the axis convention between the rtm's weapon space and the converted MLOD in
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


def hands_in_weapon_space(bones, parents, frame):
    """(left, right) wrist positions in the `weapon` bone's space, metres."""
    world = world_transforms(bones, parents, frame)
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
    for m in signed_permutations():
        l, r = mat_vec(m, left), mat_vec(m, right)
        right_error = norm(sub(r, trigger))
        bore, along = distance_to_line(l, trigger, muzzle)
        if along <= 0.05 or along >= 1.0 or bore > LEFT_HAND_BORE_M:
            continue  # left hand behind the trigger, past the muzzle, or off the barrel
        score = right_error + 0.001 * (m != A3OB)  # a tie goes to the known A3OB convention
        if best is None or score < best[0]:
            best = (score, m, right_error, bore, along)
    if best is None:
        return None, {"fit": False, "reason": "no axis map puts the left hand on the barrel ahead of the trigger"}
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
    (None, None, report) when the pose does not fit the weapon.
    """
    bones, parents, frame = load_clip(stem, manifest_path, roots)
    left, right = hands_in_weapon_space(bones, parents, frame)
    m, report = choose_axis_map(left, right, tuple(trigger), tuple(muzzle))
    report["clip"] = stem
    if m is None:
        return None, None, report
    return mat_vec(m, left), mat_vec(m, right), report
