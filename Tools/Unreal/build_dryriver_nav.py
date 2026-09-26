# Copyright Southern Spear. All Rights Reserved.
#
# Second pass of the Dry River level build: navigation.
#
#   UnrealEditor-Cmd.exe SouthernSpear.uproject -nullrhi -unattended -nosplash \
#       -nosound \
#       -ini:Engine:[/Script/NavigationSystem.NavigationSystemV1]:bWaitForAsyncLoadingBeforeBuildingNavigationAutomatically=False \
#       -ExecutePythonScript=Tools/Unreal/build_dryriver_nav.py
#
# WHY THIS IS A SEPARATE PASS — this is the whole reason the pipeline is split.
#
# UNavigationSystemV1::GatherNavigationBounds() (NavigationSystem.cpp) walks the
# world for ANavMeshBoundsVolume and silently skips any volume that fails
#     V->HasActorRegisteredAllComponents()
# with the comment that it will "wait [for] calls to OnNavigationBoundsAdded".
# That callback fires from ANavMeshBoundsVolume::PostRegisterAllComponents.
#
# An actor created by Python's spawn_actor_from_class does not reach that state
# in time, so the volume is skipped and the build reports
#     FRecastNavMeshGenerator::UpdateNavigationBounds TotalNavBounds: IsValid=false
# leaving a navmesh covering nothing. Reloading the saved map runs the normal
# registration path and fixes it. So: construct in one invocation, load and
# build in another. This is also exactly what an artist does by hand — save,
# reload, Build Paths — so the pipeline matches the interactive workflow.
#
# See build_dryriver_level.py for the construction pass and Docs/CHANGELOG.md
# for the evidence trail.

import json
import os
import traceback

import unreal

PROJECT_DIR = unreal.Paths.project_dir()
LEVEL_PATH = "/Game/Maps/L_DryRiver_01"
REPORT_PATH = os.path.join(PROJECT_DIR, "Build", "dryriver_nav_report.json")
LAYOUT_CSV = os.path.join(PROJECT_DIR, "Content", "Art", "Blockout", "SS_MAP_DryRiver_01_Layout.csv")

# Query just above the terrain: the nav query extent is small and a point
# floating a metre over the surface fails to project.
QUERY_Z_OFFSET_M = 0.1

report = {"ok": False, "steps": [], "warnings": [], "errors": []}


def log(msg):
    unreal.log("[DryRiverNav] {}".format(msg))


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    log("{} {} {}".format("OK  " if ok else "FAIL", name, detail))
    return bool(ok)


def warn(msg):
    report["warnings"].append(str(msg))
    log("WARN {}".format(msg))


def read_layout():
    import csv
    rows = []
    with open(LAYOUT_CSV, "r", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append({k: row[k] for k in row})
    return rows


def load_level():
    """The load is what makes the nav bounds volume register."""
    try:
        world = unreal.EditorLoadingAndSavingUtils.load_map(LEVEL_PATH)
    except Exception as exc:  # noqa: BLE001
        return step("load_map", False, str(exc))
    ok = step("load_map", bool(world), "{} -> {}".format(LEVEL_PATH, world.get_name() if world else None))
    if world:
        report["world_name"] = world.get_name()
    return ok


def count_registered_volumes():
    """Distinguish 'the volume is in the world' from 'the nav system sees it'."""
    world = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).get_current_level().get_world()
    try:
        vols = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.NavMeshBoundsVolume)
    except Exception as exc:  # noqa: BLE001
        warn("volume query failed: {}".format(exc))
        return -1
    report["nav_bounds_volume_count"] = len(vols)
    for v in vols:
        s = v.get_actor_scale3d()
        log("  volume {} at {} scale ({:.1f},{:.1f},{:.1f})".format(
            v.get_actor_label(), v.get_actor_location(), s.x, s.y, s.z))
        report["nav_volume_world_scale"] = [s.x, s.y, s.z]
    return len(vols)


def count_nav_data():
    """The build needs actual navigation data in the level. A bounds volume on
    its own is not enough, and a map without nav data will report a successful
    BUILDPATHS while producing nothing.

    Loading the map is what creates it: the volume registers on load via
    PostRegisterAllComponents -> OnNavigationBoundsAdded, and the navigation
    system creates the matching nav data. Spawning one from script instead was
    tried and removed, because that path defers registration to a tick and a
    one-shot script never ticks.
    """
    world = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).get_current_level().get_world()
    try:
        navs = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.RecastNavMesh)
    except Exception as exc:  # noqa: BLE001
        warn("nav data query failed: {}".format(exc))
        return -1
    report["recast_navmesh_count"] = len(navs)
    for n in navs:
        log("  navdata {} label={}".format(n.get_class().get_name(), n.get_actor_label()))
    if navs:
        return len(navs)

    # Fallback for a map saved without nav data. Registration is deferred here
    # too, so build twice and let the second call see the completed registration.
    log("  no RecastNavMesh after load; spawning one and building twice")
    try:
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        actors.spawn_actor_from_class(unreal.RecastNavMesh, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    except Exception as exc:  # noqa: BLE001
        warn("could not spawn RecastNavMesh: {}".format(exc))
    return 0


def describe_level():
    """Report what the loaded map actually contains.

    The build reports success in 0.00s with zero tiles whenever the terrain
    component is missing or not navigation-relevant, and gives no indication
    which. So check the facts rather than inferring them: the actor must have
    survived the save, the mesh must be assigned, and collision must be on.
    """
    world = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).get_current_level().get_world()
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
    report["static_mesh_actor_count"] = len(actors)
    log("  {} StaticMeshActor(s) in loaded level".format(len(actors)))

    for a in actors:
        entry = {"label": a.get_actor_label()}
        smc = None
        try:
            smc = a.static_mesh_component
        except Exception as exc:  # noqa: BLE001
            entry["component_error"] = str(exc)
        if smc is not None:
            # Each field is read independently: one unavailable symbol must not
            # cost us the whole report, which is the only diagnostic we have
            # for a build that silently produces no tiles.
            for key, fn in (
                ("mesh", lambda: smc.get_editor_property("static_mesh")),
                ("collision_profile", lambda: smc.get_collision_profile_name()),
                ("collision_enabled", lambda: smc.get_collision_enabled()),
                ("can_ever_affect_navigation",
                 lambda: smc.get_editor_property("can_ever_affect_navigation")),
                ("nav_collision_enabled", lambda: smc.get_editor_property(
                    "bUseComplexAsSimpleForNavigation")),
            ):
                try:
                    v = fn()
                    entry[key] = v.get_name() if hasattr(v, "get_name") else (
                        bool(v) if isinstance(v, bool) else v)
                except Exception as exc:  # noqa: BLE001
                    entry[key + "_error"] = str(exc)
        report.setdefault("mesh_actors", []).append(entry)
        log("  mesh actor: {}".format(entry))

    return bool(actors)


def build_paths():
    world = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).get_current_level().get_world()
    try:
        unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")
        return step("build_paths", True, "BUILDPATHS issued")
    except Exception as exc:  # noqa: BLE001
        return step("build_paths", False, str(exc))


def trace_ground(x_m, y_m):
    """Find the real terrain height at a map position by tracing straight down.

    The layout CSV carries the height Blender computed, but the navmesh sits on
    whatever collision actually exists, and guessing the query height is what
    produced "start point not on navmesh". Tracing also proves the terrain
    carries collision at that exact spot, which is the thing being tested.

    bTraceComplex must be True: the mesh uses complex-as-simple collision, which
    a simple trace would miss entirely.
    """
    world = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).get_current_level().get_world()
    start = unreal.Vector(x_m * 100.0, y_m * 100.0, 50000.0)
    end = unreal.Vector(x_m * 100.0, y_m * 100.0, -50000.0)
    try:
        result = unreal.SystemLibrary.line_trace_single(
            world, start, end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,   # Visibility
            True,                                       # trace complex
            [], unreal.DrawDebugTrace.NONE, True,
        )
    except Exception as exc:  # noqa: BLE001
        warn("line_trace_single failed: {}".format(exc))
        return None

    # LineTraceSingle has an FHitResult& out parameter, which Python surfaces as
    # a (bHit, HitResult) tuple. Accept a bare HitResult too rather than assume.
    if isinstance(result, (list, tuple)):
        if len(result) < 2 or not result[0]:
            return None
        hit = result[1]
    else:
        hit = result
    # HitResult field names differ across versions and some are deprecated, so
    # try the plausible ones in order of preference.
    # HitResult exposes no named attributes in Python — only to_dict() and
    # export_text(). Read the impact point from the dict form.
    try:
        fields = hit.to_dict()
    except Exception as exc:  # noqa: BLE001
        warn("HitResult.to_dict failed: {}".format(exc))
        return None

    report["hitrESULT_keys"] = sorted(fields.keys())
    for key in ("impact_point", "location"):
        val = fields.get(key)
        if val:
            report["ground_hit_key"] = key
            if hasattr(val, "x"):
                return (val.x, val.y, val.z)
            if isinstance(val, (list, tuple)) and len(val) >= 3:
                return (val[0], val[1], val[2])
    warn("no position field in HitResult; keys were {}".format(sorted(fields.keys())))
    return None


def path_exists(rows):
    """The check that actually matters. A navmesh actor existing proves nothing;
    a traversable path across the full 170 m between deployments proves the
    bounds are registered, the volume is correctly sized, the terrain carries
    collision, and the build succeeded."""
    deps = [r for r in rows if r["kind"] == "Deployment"]
    world = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).get_current_level().get_world()
    if len(deps) < 2:
        return step("path_verification", False, "need 2 deployments")

    def endpoint(d):
        # Blender is right-handed, Unreal is left-handed, so the FBX import
        # mirrors Y. The layout CSV is in Blender space, so Y must be negated.
        # Getting this wrong is silent: the map is symmetric in Y, so the
        # deployments simply swap ends and the terrain still looks plausible.
        ux = float(d["x"])
        uy = -float(d["y"])
        hit = trace_ground(ux, uy)
        csv_z_cm = float(d["z"]) * 100.0
        if hit is None:
            log("  no ground hit at ({:.0f},{:.0f}) for {}; falling back to CSV z".format(ux, uy, d["name"]))
            return unreal.Vector(ux * 100.0, uy * 100.0, csv_z_cm)

        # Self-check: the traced ground height must agree with the height the
        # Blender generator recorded. Disagreement means the coordinate
        # transform is wrong, and this is what catches it.
        delta = abs(hit[2] - csv_z_cm)
        log("  {} ground z={:.1f}cm vs CSV {:.1f}cm (delta {:.1f}cm)".format(
            d["name"], hit[2], csv_z_cm, delta))
        report.setdefault("ground_check", []).append(
            {"name": d["name"], "traced_z_cm": hit[2], "csv_z_cm": csv_z_cm, "delta_cm": delta})
        if delta > 150.0:
            warn("{}: traced ground differs from the layout CSV by {:.0f}cm — "
                 "the CSV-to-Unreal coordinate transform is wrong".format(d["name"], delta))
        return unreal.Vector(ux * 100.0, uy * 100.0, hit[2] + 2.0)

    start = endpoint(deps[0])
    end = endpoint(deps[1])

    try:
        path = unreal.NavigationSystemV1.find_path_to_location_synchronously(
            world, start, end, None, None
        )
    except Exception as exc:  # noqa: BLE001
        return step("path_verification", False, str(exc))

    if not path:
        return step("path_verification", False, "no path object returned")

    # UNavigationPath exposes only PathPoints to script — bIsValid is a private,
    # non-UPROPERTY bitfield. A non-empty point list is the real evidence.
    points = [[p.x, p.y, p.z] for p in (path.get_editor_property("path_points") or [])]
    report["path_points"] = len(points)
    report["path_start"] = [start.x, start.y, start.z]
    report["path_end"] = [end.x, end.y, end.z]
    if points:
        report["path_first"] = points[0]
        report["path_last"] = points[-1]
    return step("path_verification", bool(points), "{} path point(s)".format(len(points)))


def save():
    sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    for name in ("save_current_level", "save_all_dirty_levels"):
        fn = getattr(sub, name, None)
        if fn is None:
            continue
        try:
            if fn():
                return step("save", True, name)
        except Exception as exc:  # noqa: BLE001
            warn("{}: {}".format(name, exc))
    return step("save", False, "no working save API")


def finish():
    try:
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        unreal.log("[DryRiverNav] REPORT_WRITTEN {}".format(REPORT_PATH))
    except Exception:  # noqa: BLE001
        unreal.log("[DryRiverNav] report write failed:\n" + traceback.format_exc())
    unreal.log("[DryRiverNav] COMPLETE ok={}".format(report.get("ok")))


def main():
    try:
        if not load_level():
            return finish()
        n = count_registered_volumes()
        step("nav_bounds_volume_present", n > 0, "{} volume(s) in world".format(n))
        d = count_nav_data()
        step("nav_data_present", d > 0, "{} RecastNavMesh actor(s)".format(d))
        describe_level()

        # Build twice when we had to spawn nav data: the first call may land
        # before deferred registration has completed.
        build_paths()
        if d <= 0:
            build_paths()
        path_ok = path_exists(read_layout())
        saved = save()

        report["ok"] = bool(path_ok and saved)
        report["result_summary"] = "path verified={} saved={}".format(path_ok, saved)
        return finish()
    except Exception:  # noqa: BLE001
        report["errors"].append(traceback.format_exc())
        unreal.log("[DryRiverNav] raised:\n" + traceback.format_exc())
        return finish()


main()
