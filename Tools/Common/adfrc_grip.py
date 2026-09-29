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
EVIDENCE_FOLDERS = (EVIDENCE, os.path.join(ROOT, "Docs", "evidence", "w5_reload_clips"))
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


def unit(a):
    """`a` scaled to length 1; the zero vector is returned unchanged."""
    n = norm(a)
    return tuple(c / n for c in a) if n > 1e-12 else tuple(a)


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


# --------------------------------------------------------------------------- the hold (W2b)

# Where the left hand goes is a *position* the handAnim poses measured well; how the hand sits on the
# grip is not. The rest joints of one pose disagree with each other by ~50 deg between the finger
# estimates, so they are not a target to copy (Session 073). The hold is authored instead, from the
# weapon's own axes - the same basis adfrc_reload.weapon_axes uses:
#
#     forward  trigger -> muzzle
#     up       the model's up
#     right    forward x up
#
# The hand's basis is the SAME for every weapon:
#
#     +X  the palm normal, out of the palm
#     +Y  the finger direction
#     +Z  the back-of-hand axis
#
# +Z is not the thumb: a LEFT hand has palm = thumb x finger, so palm x finger = -thumb, and the hand's
# own (palm, finger, thumb) triad is left-handed and cannot be a rotation. The earlier version of this
# file asserted palm x finger = thumb, which is a RIGHT hand's relation; it authored a mirrored fist
# that matched its own target to 0.0 deg and rendered upside down on the tube. Because the convention
# never changes, the one HandRotationOffset solved from SK_FP_Arms_Rifle's own finger bones fits every
# weapon: it is the arms' anatomy in the hold's own frame, and the hold carries the per-weapon part.
#
# A hold axis is either a unit (forward, right, up) triple, or ("tilt", base, towards, degrees) -
# `base` rotated towards `towards`, for the angles a hold is authored with. Per-weapon choices and
# angle overrides are data: GRIP_HOLDS in Tools/build_adfrc_weapons.py, passed as SS_GRIP_HOLD.
#
# palm and finger are trusted over the thumb, because those two are what lay the hand on the grip; a
# thumb that disagrees is the authored deviation and is reported, not silently averaged away.
HOLD_PROFILES = {
    # Under a plain handguard: the palm faces up into the tube, the fingers wrap over the far
    # (shooter's right) side, the thumb lies along the handguard pointing at the muzzle. The palm
    # is +up tilted 30 deg towards +right, not square: the hand sits under the LEFT of the tube.
    # Tilted, the triad stays exactly self-consistent (palm x finger = -thumb, 0 deg), because the
    # tilt carries the finger with it once it is projected square.
    "plain_handguard": {
        "palm": ("tilt", (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), 30.0),
        # -right, not +right: the fingers wrap over the tube from the shooter's LEFT, and it is the
        # left hand's relation (finger x palm = thumb) that puts the derived thumb back on +forward.
        # With +right here the triad came out a right hand's and the thumb pointed at the shooter.
        "finger": (0.0, -1.0, 0.0),   # -right, wrapping over the tube
        "thumb": (1.0, 0.0, 0.0),     # +forward, along the handguard
    },
    # A vertical foregrip: the palm faces in from the shooter's left onto the grip, the fingers
    # wrap down its front, the thumb lies up the grip. The 30 deg forward tilt is the cocked wrist
    # of a foregrip hold; it is a deliberate authored deviation, so the derived thumb sits 30 deg
    # off the one written below.
    "vertical_grip": {
        "palm": (0.0, 1.0, 0.0),      # +right
        "finger": ("tilt", (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0), 30.0),
        "thumb": (1.0, 0.0, 0.0),     # +forward
    },
}

# The arms' HandRotationOffset is solved against the socket's axes, so a weapon that carries no hold
# must not be given one: adfrc_weapon.py reports the reason instead of a bare socket.
NO_HOLD = "no hold authored (GRIP_HOLDS has no row for this weapon)"


def hold_axis(spec, basis):
    """One hold axis as a unit vector in world space. `basis` is (forward, right, up).

    A spec is either a (forward, right, up) triple, or ("tilt", base, towards, degrees): `base`
    rotated towards `towards` by that many degrees, so a hold carries its own angles as data.
    """
    if isinstance(spec, tuple) and spec and spec[0] == "tilt":
        _, base, towards, degrees = spec
        a = math.radians(degrees)
        axis = tuple(unit(base)[i] * math.cos(a) + unit(towards)[i] * math.sin(a) for i in range(3))
    else:
        axis = tuple(spec)
    # axis is in (forward, right, up): the world vector is the weighted sum of those three axes.
    return unit(tuple(sum(axis[i] * basis[i][j] for i in range(3)) for j in range(3)))


def hold_frame_rotation(profile, basis):
    """(rotation, report) for a hold profile. The rotation's columns are the hand basis
    (+X palm, +Y finger, +Z back-of-hand) in world space, matching the game's
    FRotationMatrix::MakeFromXY(Palm, Finger); the report carries the hand's own anatomical triad,
    whose thumb is finger x palm, and the authored thumb's disagreement with it, which is 0 for a
    self-consistent hold."""
    palm = hold_axis(profile["palm"], basis)
    finger = hold_axis(profile["finger"], basis)
    thumb = hold_axis(profile["thumb"], basis)
    x_axis = unit(palm)
    y_axis = unit(sub(finger, tuple(x_axis[i] * dot(x_axis, finger) for i in range(3))))
    if norm(y_axis) < 1e-6:                      # the hold folded the finger onto the palm normal
        raise ValueError("hold profile: the finger direction is parallel to the palm normal")
    z_axis = cross(x_axis, y_axis)               # palm x finger: -thumb, on a left hand
    thumb_derived = cross(y_axis, x_axis)        # finger x palm: the left hand's thumb
    rotation = tuple(tuple((x_axis, y_axis, z_axis)[c][r] for c in range(3)) for r in range(3))
    report = {"palm": [round(c, 4) for c in x_axis], "finger": [round(c, 4) for c in y_axis],
              "back_of_hand": [round(c, 4) for c in z_axis],
              "thumb_derived": [round(c, 4) for c in thumb_derived],
              "thumb_authored": [round(c, 4) for c in thumb],
              "anatomical_triad_det": round(dot(x_axis, cross(y_axis, thumb_derived)), 4),
              "thumb_deviation_deg": round(math.degrees(math.acos(
                  max(-1.0, min(1.0, dot(thumb_derived, thumb))))), 2)}
    return rotation, report


def resolve_hold(spec, trigger, muzzle):
    """(rotation, report) for a per-weapon hold spec - a profile name, optionally with per-axis
    overrides - in this weapon's own axes. None when the weapon has no hold."""
    if not spec:
        return None, {"hold": None, "reason": NO_HOLD}
    spec = {"profile": spec} if isinstance(spec, str) else dict(spec)
    name = spec.get("profile")
    if name not in HOLD_PROFILES:
        raise ValueError("unknown hold profile {!r}; known: {}".format(name, sorted(HOLD_PROFILES)))
    profile = dict(HOLD_PROFILES[name])
    for axis in ("palm", "finger", "thumb"):
        if axis in spec:
            profile[axis] = spec[axis]
    bore = sub(tuple(muzzle), tuple(trigger))
    forward = unit(bore)
    up = unit((0.0, 0.0, 1.0))
    up = unit(sub(up, tuple(forward[i] * dot(forward, up) for i in range(3))))
    basis = (forward, cross(forward, up), up)
    rotation, report = hold_frame_rotation(profile, basis)
    report["hold"] = name
    report["basis"] = {"forward": [round(c, 4) for c in basis[0]],
                       "right": [round(c, 4) for c in basis[1]],
                       "up": [round(c, 4) for c in basis[2]]}
    report["hand_axes"] = {"x": "palm normal", "y": "finger direction", "z": "back of hand (-thumb)"}
    return rotation, report


# --------------------------------------------------------------------------- files

# The decoder (Docs/Sourced/ADFRC/rtm_rigs.py) wrote the file's own quaternion convention through until R-64
# was fixed (schema adfrc-anim-local/1, and the committed evidence, which has no schema). From
# adfrc-anim-local/2 it writes standard quaternions. Everything here works in the stored convention, so a
# standard file is converted back on load; reading a /2 file as /1 would flip every rotation twice.
STANDARD_SCHEMAS = ("adfrc-anim-local/2",)


def to_stored_convention(frames, schema):
    """Frames in the stored convention (clip_rotation reads them), whatever the file's schema."""
    if schema not in STANDARD_SCHEMAS:
        return frames
    return [[{"q": [-e["q"][0], -e["q"][1], e["q"][2], e["q"][3]], "p": e["p"]} for e in frame] for frame in frames]


def load_clip_frames(stem, manifest_path=MANIFEST, roots=None):
    """(bones, parents, every frame) of the decoded clip named <stem> (e.g. GestureReloadAUG), in the stored
    convention. Looks in the decoded Animations/ tree, then in the committed evidence
    (Docs/evidence/w2_grip_clips, Docs/evidence/w5_reload_clips)."""
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
                return rig["bones"], rig["parents"], to_stored_convention(clip["frames"], clip.get("schema", ""))
    if roots is None:
        for folder in EVIDENCE_FOLDERS:
            evidence = os.path.join(folder, stem + ".json")
            if os.path.exists(evidence):
                with open(evidence, encoding="utf-8") as fh:
                    d = json.load(fh)
                frames = d["frames"] if "frames" in d else [d["frame"]]
                return d["bones"], d["parents"], to_stored_convention(frames, d.get("schema", ""))
    if not entry:
        raise FileNotFoundError("clip {} is not in {}".format(stem, manifest_path))
    raise FileNotFoundError("decoded clip {} not found under {}".format(entry["local_anim"], roots or ANIM_ROOTS))


def load_clip(stem, manifest_path=MANIFEST, roots=None):
    """(bones, parents, first frame) of the decoded clip named <stem>, in the stored convention."""
    bones, parents, frames = load_clip_frames(stem, manifest_path, roots)
    return bones, parents, frames[0]


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


RELOAD_CLIPS = ("GestureReloadAUG", "GestureReloadAUGProne", "MPP_Fast_Reload", "MPP_Slow_Reload")


def export_frames(out_dir, stems=RELOAD_CLIPS, manifest_path=MANIFEST, roots=None):
    """Every frame of each clip (stored convention, 5 decimals) to out_dir, for W5's reload paths.
    Small enough to commit: 165 frames x 66 bones is about 0.7 MB."""
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for stem in stems:
        try:
            bones, parents, frames = load_clip_frames(stem, manifest_path, roots or ANIM_ROOTS)
        except FileNotFoundError as error:
            print("skip", stem, error)
            continue
        slim = [[{"q": [round(c, 5) for c in e["q"]], "p": [round(c, 5) for c in e["p"]]} for e in frame] for frame in frames]
        path = os.path.join(out_dir, stem + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"clip": stem, "convention": "stored", "bones": bones, "parents": parents, "frames": slim}, fh)
        written.append(path)
        print("{:24s} {} frames, {} bones".format(stem, len(frames), len(bones)))
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
    if len(sys.argv) >= 3 and sys.argv[1] == "--export-frames":
        print("{} clip(s) written".format(len(export_frames(sys.argv[2]))))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--export":
        print("{} clip(s) written".format(len(export(sys.argv[2]))))
    elif len(sys.argv) >= 2 and sys.argv[1] == "--solve-rest":
        for name, (x, rms) in solve_rest_joints(evidence_clips()).items():
            print("{:10s} rest {} rms {:.5f} m".format(name, [round(c, 4) for c in x], rms))
    else:
        print("usage: python Tools/Common/adfrc_grip.py --export Docs/evidence/w2_grip_clips"
              " | --export-frames Docs/evidence/w5_reload_clips | --solve-rest")
