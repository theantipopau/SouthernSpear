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
import sys

# does_asset_exist() misses Game Feature assets in a commandlet; see Tools/Unreal/ss_assets.py.
sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Tools", "Unreal"))
from ss_assets import asset_exists  # noqa: E402

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
WEAPONS = ["A88", "A88G", "A89", "A4", "A416", "A25", "A9"]
W = FBX = DEST = None  # set per weapon by main()
SEMI_AUTO = set()
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
    if asset_exists(path):
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
    if asset_exists(path):
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
        mi = unreal.load_asset(mi_path) if asset_exists(mi_path) else tools.create_asset(
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
        mi = unreal.load_asset(mi_path) if asset_exists(mi_path) else tools.create_asset(
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
    rifle mesh is hidden and our static mesh is added in its place.

    Built in place: an existing blueprint is loaded and its SSVisual component updated, never deleted
    and re-created. delete_asset() does not remove it in a commandlet (the file stays, and create_asset
    then returns None for the taken name), which stopped every run on the first weapon (Session 054)."""
    name = "B_SS_" + W + "_Weapon"
    path = DEST + "/" + name
    parent_path = base_of(W)[2]
    parent = unreal.load_class(None, parent_path)
    if parent is None:
        raise RuntimeError("parent class " + parent_path + " did not load for " + W)
    bp = unreal.load_asset(path) if asset_exists(path) else None
    created = bp is None
    if created:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", parent)
        bp = tools.create_asset(name, DEST, unreal.Blueprint, factory)
        if bp is None:
            raise RuntimeError("could not create " + path)
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib_sd = unreal.SubobjectDataBlueprintFunctionLibrary
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    if not handles:
        raise RuntimeError("no components on the blueprint " + path)
    skeletal = None
    visual = None
    for h in handles:
        data = lib_sd.get_data(h)
        obj = lib_sd.get_object_for_blueprint(data, bp)
        if isinstance(obj, unreal.SkeletalMeshComponent):
            skeletal = h
            obj.set_editor_property("hidden_in_game", True)
            obj.set_editor_property("cast_shadow", False)
        elif isinstance(obj, unreal.StaticMeshComponent) and str(lib_sd.get_variable_name(data)) == "SSVisual":
            visual = obj
    reason = "updated in place" if not created else ""
    if visual is None:
        added, reason = sub.add_new_subobject(unreal.AddNewSubobjectParams(
            parent_handle=skeletal or handles[0], new_class=unreal.StaticMeshComponent, blueprint_context=bp))
        sub.rename_subobject(added, unreal.Text("SSVisual"))
        visual = lib_sd.get_object_for_blueprint(lib_sd.get_data(added), bp)
    if visual is None:
        raise RuntimeError("no SSVisual component on " + path + " " + str(reason))
    visual.set_editor_property("static_mesh", mesh)
    # Lyra attaches with -90 yaw (its meshes face +Y); ours faces +X, so cancel it.
    visual.set_editor_property("relative_rotation", unreal.Rotator(roll=0, pitch=0, yaw=90))
    visual.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    eal.save_loaded_asset(bp)
    return step("visual_blueprint", skeletal is not None and visual is not None, "{} (hid Lyra mesh: {}, created: {}) {}".format(
        path, skeletal is not None, created, reason)) and bp


def copy_definition(src, name):
    path = DEST + "/" + name
    if not asset_exists(path):
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


# Semi-automatic rifles (W1): Config/DefaultGame.ini SSWeaponStatsSettings rows with bFullAuto=False that copy
# Lyra's rifle. Lyra's rifle fire ability (GA_Weapon_Fire_Rifle_Auto) repeats while held; its pistol fire
# ability (GA_Weapon_Fire_Pistol) is one shot per press. Found by Tools/Unreal/probe_weapon_fire.py.
LYRA_PISTOL_WID = "/ShooterCore/Weapons/Pistol/WID_Pistol"


def semi_auto_weapons():
    """Weapons whose stats row says bFullAuto=False, read from the config the game reads."""
    ini = os.path.join(PROJECT_DIR, "Config", "DefaultGame.ini")
    with open(ini, encoding="utf-8") as fh:
        text = fh.read()
    return set(re.findall(r"^\+Weapons=\(Weapon=(\w+),[^\n]*bFullAuto=False", text, re.M))


def class_path_in(text, stem):
    """The full object path of the Blueprint class named <stem>..._C inside a property's text form."""
    match = re.search(r"(/[\w/]+/" + stem + r"[\w]*\." + stem + r"[\w]*_C)", text)
    return match.group(1) if match else None


def semi_auto(wid):
    """Give W a copy of its ability sets with the auto fire ability swapped for the pistol's semi-auto one."""
    cdo = unreal.get_default_object(wid.generated_class())
    sets_text = lib.get_property_as_text(cdo, "AbilitySetsToGrant")
    pistol = unreal.load_asset(LYRA_PISTOL_WID)
    pistol_sets = lib.get_property_as_text(unreal.get_default_object(pistol.generated_class()), "AbilitySetsToGrant") if pistol else ""
    semi_path = None
    for set_path in re.findall(r"(/[\w/]+\.[\w]+)", pistol_sets):
        ability_set = unreal.load_asset(set_path)
        text = lib.get_property_as_text(ability_set, "GrantedGameplayAbilities") if ability_set else ""
        semi_path = semi_path or class_path_in(text, "GA_Weapon_Fire_Pistol")
    if not semi_path:
        return step("semi_auto", False, "pistol fire ability not found in {}".format(pistol_sets))

    new_sets_text = sets_text
    swapped = 0
    for set_path in re.findall(r"(/[\w/]+\.[\w]+)", sets_text):
        ability_set = unreal.load_asset(set_path)
        text = lib.get_property_as_text(ability_set, "GrantedGameplayAbilities") if ability_set else ""
        auto_path = class_path_in(text, "GA_Weapon_Fire_Rifle_Auto")
        if not auto_path:
            continue
        name = "AbilitySet_SS_{}_Semi".format(W)
        copy_path = DEST + "/" + name
        if not asset_exists(copy_path):
            eal.duplicate_asset(set_path.split(".")[0], copy_path)
        copy = unreal.load_asset(copy_path)
        ok = copy and lib.set_property_from_text(copy, "GrantedGameplayAbilities", text.replace(auto_path, semi_path))
        if ok:
            eal.save_loaded_asset(copy)
            new_sets_text = new_sets_text.replace(set_path, copy.get_path_name())
            swapped += 1
    if swapped:
        ok = lib.set_property_from_text(cdo, "AbilitySetsToGrant", new_sets_text)
        if ok:
            eal.save_loaded_asset(wid)
    else:
        # Already swapped on an earlier run: the A25's own AbilitySet_SS_A25_Semi no longer holds the
        # rifle auto ability, so the loop above has nothing to replace and swapped stays 0. Reporting
        # that as a failure made every re-run of a working weapon read ok: false (Session 057). Accept
        # the end state instead: does the weapon now grant the semi-auto fire ability?
        final = lib.get_property_as_text(cdo, "AbilitySetsToGrant")
        ok = any(class_path_in(lib.get_property_as_text(ability_set, "GrantedGameplayAbilities")
                               if ability_set else "", "GA_Weapon_Fire_Pistol")
                 for ability_set in (unreal.load_asset(p) for p in re.findall(r"(/[\w/]+\.[\w]+)", final)))
    report.setdefault("semi_auto", {})[W] = {"fire_ability": semi_path, "swapped": swapped, "already_correct": not swapped and ok, "ability_sets": lib.get_property_as_text(cdo, "AbilitySetsToGrant")}
    return step("semi_auto", ok, "{} set(s) fire {} ({})".format(
        swapped or "all", semi_path.split("/")[-1] if semi_path else "-",
        "already correct" if not swapped else "swapped this run"))


def build_one():
    mesh = import_mesh()
    if not mesh:
        return False
    textured_finishes(mesh) if W in SOURCED else finishes(mesh)
    bp = visual_blueprint(mesh)
    wid = equipment_definition(bp) if bp else None
    if wid and W in SEMI_AUTO and base_of(W)[0] == LYRA_WID:
        semi_auto(wid)
    return item_definition(wid) if wid else False


def main():
    global W, FBX, DEST, SEMI_AUTO
    SEMI_AUTO = semi_auto_weapons()
    report["semi_auto_weapons"] = sorted(SEMI_AUTO)
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
