# Southern Spear - Wandarra awnings + doors pass (Session 084, ADR-041).
#
# Places the vendor GovernmentAwning Blueprints and interactable door
# Blueprints from Tools/Common/wandarra_spec.py on the saved L_Wandarra_01.
# Doors are SCENERY (ADR-041: not wired into gameplay this phase).
#
# This pass also performs the R-90 measurement the map has waited for: it dumps
# every vendor building's actor bounds in site coordinates and reports overlap
# with the road corridors and the awning intents, so footprint corrections land
# in the spec (rebuild) rather than in actor nudges.
#
# Idempotent: actors labelled SS_Dress_* are removed and re-placed each run;
# the bounds dump is read-only. Placement needs loaded collision only (ground
# traces), not the navmesh, so it is safe headless. One writer: do not run
# while the interactive editor has the map open. Writes
# Build/wandarra_dressing.json.

import json
import math
import os
import sys
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
sys.path.insert(0, os.path.join(PROJECT_DIR, "Tools", "Common"))
import wandarra_spec as SPEC  # noqa: E402
sys.path.insert(0, os.path.join(PROJECT_DIR, "Tools", "Unreal"))
from ss_assets import asset_exists  # noqa: E402

MAP = "/Game/Maps/L_Wandarra_01"
PREFIX = "SS_Dress_"
REPORT = os.path.join(PROJECT_DIR, "Build", "wandarra_dressing.json")
CLEAR_CM = 40.0  # awning kept this far clear of its building's measured box

report = {"ok": False, "steps": [], "errors": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def cm(x_m, y_m, z_m=0.0):
    """Site metres to Unreal centimetres, Y mirrored (wandarra_spec frame)."""
    return unreal.Vector(x_m * 100.0, -y_m * 100.0, z_m * 100.0)


def yaw_unreal(yaw_deg):
    """Site degrees clockwise from north -> Unreal yaw. Must match
    build_wandarra_level.py's corrected transform (yaw - 90; Session 084)."""
    return yaw_deg - 90.0


def ground_z(world, x_m, y_m):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x_m * 100, y_m * 100, 50000), unreal.Vector(x_m * 100, y_m * 100, -50000),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    return None if hit is None else hit.to_dict()["impact_point"].z


def vendor_buildings(world):
    """The 11 building-Blueprint actors, with their boxes in site coordinates."""
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        label = a.get_actor_label()
        if not (label.startswith("SS_MAP_W_Bungalow") or label.startswith("SS_MAP_W_House")
                or label.startswith("SS_MAP_W_Government")):
            continue
        o, e = a.get_actor_bounds(False)
        out.append({
            "label": label,
            "site_center_m": [round(-o.y / 100, 2), round(o.x / 100, 2)],  # (x, y) site
            "half_extents_m": [round(e.y / 100, 2), round(e.x / 100, 2)],  # (ex, ey) site
            "center": unreal.Vector(o.x, o.y, o.z),
            "half": unreal.Vector(e.x, e.y, e.z),
        })
    return out


def overlaps_road(site_x, site_y, ex, ey):
    """Building box vs the two road corridors (site-frame rects), in metres."""
    hits = []
    half = (SPEC.ROAD_W / 2 + SPEC.WALK_W)
    mx, cy = SPEC.MAIN_STREET_X, SPEC.CROSS_STREET_Y
    corridors = [(mx - half, 0.0, mx + half, SPEC.SITE["size_m"]),
                 (50.0, cy - half, SPEC.SITE["size_m"], cy + half)]
    for (x0, y0, x1, y1) in corridors:
        if site_x + ex > x0 and site_x - ex < x1 and site_y + ey > y0 and site_y - ey < y1:
            hits.append([round(v, 1) for v in (x0, y0, x1, y1)])
    return hits


def main():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not step("load_map", world is not None, MAP):
        return False
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # ---- R-90: measure first, place second ----
    buildings = vendor_buildings(world)
    report["building_count"] = len(buildings)
    report["buildings"] = [{k: v for k, v in b.items() if k in ("label", "site_center_m", "half_extents_m")}
                           for b in buildings]
    step("bounds_dump", len(buildings) == len(SPEC.BUILDINGS),
         "{} vendor boxes measured (R-90)".format(len(buildings)))

    road_overlaps = []
    for b in buildings:
        cx, cy = b["site_center_m"]
        ex, ey = b["half_extents_m"]
        for rect in overlaps_road(cx, cy, ex, ey):
            road_overlaps.append({"building": b["label"], "corridor": rect})
    report["road_overlaps"] = road_overlaps
    step("road_overlaps", True, "{} building(s) bite a road corridor".format(len(road_overlaps)))

    # ---- idempotent clear ----
    removed = 0
    for a in actors.get_all_level_actors():
        if a.get_actor_label().startswith(PREFIX):
            actors.destroy_actor(a)
            removed += 1
    report["removed_existing"] = removed

    # ---- awnings ----
    placed, missing = 0, []
    pushes = {}
    for n, (key, x, y, yaw, why) in enumerate(SPEC.AWNING_ROWS):
        path = SPEC.AWNING_BPS[key]
        cls = unreal.load_class(None, path + "." + path.split("/")[-1] + "_C")
        if cls is None:
            missing.append(path)
            continue
        pos = cm(x, y, 0.0)
        site = unreal.Vector(x * 100, -y * 100, 0)
        a = actors.spawn_actor_from_class(cls, pos, unreal.Rotator(roll=0, pitch=0, yaw=yaw_unreal(yaw)))
        if not a:
            missing.append(path + " (spawn)")
            continue
        a.set_actor_label("{}Awning_{:02d}".format(PREFIX, n))
        # Push out of the nearest measured building box along the away-vector.
        near = min(buildings, key=lambda b: (b["center"] - site).size2d()) if buildings else None
        if near is not None:
            away = site - near["center"]
            away.z = 0
            d = max(away.length(), 1.0)
            dirv = away / d
            need = ((near["half"].x * abs(dirv.x) + near["half"].y * abs(dirv.y))
                    + (a.get_actor_bounds(False)[1].x * abs(dirv.x) + a.get_actor_bounds(False)[1].y * abs(dirv.y))
                    + CLEAR_CM)
            if need > d:
                site = site + dirv * (need - d)
                a.set_actor_location(site, False, False)
                pushes[a.get_actor_label()] = round((need - d) / 100, 2)
        placed += 1
    report["awnings"] = {"placed": placed, "pushed_cm": pushes, "missing": missing}
    step("awnings", placed == len(SPEC.AWNING_ROWS) and not missing,
         "{}/{} placed, {} pushed clear".format(placed, len(SPEC.AWNING_ROWS), len(pushes)))

    # ---- doors (scenery, ADR-041) ----
    dplaced = 0
    for n, (key, x, y, yaw, why) in enumerate(SPEC.DOOR_ROWS):
        cls = unreal.load_class(None, SPEC.DOOR_BPS[key] + "." + SPEC.DOOR_BPS[key].split("/")[-1] + "_C")
        if cls is None:
            missing.append(SPEC.DOOR_BPS[key])
            continue
        z = ground_z(world, x, y)
        if z is None:
            z = 0.0
        a = actors.spawn_actor_from_class(cls, cm(x, y, z), unreal.Rotator(roll=0, pitch=0, yaw=yaw_unreal(yaw)))
        if a:
            a.set_actor_label("{}Door_{:02d}".format(PREFIX, n))
            dplaced += 1
    report["doors"] = {"placed": dplaced, "of": len(SPEC.DOOR_ROWS)}
    step("doors", dplaced == len(SPEC.DOOR_ROWS) and not missing,
         "{}/{} scenery doors at the compound and green gates".format(dplaced, len(SPEC.DOOR_ROWS)))
    report["missing_assets"] = missing

    return step("save_map", unreal.EditorLoadingAndSavingUtils.save_current_level(), MAP)


try:
    ok = main()
    report["ok"] = bool(ok) and all(s["ok"] for s in report["steps"]) and not report.get("missing_assets")
except Exception:
    report["errors"].append(traceback.format_exc())
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[WandarraDressing] ok={} -> {}".format(report["ok"], REPORT))
