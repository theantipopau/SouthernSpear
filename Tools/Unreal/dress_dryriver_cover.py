# Southern Spear - Dry River cover as Rural Australia assets (replaces the greybox shapes).
#
# Tools/Blender/dryriver_blockout.py now exports the designed cover (rocks,
# trees, scrub, the north-south fence) as SS_MAP_DryRiver_01_Cover.csv instead
# of baking low-poly shapes into the terrain mesh. This pass:
#   1. reimports the terrain FBX (now cover-free) with the level builder's settings;
#   2. places a Rural Australia mesh at every cover row, scaled to the greybox
#      size so the cover rules in MAPS_DRYRIVER.md still hold;
#   3. replaces the greybox fence and the dressing fence (SS_Dressing_FenceRail /
#      FencePost boxes) with the pack's posts and wire, collision off (ADR-022).
# Idempotent (removes its own SS_RA_Cover_* actors first). Run build_dryriver_nav.py
# and layout_spawns.py afterwards. Report: Build/dryriver_cover_report.json.

import csv
import json
import math
import os
import random
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MAP = "/Game/Maps/L_DryRiver_01"
FBX = os.path.join(PROJECT_DIR, "Content", "Art", "Blockout", "SS_MAP_DryRiver_01.fbx")
CSV = os.path.join(PROJECT_DIR, "Content", "Art", "Blockout", "SS_MAP_DryRiver_01_Cover.csv")
REPORT = os.path.join(PROJECT_DIR, "Build", "dryriver_cover_report.json")
RA = "/Game/RuralAustralia/StaticMeshes"
POST = RA + "/Props/Fence_01/SM_Fence_02"        # one post, 1.4 m
WIRE = RA + "/Props/Fence_01/SM_Fence_Wires_01"  # a 4 m run of wire along +X from a post
WIRE_SPAN = 400.0
report = {"ok": False, "placed": {}, "fence_posts": 0, "hidden_dressing": 0, "errors": []}
eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def meshes(path, keys):
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    out = []
    for d in reg.get_assets_by_path(path, recursive=True):
        if str(d.asset_class_path.asset_name) == "StaticMesh" and any(k in str(d.asset_name) for k in keys):
            out.append(unreal.load_asset(str(d.package_name)))
    return [m for m in out if m]


def extent(mesh):
    b = mesh.get_bounding_box()
    return b.max - b.min


def reimport_terrain():
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", FBX)
    task.set_editor_property("destination_path", "/Game/Art/Blockout")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", True)
    opts.set_editor_property("import_as_skeletal", False)
    opts.set_editor_property("import_animations", False)
    opts.set_editor_property("import_materials", False)
    opts.set_editor_property("import_textures", False)
    smi = opts.get_editor_property("static_mesh_import_data")
    smi.set_editor_property("combine_meshes", True)
    smi.set_editor_property("auto_generate_collision", False)
    task.set_editor_property("options", opts)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset("/Game/Art/Blockout/SS_MAP_DryRiver_01")
    body = mesh.get_editor_property("body_setup") if mesh else None
    if body:
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        eal.save_loaded_asset(mesh)
    report["terrain_reimported"] = mesh is not None


def place_fence(a, b, posts_done, label):
    """Posts every <= 4 m from a to b with the wire between them; posts shared
    with a neighbouring run are placed once. No collision (ADR-022)."""
    post, wire = unreal.load_asset(POST), unreal.load_asset(WIRE)
    d = b - a
    d.z = 0
    length = d.length()
    if length < 50 or not post or not wire:
        return 0
    n = max(1, int(math.ceil(length / WIRE_SPAN)))
    step = length / n
    yaw = math.degrees(math.atan2(d.y, d.x))
    placed = 0
    for i in range(n + 1):
        p = a + d * (i / n)
        key = (round(p.x / 50), round(p.y / 50))
        if key not in posts_done:
            posts_done.add(key)
            actor = eas.spawn_actor_from_object(post, p, unreal.Rotator(roll=0, pitch=0, yaw=yaw))
            actor.set_actor_enable_collision(False)
            actor.set_actor_label(label + "Post")
            placed += 1
        if i < n:
            actor = eas.spawn_actor_from_object(wire, p, unreal.Rotator(roll=0, pitch=0, yaw=yaw))
            actor.set_actor_scale3d(unreal.Vector(step / WIRE_SPAN, 1.0, 1.0))
            actor.set_actor_enable_collision(False)
            actor.set_actor_label(label + "Wire")
    return placed


def ue(x, y, z):  # Blender metres, Y mirrored (CLAUDE.md)
    return unreal.Vector(x * 100.0, -y * 100.0, z * 100.0)


def main():
    reimport_terrain()
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        if a.get_actor_label().startswith("SS_RA_Cover_"):
            eas.destroy_actor(a)

    pools = {
        "rock": meshes(RA + "/Rocks", ["Rock_"]),
        "tree": meshes(RA + "/Vegetation", ["Tree_M", "Tree_L"]),
        "scrub": meshes(RA + "/Vegetation", ["GrassTree", "Tree_S"]),
    }
    report["pools"] = {k: len(v) for k, v in pools.items()}
    rng = random.Random(20260927)
    posts_done = set()

    with open(CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        kind = row["kind"]
        x, y, gz = float(row["x"]), float(row["y"]), float(row["ground_z"])
        sx, sy, sz = float(row["size_x"]), float(row["size_y"]), float(row["size_z"])
        yaw = -float(row["yaw"])
        if kind == "fence_post":
            continue  # the pack's fence sections carry their own posts
        if kind == "fence_rail":
            # The rail's long axis (Blender X or Y), as a run of posts and wire.
            half = max(sx, sy) / 2
            ax, ay = (0.0, half) if sy > sx else (half, 0.0)
            start, end = ue(x - ax, y - ay, gz), ue(x + ax, y + ay, gz)
            report["fence_posts"] = report.get("fence_posts", 0) + place_fence(start, end, posts_done, "SS_RA_Cover_Fence")
            continue
        pool = pools.get(kind) or []
        if not pool:
            continue
        mesh = rng.choice(pool)
        e = extent(mesh)
        if kind == "tree":
            s = max(0.6, min(1.6, sz * 100.0 / max(e.z, 1.0)))
            scale = unreal.Vector(s, s, s)
        elif kind == "rock":
            # Match the greybox boulder's footprint and height (the cover it gave).
            scale = unreal.Vector(sx * 100.0 / max(e.x, 1.0), sy * 100.0 / max(e.y, 1.0), sz * 100.0 / max(e.z, 1.0))
            yaw += rng.uniform(-20, 20)
        else:
            s = max(0.7, min(1.3, max(sx, sy) * 100.0 / max(e.x, e.y, 1.0)))
            scale = unreal.Vector(s, s, s)
        a = eas.spawn_actor_from_object(mesh, ue(x, y, gz), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
        a.set_actor_scale3d(scale)
        a.set_actor_label("SS_RA_Cover_" + kind.capitalize())
        report["placed"][kind] = report["placed"].get(kind, 0) + 1

    # The dressing fence: flat-shaded boxes, hidden in game and without
    # collision; posts and wire follow each rail.
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        mesh = a.static_mesh_component.static_mesh
        name = mesh.get_name() if mesh else ""
        if name == "SS_Dressing_FenceRail":
            origin, box = a.get_actor_bounds(False)
            half = unreal.Vector(box.x, 0, 0) if box.x >= box.y else unreal.Vector(0, box.y, 0)
            base = origin - unreal.Vector(0, 0, box.z)
            report["fence_posts"] = report.get("fence_posts", 0) + place_fence(base - half, base + half, posts_done, "SS_RA_Cover_FarmFence")
        if name in ("SS_Dressing_FenceRail", "SS_Dressing_FencePost"):
            a.set_actor_hidden_in_game(True)
            a.set_actor_enable_collision(False)
            report["hidden_dressing"] += 1

    report["saved"] = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    report["ok"] = report["saved"] and report.get("terrain_reimported", False)


try:
    main()
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[DryRiverCover] " + json.dumps(report))
