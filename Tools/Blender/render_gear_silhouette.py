# Southern Spear - front and side orthographic renders of fitted gear over the UE5 mannequin (fit review).
#
#   blender -b --factory-startup -P Tools/Blender/render_gear_silhouette.py -- <out.png> <gear.fbx> [<gear.fbx> ...]
#
# Left pair: the bare mannequin (front, side). Right pair: mannequin + gear. Workbench, flat grey.

import math
import os
import sys

import bpy

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MANNY = os.path.join(ROOT, "Art", "Characters", "ADF", "SKM_Manny_ref.fbx")
args = sys.argv[sys.argv.index("--") + 1:]
OUT, GEAR = args[0], args[1:]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def import_meshes(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    return [o for o in new if o.type == "MESH"], new


def place(objs, dx):
    for o in objs:
        if o.parent is None:
            o.location.x += dx


body, body_all = import_meshes(MANNY)
body_b, body_b_all = import_meshes(MANNY)
gear_all = []
for g in GEAR:
    _, a = import_meshes(g)
    gear_all += a
# Four figures side by side along X (metres): bare front, bare side, dressed front, dressed side.
place(body_all, -1.5)
place(body_b_all, 0.5)
place(gear_all, 0.5)
# Side views: duplicate by rotating copies is simpler with a second camera; instead render two images.

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "SINGLE"
scene.display.shading.single_color = (0.55, 0.55, 0.52)
scene.render.resolution_x, scene.render.resolution_y = 1200, 1000
scene.render.film_transparent = False
world = bpy.data.worlds.new("W")
scene.world = world
world.color = (0.08, 0.08, 0.08)

cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 4.2
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def shoot(path, yaw):
    # Look horizontally at the figures' middle (0.9 m up), from the -Y side (the mannequin faces +Y... front).
    r = 10.0
    cam.location = (-0.5 + r * math.sin(yaw), -r * math.cos(yaw), 0.95)
    cam.rotation_euler = (math.radians(90), 0, yaw)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


base, ext = os.path.splitext(OUT)
shoot(base + "_front" + ext, math.radians(180))
print("SS_SILHOUETTE " + base)
