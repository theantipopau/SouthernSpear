"""Render the project's own A-series weapon designs to PNGs for the website.

Only Class F original geometry is rendered here: the A88 first-pass source
(W-A88-01) and the A89 light support weapon (W-A89-01, ADR-020). Nothing that
is ADFRC-derived, the provisional A88 import (L-0017) or a blocked reference
file is opened by this script, because none of those may be republished.

The renders are product shots of the original models, lit on a dark studio
backdrop. They are not captured gameplay and the site labels them as such.

Usage:
    blender --background --factory-startup -P Tools/Blender/render_weapons.py
"""
import math
import os

import bpy
from mathutils import Vector

ROOT = r"E:\SouthernSpear"
OUT = os.path.join(ROOT, "Docs", "images", "weapons")

# name -> (fbx, title, caption stem used in the filename)
WEAPONS = [
    ("a88", os.path.join(ROOT, "Art", "Weapons", "A88", "SM_A88.fbx")),
    ("a89", os.path.join(ROOT, "Art", "Weapons", "A89", "SM_A89.fbx")),
]

RES_X, RES_Y = 1800, 1350
SAMPLES = 96

# Brand-matched studio: charcoal backdrop, brass key, sage fill, sunset rim.
BACKDROP = (0.020, 0.026, 0.021, 1.0)
KEY = (1.00, 0.86, 0.64)
FILL = (0.62, 0.72, 0.66)
RIM = (0.95, 0.55, 0.30)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def add_area(name, location, rotation, size, energy, color):
    data = bpy.data.lights.new(name, type="AREA")
    data.shape = "RECTANGLE"
    data.size, data.size_y = size
    data.energy = energy
    data.color = color
    ob = bpy.data.objects.new(name, data)
    ob.location = location
    ob.rotation_euler = rotation
    bpy.context.scene.collection.objects.link(ob)
    return ob


def shade_materials():
    """The source FBX carries three named slots: a matte polymer body, a
    darker metal for the mechanism, and the optic glass. They are shaded here
    rather than textured, because the original first-pass model ships without
    texture maps and inventing a skin would misrepresent the design."""
    polymer = bpy.data.materials.new("Polymer")
    polymer.use_nodes = True
    bsdf = polymer.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.075, 0.082, 0.070, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Metallic"].default_value = 0.0

    metal = bpy.data.materials.new("Metal")
    metal.use_nodes = True
    bsdf = metal.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.150, 0.158, 0.152, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.32
    bsdf.inputs["Metallic"].default_value = 0.9

    glass = bpy.data.materials.new("Glass")
    glass.use_nodes = True
    bsdf = glass.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.16, 0.30, 0.34, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.12
    bsdf.inputs["Metallic"].default_value = 0.0
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.35
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 0.35

    return {"Polymer": polymer, "Metal": metal, "Glass": glass}


def frame(camera, target, direction, corners, margin=1.10):
    """Aim the camera at the subject and pull back until its *projected*
    silhouette fills the frame.

    A bounding-sphere fit leaves a long thin rifle floating in dead space,
    because the sphere is dominated by the length. The projected extent of
    the bounding box scales as 1/distance, so the fit is solved directly:
    measure the silhouette at unit distance, then take the square root of the
    required distance. One step, no iteration, no oscillation.
    """
    cam = camera.data
    view_dir = Vector(direction).normalized()
    quat = (-view_dir).to_track_quat("-Z", "Y")

    sensor = cam.sensor_width
    aspect = RES_X / RES_Y
    tan_x = (sensor / 2.0) / cam.lens
    tan_y = tan_x / aspect

    # Measure the silhouette with the camera one unit from the target.
    probe_loc = Vector(target) + view_dir
    inv = quat.inverted()
    need = 0.0
    for c in corners:
        local = inv @ (c - probe_loc)
        depth = -local.z
        if depth <= 1e-3:
            # A corner is level with or behind the probe plane: push the
            # camera further out so nothing is clipped by the near plane.
            need = max(need, 4.0)
            continue
        need = max(need, abs(local.x / depth) / tan_x, abs(local.y / depth) / tan_y)

    dist = math.sqrt(max(need, 1e-6)) * margin
    loc = Vector(target) + view_dir * dist
    camera.location = loc
    camera.rotation_euler = quat.to_euler()
    return dist


def render(stem, fbx_path):
    reset()
    scene = bpy.context.scene
    bpy.ops.import_scene.fbx(filepath=fbx_path)

    meshes = [o for o in scene.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit("no mesh in " + fbx_path)

    palette = shade_materials()
    for ob in meshes:
        # Replace each imported slot in place so per-face material_index
        # assignments keep pointing at the same part of the model.
        src_names = [m.name if m else "" for m in ob.data.materials]
        if not src_names:
            ob.data.materials.append(palette["Polymer"])
            continue
        for i, name in enumerate(src_names):
            key = next((k for k in palette if k.lower() in name.lower()), "Polymer")
            ob.data.materials[i] = palette[key]

    # Subject bounds drive both the framing and the light placement.
    corners = [ob.matrix_world @ Vector(c) for ob in meshes for c in ob.bound_box]
    lo = Vector((min(c[i] for c in corners) for i in range(3)))
    hi = Vector((max(c[i] for c in corners) for i in range(3)))
    target = (lo + hi) / 2.0
    radius = max((hi - lo).length / 2.0, 0.05)

    scene.render.engine = "CYCLES"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    # Transparent film: the weapon is the only opaque thing in frame, so the
    # render drops onto any dark section of the site with no seam, exactly as
    # the brand mark does. No backdrop, no floor, no wash.
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Base Contrast"

    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = BACKDROP
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.25
    scene.world = world

    # Three-point rig on the subject. The key sits up and to the front-left,
    # the fill opens the shadow side, and a warm rim traces the top edge
    # against the page's dark background.
    d = radius
    add_area("Key", (target.x - d * 1.9, target.y - d * 2.1, target.z + d * 2.0),
             (math.radians(52), 0, math.radians(-42)), (d * 1.6, d * 1.0), 320, KEY)
    add_area("Fill", (target.x + d * 2.4, target.y - d * 1.7, target.z + d * 0.4),
             (math.radians(82), 0, math.radians(54)), (d * 2.0, d * 1.4), 80, FILL)
    add_area("Rim", (target.x + d * 0.9, target.y + d * 2.0, target.z + d * 1.5),
             (math.radians(118), 0, math.radians(158)), (d * 1.2, d * 0.8), 420, RIM)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 85
    cam_data.sensor_fit = "HORIZONTAL"
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    # Three-quarter view from the front-left, slightly above the bore line.
    frame(cam, target, (-0.62, -1.0, 0.30), corners)

    os.makedirs(OUT, exist_ok=True)
    scene.render.filepath = os.path.join(OUT, stem + ".png")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)


for stem, path in WEAPONS:
    render(stem, path)
print("done")
