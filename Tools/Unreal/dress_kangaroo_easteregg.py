# Southern Spear - the kangaroo easter egg (ENV-004, L-0024).
#
# 1. Imports Content/kangaroo/textures (7 JPG maps) to
#    /Game/Art/Environment/Kangaroo/Textures.
# 2. Imports Content/kangaroo/source/source/kangaroo.FBX to
#    /Game/Art/Environment/Kangaroo/SM_Kangaroo as one static mesh.
# 3. Authors MI_SS_Kangaroo, an instance of the project's parameterised
#    M_SS_ScanPBR master (same intake pattern as the Ravenshoe props, M-008l).
#    The vendor OBJ MTL points at absolute D:\ paths, so the maps are wired by
#    hand: -0277 is the main body map (KGROmain), -0278 the underside (KGROsup).
# 4. Measures the imported mesh's real bounds and derives a uniform scale so
#    the animal stands ~1.5 m tall - a big eastern grey buck - instead of
#    trusting the vendor's units. The derived scale is written to the report.
# 5. Places two individuals per map on Red Gum Station and Dry River, each
#    anchored to an existing dressing tree (1.2 m south of its canopy edge),
#    terrain-snapped by line trace, collision OFF (decoration only: never
#    blocks nav, movement or shots), labels SS_EasterEgg_Kangaroo_* so reruns
#    remove exactly what they placed (idempotent), folder EasterEgg.
#    Each map is saved before the next is loaded.
#
# Run:
#   UnrealEditor-Cmd.exe <uproject> -run=pythonscript -nosplash -nosound \
#     -ExecutePythonScript=Tools/Unreal/dress_kangaroo_easteregg.py
#
# Writes Build/kangaroo_easteregg_report.json.
import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "kangaroo_easteregg_report.json")

SRC_FBX = os.path.join(PROJECT_DIR, "Content", "kangaroo", "source", "source", "kangaroo.FBX")
SRC_TEX = os.path.join(PROJECT_DIR, "Content", "kangaroo", "textures")
DEST = "/Game/Art/Environment/Kangaroo"
TEX_DEST = DEST + "/Textures"
MESH = DEST + "/SM_Kangaroo"
MASTER = "/Game/Art/Environment/Fab/M_SS_ScanPBR"
MATERIAL = DEST + "/MI_SS_Kangaroo"
PREFIX = "SS_EasterEgg_Kangaroo_"

TARGET_HEIGHT_CM = 150.0  # a big eastern grey kangaroo

# (map, [(anchor tree label, yaw deg, note), ...]) - the second spot per map is
# a tree from another dressing line so the two animals never sit together.
PLACEMENTS = [
    ("/Game/Maps/L_RedGum_01", [
        ("SS_RedGum_Dress_v1_TreeLine_00_02", 0, "1", "paddock treeline"),
        ("SS_RedGum_Dress_v1_TreeLine_02_03", 200, "2", "second paddock treeline"),
    ]),
    ("/Game/Maps/L_DryRiver_01", [
        ("SS_RA_Tree#7", 90, "1", "the 8th SS_RA_Tree in position order"),
        ("SS_RA_Tree#21", 305, "2", "the 22nd SS_RA_Tree in position order"),
    ]),
]

eal = unreal.EditorAssetLibrary
ats = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
report = {"ok": False, "steps": [], "errors": [], "warnings": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def import_textures():
    os.makedirs(os.path.join(PROJECT_DIR, "Build"), exist_ok=True)
    eal.make_directory(TEX_DEST)
    tasks = []
    for name in sorted(os.listdir(SRC_TEX)):
        if not name.lower().endswith((".jpg", ".jpeg", ".tga", ".png")):
            continue
        task = unreal.AssetImportTask()
        task.filename = os.path.join(SRC_TEX, name)
        task.destination_path = TEX_DEST
        task.automated = True
        task.replace_existing = True
        task.save = True
        tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    done = [os.path.splitext(os.path.basename(t.filename))[0] for t in tasks
            if eal.does_asset_exist(TEX_DEST + "/" + os.path.splitext(os.path.basename(t.filename))[0])]
    return done


def purge_piece_import():
    """Interchange split the FBX into 01kangaroo..24 + KGRO* materials; remove them."""
    purged = 0
    if not eal.does_directory_exist(DEST):
        return 0
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = ar.get_assets_by_path(unreal.Name(DEST), recursive=False)
    for a in assets:
        name = str(a.asset_name)
        if name.startswith(("01kangaroo", "KGRO")):
            if eal.delete_asset(DEST + "/" + name):
                purged += 1
    return purged


def import_mesh():
    if eal.does_asset_exist(MESH):
        return True
    try:
        ui = unreal.FbxImportUI()
        ui.import_mesh = True
        ui.import_textures = False
        ui.import_materials = False
        ui.import_as_skeletal = False
        ui.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
        ui.static_mesh_import_data.combine_meshes = True
        ui.static_mesh_import_data.convert_scene = True
        ui.static_mesh_import_data.import_uniform_scale = 1.0
        options = ui
    except Exception as exc:
        report["warnings"].append("FbxImportUI unavailable (%s); using Interchange default" % exc)
        options = None
    task = unreal.AssetImportTask()
    task.filename = SRC_FBX
    task.destination_path = DEST
    task.destination_name = "SM_Kangaroo"
    task.automated = True
    task.replace_existing = False
    task.save = True
    if options is not None:
        task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return eal.does_asset_exist(MESH)


def load_texture(name):
    path = TEX_DEST + "/" + name
    return eal.load_asset(path) if eal.does_asset_exist(path) else None


def author_material():
    """MI_SS_Kangaroo under the project's ScanPBR master; body map -0277."""
    ump = unreal.MaterialEditingLibrary
    if eal.does_asset_exist(MATERIAL):
        mat = eal.load_asset(MATERIAL)
    else:
        master = eal.load_asset(MASTER)
        if not master:
            return None
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "MI_SS_Kangaroo", DEST, unreal.MaterialInstanceConstant, factory)
        if not mat:
            return None
        try:
            ump.set_material_instance_parent(mat, master)
        except Exception as exc:
            report["warnings"].append("parent set: %s" % exc)
    for param, name in (("BaseColor", "znzmoModel-1132355448-0277"),
                        ("Normal", "znzmoModel-1132355448-0278")):
        tex = load_texture(name)
        if tex is None:
            report["warnings"].append("missing texture %s for %s" % (name, param))
            continue
        try:
            ump.set_material_instance_texture_parameter_value(mat, param, tex)
        except Exception as exc:
            report["warnings"].append("param %s: %s" % (param, exc))
    eal.save_loaded_asset(mat)
    return mat


def scale_for(mesh):
    """Uniform scale that stands the mesh's tallest axis at TARGET_HEIGHT_CM."""
    try:
        bounds = mesh.get_bounds()
        size = bounds.box_extent * 2.0
        tallest = max(size.x, size.y, size.z)
        if tallest <= 0:
            return 1.0
        s = TARGET_HEIGHT_CM / tallest
        report["source_bounds_cm"] = [round(size.x, 1), round(size.y, 1), round(size.z, 1)]
        report["derived_scale"] = round(s, 4)
        return s
    except Exception as exc:
        report["warnings"].append("bounds measure failed: %s" % exc)
        return 1.0


def ground_z(world, x, y):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, 50000), unreal.Vector(x, y, -50000),
        unreal.TraceTypeQuery.ECC_VISIBILITY, True, [],
        unreal.DrawDebugTrace.NONE, True)
    if hit is None:
        return None
    hr = hit[1] if isinstance(hit, (list, tuple)) else hit
    try:
        d = hr.to_dict()
        p = d.get("impact_point") or d.get("location")
        return p.z if p is not None else None
    except Exception:
        return None


def find_actor(world, label):
    """Exact label, or Base#N = the Nth (0-based) actor starting with Base,
    ordered by position so identical labels still resolve to distinct trees."""
    if "#" in label:
        base, idx = label.split("#")
        actors = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
                  if a.get_actor_label().startswith(base)]
        actors.sort(key=lambda a: (a.get_actor_location().x, a.get_actor_location().y))
        try:
            return actors[int(idx)]
        except IndexError:
            report["warnings"].append("%s: only %d matches" % (label, len(actors)))
            return None
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        if actor.get_actor_label() == label:
            return actor
    return None


def remove_owned(world):
    n = 0
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        if actor.get_actor_label().startswith(PREFIX):
            ats.destroy_actor(actor)
            n += 1
    return n


def place(world, mesh, material, anchor_label, yaw, egg_name, note, scale):
    tree = find_actor(world, anchor_label)
    if not tree:
        report["warnings"].append("anchor tree %s not found (%s)" % (anchor_label, note))
        return False
    origin, extent = tree.get_actor_bounds(False)
    x = origin.x
    y = origin.y - min(extent.x, extent.y) - 120.0  # 1.2 m south of the canopy edge
    # The tree's pivot z, not a trace: the dressing passes spawn trees at
    # terrain height, and a downward visibility trace at the trunk returns the
    # CANOPY top on trees whose collision is on - which floated the first
    # kangaroos up in the branches (Session 084 defect, producer screenshot).
    z = tree.get_actor_location().z
    actor = ats.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z + 1.0),
                                       unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    if not actor:
        return False
    actor.static_mesh_component.set_static_mesh(mesh)
    for slot in range(actor.static_mesh_component.get_num_materials()):
        actor.static_mesh_component.set_material(slot, material)
    actor.set_actor_label(PREFIX + egg_name)
    try:
        actor.set_folder_path(unreal.Name("EasterEgg"))
    except Exception:
        pass
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    actor.set_actor_enable_collision(False)
    return True


def save_level():
    try:
        return bool(unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
    except Exception:
        return bool(unreal.EditorLoadingAndSavingUtils.save_current_level())


def main():
    if not step("master_material", eal.does_asset_exist(MASTER), MASTER):
        return
    textures = import_textures()
    step("import_textures", len(textures) >= 5, "%d maps imported" % len(textures))
    purged = purge_piece_import()
    if purged:
        report["purged_piece_import"] = purged
    if not step("import_mesh", import_mesh(), MESH):
        return
    mesh = eal.load_asset(MESH)
    if not step("load_mesh", mesh is not None, MESH):
        return
    material = author_material()
    if not step("author_material", material is not None, MATERIAL):
        return
    scale = scale_for(mesh)

    placed_total = 0
    for map_path, spots in PLACEMENTS:
        world = unreal.EditorLoadingAndSavingUtils.load_map(map_path)
        if not step("load_map", world is not None, map_path):
            return
        removed = remove_owned(world)
        placed = 0
        for anchor, yaw, egg_name, note in spots:
            if place(world, mesh, material, anchor, yaw, egg_name, note, scale):
                placed += 1
                placed_total += 1
        report.setdefault("by_map", {})[map_path] = "%d placed (%d previous removed)" % (placed, removed)
        step("place_" + map_path.rsplit("/", 1)[-1], placed == len(spots),
             "%d/%d under named trees" % (placed, len(spots)))
        saved = save_level()
        step("save_" + map_path.rsplit("/", 1)[-1], saved, map_path)
    step("place_kangaroos_total", placed_total == 4, "placed %d/4 (2 per map)" % placed_total)
    report["ok"] = all(s["ok"] for s in report["steps"]) and placed_total == 4


try:
    main()
except Exception:
    report["errors"].append(traceback.format_exc())
    unreal.log_error("[KangarooEasterEgg] raised:\n" + traceback.format_exc())
finally:
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    unreal.log("[KangarooEasterEgg] complete ok={} report={}".format(report["ok"], REPORT))
