"""Bake the Ravenshoe navmesh headlessly, clearing stale data first.

Every previous attempt crashed in UnrealEd immediately after the build
completed, with:

    Recreating dtNavMesh instance (RecastNavMesh-Default) due mismatch in
    number of bytes required to store serialized maxTiles
    (serialized: 5643, 13 bits) vs calculated required (2448, 12 bits)

The build itself is fine - "UNavigationSystemV1::Build total execution
time: 0.30s" prints every time. The crash is the save. The saved navmesh
data in the .umap was serialised against a different tile budget than the
live dtNavMesh instance, and reconciling the two faults on save. Note the
"calculated required" figure is 2448 whatever the bounds volume is sized,
so it is a fixed config value, not something the volume can be tuned under.

So: drop the stale data first, then build. ClearNavigation empties the tiles
without touching the actor, and the fresh build then has nothing to mismatch
against.

Run with:
    SS_RAVENSHOE_NAV_BUILD=1
    -ini:Engine:[/Script/NavigationSystem.NavigationSystemV1]:bWaitForAsyncLoadingBeforeBuildingNavigationAutomatically=False
"""
import json
import os
import traceback

import unreal

MAP = "/Game/Maps/L_Ravenshoe_01"
OUT = os.path.join(
    unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()),
    "Build", "ravenshoe_nav_bake.json")

report = {"map": MAP, "steps": [], "errors": []}


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)[:160]})
    return ok


def routes(world, nav_world):
    """Reachable both ways, and with what, so a failure says which end."""
    objs = {a.get_actor_label(): a.get_actor_location()
            for a in unreal.GameplayStatics.get_all_actors_of_class(
                world, unreal.SSObjectiveActor)}
    starts = {a.get_actor_label(): a.get_actor_location()
              for a in unreal.GameplayStatics.get_all_actors_of_class(
                  world, unreal.PlayerStart)}
    out = []
    for on, ol in objs.items():
        for sn, sl in starts.items():
            a = unreal.NavigationSystemV1.find_path_to_location_synchronously(
                world, ol, sl)
            b = unreal.NavigationSystemV1.find_path_to_location_synchronously(
                world, sl, ol)
            out.append({
                "objective": on, "start": sn,
                "fwd": a is not None, "back": b is not None,
                "fwd_path": None if a is None else _pathlen(a),
            })
    return objs, starts, out


def _pathlen(p):
    try:
        return len(p.get_editor_property("path_points"))
    except Exception:                                       # noqa: BLE001
        return -1


try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    step("load_map", True, MAP)

    # 1. drop the stale serialised nav data. This is the whole point of the
    #    script: without it the save reconciles two tile budgets and faults.
    for cmd in ("ClearNavigation", "ResetNav"):
        try:
            unreal.SystemLibrary.execute_console_command(world, cmd)
            step("console_" + cmd, True, "issued")
        except Exception as exc:                            # noqa: BLE001
            step("console_" + cmd, False, type(exc).__name__)

    # 2. build.
    for i in range(2):
        try:
            unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")
            step("buildpaths_%d" % i, True, "issued")
        except Exception as exc:                            # noqa: BLE001
            step("buildpaths_%d" % i, False, type(exc).__name__)

    # 3. does anything reach the mesh now?
    probe = unreal.NavigationSystemV1.project_point_to_navigation(
        world, unreal.Vector(0, 0, 1400), None, None,
        unreal.Vector(500, 500, 5000))
    report["probe_obj_a"] = str(probe)
    step("navmesh_exists", probe is not None and str(probe) != "None", str(probe))

    objs, starts, rs = routes(world, world)
    report["objectives"] = {k: [round(v.x), round(v.y), round(v.z)] for k, v in objs.items()}
    report["starts"] = {k: [round(v.x), round(v.y), round(v.z)] for k, v in starts.items()}
    report["routes"] = rs
    good = sum(1 for r in rs if r["fwd"] and r["back"])
    report["routes_ok"] = good
    report["routes_total"] = len(rs)
    step("routes", good == len(rs) and bool(rs),
         "%d / %d both-ways" % (good, len(rs)))

    saved = unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)
    step("save_map", saved, MAP)
    report["ok"] = not report["errors"] and saved
except Exception:                                           # noqa: BLE001
    report["exception"] = traceback.format_exc()
    report["ok"] = False

with open(OUT, "w") as fh:
    json.dump(report, fh, indent=2, default=str)
print("BAKE_WRITTEN", OUT, "ok=", report.get("ok"),
      "routes=", report.get("routes_ok"), "/", report.get("routes_total"))
