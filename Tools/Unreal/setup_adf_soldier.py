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
MESHES = ["SK_ADF_Uniform_G3", "SK_ADF_Vest_TBAS", "SK_ADF_Helmet_OpsCore",
          "SK_MAF_Vest_Peacekeeper", "SK_MAF_Helmet_PASGT"]  # MAF: a conventional force, not Australian camo
# MAF palette (ADR-016: MAF is a conventional army with its own look, never AMCU or a real nation's
# pattern): plain green uniform textures; Australian camo on MAF gear becomes flat olive.
MAF_SWAP = {"crye_g3_shirt_amc_co": "Crye_G3_Shirt_Green_co", "crye_g3_pants_amc_co": "Crye_G3_Pants_green_co",
            "crye_g3_boots_coyote_brown_co": "Crye_G3_Boots_Ranger_Green_co"}
MAF_FLAT = ("pasgt_dpc_co", "belt_amcu_co", "tacgear_amcu_co")
# ADFRC colour sheets are 4096^2. A cap below that halves them on import (Session 051).
MAX_TEXTURE_SIZE = 4096
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


def fabric_master():
    """M_SS_FabricPBR: cloth and webbing. Arma's SMDI gloss (B) and specular (G) vary the surface inside a
    cloth-like band instead of the weapon mapping (rough = 1 - 0.85 * gloss), which rendered fabric
    chrome-white; before this, fabric used one flat roughness (0.85) and looked like plastic."""
    path = DEST + "/M_SS_FabricPBR"
    E = unreal
    # Same trap as material_for: does_asset_exist() answers False for this plugin path, so branch on
    # the load instead or a re-run tries to create a material that is already there.
    existing = unreal.load_asset(path)
    if existing is not None:
        return existing
    m = tools.create_asset("M_SS_FabricPBR", DEST, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("used_with_skeletal_mesh", True)
    col = mel.create_material_expression(m, E.MaterialExpressionTextureSampleParameter2D, -900, 0)
    col.set_editor_property("parameter_name", "BaseColorMap")
    nrm = mel.create_material_expression(m, E.MaterialExpressionTextureSampleParameter2D, -900, 300)
    nrm.set_editor_property("parameter_name", "NormalMap")
    nrm.set_editor_property("sampler_type", E.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    nrm.set_editor_property("texture", unreal.load_asset("/Engine/EngineMaterials/FlatNormal"))
    smdi = mel.create_material_expression(m, E.MaterialExpressionTextureSampleParameter2D, -900, 600)
    smdi.set_editor_property("parameter_name", "SMDIMap")
    smdi.set_editor_property("sampler_type", E.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    smdi.set_editor_property("texture", unreal.load_asset("/Engine/EngineResources/Black"))

    def param(name, value, x, y):
        e = mel.create_material_expression(m, E.MaterialExpressionScalarParameter, x, y)
        e.set_editor_property("parameter_name", name)
        e.set_editor_property("default_value", value)
        return e

    rmin, rmax = param("RoughnessMin", 0.62, -600, 800), param("RoughnessMax", 0.95, -600, 700)
    strength, spec_scale = param("NormalStrength", 1.0, -600, 450), param("SpecularScale", 0.35, -600, 950)
    # Roughness: glossy texels (B high) toward RoughnessMin.
    rough = mel.create_material_expression(m, E.MaterialExpressionLinearInterpolate, -300, 700)
    mel.connect_material_expressions(rmax, "", rough, "A")
    mel.connect_material_expressions(rmin, "", rough, "B")
    mel.connect_material_expressions(smdi, "B", rough, "Alpha")
    # Specular: 0.15 + G * SpecularScale.
    spec_mul = mel.create_material_expression(m, E.MaterialExpressionMultiply, -400, 900)
    mel.connect_material_expressions(smdi, "G", spec_mul, "A")
    mel.connect_material_expressions(spec_scale, "", spec_mul, "B")
    spec = mel.create_material_expression(m, E.MaterialExpressionAdd, -250, 900)
    spec.set_editor_property("const_b", 0.15)
    mel.connect_material_expressions(spec_mul, "", spec, "A")
    # Normal strength: lerp from flat.
    flat = mel.create_material_expression(m, E.MaterialExpressionConstant3Vector, -600, 350)
    flat.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
    nlerp = mel.create_material_expression(m, E.MaterialExpressionLinearInterpolate, -300, 350)
    mel.connect_material_expressions(flat, "", nlerp, "A")
    mel.connect_material_expressions(nrm, "RGB", nlerp, "B")
    mel.connect_material_expressions(strength, "", nlerp, "Alpha")
    mel.connect_material_property(col, "RGB", E.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(nlerp, "", E.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(rough, "", E.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(spec, "", E.MaterialProperty.MP_SPECULAR)
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
        # Resident at full source resolution: script-built materials carry no texture-streaming data, so
        # streamed textures stayed at low mips and the AMCU pattern smeared (Session 040 capture). Same
        # fix as the weapons (upgrade_weapon_materials.py).
        #
        # The cap was 2048 to hold memory down, but the ADFRC colour sheets are 4096^2, so it was
        # halving every uniform texture on import: the camo the producer reads as "bad textures" was
        # 1024^2 on screen. A cap can only ever downscale, so 4096 leaves the 1024 gloves and 2048
        # normals untouched and costs only what the sheets already occupy (they were resident either
        # way). Session 051, Docs/PLAYER_MODEL_PLAN.md P1.
        tex.set_editor_property("never_stream", True)
        tex.set_editor_property("max_texture_size", MAX_TEXTURE_SIZE)
        eal.save_loaded_asset(tex)
    return tex


def colour_stem(stem):
    if re.search(r"_mc(_|$)", stem):
        for alt in (re.sub(r"_mc(_|$)", r"_amcu\1", stem), re.sub(r"_mc(_|$)", r"_coyote\1", stem)):
            if alt.lower() in index:
                return alt, "amcu-or-coyote variant"
        return None, "multicam: flat coyote"
    return stem, "as authored"


def material_for(slot_name, parent, prefix="MI_ADF_", maf=False):
    # Slot names from adfrc_gear_rig.py: "<texture>__<rvmat>", e.g. crye_g3_shirt_amc_co__crye_g3_shirt.
    m = re.search(r"([A-Za-z0-9]+(?:_[A-Za-z0-9]+)*?)_(co|ca)__", slot_name)
    rv = re.search(r"__([A-Za-z0-9_]+?)(?:_\d+)?(?:\s|$)", slot_name)
    stem = (m.group(1) + "_" + m.group(2)) if m else None
    rvstem = rv.group(1) if rv else (m.group(1) if m else None)
    name = prefix + re.sub(r"[^A-Za-z0-9_]", "_", (m.group(1) if m else slot_name))[:60]
    path = DEST + "/" + name
    # Load first, create only if that genuinely fails. EditorAssetLibrary.does_asset_exist() answers
    # False for these game-feature paths (SSExp_ObjectiveAssault is not mounted in a commandlet) even
    # when the asset is on disk and load_asset resolves it, so branching on it sent every re-run down
    # the create path for an asset that already existed; create_asset then returned None and the run
    # died on the MAF uniform slots, leaving Build/adf_soldier_setup.json with an empty
    # maf_uniform_slots -- which setup_soldiers.py reads. Session 051.
    mi = unreal.load_asset(path)
    if mi is None:
        mi = tools.create_asset(name, DEST, unreal.MaterialInstanceConstant,
                                unreal.MaterialInstanceConstantFactoryNew())
    if mi is None:
        raise RuntimeError("cannot load or create material instance " + path)
    mi.set_editor_property("parent", parent)
    note = "no texture"
    if stem:
        cstem, note = colour_stem(stem)
        if maf and stem.lower() in MAF_SWAP:
            cstem, note = MAF_SWAP[stem.lower()], "MAF green"
        elif maf and stem.lower() in MAF_FLAT:
            cstem, note = None, "MAF flat olive"
        col = texture(cstem) if cstem else None
        if col:
            mel.set_material_instance_texture_parameter_value(mi, "BaseColorMap", col)
        else:
            # No Multicam (ADR-016): a plain coyote finish (Art/Characters/ADF/T_ADF_Coyote.png).
            flat = "T_ADF_Olive" if maf else "T_ADF_Coyote"
            index.setdefault(flat.lower(), os.path.join(ART, flat + ".png"))
            mel.set_material_instance_texture_parameter_value(mi, "BaseColorMap", texture(flat))
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
        if not hard:
            # Cloth: the fabric master reads the SMDI inside a cloth band (see fabric_master).
            mi.set_editor_property("parent", fabric_master())
            for cand in (rvstem + "_smdi", base + "_smdi"):
                sm = texture(cand, masks=True)
                if sm:
                    mel.set_material_instance_texture_parameter_value(mi, "SMDIMap", sm)
                    break
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
            maf = name.startswith("SK_MAF_")
            mi, stem, note = material_for(full + " " + slot, parent, "MI_MAF_" if maf else "MI_ADF_", maf)
            sm.set_editor_property("material_interface", mi)
            mats[i] = sm
            slots.append({"slot": slot, "source": full, "texture": stem, "note": note})
        mesh.set_editor_property("materials", mats)
        # A property set from Python does not dirty the package: save unconditionally, or the
        # imported default (WorldGridMaterial) stays on disk.
        report["meshes"][name] = {"slots": slots, "saved": eal.save_loaded_asset(mesh, False)}
    # MAF wears the same uniform mesh with the green palette: material instances only (applied as
    # the soldier's OpposingMaterialOverrides by setup_soldiers.py, in the uniform's slot order).
    uniform = unreal.load_asset(DEST + "/SK_ADF_Uniform_G3")
    report["maf_uniform_slots"] = []
    for sm in uniform.get_editor_property("materials"):
        slot = str(sm.get_editor_property("material_slot_name"))
        mi, stem, note = material_for(slot, parent, "MI_MAF_", True)
        report["maf_uniform_slots"].append(mi.get_path_name())
    # Proof, not assertion, that the texture cap is not halving anything: source size beside the cap
    # actually set on the asset, for every texture this script imported.
    report["textures"] = []
    halved = 0
    for d in reg.get_assets_by_path(DEST + "/Textures", recursive=True):
        tex = unreal.load_asset(str(d.package_name) + "." + str(d.asset_name))
        if not isinstance(tex, unreal.Texture):
            continue
        try:
            w, h = tex.blueprint_get_size_x(), tex.blueprint_get_size_y()
        except Exception as exc:
            report["textures"].append({"name": str(d.asset_name), "error": str(exc)})
            continue
        cap = int(tex.get_editor_property("max_texture_size") or 0)
        shrunk = bool(cap) and max(w, h) > cap
        halved += int(shrunk)
        report["textures"].append({"name": str(d.asset_name), "size": [w, h],
                                   "max_texture_size": cap, "downscaled": shrunk})
    report["textures_halved"] = halved
    report["ok"] = (all(isinstance(v, dict) and v["saved"] for v in report["meshes"].values())
                    and halved == 0)


try:
    main()
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[ADFSoldier] ok={}".format(report["ok"]))
