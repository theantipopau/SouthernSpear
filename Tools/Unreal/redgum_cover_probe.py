"""Does the Red Gum dressing actually block anything?

The playability audit counted 2 hard / 0 soft cover on a map carrying 1,183
static mesh actors, and reported 69% of sampled ground with nothing within 30 m.
Those numbers are only explicable if the dressing does not collide: a tree that
looks solid and passes bullets and AI is worse than no tree, because it reads
as cover in a screenshot and is not.

    A TREE THAT LOOKS LIKE COVER AND IS NOT IS THE EXPENSIVE KIND OF DRESSING.

HOW THIS MEASURES IT, AND WHY THE OBVIOUS WAY IS WRONG

The first version traced 90 cm sideways from each actor's bounds centre and
found that even the farmhouse - known solid, verified 5 of 5 by a vertical
trace during placement - blocked nothing. A trace that STARTS INSIDE a convex
hull does not report a blocking hit, so the control group failed with the
subjects and the measurement looked like "nothing collides".

This version traces INTO each actor from clear air 3 m outside its bounds, so
the ray is outside the shape before it can hit it, and it also reports
bUseComplexAsSimple and CollisionComplexity, which together with the stored
simple-collision count decide whether a component has any shape at all.

The homestead meshes, imported with auto_generate_collision, are the control
group: if the pack's trees differ from them, the difference is in the asset.

Read only. Writes Build/redgum_cover_probe.json.
"""
import json
import math
import os
from collections import OrderedDict

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT = os.path.join(PROJECT_DIR, "Build", "redgum_cover_probe.json")
MAP = "/Game/Maps/L_RedGum_01"
SAMPLE_PER_KIND = 5
DRESS_PREFIX = "SS_RedGum_Dress_v1_"
HOME_PREFIX = "SS_RedGum_Homestead_"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
if not world:
    raise SystemExit("could not load " + MAP)

SIMPLE_PROPS = ("box_elems", "sphere_elems", "convex_elems",
                "tapered_capsule_elems", "level_set_elems")


def mesh_flag(mesh, prop):
    try:
        return str(mesh.get_editor_property(prop))
    except Exception:  # noqa: BLE001
        return "unreadable"


def simple_elements(mesh):
    try:
        geom = mesh.get_editor_property("body_setup").get_editor_property("agg_geom")
    except Exception:  # noqa: BLE001
        return None
    total = 0
    for prop in SIMPLE_PROPS:
        try:
            total += len(geom.get_editor_property(prop))
        except Exception:  # noqa: BLE001
            pass
    return total


def trace_into(world, origin, extent):
    """Trace at the actor from 3 m of clear air outside its own bounds.

    Started outside on purpose - see the module docstring. Any hit means the
    ray found this actor's geometry (or something in front of it, which is why
    the distance to the impact is compared against the actor's own extent).
    """
    start = unreal.Vector(origin.x + extent.x + 300.0, origin.y, origin.z)
    res = unreal.SystemLibrary.line_trace_single(
        world, start, unreal.Vector(origin.x, origin.y, origin.z),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [],
        unreal.DrawDebugTrace.NONE, True)
    if res is None:
        return {"hit": False, "travelled_m": None, "hit_actor": None}
    if isinstance(res, (list, tuple)):
        if not res or not res[0]:
            return {"hit": False, "travelled_m": None, "hit_actor": None}
        res = res[1]
    try:
        fields = res.to_dict()
    except Exception:  # noqa: BLE001
        return {"hit": True, "travelled_m": None, "hit_actor": None}
    point = fields.get("impact_point") or fields.get("location")
    travelled = None
    if point is not None:
        # Read the components: unreal.Vector(some_vector) tries to re-nativise
        # a Vector through MakeVector and raises, so the fields are read out.
        try:
            dx = float(point.x) - start.x
            dy = float(point.y) - start.y
            dz = float(point.z) - start.z
            travelled = round(math.sqrt(dx * dx + dy * dy + dz * dz) / 100.0, 2)
        except Exception:  # noqa: BLE001
            travelled = None
    return {"hit": True, "travelled_m": travelled, "hit_actor": str(fields.get("actor"))}


def kind_of(label):
    """Dressing kind without the pass prefix: TreeLine_08_08 -> TreeLine."""
    body = label[len(DRESS_PREFIX):] if label.startswith(DRESS_PREFIX) else \
        label[len(HOME_PREFIX):]
    return body.rsplit("_", 2)[0] if body.count("_") >= 2 else body


kinds = OrderedDict()
for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
    label = actor.get_actor_label()
    if not (label.startswith(DRESS_PREFIX) or label.startswith(HOME_PREFIX)):
        continue
    kinds.setdefault(kind_of(label), []).append(actor)

report = {"map": MAP, "actors_by_kind": {}, "kinds": {}}
for kind, actors in sorted(kinds.items()):
    report["actors_by_kind"][kind] = len(actors)
    rows = []
    for actor in actors[:SAMPLE_PER_KIND]:
        mesh = actor.static_mesh_component.static_mesh
        if mesh is None:
            continue
        origin, extent = actor.get_actor_bounds(False)
        probe = trace_into(world, origin, extent)
        rows.append({
            "label": actor.get_actor_label(),
            "mesh": mesh.get_name(),
            "trace_flag": mesh_flag(mesh, "body_setup") and str(
                mesh.get_editor_property("body_setup")
                .get_editor_property("collision_trace_flag")),
            "simple_elements": simple_elements(mesh),
            "complex_as_simple": mesh_flag(mesh, "b_use_complex_as_simple"),
            "collision_complexity": mesh_flag(mesh, "collision_complexity"),
            "bounds_m": [round(2 * extent.x / 100, 2), round(2 * extent.y / 100, 2),
                         round(2 * extent.z / 100, 2)],
            "actor_collision_enabled": actor.get_actor_enable_collision(),
            "profile": str(actor.static_mesh_component.get_collision_profile_name()),
            "ray_from_outside": probe,
        })
    if rows:
        report["kinds"][kind] = {
            "sampled": len(rows),
            "trace_flags": sorted({r["trace_flag"] for r in rows}),
            "simple_elements": sorted({str(r["simple_elements"]) for r in rows}),
            "complex_as_simple": sorted({r["complex_as_simple"] for r in rows}),
            "collision_complexity": sorted({r["collision_complexity"] for r in rows}),
            "hit_from_outside": "{}/{}".format(
                sum(1 for r in rows if r["ray_from_outside"]["hit"]), len(rows)),
            "rows": rows,
        }

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
unreal.log("[RedGumCoverProbe] {} kinds".format(len(report["kinds"])))
