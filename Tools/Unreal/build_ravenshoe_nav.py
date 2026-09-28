# Southern Spear - Ravenshoe Crossing navigation pass.
#
# Run order:
#     import_ravenshoe -> dress_ravenshoe_props -> setup_ravenshoe_surfaces
#     -> dress_ravenshoe_groundcover -> light_ravenshoe
#     -> wire_ravenshoe_experience -> build_ravenshoe_nav
#
# TWO MODES, AND ONLY ONE OF THEM CAN RUN WITHOUT A HUMAN
#
#   verify  (default) - READ ONLY. Runs headlessly under -nullrhi. Reports
#           whether nav data exists, whether every objective is reachable from
#           every deployment, and whether the deck and the creek bed are
#           standable. This is the mode that can be run from a terminal, and it
#           is how you find out whether the build mode has been run yet.
#
#   build             - runs BUILDPATHS and saves. REQUIRES AN INTERACTIVE
#           EDITOR. See below for why, which is not a guess.
#
# WHY BUILDPATHS CANNOT RUN HEADLESS HERE
#
#   BUILDPATHS is a NO-OP without a real rendering device. It does not crash
#   and it does not warn; it silently does nothing and leaves a navmesh covering
#   nothing. Tools/Unreal/redgum_nav_build.py states this for Red Gum outright,
#   after confirming it against zero nav projection and missing Recast tile data.
#
#   Both headless workarounds were tried on this machine and both fail:
#     -nullrhi            -> no RHI at all, so the build is skipped.
#     -RenderOffscreen    -> still logs rhiname="Null", i.e. it falls back to
#                            the Null RHI, so the build is skipped there too;
#                            it then crashes on the way out.
#   A real RHI needs a display or a working offscreen D3D device, neither of
#   which a commandlet gets here. So the build is done the way an artist does
#   it: open the editor with the map loaded, and run this from the Python
#   console with build mode on.
#
# WHY A SEPARATE PASS AT ALL
#
#   UNavigationSystemV1::GatherNavigationBounds() walks the world for
#   ANavMeshBoundsVolume and silently skips any volume failing
#   V->HasActorRegisteredAllComponents(), waiting for the OnNavigationBoundsAdded
#   callback that fires from PostRegisterAllComponents. An actor created by
#   spawn_actor_from_class does not reach that state in time, so the volume is
#   skipped and the build reports TotalNavBounds: IsValid=false - a navmesh over
#   nothing. Reloading the SAVED map runs the normal registration path. So the
#   volume must be constructed in one invocation and built in another. This is
#   the same reason build_dryriver_nav.py exists.
#
# Writes Build/ravenshoe_nav_report.json.

import json
import os
import traceback

import unreal

PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MAP = "/Game/Maps/L_Ravenshoe_01"
REPORT = os.path.join(PROJECT, "Build", "ravenshoe_nav_report.json")

# The bounds volume is OWNED by expand_ravenshoe.py, which sizes it to the play space with a
# read-back correction and asserts coverage (including the ramp feet at x = +/-98 m, the thing a
# smaller volume silently drops). A build run only ASSERTS the coverage here - re-imposing bounds
# from this script is exactly how the correct play-space bounds were reverted to the old
# quarter-map positive quadrant after the play-test fix (Session: nav report 0/32 routes while
# the deck and bed both project onto nav).
COVER_CM = [("ObjA/ObjB on centreline", 0.0, 0.0, 100.0),
            ("DeployAlpha y=+13000", 0.0, 13000.0, 100.0),
            ("DeployBravo y=-13000", 0.0, -13000.0, 100.0),
            ("ramp feet x=+/-9800", 9800.0, 0.0, 200.0),
            ("ramp feet x=-9800", -9800.0, 0.0, 200.0),
            ("creek bed z=-1800", 0.0, 0.0, -1800.0),
            ("ridge crest z=+3400", 0.0, 0.0, 3400.0)]

report = {"ok": False, "mode": "verify", "steps": [], "errors": [], "routes": []}

# Build mode is opt-in. Set SS_RAVENSHOE_NAV_BUILD=1 in the environment, or
# change this to True to build from an interactive editor session. Defaulting
# to off is deliberate: a read-only run from a terminal should never be able to
# silently attempt a build that cannot succeed and then save the map.
BUILD = os.environ.get("SS_RAVENSHOE_NAV_BUILD", "") == "1"
report["mode"] = "build" if BUILD else "verify"


def step(name, ok, detail=""):
    report["steps"].append({"step": name, "ok": bool(ok), "detail": str(detail)})
    return bool(ok)


def reachable(world, a, b):
    p = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, a, b)
    return p is not None and p.is_valid() and not p.is_partial()


def main():
    # 1. load the SAVED map so the bounds volume registers properly
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    if not step("load_map", world is not None, MAP):
        report["errors"].append("could not open " + MAP)
        return
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)    # 2. a RecastNavMesh must exist, with a tile pool big enough for the play space. The pool is a
    #    property of the actor; expand_ravenshoe.py raises it to 4096 (the play space needs ~1285 at
    #    TileSizeUU 1000, over the default 1024 - which is what access-violated the save).
    recast = [a for a in unreal.GameplayStatics.get_all_actors_of_class(
        world, unreal.RecastNavMesh)]
    if not recast and BUILD:
        spawned = sub.spawn_actor_from_class(
            unreal.RecastNavMesh, unreal.Vector(0, 0, 0),
            unreal.Rotator(roll=0, pitch=0, yaw=0))
        if spawned is not None:
            spawned.set_actor_label("SS_Raven_RecastNavMesh")
        recast = [spawned] if spawned else []
    pool_ok = True
    if recast:
        pool = recast[0].get_editor_property("TilePoolSize")
        report["recast_tile_pool"] = pool
        pool_ok = pool >= 2048
        if not pool_ok:
            report["errors"].append(
                "RecastNavMesh TilePoolSize {} is below the play-space tile count; "
                "re-run expand_ravenshoe.py, which raises it to 4096".format(pool))
    step("recast_navmesh", bool(recast) and pool_ok,
         "{} present, pool {}".format(len(recast), report.get("recast_tile_pool")))

    # 3. the bounds volume, from the SAVED map - asserted, never resized here
    vols = [a for a in unreal.GameplayStatics.get_all_actors_of_class(
        world, unreal.NavMeshBoundsVolume)]
    covered = False
    if vols:
        lo, hi = vols[0].get_actor_bounds(False)
        report["nav_bounds_min"] = [round(lo.x), round(lo.y), round(lo.z)]
        report["nav_bounds_max"] = [round(hi.x), round(hi.y), round(hi.z)]
        misses = []
        for name, px, py, pz in COVER_CM:
            inside = (lo.x <= px <= hi.x and lo.y <= py <= hi.y and lo.z <= pz <= hi.z)
            if not inside:
                misses.append(name)
        covered = not misses
        if misses:
            report["errors"].append("nav bounds do not cover: " + ", ".join(misses)
                                    + " (re-run expand_ravenshoe.py)")
    report["nav_bounds_scale"] = (
        [round(v) for v in vols[0].get_actor_scale3d().to_tuple()] if vols else None)
    step("nav_bounds_volume", bool(vols) and covered,
         "{} volume(s) scale {}".format(
             len(vols), report["nav_bounds_scale"]))

    # 4. build - only in build mode, ONCE. build_dryriver_nav.py issues a single BUILDPATHS and its
    #    map saves; issuing it a second time rebuilds on live tile data and access-violates UnrealEd
    #    here (measured 2026-09-29: build completes in 1.15 s, the crash lands 2.3 s later, on the
    #    second rebuild). The bounds volume comes from the SAVED map via load_map, so its
    #    registration - the thing Red Gum needed the second pass for - is already done.
    if BUILD:
        unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")
        step("buildpaths_issued", True, "BUILDPATHS x1")
    else:
        report["notes"] = [
            "read-only verify run: no BUILDPATHS, nothing saved",
            "set SS_RAVENSHOE_NAV_BUILD=1 and run in an INTERACTIVE editor "
            "to bake; BUILDPATHS is a no-op under -nullrhi and "
            "-RenderOffscreen falls back to the Null RHI on this machine",
        ]
        step("buildpaths_issued", True, "skipped (verify mode)")

    # 5. does the nav data actually exist? Under -nullrhi it silently does not,
    #    so this is the check that distinguishes the two cases.
    navsys = unreal.NavigationSystemV1.get_navigation_system(world)
    probe = unreal.Vector(0.0, 0.0, 1400.0)      # OBJ A, the span
    projected = unreal.NavigationSystemV1.project_point_to_navigation(
        world, probe, None, None, unreal.Vector(500, 500, 5000))
    have = projected is not None and str(projected) != "None"
    report["nav_projection_at_obj_a"] = str(projected)
    report["nav_baked"] = have
    if BUILD:
        step("navmesh_exists", have,
             "project_point_to_navigation -> {}".format(projected))
    else:
        report.setdefault("checks", {})["navmesh_exists"] = have

    # 6. the thing that actually matters: can a player walk the map?
    objs = {a.get_actor_label(): a.get_actor_location()
            for a in unreal.GameplayStatics.get_all_actors_of_class(
                world, unreal.SSObjectiveActor)}
    starts = {a.get_actor_label(): a.get_actor_location()
              for a in unreal.GameplayStatics.get_all_actors_of_class(
                  world, unreal.PlayerStart)}
    report["objectives"] = {k: [round(v) for v in loc.to_tuple()]
                            for k, loc in objs.items()}
    report["deployments"] = {k: [round(v) for v in loc.to_tuple()]
                             for k, loc in starts.items()}

    pairs = []
    for on, ol in objs.items():
        for sn, sl in starts.items():
            ok = reachable(world, ol, sl) and reachable(world, sl, ol)
            pairs.append(ok)
            report["routes"].append({
                "from": on, "to": sn, "reachable_both_ways": ok})
    step("objectives_reachable_from_deployments", bool(pairs) and all(pairs),
         "{}/{} route(s)".format(sum(pairs), len(pairs)))
    if not all(pairs):
        report["errors"].append(
            "not every objective is reachable from every deployment; see routes")

    # 7. the creek bed is the map's second lane and is a distinct design
    #    commitment, so it is probed explicitly rather than assumed.
    bed = unreal.NavigationSystemV1.project_point_to_navigation(
        world, unreal.Vector(0.0, 0.0, -1800.0), None, None,
        unreal.Vector(3000, 3000, 3000))
    report["nav_in_creek_bed"] = str(bed)
    step("creek_bed_navigable", bed is not None and str(bed) != "None", str(bed))

    # 8. the deck itself: the map's primary firefight must be standable
    deck = unreal.NavigationSystemV1.project_point_to_navigation(
        world, unreal.Vector(0.0, 0.0, 1500.0), None, None,
        unreal.Vector(4000, 4000, 2000))
    report["nav_on_deck"] = str(deck)
    step("deck_navigable", deck is not None and str(deck) != "None", str(deck))

    saved = True
    if BUILD:
        # The Dry River pipeline's save, exactly. EditorLoadingAndSavingUtils.save_map reports
        # success here but serialises NO nav tiles (measured 2026-09-29: the map stayed 1.17 MB
        # against Dry River's 7.6 MB, and a fresh verify run found nothing) - and it is where the
        # earlier access-violation landed. LevelEditorSubsystem.save_current_level is what
        # build_dryriver_nav.py uses, and Dry River carries 560 tiles.
        sub = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        saved, via = False, "no working save API"
        for name in ("save_current_level", "save_all_dirty_levels"):
            fn = getattr(sub, name, None)
            if fn is None:
                continue
            try:
                if fn():
                    saved, via = True, name
                    break
            except Exception as exc:               # noqa: BLE001
                report["warnings"].append("{}: {}".format(name, exc))
    step("save_map", saved, MAP if BUILD else "not saved (verify mode)")

    # In verify mode a missing navmesh is a FINDING, not a pass/failure: the
    # script is being asked what the state is, not to change it. Only build
    # mode can be held responsible for producing nav.
    if not BUILD:
        report["ok"] = not report["errors"]
        report["nav_baked"] = bool(
            step("navmesh_exists", have, str(projected)))
    else:
        report["ok"] = all(s["ok"] for s in report["steps"]) and not report["errors"]


try:
    main()
except Exception:  # noqa: BLE001
    report["errors"].append(traceback.format_exc())
finally:
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, default=str)
