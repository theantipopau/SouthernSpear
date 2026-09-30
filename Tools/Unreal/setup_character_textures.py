# Southern Spear - original character uniforms on the licensed bodies (ADR-016, ADR-021, ADR-042).
#
# Imports the script-generated CMECU / MAF / gear textures, authors four
# original fabric materials around them, and assigns them as cosmetic material
# overrides on B_SS_Soldier's OPPOSING (MAF) parts. Since ADR-042 the friendly
# look is the Quantum body, whose modules carry their own materials (the ADFRC
# camo from setup_quantum_proto.py, authored arms and head), so the friendly
# override list stays empty. The vendor meshes (Fab, L-0016) are not duplicated
# or edited: overrides ride on the character-part components, so appearance is
# ours while the licensed geometry stays untouched (ADR-004).
#
# Idempotent: the Southern Spear materials are rebuilt each run.
# Writes Build/character_materials_setup.json.

import json
import os
import traceback

import unreal
import sys

# does_asset_exist() misses Game Feature assets in a commandlet; see Tools/Unreal/ss_assets.py.
sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Tools", "Unreal"))
from ss_assets import asset_exists  # noqa: E402

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
ART = os.path.join(PROJECT_DIR, "Art", "Characters", "Textures")
REPORT = os.path.join(PROJECT_DIR, "Build", "character_materials_setup.json")

DEST_ROOT = "/SSExp_ObjectiveAssault/Characters"
TEX_DEST = DEST_ROOT + "/Textures"
MAT_DEST = DEST_ROOT + "/Materials"
SOLDIER = DEST_ROOT + "/B_SS_Soldier"

OPPOSING_MESHES = [
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Head",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Hands",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Sweater",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Pants_Military",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Shoes",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Armor_Small",
    "/Game/Modern_Insurgent_7/Mesh/Separate_Parts/SK_Beret",
]

# Texture set -> (base colour, normal, ORM, tiling, roughness scale note)
SETS = {
    "CMECU": ("T_SS_CMECU_Camo_BC", "T_SS_CMECU_Camo_N", "T_SS_CMECU_Camo_ORM", 2.0),
    "MAF": ("T_SS_MAF_Camo_BC", "T_SS_MAF_Camo_N", "T_SS_MAF_Camo_ORM", 2.0),
    "GearTan": ("T_SS_Gear_BC", "T_SS_Gear_N", "T_SS_Gear_ORM", 4.0),
    "GearDark": ("T_SS_GearDark_BC", "T_SS_GearDark_N", "T_SS_GearDark_ORM", 4.0),
}

# Material slot name -> set, for the seven MAF parts.
OPPOSING_SLOTS = {
    "Sweater": "MAF",
    "PantsMilitary": "MAF",
    "Shoes": "GearDark",
    "ArmorSmall": "GearDark",
    "Beret": "GearDark",
}

eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
report = {"ok": False, "textures": {}, "materials": {}, "overrides": {}, "errors": []}


def step(ok, detail=""):
    report.setdefault("steps", []).append({"ok": bool(ok), "detail": str(detail)})
    return ok


def import_texture(stem):
    """Import one PNG and return the texture asset, or None."""
    src = os.path.join(ART, stem + ".png")
    if not os.path.exists(src):
        report["errors"].append("missing source %s" % src)
        return None
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", TEX_DEST)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    tools.import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths") or [])
    if not imported:
        report["errors"].append("import produced nothing for %s" % stem)
        return None
    return unreal.load_asset(imported[0])


def configure_texture(tex, is_normal):
    """Set import settings defensively: names differ between engine versions."""
    notes = []
    try:
        tex.set_editor_property("srgb", not is_normal)
    except Exception as exc:
        notes.append("srgb: %s" % exc)
    try:
        tex.set_editor_property(
            "compression_settings",
            unreal.TextureCompressionSettings.TC_NORMALMAP if is_normal
            else unreal.TextureCompressionSettings.TC_DEFAULT,
        )
    except Exception as exc:
        notes.append("compression: %s" % exc)
    for candidate in ("TF_ANISOTROPIC", "TF_Anisotropic"):
        enum = getattr(unreal.TextureFilter, candidate, None)
        if enum is not None:
            try:
                tex.set_editor_property("filter", enum)
            except Exception as exc:
                notes.append("filter: %s" % exc)
            break
    try:
        eal.save_loaded_asset(tex)
    except Exception as exc:
        notes.append("save: %s" % exc)
    return notes


def build_material(name, bc, nrm, orm, tiling):
    """Author a simple original fabric material: BC + normal + ORM on UV0."""
    path = MAT_DEST + "/" + name
    if asset_exists(path):
        eal.delete_asset(path)
    factory = unreal.MaterialFactoryNew()
    mat = tools.create_asset(name, MAT_DEST, unreal.Material, factory)
    if mat is None:
        report["errors"].append("could not create %s" % path)
        return None

    def expr(cls, x, y, **kw):
        e = mel.create_material_expression(mat, cls, x, y)
        for k, v in kw.items():
            e.set_editor_property(k, v)
        return e

    tc = expr(unreal.MaterialExpressionTextureCoordinate, -1100, 0)
    notes = []

    def tiled_chain(target_x, y, scale):
        mul = expr(unreal.MaterialExpressionMultiply, target_x - 300, y)
        const = expr(unreal.MaterialExpressionConstant, target_x - 300, y + 160, r=scale)
        try:
            mel.connect_material_expressions(tc, "", mul, "A")
            mel.connect_material_expressions(const, "", mul, "B")
        except Exception as exc:
            notes.append("tiling chain: %s" % exc)
        return mul

    for y, (stem, tex, is_normal) in enumerate((
        ("BC", bc, False),
        ("N", nrm, True),
        ("ORM", orm, False),
    )):
        chain = tiled_chain(-800, y * 320 - 320, tiling)
        sample = expr(
            unreal.MaterialExpressionTextureSampleParameter2D, -400, y * 320 - 320,
            parameter_name=stem, texture=tex,
        )
        if is_normal:
            sample.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        try:
            mel.connect_material_expressions(chain, "", sample, "Coordinates")
        except Exception as exc:
            notes.append("%s coords: %s" % (stem, exc))
        if stem == "BC":
            mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
        elif stem == "N":
            mel.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_NORMAL)
        else:
            mel.connect_material_property(sample, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
            mel.connect_material_property(sample, "G", unreal.MaterialProperty.MP_ROUGHNESS)
            mel.connect_material_property(sample, "B", unreal.MaterialProperty.MP_METALLIC)

    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    report["materials"][name] = {"path": path, "notes": notes}
    return mat


def slot_overrides(mesh_path, mapping, mats):
    """Build one inner override array for a mesh, keyed by material slot name."""
    mesh = unreal.load_asset(mesh_path)
    if mesh is None:
        report["errors"].append("mesh missing %s" % mesh_path)
        return []
    out = []
    for sm in mesh.get_editor_property("materials"):
        name = str(sm.get_editor_property("material_slot_name"))
        key = mapping.get(name)
        out.append(mats.get(key) if key else None)
    return out


def main():
    for key, (bc_stem, n_stem, orm_stem, tiling) in SETS.items():
        loaded = {}
        tex_notes = {}
        for role, stem, is_normal in (("BC", bc_stem, False), ("N", n_stem, True), ("ORM", orm_stem, False)):
            tex = import_texture(stem)
            if tex:
                tex_notes[role] = configure_texture(tex, is_normal)
                loaded[role] = tex
        report["texture_notes"] = report.get("texture_notes", {})
        report["texture_notes"][key] = tex_notes
        report["textures"][key] = {k: (v.get_path_name() if v else None) for k, v in loaded.items()}
        if len(loaded) == 3:
            build_material("M_SS_%s" % key, loaded["BC"], loaded["N"], loaded["ORM"], tiling)
    step(all(report["materials"]), "materials: %s" % ", ".join(sorted(report["materials"])))

    mats = {k: unreal.load_asset(MAT_DEST + "/M_SS_" + k) for k in SETS}
    mats = {k: v for k, v in mats.items() if v}
    step(len(mats) == len(SETS), "resolved %d/%d materials" % (len(mats), len(SETS)))

    soldier = unreal.load_asset(SOLDIER)
    if soldier is None:
        report["errors"].append("missing %s" % SOLDIER)
        return
    cdo = unreal.get_default_object(soldier.generated_class())

    def wrap(slots):
        s = unreal.SSPartMaterialOverride()
        s.set_editor_property("slots", slots)
        return s

    opposing = [wrap(slot_overrides(p, OPPOSING_SLOTS, mats)) for p in OPPOSING_MESHES]
    # Friendly overrides belong to setup_soldiers.py since ADR-042 (the ADFRC camo on the
    # Quantum modules, R-91): this pass must not touch friendly_material_overrides, or it
    # would wipe the camo off the friendly look.
    cdo.set_editor_property("opposing_material_overrides", opposing)
    report["overrides"] = {
        "friendly": "left to setup_soldiers.py (ADR-042)",
        "opposing": [[m.get_path_name() if m else None for m in r.get_editor_property("slots")] for r in opposing],
    }
    unreal.BlueprintEditorLibrary.compile_blueprint(soldier)
    step(eal.save_loaded_asset(soldier), "B_SS_Soldier saved")


try:
    main()
    report["ok"] = all(s["ok"] for s in report["steps"]) and not report["errors"]
except Exception:
    report["errors"].append(traceback.format_exc())
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[CharacterMaterials] ok={} errors={}".format(report["ok"], len(report["errors"])))
