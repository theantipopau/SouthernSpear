"""The only collision test that cannot be argued with: a ray that can only hit
the actor it is aimed at.

Every previous measurement on this map was ambiguous:

  - rays fired INTO an actor from 3 m outside missed the known-solid farmhouse,
  - rays fired straight down at it "hit" at 423 cm, which is 3 cm above the
    house's own base - i.e. they hit the terrain underneath and passed through
    the house on the way.

So this fires a 1 m ray from 50 cm above the actor's own top, straight down to
50 cm below it. The ray is entirely within the actor's vertical extent plus a
margin, so terrain cannot be the answer, and there is nothing else in 1 m of
clear air above a roof. Hit means this actor is solid. Miss means it is a
picture of a wall.

Run across a sample of every placed kind, plus the pack's own ridges and the
Landscape for calibration.

Read only. Writes Build/redgum_selfcollide.json.
"""
import json
import os
from collections import OrderedDict

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT = os.path.join(PROJECT_DIR, "Build", "redgum_selfcollide.json")
MAP = "/Game/Maps/L_RedGum_01"
DRESS = "SS_RedGum_Dress_v1_"
HOME = "SS_RedGum_Homestead_"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise SystemExit("could not load " + MAP)


def hit_between(start, end):
    res = unreal.SystemLibrary.line_trace_single(
        world, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
        False, [], unreal.DrawDebugTrace.NONE, True)
    if res is None:
        return False, None
    if isinstance(res, (list, tuple)):
        if not res or not res[0]:
            return False, None
        hit = res[1]
    else:
        hit = res
    try:
        point = (hit.to_dict().get("impact_point") or {}).get("z")
    except Exception:  # noqa: BLE001
        point = None
    return True, round(float(point)) if point is not None else None


def self_test(actor):
    """Hit the actor from directly above its own bounds. 1 m ray."""
    origin, extent = actor.get_actor_bounds(False)
    top = origin.z + extent.z
    return hit_between(unreal.Vector(origin.x, origin.y, top + 50.0),
                       unreal.Vector(origin.x, origin.y, top - 50.0))


kinds = OrderedDict()
for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
    label = actor.get_actor_label()
    if label.startswith(DRESS):
        kinds.setdefault(label[len(DRESS):].rsplit("_", 2)[0], []).append(actor)
    elif label.startswith(HOME):
        kinds.setdefault("HOME_" + label[len(HOME):], []).append(actor)

report = {"map": MAP, "results": {}, "sample_per_kind": 8}
for kind, actors in sorted(kinds.items()):
    tested, hits = 0, 0
    detail = []
    for actor in actors[:8]:
        if not actor.static_mesh_component.static_mesh:
            continue
        tested += 1
        hit, z = self_test(actor)
        hits += 1 if hit else 0
        if len(detail) < 3:
            origin, extent = actor.get_actor_bounds(False)
            detail.append({"label": actor.get_actor_label(),
                           "mesh": actor.static_mesh_component.static_mesh.get_name(),
                           "hit": hit, "impact_z": z,
                           "bounds_top_z": round(origin.z + extent.z),
                           "height_m": round(2 * extent.z / 100, 2)})
    report["results"][kind] = {"actors": len(actors), "tested": tested,
                               "solid": "{}/{}".format(hits, tested), "detail": detail}

# Calibration: the Landscape must be solid, or the trace is broken.
landscape = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LandscapeProxy)
if landscape:
    res = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(0, 0, 50000), unreal.Vector(0, 0, -50000),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [],
        unreal.DrawDebugTrace.NONE, True)
    report["calibration_landscape_hit"] = bool(res)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2, default=str)
unreal.log("[RedGumSelfCollide] done")
