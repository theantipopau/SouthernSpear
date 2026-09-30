# Southern Spear - build the Wandarra training village (M-009) - level pass.
#
# Wandarra is BUILT, not copied: the MOUT pack has no suitable source level, so
# this follows build_dryriver_level.py (new_level, spawn, nav volume, save) with
# build_objective_map.py's objective wiring. Assets are referenced in place from
# three cleared packs (ADR-021/ADR-028): MOUT_Civilian (UE 4.26, upconverted on
# load - R-67 evidence is this first load), RustyCarsFree and EuropeanBeech
# (5.1 native). Layout is Tools/Common/wandarra_spec.py (single source).
#
#   SS_PASS=level  build the village and its gameplay wiring, save to
#                  /Game/Maps/L_Wandarra_01
#   SS_PASS=nav    reload, ensure RecastNavMesh, BUILDPATHS, then nudge each
#                  objective/start to the nearest reachable point (build_wandarra_nav.py)
#
# Writes Build/wandarra_level.json. Never edits pack assets.

import json
import math
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
import sys  # noqa: E402
sys.path.insert(0, os.path.join(PROJECT_DIR, "Tools", "Common"))
import wandarra_spec as SPEC  # noqa: E402
sys.path.insert(0, os.path.join(PROJECT_DIR, "Tools", "Unreal"))
from ss_assets import asset_exists  # noqa: E402

MAP = "/Game/Maps/L_Wandarra_01"
GROUND_MASTER = "/Game/Art/Environment/Fab/M_SS_WorldGroundVT"
REPORT = os.path.join(PROJECT_DIR, "Build", "wandarra_level.json")
EXP_CLASS = "/SSExp_ObjectiveAssault/Experiences/B_SS_ObjectiveAssault.B_SS_ObjectiveAssault_C"
PREFIX = "SS_MAP_W_"
report = {"ok": False, "steps": [], "counts": {}, "errors": []}
eal = unreal.EditorAssetLibrary


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def cm(x_m, y_m, z_m=0.0):
    """Site metres to Unreal centimetres, Y mirrored (layout-CSV convention)."""
    return unreal.Vector(x_m * 100.0, -y_m * 100.0, z_m * 100.0)


def yaw_unreal(yaw_deg):
    """Site-frame degrees clockwise from north -> Unreal Z yaw.

    Derivation (Session 083 defect, was wrongly `-yaw`): Unreal yaw is CCW from
    +X when viewed top-down (yaw 90 forward = +Y), and Unreal Y mirrors site Y.
    Site north (yaw 0) = Unreal (0,-1) = Unreal yaw -90; site east (90) = +X =
    0; site south (180) = +Y = 90. Hence yaw - 90. The shipped `-yaw` put every
    rotated actor one cardinal direction off; the map must be rebuilt to apply.
    """
    return yaw_deg - 90.0


class Builder(object):
    def __init__(self, world, actors):
        self.world = world
        self.actors = actors
        self.counts = {}
        self.missing = []

    def mesh(self, path, label, x, y, z=0.0, yaw=0.0, scale=1.0, collide=True,
             nav_relevant=True):
        asset = unreal.load_asset(path) if asset_exists(path) else None
        if asset is None:
            self.missing.append(path)
            return None
        a = self.actors.spawn_actor_from_class(unreal.StaticMeshActor, cm(x, y, z),
                                               unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw_unreal(yaw)))
        a.set_actor_label(PREFIX + label)
        a.static_mesh_component.set_static_mesh(asset)
        if isinstance(scale, (int, float)):
            a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        else:
            a.set_actor_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
        component = a.static_mesh_component
        component.set_editor_property("can_ever_affect_navigation", nav_relevant)
        # Set collision on the placed component, not on shared vendor mesh assets.
        # This preserves player/world blocking while letting selected actors opt out
        # of Recast's geometry export independently of their collision settings.
        component.set_collision_enabled(
            unreal.CollisionEnabled.QUERY_AND_PHYSICS if collide
            else unreal.CollisionEnabled.NO_COLLISION)
        self.counts[label.split("_")[0]] = self.counts.get(label.split("_")[0], 0) + 1
        return a

    def blueprint(self, path, label, x, y, yaw):
        cls = unreal.load_class(None, path + "." + path.split("/")[-1] + "_C")
        if cls is None:
            self.missing.append(path)
            return None
        a = self.actors.spawn_actor_from_class(cls, cm(x, y, 0.0),
                                               unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw_unreal(yaw)))
        if a:
            a.set_actor_label(PREFIX + label)
            self.counts[label.split("_")[0]] = self.counts.get(label.split("_")[0], 0) + 1
        return a


def ground_material():
    """MI_SS_WorldGround_Wandarra: Ravenshoe gravel, world-mapped (no stretching
    over 300 m), tinted toward dry township earth."""
    mi_path = "/Game/Art/Environment/Fab/MI_SS_WorldGround_Wandarra"
    master = unreal.load_asset(GROUND_MASTER)
    d = unreal.load_asset(SPEC.GRAVEL_D)
    n = unreal.load_asset(SPEC.GRAVEL_N)
    if not (master and d and n) or asset_exists(mi_path):
        return unreal.load_asset(mi_path) if asset_exists(mi_path) else master
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi = tools.create_asset("MI_SS_WorldGround_Wandarra", "/Game/Art/Environment/Fab",
                            unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel = unreal.MaterialEditingLibrary
    mel.set_material_instance_parent(mi, master)
    mel.set_material_instance_texture_parameter_value(mi, "Albedo", d)
    mel.set_material_instance_texture_parameter_value(mi, "Normal", n)
    mel.set_material_instance_scalar_parameter_value(mi, "TileCm", SPEC.GROUND_TILE_CM)
    mel.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(0.93, 0.88, 0.80, 1.0))
    eal.save_loaded_asset(mi)
    return mi


def spawn_ground(b, mat):
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    g = b.actors.spawn_actor_from_class(unreal.StaticMeshActor, cm(150, 150, -50))
    g.set_actor_label(PREFIX + "Ground")
    g.static_mesh_component.set_static_mesh(cube)
    g.set_actor_scale3d(unreal.Vector(SPEC.SITE["size_m"], SPEC.SITE["size_m"], 1.0))
    if mat:
        g.static_mesh_component.set_material(0, mat)


def snap_cm(v):
    return round(v / SPEC.SNAP_M) * SPEC.SNAP_M


def church(b):
    """Assemble the church from ChurchKit on the site grid: nave from walls,
    gabled roof, west tower topped with the cross, east door."""
    c = SPEC.CHURCH
    x, y = float(c["x"]), float(c["y"])
    hw, hl = c["body_w"] / 2.0, c["body_l"] / 2.0
    placed = 0
    # Nave walls: two long sides + west gable, door opening left on the east front.
    n = int(round(c["body_l"] / SPEC.WALL_L))
    seg = c["body_l"] / n
    for i in range(n):
        cx = x - hl + seg * (i + 0.5)
        b.mesh(SPEC.CHURCH_PARTS["wall"], "Church_Wall_N%02d" % i, cx, y + hw, 0.0, 90.0)
        b.mesh(SPEC.CHURCH_PARTS["wall"], "Church_Wall_S%02d" % i, cx, y - hw, 0.0, 90.0)
        placed += 2
    # Windows between long-wall segments (every second bay, both sides).
    for i in range(0, n, 2):
        cx = x - hl + seg * (i + 0.5)
        b.mesh(SPEC.CHURCH_PARTS["window"], "Church_Window_N%02d" % i, cx, y + hw, 0.0, 90.0)
        b.mesh(SPEC.CHURCH_PARTS["window"], "Church_Window_S%02d" % i, cx, y - hw, 0.0, 90.0)
        placed += 2
    # West gable + east door leaves the east front open at the door.
    b.mesh(SPEC.CHURCH_PARTS["wall"], "Church_Wall_W", x - hl, y, 0.0, 0.0)
    b.mesh(SPEC.CHURCH_PARTS["door"], "Church_Door", x + hl, y, 0.0, 90.0)
    placed += 2
    # Roof: centre pieces end to end.
    for i in range(n):
        cx = x - hl + seg * (i + 0.5)
        b.mesh(SPEC.CHURCH_PARTS["roof"], "Church_Roof_%02d" % i, cx, y, c["wall_h"], 90.0)
        placed += 1
    # Bell tower at the west end, cross on top.
    b.mesh(SPEC.CHURCH_PARTS["tower_top"], "Church_Tower", x - hl, y, c["wall_h"], 0.0)
    b.mesh(SPEC.CHURCH_PARTS["cross"], "Church_Cross", x - hl, y,
           c["wall_h"] + 3.0, 0.0)
    placed += 2
    return placed


def fences(b):
    """Tile fence runs with the longest kit length that fits; leave gate gaps."""
    kinds = [(2.0, SPEC.FURNITURE_MESH["fence_2m"]), (1.5, SPEC.FURNITURE_MESH["fence_1_5m"]),
             (1.0, SPEC.FURNITURE_MESH["fence_1m"])]
    total = 0
    for (x0, y0, x1, y1, gaps, picket, why) in SPEC.FENCE_RUNS:
        length = math.hypot(x1 - x0, y1 - y0)
        yaw = math.degrees(math.atan2(y1 - y0, x1 - x0))
        gaps = sorted(gaps)
        s = 0.0
        while s < length - 0.01:
            # next gap along the run?
            g0 = next((g0 for (g0, g1) in gaps if g1 > s), None)
            end = g0 if g0 is not None else length
            # clip the last piece to the run
            while s < end - 0.01:
                piece = next((l for (l, _) in kinds if l <= end - s + 0.01), 1.0)
                t = s + piece / 2.0
                px, py = x0 + (x1 - x0) * t / length, y0 + (y1 - y0) * t / length
                mesh = SPEC.FURNITURE_MESH["picket_1m"] if picket else dict(kinds)[piece]
                b.mesh(mesh, "Fence", snap_cm(px), snap_cm(py), 0.0, yaw)
                total += 1
                s += piece
            # skip the gap
            g = next(((g0, g1) for (g0, g1) in gaps if g1 > s), None)
            if g:
                s = g[1]
            else:
                break
    return total


def trees(b):
    """Rows and clusters from the spec with deterministic jitter, snaped to
    ground by trace (SimpleWind meshes pivot at the trunk base)."""
    import random
    rng = random.Random(SPEC.TREE_SEED)
    total = 0
    for (x0, y0, x1, y1, count, why) in SPEC.TREE_ROWS:
        for i in range(count):
            t = (i + 0.5) / count
            jx = rng.uniform(-2.5, 2.5)
            jy = rng.uniform(-2.5, 2.5)
            x = x0 + (x1 - x0) * t + jx
            y = y0 + (y1 - y0) * t + jy
            if not SPEC.run_clears_protected(x, y, x, y, margin_m=1.0):
                continue
            mesh = SPEC.TREE_MESHES[rng.randrange(len(SPEC.TREE_MESHES))]
            b.mesh(mesh, "Tree", x, y, 0.0, rng.uniform(0.0, 360.0),
                   rng.uniform(0.9, 1.25), collide=True, nav_relevant=False)
            total += 1
    return total


def furniture(b):
    n = 0
    for (kind, x, y, yaw, why) in SPEC.FURNITURE:
        b.mesh(SPEC.FURNITURE_MESH[kind], kind.capitalize(), snap_cm(x), snap_cm(y), 0.0, yaw)
        n += 1
    return n


def cars(b):
    n = 0
    for (idx, x, y, yaw, why) in SPEC.CARS_LAYOUT:
        # Wrecks are visual cover, but their vendor collision exports up to
        # 972k triangles into Recast. Exclude only their nav export; leave the
        # original meshes and collision untouched until a dedicated proxy exists.
        b.mesh(SPEC.CAR_MESHES[idx], "Car_%02d" % n, x, y, 0.0, yaw,
               collide=True, nav_relevant=False)
        n += 1
    return n


def buildings(b):
    n = 0
    for (key, x, y, facing, why) in SPEC.BUILDINGS:
        yaw = {"N": 180.0, "E": -90.0, "S": 0.0, "W": 90.0}[facing]
        b.blueprint(SPEC.BUILDING_BPS[key], key.capitalize(), snap_cm(x), snap_cm(y), yaw)
        n += 1
    return n


def gameplay(world, b):
    """Deployments, objectives, director, nav volume, experience (the
    build_objective_map.py wiring on spec layout)."""
    start_cls = unreal.load_class(None, "/Script/LyraGame.LyraPlayerStart")
    # Teams enter on their own PlayerStartTag; layout_spawns.py re-lays 8 per
    # team on the navmesh afterwards.
    for d in SPEC.DEPLOYS:
        s = b.actors.spawn_actor_from_class(start_cls, cm(d["x"], d["y"], 100.0), unreal.Rotator(roll=0, pitch=0, yaw=0))
        s.set_actor_label("{}Deploy{}".format(PREFIX, d["name"]))
        s.set_editor_property("player_start_tag", d["team"])
    report["counts"]["deployments"] = len(SPEC.DEPLOYS)

    placed = []
    for i, o in enumerate(SPEC.OBJECTIVES):
        a = b.actors.spawn_actor_from_class(unreal.SSObjectiveActor, cm(o["x"], o["y"], 0.0),
                                            unreal.Rotator(roll=0, pitch=0, yaw=0))
        a.set_actor_label("{}Obj{}_{}".format(PREFIX, o["key"], o["name"].replace(" ", "")))
        a.set_editor_property("sequence_index", i)
        a.set_editor_property("objective_name", unreal.Text(o["name"]))
        a.get_component_by_class(unreal.SphereComponent).set_sphere_radius(o["radius_cm"])
        placed.append(o["name"])
    step("objectives", len(placed) == 3, placed)

    d = b.actors.spawn_actor_from_class(unreal.SSObjectiveAssaultDirector, cm(150, 150, 0),
                                        unreal.Rotator(roll=0, pitch=0, yaw=0))
    d.set_actor_label("SS_ObjectiveAssault_Director")
    vol = b.actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume, cm(150, 150, 500),
                                          unreal.Rotator(roll=0, pitch=0, yaw=0))
    # Brush volumes arrive at 2 m cube and read scale x4 on reload (R-10); scale
    # so the saved scale covers the site: 300 m => 150 (half) / 2 m base = 75.
    vol.set_actor_scale3d(unreal.Vector(75.0, 75.0, 15.0))
    vol.set_actor_label(PREFIX + "NavBounds")
    # Save the RecastNavMesh into the map: script-spawned nav actors register
    # on a later tick, so the nav pass must load it from disk, not spawn it.
    b.actors.spawn_actor_from_class(unreal.RecastNavMesh, cm(150, 150, 0),
                                    unreal.Rotator(roll=0, pitch=0, yaw=0))
    ws = world.get_world_settings()
    ok = unreal.SSObjectivesEditorLibrary.set_property_from_text(ws, "DefaultGameplayExperience", EXP_CLASS)
    step("world_experience", ok, EXP_CLASS)


def lighting(world, b):
    """The light_dryriver rig: movable sun + atmosphere + sky + fog + PPV."""
    sun = b.actors.spawn_actor_from_class(unreal.DirectionalLight, cm(150, 150, 5000),
                                          unreal.Rotator(roll=0, pitch=-52, yaw=35))
    c = sun.light_component
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    c.set_intensity(10.0)
    c.set_light_color(unreal.LinearColor(1.0, 0.95, 0.86, 1.0))
    c.set_editor_property("atmosphere_sun_light", True)
    c.set_editor_property("cast_shadows", True)
    b.actors.spawn_actor_from_class(unreal.SkyAtmosphere, cm(0, 0), unreal.Rotator(roll=0, pitch=0, yaw=0))
    sky = b.actors.spawn_actor_from_class(unreal.SkyLight, cm(150, 150, 3000),
                                          unreal.Rotator(roll=0, pitch=0, yaw=0))
    sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("real_time_capture", True)
    fog = b.actors.spawn_actor_from_class(unreal.ExponentialHeightFog, cm(150, 150),
                                          unreal.Rotator(roll=0, pitch=0, yaw=0))
    fog.component.set_editor_property("fog_density", 0.01)
    fog.component.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.75, 0.68, 0.58, 1.0))
    ppv = b.actors.spawn_actor_from_class(unreal.PostProcessVolume, cm(0, 0),
                                          unreal.Rotator(roll=0, pitch=0, yaw=0))
    ppv.set_editor_property("unbound", True)
    st = ppv.settings
    st.set_editor_property("override_auto_exposure_min_brightness", True)
    st.set_editor_property("auto_exposure_min_brightness", 0.5)
    st.set_editor_property("override_auto_exposure_max_brightness", True)
    st.set_editor_property("auto_exposure_max_brightness", 2.0)
    ppv.set_editor_property("settings", st)
    step("lighting", True, "sun, atmosphere, skylight, fog, PPV")


def level_pass():
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    # NewLevel refuses to overwrite; delete first (the level is a pure build
    # artefact of this script, as in build_dryriver_level.py).
    if asset_exists(MAP):
        if not eal.delete_asset(MAP):
            return step("delete_existing", False, MAP)
        step("delete_existing", True, MAP)
    if not les.new_level(MAP):
        return step("new_level", False, MAP)
    step("new_level", True, MAP)
    level = les.get_current_level()
    world = level.get_world() if level else None
    if world is None:
        return step("world", False, "no world from new_level")
    b = Builder(world, unreal.get_editor_subsystem(unreal.EditorActorSubsystem))

    mat = ground_material()
    spawn_ground(b, mat)
    step("ground", mat is not None, "MI_SS_WorldGround_Wandarra (Ravenshoe gravel)")

    n = buildings(b)
    step("buildings", n == len(SPEC.BUILDINGS), "{} vendor blueprints".format(n))
    n = church(b)
    step("church", n >= 12, "{} ChurchKit parts".format(n))
    n = fences(b)
    step("fences", n >= 40, "{} kit segments".format(n))
    n = furniture(b)
    step("furniture", n == len(SPEC.FURNITURE), "{} props".format(n))
    n = cars(b)
    step("cars", n == len(SPEC.CARS_LAYOUT), "{} RustyCars wrecks".format(n))
    n = trees(b)
    step("trees", n >= 30, "{} EuropeanBeech".format(n))

    gameplay(world, b)
    lighting(world, b)
    report["counts"]["missing_assets"] = b.missing
    report["counts"].update({k: v for k, v in b.counts.items() if not k.startswith("SS")})
    if b.missing:
        step("assets_all_found", False, "{} missing".format(len(b.missing)))
    else:
        step("assets_all_found", True, "every spec asset resolved")

    ok = les.save_current_level()
    step("save_map", ok, MAP)


try:
    level_pass()
    report["ok"] = all(s["ok"] for s in report["steps"]) and not report["counts"].get("missing_assets")
except Exception:
    report["errors"].append(traceback.format_exc())
    try:
        unreal.EditorLoadingAndSavingUtils.save_map(unreal.EditorLoadingAndSavingUtils.get_editor_world(), MAP)
    except Exception:
        pass
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[Wandarra] level ok={} -> {}".format(report["ok"], REPORT))
