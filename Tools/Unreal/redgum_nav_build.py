"""Verify Red Gum navigation in a live editor world after Build > Build Paths.

The nav data is static, and commandlet execution with -nullrhi only loads the
stored navmesh; BUILDPATHS is a no-op there (confirmed by the map's zero nav
projection and the missing Recast tile data). Build the mesh in the UE editor
with /Game/Maps/L_RedGum_01 open, then run this Python script in that editor.
The script is read-only apart from saving the editor-built nav data if dirty.
"""
import json
import os
import traceback
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MAP = "/Game/Maps/L_RedGum_01"
OUT = os.path.join(PROJECT_DIR, "Build", "redgum_nav_build_report.json")

report = {"ok": False, "map": MAP, "errors": [], "queries": [], "routes": []}


def main():
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.load_level(MAP):
        report["errors"].append("could not load " + MAP)
        return
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        report["errors"].append("editor world unavailable")
        return

    nav = unreal.NavigationSystemV1.get_navigation_system(world)
    report["nav_system"] = str(nav)
    report["building_or_locked"] = unreal.NavigationSystemV1.is_navigation_being_built_or_locked(world)

    objectives = sorted(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SSObjectiveActor),
                        key=lambda o: o.get_editor_property("sequence_index"))
    starts = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PlayerStart)
    expected = [("DeployA", next((s.get_actor_location() for s in starts
                                  if s.get_actor_label() == "SS_MAP_RedGum_DeployA"), None)),
                ("ObjA", objectives[0].get_actor_location() if len(objectives) > 0 else None),
                ("ObjB", objectives[1].get_actor_location() if len(objectives) > 1 else None),
                ("ObjC", objectives[2].get_actor_location() if len(objectives) > 2 else None),
                ("DeployB", next((s.get_actor_location() for s in starts
                                  if s.get_actor_label() == "SS_MAP_RedGum_DeployB"), None)),
                ("WestFlank", unreal.Vector(-30000, 25000, 500)),
                ("EastFlank", unreal.Vector(30000, -25000, 500)),
                ("NorthFlank", unreal.Vector(0, -27000, 500)),
                ("SouthFlank", unreal.Vector(0, 27000, 500))]
    projected = {}
    for label, point in expected:
        result = unreal.NavigationSystemV1.project_point_to_navigation(
            world, point, None, None, unreal.Vector(500, 500, 3000)) if point else None
        projected[label] = result
        report["queries"].append({"label": label, "input_cm": list(point) if point else None,
                                  "projected_cm": list(result) if result else None})

    for (a_name, _), (b_name, _) in zip(expected, expected[1:]):
        p0, p1 = projected.get(a_name), projected.get(b_name)
        if not p0 or not p1:
            report["routes"].append({"from": a_name, "to": b_name, "ok": False,
                                     "reason": "endpoint did not project onto navigation"})
            continue
        path = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, p0, p1)
        ok = path is not None and path.is_valid() and not path.is_partial()
        report["routes"].append({"from": a_name, "to": b_name, "ok": ok,
                                 "path_points": len(path.path_points) if path else 0,
                                 "length_m": round(path.get_path_length()/100, 1) if ok else None})

    # This is only a save of the data already baked by Build > Build Paths.
    saved = bool(level_editor.save_current_level())
    report["saved"] = saved
    report["ok"] = bool(all(q["projected_cm"] is not None for q in report["queries"])
                        and all(r["ok"] for r in report["routes"]) and saved)


try:
    main()
except Exception:
    report["errors"].append(traceback.format_exc())
finally:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, default=str)
    unreal.log("[RedGumNavBuild] ok={} report={}".format(report.get("ok"), OUT))
