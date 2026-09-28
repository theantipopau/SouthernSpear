# Southern Spear - measure the Objective Assault maps against the Dry River
# design rules. Read only: it loads each map, reports, and saves nothing, so it
# is safe to run against a map another tool is still dressing.
#
# The design rules live in Docs/MAPS_DRYRIVER.md and were written for the
# hand-built 260 x 180 m blockout, not for the Fab environment maps. Until now
# nothing measured them, so "Saltbush is a good FPS map" was an opinion. This
# samples ground and traces at eye and chest height to turn each rule into a
# number:
#
#   open crossing   the largest stretch a player crosses with no cover within a
#                   clear radius (chest-height traces). Target 20 m.
#   hard:soft       static meshes by crouch-over height, target 1:3.
#   close quarters  clear sightlines at 3, 5, 8 and 15 m from sampled ground.
#                   The design intends close combat to be possible.
#   sightlines      distribution of clear eye-height sightlines between sampled
#                   positions, reported against the map's own diagonal as well
#                   as the absolute 220 m figure, which only means something on
#                   a map the size the rule was written for.
#   objectives      cover within 20 m, overwatch beyond 40 m, walk parity
#                   between the teams (ADR-018).
#   deployments     starts per team, spacing, cross-team exposure.
#
# Report: Build/map_playability.json and .md, rewritten after every map so a
# long run is still observable. "rules" lists {rule, target, measured, pass}.
# This is an audit, not a gate: a fail is a finding, never a reason to move an
# objective by itself.
#
# Two engine behaviours shaped this script and are worth knowing before
# editing it:
#
#   Navigation is locked while a map loads, so BUILDPATHS is a no-op and path
#   queries run against the navmesh stored in the level. Projecting to
#   navigation must be seeded from the traced ground height: seeded from the
#   middle of the map's bounding box it silently misses on any map with a tall
#   z range, which reads as "no navmesh" on a map that has one.
#
#   find_path_to_location_synchronously floods the whole navmesh when the goal
#   is on an island the start cannot reach. On one Dry River objective that
#   took nine minutes and nothing can interrupt it, so walking distance is
#   measured with nav_chain: a polyline of projected points along the straight
#   line, which reports "unreachable" by failing instead of by stalling.
#
#   SS_MAPS=L_SelatCanal_01 limits the maps (default: all four).
#   SS_SAMPLE=<n> walkable sample points (default 220).
#   SS_OUT=<name>.json writes somewhere else, for re-running one map without
#   overwriting the others' results.

import json
import math
import os
import random
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
REPORT = os.path.join(PROJECT_DIR, "Build", os.environ.get("SS_OUT", "map_playability.json"))
MD = REPORT[:-5] + ".md"
PROGRESS = os.path.join(PROJECT_DIR, "Build", "map_playability.progress")
ALL = ["L_DryRiver_01", "L_RedGum_01", "L_Saltbush_01", "L_SelatCanal_01"]
MAPS = [m for m in os.environ.get("SS_MAPS", ",".join(ALL)).split(",") if m]
SAMPLE = int(os.environ.get("SS_SAMPLE", "220"))

# Dry River reference values (Docs/MAPS_DRYRIVER.md). Centimetres internally.
MAX_OPEN_CROSSING = 2000.0   # 20 m: no player crosses more open ground
MAX_SIGHTLINE = 22000.0      # 220 m: longest sightline the blockout allows
BLOCKOUT_DIAGONAL = 31600.0  # 260 x 180 m corner to corner
HARD_COVER_H = 140.0         # a 1.4 m crate is hard; below that you can vault
SOFT_COVER_H = 60.0          # below 0.6 m is a kerb, not cover
CHEST = 90.0                 # cm, chest height for the open-crossing test
EYE = 160.0                  # cm, eye height for sightlines
PROBE = 200.0                # cm, trace step
CAP = 3000.0                 # cm, give up looking for cover past 30 m
PAIRS = 3000                 # sightline pairs, sampled not exhaustive
SHORT = (300.0, 500.0, 800.0, 1500.0)   # close-quarters probe distances

report = {"ok": False, "maps": {}, "errors": []}


def say(text):
    with open(PROGRESS, "a") as fh:
        fh.write(text + "\n")


def flush():
    with open(REPORT, "w") as fh:
        json.dump(report, fh, indent=1)


def blocked(world, a, b):
    """True when something solid sits between a and b."""
    return bool(unreal.SystemLibrary.line_trace_single(
        world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
        unreal.DrawDebugTrace.NONE, True))


def ground_z(world, x, y):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, 50000), unreal.Vector(x, y, -50000),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
        unreal.DrawDebugTrace.NONE, True)
    return None if hit is None else hit.to_dict()["impact_point"].z


def nav(world, p, ext):
    try:
        return unreal.NavigationSystemV1.project_point_to_navigation(world, p, None, None, ext)
    except Exception:
        return None


def nav_chain(world, a, b, step=500.0):
    """On-foot distance in metres as (length, complete).

    Projects a polyline of points along the straight line and sums it. It
    ignores detours the navmesh would take, so it reads short, but the error
    applies to both teams equally, which is all the fairness comparison needs.

    A straight line that leaves the navmesh is normal, not a disconnection: on
    Saltbush it reported every objective as unreachable for one team. When the
    chain breaks it is retried with a lateral offset, and failing that it
    returns the distance covered so far with complete=False, so the caller can
    report a lower bound instead of a wrong "no route".
    """
    d = b - a
    length = d.length()
    if length < 1.0:
        return 0.0, True
    steps = max(2, int(length / step))
    side = unreal.Vector(-d.y, d.x, 0)
    side = side / side.length() if side.length() > 1.0 else unreal.Vector(1, 0, 0)
    best_partial = (0.0, False)
    for offset in (0.0, 1000.0, -1000.0, 2000.0, -2000.0, 3000.0, -3000.0):
        total, prev, ok = 0.0, None, True
        for k in range(steps + 1):
            p = a + d * (k / float(steps)) + side * offset
            q = nav(world, p, unreal.Vector(400, 400, 800))
            if q is None:
                ok = False
                break
            if prev is not None:
                seg = (q - prev).length()
                if seg > step * 4:      # the chain jumped something; not a walk
                    ok = False
                    break
                total += seg
            prev = q
        if ok:
            return total / 100.0, True
        if total > best_partial[0]:
            best_partial = (total / 100.0, False)
    return best_partial


def play_bounds(world):
    """Bounds of the level's geometry, and its navigation volume.

    Mesh bounds can be far larger than the playable area (terrain skirts, a
    water plane), so both are reported or "31% nav coverage" reads as a defect
    when it is just how much landscape sits outside the volume.
    """
    lo, hi = [1e9] * 3, [-1e9] * 3
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if isinstance(a, (unreal.StaticMeshActor, unreal.LandscapeProxy)):
            o, e = a.get_actor_bounds(False)
            if e.x > 100000 or e.y > 100000:
                continue  # sky dome, horizon ring
            for i in range(3):
                lo[i] = min(lo[i], [o.x, o.y, o.z][i] - [e.x, e.y, e.z][i])
                hi[i] = max(hi[i], [o.x, o.y, o.z][i] + [e.x, e.y, e.z][i])
    volumes = []
    for v in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.NavMeshBoundsVolume):
        o, e = v.get_actor_bounds(False)
        volumes.append([round(2 * e.x / 100), round(2 * e.y / 100), round(2 * e.z / 100)])
    return lo, hi, volumes


def stands(world, q):
    """A spot a player can occupy: ground under it and room to stand up."""
    return not blocked(world, q + unreal.Vector(0, 0, 20), q + unreal.Vector(0, 0, 190))


def clear_radius(world, q):
    """Distance to the nearest cover in twelve directions, at chest height.

    Small means in cover, large means open ground. Probes outward in PROBE
    steps and stops at the first block, so cost follows how open the ground is.
    The search stops at CAP: ground with no cover within CAP reads as CAP, and
    capped_pct says how much of the map is that open, so a capped maximum is
    never mistaken for a measured one.
    """
    best = CAP
    chest = q + unreal.Vector(0, 0, CHEST)
    for k in range(12):
        ang = 2 * math.pi * k / 12
        d = PROBE
        while d < min(best, CAP):
            if blocked(world, chest, chest + unreal.Vector(math.cos(ang) * d, math.sin(ang) * d, 0)):
                break
            d += PROBE
        best = min(best, d)
        if best <= PROBE:
            break
    return best


def spread(points, want):
    """Farthest-point sample so the audit spreads over the whole map."""
    if len(points) <= want:
        return list(points)
    out = [max(points, key=lambda p: (p.x + p.y))]
    while len(out) < want:
        out.append(max(points, key=lambda p: min((p - c).length() for c in out)))
    return out


def cover_inventory(world):
    """Static meshes a player can use as cover, split hard from soft.

    Height comes from the actor bounds, so a wall scores hard and a kerb is
    ignored. A mesh only counts when a trace through its middle is blocked,
    which drops decorative and non-colliding props.

    get_actor_bounds returns (origin, box extent), so height is twice the z
    extent. Reading the origin as a corner instead silently classified every
    prop as a kerb and reported zero cover on a map with 290 dressing props.
    Only StaticMeshActors are counted, so cover that lives in a blueprint or in
    instanced foliage is not in this number.
    """
    hard = soft = 0
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
    say("cover: scanning {} static meshes".format(len(actors)))
    for a in actors[:6000]:
        o, e = a.get_actor_bounds(False)
        height = 2 * e.z
        if height < SOFT_COVER_H or 2 * e.x > 4000:
            continue  # kerb or sky-sized prop
        mid = unreal.Vector(o.x, o.y, o.z + min(height * 0.5, CHEST))
        if not blocked(world, mid, mid + unreal.Vector(70, 0, 0)):
            continue
        if height >= HARD_COVER_H:
            hard += 1
        else:
            soft += 1
    return hard, soft


def sample_ground(world, lo, hi, want_cells=3600):
    """Walkable points on a grid sized to the map, and the navmesh's share.

    The grid step grows on large maps: Red Gum is a kilometre across, and a
    fixed 10 m grid there is ten thousand ground traces and no extra detail.
    """
    extent = max(hi[0] - lo[0], hi[1] - lo[1])
    step = max(1000.0, extent / math.sqrt(want_cells))
    cells, on_nav, total, hits = [], 0, 0, 0
    x = lo[0]
    while x <= hi[0]:
        y = lo[1]
        while y <= hi[1]:
            total += 1
            z = ground_z(world, x, y)
            if z is not None and lo[2] < z < hi[2]:
                hits += 1
                p = unreal.Vector(x, y, z)
                q = nav(world, p, unreal.Vector(250, 250, 400))
                if q:
                    on_nav += 1
                else:
                    q = p       # walkable ground even where the navmesh stops
                if stands(world, q):
                    cells.append(q)
            y += step
        x += step
    return cells, on_nav, total, hits, step


def audit(name):
    world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/Maps/" + name)
    if not world:
        return {"error": "load failed"}
    unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")

    objs = sorted(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SSObjectiveActor),
                  key=lambda o: o.get_editor_property("sequence_index"))
    starts = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
    teams = {t: [s.get_actor_location() for s in starts if str(s.get_editor_property("player_start_tag")) == t]
             for t in ("TeamOne", "TeamTwo")}
    lo, hi, volumes = play_bounds(world)
    cells, on_nav, total, hits, step = sample_ground(world, lo, hi)
    if len(cells) < 12:
        return {"error": "no walkable ground found in {} x {} m".format(
            round((hi[0] - lo[0]) / 100), round((hi[1] - lo[1]) / 100))}

    width = (hi[0] - lo[0]) / 100.0
    depth = (hi[1] - lo[1]) / 100.0
    diagonal = math.hypot(width, depth)
    sampled = spread(cells, SAMPLE)
    out = {
        "size_m": [round(width), round(depth)],
        "diagonal_m": round(diagonal),
        "grid_step_m": round(step / 100.0),
        "grid_cells": total,
        "walkable_cells": len(cells),
        "walkable_pct": round(100.0 * len(cells) / total),
        "nav_cells": on_nav,
        "nav_coverage_pct": round(100.0 * on_nav / max(1, hits)),
        "nav_volumes_m": volumes,
        "sampled": len(sampled),
    }
    say("{}: {} x {} m, {} of {} cells walkable, {} of those on the navmesh".format(
        name, out["size_m"][0], out["size_m"][1], len(cells), total, on_nav))

    # Open crossing. The headline is the 90th percentile: if a tenth of the map
    # is a long dash in the open, the rule is broken for a lot of the round.
    radii = sorted(clear_radius(world, q) / 100.0 for q in sampled)
    out["open_crossing_m"] = {
        "p50": round(radii[len(radii) // 2], 1),
        "p90": round(radii[int(len(radii) * 0.9)], 1),
        "max": round(radii[-1], 1),
        "over_20m_pct": round(100.0 * sum(1 for r in radii if r > 20.0) / len(radii)),
        "capped_pct": round(100.0 * sum(1 for r in radii if r >= CAP / 100.0) / len(radii)),
    }
    say("{}: open crossing p50/p90/max {}/{}/{} m, {}% has no cover within 30 m".format(
        name, out["open_crossing_m"]["p50"], out["open_crossing_m"]["p90"],
        out["open_crossing_m"]["max"], out["open_crossing_m"]["capped_pct"]))

    # Close quarters, measured directly: the sample grid is 10 m or coarser so
    # two sampled points can never be near enough to test this.
    short = {"under_5m": 0, "5_to_20m": 0}
    for q in sampled:
        eye = q + unreal.Vector(0, 0, EYE)
        for k in range(8):
            ang = 2 * math.pi * k / 8
            for dist in SHORT:
                if not blocked(world, eye, eye + unreal.Vector(math.cos(ang) * dist, math.sin(ang) * dist, 0)):
                    short["under_5m" if dist < 500.0 else "5_to_20m"] += 1
    out["close_quarters"] = dict(short, probes=len(sampled) * 8 * len(SHORT))
    say("{}: {} clear probes under 5 m, {} between 5 and 20 m".format(
        name, short["under_5m"], short["5_to_20m"]))

    # Engagement: clear eye-height sightlines, sampled pairs rather than every
    # combination so a big map does not cost a quadratic in traces.
    rng = random.Random(11)
    pairs = {}
    # A map with 31 walkable points has only 465 distinct pairs, so asking for
    # 3000 of them loops forever. Stop at whichever comes first.
    wanted = min(PAIRS, len(sampled) * (len(sampled) - 1) // 2)
    while len(pairs) < wanted:
        a, b = rng.choice(sampled), rng.choice(sampled)
        if a is b:
            continue
        pairs[tuple(sorted(((round(a.x), round(a.y)), (round(b.x), round(b.y)))))] = (a, b)
    distances, long_range = [], 0
    for a, b in pairs.values():
        d = (a - b).length()
        if d < PROBE:
            continue
        if not blocked(world, a + unreal.Vector(0, 0, EYE), b + unreal.Vector(0, 0, EYE)):
            distances.append(d / 100.0)
            if d > MAX_SIGHTLINE:
                long_range += 1
    distances.sort()
    out["sightlines_m"] = {
        "pairs": len(pairs), "clear": len(distances),
        "p10": round(distances[len(distances) // 10], 1) if distances else None,
        "p50": round(distances[len(distances) // 2], 1) if distances else None,
        "p90": round(distances[int(len(distances) * 0.9)], 1) if distances else None,
        "max": round(distances[-1], 1) if distances else None,
        "max_pct_of_diagonal": round(100.0 * (distances[-1] if distances else 0) / diagonal),
        "over_220m": long_range,
    }
    say("{}: {}/{} sightlines clear, p50 {} m, max {} m ({}% of the diagonal)".format(
        name, len(distances), len(pairs), out["sightlines_m"]["p50"],
        out["sightlines_m"]["max"], out["sightlines_m"]["max_pct_of_diagonal"]))

    hard, soft = cover_inventory(world)
    out["cover"] = {"hard": hard, "soft": soft,
                    "hard_to_soft": round(hard / float(soft), 2) if soft else None,
                    "per_walkable_cell": round((hard + soft) / float(len(cells)), 2)}
    say("{}: cover {} hard / {} soft ({} per walkable cell)".format(
        name, hard, soft, out["cover"]["per_walkable_cell"]))

    # Objectives: cover to fight from, overwatch, and the ADR-018 walk parity.
    out["objectives"] = []
    for o in objs:
        at = o.get_actor_location()
        near = nav(world, at, unreal.Vector(400, 400, 2000)) or at
        close = overwatch = 0
        for q in sampled:
            d = (q - near).length()
            if d > 6000.0:
                continue
            if blocked(world, q + unreal.Vector(0, 0, EYE), near + unreal.Vector(0, 0, EYE)):
                continue
            if d <= 2000.0:
                close += 1
            elif d >= 4000.0:
                overwatch += 1
        # One representative start per team, the one nearest its own centroid:
        # a deployment is a cluster, so eight queries per team measure the same
        # walk eight times over.
        walks, partial = {}, False
        for t in ("TeamOne", "TeamTwo"):
            locs = teams[t]
            if not locs:
                walks[t] = (None, False)
                continue
            c = sum(locs, unreal.Vector()) / len(locs)
            home = min(locs, key=lambda l: (l - c).length())
            start = nav(world, home, unreal.Vector(250, 250, 400)) or home
            walks[t] = nav_chain(world, start, near)
            partial = partial or not walks[t][1]
        a, b = walks["TeamOne"][0], walks["TeamTwo"][0]
        balance = round(100.0 * abs(a - b) / max(a, b)) if a and b else None
        out["objectives"].append({
            "name": o.get_actor_label(),
            "cover_within_20m": close,
            "overwatch_beyond_40m": overwatch,
            "walk_team_one_m": round(a) if a is not None else None,
            "walk_team_two_m": round(b) if b is not None else None,
            "imbalance_pct": balance,
            "walk_note": "partial route, distance is a lower bound" if partial else "",
        })
        say("{}: {} cover20={} overwatch={} walk {}/{} m imbalance {}".format(
            name, o.get_actor_label(), close, overwatch,
            out["objectives"][-1]["walk_team_one_m"], out["objectives"][-1]["walk_team_two_m"], balance))

    # Deployments: layout_spawns.py writes these, so the audit only measures.
    # Exposure is the number of start pairs that can see each other on the
    # opening frame.
    eye = unreal.Vector(0, 0, EYE)
    exposure = sum(1 for x in teams["TeamOne"] for y in teams["TeamTwo"]
                   if not blocked(world, x + eye, y + eye))
    gap = 0.0
    for t in ("TeamOne", "TeamTwo"):
        locs = teams[t]
        for i, a in enumerate(locs):
            for b in locs[i + 1:]:
                gap = max(gap, (a - b).length())
    sep = None
    if teams["TeamOne"] and teams["TeamTwo"]:
        c1 = sum(teams["TeamOne"], unreal.Vector()) / len(teams["TeamOne"])
        c2 = sum(teams["TeamTwo"], unreal.Vector()) / len(teams["TeamTwo"])
        sep = round((c1 - c2).length() / 100.0)
    out["deployments"] = {
        "team_one": len(teams["TeamOne"]), "team_two": len(teams["TeamTwo"]),
        "separation_m": sep, "widest_start_gap_m": round(gap / 100.0),
        "exposed_pairs": "{}/{}".format(exposure, len(teams["TeamOne"]) * len(teams["TeamTwo"])),
    }
    return out


def rules_for(r):
    """The Dry River rules as measured numbers, pass, fail, or not applicable.

    A 220 m sightline means one thing on a 260 m blockout and something else
    entirely on a kilometre of paddock, so the absolute rules are only scored on
    a map near the size they were written for. Everything else is scored on
    every map, and the same numbers are reported either way.
    """
    out = []
    sight = r.get("sightlines_m", {})
    cover = r.get("cover", {})
    dep = r.get("deployments", {})
    oc = r.get("open_crossing_m", {})
    cq = r.get("close_quarters", {})
    blockout = r.get("diagonal_m", 0) <= BLOCKOUT_DIAGONAL / 100.0 * 1.5

    def add(rule, target, measured, ok):
        out.append({"rule": rule, "target": target, "measured": measured,
                    "pass": None if ok is None else bool(ok)})

    add("open crossing", "<= 20 m (p90)", "{} m".format(oc.get("p90")),
        oc.get("p90") is not None and oc["p90"] <= 20.0)
    add("close quarters", "clear probes under 5 m", cq.get("under_5m"),
        bool(cq.get("under_5m")))
    add("max sightline", "<= 220 m", "{} m".format(sight.get("max")),
        (sight.get("max") is not None and sight["max"] <= 220.0) if blockout else None)
    add("hard:soft cover", "1:3 (0.15-0.6)", cover.get("hard_to_soft"),
        cover.get("hard_to_soft") is not None and 0.15 <= cover["hard_to_soft"] <= 0.6)
    add("cover density", ">= 0.3 props per walkable cell", cover.get("per_walkable_cell"),
        cover.get("per_walkable_cell") is not None and cover["per_walkable_cell"] >= 0.3)
    add("starts", "8 + 8", "{}+{}".format(dep.get("team_one"), dep.get("team_two")),
        dep.get("team_one") == 8 and dep.get("team_two") == 8)
    add("spawn exposure", "0 of 64 start pairs see each other", dep.get("exposed_pairs"),
        dep.get("exposed_pairs") == "0/64")
    for ob in r.get("objectives", []):
        add("walk parity {}".format(ob["name"]), "<= 10% imbalance",
            "{}%".format(ob["imbalance_pct"]),
            None if ob["imbalance_pct"] is None else ob["imbalance_pct"] <= 10)
    return out


def write_md():
    lines = ["# Map playability audit (generated; source Build/map_playability.json)", "",
             "Generated by Tools/Unreal/audit_map_playability.py. Read only: it moves nothing.",
             "Rules come from Docs/MAPS_DRYRIVER.md and were written for the 260 x 180 m blockout;",
             "where a rule does not fit a map of a different size it is reported, not scored.", ""]
    for name, r in report["maps"].items():
        lines.append("## {}".format(name))
        if "error" in r:
            lines += ["- ERROR: {}".format(r["error"]), ""]
            continue
        oc, s, c, d = r["open_crossing_m"], r["sightlines_m"], r["cover"], r["deployments"]
        lines.append("- {} x {} m (diagonal {} m), nav volume(s) {}".format(
            r["size_m"][0], r["size_m"][1], r["diagonal_m"], r["nav_volumes_m"] or "none"))
        lines.append("- walkable {} of {} grid cells ({}%); {} of those project onto the navmesh ({}%)".format(
            r["walkable_cells"], r["grid_cells"], r["walkable_pct"], r["nav_cells"], r["nav_coverage_pct"]))
        lines.append("- open crossing p50 {} m / p90 {} m / max {} m; {}% of sampled ground is over 20 m open, {}% has no cover within 30 m".format(
            oc["p50"], oc["p90"], oc["max"], oc["over_20m_pct"], oc["capped_pct"]))
        lines.append("- close quarters: {} clear probes under 5 m, {} between 5 and 20 m, of {} probes".format(
            r["close_quarters"]["under_5m"], r["close_quarters"]["5_to_20m"], r["close_quarters"]["probes"]))
        lines.append("- sightlines: {}/{} sampled pairs clear, p10 {} m / p50 {} m / p90 {} m / max {} m ({}% of the diagonal), {} over 220 m".format(
            s.get("clear"), s.get("pairs"), s.get("p10"), s.get("p50"), s.get("p90"),
            s.get("max"), s.get("max_pct_of_diagonal"), s.get("over_220m")))
        lines.append("- cover: {} hard / {} soft (1:{}), {} props per walkable cell".format(
            c["hard"], c["soft"], c["hard_to_soft"], c["per_walkable_cell"]))
        lines.append("- deployments {}+{}, {} m apart, widest gap within a team {} m, exposure {}".format(
            d["team_one"], d["team_two"], d["separation_m"], d["widest_start_gap_m"], d["exposed_pairs"]))
        for ob in r["objectives"]:
            lines.append("- {}: cover within 20 m {}, overwatch beyond 40 m {}, walk {}/{} m, imbalance {}{}".format(
                ob["name"], ob["cover_within_20m"], ob["overwatch_beyond_40m"],
                ob["walk_team_one_m"], ob["walk_team_two_m"], ob["imbalance_pct"],
                " ({})".format(ob["walk_note"]) if ob["walk_note"] else ""))
        fails = [x for x in r["rules"] if x["pass"] is False]
        na = [x for x in r["rules"] if x["pass"] is None]
        lines.append("- rules: {} pass, {} fail, {} not scored".format(
            len(r["rules"]) - len(fails) - len(na), len(fails), len(na)))
        for x in fails:
            lines.append("  - FAIL {}: {} against {}".format(x["rule"], x["measured"], x["target"]))
        for x in na:
            lines.append("  - n/a  {}: {} against {}".format(x["rule"], x["measured"], x["target"]))
        lines.append("")
    with open(MD, "w") as fh:
        fh.write("\n".join(lines))


if os.path.exists(PROGRESS):
    os.remove(PROGRESS)
try:
    for m in MAPS:
        r = audit(m)
        if "error" not in r:
            r["rules"] = rules_for(r)
        report["maps"][m] = r
        flush()
        write_md()
except Exception:
    report["errors"].append(traceback.format_exc())
report["ok"] = bool(report["maps"]) and all("error" not in r for r in report["maps"].values())
flush()
write_md()
say("done ok={} errors={}".format(report["ok"], report["errors"]))
