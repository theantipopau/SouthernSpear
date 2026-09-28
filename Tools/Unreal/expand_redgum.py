"""Red Gum Station: repeatable rural dressing and playable-area expansion.

This pass only edits /Game/Maps/L_RedGum_01. It does not resize/reimport the
1.02 km landscape, regenerate the source map, alter the Rural Australia pack,
or import third-party assets. It adds manually placed instances of the cleared
Rural Australia tree/log/rock meshes, cover, and visual fence dressing. The nav
volume widens from 720 x 240 m to 720 x 600 m inside the existing landscape.

This commandlet changes the volume but cannot bake static Recast data. After
running it, use Build > Build Paths in the interactive Unreal Editor and verify
the baked routes. Do not claim the enlarged AI-playable space until that is
complete.

The Rural Australia pack contains no farm-house/shed mesh. This pass avoids
reusing unrelated Asian canal buildings; a homestead needs original art or a
separately reviewed rural asset.

Labels use SS_RedGum_Dress_v1_ and only actors owned by this pass are removed
on rerun. The Rural Australia source meshes are referenced, never modified.
"""
import json
import math
import os
import random
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MAP = "/Game/Maps/L_RedGum_01"
REPORT = os.path.join(PROJECT_DIR, "Build", "redgum_expansion_report.json")
PREFIX = "SS_RedGum_Dress_v1_"
FOLDER = unreal.Name("RedGum/Dressing")
NAV_LABEL = "SS_MAP_RedGum_NavBounds"
NAV_SCALE = unreal.Vector(360.0, 300.0, 100.0)  # 720 x 600 x 200 m

RA = "/Game/RuralAustralia/StaticMeshes"
MESH_PATHS = {
    "tree_large": RA + "/Vegetation/Tree_L_01/SM_Tree_L_01",
    "tree_mid_a": RA + "/Vegetation/Tree_M_01/SM_Tree_M_01",
    "tree_mid_b": RA + "/Vegetation/Tree_M_02/SM_Tree_M_02",
    "tree_small": RA + "/Vegetation/Tree_S_01/SM_Tree_S_01",
    "grass_tree": RA + "/Vegetation/GrassTree_01/SM_GrassTree_01",
    "log_large": RA + "/Vegetation/Log_L_01/SM_Log_L_01",
    "log_mid": RA + "/Vegetation/Log_M_01/SM_Log_M_01",
    "log_small": RA + "/Vegetation/Log_S_01/SM_Log_S_01",
    "rock_mid_a": RA + "/Rocks/Rock_M_01/SM_Rock_M_01",
    "rock_mid_b": RA + "/Rocks/Rock_M_02/SM_Rock_M_02",
    "ridge_a": RA + "/Rocks/Ridge_Dirt_01/SM_Ridge_Dirt_01_A",
    "ridge_b": RA + "/Rocks/Ridge_Dirt_01/SM_Ridge_Dirt_01_B",
    "fence_post": RA + "/Props/Fence_01/SM_Fence_02",
    "fence_wire": RA + "/Props/Fence_01/SM_Fence_Wires_01",
}

# Hand-authored layout anchors (UE centimetres) around the active map core.
# Vegetation lines shape long paddock sightlines and give both deployments
# equivalent lateral routes. Open lanes remain between the lines.
TREE_LINES = [
    ((-47000, -27000), (-6000, -27000), 21),
    ((6000, -27000), (47000, -27000), 21),
    ((-47000, 27000), (-6000, 27000), 21),
    ((6000, 27000), (47000, 27000), 21),
    ((-44000, -30000), (-44000, 30000), 17),
    ((44000, -30000), (44000, 30000), 17),
    ((-32000, -43000), (32000, -43000), 23),
    ((-32000, 43000), (32000, 43000), 23),
    ((-15000, -18000), (-5000, -3000), 9),
    ((7000, 4000), (17000, 19000), 9),
    ((12000, -19000), (22000, -5000), 8),
    ((-21000, 5000), (-11000, 20000), 8),
    # Added for the enlarged play space. The original lines stopped at
    # y = +-270 m, which left the third of the map that the widened nav volume
    # made playable as bare open ground with nothing to fight behind.
    ((-47000, -31000), (-6000, -31000), 21),
    ((6000, -31000), (47000, -31000), 21),
    ((-47000, 31000), (-6000, 31000), 21),
    ((6000, 31000), (47000, 31000), 21),
    # Flank cover on the deployment-to-homestead axis, 260-400 m out. The
    # middle 260 m stays open; both deployments still get something to fight
    # through on the way in, and the long axial sightline gets broken.
    ((-40000, 0), (-26000, 0), 11),
    ((26000, 0), (40000, 0), 11),
    # Diagonal cover in the south-west and north-east quadrants, so the
    # enlarged area offers more than one axis of approach to fight along.
    ((-30000, -15000), (-22000, -22000), 9),
    ((22000, 15000), (30000, 22000), 9),
    # Deep treelines marking the far edge of the play space.
    ((-12000, -33000), (12000, -33000), 15),
    ((-12000, 33000), (12000, 33000), 15),
]
BUSH_CLUSTERS = [
    (-26000, -13000, 9), (26000, -13000, 9),
    (-26000, 13000, 9), (26000, 13000, 9),
    (-7000, -22000, 7), (7000, 22000, 7),
    (29000, 0, 8), (-29000, 0, 8),
    # Enlarged-area scrub: conceals without blocking movement.
    (-33000, -26000, 8), (33000, -26000, 8),
    (-33000, 26000, 8), (33000, 26000, 8),
    (-18000, -29000, 7), (18000, 29000, 7),
    (-15000, 3000, 6), (15000, -3000, 6),
]
LOG_CLUSTERS = [(-25000, -16000), (25000, -16000), (-25000, 16000),
                (25000, 16000), (-7000, -22000), (7000, 22000),
                (30000, 0), (-30000, 0),
                # Enlarged-area piles, plus two inside the play space so the
                # centre is not fought entirely around the homestead.
                (-34000, -24000), (34000, -24000),
                (-34000, 24000), (34000, 24000),
                (-16000, -8000), (16000, 8000)]
ROCK_CLUSTERS = [(-34000, -18000), (34000, -18000), (-34000, 18000),
                 (34000, 18000), (-8000, 26000), (8000, -26000),
                 (-22000, -30000), (22000, 30000),
                 (-20000, 30000), (20000, -30000)]

# Long low dirt ridges. One rock is cover you can walk around in two steps; a
# 40 m ridge is a sightline breaker, which is what a 1 km map needs or every
# long-range fight resolves itself down the middle. Kept off the centre so they
# cannot wall the homestead objective in.
RIDGE_RUNS = [
    ((-36000, -34000), (-20000, -30000), 8),
    ((20000, 30000), (36000, 34000), 8),
    ((-38000, 20000), (-28000, 26000), 6),
    ((28000, -20000), (38000, -26000), 6),
]

# Actors placed by import_redgum_homestead.py. Dressing keeps clear of them:
# a gum tree through the shearing shed roof is the sort of thing nobody notices
# until a screenshot, and a rerun of this pass would happily cause it. The
# keep-out is read from the placed actors' real bounds rather than hard-coded,
# so moving the station in Blender cannot leave a stale exclusion behind.
HOMESTEAD_PREFIX = "SS_RedGum_Homestead_"

report = {"ok": False, "map": MAP, "steps": [], "placed": {}, "errors": [], "warnings": []}
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    unreal.log("[RedGumExpansion] {} {} {}".format("OK" if ok else "FAIL", name, detail))
    return bool(ok)


def load_meshes():
    meshes = {}
    missing = []
    for key, path in MESH_PATHS.items():
        asset = unreal.load_asset(path)
        if asset is None or not isinstance(asset, unreal.StaticMesh):
            missing.append(path)
        else:
            meshes[key] = asset
    report["missing_assets"] = missing
    return meshes


def remove_owned_actors():
    removed = 0
    for actor in actor_sub.get_all_level_actors():
        if actor.get_actor_label().startswith(PREFIX):
            actor_sub.destroy_actor(actor)
            removed += 1
    report["removed_previous_pass"] = removed
    return True


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


def spawn_mesh(world, meshes, key, label, x, y, yaw, scale, collision):
    z = ground_z(world, x, y)
    if z is None:
        report["warnings"].append("no terrain hit at {} ({}, {})".format(label, x, y))
        return False
    # Spawn the actor class and hand it the mesh. spawn_actor_from_object
    # logs only "SpawnActorFromObject. No actor was spawned." and does nothing
    # for any mesh in this commandlet. dress_dryriver.py already uses this
    # route; using the other one is what made this pass delete 864 dressing
    # actors, place nothing, and save the map without them.
    actor = actor_sub.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(x, y, z),
        unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    if not actor:
        return False
    actor.static_mesh_component.set_static_mesh(meshes[key])
    actor.set_actor_label(PREFIX + label)
    try:
        actor.set_folder_path(FOLDER)
    except Exception:
        pass
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    actor.set_actor_enable_collision(collision)
    report["placed"][key] = report["placed"].get(key, 0) + 1
    return True


def lerp_line(a, b, count, jitter, rng):
    for i in range(count):
        t = i / float(max(1, count - 1))
        yield (round(a[0] + (b[0] - a[0]) * t + rng.uniform(-jitter, jitter)),
               round(a[1] + (b[1] - a[1]) * t + rng.uniform(-jitter, jitter)))


def far_from(point, others, radius):
    return all(math.hypot(point[0] - p[0], point[1] - p[1]) >= radius for p in others)


def homestead_zones(world):
    """Keep-out discs around every placed homestead structure, plus margin."""
    zones = []
    for actor in unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.StaticMeshActor):
        if not actor.get_actor_label().startswith(HOMESTEAD_PREFIX):
            continue
        origin, extent = actor.get_actor_bounds(False)
        # 2.5 m of clearance: the farmhouse roof overhangs 0.35 m and the
        # verandah posts stand off the wall, so the bounds alone are tight.
        zones.append((origin.x, origin.y, max(extent.x, extent.y) + 250.0))
    report["homestead_zones"] = len(zones)
    return zones


def clear_of_station(point, zones):
    return all(math.hypot(point[0] - z[0], point[1] - z[1]) >= z[2] for z in zones)


def place_tree_lines(world, meshes, rng, objectives, starts, zones):
    n = 0
    for line_idx, (a, b, count) in enumerate(TREE_LINES):
        for i, (x, y) in enumerate(lerp_line(a, b, count, 850, rng)):
            key = rng.choice(("tree_large", "tree_mid_a", "tree_mid_a", "tree_mid_b"))
            scale = rng.uniform(0.78, 0.98) if key == "tree_large" else rng.uniform(0.82, 1.06)
            p = (x, y)
            if not far_from(p, objectives, 2400) or not far_from(p, starts, 1800):
                continue
            if not clear_of_station(p, zones):
                continue
            if spawn_mesh(world, meshes, key, "TreeLine_{:02d}_{:02d}".format(line_idx, i),
                          x, y, rng.uniform(0, 360), scale, True):
                n += 1
    return n


def place_bushes(world, meshes, rng, objectives, starts, zones):
    n = 0
    for cidx, (cx, cy, count) in enumerate(BUSH_CLUSTERS):
        placed = 0
        tries = 0
        while placed < count and tries < count * 5:
            tries += 1
            angle = rng.uniform(0, math.tau)
            radius = rng.uniform(250, 2000)
            x, y = round(cx + math.cos(angle) * radius), round(cy + math.sin(angle) * radius)
            p = (x, y)
            if not far_from(p, objectives, 1700) or not far_from(p, starts, 1900):
                continue
            if not clear_of_station(p, zones):
                continue
            key = rng.choice(("grass_tree", "tree_small"))
            scale = rng.uniform(0.8, 1.1) if key == "grass_tree" else rng.uniform(0.8, 1.0)
            if spawn_mesh(world, meshes, key, "Bush_{:02d}_{:02d}".format(cidx, placed),
                          x, y, rng.uniform(0, 360), scale, key == "tree_small"):
                placed += 1
                n += 1
    return n


def place_logs(world, meshes, rng, objectives, starts, zones):
    n = 0
    for cidx, (cx, cy) in enumerate(LOG_CLUSTERS):
        for i in range(4):
            angle = rng.uniform(0, math.tau)
            radius = rng.uniform(300, 2300)
            x, y = round(cx + math.cos(angle) * radius), round(cy + math.sin(angle) * radius)
            p = (x, y)
            if not far_from(p, objectives, 1700) or not far_from(p, starts, 1500):
                continue
            if not clear_of_station(p, zones):
                continue
            key = rng.choice(("log_mid", "log_mid", "log_small", "log_large"))
            b = meshes[key].get_bounds()
            scale = min(1.0, 1.0 / max(b.box_extent.x, b.box_extent.y, 1.0) * 700.0)
            scale = max(0.55, scale)
            if spawn_mesh(world, meshes, key, "Log_{:02d}_{:02d}".format(cidx, i),
                          x, y, rng.uniform(0, 360), scale, True):
                n += 1
    return n


def place_rocks(world, meshes, rng, objectives, starts, zones):
    n = 0
    for cidx, (cx, cy) in enumerate(ROCK_CLUSTERS):
        for i in range(3):
            angle = rng.uniform(0, math.tau)
            radius = rng.uniform(500, 2500)
            x, y = round(cx + math.cos(angle) * radius), round(cy + math.sin(angle) * radius)
            p = (x, y)
            if not far_from(p, objectives, 2600) or not far_from(p, starts, 2300):
                continue
            if not clear_of_station(p, zones):
                continue
            key = rng.choice(("rock_mid_a", "rock_mid_b", "ridge_a", "ridge_b"))
            scale = rng.uniform(1.15, 1.8) if key.startswith("rock") else rng.uniform(0.45, 0.7)
            if spawn_mesh(world, meshes, key, "Rock_{:02d}_{:02d}".format(cidx, i),
                          x, y, rng.uniform(0, 360), scale, True):
                n += 1
    return n


def place_ridges(world, meshes, rng, objectives, starts, zones):
    """Long low dirt ridges, the map's sightline breakers.

    These are placed on an explicit run rather than scattered, because a ridge
    is a line: scattered copies of a 20 m mesh read as boulders, not as the
    long low spines that make a kilometre of paddock fightable at more than
    one range.
    """
    n = 0
    for run_idx, (a, b, count) in enumerate(RIDGE_RUNS):
        for i, (x, y) in enumerate(lerp_line(a, b, count, 700, rng)):
            p = (x, y)
            if not far_from(p, objectives, 3000) or not far_from(p, starts, 2600):
                continue
            if not clear_of_station(p, zones):
                continue
            key = "ridge_a" if i % 2 == 0 else "ridge_b"
            if spawn_mesh(world, meshes, key,
                          "Ridge_{:02d}_{:02d}".format(run_idx, i),
                          x, y, rng.uniform(0, 360), rng.uniform(0.55, 0.8), True):
                n += 1
    return n


def place_fence(world, meshes, line_index, a, b, spacing=600.0):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 1.0:
        return 0
    yaw = math.degrees(math.atan2(dy, dx))
    count = max(2, int(length / spacing) + 1)
    span = length / (count - 1)
    n = 0
    for i in range(count - 1):
        t = i / float(count - 1)
        x, y = round(a[0] + dx * t), round(a[1] + dy * t)
        z = ground_z(world, x, y)
        if z is None:
            continue
        post = actor_sub.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(x, y, z),
            unreal.Rotator(roll=0, pitch=0, yaw=yaw))
        if post:
            post.static_mesh_component.set_static_mesh(meshes["fence_post"])
        if post:
            post.set_actor_label(PREFIX + "Fence_{:02d}_Post_{:02d}".format(line_index, i))
            post.set_actor_enable_collision(False)
            post.set_actor_scale3d(unreal.Vector(0.8, 0.8, 0.8))
            n += 1
        wire = actor_sub.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(x, y, z),
            unreal.Rotator(roll=0, pitch=0, yaw=yaw))
        if wire:
            wire.static_mesh_component.set_static_mesh(meshes["fence_wire"])
        if wire:
            wire.set_actor_label(PREFIX + "Fence_{:02d}_Wire_{:02d}".format(line_index, i))
            wire.set_actor_enable_collision(False)
            wire.set_actor_scale3d(unreal.Vector(span / 400.0, 0.75, 0.75))
            n += 1
    x, y = b
    z = ground_z(world, x, y)
    if z is not None:
        post = actor_sub.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(x, y, z),
            unreal.Rotator(roll=0, pitch=0, yaw=yaw))
        if post:
            post.static_mesh_component.set_static_mesh(meshes["fence_post"])
        if post:
            post.set_actor_label(PREFIX + "Fence_{:02d}_Post_{:02d}".format(line_index, count - 1))
            post.set_actor_enable_collision(False)
            post.set_actor_scale3d(unreal.Vector(0.8, 0.8, 0.8))
            n += 1
    return n


def place_paddock_fences(world, meshes):
    lines = [((-40000, -35000), (-5000, -35000)),
             ((5000, -35000), (40000, -35000)),
             ((-40000, 35000), (-5000, 35000)),
             ((5000, 35000), (40000, 35000)),
             ((-36000, -5000), (-24000, -5000)),
             ((24000, 5000), (36000, 5000))]
    total = 0
    for idx, (a, b) in enumerate(lines):
        total += place_fence(world, meshes, idx, a, b)
    report["placed"]["fence_components"] = total
    return total


def expand_nav_volume(world):
    matches = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.NavMeshBoundsVolume)
               if a.get_actor_label() == NAV_LABEL]
    if len(matches) != 1:
        return False, "expected exactly one {} volume, found {}".format(NAV_LABEL, len(matches))
    matches[0].set_actor_scale3d(NAV_SCALE)
    report["nav_bounds_m"] = [720, 600, 200]
    return True, "nav bounds widened to 720 x 600 x 200 m inside existing terrain; Recast rebuild is a separate editor step"


def save_level():
    try:
        return bool(unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
    except Exception:
        return bool(unreal.EditorLoadingAndSavingUtils.save_current_level())


def main():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not step("load_map", world is not None, MAP):
        return
    meshes = load_meshes()
    if len(meshes) != len(MESH_PATHS):
        return step("load_assets", False, "loaded {}/{}; missing {}".format(
            len(meshes), len(MESH_PATHS), report["missing_assets"]))
    step("load_assets", True, "{} existing Rural Australia meshes".format(len(meshes)))
    remove_owned_actors()
    objectives = [(o.get_actor_location().x, o.get_actor_location().y)
                  for o in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SSObjectiveActor)]
    starts = [(s.get_actor_location().x, s.get_actor_location().y)
              for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)]
    rng = random.Random(20260928)

    zones = homestead_zones(world)
    tree_n = place_tree_lines(world, meshes, rng, objectives, starts, zones)
    bush_n = place_bushes(world, meshes, rng, objectives, starts, zones)
    log_n = place_logs(world, meshes, rng, objectives, starts, zones)
    rock_n = place_rocks(world, meshes, rng, objectives, starts, zones)
    ridge_n = place_ridges(world, meshes, rng, objectives, starts, zones)
    fence_n = place_paddock_fences(world, meshes)
    step("place_rural_dressing", tree_n + bush_n + log_n + rock_n + ridge_n > 0,
         "trees={} bushes={} logs={} rocks={} ridges={} fence_components={}".format(
             tree_n, bush_n, log_n, rock_n, ridge_n, fence_n))

    # Sanity gate before anything is written. This pass deletes the dressing it
    # owns and then rebuilds it, so a spawn route that silently does nothing
    # turns into a saved map that is simply missing its dressing - and the only
    # trace of it is a report nobody reads. Refuse to save unless the rebuild
    # put back roughly what it took out.
    placed_total = sum(v for k, v in report["placed"].items() if k != "fence_components")
    removed = report.get("removed_previous_pass", 0)
    report["placed_total"] = placed_total
    healthy = placed_total > 0 and (removed == 0 or placed_total >= removed * 0.5)
    step("dressing_sanity", healthy,
         "placed {} of {} removed actors".format(placed_total, removed))
    if not healthy:
        report["ok"] = False
        step("save_map", False, "refused: the pass would have stripped the map")
        return

    nav_ok, detail = expand_nav_volume(world)
    step("expand_nav_bounds", nav_ok, detail)
    saved = save_level()
    step("save_map", saved, MAP)
    report["ok"] = all(s["ok"] for s in report["steps"])


try:
    main()
except Exception:
    report["errors"].append(traceback.format_exc())
    unreal.log_error("[RedGumExpansion] raised:\n" + traceback.format_exc())
finally:
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    unreal.log("[RedGumExpansion] complete ok={} report={}".format(report["ok"], REPORT))
