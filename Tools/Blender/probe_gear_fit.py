# Southern Spear - measure how far fitted gear sits outside the UE5 mannequin's skin, per body region.
#
#   blender -b --factory-startup -P Tools/Blender/probe_gear_fit.py -- <gear.fbx> [<gear.fbx> ...]
#
# Both the gear FBX (from adfrc_gear_rig.py) and Art/Characters/ADF/SKM_Manny_ref.fbx are in the
# mannequin's rest space. For each gear vertex: signed distance to the nearest body surface point
# (positive = outside), grouped by the vertex's strongest bone weight. Prints SS_GEARFIT <json>.

import json
import os
import statistics
import sys

import bpy
from mathutils.bvhtree import BVHTree

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MANNY = os.path.join(ROOT, "Art", "Characters", "ADF", "SKM_Manny_ref.fbx")
GEAR = sys.argv[sys.argv.index("--") + 1:]

REGIONS = {"upperarm": "upper arm", "lowerarm": "forearm", "thigh": "thigh", "calf": "calf",
           "spine": "torso", "clavicle": "torso", "pelvis": "pelvis", "neck": "neck", "hand": "hand", "foot": "foot"}


def import_meshes(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.type == "MESH"]


def region(obj, v):
    if not v.groups:
        return "unweighted"
    g = max(v.groups, key=lambda x: x.weight)
    name = obj.vertex_groups[g.group].name.lower()
    for key, label in REGIONS.items():
        if key in name:
            return label
    return "other"


bpy.ops.wm.read_factory_settings(use_empty=True)
body_objs = import_meshes(MANNY)
body = max(body_objs, key=lambda o: len(o.data.vertices))
deps = bpy.context.evaluated_depsgraph_get()
tree = BVHTree.FromObject(body, deps)  # world space via FromObject? (uses object data: apply below)
# BVHTree.FromObject builds in object space; keep everything in world space explicitly.
mw = body.matrix_world
verts = [mw @ v.co for v in body.data.vertices]
polys = [list(p.vertices) for p in body.data.polygons]
tree = BVHTree.FromPolygons(verts, polys)

out = {"body": body.name, "body_verts": len(verts), "gear": {}}
for path in GEAR:
    for obj in import_meshes(path):
        by = {}
        gw = obj.matrix_world
        for v in obj.data.vertices:
            p = gw @ v.co
            hit, normal, _, dist = tree.find_nearest(p)
            if hit is None:
                continue
            sign = 1.0 if (p - hit).dot(normal) >= 0 else -1.0
            by.setdefault(region(obj, v), []).append(sign * dist * 100.0)  # cm (FBX imports in metres)
        out["gear"][os.path.basename(path) + ":" + obj.name] = {
            r: {"n": len(d), "median_cm": round(statistics.median(d), 2),
                "p90_cm": round(sorted(d)[int(len(d) * 0.9)], 2)} for r, d in sorted(by.items())}
print("SS_GEARFIT " + json.dumps(out))
