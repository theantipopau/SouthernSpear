"""Can this commandlet ray-trace a static mesh at all?

Every StaticMeshActor tested so far - the pack's trees, rocks, logs and ridges,
and the homestead this session imported - is invisible to
SystemLibrary.line_trace_single, while the Landscape is hit. Two explanations
remain and they mean opposite things:

  (a) the actors really have no collision, in which case the playability
      audit's "2 hard / 0 soft cover" and "69% of ground with nothing within
      30 m" are TRUE and the map is a shooting gallery, or
  (b) the commandlet only registers actors that existed when the map loaded,
      in which case the audit's cover numbers are a measurement artifact and
      say nothing about the map.

The discriminator is a pre-existing actor. Anything not labelled
SS_RedGum_Dress_v1_ or SS_RedGum_Homestead_ came out of the .umap, so the
engine had it registered at load time. If those are hit, it is (b).

Read only. Writes Build/redgum_collision_capability.json.
"""
import json
import os

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT = os.path.join(PROJECT_DIR, "Build", "redgum_collision_capability.json")
MAP = "/Game/Maps/L_RedGum_01"
MINE = ("SS_RedGum_Dress_v1_", "SS_RedGum_Homestead_")

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise SystemExit("could not load " + MAP)


def self_test(actor):
    """1 m ray from 50 cm above the actor's own top, down into it."""
    origin, extent = actor.get_actor_bounds(False)
    top = origin.z + extent.z
    res = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(origin.x, origin.y, top + 50.0),
        unreal.Vector(origin.x, origin.y, top - 50.0),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
        unreal.DrawDebugTrace.NONE, True)
    if res is None:
        return False
    if isinstance(res, (list, tuple)):
        return bool(res and res[0])
    return True


pre_existing, from_this_session = [], []
for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
    label = actor.get_actor_label()
    if not actor.static_mesh_component.static_mesh:
        continue
    origin, extent = actor.get_actor_bounds(False)
    if 2 * extent.z < 200:      # skip kerbs; a 1 m ray above a 20 cm fence hits sky
        continue
    row = {"label": label, "mesh": actor.static_mesh_component.static_mesh.get_name(),
           "height_m": round(2 * extent.z / 100, 2), "solid": self_test(actor)}
    (from_this_session if label.startswith(MINE) else pre_existing).append(row)

report = {
    "map": MAP,
    "pre_existing_total": len(pre_existing),
    "pre_existing_solid": sum(1 for r in pre_existing if r["solid"]),
    "this_session_total": len(from_this_session),
    "this_session_solid": sum(1 for r in from_this_session if r["solid"]),
    "pre_existing_sample": pre_existing[:25],
    "verdict": None,
}
report["verdict"] = (
    "commandlet cannot query pre-existing static meshes either -> the audit's "
    "cover numbers are a measurement artifact"
    if report["pre_existing_solid"] == 0 else
    "pre-existing static meshes ARE solid -> actors spawned by this session are "
    "missing from the physics scene, and the audit's cover numbers are wrong for "
    "the same reason")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2, default=str)
unreal.log("[RedGumCollisionCapability] {}".format(report["verdict"]))
