# Southern Spear - original weapons into the game (ADR-016, ADR-019, ADR-020).
#
# For each weapon in WEAPONS (built by Tools/Blender/<name>_*.py into Art/Weapons/<NAME>/):
#
# 1. Imports Art/Weapons/A88/SM_A88.fbx (built by Tools/Blender/a88_rifle.py).
# 2. Creates a flat PBR master material and palette material instances, and
#    assigns them by slot name (Polymer, Metal, Glass).
# 3. Creates B_SS_A88 (ASSHeldItemVisualActor) showing the mesh.
# 4. Creates WID_SS_A88 / ID_SS_A88 as copies of Lyra's rifle definitions,
#    pointed at B_SS_A88. Lyra's rifle behaviour (abilities, animation
#    layers, fire and reload) is reused unchanged; Lyra's own assets are not
#    modified.
# The starting loadout itself is data: Config/DefaultGame.ini
# [/Script/SouthernSpearLyraBridge.SSLoadoutSettings].
#
# Idempotent. Writes Build/a88_setup.json.

import json
import re
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
WEAPONS = ["A88", "A88G", "A89", "A4", "A416", "A25", "A9"]
W = FBX = DEST = None  # set per weapon by main()
REPORT = os.path.join(PROJECT_DIR, "Build", "weapons_setup.json")
MAT_DIR = "/SSExp_ObjectiveAssault/Materials"
LYRA_WID = "/ShooterCore/Weapons/Rifle/WID_Rifle"
LYRA_ID = "/ShooterCore/Weapons/Rifle/ID_Rifle"
LYRA_VISUAL = "/ShooterCore/Weapons/Rifle/B_Rifle.B_Rifle_C"

# Weapons built from a supplied textured model instead of a Blender script:
# FBX (from Tools/Blender/<name>_sourced.py) and one colour atlas per slot.
SOURCED = {
    # ADFRC models (L-0021) via Tools/Blender/adfrc_weapon.py: FBX + manifest of
    # slot -> extracted colour/normal PNGs. Renamed to A-series (ADR-016).
    "A88": {"manifest": os.path.join("Art", "Weapons", "A88", "ADFRC", "manifest.json")},
    "A4": {"manifest": os.path.join("Art", "Weapons", "A4", "ADFRC", "manifest.json")},
    "A9": {"manifest": os.path.join("Art", "Weapons", "A9", "ADFRC", "manifest.json")},
    "A88G": {"manifest": os.path.join("Art", "Weapons", "A88G", "ADFRC", "manifest.json")},
    "A89": {"manifest": os.path.join("Art", "Weapons", "A89", "ADFRC", "manifest.json")},
    "A416": {"manifest": os.path.join("Art", "Weapons", "A416", "ADFRC", "manifest.json")},
    "A25": {"manifest": os.path.join("Art", "Weapons", "A25", "ADFRC", "manifest.json")},
}

# Lyra definitions each weapon copies (behaviour, abilities, animation layers).
LYRA_BASE = {
    "A9": ("/ShooterCore/Weapons/Pistol/WID_Pistol", "/ShooterCore/Weapons/Pistol/ID_Pistol",
           "/ShooterCore/Weapons/Pistol/B_Pistol.B_Pistol_C"),
}


def base_of(name):
    return LYRA_BASE.get(name, (LYRA_WID, LYRA_ID, LYRA_VISUAL))


def load_manifest(name):
    with open(os.path.join(PROJECT_DIR, SOURCED[name]["manifest"]), encoding="utf-8") as fh:
        return json.load(fh)


# Palette-derived finishes (Site/styles.css family): olive-drab polymer, dark metal, tinted glass.
FINISHES = {
    "Polymer": {"BaseColor": (0.060, 0.063, 0.042), "Roughness": 0.72, "Metallic": 0.0},
    "Metal": {"BaseColor": (0.018, 0.019, 0.018), "Roughness": 0.42, "Metallic": 0.85},
    "Glass": {"BaseColor": (0.020, 0.045, 0.040), "Roughness": 0.08, "Metallic": 0.3},
}

eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.SSObjectivesEditorLibrary
report = {"ok": False, "steps": [], "errors": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": "{}:{}".format(W, name), "ok": bool(ok), "detail": str(detail)})
    return ok


def import_mesh():
    task = unreal.AssetImportTask()
    task.filename = FBX
    task.destination_path = DEST
    task.destination_name = "SM_" + W
    task.replace_existing = True
    task.automated = True
    task.save = True
    ui = unreal.FbxImportUI()
    ui.import_mesh = True
    ui.import_as_skeletal = False
    ui.import_materials = False
    ui.import_textures = False
    ui.import_animations = False
    ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    ui.static_mesh_import_data.combine_meshes = True
    ui.static_mesh_import_data.auto_generate_collision = False
    task.options = ui
    tools.import_asset_tasks([task])
    mesh = unreal.load_asset(DEST + "/SM_" + W)
    if mesh:
        box = mesh.get_bounding_box()
        size = box.max - box.min
        report.setdefault("mesh_size_cm", {})[W] = [round(size.x, 1), round(size.y, 1), round(size.z, 1)]
        report.setdefault("muzzle_socket", {})[W] = mesh.find_socket("Muzzle") is not None
    return step("import_mesh", mesh is not None, report["mesh_size_cm"][W]) and mesh


def master_material():
    path = MAT_DIR + "/M_SS_FlatPBR"
    if eal.does_asset_exist(path):
        return unreal.load_asset(path)
    mat = tools.create_asset("M_SS_FlatPBR", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    col = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 0)
    col.set_editor_property("parameter_name", "BaseColor")
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -400, 200)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.6)
    metal = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -400, 300)
    metal.set_editor_property("parameter_name", "Metallic")
    mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    return mat


def textured_master():
    path = MAT_DIR + "/M_SS_TexturedPBR"
    if eal.does_asset_exist(path):
        return unreal.load_asset(path)
    mat = tools.create_asset("M_SS_TexturedPBR", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    tex = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -500, 0)
    tex.set_editor_property("parameter_name", "BaseColorMap")
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -400, 250)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.55)
    metal = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -400, 350)
    metal.set_editor_property("parameter_name", "Metallic")
    metal.set_editor_property("default_value", 0.35)
    mel.connect_material_property(tex, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    return mat


def import_texture(path, name):
    task = unreal.AssetImportTask()
    task.filename = path if os.path.isabs(path) else os.path.join(PROJECT_DIR, path)
    task.destination_path = DEST
    task.destination_name = name
    task.replace_existing = True
    task.automated = True
    task.save = True
    tools.import_asset_tasks([task])
    return unreal.load_asset(DEST + "/" + name)


def textured_finishes(mesh):
    """One MI per slot from the manifest's colour texture; slots without a
    texture fall back to the flat Metal finish."""
    parent = textured_master()
    flat_parent = master_material()
    textures = load_manifest(W)["textures"]
    slots = mesh.get_editor_property("static_materials")
    assigned = []
    for i, slot in enumerate(slots):
        name = str(slot.material_slot_name)
        entry = textures.get(name) or textures.get(name.lower()) or {}
        mi_path = DEST + "/MI_" + W + "_" + name
        mi = unreal.load_asset(mi_path) if eal.does_asset_exist(mi_path) else tools.create_asset(
            "MI_" + W + "_" + name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        if entry.get("colour"):
            mi.set_editor_property("parent", parent)
            tex = import_texture(entry["colour"], "T_" + W + "_" + name)
            mel.set_material_instance_texture_parameter_value(mi, "BaseColorMap", tex)
        else:
            mi.set_editor_property("parent", flat_parent)
            f = FINISHES["Metal"]
            mel.set_material_instance_vector_parameter_value(mi, "BaseColor", unreal.LinearColor(*f["BaseColor"], 1.0))
            mel.set_material_instance_scalar_parameter_value(mi, "Roughness", f["Roughness"])
            mel.set_material_instance_scalar_parameter_value(mi, "Metallic", f["Metallic"])
        eal.save_loaded_asset(mi)
        mesh.set_material(i, mi)
        assigned.append(name)
    eal.save_loaded_asset(mesh)
    return step("textured_finishes", len(assigned) == len(slots), assigned)


def finishes(mesh):
    parent = master_material()
    step("master_material", parent is not None)
    slots = mesh.get_editor_property("static_materials")
    assigned = []
    for i, slot in enumerate(slots):
        name = str(slot.material_slot_name)
        key = next((k for k in FINISHES if name.startswith(k)), None)
        if not key:
            continue
        mi_path = DEST + "/MI_" + W + "_" + key
        mi = unreal.load_asset(mi_path) if eal.does_asset_exist(mi_path) else tools.create_asset(
            "MI_" + W + "_" + key, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property("parent", parent)
        f = FINISHES[key]
        mel.set_material_instance_vector_parameter_value(mi, "BaseColor", unreal.LinearColor(*f["BaseColor"], 1.0))
        mel.set_material_instance_scalar_parameter_value(mi, "Roughness", f["Roughness"])
        mel.set_material_instance_scalar_parameter_value(mi, "Metallic", f["Metallic"])
        eal.save_loaded_asset(mi)
        mesh.set_material(i, mi)
        assigned.append(name)
    eal.save_loaded_asset(mesh)
    return step("finishes", len(assigned) == len(slots) and assigned, assigned)


def visual_blueprint(mesh):
    """B_SS_<W>_Weapon: a child of Lyra's B_Rifle, so everything Lyra's weapon
    abilities expect from the weapon actor (the reload in particular only works
    with a B_Rifle-derived actor, Session 024) is inherited unchanged. Lyra's
    rifle mesh is hidden and our static mesh is added in its place."""
    name = "B_SS_" + W + "_Weapon"
    path = DEST + "/" + name
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.load_class(None, base_of(W)[2]))
    bp = tools.create_asset(name, DEST, unreal.Blueprint, factory)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib_sd = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    skeletal = None
    for h in handles:
        data = lib_sd.get_data(h)
        obj = lib_sd.get_object_for_blueprint(data, bp)
        if isinstance(obj, unreal.SkeletalMeshComponent):
            skeletal = h
            obj.set_editor_property("hidden_in_game", True)
            obj.set_editor_property("cast_shadow", False)
    added, reason = sub.add_new_subobject(unreal.AddNewSubobjectParams(
        parent_handle=skeletal or handles[0], new_class=unreal.StaticMeshComponent, blueprint_context=bp))
    sub.rename_subobject(added, unreal.Text("SSVisual"))
    visual = lib_sd.get_object_for_blueprint(lib_sd.get_data(added), bp)
    visual.set_editor_property("static_mesh", mesh)
    # Lyra attaches with -90 yaw (its meshes face +Y); ours faces +X, so cancel it.
    visual.set_editor_property("relative_rotation", unreal.Rotator(roll=0, pitch=0, yaw=90))
    visual.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    eal.save_loaded_asset(bp)
    return step("visual_blueprint", skeletal is not None and visual is not None, "{} (hid Lyra mesh: {}) {}".format(
        path, skeletal is not None, reason)) and bp


def copy_definition(src, name):
    path = DEST + "/" + name
    if not eal.does_asset_exist(path):
        eal.duplicate_asset(src, path)
    return unreal.load_asset(path)


def equipment_definition(visual_bp):
    wid = copy_definition(base_of(W)[0], "WID_SS_" + W)
    cdo = unreal.get_default_object(wid.generated_class())
    text = lib.get_property_as_text(cdo, "ActorsToSpawn")
    ours = visual_bp.generated_class().get_path_name()
    new = re.sub(r'ActorToSpawn="[^"]*"', 'ActorToSpawn="{}"'.format(ours), text, count=1)
    ok = ours in new
    ok = ok and lib.set_property_from_text(cdo, "ActorsToSpawn", new)
    report.setdefault("actors_to_spawn", {})[W] = lib.get_property_as_text(cdo, "ActorsToSpawn")
    eal.save_loaded_asset(wid)
    return step("equipment_definition", ok, report["actors_to_spawn"][W]) and wid


def item_definition(wid):
    item = copy_definition(base_of(W)[1], "ID_SS_" + W)
    cdo = unreal.get_default_object(item.generated_class())
    lib.set_property_from_text(cdo, "DisplayName", 'NSLOCTEXT("SSWeapons", "{0}", "{0}")'.format(W))
    ours = wid.generated_class()
    pointed = 0
    for fragment in cdo.get_editor_property("fragments"):
        if fragment and "EquippableItem" in fragment.get_class().get_name():
            if lib.set_property_from_text(fragment, "EquipmentDefinition", ours.get_path_name()):
                pointed += 1
    eal.save_loaded_asset(item)
    report.setdefault("item_class", {})[W] = item.generated_class().get_path_name()
    return step("item_definition", pointed == 1, "{} equippable fragment(s) -> {}".format(pointed, ours.get_name()))


def build_one():
    mesh = import_mesh()
    if not mesh:
        return False
    textured_finishes(mesh) if W in SOURCED else finishes(mesh)
    bp = visual_blueprint(mesh)
    wid = equipment_definition(bp) if bp else None
    return item_definition(wid) if wid else False


def main():
    global W, FBX, DEST
    results = []
    for name in WEAPONS:
        W = name
        FBX = load_manifest(name)["fbx"] if name in SOURCED else             os.path.join(PROJECT_DIR, "Art", "Weapons", name, "SM_" + name + ".fbx")
        DEST = "/SSExp_ObjectiveAssault/Weapons/" + name
        results.append(bool(build_one()))
    return all(results)


try:
    ok = main()
    report["ok"] = bool(ok) and all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=2)
unreal.log("[Weapons] result ok={} -> {}".format(report["ok"], REPORT))
