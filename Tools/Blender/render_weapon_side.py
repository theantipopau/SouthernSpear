"""Orthographic side view of weapon FBXs (for checking optic placement and direction).

    blender -b --factory-startup -P Tools/Blender/render_weapon_side.py -- <out_dir> <fbx> [<fbx> ...]

Workbench render, muzzle to the right (+X), a 5 cm grid on the ground plane for scale. Writes <out>/<name>_side.png.
"""
import math
import os
import sys

import bpy
import mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
out_dir, files = argv[0], argv[1:]
os.makedirs(out_dir, exist_ok=True)
OPTIC_HINTS = ("ta31", "ta648", "acog", "spectr", "optic", "glass", "ret", "elcan", "scope")

for path in files:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    # Optic parts in orange, the rest grey, so direction and placement read at a glance.
    grey = bpy.data.materials.new("grey"); grey.diffuse_color = (0.55, 0.55, 0.55, 1)
    orange = bpy.data.materials.new("orange"); orange.diffuse_color = (1.0, 0.45, 0.1, 1)
    for ob in meshes:
        for slot in ob.material_slots:
            name = (slot.material.name if slot.material else "").lower()
            slot.material = orange if any(h in name for h in OPTIC_HINTS) else grey
    pts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    lo = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c = (lo + hi) / 2
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    bpy.context.scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = (hi.x - lo.x) * 1.1
    cam.location = (c.x, lo.y - 2.0, c.z)
    cam.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.scene.camera = cam
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    sc.render.resolution_x, sc.render.resolution_y = 1400, int(1400 * (hi.z - lo.z + 0.1) / ((hi.x - lo.x) * 1.1))
    sc.render.filepath = os.path.join(out_dir, os.path.splitext(os.path.basename(path))[0] + "_side.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath)
