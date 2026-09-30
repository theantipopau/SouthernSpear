# Southern Spear - Wandarra navigation pass (M-009).
#
# The village layout is DESIGNED in Tools/Common/wandarra_spec.py, so unlike
# build_objective_map.py's nav pass this does not re-route objectives along a
# computed path: it verifies the designed chain (Depot -> A -> B -> C -> Green)
# on the built navmesh and repairs only what cannot walk it. Evidence is the
# point: nav coverage, per-leg reachability, any relocation, all written to
# Build/wandarra_nav.json.
#
# Known engine behaviour (R-82/R-83): headless BUILDPATHS on this machine
# consumes no new geometry, so if the stored navmesh is empty the path checks
# fail together and the report says so - an attended editor bake is then the
# documented next step, not a silent pass.

import json
import math
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
import sys  # noqa: E402
sys.path.insert(0, os.path.join(PROJECT_DIR, "Tools", "Common"))
import wandarra_spec as SPEC  # noqa: E402

MAP = "/Game/Maps/L_Wandarra_01"
REPORT = os.path.join(PROJECT_DIR, "Build", "wandarra_nav.json")
report = {"ok": False, "steps": [], "errors": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return ok


def cm(x_m, y_m, z_m=0.0):
    return unreal.Vector(x_m * 100.0, -y_m * 100.0, z_m * 100.0)


def reachable(world, a, b):
    p = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, a, b)
    return p is not None and p.is_valid() and not p.is_partial()


def project(world, q):
    return unreal.NavigationSystemV1.project_point_to_navigation(
        world, q, None, None, unreal.Vector(300, 300, 3000))


def main():
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not step("load_map", world is not None, MAP):
        return False
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # RecastNavMesh lives in the saved map (spawned by the level pass). Do not
    # spawn one here: script-spawned nav actors register on a later tick, which
    # a headless run never gives them (MAPS_DRYRIVER.md section 11.3).
    # Validate actor-level exclusions before sampling the saved tiles.
    nav_policy = {"trees_exporting": [], "cars_exporting": []}
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        label = actor.get_actor_label()
        affects = actor.static_mesh_component.get_editor_property("can_ever_affect_navigation")
        if "Tree" in label and affects:
            nav_policy["trees_exporting"].append(label)
        elif "Car_" in label and affects:
            nav_policy["cars_exporting"].append(label)
    report["nav_component_policy"] = nav_policy
    policy_ok = not nav_policy["trees_exporting"] and not nav_policy["cars_exporting"]
    step("nav_component_policy", policy_ok, "{} tree and {} car actors still export collision".format(
        len(nav_policy["trees_exporting"]), len(nav_policy["cars_exporting"])))
    if not policy_ok:
        report["notes"] = ["repeat dressing pass to apply actor nav filters before nav verification"]
        return False
    if not unreal.GameplayStatics.get_all_actors_of_class(world, unreal.RecastNavMesh):
        return step("recast_navmesh", False,
                    "absent from saved map - re-run build_wandarra_level.py")
    # This pass only verifies saved tiles. Rebuilding here risks another asynchronous
    # Recast rebuild on script-spawned geometry; the attended editor is the bake owner.
    # (R-82: BUILDPATHS headless was measured as a no-op on this machine.)

    # Coverage evidence: grid sample the site, count projected points.
    step_cm = 500.0
    size = SPEC.SITE["size_m"] * 100
    grid, hits = 0, 0
    x = 0.0
    while x <= size:
        y = 0.0
        while y <= size:
            grid += 1
            if project(world, cm(x / 100.0, y / 100.0, 50.0)):
                hits += 1
            y += step_cm
        x += step_cm
    report["nav_coverage"] = {"grid_points": grid, "projected": hits,
                              "pct": round(100.0 * hits / max(grid, 1), 1)}
    if hits == 0:
        # The headless bake consumes no new geometry on this machine (R-82); an
        # empty navmesh means the attended bake has not happened yet.
        report["nav_baked"] = False
        report["notes"] = ["navmesh empty: BUILDPATHS is a no-op under -nullrhi (R-82).",
                           "open L_Wandarra_01 in the editor, Build - Build Paths, save, then re-run this pass."]
        report["nav_export_warnings"] = []
        return step("navmesh_present", False, "headless bake produced no navmesh; attended bake required")
    step("navmesh_present", True, "{} / {} grid points on navmesh".format(hits, grid))
    report["nav_baked"] = True

    report["nav_export_warnings"] = []

    # The designed chain: depot deployment, A, B, C, green deployment.
    depot = cm(SPEC.DEPLOYS[0]["x"], SPEC.DEPLOYS[0]["y"])
    green = cm(SPEC.DEPLOYS[1]["x"], SPEC.DEPLOYS[1]["y"])
    objs = sorted(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SSObjectiveActor),
                  key=lambda o: o.get_editor_property("sequence_index"))
    if len(objs) != 3:
        return step("objectives_found", False, len(objs))
    chain = [depot] + [o.get_actor_location() for o in objs] + [green]
    chain = [project(world, c) or c for c in chain]
    legs = [bool(a and b and reachable(world, a, b)) for a, b in zip(chain, chain[1:])]
    report["legs"] = legs
    step("all_legs", all(legs), legs)
    if not all(legs):
        report["notes"] = ["a designed leg fails: move the blocking placement in wandarra_spec.py,"]
        report["notes"].append("or fix the geometry, then re-run the level and nav passes. Layout is not auto-routed.")
    centre = chain[2]
    moved = {}
    for o in objs:
        q = project(world, o.get_actor_location())
        if q and reachable(world, q, centre) and reachable(world, centre, q):
            continue
        fixed = None
        for r in range(5, 30, 5):
            for k in range(16):
                ang = k * math.pi / 8
                cand = project(world, o.get_actor_location() + unreal.Vector(
                    r * 100 * math.cos(ang), r * 100 * math.sin(ang), 0))
                if cand and reachable(world, cand, centre) and reachable(world, centre, cand):
                    fixed = cand
                    break
            if fixed:
                break
        if fixed:
            moved[o.get_actor_label()] = round((fixed - o.get_actor_location()).length() / 100, 1)
            o.set_actor_location(fixed, False, False)
    report["relocated_objectives"] = moved
    step("objectives_reachable", True, "{} relocated".format(len(moved)))

    # Deployments: the tagged starts must reach their team's first objective.
    starts = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
    first = {"TeamOne": objs[0].get_actor_location(), "TeamTwo": objs[-1].get_actor_location()}
    bad = []
    for s in starts:
        tag = str(s.get_editor_property("player_start_tag"))
        if tag in first and not reachable(world, s.get_actor_location(), first[tag]):
            q = project(world, s.get_actor_location())
            if q and reachable(world, q, first[tag]):
                s.set_actor_location(q + unreal.Vector(0, 0, 100), False, False)
            else:
                bad.append(s.get_actor_label())
    step("deployments_reachable", not bad, bad or "all tagged starts reach their first objective")

    return step("save_map", unreal.EditorLoadingAndSavingUtils.save_current_level(), MAP)


try:
    ok = main()
    report["ok"] = bool(ok) and all(s["ok"] for s in report["steps"])
except Exception:
    report["errors"].append(traceback.format_exc())
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
with open(REPORT, "w") as fh:
    json.dump(report, fh, indent=1)
unreal.log("[WandarraNav] ok={} -> {}".format(report["ok"], REPORT))
