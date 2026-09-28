"""Probe the three candidate body meshes: do they carry an armature, and do its bone names match Lyra's mannequin?

    blender -b --factory-startup --python Tools/Blender/probe_candidate_bodies.py

The Quantum pack shipped .uasset only, so it could not be re-rigged. These three are source files
(GLB/FBX) in the Fab library cache, so the Blender route is open. What decides whether a candidate is
usable is the bone names: leader pose and any retargeter match by name, so a rig that is not already
Manny-compatible costs a rename pass (cheap) or an IK rig (not cheap). This reports vertices,
materials, armatures and the bone-name overlap with the mannequin.
"""
import glob
import json
import os
import sys

import bpy

LIBRARY = "E:/SouthernSpear/Content/Downloaded/VaultCache/FabLibrary"
OUT = "E:/SouthernSpear/Build/probe_candidate_bodies.json"
# Lyra's mannequin bone names, from Build/probe_manny_bones.json (164 bones).
MANNY = set(json.load(open("E:/SouthernSpear/Build/probe_manny_bones.json"))["SK_Mannequin"]["bones"])
QUANTUM = set()

CANDIDATES = {
    "male_base_mesh": os.path.join(LIBRARY, "Free_Pack_-_Male_Base_Mesh-6ea2f53a/fbx/free_pack_male_base_mesh.fbx"),
    "fsb_operator": os.path.join(LIBRARY, "FSB_Operator-d68905bd/glb/converted/fsb_operator.glb"),
    "swat_operator": os.path.join(LIBRARY, "S_W_A_T__Operator-_4k_Followers_Special_Remaster-09e47572"
                                        "/glb/converted/swat_operator_4k_followers_special_remaster.glb"),
}

report = {"manny_bones": len(MANNY), "candidates": {}}

for name, path in CANDIDATES.items():
    entry = {"path": path, "exists": os.path.exists(path)}
    if not entry["exists"]:
        report["candidates"][name] = entry
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        if path.lower().endswith(".glb"):
            bpy.ops.import_scene.gltf(filepath=path)
        else:
            bpy.ops.import_scene.fbx(filepath=path)
    except Exception as exc:
        entry["import_error"] = str(exc)[:300]
        report["candidates"][name] = entry
        continue

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    entry["mesh_objects"] = len(meshes)
    entry["armatures"] = len(armatures)
    entry["verts"] = sum(len(o.data.vertices) for o in meshes)
    entry["tris"] = sum(len(o.data.polygons) for o in meshes)
    entry["materials"] = sorted({m.name for o in meshes for m in o.data.materials if m})
    # Blender 5.x: textures are node-tree Image Texture nodes, not a collection on the tree.
    textures = set()
    for o in meshes:
        for m in o.data.materials:
            tree = getattr(m, "node_tree", None)
            if not tree:
                continue
            for node in tree.nodes:
                if node.type == "TEX_IMAGE" and node.image:
                    textures.add(node.image.filepath or node.image.name)
    entry["image_textures"] = sorted(textures)[:12]

    if armatures:
        bones = [b.name for b in armatures[0].data.bones]
        entry["bone_count"] = len(bones)
        entry["bones_sample"] = bones[:20]
        shared = sorted(set(bones) & MANNY)
        entry["shared_with_manny"] = len(shared)
        entry["manny_compatible"] = len(set(bones) - MANNY) == 0
        entry["missing_from_mesh"] = len(MANNY - set(bones))
        entry["bpy_materials_slot_count"] = sum(len(o.material_slots) for o in meshes)
        entry["modifiers"] = sorted({m.type for o in meshes for m in o.modifiers})
    report["candidates"][name] = entry

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=1)
print("WROTE", OUT)
