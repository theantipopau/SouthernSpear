# Southern Spear - A88 rifle into the game (ADR-016, ADR-019, ADR-020).
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
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
FBX = os.path.join(PROJECT_DIR, "Art", "Weapons", "A88", "SM_A88.fbx")
REPORT = os.path.join(PROJECT_DIR, "Build", "a88_setup.json")
DEST = "/SSExp_ObjectiveAssault/Weapons/A88"
MAT_DIR = "/SSExp_ObjectiveAssault/Materials"
LYRA_WID = "/ShooterCore/Weapons/Rifle/WID_Rifle"
LYRA_ID = "/ShooterCore/Weapons/Rifle/ID_Rifle"
LYRA_VISUAL = "/ShooterCore/Weapons/Rifle/B_Rifle.B_Rifle_C"

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
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def import_mesh():
    task = unreal.AssetImportTask()
    task.filename = FBX
    task.destination_path = DEST
    task.destination_name = "SM_A88"
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
    mesh = unreal.load_asset(DEST + "/SM_A88")
    if mesh:
        box = mesh.get_bounding_box()
        size = box.max - box.min
        report["mesh_size_cm"] = [round(size.x, 1), round(size.y, 1), round(size.z, 1)]
        report["muzzle_socket"] = mesh.find_socket("Muzzle") is not None
    return step("import_mesh", mesh is not None, report.get("mesh_size_cm")) and mesh


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
        mi_path = DEST + "/MI_A88_" + key
        mi = unreal.load_asset(mi_path) if eal.does_asset_exist(mi_path) else tools.create_asset(
            "MI_A88_" + key, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property("parent", parent)
        f = FINISHES[key]
        mel.set_material_instance_vector_parameter_value(mi, "BaseColor", unreal.LinearColor(*f["BaseColor"], 1.0))
        mel.set_material_instance_scalar_parameter_value(mi, "Roughness", f["Roughness"])
        mel.set_material_instance_scalar_parameter_value(mi, "Metallic", f["Metallic"])
        eal.save_loaded_asset(mi)
        mesh.set_material(i, mi)
        assigned.append(name)
    eal.save_loaded_asset(mesh)
    return step("finishes", len(assigned) == len(FINISHES), assigned)


def visual_blueprint(mesh):
    path = DEST + "/B_SS_A88"
    if eal.does_asset_exist(path):
        bp = unreal.load_asset(path)
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.SSHeldItemVisualActor)
        bp = tools.create_asset("B_SS_A88", DEST, unreal.Blueprint, factory)
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property("visual_mesh", mesh)
    # Lyra attaches with -90 yaw (its meshes face +Y); ours faces +X, so cancel it.
    cdo.set_editor_property("mesh_offset", unreal.Transform(rotation=unreal.Rotator(roll=0, pitch=0, yaw=90)))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    eal.save_loaded_asset(bp)
    return step("visual_blueprint", bp is not None, path) and bp


def copy_definition(src, name):
    path = DEST + "/" + name
    if not eal.does_asset_exist(path):
        eal.duplicate_asset(src, path)
    return unreal.load_asset(path)


def equipment_definition(visual_bp):
    wid = copy_definition(LYRA_WID, "WID_SS_A88")
    cdo = unreal.get_default_object(wid.generated_class())
    text = lib.get_property_as_text(cdo, "ActorsToSpawn")
    ours = visual_bp.generated_class().get_path_name()
    new = text.replace(LYRA_VISUAL, ours)
    ok = new != text or ours in text
    ok = ok and lib.set_property_from_text(cdo, "ActorsToSpawn", new)
    report["actors_to_spawn"] = lib.get_property_as_text(cdo, "ActorsToSpawn")
    eal.save_loaded_asset(wid)
    return step("equipment_definition", ok, report["actors_to_spawn"]) and wid


def item_definition(wid):
    item = copy_definition(LYRA_ID, "ID_SS_A88")
    cdo = unreal.get_default_object(item.generated_class())
    lib.set_property_from_text(cdo, "DisplayName", 'NSLOCTEXT("SSWeapons", "A88", "A88")')
    ours = wid.generated_class()
    pointed = 0
    for fragment in cdo.get_editor_property("fragments"):
        if fragment and "EquippableItem" in fragment.get_class().get_name():
            if lib.set_property_from_text(fragment, "EquipmentDefinition", ours.get_path_name()):
                pointed += 1
    eal.save_loaded_asset(item)
    report["item_class"] = item.generated_class().get_path_name()
    return step("item_definition", pointed == 1, "{} equippable fragment(s) -> {}".format(pointed, ours.get_name()))


def main():
    mesh = import_mesh()
    if not mesh:
        return False
    finishes(mesh)
    bp = visual_blueprint(mesh)
    wid = equipment_definition(bp) if bp else None
    return item_definition(wid) if wid else False


try:
    ok = main()
    report["ok"] = bool(ok) and all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=2)
unreal.log("[A88] result ok={} -> {}".format(report["ok"], REPORT))
