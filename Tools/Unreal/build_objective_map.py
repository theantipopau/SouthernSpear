# Southern Spear - Objective Assault maps from Fab environments (ADR-022 pattern, L-0016).
#
# One configurable builder for the environment-based maps (Red Gum has its own
# scripts). Select the map with the environment variable SS_MAP and the pass with
# SS_PASS=level|nav:
#   level: copy the source level (never saved itself) to /Game/Maps/<target>,
#          remove the sample's player starts and cine cameras, place two
#          deployments (LyraPlayerStart + extras) and three objectives on the
#          long axis by ground trace, the director, nav bounds and the SS experience.
#   nav:   reload, build navigation, move any objective/deployment that cannot
#          reach the centre objective to the nearest reachable point, verify all legs.
# Writes Build/objective_map_<key>_<pass>.json.

import json
import math
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
EXP_CLASS = "/SSExp_ObjectiveAssault/Experiences/B_SS_ObjectiveAssault.B_SS_ObjectiveAssault_C"

# key -> source, target, fictional objective names (ADR-016), capture radius
MAPS = {
    "saltbush": {"src": "/Game/Namaqualand/Levels/Showcase", "dst": "/Game/Maps/L_Saltbush_01",
                 "label": "Saltbush", "objectives": ["Windmill", "Stock Yards", "Dry Dam"], "radius": 900.0},
    "canal": {"src": "/Game/Singapore_Canal/Map/Singapore_Canal", "dst": "/Game/Maps/L_SelatCanal_01",
              "label": "SelatCanal", "objectives": ["Footbridge", "Market Row", "Pump House"], "radius": 700.0},
    "quarry": {"src": "/Game/Scene_QuarrySlate/Maps/Quarry_Slate", "dst": "/Game/Maps/L_Bluestone_01",
               "label": "Bluestone", "objectives": ["Loading Bay", "Cutting Face", "Spoil Heaps"], "radius": 700.0,
               # A studio-lit Megascans diorama (~70 x 80 m flooded pit), not a level: keep the pit, drop the
               # showroom, give the meshes collision, light it outdoors and ring it with a walkable rim.
               "diorama": {"keep": (11000, -4500, 19500, 4500), "rim_z": 950.0, "rim_width": 40000.0, "floor": "SM_Qua_Sla_Ground_01",
                            "ground_d": "/Game/Scene_QuarrySlate/Assets/MS/Surfaces/Qua_Sla_Ground_Gravel_Rocky_02/T_Qua_Sla_Ground_Gravel_Rocky_02_D", "ground_n": "/Game/Scene_QuarrySlate/Assets/MS/Surfaces/Qua_Sla_Ground_Gravel_Rocky_02/T_Qua_Sla_Ground_Gravel_Rocky_02_N", "ground_tile_cm": 350.0, "wall": 3000.0, "tuck": 400.0, "scatter_count": 70,
                            "scatter": ["/Game/Scene_QuarrySlate/Assets/MS/3D/Qua_Sla_Cluster_Rock_M_07/SM_Qua_Sla_Cluster_Rock_M_07",
                                        "/Game/Scene_QuarrySlate/Assets/MS/3D/Qua_Sla_Pile_Rock_S_01/SM_Qua_Sla_Pile_Rock_S_01",
                                        "/Game/Scene_QuarrySlate/Assets/MS/3D/Qua_Sla_Cluster_Ledge_Rock_M_01/SM_Qua_Sla_Cluster_Ledge_Rock_M_01",
                                        "/Game/Scene_QuarrySlate/Assets/MS/3D/Qua_Sla_Cluster_Rock_M_06/SM_Qua_Sla_Cluster_Rock_M_06",
                                        "/Game/Scene_QuarrySlate/Assets/MS/3D_Plants/Tun_Nor_Bush_EuropeanSpindle_Set_01/SM_Tun_Nor_Bush_EuropeanSpindle_Set_01_G"],
                            "cliff_rock": "/Game/Scene_QuarrySlate/Assets/MS/3D/Qua_Sla_Ledge_Rock_L_01/SM_Qua_Sla_Ledge_Rock_L_01"}},
}

KEY = os.environ.get("SS_MAP", "")
PASS = os.environ.get("SS_PASS", "level")
CFG = MAPS.get(KEY)
REPORT = os.path.join(PROJECT_DIR, "Build", "objective_map_{}_{}.json".format(KEY, PASS))
EXTRA_STARTS = 7
SPACING_CM = 300.0

eal = unreal.EditorAssetLibrary
report = {"ok": False, "map": KEY, "pass": PASS, "steps": [], "errors": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def ground(world, x, y):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, 50000), unreal.Vector(x, y, -50000),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    return None if hit is None else hit.to_dict()["impact_point"].z


def play_bounds(world):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if a.get_actor_label().startswith("SS_MAP_Rim_"):
            continue  # visual ground out into the fog; the walls bound play
        if isinstance(a, (unreal.StaticMeshActor, unreal.LandscapeProxy)):
            o, e = a.get_actor_bounds(False)
            if e.x > 100000 or e.y > 100000:
                continue  # skyboxes, horizon rings
            for i, (oc, ec) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))):
                lo[i], hi[i] = min(lo[i], oc - ec), max(hi[i], oc + ec)
    return lo, hi


def world_ground_material(cfg):
    """M_SS_WorldGround: colour + normal sampled in world XY (tile size in metres), so a large flat rim does
    not stretch one texture over hundreds of metres. Samplers follow the textures' virtual-texture flag."""
    mel = unreal.MaterialEditingLibrary
    E = unreal
    col_tex, nrm_tex = unreal.load_asset(cfg["ground_d"]), unreal.load_asset(cfg["ground_n"])
    vt = bool(col_tex.get_editor_property("virtual_texture_streaming"))
    path = "/Game/Art/Environment/Fab/M_SS_WorldGround" + ("VT" if vt else "")
    if eal.does_asset_exist(path):
        master = unreal.load_asset(path)
    else:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        master = tools.create_asset(path.split("/")[-1], "/Game/Art/Environment/Fab", unreal.Material, unreal.MaterialFactoryNew())
        wp = mel.create_material_expression(master, E.MaterialExpressionWorldPosition, -1400, 0)
        mask = mel.create_material_expression(master, E.MaterialExpressionComponentMask, -1200, 0)
        mask.set_editor_property("r", True)
        mask.set_editor_property("g", True)
        mel.connect_material_expressions(wp, "", mask, "")
        tile = mel.create_material_expression(master, E.MaterialExpressionScalarParameter, -1400, 200)
        tile.set_editor_property("parameter_name", "TileCm")
        tile.set_editor_property("default_value", 400.0)
        uv = mel.create_material_expression(master, E.MaterialExpressionDivide, -1000, 0)
        mel.connect_material_expressions(mask, "", uv, "A")
        mel.connect_material_expressions(tile, "", uv, "B")
        col = mel.create_material_expression(master, E.MaterialExpressionTextureSampleParameter2D, -700, -200)
        col.set_editor_property("parameter_name", "Albedo")
        col.set_editor_property("sampler_type", E.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_COLOR if vt else E.MaterialSamplerType.SAMPLERTYPE_COLOR)
        col.set_editor_property("texture", col_tex)
        nrm = mel.create_material_expression(master, E.MaterialExpressionTextureSampleParameter2D, -700, 200)
        nrm.set_editor_property("parameter_name", "Normal")
        nrm.set_editor_property("sampler_type", E.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_NORMAL if vt else E.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        nrm.set_editor_property("texture", nrm_tex)
        for e in (col, nrm):
            mel.connect_material_expressions(uv, "", e, "UVs")
        tint = mel.create_material_expression(master, E.MaterialExpressionVectorParameter, -700, -450)
        tint.set_editor_property("parameter_name", "Tint")
        tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
        mul = mel.create_material_expression(master, E.MaterialExpressionMultiply, -400, -250)
        mel.connect_material_expressions(col, "RGB", mul, "A")
        mel.connect_material_expressions(tint, "", mul, "B")
        rough = mel.create_material_expression(master, E.MaterialExpressionScalarParameter, -400, 50)
        rough.set_editor_property("parameter_name", "Roughness")
        rough.set_editor_property("default_value", 0.9)
        mel.connect_material_property(mul, "", E.MaterialProperty.MP_BASE_COLOR)
        mel.connect_material_property(nrm, "RGB", E.MaterialProperty.MP_NORMAL)
        mel.connect_material_property(rough, "", E.MaterialProperty.MP_ROUGHNESS)
        mel.recompile_material(master)
        eal.save_loaded_asset(master)
    mi_path = "/Game/Art/Environment/Fab/MI_SS_WorldGround_" + CFG["label"]
    if eal.does_asset_exist(mi_path):
        eal.delete_asset(mi_path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi = tools.create_asset(mi_path.split("/")[-1], "/Game/Art/Environment/Fab", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, master)
    mel.set_material_instance_texture_parameter_value(mi, "Albedo", col_tex)
    mel.set_material_instance_texture_parameter_value(mi, "Normal", nrm_tex)
    mel.set_material_instance_scalar_parameter_value(mi, "TileCm", cfg.get("ground_tile_cm", 400.0))
    eal.save_loaded_asset(mi)
    return mi


def prepare_diorama(world, actors, cfg):
    """Turn a studio showcase scene into an outdoor play space (see MAPS entry in CFG)."""
    x0, y0, x1, y1 = cfg["keep"]
    dropped, solid = 0, set()
    keep_cls = (unreal.WorldSettings, unreal.Brush, unreal.InstancedFoliageActor)
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if isinstance(a, keep_cls) or a.get_class().get_name() in ("Actor", "AbstractNavData", "RecastNavMesh"):
            continue
        o = a.get_actor_location()
        studio = isinstance(a, (unreal.RectLight, unreal.PostProcessVolume)) or "Demo" in a.get_class().get_name()
        if isinstance(a, unreal.StaticMeshActor):  # light bars and reflection cards above the pit
            m = a.static_mesh_component.static_mesh
            studio = studio or (m is not None and ("/Engine/" in m.get_path_name() or "VisualFramework" in m.get_path_name()))
        if studio or not (x0 <= o.x <= x1 and y0 <= o.y <= y1):
            actors.destroy_actor(a)
            dropped += 1
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.static_mesh
            if not m:
                continue
            path = m.get_path_name()
            if "Water" in path:
                c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)  # shallow flooded floor: wade through
            elif "3D_Plants" not in path and "/Scene_" in path and path not in solid:
                bs = m.get_editor_property("body_setup")
                if bs:
                    bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
                    eal.save_loaded_asset(m, False)
                    solid.add(path)
    step("diorama_strip", dropped > 0, "{} studio actors removed".format(dropped))
    step("diorama_collision", len(solid) > 0, "{} meshes complex-as-simple".format(len(solid)))

    # Walkable rim at the pit's top, out to a boundary wall, in the pack's own dirt.
    rim_mat = None
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        m = a.static_mesh_component.static_mesh
        if m and "Patch_Tracks_Dirt" in m.get_name():
            rim_mat = a.static_mesh_component.get_material(0)
            break
    if cfg.get("ground_d"):
        rim_mat = world_ground_material(cfg)
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    w, z = cfg["rim_width"], cfg["rim_z"]  # w: visual ground out into the fog; walls at cfg["wall"]
    wall_d = cfg.get("wall", 3000.0)
    # Fit the rim to the scene's real outline (not the keep box) and tuck it under the edge rocks, so there
    # is no strip of open sky between the rim and the pit (producer screenshot, first build).
    lo, hi = [1e9, 1e9], [-1e9, -1e9]
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        m = a.static_mesh_component.static_mesh
        path = m.get_path_name() if m else ""
        if "/Scene_" not in path or "3D_Plants" in path or "Water" in path:
            continue
        o, e = a.get_actor_bounds(False)
        lo = [min(lo[0], o.x - e.x), min(lo[1], o.y - e.y)]
        hi = [max(hi[0], o.x + e.x), max(hi[1], o.y + e.y)]
    tuck = cfg.get("tuck", 400.0)
    x0, y0, x1, y1 = lo[0] + tuck, lo[1] + tuck, hi[0] - tuck, hi[1] - tuck
    report["diorama_outline_m"] = [round(v / 100, 1) for v in (lo[0], lo[1], hi[0], hi[1])]
    cx, cy, hx, hy = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    # Each side's rim sits at that side's own edge height (the pit is open and lower on one side).
    unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")  # traces need it
    edge = {"N": [(x0 + (x1 - x0) * k / 12, y0) for k in range(13)], "S": [(x0 + (x1 - x0) * k / 12, y1) for k in range(13)],
            "W": [(x0, y0 + (y1 - y0) * k / 12) for k in range(13)], "E": [(x1, y0 + (y1 - y0) * k / 12) for k in range(13)]}
    side_z = {}
    for name, pts in edge.items():
        zs = sorted(v for v in (ground(world, px, py) for px, py in pts) if v is not None)
        side_z[name] = (zs[len(zs) // 2] - 30.0) if zs else z
    report["rim_side_z_m"] = {k: round(v / 100, 1) for k, v in side_z.items()}
    # A low (open) side meets the pit floor, not the rim rocks: run its slab in to the floor mesh's edge.
    inner = {"W": x0, "E": x1, "N": y0, "S": y1}
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        m = a.static_mesh_component.static_mesh
        if m and cfg.get("floor") and m.get_name() == cfg["floor"]:
            fo, fe = a.get_actor_bounds(False)
            for name in inner:
                if side_z[name] < z - 300.0:
                    inner[name] = {"W": fo.x - fe.x + tuck, "E": fo.x + fe.x - tuck,
                                   "N": fo.y - fe.y + tuck, "S": fo.y + fe.y - tuck}[name]
    report["rim_inner_m"] = {k: round(v / 100, 1) for k, v in inner.items()}
    # W/E run the full depth (corners included); N/S only span the scene, so a step between a low and a
    # high side is one short face, dressed below with the pack's ledge rocks.
    slabs = [("N", cx, y0 - w / 2, 2 * hx, w), ("S", cx, y1 + w / 2, 2 * hx, w),
             ("W", (inner["W"] + x0 - w) / 2, cy, inner["W"] - (x0 - w), 2 * hy + 2 * w),
             ("E", (inner["E"] + x1 + w) / 2, cy, (x1 + w) - inner["E"], 2 * hy + 2 * w)]
    for name, sx, sy, lx, ly in slabs:
        slab = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(sx, sy, side_z[name] - 50), unreal.Rotator(roll=0, pitch=0, yaw=0))
        slab.set_actor_label("SS_MAP_Rim_" + name)
        slab.static_mesh_component.set_static_mesh(cube)
        slab.set_actor_scale3d(unreal.Vector(lx / 100, ly / 100, 1.0))
        if rim_mat:
            slab.static_mesh_component.set_material(0, rim_mat)
        wx = {"W": x0 - wall_d, "E": x1 + wall_d}.get(name, cx)
        wy = {"N": y0 - wall_d, "S": y1 + wall_d}.get(name, cy)
        wall = actors.spawn_actor_from_class(unreal.BlockingVolume, unreal.Vector(wx, wy, side_z[name] + 2000), unreal.Rotator(roll=0, pitch=0, yaw=0))
        wall.set_actor_label("SS_MAP_Boundary_" + name)
        wall.set_actor_scale3d(unreal.Vector((2 * hx + 2 * wall_d if name in "NS" else 200) / 200,
                                             (2 * hy + 2 * wall_d if name in "WE" else 200) / 200, 6000 / 200))
    rock = unreal.load_asset(cfg["cliff_rock"]) if cfg.get("cliff_rock") else None
    cliffs = 0
    for side, fx in (("W", x0), ("E", x1)):
        for other, ya, yb in (("N", y0 - wall_d, y0), ("S", y1, y1 + wall_d)):
            drop = side_z[other] - side_z[side]
            if rock is None or abs(drop) < 250.0:
                continue
            low = min(side_z[other], side_z[side])
            for k in range(4):  # rocks along the face, sunk into the low ground
                py = ya + (yb - ya) * (k + 0.5) / 4
                r = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(fx, py, low + abs(drop) * 0.35),
                                                  unreal.Rotator(roll=0, pitch=0, yaw=37.0 * k + (0 if side == "W" else 180)))
                r.static_mesh_component.set_static_mesh(rock)
                r.set_actor_scale3d(unreal.Vector(0.55, 0.55, max(0.6, abs(drop) / 1000.0)))
                r.set_actor_label("SS_MAP_RimCliff_{}{}_{}".format(side, other, k))
                cliffs += 1
    report["rim_cliff_rocks"] = cliffs
    import random
    rng = random.Random(11)
    kit = [unreal.load_asset(p) for p in cfg.get("scatter", [])]
    kit = [k for k in kit if k]
    band = wall_d - 300.0
    placed_scatter = 0
    for n in range(cfg.get("scatter_count", 0) if kit else 0):
        side = rng.choice("NNSSWE")
        if side in "NS":
            px = rng.uniform(x0, x1)
            py = y0 - rng.uniform(300.0, band) if side == "N" else y1 + rng.uniform(300.0, band)
        else:
            py = rng.uniform(y0 - band, y1 + band)
            px = x0 - rng.uniform(300.0, band) if side == "W" else x1 + rng.uniform(300.0, band)
        mesh = kit[n % len(kit)]
        sc = rng.uniform(0.7, 1.3)
        d = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(px, py, side_z[side] - 20.0),
                                          unreal.Rotator(roll=0, pitch=0, yaw=rng.uniform(0, 360)))
        d.static_mesh_component.set_static_mesh(mesh)
        d.set_actor_scale3d(unreal.Vector(sc, sc, sc))
        d.set_actor_label("SS_MAP_RimDress_{:02d}".format(n))
        placed_scatter += 1
    report["rim_scatter"] = placed_scatter
    step("diorama_rim", True, "4 rim slabs, material {}".format(rim_mat.get_name() if rim_mat else "default"))

    # Outdoor daylight (as light_dryriver.py): the showcase was lit by studio rect lights only.
    sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(cx, cy, 5000), unreal.Rotator(roll=0, pitch=-48, yaw=35))
    c = sun.light_component
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    c.set_intensity(10.0)
    c.set_light_color(unreal.LinearColor(1.0, 0.95, 0.86, 1.0))
    c.set_editor_property("atmosphere_sun_light", True)
    actors.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(roll=0, pitch=0, yaw=0))
    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(cx, cy, 3000), unreal.Rotator(roll=0, pitch=0, yaw=0))
    sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("real_time_capture", True)
    fog = actors.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(cx, cy, 0), unreal.Rotator(roll=0, pitch=0, yaw=0))
    fog.component.set_editor_property("fog_density", 0.03)
    fog.component.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.72, 0.68, 0.62, 1.0))
    ppv = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator(roll=0, pitch=0, yaw=0))
    ppv.set_editor_property("unbound", True)
    st = ppv.settings
    st.set_editor_property("override_auto_exposure_min_brightness", True)
    st.set_editor_property("auto_exposure_min_brightness", 0.5)
    st.set_editor_property("override_auto_exposure_max_brightness", True)
    st.set_editor_property("auto_exposure_max_brightness", 2.0)
    ppv.set_editor_property("settings", st)
    step("diorama_daylight", True, "sun, atmosphere, sky light, fog, post-process")


def level_pass():
    if eal.does_asset_exist(CFG["dst"]):
        eal.delete_asset(CFG["dst"])
    world = unreal.EditorLoadingAndSavingUtils.load_map(CFG["src"])
    if not step("load_map", world is not None, CFG["src"]):
        return
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for cls in (unreal.CineCameraActor, unreal.PlayerStart):
        for a in unreal.GameplayStatics.get_all_actors_of_class(world, cls):
            actors.destroy_actor(a)
    if "diorama" in CFG:
        prepare_diorama(world, actors, CFG["diorama"])
    unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")  # traces need it

    lo, hi = play_bounds(world)
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    along_x = (hi[0] - lo[0]) >= (hi[1] - lo[1])
    half = ((hi[0] - lo[0]) if along_x else (hi[1] - lo[1])) / 2
    report["bounds_m"] = [[round(v / 100) for v in lo], [round(v / 100) for v in hi]]

    def at(t, side=0.0):  # t in -1..1 along the long axis, side offset cm
        return (cx + t * half, cy + side) if along_x else (cx + side, cy + t * half)

    start_class = unreal.load_class(None, "/Script/LyraGame.LyraPlayerStart")
    starts = 0
    for side, t0 in (("A", -0.82), ("B", 0.82)):
        # Step inward until the primary start finds ground (map edges can be open).
        t = t0
        while abs(t) > 0.5 and ground(world, *at(t)) is None:
            t -= 0.03 if t > 0 else -0.03
        yaw = (0.0 if t < 0 else 180.0) if along_x else (90.0 if t < 0 else -90.0)
        offsets = [0.0] + [(i // 2 + 1) * SPACING_CM * (1 if i % 2 == 0 else -1) for i in range(EXTRA_STARTS)]
        for n, off in enumerate(offsets):
            x, y = at(t, off)
            z = ground(world, x, y)
            if z is None:
                continue
            s = actors.spawn_actor_from_class(start_class, unreal.Vector(x, y, z + 100), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
            s.set_actor_label("SS_MAP_{}_Deploy{}{}".format(CFG["label"], side, "" if n == 0 else "_Extra{:02d}".format(n)))
            starts += 1
    step("starts", starts >= 2 * (EXTRA_STARTS + 1) - 4, starts)

    placed = []
    for index, (t, name) in enumerate(zip((-0.42, 0.0, 0.42), CFG["objectives"])):
        x, y = at(t)
        z = ground(world, x, y)
        if z is None:
            continue
        o = actors.spawn_actor_from_class(unreal.SSObjectiveActor, unreal.Vector(x, y, z), unreal.Rotator(roll=0, pitch=0, yaw=0))
        o.set_actor_label("SS_MAP_{}_Obj{}_{}".format(CFG["label"], "ABC"[index], name.replace(" ", "")))
        o.set_editor_property("sequence_index", index)
        o.set_editor_property("objective_name", unreal.Text(name))
        o.get_component_by_class(unreal.SphereComponent).set_sphere_radius(CFG["radius"])
        placed.append(name)
    step("objectives", len(placed) == 3, placed)

    d = actors.spawn_actor_from_class(unreal.SSObjectiveAssaultDirector, unreal.Vector(cx, cy, 0), unreal.Rotator(roll=0, pitch=0, yaw=0))
    d.set_actor_label("SS_ObjectiveAssault_Director")
    vol = actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume, unreal.Vector(cx, cy, (lo[2] + hi[2]) / 2), unreal.Rotator(roll=0, pitch=0, yaw=0))
    vol.set_actor_scale3d(unreal.Vector((hi[0] - lo[0]) / 200 + 5, (hi[1] - lo[1]) / 200 + 5, max(20.0, (hi[2] - lo[2]) / 200 + 10)))
    vol.set_actor_label("SS_MAP_{}_NavBounds".format(CFG["label"]))

    ws = world.get_world_settings()
    ok = unreal.SSObjectivesEditorLibrary.set_property_from_text(ws, "DefaultGameplayExperience", EXP_CLASS)
    step("world_experience", ok)
    step("save_map", unreal.EditorLoadingAndSavingUtils.save_map(world, CFG["dst"]), CFG["dst"])


def reachable(world, a, b):
    p = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, a, b)
    return p is not None and p.is_valid() and not p.is_partial()


def nav_pass():
    world = unreal.EditorLoadingAndSavingUtils.load_map(CFG["dst"])
    if not unreal.GameplayStatics.get_all_actors_of_class(world, unreal.RecastNavMesh):
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
            unreal.RecastNavMesh, unreal.Vector(0, 0, 0), unreal.Rotator(roll=0, pitch=0, yaw=0))
    for _ in range(2):
        unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")
    objs = sorted(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SSObjectiveActor), key=lambda a: a.get_actor_label())
    starts = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
    centre = objs[1].get_actor_location()
    ok_to = lambda q: reachable(world, q, centre) and reachable(world, centre, q)

    def relocate(c):
        if ok_to(c):
            return c
        for r in range(5, 60, 5):
            for k in range(16):
                ang = k * math.pi / 8
                q = unreal.NavigationSystemV1.project_point_to_navigation(
                    world, unreal.Vector(c.x + r * 100 * math.cos(ang), c.y + r * 100 * math.sin(ang), c.z),
                    None, None, unreal.Vector(300, 300, 3000))
                if q and ok_to(q):
                    return q
        return None

    # Layout from walkable space: sample a grid of nav points reachable from the
    # centre, take the two farthest apart as deployments and space the objectives
    # between them. Robust to walled or watery map ends.
    lo, hi = play_bounds(world)
    grid = []
    step_cm = 500.0
    x = lo[0]
    while x <= hi[0]:
        y = lo[1]
        while y <= hi[1]:
            q = unreal.NavigationSystemV1.project_point_to_navigation(
                world, unreal.Vector(x, y, centre.z), None, None, unreal.Vector(200, 200, 3000))
            if q:
                grid.append(q)
            y += step_cm
        x += step_cm
    # Seed from the grid point that reaches the most of the map (largest walkable
    # island), not from wherever the centre objective happened to land.
    import random as _random
    _random.seed(7)
    seeds = _random.sample(grid, min(24, len(grid))) + [centre]
    best, reach = centre, []
    for seed in seeds:
        r = [q for q in grid if reachable(world, seed, q)]
        if len(r) > len(reach):
            best, reach = seed, r
    centre = best
    report["grid"] = {"points": len(grid), "reachable": len(reach)}
    moves = {}
    if len(reach) >= 3:
        # Deployments: from a spread sample of the island, the pair that is far
        # apart both on foot (nav path length) and in a straight line (sight):
        # score = min(walk, 1.6 x straight). Straight line alone picked two
        # ends of a walled canal 70 m apart; walk alone picked two banks 20 m
        # apart across the water.
        sample = [max(reach, key=lambda q: (q - centre).length())]
        while len(sample) < min(36, len(reach)):
            sample.append(max(reach, key=lambda q: min((q - c).length() for c in sample)))
        best_score, best_len, p1, p2, route_pts = -1.0, 0.0, None, None, []
        for i, a in enumerate(sample):
            for b in sample[i + 1:]:
                path = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, a, b)
                if not (path and path.is_valid() and not path.is_partial()):
                    continue
                score = min(path.get_path_length(), 1.6 * (a - b).length())
                if score > best_score:
                    best_score, best_len, p1, p2 = score, path.get_path_length(), a, b
                    route_pts = list(path.get_editor_property("path_points"))
        report["deploy_separation_m"] = round((p1 - p2).length() / 100)
        report["deploy_walk_m"] = round(best_len / 100)

        def along(t):  # point at fraction t of the route polyline
            goal, run = best_len * t, 0.0
            for a, b in zip(route_pts, route_pts[1:]):
                seg = (b - a).length()
                if run + seg >= goal and seg > 0:
                    return a + (b - a) * ((goal - run) / seg)
                run += seg
            return route_pts[-1]

        # Objectives along the walking route, so each leg is a real advance.
        for a, t in zip(objs, (0.28, 0.5, 0.72)):
            want = along(t)
            q = min(reach, key=lambda r: (r - want).length())  # stay on the connected island
            a.set_actor_location(q, False, False)
            moves[a.get_actor_label()] = round((q - want).length() / 100, 1)
        for side, anchor in (("A", p1), ("B", p2)):
            label = "SS_MAP_{}_Deploy{}".format(CFG["label"], side)
            group = sorted([s for s in starts if s.get_actor_label().startswith(label)], key=lambda s: s.get_actor_label())
            toward = (p2 - p1) if side == "A" else (p1 - p2)
            toward.z = 0
            toward = toward / max(toward.length(), 1.0)
            across = unreal.Vector(-toward.y, toward.x, 0)
            for n, st in enumerate(group):
                off = ((n + 1) // 2) * 300.0 * (1 if n % 2 else -1)
                want = anchor + across * off
                q = unreal.NavigationSystemV1.project_point_to_navigation(world, want, None, None, unreal.Vector(400, 400, 3000))
                if not q or not reachable(world, centre, q):
                    q = min(reach, key=lambda r: (r - want).length())
                st.set_actor_location(q + unreal.Vector(0, 0, 100), False, False)
                st.set_actor_rotation(unreal.MathLibrary.conv_vector_to_rotator(toward), False)
            moves[label] = "placed at walkable end"
    report["moves_m"] = moves
    starts = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
    pts = {s.get_actor_label(): s.get_actor_location() for s in starts}
    route = [pts.get("SS_MAP_{}_DeployA".format(CFG["label"]))] + [o.get_actor_location() for o in objs] + \
            [pts.get("SS_MAP_{}_DeployB".format(CFG["label"]))]
    legs = [bool(a and b and reachable(world, a, b)) for a, b in zip(route, route[1:])]
    report["legs"] = legs
    step("all_legs", all(legs), legs)
    step("save_map", unreal.EditorLoadingAndSavingUtils.save_current_level(), CFG["dst"])


try:
    if not CFG:
        raise RuntimeError("SS_MAP must be one of " + ", ".join(MAPS))
    level_pass() if PASS == "level" else nav_pass()
    report["ok"] = all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[ObjectiveMap] {} {} ok={}".format(KEY, PASS, report["ok"]))
