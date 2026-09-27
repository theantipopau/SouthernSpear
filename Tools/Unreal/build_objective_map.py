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
        if isinstance(a, (unreal.StaticMeshActor, unreal.LandscapeProxy)):
            o, e = a.get_actor_bounds(False)
            if e.x > 100000 or e.y > 100000:
                continue  # skyboxes, horizon rings
            for i, (oc, ec) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))):
                lo[i], hi[i] = min(lo[i], oc - ec), max(hi[i], oc + ec)
    return lo, hi


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
