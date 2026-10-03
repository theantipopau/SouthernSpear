# Southern Spear - first-person arms from a Fab FPS animation pack (ADR-021; producer 2026-09-28:
# "arms view model"). Keeps the pack's arms mesh, skeleton and clips; drops its real-weapon model
# (ADR-016: our A-series weapon rides on the pack's weapon bone in game instead).
#
#   blender -b --factory-startup -P Tools/Blender/fp_arms.py -- <pack.fbx> <prefix> <out.fbx>
#   e.g. ... -- ".../M4 Animations/M4.fbx" FP_Rifle Build/fp_arms/SK_FP_Arms_Rifle.fbx
#
# Clips are renamed "<prefix>_<Clip>" (Draw, Fire, Holster, Idle, Reload, Reload_Empty). Writes
# <out>.json with the bone list, clip lengths and the weapon bone's rest transform.

import json
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, PREFIX, OUT = argv[0], argv[1], argv[2]
KEEP_MESH = "Hand_Mesh"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC, automatic_bone_orientation=False)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")

for o in list(bpy.data.objects):
    if o.type == "MESH" and o.name != KEEP_MESH:
        bpy.data.objects.remove(o, do_unlink=True)

clips = {}
for act in list(bpy.data.actions):
    parts = act.name.split("|")
    if parts[0] != arm.name or len(parts) < 2:
        bpy.data.actions.remove(act)  # per-object weapon-part actions
        continue
    clip = parts[1].replace("ReloadEmpty", "Reload_Empty")
    act.name = "{}_{}".format(PREFIX, clip)
    act.use_fake_user = True
    clips[act.name] = [act.frame_range[0], act.frame_range[1]]

weapon_bone = next((b.name for b in arm.data.bones if b.name == "Main_j"), None)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
bpy.ops.export_scene.fbx(
    filepath=OUT, use_selection=False, object_types={"ARMATURE", "MESH"}, add_leaf_bones=False,
    bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False,
    bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0, use_armature_deform_only=False)

mesh = bpy.data.objects[KEEP_MESH]
GLOVE_REPORT = {}
if os.environ.get("SS_FP_GLOVES") == "1":
    # Session 095: the glove asset's hands instead of the pack's bare ones (Tools/Blender/fp_arms_gloves.py).
    # Re-exports over OUT so the clips and the mesh stay one file.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fp_arms_gloves
    mesh = fp_arms_gloves.graft(arm, mesh, GLOVE_REPORT)
    bpy.ops.export_scene.fbx(
        filepath=OUT, use_selection=False, object_types={"ARMATURE", "MESH"}, add_leaf_bones=False,
        bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False,
        bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0, use_armature_deform_only=False)

# UV region mask source for Tools/Textures/make_fp_arms_texture.py: each polygon's UVs, labelled by its
# dominant bone ("sleeve": forearm / upper arm, "glove": hand and fingers). The pack's UV layout does not
# split the regions along one axis, so the texture needs the polygons.
groups = {g.index: g.name for g in mesh.vertex_groups}
uvs = mesh.data.uv_layers.active.data
polys = []
for poly in mesh.data.polygons:
    weight = {}
    for vi in poly.vertices:
        for g in mesh.data.vertices[vi].groups:
            weight[groups[g.group]] = weight.get(groups[g.group], 0.0) + g.weight
    top = max(weight, key=weight.get) if weight else ""
    total = sum(weight.values()) or 1.0
    forearm = sum(v for k, v in weight.items() if "ForeArm" in k) / total
    # Wrist polygons lean on the hand bone: keep them sleeve unless the forearm share is small, so the cuff
    # sits at the wrist rather than halfway up the forearm (pistol pose, in-game check).
    label = "glove" if ("Hand" in top and forearm < 0.08) else "sleeve"
    polys.append([label, [[round(uvs[li].uv[0], 5), round(uvs[li].uv[1], 5)] for li in poly.loop_indices]])
with open(OUT + ".uvmask.json", "w") as fh:
    json.dump(polys, fh)
report = {"source": SRC, "out": OUT, "clips": clips, "bones": [b.name for b in arm.data.bones],
          "weapon_bone": weapon_bone, "mesh_vertices": len(mesh.data.vertices),
          "mesh_dimensions": list(mesh.dimensions), "armature_scale": list(arm.scale), "gloves": GLOVE_REPORT}
with open(OUT + ".json", "w") as fh:
    json.dump(report, fh, indent=1)
print("[fp_arms] wrote", OUT, len(clips), "clips")
