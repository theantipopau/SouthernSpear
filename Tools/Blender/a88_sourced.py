# Southern Spear - A88 from the producer-supplied royalty-free model (Art/Weapons/A88/New).
#
# The download's OBJ carries no material assignments and its MTL names do not
# match the PNGs, so slots are assigned here by object name:
#   *Material_1* (body, magazine, trigger, straps)  -> slot "TexBody"      (a22af57e... atlas)
#   *Material_2* (scope, lens)                      -> slot "TexOptic"     (8e6ddb10... atlas)
#   *Material_3* (foregrip, laser, suppressor)      -> slot "TexFurniture" (8e6ddb10... atlas)
# b107502a... is a black/white mask, not a colour map; unused. Pairings were
# chosen from rendered permutations (Session 022).
#
# Conventions (ss_weapon_kit): +X muzzle, +Z up, metres, origin at the top of
# the pistol grip, SOCKET_Muzzle empty. The source is in centimetres, muzzle -X.
#
# Run: blender --background --factory-startup --python Tools/Blender/a88_sourced.py
# Out: Art/Weapons/A88/New/SM_A88_Sourced.fbx, Build/sm_a88_sourced_report.json

import json
import math
import os

import bpy
import mathutils

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "Art", "Weapons", "A88", "New")
OUT = os.path.join(SRC, "SM_A88_Sourced.fbx")
SLOTS = {"Material_1": "TexBody", "Material_2": "TexOptic", "Material_3": "TexFurniture"}
GRIP_TOP_CM = (1.0, 2.0)  # source X, Z of the grip top (before the 180 degree turn)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=os.path.join(SRC, "model.obj"))
parts = [o for o in bpy.context.scene.objects if o.type == "MESH"]
mats = {name: bpy.data.materials.new(name) for name in SLOTS.values()}
for o in parts:
    key = next(k for k in SLOTS if k in o.name)
    o.data.materials.clear()
    o.data.materials.append(mats[SLOTS[key]])

bpy.ops.object.select_all(action="DESELECT")
for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
obj = bpy.context.active_object
obj.name = obj.data.name = "SM_A88"

# Keep the importer's Y-up to Z-up rotation, then grip top to origin, muzzle
# to +X, centimetres to metres.
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
obj.location = (-GRIP_TOP_CM[0], 0.0, -GRIP_TOP_CM[1])
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
obj.rotation_euler = (0.0, 0.0, math.pi)
obj.scale = (0.01, 0.01, 0.01)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Muzzle socket at the front of the barrel line (highest-X vertices).
xs = [v.co.x for v in obj.data.vertices]
front = max(xs)
tip = [v.co for v in obj.data.vertices if v.co.x > front - 0.01]
muzzle = mathutils.Vector((front, sum(v.y for v in tip) / len(tip), sum(v.z for v in tip) / len(tip)))
sock = bpy.data.objects.new("SOCKET_Muzzle", None)
sock.location = muzzle
bpy.context.collection.objects.link(sock)
sock.parent = obj

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                         axis_forward="-Y", axis_up="Z", mesh_smooth_type="FACE", add_leaf_bones=False)
dims = list(obj.dimensions)
tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
report = {"ok": 0.7 < dims[0] < 0.9, "dimensions_m": dims, "triangles": tris, "muzzle_m": list(muzzle),
          "slots": [m.name for m in obj.data.materials], "fbx": OUT}
with open(os.path.join(ROOT, "Build", "sm_a88_sourced_report.json"), "w") as fh:
    json.dump(report, fh, indent=1)
print("[A88 sourced]", report)
