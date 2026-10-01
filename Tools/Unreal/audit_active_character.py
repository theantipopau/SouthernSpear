# Southern Spear - Audit of the active friendly soldier assembly (ADR-042).
#
# Measures exact LOD counts, vertex totals, triangles, skeletons, and physics assets
# for the active Quantum modules and ADFRC leader-posed gear.
# Updates the historical R-58 and R-59 baselines with measured data.
# Writes Build/active_character_audit.json.
# Requires the Game Feature to be mounted (unreal.load_asset paths otherwise resolve to None).

import json
import os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT_PATH = os.path.join(PROJECT_DIR, "Build", "active_character_audit.json")

PARTS = {
    "Quantum_Shirt": "/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Shirt_RolledUp_Blue",
    "Quantum_Jeans": "/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Jeans",
    "Quantum_Arms": "/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Arms",
    "Quantum_Head": "/SSExp_ObjectiveAssault/Characters/QuantumProto/SKM_Head",
    "ADF_Vest": "/SSExp_ObjectiveAssault/Characters/ADF/SK_ADF_Vest_TBAS",
    "ADF_Helmet": "/SSExp_ObjectiveAssault/Characters/ADF/SK_ADF_Helmet_OpsCore",
}

report = {
    "ok": False,
    "assembly": "ADR-042 Quantum Modules + ADFRC Gear",
    "parts": {},
    "total_verts_lod0": 0,
    "total_triangles_lod0": 0,
    "has_physics_assets": False,
    "summary": ""
}

total_verts = 0
total_tris = 0
all_have_physics = True

for part_name, asset_path in PARTS.items():
    part_info = {"asset": asset_path, "loaded": False}
    mesh = unreal.load_asset(asset_path)
    if mesh is None:
        part_info["error"] = "Failed to load asset"
        all_have_physics = False
        report["parts"][part_name] = part_info
        continue

    part_info["loaded"] = True
    try:
        skel = mesh.get_editor_property("skeleton")
        part_info["skeleton"] = skel.get_path_name() if skel else None
        if skel:
            part_info["bone_count"] = len(skel.get_reference_pose().get_bone_names())
        phys = mesh.get_editor_property("physics_asset")
        part_info["physics_asset"] = phys.get_path_name() if phys else None

        # Optional VibeUE details supplement native skeletal mesh properties; core audit data
        # remains available when that editor plugin is absent.
        try:
            vibe_info = unreal.SkeletonService.get_skeletal_mesh_info(asset_path)
            if vibe_info:
                part_info["socket_count"] = vibe_info.socket_count
                part_info["bounds_min"] = [vibe_info.bounds_min.x, vibe_info.bounds_min.y, vibe_info.bounds_min.z]
                part_info["bounds_max"] = [vibe_info.bounds_max.x, vibe_info.bounds_max.y, vibe_info.bounds_max.z]
        except Exception as exc:
            part_info["vibe_error"] = str(exc)

        if not part_info.get("physics_asset"):
            all_have_physics = False

        subsystem = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
        num_lods = subsystem.get_lod_count(mesh)
        verts_lod0 = subsystem.get_num_verts(mesh, 0)
        tris_lod0 = mesh.get_num_triangles(0)
        part_info["num_lods"] = num_lods
        part_info["verts_lod0"] = verts_lod0
        part_info["triangles_lod0"] = tris_lod0
        part_info["materials"] = [
            str(m.get_editor_property("material_slot_name")) + " -> " +
            (m.get_editor_property("material_interface").get_path_name() if m.get_editor_property("material_interface") else "None")
            for m in mesh.get_editor_property("materials")
        ]
        total_verts += verts_lod0
        total_tris += tris_lod0
    except Exception as exc:
        part_info["error"] = str(exc)
        part_info["measurement_ok"] = False

    report["parts"][part_name] = part_info

report["total_verts_lod0"] = total_verts
report["total_triangles_lod0"] = total_tris
report["has_physics_assets"] = all_have_physics
report["ok"] = len(report["parts"]) == len(PARTS) and all(
    p.get("loaded", False) and not p.get("error")
    and "verts_lod0" in p and "triangles_lod0" in p
    for p in report["parts"].values()
)
report["summary"] = f"Total assembled LOD0 geometry: {total_verts:,} vertices, {total_tris:,} triangles across {len(PARTS)} parts. Physics assets: {'All present' if all_have_physics else 'Missing on some/all parts'}."

with open(REPORT_PATH, "w") as f:
    json.dump(report, f, indent=2)

unreal.log(f"[CharacterAudit] Complete: {report['summary']}")
