"""Is the Red Gum tree dressing solid, or does it only look it?

Two questions, one experiment, because both earlier measurements were
untrustworthy:

  1. Does SM_Tree_L_01 (the big gum, 352 of them on the map) have any collision
     at all? The cover probe says it stores 0 simple-collision elements.
  2. Is the probe's own trace call valid? It reported that the farmhouse -
     which placement verified with 5 of 5 vertical trace probes - blocked
     nothing, which cannot both be true.

So this runs the same rays four ways against one known-solid actor and one
tree actor: horizontal-from-outside and vertical-from-above, each with
trace_complex False and True. The farmhouse is the control: whatever the
control answers, that is what "a working trace" looks like on this build, and
the tree is then read against it rather than against my assumptions.

Read only. Writes Build/redgum_trace_ab.json.
"""
import json
import os

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT = os.path.join(PROJECT_DIR, "Build", "redgum_trace_ab.json")
MAP = "/Game/Maps/L_RedGum_01"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise SystemExit("could not load " + MAP)


def trace(start, end, complex_trace):
    res = unreal.SystemLibrary.line_trace_single(
        world, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
        complex_trace, [], unreal.DrawDebugTrace.NONE, True)
    if res is None:
        return {"hit": False, "raw": "None"}
    if isinstance(res, (list, tuple)):
        if not res or not res[0]:
            return {"hit": False, "raw": "tuple-false"}
        hit = res[1]
    else:
        hit = res
    try:
        fields = hit.to_dict()
    except Exception as exc:  # noqa: BLE001
        return {"hit": True, "raw": "no-dict: {}".format(exc)}
    point = fields.get("impact_point") or fields.get("location")
    return {
        "hit": True,
        "impact_z_cm": round(float(point.z)) if point is not None else None,
        "actor": str(fields.get("actor"))[:60],
    }


def probe(actor):
    mesh = actor.static_mesh_component.static_mesh
    origin, extent = actor.get_actor_bounds(False)
    comp = actor.static_mesh_component
    out = {
        "label": actor.get_actor_label(),
        "mesh": mesh.get_name() if mesh else None,
        "bounds_m": [round(2 * extent.x / 100, 2), round(2 * extent.y / 100, 2),
                     round(2 * extent.z / 100, 2)],
        "actor_collision_enabled": actor.get_actor_enable_collision(),
        "component_collision_enabled": comp.get_collision_enabled(),
        "profile": str(comp.get_collision_profile_name()),
        "component_world_location": [round(float(comp.get_world_location().x)),
                                     round(float(comp.get_world_location().y)),
                                     round(float(comp.get_world_location().z))],
        "component_scale": round(comp.get_world_scale().x, 3),
        "responses": {},
    }
    # Outward-in horizontal rays from four sides.
    for label, start in (
            ("east", unreal.Vector(origin.x + extent.x + 300.0, origin.y, origin.z)),
            ("west", unreal.Vector(origin.x - extent.x - 300.0, origin.y, origin.z)),
            ("north", unreal.Vector(origin.x, origin.y + extent.y + 300.0, origin.z)),
    ):
        for cx in (False, True):
            key = "h_{}_{}".format(label, "complex" if cx else "simple")
            out["responses"][key] = trace(
                start, unreal.Vector(origin.x, origin.y, origin.z), cx)
    # Straight down from above the top of the bounds.
    for cx in (False, True):
        key = "v_down_{}".format("complex" if cx else "simple")
        out["responses"][key] = trace(
            unreal.Vector(origin.x, origin.y, origin.z + extent.z + 500.0),
            unreal.Vector(origin.x, origin.y, origin.z - extent.z - 500.0), cx)
    return out


def find_one(prefix):
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        if actor.get_actor_label().startswith(prefix):
            return actor
    return None


result = {"map": MAP, "actors": {}}
for name, prefix in (("farmhouse_CONTROL_known_solid", "SS_RedGum_Homestead_Farmhouse"),
                     ("treeline_SM_Tree_L_01", "SS_RedGum_Dress_v1_TreeLine_"),
                     ("rock_SM_Rock_M_01", "SS_RedGum_Dress_v1_Rock_"),
                     ("log_SM_Log_M_01", "SS_RedGum_Dress_v1_Log_")):
    actor = find_one(prefix)
    result["actors"][name] = probe(actor) if actor else {"error": "not found"}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(result, fh, indent=2, default=str)
unreal.log("[RedGumTraceAB] done")
