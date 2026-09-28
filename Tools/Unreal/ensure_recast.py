"""Get a RecastNavMesh back onto the map after the bounds resize.

The previous pass destroyed the old actor (its tile pool was serialised for
2448 tiles against a bounds volume that covered a quarter of the map) and the
replacement spawn returned None. UE should auto-create nav data for a level
that has a NavMeshBoundsVolume, so the first thing to check is whether one has
already appeared on load. If not, try the EditorActorSubsystem spawn route,
which is the non-deprecated path and is more permissive than the level library.

Read-only apart from the spawn attempt. Writes Build/ravenshoe_recast.json.
"""
import json
import os
import traceback

import unreal

MAP = "/Game/Maps/L_Ravenshoe_01"
OUT = os.path.join(
    unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()),
    "Build", "ravenshoe_recast.json")
report = {"map": MAP, "attempts": []}


def recasts(sub):
    return [a for a in sub.get_all_level_actors()
            if isinstance(a, unreal.RecastNavMesh)]


def attempt(name, fn):
    try:
        got = fn()
        report["attempts"].append({"how": name, "ok": bool(got),
                                   "detail": str(got)[:120]})
        return got
    except Exception as exc:                              # noqa: BLE001
        report["attempts"].append({"how": name, "ok": False,
                                   "detail": type(exc).__name__ + ": "
                                   + str(exc).splitlines()[0][:100]})
        return None


try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    world = unreal.EditorLevelLibrary.get_editor_world()
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    found = recasts(sub)
    report["on_load"] = [a.get_actor_label() for a in found]
    report["auto_created"] = bool(found)

    if not found:
        report["spawn"] = str(attempt(
            "EditorActorSubsystem.spawn_actor_from_class",
            lambda: sub.spawn_actor_from_class(
                unreal.RecastNavMesh, unreal.Vector(0, 0, 0),
                unreal.Rotator(0, 0, 0))))
        found = recasts(sub)
        report["after_subsystem_spawn"] = [a.get_actor_label() for a in found]

    if not found:
        report["spawn2"] = str(attempt(
            "EditorLevelLibrary.spawn_actor_from_object",
            lambda: unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.RecastNavMesh, unreal.Vector(0, 0, 0),
                unreal.Rotator(0, 0, 0))))
        found = recasts(sub)
        report["after_library_spawn"] = [a.get_actor_label() for a in found]

    if found:
        found[0].set_actor_label("RecastNavMesh-Default")

    # Whatever the outcome, report the bounds volume too, because that is the
    # thing the navmesh has to fit inside.
    vols = [a for a in sub.get_all_level_actors()
            if isinstance(a, unreal.NavMeshBoundsVolume)]
    report["bounds_volumes"] = []
    for v in vols:
        b = v.get_actor_bounds(False)
        report["bounds_volumes"].append({
            "label": v.get_actor_label(),
            "min": [b[0].x, b[0].y, b[0].z],
            "max": [b[1].x, b[1].y, b[1].z],
        })

    report["has_recast"] = bool(recasts(sub))
    saved = False
    if report["has_recast"]:
        saved = unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)
    report["saved"] = saved
    report["ok"] = report["has_recast"]
except Exception:                                         # noqa: BLE001
    report["exception"] = traceback.format_exc()
    report["ok"] = False

with open(OUT, "w") as fh:
    json.dump(report, fh, indent=2, default=str)
print("RECAST_WRITTEN", OUT, "ok=", report.get("ok"))
