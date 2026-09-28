# Southern Spear - materials from downloaded Fab / Megascans texture sets (FBX downloads, not UE packs).
#
#   UnrealEditor-Cmd ... -ExecutePythonScript=E:/SouthernSpear/Tools/Unreal/setup_fab_materials.py
#
# The Fab launcher unpacks FBX downloads under Content/Downloaded/VaultCache/FabLibrary/<listing>/ (git-ignored).
# This imports the chosen texture maps into /Game/Art/Environment/Fab/<Name>/ and builds one instance each of a
# small PBR master (M_SS_ScanPBR: BaseColor, Normal, Roughness, AO, Metalness, UV tiling). Idempotent.
# Used for the station structures' corrugated iron (Tools/Unreal/expand_dryriver.py, import_redgum_homestead.py):
# the Singapore Canal "metal" carried carved Asian ornament (Session 041 producer screenshots).
# Licence: Quixel Megascans via Fab, Fab Standard License (Docs/LICENCE_REGISTER.md L-0016).
# Report: Build/fab_materials_report.json.

import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
FAB = os.path.join(PROJECT_DIR, "Content", "Downloaded", "VaultCache", "FabLibrary")
REPORT = os.path.join(PROJECT_DIR, "Build", "fab_materials_report.json")
DEST = "/Game/Art/Environment/Fab"
MASTER = DEST + "/M_SS_ScanPBR"
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
report = {"ok": False, "materials": {}, "errors": []}

# name -> (folder under FabLibrary, file prefix, UV tiling)
SETS = {
    "CorrugatedIron": ("Military_Trenches_Wall_Metal_Corrugated_04-e15620d3/fbx/mid/military_trenches_wall_m_extracted",
                       "Military_Trenches_Wall_Metal_Corrugated_04_ydynfbh_Mid_2K_", 1.0),
}
MAPS = {  # map -> (texture parameter, compression, sRGB)
    "BaseColor": ("BaseColor", unreal.TextureCompressionSettings.TC_DEFAULT, True),
    "Normal": ("Normal", unreal.TextureCompressionSettings.TC_NORMALMAP, False),
    "Roughness": ("Roughness", unreal.TextureCompressionSettings.TC_MASKS, False),
    "AO": ("AO", unreal.TextureCompressionSettings.TC_MASKS, False),
    "Metalness": ("Metalness", unreal.TextureCompressionSettings.TC_MASKS, False),
}


def build_master():
    if eal.does_asset_exist(MASTER):
        return unreal.load_asset(MASTER)
    m = tools.create_asset("M_SS_ScanPBR", DEST, unreal.Material, unreal.MaterialFactoryNew())
    coord = mel.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -1200, 0)
    tiling = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -1200, 150)
    tiling.set_editor_property("parameter_name", "Tiling")
    tiling.set_editor_property("default_value", 1.0)
    uv = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -1000, 50)
    mel.connect_material_expressions(coord, "", uv, "A")
    mel.connect_material_expressions(tiling, "", uv, "B")
    outs = {}
    for i, (key, (param, _, _)) in enumerate(MAPS.items()):
        t = mel.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -700, -400 + i * 250)
        t.set_editor_property("parameter_name", param)
        if key == "Normal":
            t.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        elif key != "BaseColor":
            t.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
        mel.connect_material_expressions(uv, "", t, "UVs")
        outs[key] = t
    tint = mel.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -400, -600)
    tint.set_editor_property("parameter_name", "Tint")
    tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
    col = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, -400)
    mel.connect_material_expressions(outs["BaseColor"], "RGB", col, "A")
    mel.connect_material_expressions(tint, "", col, "B")
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(outs["Normal"], "RGB", unreal.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(outs["Roughness"], "R", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(outs["AO"], "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    mel.connect_material_property(outs["Metalness"], "R", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    return m


def import_texture(path, dest, compression, srgb):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", path)
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    tools.import_asset_tasks([task])
    name = os.path.splitext(os.path.basename(path))[0]
    tex = unreal.load_asset(dest + "/" + name)
    if tex:
        tex.set_editor_property("compression_settings", compression)
        tex.set_editor_property("srgb", srgb)
        eal.save_loaded_asset(tex, False)
    return tex


def main():
    master = build_master()
    for name, (folder, prefix, tiling) in SETS.items():
        src = os.path.join(FAB, folder)
        dest = DEST + "/" + name
        if not os.path.isdir(src):
            report["errors"].append("{}: download not found at {}".format(name, src))
            continue
        path = dest + "/MI_SS_" + name
        mi = unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset(
            "MI_SS_" + name, dest, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property("parent", master)
        got = []
        for key, (param, compression, srgb) in MAPS.items():
            f = os.path.join(src, prefix + key + ".jpg")
            if not os.path.exists(f):
                continue
            tex = import_texture(f, dest, compression, srgb)
            if tex:
                mel.set_material_instance_texture_parameter_value(mi, param, tex)
                got.append(key)
        mel.set_material_instance_scalar_parameter_value(mi, "Tiling", tiling)
        eal.save_loaded_asset(mi)
        report["materials"][name] = {"instance": path, "maps": got}
    report["ok"] = bool(report["materials"]) and all(len(v["maps"]) >= 3 for v in report["materials"].values())


try:
    main()
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[FabMaterials] ok={}".format(report["ok"]))
