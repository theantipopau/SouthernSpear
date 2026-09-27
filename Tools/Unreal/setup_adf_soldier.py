# Southern Spear - ADF soldier gear onto Lyra's mannequin skeleton (ADR-025).
#
# Imports the meshes fitted by Tools/Blender/adfrc_gear_rig.py (Art/Characters/ADF/SK_ADF_*.fbx) as
# skeletal meshes on /Game/Characters/Heroes/Mannequin/Meshes/SK_Mannequin, and builds their
# materials from the ADFRC texture sets: colour (_co), normal (_nohq) and Arma specular/gloss
# (_smdi), found by the Arma material names kept in each slot ("<texture>_co.paa :: <rvmat>.rvmat").
# Multicam textures ("_mc", a Crye trademark: ADR-016 still applies) take an AMCU variant when one
# exists, else a flat coyote finish. Report: Build/adf_soldier_setup.json.

import glob
import json
import os
import re
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
ART = os.path.join(PROJECT_DIR, "Art", "Characters", "ADF")
TEX_ROOT = os.path.join(PROJECT_DIR, "Art", "ADFRC", "Textures")
DEST = "/SSExp_ObjectiveAssault/Characters/ADF"
SKELETON = "/Game/Characters/Heroes/Mannequin/Meshes/SK_Mannequin"
MESHES = ["SK_ADF_Uniform_G3", "SK_ADF_Vest_TBAS", "SK_ADF_Helmet_OpsCore"]
REPORT = os.path.join(PROJECT_DIR, "Build", "adf_soldier_setup.json")
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
report = {"ok": False, "meshes": {}, "errors": []}

index = {}
for path in glob.glob(os.path.join(TEX_ROOT, "**", "*.png"), recursive=True):
    index.setdefault(os.path.splitext(os.path.basename(path))[0].lower(), path)


def gear_master():
    """M_SS_GearPBR: the weapon PBR graph (colour, normal, SMDI) flagged for skeletal meshes."""
    path = DEST + "/M_SS_GearPBR"
    if not eal.does_asset_exist(path):
        eal.duplicate_asset("/SSExp_ObjectiveAssault/Materials/M_SS_WeaponPBR", path)
    m = unreal.load_asset(path)
    m.set_editor_property("used_with_skeletal_mesh", True)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    return m


def texture(stem, normal=False, masks=False):
    src = index.get(stem.lower())
    if not src:
        return None
    name = "T_ADF_" + re.sub(r"[^A-Za-z0-9_]", "_", stem)
    path = DEST + "/Textures/" + name
    if not eal.does_asset_exist(path):
        task = unreal.AssetImportTask()
        task.filename = src
        task.destination_path = DEST + "/Textures"
        task.destination_name = name
        task.automated = True
        task.replace_existing = True
        task.save = False
        tools.import_asset_tasks([task])
    tex = unreal.load_asset(path)
    if tex and (normal or masks):
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings",
                                unreal.TextureCompressionSettings.TC_NORMALMAP if normal else unreal.TextureCompressionSettings.TC_MASKS)
    if tex:
        tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_CHARACTER)
        eal.save_loaded_asset(tex)
    return tex


def colour_stem(stem):
    if re.search(r"_mc(_|$)", stem):
        for alt in (re.sub(r"_mc(_|$)", r"_amcu\1", stem), re.sub(r"_mc(_|$)", r"_coyote\1", stem)):
            if alt.lower() in index:
                return alt, "amcu-or-coyote variant"
        return None, "multicam: flat coyote"
    return stem, "as authored"


def material_for(slot_name, parent):
    # Slot names from adfrc_gear_rig.py: "<texture>__<rvmat>", e.g. crye_g3_shirt_amc_co__crye_g3_shirt.
    m = re.search(r"([A-Za-z0-9]+(?:_[A-Za-z0-9]+)*?)_(co|ca)__", slot_name)
    rv = re.search(r"__([A-Za-z0-9_]+?)(?:_\d+)?(?:\s|$)", slot_name)
    stem = (m.group(1) + "_" + m.group(2)) if m else None
    rvstem = rv.group(1) if rv else (m.group(1) if m else None)
    name = "MI_ADF_" + re.sub(r"[^A-Za-z0-9_]", "_", (m.group(1) if m else slot_name))[:60]
    path = DEST + "/" + name
    mi = unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset(
        name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    note = "no texture"
    if stem:
        cstem, note = colour_stem(stem)
        col = texture(cstem) if cstem else None
        if col:
            mel.set_material_instance_texture_parameter_value(mi, "BaseColorMap", col)
        else:
            # No Multicam (ADR-016): a plain coyote finish (Art/Characters/ADF/T_ADF_Coyote.png).
            index.setdefault("t_adf_coyote", os.path.join(ART, "T_ADF_Coyote.png"))
            mel.set_material_instance_texture_parameter_value(mi, "BaseColorMap", texture("T_ADF_Coyote"))
            mel.set_material_instance_scalar_parameter_value(mi, "Roughness", 0.8)
        base = m.group(1)
        base = re.sub(r"_(mc|amcu|amc|coyote|tan|green|grey|black|coyote_brown)$", "", base)
        for cand in (rvstem + "_nohq", base + "_nohq", rvstem.split("_")[0] + "_nohq"):
            n = texture(cand, normal=True)
            if n:
                mel.set_material_instance_texture_parameter_value(mi, "NormalMap", n)
                break
        # Fabric and webbing: matte and non-metallic. Arma SMDI gloss made pouches and straps render
        # chrome-white under Lumen (in-game capture). Hard items keep their SMDI.
        hard = any(k in stem.lower() for k in ("mag", "peltor", "comtac", "holster", "safariland", "nvg", "battery", "g19"))
        mel.set_material_instance_scalar_parameter_value(mi, "Metallic", 0.0)
        mel.set_material_instance_scalar_parameter_value(mi, "UseSMDI", 0.0)
        mel.set_material_instance_scalar_parameter_value(mi, "Roughness", 0.55 if hard else 0.85)
        if hard:
            for cand in (rvstem + "_smdi", base + "_smdi"):
                sm = texture(cand, masks=True)
                if sm:
                    mel.set_material_instance_texture_parameter_value(mi, "SMDIMap", sm)
                    mel.set_material_instance_scalar_parameter_value(mi, "UseSMDI", 1.0)
                    break
    eal.save_loaded_asset(mi)
    return mi, stem, note


def import_mesh(name):
    task = unreal.AssetImportTask()
    task.filename = os.path.join(ART, name + ".fbx")
    task.destination_path = DEST
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", True)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    ui.set_editor_property("skeleton", unreal.load_asset(SKELETON))
    ui.set_editor_property("import_materials", False)  # slot names come from the FBX material names anyway
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("import_animations", False)
    ui.set_editor_property("create_physics_asset", False)
    task.options = ui
    tools.import_asset_tasks([task])
    return unreal.load_asset(DEST + "/" + name)


def main():
    parent = gear_master()
    # Materials an earlier import created from slot names (import_materials keeps the names but the
    # assets are unused): remove them.
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    for d in reg.get_assets_by_path(DEST, recursive=False):
        n = str(d.asset_name)
        if n.startswith("_") or n.startswith("MI_ADF__"):
            eal.delete_asset(str(d.package_name))
    for name in MESHES:
        mesh = import_mesh(name)
        if not mesh:
            report["meshes"][name] = "import failed"
            continue
        slots = []
        mats = mesh.get_editor_property("materials")
        for i, sm in enumerate(mats):
            slot = str(sm.get_editor_property("material_slot_name"))
            imported = sm.get_editor_property("material_interface")
            full = imported.get_name() if imported else slot
            mi, stem, note = material_for(full + " " + slot, parent)
            sm.set_editor_property("material_interface", mi)
            mats[i] = sm
            slots.append({"slot": slot, "source": full, "texture": stem, "note": note})
        mesh.set_editor_property("materials", mats)
        # A property set from Python does not dirty the package: save unconditionally, or the
        # imported default (WorldGridMaterial) stays on disk.
        report["meshes"][name] = {"slots": slots, "saved": eal.save_loaded_asset(mesh, False)}
    report["ok"] = all(isinstance(v, dict) and v["saved"] for v in report["meshes"].values())


try:
    main()
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[ADFSoldier] ok={}".format(report["ok"]))
