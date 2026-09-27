# Southern Spear - content fixes found in play (Session 025).
#
# 1. Re-writes the Objective Assault Game Feature component grants (adds Lyra's
#    music manager: the game state warned on screen every frame without it).
# 2. Flags every material used by the soldier bodies (B_SS_Soldier parts), the
#    Southern Spear character materials and the first-person arms as used with
#    skeletal meshes. Without the flag the engine cannot compile the skinned
#    variant at runtime and draws the default grey material ("Material with
#    missing usage flag was applied to skeletal mesh"). Vendor materials live in
#    git-ignored Fab folders; the flag is a local fix re-applied by this script.
#
# Writes Build/skeletal_materials_fix.json.

import json
import os
import sys
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "skeletal_materials_fix.json")
MESHES = [
    "/Game/QuantumCharacter/Mesh/SKM_QuantumCharacter",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Head",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Hands",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Sweater",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Pants_Military",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Shoes",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Armor_Small",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Beret",
    "/Game/FP_AKS74U_Animation/Demo/FirstPersonArms/Character/Mesh/SK_Mannequin_Arms",
]
EXTRA_MATERIAL_DIRS = ["/SSExp_ObjectiveAssault/Characters/Materials"]

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
report = {"ok": False, "flagged": [], "already": [], "errors": []}


def base_material(mi):
    m = mi
    while isinstance(m, unreal.MaterialInstance):
        m = m.get_editor_property("parent")
    return m if isinstance(m, unreal.Material) else None


def flag(material):
    if material is None:
        return
    name = material.get_path_name()
    if name in report["flagged"] or name in report["already"]:
        return
    if material.get_editor_property("used_with_skeletal_mesh"):
        report["already"].append(name)
        return
    material.set_editor_property("used_with_skeletal_mesh", True)
    mel.recompile_material(material)
    eal.save_loaded_asset(material, False)
    report["flagged"].append(name)


try:
    sys.path.insert(0, os.path.join(PROJECT_DIR, "Tools", "Unreal"))
    os.environ["SS_OA_IMPORT_ONLY"] = "1"
    import setup_objective_assault as soa
    report["grants_ok"] = bool(soa.ensure_game_feature_data())

    for path in MESHES:
        mesh = unreal.load_asset(path)
        if mesh is None:
            report["errors"].append("missing " + path)
            continue
        for sm in mesh.get_editor_property("materials"):
            flag(base_material(sm.get_editor_property("material_interface")))
    for folder in EXTRA_MATERIAL_DIRS:
        for asset_path in eal.list_assets(folder, recursive=True):
            asset = unreal.load_asset(asset_path)
            if isinstance(asset, unreal.MaterialInterface):
                flag(base_material(asset) if isinstance(asset, unreal.MaterialInstance) else asset)
    report["ok"] = report["grants_ok"] and not report["errors"]
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[SkeletalMaterials] ok={} flagged={}".format(report["ok"], len(report["flagged"])))
