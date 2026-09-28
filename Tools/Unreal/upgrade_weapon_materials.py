"""Weapon materials use the full ADFRC texture set: colour (_co), normal
(_nohq) and Arma specular/gloss (_smdi: G specular, B gloss). Creates
M_SS_WeaponPBR, re-parents every textured weapon MI to it, imports the normal
and SMDI maps beside the colour map, and keeps weapon textures resident
(no streaming) so the first-person view model stays sharp.
Report: Build/weapon_materials_report.json."""
import json
import os
import re
import unreal
import sys

# does_asset_exist() misses Game Feature assets in a commandlet; see Tools/Unreal/ss_assets.py.
sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Tools", "Unreal"))
from ss_assets import asset_exists  # noqa: E402

ROOT = "E:/SouthernSpear/Art/Weapons"
MAT = "/SSExp_ObjectiveAssault/Materials/M_SS_WeaponPBR"
WEAPONS = ["A88", "A88G", "A89", "A4", "A416", "A25", "A9"]
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
report = {}


def master():
    if asset_exists(MAT):
        return unreal.load_asset(MAT)
    m = tools.create_asset("M_SS_WeaponPBR", os.path.dirname(MAT), unreal.Material, unreal.MaterialFactoryNew())
    E = unreal
    col = mel.create_material_expression(m, E.MaterialExpressionTextureSampleParameter2D, -700, 0)
    col.set_editor_property("parameter_name", "BaseColorMap")
    nrm = mel.create_material_expression(m, E.MaterialExpressionTextureSampleParameter2D, -700, 300)
    nrm.set_editor_property("parameter_name", "NormalMap")
    nrm.set_editor_property("sampler_type", E.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    nrm.set_editor_property("texture", unreal.load_asset("/Engine/EngineMaterials/FlatNormal"))
    smdi = mel.create_material_expression(m, E.MaterialExpressionTextureSampleParameter2D, -700, 600)
    smdi.set_editor_property("parameter_name", "SMDIMap")
    smdi.set_editor_property("sampler_type", E.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    smdi.set_editor_property("texture", unreal.load_asset("/Engine/EngineResources/WhiteSquareTexture"))
    use = mel.create_material_expression(m, E.MaterialExpressionScalarParameter, -700, 900)
    use.set_editor_property("parameter_name", "UseSMDI")
    rough_default = mel.create_material_expression(m, E.MaterialExpressionScalarParameter, -700, 1000)
    rough_default.set_editor_property("parameter_name", "Roughness")
    rough_default.set_editor_property("default_value", 0.55)
    metal = mel.create_material_expression(m, E.MaterialExpressionScalarParameter, -300, 900)
    metal.set_editor_property("parameter_name", "Metallic")
    metal.set_editor_property("default_value", 0.2)
    # Roughness from Arma gloss (B): rough = 1 - 0.85 * gloss.
    inv = mel.create_material_expression(m, E.MaterialExpressionOneMinus, -400, 650)
    gloss = mel.create_material_expression(m, E.MaterialExpressionMultiply, -500, 650)
    gloss.set_editor_property("const_b", 0.85)
    mel.connect_material_expressions(smdi, "B", gloss, "A")
    mel.connect_material_expressions(gloss, "", inv, "")
    lerp = mel.create_material_expression(m, E.MaterialExpressionLinearInterpolate, -200, 700)
    mel.connect_material_expressions(rough_default, "", lerp, "A")
    mel.connect_material_expressions(inv, "", lerp, "B")
    mel.connect_material_expressions(use, "", lerp, "Alpha")
    spec = mel.create_material_expression(m, E.MaterialExpressionLinearInterpolate, -200, 850)
    spec.set_editor_property("const_a", 0.5)
    mel.connect_material_expressions(smdi, "G", spec, "B")
    mel.connect_material_expressions(use, "", spec, "Alpha")
    mel.connect_material_property(col, "RGB", E.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(nrm, "RGB", E.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(lerp, "", E.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(spec, "", E.MaterialProperty.MP_SPECULAR)
    mel.connect_material_property(metal, "", E.MaterialProperty.MP_METALLIC)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    return m


def import_tex(path, dest, name, normal):
    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = dest
    task.destination_name = name
    task.replace_existing = True
    task.automated = True
    task.save = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = unreal.load_asset(dest + "/" + name)
    if tex:
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings",
                                unreal.TextureCompressionSettings.TC_NORMALMAP if normal else unreal.TextureCompressionSettings.TC_MASKS)
        resident(tex)
    return tex


def resident(tex):
    tex.set_editor_property("never_stream", True)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WEAPON)
    eal.save_loaded_asset(tex)


parent = master()
for w in WEAPONS:
    manifest = os.path.join(ROOT, w, "ADFRC", "manifest.json")
    if not os.path.exists(manifest):
        continue
    textures = json.load(open(manifest))["textures"]
    dest = "/SSExp_ObjectiveAssault/Weapons/" + w
    done = []
    for slot, entry in textures.items():
        mi_path = dest + "/MI_{}_{}".format(w, slot)
        if not entry.get("colour") or not asset_exists(mi_path):
            continue
        mi = unreal.load_asset(mi_path)
        if isinstance(mi.get_editor_property("parent"), unreal.Material) and mi.get_editor_property("parent").get_name() == "M_SS_OpticGlass":
            continue
        colour = unreal.load_asset(dest + "/T_{}_{}".format(w, slot))
        mi.set_editor_property("parent", parent)
        if colour:
            mel.set_material_instance_texture_parameter_value(mi, "BaseColorMap", colour)
            resident(colour)
        got = []
        if entry.get("normal") and os.path.exists(entry["normal"]):
            n = import_tex(entry["normal"], dest, "T_{}_{}_N".format(w, slot), True)
            if n:
                mel.set_material_instance_texture_parameter_value(mi, "NormalMap", n)
                got.append("normal")
        smdi_path = re.sub(r"_(co|ca)\.png$", "_smdi.png", entry["colour"], flags=re.I)
        if smdi_path != entry["colour"] and not os.path.exists(smdi_path):
            smdi_path = re.sub(r"_(CO|CA)\.png$", "_SMDI.png", entry["colour"])
        if os.path.exists(smdi_path) and smdi_path != entry["colour"]:
            sm = import_tex(smdi_path, dest, "T_{}_{}_SMDI".format(w, slot), False)
            if sm:
                mel.set_material_instance_texture_parameter_value(mi, "SMDIMap", sm)
                mel.set_material_instance_scalar_parameter_value(mi, "UseSMDI", 1.0)
                got.append("smdi")
        eal.save_loaded_asset(mi)
        done.append("{}[{}]".format(slot, ",".join(got)))
    report[w] = done
json.dump(report, open("E:/SouthernSpear/Build/weapon_materials_report.json", "w"), indent=1)
unreal.log("SS_WEAPONMAT " + json.dumps(report))
