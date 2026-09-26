# Probe for R-10: does dressing collision exist after the map is reopened?
#
# Read-only: loads L_DryRiver_01, never saves. For a few dressing actors it
# traces a real (non-zero-length) vertical ray and a horizontal ray through the
# actor, records the component and body setup state, then forces the physics
# state to be recreated and traces again. Writes Build/r10_probe.json.

import json
import os

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT = os.path.join(PROJECT_DIR, "Build", "r10_probe.json")
MAP = "/Game/Maps/L_DryRiver_01"
SAMPLES = ("SS_Dressing_PaddockEast_Post00", "SS_Dressing_PaddockEast_Rail00_055",
           "SS_Dressing_Wreck_WestBank")

report = {"samples": []}


def trace(world, a, b, complex_=True):
    res = unreal.SystemLibrary.line_trace_single(
        world, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, complex_, [],
        unreal.DrawDebugTrace.NONE, True)
    # (bHit, HitResult) tuple, as build_dryriver_nav.py documents.
    # Python surfaces this as a bare HitResult on a hit and None on a miss.
    if res is None:
        return {"hit": False, "actor": None, "z": None}
    hr = res[1] if isinstance(res, (list, tuple)) else res
    d = hr.to_dict()
    actor = d.get("hit_actor")
    point = d.get("impact_point")
    return {"hit": bool(d.get("blocking_hit", True)),
            "actor": actor.get_actor_label() if actor else None,
            "z": point.z if point is not None and hasattr(point, "z") else None}


def probe(world, actor):
    loc = actor.get_actor_location()
    comp = actor.static_mesh_component
    mesh = comp.static_mesh
    body = mesh.get_editor_property("body_setup") if mesh else None
    agg = body.get_editor_property("agg_geom") if body else None
    down = trace(world, loc + unreal.Vector(0, 0, 400), loc - unreal.Vector(0, 0, 50))
    across = trace(world, loc + unreal.Vector(-300, 0, 20), loc + unreal.Vector(300, 0, 20))
    across_y = trace(world, loc + unreal.Vector(0, -300, 20), loc + unreal.Vector(0, 300, 20))
    across_simple = trace(world, loc + unreal.Vector(-300, 0, 20), loc + unreal.Vector(300, 0, 20), False)
    down_simple = trace(world, loc + unreal.Vector(0, 0, 400), loc - unreal.Vector(0, 0, 50), False)
    ground = trace(world, loc + unreal.Vector(0, 0, 50000), loc - unreal.Vector(0, 0, 50000))
    origin, extent = actor.get_actor_bounds(False)
    mb = mesh.get_bounds() if mesh else None
    return {
        "loc": [loc.x, loc.y, loc.z],
        "scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z],
        "actor_bounds": [origin.z - extent.z, origin.z + extent.z, extent.x, extent.y],
        "mesh_bounds": [mb.origin.z - mb.box_extent.z, mb.origin.z + mb.box_extent.z] if mb else None,
        "mesh": mesh.get_name() if mesh else None,
        "convex": len(agg.get_editor_property("convex_elems")) if agg else None,
        "boxes": len(agg.get_editor_property("box_elems")) if agg else None,
        "trace_flag": str(body.get_editor_property("collision_trace_flag")) if body else None,
        "collision_enabled": str(comp.get_collision_enabled()),
        "profile": str(comp.get_collision_profile_name()),
        "mobility": str(comp.mobility),
        "down": down, "across_x": across, "across_y": across_y,
        "across_simple": across_simple, "down_simple": down_simple, "ground_control": ground,
    }


try:
    # Same load path as build_dryriver_nav.py.
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    report["ground_before_buildpaths"] = trace(
        world, unreal.Vector(0, 8500, 50000), unreal.Vector(0, 8500, -50000))
    # build_dryriver_nav.py traces only after this; mirror it exactly.
    unreal.SystemLibrary.execute_console_command(world, "BUILDPATHS")
    report["ground_after_buildpaths"] = trace(
        world, unreal.Vector(0, 8500, 50000), unreal.Vector(0, 8500, -50000))
    actors = {a.get_actor_label(): a for a in
              unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)}
    for name in SAMPLES:
        a = actors.get(name)
        if a is None:
            report["samples"].append({"label": name, "missing": True})
            continue
        before = probe(world, a)
        comp = a.static_mesh_component
        # Force the component's physics body to be rebuilt, then look again.
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        after = probe(world, a)
        report["samples"].append({"label": name, "before": before, "after_recreate": after})
except Exception as exc:  # noqa: BLE001
    report["error"] = repr(exc)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
unreal.log("R10 probe written: " + OUT)
