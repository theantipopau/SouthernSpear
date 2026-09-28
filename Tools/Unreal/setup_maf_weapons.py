# Southern Spear - MAF weapon display meshes (ADR-016 W-101/W-102: cosmetic counterparts, same gameplay).
#
#   UnrealEditor-Cmd ... -ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/setup_maf_weapons.py
#   (after Tools/Blender/maf_weapon.py)
#
# Imports Art/Weapons/MAF/SM_MAF_R1.fbx to /SSExp_ObjectiveAssault/Weapons/MAF/SM_MAF_R1 with the Fab pack's own
# materials (FPS Animation Pack AKS74U, cleared under ADR-028; referenced in place, not copied), and duplicates it
# as SM_MAF_S1, the support-weapon counterpart, until a cleared belt-fed model is sourced. The Lyra bridge swaps
# a soldier's held A-series mesh for these when, to the viewer, he is on the other side (SSViewerTeamTintSubsystem).
# Report: Build/setup_maf_weapons.json.

import json
import os

import unreal
import sys

# does_asset_exist() misses Game Feature assets in a commandlet; see Tools/Unreal/ss_assets.py.
sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Tools", "Unreal"))
from ss_assets import asset_exists  # noqa: E402

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
DEST = "/SSExp_ObjectiveAssault/Weapons/MAF"
PACK = "/Game/FP_AKS74U_Animation/AKS74U/Materials/"
MATERIALS = {"MI_AKS74U": PACK + "MI_AKS74U", "MI_Magazine": PACK + "MI_Magazine"}
report = {"ok": False, "meshes": {}, "errors": []}
eal = unreal.EditorAssetLibrary

task = unreal.AssetImportTask()
task.set_editor_property("filename", os.path.join(ROOT, "Art", "Weapons", "MAF", "SM_MAF_R1.fbx"))
task.set_editor_property("destination_path", DEST)
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", False)
opts = unreal.FbxImportUI()
opts.set_editor_property("import_mesh", True)
opts.set_editor_property("import_as_skeletal", False)
opts.set_editor_property("import_materials", False)
opts.set_editor_property("import_textures", False)
smi = opts.get_editor_property("static_mesh_import_data")
smi.set_editor_property("combine_meshes", True)
smi.set_editor_property("auto_generate_collision", False)
task.set_editor_property("options", opts)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

mesh = unreal.load_asset(DEST + "/SM_MAF_R1")
if not mesh:
    report["errors"].append("SM_MAF_R1 did not import")
else:
    slots = []
    for sm in mesh.get_editor_property("static_materials"):
        name = str(sm.get_editor_property("material_slot_name"))
        mat = unreal.load_asset(MATERIALS.get(name, PACK + "MI_AKS74U"))
        slots.append(unreal.StaticMaterial(material_interface=mat, material_slot_name=name))
    mesh.set_editor_property("static_materials", slots)
    eal.save_loaded_asset(mesh, False)
    report["meshes"]["SM_MAF_R1"] = {"slots": [(str(s.material_slot_name), s.material_interface.get_name() if s.material_interface else None) for s in slots],
                                     "muzzle": str(mesh.find_socket("Muzzle").get_editor_property("relative_location")) if mesh.find_socket("Muzzle") else None}
    if asset_exists(DEST + "/SM_MAF_S1"):
        eal.delete_asset(DEST + "/SM_MAF_S1")
    support = eal.duplicate_asset(DEST + "/SM_MAF_R1", DEST + "/SM_MAF_S1")
    report["meshes"]["SM_MAF_S1"] = bool(support) and eal.save_loaded_asset(support, False)

report["ok"] = not report["errors"] and report["meshes"].get("SM_MAF_R1", {}).get("muzzle") is not None
with open(os.path.join(ROOT, "Build", "setup_maf_weapons.json"), "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[SetupMafWeapons] ok={}".format(report["ok"]))
