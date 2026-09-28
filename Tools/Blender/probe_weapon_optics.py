"""Measure each weapon FBX's optic: where it sits and which way it faces.

    blender -b --factory-startup -P Tools/Blender/probe_weapon_optics.py -- <fbx> [<fbx> ...]

Our weapons point +X (muzzle), up +Z. The optic's parts are the faces whose material name carries an optic
hint (as fix_weapon_optics.py). An optic's objective (front) end is the wider one: the script compares the
YZ cross-section of the optic's rear and front eighths. Prints one JSON line per file.
"""
import json
import sys

import bpy

OPTIC_HINTS = ("ta31", "ta648", "acog", "spectr", "optic", "glass", "ret", "elcan", "scope")


def probe(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    optic, body = [], []
    mats = set()
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH":
            continue
        me = ob.data
        for poly in me.polygons:
            mat = ob.material_slots[poly.material_index].material if ob.material_slots else None
            name = (mat.name if mat else "").lower()
            pts = [ob.matrix_world @ me.vertices[i].co for i in poly.vertices]
            if any(h in name for h in OPTIC_HINTS):
                optic += pts
                mats.add(mat.name)
            else:
                body += pts
    out = {"file": path.replace("\\", "/").split("/")[-1], "optic_materials": sorted(mats)}
    if body:
        out["body_x"] = [round(min(p.x for p in body), 3), round(max(p.x for p in body), 3)]
        out["body_z"] = [round(min(p.z for p in body), 3), round(max(p.z for p in body), 3)]
    if optic:
        lo, hi = min(p.x for p in optic), max(p.x for p in optic)
        span = hi - lo
        rear = [p for p in optic if p.x < lo + span / 8]
        front = [p for p in optic if p.x > hi - span / 8]
        size = lambda ps: round(max(max(p.y for p in ps) - min(p.y for p in ps), max(p.z for p in ps) - min(p.z for p in ps)), 3)
        out.update({"optic_x": [round(lo, 3), round(hi, 3)],
                    "optic_z": [round(min(p.z for p in optic), 3), round(max(p.z for p in optic), 3)],
                    "rear_size": size(rear), "front_size": size(front),
                    "faces": "muzzle (objective front)" if size(front) >= size(rear) else "REVERSED (objective at the rear)"})
    print("PROBE " + json.dumps(out))


for f in sys.argv[sys.argv.index("--") + 1:]:
    probe(f)
