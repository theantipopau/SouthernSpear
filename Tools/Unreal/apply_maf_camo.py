# Southern Spear - MAF uniform camouflage: import Tools/Textures/make_maf_uniform.py's textures and give them to
# the MAF G3 shirt and trouser material instances (the opposing soldier's uniform, viewer-relative).
#
#   UnrealEditor-Cmd ... -ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/apply_maf_camo.py
#   (after Tools/Textures/make_maf_uniform.py; run again after Tools/Unreal/setup_adf_soldier.py, which rebuilds
#   the MAF instances with the plain green G3 texture)
#
# Report: Build/apply_maf_camo.json.

import json
import os

import unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
TEX_DIR = "/SSExp_ObjectiveAssault/Characters/ADF/Textures"
MAT_DIR = "/SSExp_ObjectiveAssault/Characters/ADF"
PAIRS = {"MI_MAF_crye_g3_shirt_amc": "T_SS_MAF_G3_Shirt_co", "MI_MAF_crye_g3_pants_amc": "T_SS_MAF_G3_Pants_co"}
report = {"ok": False, "applied": {}, "errors": []}

for mi_name, tex_name in PAIRS.items():
    src = os.path.join(ROOT, "Art", "Characters", "Textures", tex_name + ".png")
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", TEX_DIR)
    task.set_editor_property("destination_name", tex_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = unreal.load_asset(TEX_DIR + "/" + tex_name)
    mi = unreal.load_asset(MAT_DIR + "/" + mi_name)
    if not tex or not mi:
        report["errors"].append("{}: texture {} material {}".format(mi_name, bool(tex), bool(mi)))
        continue
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
    # Resident like the other soldier textures (Session 040: streamed soldier textures read blurry up close).
    tex.set_editor_property("never_stream", True)
    unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, "BaseColorMap", tex)
    unreal.EditorAssetLibrary.save_loaded_asset(mi, False)
    got = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi, "BaseColorMap")
    report["applied"][mi_name] = got.get_name() if got else None

report["ok"] = not report["errors"] and all(v == PAIRS[k] for k, v in report["applied"].items())
with open(os.path.join(ROOT, "Build", "apply_maf_camo.json"), "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[ApplyMafCamo] ok={}".format(report["ok"]))
