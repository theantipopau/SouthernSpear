"""Render the prepped Fab props so they can be judged before import.

Numbers alone will not tell you that a car wreck came out with its doors flung
open across three and a half metres, or that the "barn" is really four
unrelated panels. Decimation and re-pivoting are exactly the steps where
something quietly goes wrong, so every prepped prop is rendered from a
three-quarter view against a one-metre ground grid.

Run:  blender -b --factory-startup --python Tools/Blender/render_fab_props.py
"""
import json
import os

import bpy
from mathutils import Vector

ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PROPS = os.path.join(ROOT, "Build", "ravenshoe", "props")
SHOTS = os.path.join(ROOT, "Build", "ravenshoe")

TAGS = ["wreck_car", "wreck_junk", "fuel_drum", "windmill", "barn",
        "sandbag_stack", "trench_wall"]


def look_at(obj, target):
    """Point the camera's -Z at target. Blender cameras look down -Z."""
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def scale_ref(half):
    """Ground plane plus an exact 1 m cube beside the prop.

    A wire grid is fiddly and easy to misread at this resolution; a plain 1 m
    cube is the classic model-sheet reference and cannot be mistaken for
    anything other than one metre.
    """
    mesh = bpy.data.meshes.new("ground")
    mesh.from_pydata([(-half, -half, 0), (half, -half, 0),
                      (half, half, 0), (-half, half, 0)], [], [(0, 1, 2, 3)])
    ground = bpy.data.objects.new("ground", mesh)
    bpy.context.scene.collection.objects.link(ground)

    cube_mesh = bpy.data.meshes.new("refcube")
    x = y = z = 0.5
    cube_mesh.from_pydata(
        [(0, 0, 0), (x, 0, 0), (x, y, 0), (0, y, 0),
         (0, 0, z), (x, 0, z), (x, y, z), (0, y, z)],
        [], [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
    cube = bpy.data.objects.new("ref_1m", cube_mesh)
    # Park the cube just outside the prop's own footprint.
    cube.location = (half * 0.8, -half * 0.8, 0)
    bpy.context.scene.collection.objects.link(cube)
    return ground, cube


report = []
for tag in TAGS:
    src = os.path.join(PROPS, "SS_Raven_{}.fbx".format(tag))
    if not os.path.isfile(src):
        report.append({"tag": tag, "error": "missing"})
        continue

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=src)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        report.append({"tag": tag, "error": "no mesh"})
        continue

    cos = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    lo = Vector((min(c.x for c in cos), min(c.y for c in cos), min(c.z for c in cos)))
    hi = Vector((max(c.x for c in cos), max(c.y for c in cos), max(c.z for c in cos)))
    size = hi - lo
    centre = (lo + hi) * 0.5
    span = max(size.x, size.y, size.z)

    # Lighting: a key and a fill, enough to read form without a render pass.
    for name, loc, energy, size_l in (("key", (6, -6, 9), 900, 6),
                                      ("fill", (-7, -4, 5), 350, 8)):
        ld = bpy.data.lights.new(name, type="SUN")
        ld.energy = energy
        lo_obj = bpy.data.objects.new(name, ld)
        lo_obj.location = loc
        look_at(lo_obj, centre)
        bpy.context.scene.collection.objects.link(lo_obj)

    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    dist = span * 2.1 + 3.0
    cam.location = (centre.x + dist * 0.75, centre.y - dist * 0.95,
                    centre.z + dist * 0.55)
    look_at(cam, centre)
    cam_data.lens = 55

    scn = bpy.context.scene
    scn.render.engine = "BLENDER_WORKBENCH"
    scn.render.resolution_x = 900
    scn.render.resolution_y = 620
    # Must be set explicitly. A factory-startup scene does not always default
    # to PNG, and write_still then writes a differently-named file, so the
    # render appears to succeed and no image is where the report says it is.
    scn.render.image_settings.file_format = "PNG"
    scn.render.film_transparent = False
    sh = scn.display.shading
    sh.light = "STUDIO"
    sh.color_type = "RANDOM"
    sh.show_cavity = True
    scn.display.render_aa = "8"

    # A 1 m reference cube under the prop, so a 4.6 m car and a 0.9 m drum are
    # visibly different sizes in the picture.
    half = int(span) + 3
    scale_ref(half)

    dest = os.path.join(SHOTS, "prop_{}.png".format(tag))
    scn.render.filepath = dest
    bpy.ops.render.render(write_still=True)
    report.append({"tag": tag, "size": [round(v, 3) for v in size],
                   "shot": os.path.relpath(dest, ROOT).replace(os.sep, "/")})
    print("rendered {} {}".format(tag, size))

with open(os.path.join(ROOT, "Build", "render_fab_props.json"), "w",
          encoding="utf-8") as fh:
    json.dump(report, fh, indent=2)
print("done")
