"""
Southern Spear - where the hands go on each weapon, from the ADF Re-Cut handAnim poses (W2).

Each ADFRC weapon names a static hand pose (handAnim[], e.g. EF88_Vg_static): the Arma soldier's arms
holding that weapon. This module turns one into two points on the weapon model, the left and right
wrists, which become SOCKET_LeftHandGrip / SOCKET_RightHandGrip.

What the decoded clips actually hold (Session 056, measured on Docs/evidence/w2_grip_clips):

- **Each bone's transform is a rotation about its own rest joint, relative to its parent**, in the
  soldier's rest (model) space - not a bone offset. A pose-independent bone length would make a child's
  offset constant across poses; `lefthand`'s ranges 0.08-0.42 m across clips of one rig. Instead, every
  arm bone's transform has a fixed point, the same in every clip to under a millimetre: its rest joint.
  So the joint in pose = (the bone's transforms composed down the hierarchy) applied to that rest joint.
- **The decoder stored the quaternion's handedness wrong for these positions**: rotations must be read
  as (-x, -y, z, w). Only that reading makes the fixed points consistent (sum of residuals over ten arm
  joints 1.04 m as stored, under 0.001 m corrected), and the recovered skeleton is mirror-symmetric
  (wrists at x = +/-0.587 m).
- **`weapon` hangs off the body (Arma: Spine1), not the right hand** (rtm_rigs.py's naming rule). Its
  transform is identical in every rifle clip; the arms move to it. Parented to the hand it would move
  with the hand; parented to the body the right wrist lands at the same place on the weapon in every
  clip (1-4 cm) and the left wrist forward along one axis.
- Rest space is x = soldier's left, -y = forward, z = up. The converted MLOD in Blender has the barrel
  along one horizontal axis and z up; REST_TO_MLOD is the one proper rotation between the two, chosen
  from the weapon's own trigger and muzzle points (no search over reflections).

The weapon's rest placement in the soldier model (its proxy) is not in the clips, so the right wrist is
anchored at the weapon's `trigger_axis` memory point and the left wrist placed relative to it. That
relative placement is the part the pose measures; the fit test is that it lands on the barrel, ahead of
the trigger and near the bore. Downstream, attach the weapon by SOCKET_RightHandGrip and drive left-hand
IK to SOCKET_LeftHandGrip, so the two hands keep the pose's spacing whatever the absolute offset.

Pure Python (no bpy, no numpy): python Tools/Common/test_adfrc_grip.py
Used by Tools/Blender/adfrc_weapon.py (SS_GRIP_CLIP).
"""

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(ROOT, "Docs", "Sourced", "ADFRC", "ASSET_MANIFEST.json")
EVIDENCE = os.path.join(ROOT, "Docs", "evidence", "w2_grip_clips")
# Where the decoded Animations/ tree lives on the producer's machine (git-ignored).
ANIM_ROOTS = [
    os.path.join(ROOT, "Content", "Sourced", "ADF_Extracted", "Animations"),
    os.path.join(ROOT, "Art", "ADFRC", "Animations"),
]

# Arma's parent for the weapon bone (OFP2_ManSkeleton); the decoder's rig files say righthand.
WEAPON_PARENT = "spine1"

# Rest joints (soldier rest space, metres), solved as the fixed points of each bone's transforms over
# the eight committed grip clips: `python Tools/Common/adfrc_grip.py --solve-rest` reproduces them.
REST_JOINTS = {
    "lefthand": (0.5872, 0.0743, 0.0665),
    "righthand": (-0.5858, 0.0744, 0.0659),
}

# Fit tolerances for the left wrist, relative to the right wrist anchored at the trigger.
LEFT_BORE_MAX_M = 0.15          # wrist to the bore line (the wrist sits beside and below the handguard)
LEFT_FORWARD_MIN_M = 0.10       # ahead of the trigger ...
LEFT_ALONG_MAX = 1.0            # ... and not past the muzzle


# --------------------------------------------------------------------------- vector maths

def sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def add(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    return math.sqrt(dot(a, a))


def mat_vec(m, v):
    return tuple(sum(m[r][c] * v[c] for c in range(3)) for r in range(3))


def mat_mul(a, b):
    return tuple(tuple(sum(a[r][k] * b[k][c] for k in range(3)) for c in range(3)) for r in range(3))


def transpose(m):
    return tuple(tuple(m[c][r] for c in range(3)) for r in range(3))


def quat_to_mat(q):
    """[x, y, z, w] to a 3x3 rotation (standard convention; see clip_rotation for the clips' own)."""
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def clip_rotation(q):
    """A decoded clip's stored quaternion as the rotation that goes with its stored positions."""
    return quat_to_mat((-q[0], -q[1], q[2], q[3]))


def solve3(a, b):
    """Solve the 3x3 system a x = b (Gaussian elimination with pivoting); None when singular."""
    m = [list(a[r]) + [b[r]] for r in range(3)]
    for c in range(3):
        p = max(range(c, 3), key=lambda r: abs(m[r][c]))
        if abs(m[p][c]) < 1e-12:
            return None
        m[c], m[p] = m[p], m[c]
        for r in range(3):
            if r != c:
                f = m[r][c] / m[c][c]
                m[r] = [m[r][k] - f * m[c][k] for k in range(4)]
    return tuple(m[r][3] / m[r][r] for r in range(3))


# --------------------------------------------------------------------------- pose

def lower_index(bones):
    return {b.lower(): i for i, b in enumerate(bones)}


def compose(bones, parents, frame, weapon_parent=WEAPON_PARENT):
    """Per bone (R, p): the clip's transforms composed down the hierarchy, with `weapon` re-parented."""
    index = lower_index(bones)
    parents = list(parents)
    if weapon_parent and "weapon" in index and weapon_parent in index:
        parents[index["weapon"]] = index[weapon_parent]
    out = [None] * len(bones)

    def solve(i, depth=0):
        if out[i] is not None:
            return out[i]
        r, p = clip_rotation(frame[i]["q"]), tuple(frame[i]["p"])
        parent = parents[i]
        if parent is None or depth > len(bones):
            out[i] = (r, p)
        else:
            pr, pp = solve(parent, depth + 1)
            out[i] = (mat_mul(pr, r), add(mat_vec(pr, p), pp))
        return out[i]

    for i in range(len(bones)):
        solve(i)
    return {name.lower(): out[i] for i, name in enumerate(bones)}


def hands_in_weapon_space(bones, parents, frame, rest=REST_JOINTS, weapon_parent=WEAPON_PARENT):
    """(left, right) wrists in the weapon's rest frame: the rest-space points the weapon transform
    carries onto each posed wrist. Only their difference is used; the offset is the proxy's placement."""
    posed = compose(bones, parents, frame, weapon_parent)
    missing = [b for b in ("weapon", "lefthand", "righthand") if b not in posed]
    if missing:
        raise ValueError("pose has no bone(s): " + ", ".join(missing))
    wr, wp = posed["weapon"]
    inv = transpose(wr)
    hands = []
    for h in ("lefthand", "righthand"):
        r, p = posed[h]
        joint = add(mat_vec(r, rest[h]), p)
        hands.append(mat_vec(inv, sub(joint, wp)))
    return tuple(hands)


def solve_rest_joints(clips, names=("lefthand", "righthand")):
    """Each bone's rest joint as the fixed point of its own transform in every frame: (I - R) x = p,
    least squares over all frames. Returns {name: (x, rms residual m)}."""
    out = {}
    for name in names:
        ata = [[0.0] * 3 for _ in range(3)]
        aty = [0.0] * 3
        rows = []
        for bones, frames in clips:
            index = lower_index(bones)
            if name not in index:
                continue
            for frame in frames:
                entry = frame[index[name]]
                r = clip_rotation(entry["q"])
                a = tuple(tuple((1.0 if i == j else 0.0) - r[i][j] for j in range(3)) for i in range(3))
                y = tuple(entry["p"])
                rows.append((a, y))
                for i in range(3):
                    for j in range(3):
                        ata[i][j] += sum(a[k][i] * a[k][j] for k in range(3))
                    aty[i] += sum(a[k][i] * y[k] for k in range(3))
        x = solve3(ata, aty) if rows else None
        if x is None:
            continue
        err = [mat_vec(a, x)[k] - y[k] for a, y in rows for k in range(3)]
        out[name] = (x, math.sqrt(sum(e * e for e in err) / len(err)))
    return out


# --------------------------------------------------------------------------- the weapon

def rest_to_mlod(trigger, muzzle):
    """The rotation from soldier rest space (x left, -y forward, z up) to this MLOD's space, where the
    barrel runs along the horizontal model axis nearest trigger->muzzle and z is up."""
    bore = sub(muzzle, trigger)
    axis = max((0, 1), key=lambda i: abs(bore[i]))
    forward = tuple((1.0 if bore[axis] > 0 else -1.0) if i == axis else 0.0 for i in range(3))
    up = (0.0, 0.0, 1.0)
    right = cross(forward, up)
    # rest: left = +x, forward = -y, up = +z  ->  columns are the images of rest x, y, z
    cols = (tuple(-c for c in right), tuple(-c for c in forward), up)
    return tuple(tuple(cols[c][r] for c in range(3)) for r in range(3))


def distance_to_line(point, a, b):
    ab = sub(b, a)
    length = norm(ab) or 1.0
    t = dot(sub(point, a), ab) / (length * length)
    closest = tuple(a[i] + ab[i] * t for i in range(3))
    return norm(sub(point, closest)), t


def place_hands(left, right, trigger, muzzle):
    """Right wrist on the trigger, left wrist where the pose puts it relative to the right. Returns
    (left_mlod, right_mlod, report); the points are None when the left wrist is not on the barrel."""
    m = rest_to_mlod(trigger, muzzle)
    right_m = tuple(trigger)
    left_m = add(right_m, mat_vec(m, sub(left, right)))
    bore, along = distance_to_line(left_m, trigger, muzzle)
    barrel = norm(sub(muzzle, trigger))
    forward = along * barrel
    report = {"fit": bore <= LEFT_BORE_MAX_M and forward >= LEFT_FORWARD_MIN_M and along <= LEFT_ALONG_MAX,
              "rest_to_mlod": [list(r) for r in m], "hand_span_m": round(norm(sub(left, right)), 4),
              "barrel_m": round(barrel, 4), "left_hand_to_bore_m": round(bore, 4),
              "left_hand_forward_m": round(forward, 4), "left_hand_along_barrel": round(along, 3),
              "right_hand": "anchored at trigger_axis"}
    if not report["fit"]:
        report["reason"] = "left wrist {:.3f} m from the bore, {:.3f} m ahead of the trigger ({:.0%} of the barrel)".format(
            bore, forward, along)
        return None, None, report
    return left_m, right_m, report


# --------------------------------------------------------------------------- files

def load_clip(stem, manifest_path=MANIFEST, roots=None):
    """(bones, parents, first frame) of the decoded clip named <stem> (e.g. EF88_Vg_static). Looks in the
    decoded Animations/ tree, then in the committed evidence (Docs/evidence/w2_grip_clips)."""
    with open(manifest_path, encoding="utf-8") as fh:
        clips = json.load(fh)["clips"]
    entry = None
    for key, value in clips.items():
        name = key.replace("\\", "/").split("/")[-1]
        if name.lower() == (stem + ".json").lower() and value.get("local_anim"):
            entry = value
            break
    if entry:
        for root in roots or ANIM_ROOTS:
            rig_path = os.path.join(root, entry["rig_file"])
            clip_path = os.path.join(root, entry["local_anim"])
            if os.path.exists(rig_path) and os.path.exists(clip_path):
                with open(rig_path, encoding="utf-8") as fh:
                    rig = json.load(fh)
                with open(clip_path, encoding="utf-8") as fh:
                    clip = json.load(fh)
                return rig["bones"], rig["parents"], clip["frames"][0]
    evidence = os.path.join(EVIDENCE, stem + ".json")
    if roots is None and os.path.exists(evidence):
        with open(evidence, encoding="utf-8") as fh:
            d = json.load(fh)
        return d["bones"], d["parents"], d["frame"]
    if not entry:
        raise FileNotFoundError("clip {} is not in {}".format(stem, manifest_path))
    raise FileNotFoundError("decoded clip {} not found under {}".format(entry["local_anim"], roots or ANIM_ROOTS))


def grip_points(stem, trigger, muzzle, manifest_path=MANIFEST, roots=None):
    """
    Left and right wrist positions in the MLOD's (pre-transform) space for weapon pose <stem>, or
    (None, None, report) when the pose does not put the left hand on this weapon's barrel.
    """
    bones, parents, frame = load_clip(stem, manifest_path, roots)
    left, right = hands_in_weapon_space(bones, parents, frame)
    left_m, right_m, report = place_hands(left, right, tuple(trigger), tuple(muzzle))
    report.update({"clip": stem, "weapon_parent": WEAPON_PARENT,
                   "left_minus_right_rest": [round(c, 4) for c in sub(left, right)],
                   "trigger_mlod": [round(c, 4) for c in trigger], "muzzle_mlod": [round(c, 4) for c in muzzle]})
    return left_m, right_m, report


# --------------------------------------------------------------------------- evidence

GRIP_CLIPS = ("EF88_Vg_static", "AUG_GL", "AUG", "ar15_8in_cgrip_static", "hk416_cgrip_static",
              "ar15_10in_cgrip_static", "Minimi_Standard", "hk417_static")


def export(out_dir, stems=GRIP_CLIPS, manifest_path=MANIFEST, roots=None):
    """Copy each grip clip's first frame and its rig (bones, parents) to out_dir, so the pose maths can
    be checked without the git-ignored Animations/ tree. Small JSON, ADFRC (ADR-035)."""
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for stem in stems:
        try:
            bones, parents, frame = load_clip(stem, manifest_path, roots or ANIM_ROOTS)
        except FileNotFoundError as error:
            print("skip", stem, error)
            continue
        path = os.path.join(out_dir, stem + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"clip": stem, "bones": bones, "parents": parents, "frame": frame}, fh)
        written.append(path)
    return written


def evidence_clips(folder=EVIDENCE):
    out = []
    for name in sorted(os.listdir(folder)):
        if name.endswith(".json"):
            with open(os.path.join(folder, name), encoding="utf-8") as fh:
                d = json.load(fh)
            out.append((d["bones"], [d["frame"]]))
    return out


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3 and sys.argv[1] == "--export":
        print("{} clip(s) written".format(len(export(sys.argv[2]))))
    elif len(sys.argv) >= 2 and sys.argv[1] == "--solve-rest":
        for name, (x, rms) in solve_rest_joints(evidence_clips()).items():
            print("{:10s} rest {} rms {:.5f} m".format(name, [round(c, 4) for c in x], rms))
    else:
        print("usage: python Tools/Common/adfrc_grip.py --export Docs/evidence/w2_grip_clips | --solve-rest")
