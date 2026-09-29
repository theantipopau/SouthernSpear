# Southern Spear - ADFRC weapon to game mesh (L-0021; ADR-016 naming).
#
# Input: an Arma MLOD converted to .blend (Art/ADFRC_BLEND/<addon>/<model>_MLOD.blend).
# Output: Art/Weapons/<NAME>/ADFRC/SM_<NAME>.fbx and a texture manifest for
# Tools/Unreal/setup_weapons.py.
#
# - Keeps LOD0 of each visual part: in the view_R0 collection each part appears
#   once per LOD (per material); the first occurrence is the highest detail.
# - Drops identification decals (tag, ruid, patch, flag, logo): no real
#   insignia or unit markings (ADR-016).
# - Material slots are named after their colour texture stem (e.g.
#   adfrc_ef88_co); the manifest maps each slot to the extracted PNG
#   (Art/ADFRC/Textures/**, colour _co and normal _nohq).
# - Orientation from the Arma memory LOD: muzzle_pos to +X, origin at
#   trigger_axis (the gripping hand), SOCKET_Muzzle at muzzle_pos. Without
#   memory points: thinner end to +X, bounding-box centre. Metres.
# - Optional third argument: an optic FBX/blend merged between the iron sights
#   at eye height (or on the bullpup optic proxy when there are no iron sights).
# - SS_GRIP_CLIP=<handAnim pose> (W2): SOCKET_LeftHandGrip / SOCKET_RightHandGrip where the ADFRC
#   pose puts the wrists on this weapon (Tools/Common/adfrc_grip.py, calibrated on trigger_axis and
#   muzzle_pos). No sockets, and the reason in the manifest, when the pose does not fit.
# - SS_GRIP_HOLD=<json> (W2b): the hold the left hand takes on this weapon, as documentation only.
#   The handAnim poses are not a target for this: their finger rest joints disagree by ~50 deg, and
#   the FBX round trip mangles a socket's rotation, so the game builds the hold itself at run time
#   from the socket positions (FSSHandIK::BuildGripHold) and reads its per-weapon angle from
#   Config/DefaultGame.ini. Nothing is written to the socket; the profile and the resolved axes are
#   recorded in the manifest under "hold" so the export can be checked against them.
# - W3: SOCKET_Eject at the ejection port (nabojnicestart) and SOCKET_EjectEnd where the case is thrown
#   (nabojniceend); manifest "eject".
#
# Run: blender --background --factory-startup --python Tools/Blender/adfrc_weapon.py -- <src.blend> <NAME> [optic.fbx]

import json
import math
import os
import re
import sys

import bpy
import mathutils

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEXTURES = os.path.join(ROOT, "Art", "ADFRC", "Textures")
DROP = re.compile(r"(tag|ruid|patch|flag|logo|insignia)", re.I)

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, NAME = argv[0], argv[1]
OPTIC = os.path.abspath(argv[2]) if len(argv) > 2 else None  # optional optic FBX merged on the rail
OUT_DIR = os.path.join(ROOT, "Art", "Weapons", NAME, "ADFRC")
OPTIC_AHEAD_OF_EYE = float(os.environ.get("SS_OPTIC_AHEAD", "0.10"))  # m, rear of the optic ahead of the eye point
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(SRC))

# PNG index by lower-case stem.
index = {}
for dirpath, _, files in os.walk(TEXTURES):
    for f in files:
        if f.lower().endswith(".png"):
            index.setdefault(os.path.splitext(f)[0].lower(), os.path.join(dirpath, f))


def texture_stem(material_name):
    # "P3D: adfrc_ef88_co.paa :: adfrc_ef88_poly.rvmat" -> "adfrc_ef88_co"
    m = re.search(r"([\w\-]+)\.paa", material_name or "", re.I)
    return m.group(1).lower() if m else None


# Arma memory LOD points (named vertex groups): muzzle, trigger, sight eye.
memory = {}
mem = bpy.data.objects.get("Memory")
if mem:
    for g in mem.vertex_groups:
        pts = [v.co.copy() for v in mem.data.vertices if any(e.group == g.index for e in v.groups)]
        if pts:
            memory[g.name] = sum(pts, mathutils.Vector()) / len(pts)

view = bpy.data.collections.get("view_R0") or bpy.data.collections.get("LODs")
candidates = [o for o in (view.all_objects if view else bpy.data.objects) if o.type == "MESH"]
seen, keep, dropped = set(), [], []
for o in sorted(candidates, key=lambda o: o.name):
    base = re.sub(r"\.\d+$", "", o.name)
    mat = o.data.materials[0].name if o.data.materials and o.data.materials[0] else ""
    key = (base, mat)
    if key in seen:
        continue
    seen.add(key)
    if DROP.search(base) or DROP.search(mat):
        dropped.append(base)
        continue
    if not texture_stem(mat):
        dropped.append(base + " (no texture)")
        continue
    keep.append(o)

for o in bpy.data.objects:
    o.select_set(False)
parts = []
for o in keep:
    c = o.copy()
    c.data = o.data.copy()
    bpy.context.scene.collection.objects.link(c)
    parts.append(c)
for o in list(bpy.data.objects):
    if o not in parts:
        bpy.data.objects.remove(o, do_unlink=True)
for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
obj = bpy.context.active_object
obj.name = obj.data.name = "SM_" + NAME
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Slots named after their colour texture.
manifest = {}
for slot in obj.material_slots:
    stem = texture_stem(slot.material.name if slot.material else "")
    if not stem:
        continue
    mat = bpy.data.materials.get(stem) or bpy.data.materials.new(stem)
    slot.material = mat
    colour = index.get(stem)
    normal = index.get(re.sub(r"_(co|ca)$", "_nohq", stem))
    manifest[stem] = {"colour": colour, "normal": normal}

# Placement. Points are kept in step with the mesh through every transform.
points = dict(memory)

# W2: the hands, from the weapon's own handAnim pose, in this MLOD's space (before any transform below).
grip_report = None
GRIP_CLIP = os.environ.get("SS_GRIP_CLIP")
# W2b: SS_GRIP_HOLD names the hold profile the left hand takes on this weapon, as JSON so the choice
# and any angle overrides stay data (GRIP_HOLDS in build_adfrc_weapons.py), not a branch here.
GRIP_HOLD = os.environ.get("SS_GRIP_HOLD")
if GRIP_CLIP or GRIP_HOLD:
    sys.path.insert(0, os.path.join(ROOT, "Tools", "Common"))
    import adfrc_grip
if GRIP_CLIP:
    if "trigger_axis" in memory and "muzzle_pos" in memory:
        try:
            left_hand, right_hand, grip_report = adfrc_grip.grip_points(
                GRIP_CLIP, tuple(memory["trigger_axis"]), tuple(memory["muzzle_pos"]))
            if left_hand is not None:
                points["grip_left"] = mathutils.Vector(left_hand)
                points["grip_right"] = mathutils.Vector(right_hand)
        except (OSError, ValueError, KeyError) as error:
            grip_report = {"clip": GRIP_CLIP, "fit": False, "reason": str(error)}
    else:
        grip_report = {"clip": GRIP_CLIP, "fit": False, "reason": "no trigger_axis/muzzle_pos memory points"}
    print("[ADFRC grip]", NAME, json.dumps(grip_report))


def transform(fn):
    for v in obj.data.vertices:
        v.co = fn(v.co)
    for k in points:
        points[k] = fn(points[k])


dims = obj.dimensions
if dims.y > dims.x and dims.y >= dims.z:
    transform(lambda c: mathutils.Vector((c.y, -c.x, c.z)))
length = max(v.co.x for v in obj.data.vertices) - min(v.co.x for v in obj.data.vertices)


def end_height(sign):
    xs = [v.co.x for v in obj.data.vertices]
    lo_x, hi_x = min(xs), max(xs)
    edge = hi_x if sign > 0 else lo_x
    band = [v.co for v in obj.data.vertices if abs(v.co.x - edge) < length * 0.1]
    return (max(v.z for v in band) - min(v.z for v in band)) if band else 0.0


# Muzzle to +X: from the memory point when present, else the thinner end.
if "muzzle_pos" in points and "trigger_axis" in points:
    flip = points["muzzle_pos"].x < points["trigger_axis"].x
else:
    flip = end_height(-1) < end_height(+1)
if flip:
    transform(lambda c: mathutils.Vector((-c.x, -c.y, c.z)))

# Origin at the trigger (the gripping hand), else the bounding-box centre.
if "trigger_axis" in points:
    origin = points["trigger_axis"].copy()
else:
    vs = [v.co for v in obj.data.vertices]
    origin = mathutils.Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2, 0.0,
                               (min(v.z for v in vs) + max(v.z for v in vs)) / 2))
transform(lambda c: c - origin)

if "muzzle_pos" in points:
    muzzle = points["muzzle_pos"].copy()
else:
    front = max(v.co.x for v in obj.data.vertices)
    tip = [v.co for v in obj.data.vertices if v.co.x > front - 0.01]
    muzzle = mathutils.Vector((front, sum(v.y for v in tip) / len(tip), sum(v.z for v in tip) / len(tip)))

# Optional optic on the rail: sight axis at the iron-sight eye height, centred
# between the trigger and the eye point.
optic_report = None
optic_eye = None
if OPTIC and os.path.exists(OPTIC):
    before = set(bpy.data.objects)
    if OPTIC.lower().endswith(".blend"):
        # Arma optic converted with Tools/Blender/p3d_to_blend.py: take the most
        # detailed visual LOD ("Resolution N", lowest N).
        with bpy.data.libraries.load(OPTIC, link=False) as (src, dst):
            lods = sorted((n for n in src.objects if n.startswith("Resolution")),
                          key=lambda n: float(re.sub(r"[^0-9.]", "", n) or 0))
            # Other converts (the C79) keep one object per material per LOD instead: "<material>_R0" is LOD0.
            dst.objects = lods[:1] or [n for n in src.objects if n.endswith("_R0")]
            dst.objects += [n for n in src.objects if n == "Memory"]
        # The optic's own eye point (Arma memory "eye" / "eye1"): the eyepiece end, which must face the stock.
        loaded = [o for o in dst.objects if o]
        memories = [o for o in loaded if o.name.startswith("Memory")]
        for o in memories:
            for g in o.vertex_groups:
                if g.name in ("eye", "eye1"):
                    pts = [v.co.copy() for v in o.data.vertices if any(e.group == g.index for e in v.groups)]
                    if pts:
                        optic_eye = o.matrix_world @ (sum(pts, mathutils.Vector()) / len(pts))
        geometry = [o for o in loaded if o not in memories]
        for o in memories:
            bpy.data.objects.remove(o, do_unlink=True)
        for o in geometry:
            bpy.context.scene.collection.objects.link(o)
    else:
        bpy.ops.import_scene.fbx(filepath=OPTIC)
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if new:
        for o in bpy.data.objects:
            o.select_set(o in new)
        bpy.context.view_layer.objects.active = new[0]
        if len(new) > 1:
            bpy.ops.object.join()
        opt = bpy.context.active_object
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        d = opt.dimensions
        if d.y > d.x and d.y >= d.z:
            for v in opt.data.vertices:
                v.co = mathutils.Vector((v.co.y, -v.co.x, v.co.z))
            if optic_eye is not None:
                optic_eye = mathutils.Vector((optic_eye.y, -optic_eye.x, optic_eye.z))
        # Which way it looks: the objective (front) end of a scope is the wider one. Turning the long axis onto
        # X leaves the direction to chance - every optic came out reversed, the objective bell facing the
        # shooter (producer, Session 047: "scopes on the weapons are wrong way around"). Wider end to +X.
        def end_size(sign):
            xs = [v.co.x for v in opt.data.vertices]
            lo_x, hi_x = min(xs), max(xs)
            cut = (hi_x - lo_x) / 8.0
            band = [v.co for v in opt.data.vertices if (v.co.x > hi_x - cut if sign > 0 else v.co.x < lo_x + cut)]
            return max(max(v.y for v in band) - min(v.y for v in band), max(v.z for v in band) - min(v.z for v in band)) if band else 0.0
        # Prefer the optic's eye point: its end is the eyepiece. Without one, the objective is taken as the wider
        # end (true of the ACOGs, not of the C79, whose eyepiece is the larger).
        o_mid_x = sum(v.co.x for v in opt.data.vertices) / max(len(opt.data.vertices), 1)
        if optic_eye is not None:
            optic_turned = optic_eye.x > o_mid_x
        else:
            optic_turned = end_size(-1) > end_size(+1)
        if optic_turned:
            for v in opt.data.vertices:
                v.co = mathutils.Vector((-v.co.x, -v.co.y, v.co.z))
        ovs = [v.co for v in opt.data.vertices]
        o_lo = mathutils.Vector((min(v.x for v in ovs), min(v.y for v in ovs), min(v.z for v in ovs)))
        o_hi = mathutils.Vector((max(v.x for v in ovs), max(v.y for v in ovs), max(v.z for v in ovs)))
        eye = points.get("eye", mathutils.Vector((-0.15, 0.0, 0.08)))
        # The scope belongs BETWEEN the iron sights, at eye height. The old
        # rule was eye.x / 2 - the midpoint of the trigger (the origin) and the
        # REAR sight - which parked every scope over the buffer tube or the
        # stock, behind the shooter. Prefer the model's own sight points; fall
        # back to the optic proxy (bullpup rail weapons have no iron sights).
        # Where along the rail: a magnified optic sits on the receiver's flat-top just ahead of the rear sight
        # (Session 047: centring it between the iron sights parked ACOGs out over the handguard). Bullpups use
        # their optic proxy; otherwise (the F89) just ahead of the eye point, on the receiver's feed cover rail.
        rear = points.get("rear_sight_axis")
        o_len = o_hi.x - o_lo.x
        if os.environ.get("SS_OPTIC_X"):
            centre_x = float(os.environ["SS_OPTIC_X"])  # a verified placement (build_adfrc_weapons.py)
        elif rear is not None:
            centre_x = rear.x + o_len / 2.0 + 0.02
        elif "op_axis" in points:
            centre_x = points["op_axis"].x
        else:
            centre_x = eye.x + o_len / 2.0 + OPTIC_AHEAD_OF_EYE
        target = mathutils.Vector((centre_x, 0.0, eye.z))  # optic centre on the sight line
        print("[ADFRC optic] rear_sight", tuple(round(c, 3) for c in rear) if rear is not None else None,
              "optic x", round(o_lo.x, 3), round(o_hi.x, 3), "len", round(o_len, 3), "centre_x", round(centre_x, 3),
              "eye", tuple(round(c, 3) for c in optic_eye) if optic_eye is not None else None, "turned", optic_turned)
        shift = target - (o_lo + o_hi) / 2
        for v in opt.data.vertices:
            v.co += shift
        for slot in opt.material_slots:
            stem = texture_stem(slot.material.name if slot.material else "")
            if stem:  # textured Arma optic: keep a slot per texture
                slot.material = bpy.data.materials.get(stem) or bpy.data.materials.new(stem)
                manifest[stem] = {"colour": index.get(stem), "normal": index.get(re.sub(r"_(co|ca)$", "_nohq", stem))}
            else:
                slot.material = bpy.data.materials.get("optic") or bpy.data.materials.new("optic")
        for o in bpy.data.objects:
            o.select_set(o in (obj, opt))
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.join()
        optic_report = {"source": OPTIC, "centre_m": list(target), "size_m": list(o_hi - o_lo),
                        "turned_to_face_muzzle": optic_turned,
                        "direction_from": "optic eye point" if optic_eye is not None else "wider end",
                        # Height of the optical axis (the optic's eye point, moved with it): the Sight socket.
                        "axis_z_m": (optic_eye.z + shift.z) if optic_eye is not None else None,
                        "rule": "ahead of rear sight" if rear is not None else ("optic proxy" if "op_axis" in points else "ahead of eye point")}
        manifest.setdefault("optic", {"colour": None, "normal": None})

sock = bpy.data.objects.new("SOCKET_Muzzle", None)
sock.location = muzzle
bpy.context.scene.collection.objects.link(sock)
sock.parent = obj

# W2: hand IK targets (wrist positions), carried through the same transforms as the mesh. Position only:
# the exporter transposes an empty's rotation on the way out, and a handAnim pose is too uncertain a
# target anyway, so the game builds the hold from the socket positions instead (W2b below is the record
# of what that hold is, for checking the export against).
hold_report = None
hold_spec = json.loads(GRIP_HOLD) if GRIP_HOLD else None
if hold_spec is not None:
    try:
        _, hold_report = adfrc_grip.resolve_hold(
            hold_spec, tuple(points["trigger_axis"]), tuple(points["muzzle_pos"]))
    except ValueError as error:
        hold_report = {"hold": hold_spec, "reason": str(error)}
    print("[ADFRC hold]", NAME, json.dumps(hold_report))

for key, socket_name in (("grip_left", "SOCKET_LeftHandGrip"), ("grip_right", "SOCKET_RightHandGrip")):
    if key in points:
        hand = bpy.data.objects.new(socket_name, None)
        hand.location = points[key]
        bpy.context.scene.collection.objects.link(hand)
        hand.parent = obj
# W3: the ejection port (nabojnicestart) and where the case is thrown to (nabojniceend), as two sockets so
# the throw direction survives the FBX axis conversion; the game takes the direction between them at runtime.
eject_report = None
if "nabojnicestart" in points and "nabojniceend" in points:
    throw = points["nabojniceend"] - points["nabojnicestart"]
    if throw.length > 0.005:
        for key, socket_name in (("nabojnicestart", "SOCKET_Eject"), ("nabojniceend", "SOCKET_EjectEnd")):
            port = bpy.data.objects.new(socket_name, None)
            port.location = points[key]
            bpy.context.scene.collection.objects.link(port)
            port.parent = obj
        eject_report = {"port_m": [round(c, 4) for c in points["nabojnicestart"]],
                        "direction": [round(c, 3) for c in throw.normalized()]}
    else:
        eject_report = {"reason": "nabojnicestart and nabojniceend coincide"}
else:
    eject_report = {"reason": "no nabojnicestart/nabojniceend memory points"}
print("[ADFRC eject]", NAME, json.dumps(eject_report))

if grip_report is not None and "grip_left" in points:
    grip_report["left_m"] = [round(c, 4) for c in points["grip_left"]]
    grip_report["right_m"] = [round(c, 4) for c in points["grip_right"]]

fbx = os.path.join(OUT_DIR, "SM_" + NAME + ".fbx")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                         axis_forward="-Y", axis_up="Z", mesh_smooth_type="FACE", add_leaf_bones=False)
report = {"source": SRC, "fbx": fbx, "dimensions_m": list(obj.dimensions),
          "triangles": sum(len(p.vertices) - 2 for p in obj.data.polygons), "parts": len(keep),
          "dropped": sorted(set(dropped)), "textures": manifest, "muzzle_m": list(muzzle),
          "memory_points": sorted(memory), "origin": "trigger_axis" if "trigger_axis" in memory else "bbox centre",
          "optic": optic_report, "grip": grip_report, "hold": hold_report, "eject": eject_report}
with open(os.path.join(OUT_DIR, "manifest.json"), "w") as fh:
    json.dump(report, fh, indent=1)
print("[ADFRC weapon]", NAME, json.dumps({k: report[k] for k in ("dimensions_m", "triangles", "parts", "dropped")}))
