# Southern Spear - fair objective layout for the three-objective environment maps.
#
# Objective Assault opens every round on objective A and takes A, B, C in order
# (ADR-018), so an objective nearer one deployment hands that team the opening.
# The environment-map builders spaced A-B-C along the deployment line, which put
# A a third of the way from Team One (Saltbush: 46 m vs 134 m on foot).
#
# This lays the three objectives ACROSS the map instead: B at the walkable point
# closest to equal walking distance from both deployments, A and C on the left
# and right flanks at similar equal-walk points. Deployments (the team-tagged
# starts) are not moved; run layout_spawns.py afterwards.
#
# Report: Build/objective_layout.json - per objective the walk (m) from each
# deployment and the imbalance. SS_MAPS limits the maps.

import json
import math
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", "objective_layout.json")
# Fictional names (ADR-016), left flank / centre / right flank.
NAMES = {
    "L_RedGum_01": ["North Paddock", "Homestead", "South Paddock"],
    "L_Saltbush_01": ["Windmill", "Stock Yards", "Dry Dam"],
    "L_SelatCanal_01": ["Footbridge", "Market Row", "Pump House"],
}
MAPS = [m for m in os.environ.get("SS_MAPS", ",".join(NAMES)).split(",") if m]
report = {"ok": False, "maps": {}, "errors": []}
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def walk(world, a, b):
    p = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, a, b)
    return p.get_path_length() if p and p.is_valid() and not p.is_partial() else None


def layout(name):
    world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/" + name)
    if not world:
        return {"error": "load failed"}
    for _ in range(2):
        unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")
    objs = sorted(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SSObjectiveActor),
                  key=lambda o: o.get_editor_property("sequence_index"))
    starts = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
    teams = {t: [s.get_actor_location() for s in starts if str(s.get_editor_property("player_start_tag")) == t]
             for t in ("TeamOne", "TeamTwo")}
    if len(objs) != 3 or not teams["TeamOne"] or not teams["TeamTwo"]:
        return {"error": "objectives={} tagged starts={}".format(len(objs), {k: len(v) for k, v in teams.items()})}
    # Anchor on the real start nearest each team's centroid (a centroid can
    # project onto a disconnected patch, e.g. across a canal).
    def anchor(locs):
        c = sum(locs, unreal.Vector()) / len(locs)
        nearest = min(locs, key=lambda l: (l - c).length())
        return unreal.NavigationSystemV1.project_point_to_navigation(world, nearest, None, None, unreal.Vector(200, 200, 400))
    one, two = anchor(teams["TeamOne"]), anchor(teams["TeamTwo"])
    if not one or not two:
        return {"error": "deployment anchors not on navigation"}

    axis = two - one
    axis.z = 0
    sep = axis.length()
    axis = axis / sep
    lateral = unreal.Vector(-axis.y, axis.x, 0)
    mid = (one + two) / 2

    # Grid over the middle band of the map, in the deployment frame.
    step = max(400.0, sep / 45.0)
    half_along, half_across = 0.3 * sep, max(0.6 * sep, 4000.0)
    points = []
    u = -half_along
    while u <= half_along:
        v = -half_across
        while v <= half_across:
            want = mid + axis * u + lateral * v
            q = unreal.NavigationSystemV1.project_point_to_navigation(world, want, None, None, unreal.Vector(step / 2, step / 2, 3000))
            if q:
                wa, wb = walk(world, one, q), walk(world, two, q)
                if wa and wb:
                    d = q - mid
                    points.append({"q": q, "wa": wa, "wb": wb, "along": d.x * axis.x + d.y * axis.y,
                                   "across": d.x * lateral.x + d.y * lateral.y,
                                   "imb": abs(wa - wb) / ((wa + wb) / 2)})
            v += step
        u += step
    if len(points) < 3:
        return {"error": "only {} two-way reachable points in the middle band".format(len(points))}

    # Centre: most even, then nearest the middle.
    centre = min(points, key=lambda p: p["imb"] + 0.5 * abs(p["across"]) / sep + 0.5 * abs(p["along"]) / sep)
    # Flanks: even, well to each side (as far as the walkable band allows).
    spread = min(0.35 * sep, 12000.0)
    picks = []
    for side in (-1, 1):
        cands = [p for p in points if p["across"] * side > 0.4 * spread and p["imb"] < 0.15]
        if cands:
            picks.append(min(cands, key=lambda p: p["imb"] * 2 + abs(abs(p["across"]) - spread) / sep
                             + 0.5 * abs(p["along"]) / sep))
    if len(picks) == 2:
        order = [picks[0], centre, picks[1]]
        result_layout = "flanks"
    else:
        # Narrow walkable band: the two even points farthest from the centre
        # and from each other, left to right.
        # Loosen evenness only as far as needed for the objectives to stand
        # at least MIN_GAP apart (Saltbush packed three within 16 m at 12%).
        MIN_GAP = 4000.0
        first = second = None
        for limit in (0.12, 0.18, 0.25, 0.35):
            fair = [p for p in points if p["imb"] < limit and p is not centre]
            if len(fair) < 2:
                continue
            first = max(fair, key=lambda p: (p["q"] - centre["q"]).length())
            second = max(fair, key=lambda p: min((p["q"] - centre["q"]).length(), (p["q"] - first["q"]).length()))
            if min((first["q"] - centre["q"]).length(), (second["q"] - centre["q"]).length(), (first["q"] - second["q"]).length()) >= MIN_GAP:
                break
        if not first or not second:
            return {"error": "fewer than three evenly reachable points"}
        order = sorted([first, centre, second], key=lambda p: p["across"])
        result_layout = "spread"

    result = {"layout": result_layout, "grid_points": len(points), "deploy_separation_m": round(sep / 100), "objectives": []}
    for o, p, label in zip(objs, order, NAMES.get(name, [None] * 3)):
        o.set_actor_location(p["q"], False, False)
        if label:
            o.set_editor_property("objective_name", unreal.Text(label))
            parts = o.get_actor_label().split("_")
            o.set_actor_label("_".join(parts[:4]) + "_" + label.replace(" ", ""))
        result["objectives"].append({"name": label, "walk_team_one_m": round(p["wa"] / 100),
                                     "walk_team_two_m": round(p["wb"] / 100), "imbalance_pct": round(100 * p["imb"])})
    legs = [walk(world, a["q"], b["q"]) for a, b in zip(order, order[1:])]
    result["legs_m"] = [round(l / 100) if l else None for l in legs]
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
unreal.log("[ObjectiveLayout] ok={} {}".format(report["ok"], json.dumps(report["maps"])))
