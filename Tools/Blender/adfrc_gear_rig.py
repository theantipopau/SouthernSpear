# Southern Spear - fit ADFRC (Arma) character gear to the UE5 mannequin skeleton (ADR-025).
#
#   blender --background --python Tools/Blender/adfrc_gear_rig.py -- <mode> <converted.blend> <visual object> <out.fbx>
#
#   mode "skin":   clothing (uniform). The Arma visual LOD carries no bone weights, so:
#                  1. place it on the mannequin (feet on the floor, pelvis over pelvis);
#                  2. pull the Arma limb joints (the Memory LOD's lelbow / lwrist / lfemur / lknee /
#                     lankle ... points) onto the mannequin's joints with a temporary rig, baking the
#                     clothing into the mannequin's rest pose;
#                  3. transfer skin weights from the mannequin's own body mesh (nearest face);
#                  4. export mesh + mannequin armature for import onto Lyra's SK_Mannequin skeleton.
#   mode "rigid:<bone>": headgear or a plate carrier. Placed the same way, every vertex weighted
#                  1.0 to <bone> (e.g. rigid:head, rigid:spine_05).
#
# The converted .blend comes from Tools/Blender/p3d_to_blend.py (Arma 3 Object Builder), which keeps
# the Memory LOD. Manny reference: Art/Characters/ADF/SKM_Manny_ref.fbx, exported from Lyra's
# SKM_Manny (Epic content: git-ignored, re-export with -RenderOffscreen if missing).
#
# Rebuild the 3 ACR kit (then Tools/Unreal/setup_adf_soldier.py and setup_soldiers.py):
#   blender -b -P Tools/Blender/p3d_to_blend.py -- Build/adfrc_converted #       Art/ADFRC_MLOD/adfrc_uniforms/crye_g3_MLOD.p3d Art/ADFRC_MLOD/adfrc_helmets/opscore_MLOD.p3d #       Art/ADFRC_MLOD/adfrc_vests/TBAS_T5_PC_MLOD.p3d
#   G=Build/adfrc_converted/crye_g3_MLOD.blend
#   blender -b -P Tools/Blender/adfrc_gear_rig.py -- skin $G "Resolution 1" Art/Characters/ADF/SK_ADF_Uniform_G3.fbx
#   blender -b -P Tools/Blender/adfrc_gear_rig.py -- rigid:head Build/adfrc_converted/opscore_MLOD.blend "Resolution 1" Art/Characters/ADF/SK_ADF_Helmet_OpsCore.fbx $G
#   blender -b -P Tools/Blender/adfrc_gear_rig.py -- skin Build/adfrc_converted/TBAS_T5_PC_MLOD.blend "Resolution 1" Art/Characters/ADF/SK_ADF_Vest_TBAS.fbx $G

import json
import os
import sys

import bpy
import mathutils

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MANNY = os.path.join(ROOT, "Art", "Characters", "ADF", "SKM_Manny_ref.fbx")
argv = sys.argv[sys.argv.index("--") + 1:]
MODE, SRC, VISUAL, OUT = argv[0], argv[1], argv[2], argv[3]
MEMORY_SRC = argv[4] if len(argv) > 4 else SRC  # rigid items: the character .blend with the Memory LOD
report = {"mode": MODE, "source": SRC, "visual": VISUAL, "out": OUT}

# Arma memory points -> mannequin bones whose HEAD is that joint.
CHAIN = {  # arma point: (manny bone at this joint, arma child point, manny bone at child joint)
    "leftshoulder": ("upperarm_l", "lelbow", "lowerarm_l"),
    "lelbow": ("lowerarm_l", "lwrist", "hand_l"),
    "rightshoulder": ("upperarm_r", "relbow", "lowerarm_r"),
    "relbow": ("lowerarm_r", "rwrist", "hand_r"),
    "lfemur": ("thigh_l", "lknee", "calf_l"),
    "lknee": ("calf_l", "lankle", "foot_l"),
    "rfemur": ("thigh_r", "rknee", "calf_r"),
    "rknee": ("calf_r", "rankle", "foot_r"),
}


def load_objects(path, names):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in names]
    for o in dst.objects:
        bpy.context.scene.collection.objects.link(o)
    return {o.name: o for o in dst.objects}


def memory_points(mem):
    pts = {}
    for g in mem.vertex_groups:
        vs = [mem.matrix_world @ v.co for v in mem.data.vertices if any(x.group == g.index for x in v.groups)]
        if vs:
            pts[g.name] = sum(vs, mathutils.Vector()) / len(vs)
    return pts


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=MANNY)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
body = next(o for o in bpy.data.objects if o.type == "MESH")
bpy.context.view_layer.update()
bone_head = {b.name: arm.matrix_world @ b.head_local for b in arm.data.bones}

if VISUAL.startswith("*"):
    # Every object whose name ends with the suffix (the other converter splits LOD0 by material,
    # e.g. "*_R0"), joined into one mesh.
    with bpy.data.libraries.load(SRC, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.endswith(VISUAL[1:])]
    parts = list(dst.objects)
    for o in parts:
        bpy.context.scene.collection.objects.link(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    item = bpy.context.view_layer.objects.active
    for g in list(item.vertex_groups):
        item.vertex_groups.remove(g)  # Arma selections (no weights in this converter)
else:
    item = load_objects(SRC, [VISUAL])[VISUAL]
mem = load_objects(MEMORY_SRC, ["Memory"]).get("Memory")
if mem is None:
    raise SystemExit("no Memory LOD in " + MEMORY_SRC)
pts = memory_points(mem)

# 0. Drop Arma helper faces (no material) and Bohemia's skin (hl_* heads/bodies: not ADFRC
#    content, and our head and gloves cover them).
drop = {i for i, m in enumerate(item.data.materials) if not m or "no material" in m.name or ":: hl_" in m.name
        or "hl_white" in m.name or "flag" in m.name.lower() or "patch" in m.name.lower()}  # ADR-025: no flags or patches
if drop:
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(item.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in drop], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bm.to_mesh(item.data)
    bm.free()
    for i in sorted(drop, reverse=True):
        item.data.materials.pop(index=i)
report["dropped_material_slots"] = len(drop)

# 1. Placement: feet on the floor, pelvis over the mannequin's pelvis (x, y).
floor = min(pts["footstepl"].z, pts["footstepr"].z)
offset = mathutils.Vector((bone_head["pelvis"].x - pts["pelvis"].x, bone_head["pelvis"].y - pts["pelvis"].y, -floor))
# Gear files (helmets, vests) are authored in Arma's true character space; the uniform file used
# for the Memory points is offset from it. SS_GEAR_SPACE ("dx,dy,dz", metres) maps gear into the
# uniform's space; the default was measured from the helmet against the uniform's head point.
gear_space = mathutils.Vector((0.0, 0.0, 0.0))
if MEMORY_SRC != SRC:
    gear_space = mathutils.Vector([float(v) for v in os.environ.get("SS_GEAR_SPACE", "-0.305,0.44,-0.85").split(",")])
item.location += offset + gear_space
mem.location += offset
report["gear_space"] = list(gear_space)
bpy.context.view_layer.update()
pts = memory_points(mem)
report["offset"] = list(offset)

if MODE == "skin":
    # 2. Temporary rig on the Arma joints; stretch each segment onto the mannequin's.
    rig_data = bpy.data.armatures.new("ArmaRig")
    rig = bpy.data.objects.new("ArmaRig", rig_data)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    root = rig_data.edit_bones.new("root")
    root.head, root.tail = pts["pelvis"], pts["neck"]
    for joint, (mb, child, mchild) in CHAIN.items():
        b = rig_data.edit_bones.new(joint)
        b.head, b.tail = pts[joint], pts[child]
        b.parent = root
    bpy.ops.object.mode_set(mode="OBJECT")
    # Pose weights by distance to each rig segment (heat weighting fails on open
    # clothing shells): nearest segment, blended with the second nearest near
    # joints. Only carries the pose change; skin weights come from the mannequin.
    segs = {"root": (pts["pelvis"], pts["neck"])}
    segs.update({j: (pts[j], pts[c]) for j, (mb, c, mc) in CHAIN.items()})

    def seg_dist(p, a, b):
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
        return (p - (a + ab * t)).length

    groups = {n: item.vertex_groups.new(name=n) for n in segs}
    for v in item.data.vertices:
        p = item.matrix_world @ v.co
        d = sorted((seg_dist(p, a, b), n) for n, (a, b) in segs.items())
        (d1, n1), (d2, n2) = d[0], d[1]
        w2 = max(0.0, 1.0 - (d2 - d1) / 0.06) * 0.5  # blend within 6 cm of equal distance
        groups[n1].add([v.index], 1.0 - w2, "REPLACE")
        if w2 > 0:
            groups[n2].add([v.index], w2, "REPLACE")
    amod = item.modifiers.new("ArmaPose", "ARMATURE")
    amod.object = rig
    report["pose_weights"] = "segment distance"
    targets = {}
    for joint, (mb, child, mchild) in CHAIN.items():
        for name in (mb, mchild):
            if name not in targets:
                e = bpy.data.objects.new("T_" + name, None)
                e.location = bone_head[name]
                bpy.context.scene.collection.objects.link(e)
                targets[name] = e
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    for joint, (mb, child, mchild) in CHAIN.items():
        pb = rig.pose.bones[joint]
        c = pb.constraints.new("COPY_LOCATION")
        c.target = targets[mb]
        s = pb.constraints.new("STRETCH_TO")
        s.target = targets[mchild]
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = item
    bpy.ops.object.modifier_apply(modifier="ArmaPose")
    for g in list(item.vertex_groups):
        item.vertex_groups.remove(g)
    bpy.data.objects.remove(rig, do_unlink=True)
    for e in targets.values():
        bpy.data.objects.remove(e, do_unlink=True)

    # 3. Skin weights from the mannequin's body mesh.
    for g in body.vertex_groups:
        item.vertex_groups.new(name=g.name)
    dt = item.modifiers.new("Weights", "DATA_TRANSFER")
    dt.object = body
    dt.use_vert_data = True
    dt.data_types_verts = {"VGROUP_WEIGHTS"}
    dt.vert_mapping = "POLYINTERP_NEAREST"
    dt.layers_vgroup_select_src = "ALL"
    dt.layers_vgroup_select_dst = "NAME"
    bpy.context.view_layer.objects.active = item
    bpy.ops.object.modifier_apply(modifier=dt.name)
else:
    # Rigid item: every vertex on one bone.
    bone = MODE.split(":", 1)[1]
    # Arma selections can share bone names ("head"); a new group would become "head.001" and bind
    # to nothing, so clear them first.
    for old in list(item.vertex_groups):
        item.vertex_groups.remove(old)
    g = item.vertex_groups.new(name=bone)
    g.add([v.index for v in item.data.vertices], 1.0, "REPLACE")

# 4. Material names survive FBX only as plain identifiers: "<texture>__<rvmat>" (e.g.
#    crye_g3_shirt_amc_co__crye_g3_shirt), parsed by Tools/Unreal/setup_adf_soldier.py.
import re
for m in item.data.materials:
    if not m:
        continue
    tex = re.search(r"([A-Za-z0-9_]+_(?:co|ca))\.paa", m.name)
    rv = re.search(r"([A-Za-z0-9_]+)\.rvmat", m.name)
    m.name = "{}__{}".format(tex.group(1) if tex else "none", rv.group(1) if rv else "none")
report["material_names"] = [m.name for m in item.data.materials if m]

# 5. Bind to the mannequin armature and export (mesh + armature only).
item.parent = arm
item.matrix_parent_inverse = arm.matrix_world.inverted()
mod = item.modifiers.new("Armature", "ARMATURE")
mod.object = arm
bpy.data.objects.remove(mem, do_unlink=True)
bpy.data.objects.remove(body, do_unlink=True)
bpy.ops.object.select_all(action="DESELECT")
item.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.fbx(filepath=OUT, use_selection=True, add_leaf_bones=False, bake_anim=False,
                         object_types={"ARMATURE", "MESH"}, mesh_smooth_type="FACE", primary_bone_axis="Y",
                         secondary_bone_axis="X", armature_nodetype="NULL")
report["verts"] = len(item.data.vertices)
report["materials"] = [m.name for m in item.data.materials if m]
report["weighted_verts"] = sum(1 for v in item.data.vertices if v.groups)
print("SS_GEARRIG " + json.dumps(report))
