"""MAF weapon display mesh from a skinned Fab weapon: static, in the A-series convention.

    blender -b --factory-startup -P Tools/Blender/maf_weapon.py -- <src.fbx> <NAME> [<trigger bone>] [<magazine.fbx>]

MAF weapons are cosmetic counterparts (ADR-016, W-101/W-102): the same gameplay definitions, a different mesh
shown to viewers for whom that soldier is on the other side. Input: an FBX exported from the pack's skeletal
mesh (Tools/Unreal/export_maf_source.py). Output: Art/Weapons/MAF/SM_<NAME>.fbx, the convention every held
weapon uses (Tools/Blender/adfrc_weapon.py): muzzle to +X, up +Z, origin at the trigger bone, SOCKET_Muzzle
at the muzzle, metres. The skeleton is dropped (the rest pose is the display pose).
"""
import json
import math
import os
import sys

import bpy
import mathutils

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
argv = sys.argv[sys.argv.index("--") + 1:]
SRC, NAME = argv[0], argv[1]
TRIGGER = argv[2] if len(argv) > 2 else "Trigger"
MAGAZINE = argv[3] if len(argv) > 3 else None  # the pack's separate magazine mesh, seated at the Magazine bone
OUT = os.path.join(ROOT, "Art", "Weapons", "MAF")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
trigger = None
magazine = None
if arm:
    for b in arm.data.bones:
        if b.name == TRIGGER:
            trigger = arm.matrix_world @ b.head_local
        if b.name.lower().startswith("magazine") and not b.name.lower().endswith("_end"):
            magazine = arm.matrix_world @ b.head_local
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
for o in meshes:
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    o.parent = None
    o.matrix_world = o.matrix_world.copy()
for o in list(bpy.data.objects):
    if o.type != "MESH":
        bpy.data.objects.remove(o, do_unlink=True)
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.active_object
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for vg in list(obj.vertex_groups):
    obj.vertex_groups.remove(vg)

# Long axis and muzzle end: the magazine sits ahead of the trigger on every rifle / machine gun the MAF carry,
# so the end on the magazine's side of the trigger is the muzzle (fallback: the thinner end).
vs = [v.co for v in obj.data.vertices]
dims = [max(v[i] for v in vs) - min(v[i] for v in vs) for i in range(3)]
axis = max(range(2), key=lambda i: dims[i])
if trigger is not None and magazine is not None:
    sign = 1.0 if magazine[axis] > trigger[axis] else -1.0
else:
    hi, lo = max(v[axis] for v in vs), min(v[axis] for v in vs)
    band = lambda edge: [v for v in vs if abs(v[axis] - edge) < dims[axis] * 0.1]
    height = lambda b: (max(v.z for v in b) - min(v.z for v in b)) if b else 0
    sign = 1.0 if height(band(hi)) < height(band(lo)) else -1.0
# Rotate so the muzzle direction becomes +X.
direction = mathutils.Vector((0, 0, 0))
direction[axis] = sign
rot = direction.to_track_quat("X", "Z").to_matrix().to_4x4().inverted()
origin = trigger if trigger is not None else mathutils.Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2, 0, 0))
obj.data.transform(rot @ mathutils.Matrix.Translation(-origin))

# The pack's magazine is a separate mesh in its own frame: seat it by geometry in the final weapon frame -
# upright, its curve sweeping forward (+X), the top of it in the magwell at the Magazine bone.
if MAGAZINE and magazine is not None:
    well = rot @ (magazine - origin)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=MAGAZINE)
    parts = []
    for o in [o for o in bpy.data.objects if o not in before]:
        if o.type != "MESH" or o.name.startswith("UCX_"):
            bpy.data.objects.remove(o, do_unlink=True)
        else:
            parts.append(o)
    if parts:
        bpy.ops.object.select_all(action="DESELECT")
        for o in parts:
            o.select_set(True)
        bpy.context.view_layer.objects.active = parts[0]
        if len(parts) > 1:
            bpy.ops.object.join()
        mag = bpy.context.active_object
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        mv = [v.co for v in mag.data.vertices]
        mdims = [max(v[i] for v in mv) - min(v[i] for v in mv) for i in range(3)]
        tall = max(range(3), key=lambda i: mdims[i])
        if tall == 1:
            mag.data.transform(mathutils.Matrix.Rotation(math.radians(90), 4, "X"))
        elif tall == 0:
            mag.data.transform(mathutils.Matrix.Rotation(math.radians(-90), 4, "Y"))
        mv = [v.co for v in mag.data.vertices]
        flat = 1 if (max(v.y for v in mv) - min(v.y for v in mv)) > (max(v.x for v in mv) - min(v.x for v in mv)) else 0
        if flat == 1:  # the curve runs along Y: turn it onto X
            mag.data.transform(mathutils.Matrix.Rotation(math.radians(90), 4, "Z"))
            mv = [v.co for v in mag.data.vertices]
        lo_z, hi_z = min(v.z for v in mv), max(v.z for v in mv)
        bottom = [v for v in mv if v.z < lo_z + 0.03]
        top = [v for v in mv if v.z > hi_z - 0.03]
        if sum(v.x for v in bottom) / len(bottom) < sum(v.x for v in top) / len(top):
            mag.data.transform(mathutils.Matrix.Rotation(math.radians(180), 4, "Z"))
            mv = [v.co for v in mag.data.vertices]
            top = [v for v in mv if v.z > max(v.z for v in mv) - 0.03]
        top_centre = mathutils.Vector((sum(v.x for v in top) / len(top), sum(v.y for v in top) / len(top), max(v.z for v in mv)))
        # Seat correction measured from the side render (Tools/Blender/render_weapon_side.py): the bone point is
        # below and ahead of the magwell by these amounts on the AKS-74U pack (env override for other packs).
        seat = mathutils.Vector((float(os.environ.get("SS_MAG_SEAT_X", "-0.049")), 0.0, float(os.environ.get("SS_MAG_SEAT_Z", "0.055"))))
        mag.data.transform(mathutils.Matrix.Translation(mathutils.Vector((well.x, 0.0, well.z)) - top_centre + seat))
        bpy.ops.object.select_all(action="DESELECT")
        mag.select_set(True)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.join()
        obj = bpy.context.active_object

front = max(v.co.x for v in obj.data.vertices)
tip = [v.co for v in obj.data.vertices if v.co.x > front - 0.01]
muzzle = mathutils.Vector((front, sum(v.y for v in tip) / len(tip), sum(v.z for v in tip) / len(tip)))
obj.name = obj.data.name = "SM_" + NAME
sock = bpy.data.objects.new("SOCKET_Muzzle", None)
sock.location = muzzle
bpy.context.scene.collection.objects.link(sock)
sock.parent = obj

fbx = os.path.join(OUT, "SM_" + NAME + ".fbx")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                         axis_forward="-Y", axis_up="Z", mesh_smooth_type="FACE", add_leaf_bones=False)
report = {"source": SRC, "fbx": fbx, "dimensions_m": list(obj.dimensions), "muzzle_m": list(muzzle),
          "origin": "trigger bone" if trigger is not None else "bbox", "materials": [m.name for m in obj.data.materials]}
with open(os.path.join(OUT, "SM_" + NAME + ".json"), "w") as fh:
    json.dump(report, fh, indent=1)
print("[MAF weapon]", json.dumps(report))
