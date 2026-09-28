# Southern Spear - first-person arms view model assets (producer 2026-09-28: "arms view model").
#
# Imports the arms prepared by Tools/Blender/fp_arms.py (Build/fp_arms/SK_FP_Arms_<Set>.fbx: the Fab pack's
# arms, skeleton and clips, its real-weapon model removed) and the sleeve/glove texture from
# Tools/Textures/make_fp_arms_texture.py, into /SSExp_ObjectiveAssault/FirstPerson/<Set> (beside the soldiers,
# whose fabric material it uses). The arms get a fabric material
# instance of M_SS_FabricPBR. The A-series weapon is attached in game to the arms' weapon bone (Main_j)
# by USSFirstPersonSubsystem. Writes Build/fp_arms_setup.json.
#
#   blender -b --factory-startup -P Tools/Blender/fp_arms.py -- "<M4 pack>/M4.fbx" FP_Rifle Build/fp_arms/SK_FP_Arms_Rifle.fbx
#   python Tools/Textures/make_fp_arms_texture.py "<M4 pack>/Hand_D.jpg" Build/fp_arms/T_FP_Arms_Rifle_BC.png
#   UnrealEditor-Cmd ... -ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/setup_fp_arms.py

import json
import os
import traceback

import unreal
import sys

# does_asset_exist() misses Game Feature assets in a commandlet; see Tools/Unreal/ss_assets.py.
sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Tools", "Unreal"))
from ss_assets import asset_exists  # noqa: E402

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
BUILD = os.path.join(PROJECT_DIR, "Build", "fp_arms")
REPORT = os.path.join(PROJECT_DIR, "Build", "fp_arms_setup.json")
SETS = ["Rifle", "Pistol"]  # Pistol: Fab G17 FPS pack (same hand mesh and UVs, so the same sleeve/glove texture)
OLD = "/Game/Art/FirstPerson"  # first import location (asset reference rules forbid /Game -> Game Feature)
FABRIC = "/SSExp_ObjectiveAssault/Characters/ADF/M_SS_FabricPBR"
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
report = {"ok": False, "sets": {}, "errors": []}


def import_task(src, dest, name, options=None):
    task = unreal.AssetImportTask()
    task.filename = src
    task.destination_path = dest
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    if options:
        task.options = options
    tools.import_asset_tasks([task])
    return list(task.get_editor_property("imported_object_paths"))


def setup(name):
    dest = "/SSExp_ObjectiveAssault/FirstPerson/" + name
    fbx = os.path.join(BUILD, "SK_FP_Arms_{}.fbx".format(name))
    info = {}
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", True)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("import_animations", True)
    ui.set_editor_property("create_physics_asset", False)
    ui.anim_sequence_import_data.set_editor_property("import_bone_tracks", True)
    ui.anim_sequence_import_data.set_editor_property("animation_length", unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    paths = import_task(fbx, dest, "SK_FP_Arms_" + name, ui)
    info["imported"] = [p.split("/")[-1] for p in paths]
    mesh = unreal.load_asset(dest + "/SK_FP_Arms_" + name)
    if not mesh:
        raise RuntimeError("arms mesh not imported: " + fbx)

    tex_paths = import_task(os.path.join(BUILD, "T_FP_Arms_{}_BC.png".format(name)), dest, "T_FP_Arms_{}_BC".format(name))
    tex = unreal.load_asset(tex_paths[0]) if tex_paths else None
    if tex:
        tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_CHARACTER)
        tex.set_editor_property("never_stream", True)  # script-built materials: see setup_adf_soldier.py
        eal.save_loaded_asset(tex)
    mi_path = dest + "/MI_FP_Arms_" + name
    if asset_exists(mi_path):
        eal.delete_asset(mi_path)
    mi = tools.create_asset("MI_FP_Arms_" + name, dest, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, unreal.load_asset(FABRIC))
    if tex:
        mel.set_material_instance_texture_parameter_value(mi, "BaseColorMap", tex)
    eal.save_loaded_asset(mi)
    mats = mesh.get_editor_property("materials")
    for i, sm in enumerate(mats):
        sm.set_editor_property("material_interface", mi)
        mats[i] = sm
    mesh.set_editor_property("materials", mats)
    info["saved"] = eal.save_loaded_asset(mesh, False)

    skeleton = mesh.get_editor_property("skeleton")
    info["skeleton"] = skeleton.get_path_name() if skeleton else None
    info["bounds_cm"] = [round(v, 1) for v in (mesh.get_bounds().box_extent.x * 2, mesh.get_bounds().box_extent.y * 2,
                                                 mesh.get_bounds().box_extent.z * 2)]
    anims = {}
    for d in unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path(dest, recursive=False):
        a = d.get_asset()
        if isinstance(a, unreal.AnimSequence):
            # "SK_FP_Arms_RifleArmature_FP_Rifle_Draw" -> "A_FP_Rifle_Draw"
            name_ = a.get_name()
            if name_.startswith("A_A_"):  # an earlier run's double prefix
                eal.delete_asset(a.get_path_name().split(".")[0])
                continue
            clean = "A_" + name_.split("Armature_", 1)[1] if "Armature_" in name_ else name_
            if clean != name_:
                target = dest + "/" + clean
                if asset_exists(target):
                    eal.delete_asset(target)
                eal.rename_asset(a.get_path_name().split(".")[0], target)
            anims[clean] = round(a.get_play_length(), 2)
    info["anims"] = anims
    report["sets"][name] = info


try:
    if eal.does_directory_exist(OLD):
        eal.delete_directory(OLD)
    for s in SETS:
        setup(s)
    report["ok"] = all(len(v.get("anims", {})) >= 6 for v in report["sets"].values())
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[FPArms] ok={}".format(report["ok"]))
