# Southern Spear - lay out each map's deployments: 8 starts per team (ADR-018 fairness).
#
# The final authority on player starts for every Objective Assault map. For
# each team (anchor = the centroid of its tagged starts, else a 2-means split,
# Team One nearer objective A) it samples walkable ground around the anchor,
# rejects points hard against walls or under low cover, and keeps 8 starts by
# farthest-point sampling (>= 2.5 m apart), preferring points with no sight
# line to the enemy deployment, each reachable from the anchor and facing the
# centre objective. Replaces the old starts, tags them
# (PlayerStartTag TeamOne / TeamTwo) and saves.
#
# Report: Build/spawn_layout.json - per map and team: starts, minimum spacing,
# spread, and spawn exposure (start pairs with a clear eye-height line of sight
# to an enemy start). Run after build_objective_map.py / the Dry River pipeline.
#   SS_MAPS=L_RedGum_01,L_SelatCanal_01 limits the maps (default: all four).

import json
import math
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "spawn_layout.json")
ALL = ["L_RedGum_01", "L_DryRiver_01", "L_Saltbush_01", "L_SelatCanal_01"]
MAPS = [m for m in os.environ.get("SS_MAPS", ",".join(ALL)).split(",") if m]
PER_TEAM = 8
SPACING = 250.0      # cm between starts
RADIUS = 1800.0      # cm sampled around the anchor
WALL_CLEAR = 70.0    # cm free in eight directions at chest height
HEADROOM = 200.0     # cm free overhead
MAX_WALK = 20000.0   # cm; a deployment farther than this from the centre objective slides in
report = {"ok": False, "maps": {}, "errors": []}
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def trace(world, a, b):
    return unreal.SystemLibrary.line_trace_single(
        world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)


def reachable(world, a, b):
    p = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, a, b)
    return p is not None and p.is_valid() and not p.is_partial()


def clear(world, q):
    chest = q + unreal.Vector(0, 0, 90)
    for k in range(8):
        ang = k * math.pi / 4
        if trace(world, chest, chest + unreal.Vector(math.cos(ang) * WALL_CLEAR, math.sin(ang) * WALL_CLEAR, 0)):
            return False
    return trace(world, q + unreal.Vector(0, 0, 30), q + unreal.Vector(0, 0, HEADROOM)) is None


def two_means(points):
    a, b = min(points, key=lambda p: p.x + p.y), max(points, key=lambda p: p.x + p.y)
    for _ in range(12):
        ga = [p for p in points if (p - a).length() <= (p - b).length()]
        gb = [p for p in points if (p - a).length() > (p - b).length()]
        if not ga or not gb:
            break
        a, b = sum(ga, unreal.Vector()) / len(ga), sum(gb, unreal.Vector()) / len(gb)
    return a, b


def candidates(world, anchor, goal):
    out = []
    r = 0.0
    while r <= RADIUS:
        n = 1 if r == 0 else max(8, int(2 * math.pi * r / 180))
        for k in range(n):
            ang = 2 * math.pi * k / n
            q = unreal.NavigationSystemV1.project_point_to_navigation(
                world, unreal.Vector(anchor.x + r * math.cos(ang), anchor.y + r * math.sin(ang), anchor.z),
                None, None, unreal.Vector(120, 120, 400))
            if q and abs(q.z - anchor.z) < 450 and clear(world, q) and reachable(world, anchor, q) and reachable(world, q, goal):
                out.append(q)
        r += 150.0
    return out


def pick(points, anchor, hidden):
    """Farthest-point sampling, hidden points (no sight line to the enemy
    deployment) first, then the rest; spacing relaxes if the ground is tight."""
    if not points:
        return []
    pools = [p for p in points if hidden(p)], points
    chosen = [min(pools[0] or points, key=lambda p: (p - anchor).length())]
    for pool in pools:
        for spacing in (SPACING, 180.0, 120.0):
            while len(chosen) < PER_TEAM and pool:
                best = max(pool, key=lambda p: min((p - c).length() for c in chosen))
                if min((best - c).length() for c in chosen) < spacing:
                    break
                chosen.append(best)
            if len(chosen) >= PER_TEAM:
                return chosen[:PER_TEAM]
    return chosen[:PER_TEAM]


def layout(name):
    world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/" + name)
    if not world:
        return {"error": "load failed"}
    for _ in range(2):
        unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")
    objs = sorted(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SSObjectiveActor),
                  key=lambda o: o.get_editor_property("sequence_index"))
    starts = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
    if not objs or len(starts) < 2:
        return {"error": "objectives={} starts={}".format(len(objs), len(starts))}
    tagged = {t: [s.get_actor_location() for s in starts if str(s.get_editor_property("player_start_tag")) == t]
              for t in ("TeamOne", "TeamTwo")}
    if tagged["TeamOne"] and tagged["TeamTwo"]:
        anchors = {t: sum(p, unreal.Vector()) / len(p) for t, p in tagged.items()}
    else:
        ca, cb = two_means([s.get_actor_location() for s in starts])
        first = objs[0].get_actor_location()
        anchors = {"TeamOne": ca, "TeamTwo": cb} if (ca - first).length() <= (cb - first).length() else {"TeamOne": cb, "TeamTwo": ca}
    label = name.replace("L_", "").replace("_01", "")
    centre = objs[len(objs) // 2].get_actor_location()
    start_class = unreal.load_class(None, "/Script/LyraGame.LyraPlayerStart")

    result, placed = {}, {}
    eye = unreal.Vector(0, 0, 160)
    # Every start must reach the objectives: the centre objective is the goal,
    # and an anchor that cannot reach it (a centroid on a disconnected patch)
    # is replaced by the nearest existing start that can.
    goal = unreal.NavigationSystemV1.project_point_to_navigation(
        world, centre, None, None, unreal.Vector(300, 300, 1000)) or centre
    projected = {}
    for t, a in anchors.items():
        q = unreal.NavigationSystemV1.project_point_to_navigation(world, a, None, None, unreal.Vector(400, 400, 1000)) or a
        if not reachable(world, q, goal):
            own = [s.get_actor_location() for s in starts if str(s.get_editor_property("player_start_tag")) == t] or                   [s.get_actor_location() for s in starts]
            for loc in sorted(own, key=lambda l: (l - a).length()):
                n = unreal.NavigationSystemV1.project_point_to_navigation(world, loc, None, None, unreal.Vector(200, 200, 400))
                if n and reachable(world, n, goal):
                    q = n
                    break
        # Long approaches (Red Gum: ~300 m to every objective, no captures in
        # 3 min) slide the deployment toward the centre objective, 5% at a
        # time, until the walk is within MAX_WALK; both teams alike.
        base = q
        for k in range(1, 15):
            p = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, q, goal)
            if not p or not p.is_valid() or p.is_partial() or p.get_path_length() <= MAX_WALK:
                break
            n = unreal.NavigationSystemV1.project_point_to_navigation(
                world, base + (goal - base) * (0.05 * k), None, None, unreal.Vector(600, 600, 2000))
            if n and reachable(world, n, goal):
                q = n
        projected[t] = q
    for team, side in (("TeamOne", "A"), ("TeamTwo", "B")):
        anchor = projected[team]
        enemy = projected["TeamTwo" if team == "TeamOne" else "TeamOne"] + eye
        cand = candidates(world, anchor, goal)
        chosen = pick(cand, anchor, lambda q: trace(world, q + eye, enemy) is not None)
        placed[team] = chosen
        spacing = min(((a - b).length() for i, a in enumerate(chosen) for b in chosen[i + 1:]), default=0.0)
        spread = max(((a - anchor).length() for a in chosen), default=0.0)
        result[team] = {"candidates": len(cand), "starts": len(chosen),
                        "min_spacing_m": round(spacing / 100, 1), "spread_m": round(spread / 100, 1)}

    if min(len(p) for p in placed.values()) < PER_TEAM:
        result["error"] = "not enough clear ground for {} starts per team; map left unchanged".format(PER_TEAM)
        return result

    for s in starts:
        eas.destroy_actor(s)
    for team, side in (("TeamOne", "A"), ("TeamTwo", "B")):
        for n, q in enumerate(placed[team]):
            face = centre - q
            yaw = math.degrees(math.atan2(face.y, face.x))
            s = eas.spawn_actor_from_class(start_class, q + unreal.Vector(0, 0, 100), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
            s.set_actor_label("SS_MAP_{}_Deploy{}{}".format(label, side, "" if n == 0 else "_{:02d}".format(n)))
            s.set_editor_property("player_start_tag", team)

    # Spawn exposure: start pairs with a clear line of sight between eyes.
    exposed = sum(1 for a in placed["TeamOne"] for b in placed["TeamTwo"] if trace(world, a + eye, b + eye) is None)
    result["exposed_pairs"] = "{}/{}".format(exposed, PER_TEAM * PER_TEAM)
    result["team_separation_m"] = round((sum(placed["TeamOne"], unreal.Vector()) / PER_TEAM -
                                         sum(placed["TeamTwo"], unreal.Vector()) / PER_TEAM).length() / 100)
    path = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, placed["TeamOne"][0], placed["TeamTwo"][0])
    result["walk_separation_m"] = round(path.get_path_length() / 100) if path and path.is_valid() else None
    # Fairness: each team's walk from its deployment to every objective. The
    # round opens on objective A, so the A column should be close to even.
    for team in ("TeamOne", "TeamTwo"):
        walks = []
        for o in objs:
            target = unreal.NavigationSystemV1.project_point_to_navigation(
                world, o.get_actor_location(), None, None, unreal.Vector(300, 300, 1000)) or o.get_actor_location()
            p = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, placed[team][0], target)
            walks.append(round(p.get_path_length() / 100) if p and p.is_valid() and not p.is_partial() else None)
        result[team]["walk_to_objectives_m"] = walks
    result["saved"] = les.save_current_level()
    return result


try:
    for m in MAPS:
        report["maps"][m] = layout(m)
    report["ok"] = all(r.get("saved") for r in report["maps"].values())
except Exception:
    report["errors"].append(traceback.format_exc())
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[SpawnLayout] ok={} {}".format(report["ok"], json.dumps(report["maps"])))
