"""Turn raw Fab FBX downloads into import-ready Ravenshoe props.

Three problems have to be solved before any of this is allowed near the bridge:

1. SCALE AND CONTENT. The red Renault wreck authors at 27.3 x 21.0 x 11.2 m
   because the file carries a ground plane and sits at roughly 6x real scale.
   The windmill and barn each ship a ground disc. Importing the file as-is puts
   a 27 m car on a 6 m-wide bridge, or a barn floating on a saucer.

2. PIVOT. Vendor FBX pivots are wherever the modeller left the cursor. Every
   prop must sit base-at-z=0 and centred in xy, or it sinks into the deck or
   hovers above it.

3. BUDGET. The Renault is 1.17M triangles and the compressor 73k. A game map
   cannot spend that on dressing. Each prop is decimated to a stated budget.

Loose parts are separated and only the plausible prop parts are kept, so the
ground planes and any stray debris go without touching the vendor mesh on disk
(ADR-004: appearance only - we place the mesh, we do not resell it).

Writes one FBX per prop into Build/ravenshoe/props/ and a JSON report.
"""
import json
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FAB = os.path.join(ROOT, "Content", "Downloaded", "VaultCache", "FabLibrary")
OUT = os.path.join(ROOT, "Build", "ravenshoe", "props")

# tag, source fbx, triangle budget, expected longest real-world side (metres)
PROPS = [
    ("wreck_car", "Red_car_wreck-04d70886/fbx/red_car_wreck_extracted/source/"
                  "red-renault-carwreck_extracted/red-renault-carwreck.fbx", 18000, 4.6),
    ("wreck_junk", "Abandoned___junk_Car-ee5cffe5/fbx/abandoned-junk-car_extracted/"
                   "source/SM_JUNKCAR1_DEFORMED2.fbx", 12000, 4.6),
    ("fuel_drum", "Fuel_barrel-873fee1d/fbx/barrel.fbx", 4000, 0.9),
    ("windmill", "American_Old_Windmill-d8d4a1d3/fbx/wind_mill.fbx", 9000, 7.0),
    ("barn", "Barn-eb4457bc/fbx/barn.fbx", 5000, 10.9),
    ("sandbag_stack", "Military_Trenches_Pile_Sandbag_Canvas_01-a08111c9/fbx/mid/"
                      "military_trenches_pile_s_extracted/"
                      "Military_Trenches_Pile_Sandbag_Canvas_01_yd0tae2_Mid.fbx", 6000, 0.96),
    ("trench_wall", "Military_Trenches_Wall_Metal_Corrugated_04-e15620d3/fbx/mid/"
                    "military_trenches_wall_m_extracted/"
                    "Military_Trenches_Wall_Metal_Corrugated_04_ydynfbh_Mid.fbx", 6000, 1.77),
    # Second delivery, same session. A water tower and a hand pump are the
    # right period Australian rural detail for a road-closed gorge approach,
    # and the old barn is a better ridge silhouette than the generic one.
    ("water_tower", "Water_Tower-86b17984/fbx/water-tower_extracted/source/"
                    "Water_tower_extracted/Water_tower/Source/Water_Tower.fbx", 8000, 9.0),
    ("hand_pump", "Old_Rustic_Hand_Water_Pump-0b2fc83d/fbx/handpumptexturedfab1.fbx",
                  6000, 1.6),
    ("old_barn", "Old_Barn-4915f85e/fbx/barnold.fbx", 6000, 12.0),
]

# A loose part is a ground plane, not a prop, when it is much wider than it is
# tall AND sits at the bottom of the stack. Vendors scatter these constantly.
def is_ground_plane(size, min_z, total_h):
    planar = size.z < 0.12 * max(size.x, size.y)          # very flat
    at_floor = min_z < 0.02 * max(1.0, total_h) + 0.35  # hugs the bottom
    return planar and at_floor


def split_loose(obj):
    """Split an object into connected components; returns them by name."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def prep(tag, rel, budget, want_longest):
    rec = {"tag": tag, "source": rel, "budget": budget}
    path = os.path.join(FAB, rel.replace("/", os.sep))
    if not os.path.isfile(path):
        rec["error"] = "missing source"
        return rec

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    rec["source_objects"] = len(meshes)

    # Raw vertex coordinates. object.matrix_world is stale straight after import
    # and reading it here silently yields a zero-sized bounding box.
    def raw_bounds(objs):
        cos = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
        if not cos:
            return None
        return (Vector((min(c.x for c in cos), min(c.y for c in cos),
                        min(c.z for c in cos))),
                Vector((max(c.x for c in cos), max(c.y for c in cos),
                        max(c.z for c in cos))))

    before = raw_bounds(meshes)
    rec["source_size"] = [round(v, 3) for v in (before[1] - before[0])]

    # Peel the vendor's ground planes off. split_loose() DELETES the object it
    # is handed and returns brand new ones, so ANY list of objects captured
    # before the call is stale by the time it is used. Re-query the scene and
    # act on exactly one object per iteration instead.
    dropped = []
    for _step in range(400):
        pending = [o for o in bpy.context.scene.objects
                   if o.type == "MESH" and not o.get("ss_peeled")]
        if not pending:
            break
        obj = pending[0]
        obj["ss_peeled"] = True
        parts = split_loose(obj)
        if len(parts) <= 1:
            continue
        b = raw_bounds(parts)
        total_h = b[1].z - b[0].z
        keep, kill = [], []
        for p in parts:
            (kill if is_ground_plane(p.dimensions, b[0].z, total_h)
             else keep).append(p)
        # Never let a pass empty the scene; if the heuristic rejected
        # everything, fall back to the heaviest remaining part.
        if not keep:
            keep = [max(parts, key=lambda p: len(p.data.polygons))]
        for p in kill:
            if p.name in keep:
                continue
            dropped.append("{}:{}".format(p.name,
                                          [round(v, 2) for v in p.dimensions]))
            bpy.data.objects.remove(p, do_unlink=True)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    rec["ground_parts_dropped"] = dropped

    # Join, then measure. Everything after this is on one mesh.
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = "SS_Raven_" + tag

    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0005)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_flat()

    b0 = raw_bounds([obj])
    size0 = b0[1] - b0[0]
    rec["after_cleanup_size"] = [round(v, 3) for v in size0]

    # Scale to the real-world size the prop should be. Vendor scale is a guess;
    # the design intent is not.
    longest = max(size0.x, size0.y, size0.z)
    if longest > 0:
        s = want_longest / longest
        obj.scale = (s, s, s)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    rec["scale_applied"] = round(s, 5) if longest > 0 else None

    # Decimate to budget. ratio is per-object face reduction.
    faces = len(obj.data.polygons)
    if faces > budget:
        obj.data.calc_loop_triangles()
        ratio = max(0.02, budget / float(faces))
        mod = obj.modifiers.new("dec", "DECIMATE")
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)

    # Sit base-at-z=0, centred in xy. From raw coords - a matrix_world read here
    # is exactly the stale-data trap this script exists to avoid.
    cos = [v.co for v in obj.data.vertices]
    lo = Vector((min(c.x for c in cos), min(c.y for c in cos), min(c.z for c in cos)))
    hi = Vector((max(c.x for c in cos), max(c.y for c in cos), max(c.z for c in cos)))
    for v in obj.data.vertices:
        v.co.x -= (lo.x + hi.x) * 0.5
        v.co.y -= (lo.y + hi.y) * 0.5
        v.co.z -= lo.z

    size = hi - lo
    rec["final_size"] = [round(v, 3) for v in size]
    rec["final_tris"] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    rec["final_verts"] = len(obj.data.vertices)
    rec["base_at_zero"] = True

    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, "SS_Raven_{}.fbx".format(tag))
    bpy.ops.export_scene.fbx(filepath=dest, use_selection=True, apply_scale_options="FBX_SCALE_UNITS",
                             object_types={"MESH"}, mesh_smooth_type="FACE", use_mesh_modifiers=True)
    rec["exported"] = os.path.relpath(dest, ROOT).replace(os.sep, "/")
    rec["export_mb"] = round(os.path.getsize(dest) / 1048576.0, 2)
    return rec


os.makedirs(OUT, exist_ok=True)
report = []
for tag, rel, budget, want in PROPS:
    sys.stdout.write("prep {} ... ".format(tag))
    sys.stdout.flush()
    r = prep(tag, rel, budget, want)
    report.append(r)
    if r.get("error"):
        sys.stdout.write("ERROR {}\n".format(r["error"]))
    else:
        sys.stdout.write("{} -> {} m, {} tris, scale {}\n".format(
            tag, r["final_size"], r["final_tris"], r["scale_applied"]))

with open(os.path.join(ROOT, "Build", "prep_fab_props.json"), "w",
          encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
sys.stdout.write("wrote Build/prep_fab_props.json\n")
