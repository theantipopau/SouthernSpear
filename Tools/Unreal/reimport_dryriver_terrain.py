# Southern Spear - re-import only the Dry River terrain mesh (SS_MAP_DryRiver_01) from the Blender blockout FBX,
# keeping the level as it is: complex-as-simple collision, Nanite off (expand_dryriver.py), actor overrides intact.
#
#   UnrealEditor-Cmd ... -ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/reimport_dryriver_terrain.py
#   (after Tools/Blender/dryriver_blockout.py; then farm_dryriver.py and build_dryriver_nav.py)
#
# build_dryriver_level.py does the same import as part of a full level rebuild; this is the terrain alone.
# Report: Build/reimport_dryriver_terrain.json.

import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
FBX = os.path.join(PROJECT_DIR, "Content", "Art", "Blockout", "SS_MAP_DryRiver_01.fbx")
MESH = "/Game/Art/Blockout/SS_MAP_DryRiver_01"
REPORT = os.path.join(PROJECT_DIR, "Build", "reimport_dryriver_terrain.json")
report = {"ok": False, "errors": []}


def main():
    before = unreal.load_asset(MESH)
    report["triangles_before"] = before.get_num_triangles(0) if before else None
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", FBX)
    task.set_editor_property("destination_path", "/Game/Art/Blockout")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", True)
    opts.set_editor_property("import_as_skeletal", False)
    opts.set_editor_property("import_animations", False)
    opts.set_editor_property("import_materials", False)
    opts.set_editor_property("import_textures", False)
    smi = opts.get_editor_property("static_mesh_import_data")
    smi.set_editor_property("combine_meshes", True)
    smi.set_editor_property("auto_generate_collision", False)
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(MESH)
    if not mesh:
        report["errors"].append("mesh missing after import")
        return
    mesh.get_editor_property("body_setup").set_editor_property(
        "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    ns = mesh.get_editor_property("nanite_settings")
    ns.enabled = False
    mesh.set_editor_property("nanite_settings", ns)
    report["saved"] = unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)
    report["triangles_after"] = mesh.get_num_triangles(0)
    e = mesh.get_bounds().box_extent
    report["size_m"] = [round(e.x / 50, 1), round(e.y / 50, 1), round(e.z / 50, 1)]
    report["collision"] = str(mesh.get_editor_property("body_setup").get_editor_property("collision_trace_flag"))
    report["ok"] = report["saved"] and report["triangles_after"] < (report["triangles_before"] or 1e9)


try:
    main()
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[ReimportDryRiverTerrain] ok={}".format(report["ok"]))
