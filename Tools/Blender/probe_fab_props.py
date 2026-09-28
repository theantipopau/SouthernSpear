"""Measure the new Fab downloads before anything is imported.

Every third-party FBX arrives in whatever units, axis order and orientation its
author happened to use. Importing blind into the bridge is how you end up with a
car that is 1.7 km long, lying on its side, or sunk through the deck. So:
measure first, decide second, import third.

Reports per FBX: object count, triangle count, world bounding box, implied
units-per-metre, whether it arrived Y-up (needs a -90 deg X) and the raw mesh
bounds. Writes JSON - Blender's stdout does not reach the editor log either.

Run:  blender -b --factory-startup --python Tools/Blender/probe_fab_props.py
"""
import json
import os
import sys

import bpy
from mathutils import Vector

FAB = os.path.join(bpy.path.abspath("//"), "Content", "Downloaded",
                   "VaultCache", "FabLibrary")
OUT = os.path.join(bpy.path.abspath("//"), "Build", "probe_fab_props.json")

CANDIDATES = [
    ("car_wreck", "Red_car_wreck-04d70886/fbx/red_car_wreck_extracted/source/"
                  "red-renault-carwreck_extracted/red-renault-carwreck.fbx"),
    ("junk_car", "Abandoned___junk_Car-ee5cffe5/fbx/abandoned-junk-car_extracted/"
                "source/SM_JUNKCAR1_DEFORMED2.fbx"),
    ("fuel_barrel", "Fuel_barrel-873fee1d/fbx/barrel.fbx"),
    ("windmill", "American_Old_Windmill-d8d4a1d3/fbx/wind_mill.fbx"),
    ("barn", "Barn-eb4457bc/fbx/barn.fbx"),
    ("trench_sandbags", "Military_Trenches_Pile_Sandbag_Canvas_01-a08111c9/fbx/mid/"
                        "military_trenches_pile_s_extracted/"
                        "Military_Trenches_Pile_Sandbag_Canvas_01_yd0tae2_Mid.fbx"),
    ("trench_debris", "Military_Trenches_Debris_Pile_Rock_S-11e2529f/fbx/high/"
                      "military_trenches_debris_extracted/"
                      "Military_Trenches_Debris_Pile_Rock_S_ydyqbbls_High.fbx"),
    ("trench_wall", "Military_Trenches_Wall_Metal_Corrugated_04-e15620d3/fbx/mid/"
                    "military_trenches_wall_m_extracted/"
                    "Military_Trenches_Wall_Metal_Corrugated_04_ydynfbh_Mid.fbx"),
    ("compressor", "Diesel_Compressor_IRMER_ELZE-4b406aa6/fbx/"
                   "diesel_compressor_irmere_extracted/source/"
                   "Air_Compressor_FAB.fbx"),
]


def measure(tag, rel):
    """Import one FBX into a clean scene and report what it actually is."""
    path = os.path.join(FAB, rel.replace("/", os.sep))
    rec = {"tag": tag, "path": rel, "exists": os.path.isfile(path)}
    if not rec["exists"]:
        rec["error"] = "file not found"
        return rec
    rec["bytes"] = os.path.getsize(path)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.fbx(filepath=path)
    except Exception as exc:  # noqa: BLE001
        rec["error"] = "import failed: {}".format(exc)[:200]
        return rec

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    rec["object_count"] = len(meshes)
    if not meshes:
        rec["error"] = "no mesh objects"
        return rec

    # Raw vertex coordinates only. object.matrix_world is unreliable right after
    # import and a stale read here silently yields a zero-sized bbox.
    cos = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    lo = Vector((min(c.x for c in cos), min(c.y for c in cos),
                 min(c.z for c in cos)))
    hi = Vector((max(c.x for c in cos), max(c.y for c in cos),
                 max(c.z for c in cos)))
    size = hi - lo
    rec["bbox_min"] = [round(v, 4) for v in lo]
    rec["bbox_max"] = [round(v, 4) for v in hi]
    rec["size"] = [round(v, 4) for v in size]
    rec["centre"] = [round(v, 4) for v in ((hi + lo) * 0.5)]

    # Every FBX is Y-up on export; Blender converts to Z-up. If the model came in
    # correct, the tall axis is Z. If it is the Y axis, it arrived rotated.
    longest = max(range(3), key=lambda i: size[i])
    rec["longest_axis"] = "XYZ"[longest]
    rec["probably_y_up"] = longest == 1

    rec["triangles"] = sum(len(o.data.loop_triangles)
                           for o in meshes
                           if o.data.calc_loop_triangles() is None) or None
    if rec["triangles"] is None:
        rec["triangles"] = sum(
            sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    rec["objects"] = [{"name": o.name,
                       "verts": len(o.data.vertices),
                       "faces": len(o.data.polygons),
                       "dims": [round(v, 3) for v in o.dimensions]}
                      for o in meshes[:12]]

    # A car body should land in the 3.5-6 m band. If we are far outside it the
    # author used centimetres or inches and we must scale on import.
    rec["verdict_plausible_m"] = 0.5 <= max(size.x, size.y) <= 12.0
    return rec


report = {}
for tag, rel in CANDIDATES:
    sys.stdout.write("measuring {} ... ".format(tag))
    sys.stdout.flush()
    report[tag] = measure(tag, rel)
    r = report[tag]
    if r.get("error"):
        sys.stdout.write("ERROR {}\n".format(r["error"]))
    else:
        sys.stdout.write("{} objs  size={}  tris={}\n".format(
            r["object_count"], r["size"], r["triangles"]))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
sys.stdout.write("wrote {}\n".format(OUT))
