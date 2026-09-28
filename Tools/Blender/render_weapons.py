"""Render the Loadout weapon set for the public website.

The producer has directed (2026-09-28, LICENCE_REGISTER L-0017/L-0021 and
ASSET_REGISTER intake rule) that the site's Loadout section shows renders of
the CURRENT internal weapon models, including third-party-derived material:

    a88   sourced EF88 model (L-0017) as the in-game A88 cosmetic mesh
    a89   ADFRC Minimi/Mag58-derived support weapon (L-0021)
    a4    ADFRC M4A5-derived rifle (L-0021)
    a416  ADFRC HK416-derived rifle (L-0021)
    a25   ADFRC SR25-derived marksman rifle (L-0021)
    akm   sourced AKM reference model (R-23) - published as an explicitly
          labelled reference render only; NOT a game weapon

The a88, a89, a4, a416, a25 and a9 renders wear their real textures where the
source carries them. Textures are located by material slot name (case- and
spacer-insensitive) under Art/ADFRC/Textures/, by sibling folder for the
sourced EF88, and from the AKM's own packed images. Slots that resolve to no
texture fall back to a neutral studio material so nothing renders black.

Usage:
    blender --background --factory-startup -P Tools/Blender/render_weapons.py
"""
import math
import os

import bpy
from mathutils import Vector

ROOT = r"E:\SouthernSpear"
OUT = os.path.join(ROOT, "Docs", "images", "weapons")

RES_X, RES_Y = 1800, 1350
SAMPLES = 110
MARGIN = 1.14

BACKDROP = (0.020, 0.026, 0.021, 1.0)
KEY = (1.00, 0.86, 0.64)
FILL = (0.62, 0.72, 0.66)
RIM = (0.95, 0.55, 0.30)

# name -> relative source path.
WEAPONS = {
    "a88":  r"Art\Weapons\A88\New\SM_A88_Sourced.fbx",
    "a89":  r"Art\Weapons\A89\ADFRC\SM_A89.fbx",
    "a4":   r"Art\Weapons\A4\ADFRC\SM_A4.fbx",
    "a416": r"Art\Weapons\A416\ADFRC\SM_A416.fbx",
    "a25":  r"Art\Weapons\A25\ADFRC\SM_A25.fbx",
    "akm":  r"Art\Weapons\AKM\Weathered AKM rifle.blend",
}

TEX_ROOT = os.path.join(ROOT, "Art", "ADFRC", "Textures")


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


def find_texture(slot_name):
    """Locate a colour texture for a material slot by name.

    ADFRC slots are the texture stem, e.g. 'adfrc_hk416_barrel_co' maps to
    .../Textures/adfrc_hk416/adfrc_hk416_barrel_co.png. The search normalises
    case and separators because the packs are inconsistent about both.
    """
    stem = slot_name.lower().replace(" ", "").replace("__", "_")
    if not stem:
        return None
    for dirpath, _dirnames, filenames in os.walk(TEX_ROOT):
        for fn in filenames:
            base, ext = os.path.splitext(fn)
            if ext.lower() != ".png":
                continue
            if base.lower().replace(" ", "") == stem:
                return os.path.join(dirpath, fn)
    return None


def pbr_material(name, co_path=None, packed_image=None, nohq_path=None, smdi_path=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]

    img_co = None
    if packed_image is not None:
        img_co = packed_image
    elif co_path:
        img_co = bpy.data.images.load(co_path, check_existing=True)
    if img_co is not None:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img_co
        tex.interpolation = "Smart"
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    if nohq_path and os.path.isfile(nohq_path):
        img = bpy.data.images.load(nohq_path, check_existing=True)
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.interpolation = "Smart"
        normal_map = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tex.outputs["Color"], normal_map.inputs["Color"])
        nt.links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])

    if smdi_path and os.path.isfile(smdi_path):
        # Arma SMDI: R = AO, G = specular, B = smoothness.
        img = bpy.data.images.load(smdi_path, check_existing=True)
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.interpolation = "Smart"
        if "Roughness" in bsdf.inputs:
            sep = nt.nodes.new("ShaderNodeSeparateColor")
            nt.links.new(tex.outputs["Color"], sep.inputs["Color"])
            invert = nt.nodes.new("ShaderNodeInvert")
            nt.links.new(sep.outputs["Blue"], invert.inputs["Color"])
            nt.links.new(invert.outputs["Color"], bsdf.inputs["Roughness"])

    if img_co is None and nohq_path is None and smdi_path is None:
        # Neutral fallback so an unresolved slot never renders as black.
        bsdf.inputs["Base Color"].default_value = (0.075, 0.082, 0.070, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.55
        bsdf.inputs["Metallic"].default_value = 0.0
    return mat


def studio_material(name, color, rough, metal):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return mat


def source_pbr_for_slot(slot_name, weapon_dir):
    """Build a PBR material for one ADFRC-style slot.

    Colour texture: <slot>.png (stem IS the slot name). Normal/roughness come
    from the sibling stems when they exist (_nohq / _smdi); ADFRC files vary
    in case, so the lookup normalises both sides.
    """
    co = find_texture(slot_name)
    if not co:
        return None
    base = co[:-4]
    nohq = find_texture(slot_name[:-3] + "nohq") if slot_name.lower().endswith("_co") else None
    smdi = find_texture(slot_name[:-3] + "smdi") if slot_name.lower().endswith("_co") else None
    if nohq is None:
        nohq = base[:-3] + "nohq.png"
    if smdi is None:
        smdi = base[:-3] + "smdi.png"
    return pbr_material(slot_name, co_path=co, nohq_path=nohq, smdi_path=smdi)


def akm_material():
    """The AKM pack carries five packed 4096 maps on one material."""
    mat = bpy.data.materials.new("AKM_PBR")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]

    def packed(stem):
        for img in bpy.data.images:
            if img.name.lower() == stem.lower() and img.has_data:
                return img
        return None

    base = packed("Material_BaseColor.png")
    if base:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = base
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    normal = packed("Material_Normal.png")
    if normal:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = normal
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tex.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    rough = packed("Material_Roughness.png")
    if rough:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = rough
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Roughness"])
    metal = packed("Material_Metallic.png")
    if metal:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = metal
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Metallic"])
    return mat


def mean_colour(path):
    """Average RGB of an image, sampled small. Used to tell the sourced
    EF88's three UUID-named textures apart: the body map is the green one,
    and the optic glass map is the darkest of what remains."""
    img = bpy.data.images.load(path)
    try:
        img.scale(8, 8)
        px = list(img.pixels)
        n = len(px) // 4
        if not n:
            return None
        r = sum(px[0::4]) / n
        g = sum(px[1::4]) / n
        b = sum(px[2::4]) / n
        return (r, g, b)
    finally:
        bpy.data.images.remove(img)


def sourced_ef88_texture_roles(folder):
    """Map TexBody / TexFurniture / TexOptic to the three UUID PNGs.

    The FBX's slots were renamed by the game import, so the MTL's UUID names
    no longer tell us which map is which. Classify by content instead: the
    body texture is the strongly green one (F88 foliage), and of the other
    two the darker becomes the optic, the lighter the furniture."""
    pngs = [os.path.join(folder, f) for f in os.listdir(folder)
            if f.lower().endswith(".png")]
    scored = []
    for p in pngs:
        rgb = mean_colour(p)
        if rgb:
            scored.append((p, rgb))
    if len(scored) < 3:
        return {}
    scored.sort(key=lambda item: item[1][1] - (item[1][0] + item[1][2]) / 2.0,
                reverse=True)
    body = scored[0][0]
    rest = sorted(scored[1:], key=lambda item: sum(item[1]))
    return {"TexBody": body, "TexOptic": rest[0][0], "TexFurniture": rest[1][0]}


def apply_materials(meshes, kind, weapon_dir):
    for ob in meshes:
        src_names = [m.name if m else "" for m in ob.data.materials]
        if not src_names:
            ob.data.materials.append(studio_material("Polymer", (0.075, 0.082, 0.070), 0.55, 0.0))
            continue
        for i, name in enumerate(src_names):
            mat = None
            if kind == "akm":
                mat = akm_material()
            elif kind == "a88":
                role = name if name in ("TexBody", "TexFurniture", "TexOptic") else "TexBody"
                folder = os.path.join(ROOT, "Art", "Weapons", "A88", "New")
                roles = sourced_ef88_texture_roles(folder)
                path = roles.get(role)
                if path:
                    mat = pbr_material(role, co_path=path)
                else:
                    mat = studio_material(role, (0.075, 0.082, 0.070), 0.5, 0.15)
            else:
                mat = source_pbr_for_slot(name, weapon_dir)
                if mat is None:
                    # Optic glass and reticle slots get studio treatment so
                    # they read as glass rather than untextured plastic.
                    lname = name.lower()
                    if "glass" in lname or "ret" in lname:
                        mat = studio_material(name, (0.16, 0.30, 0.34), 0.12, 0.0)
                    else:
                        mat = studio_material(name, (0.075, 0.082, 0.070), 0.5, 0.2)
            ob.data.materials[i] = mat


def frame(camera, target, direction, corners, margin=MARGIN):
    """Fit the projected bounding-box silhouette into the frame. The extent
    scales as 1/distance, so measure at unit distance and take the square
    root of the requirement: one step, no iteration."""
    cam = camera.data
    view_dir = Vector(direction).normalized()
    quat = (-view_dir).to_track_quat("-Z", "Y")

    sensor = cam.sensor_width
    aspect = RES_X / RES_Y
    tan_x = (sensor / 2.0) / cam.lens
    tan_y = tan_x / aspect

    probe_loc = Vector(target) + view_dir
    inv = quat.inverted()
    need = 0.0
    for c in corners:
        local = inv @ (c - probe_loc)
        depth = -local.z
        if depth <= 1e-3:
            need = max(need, 4.0)
            continue
        need = max(need, abs(local.x / depth) / tan_x, abs(local.y / depth) / tan_y)

    dist = math.sqrt(max(need, 1e-6)) * margin
    camera.location = Vector(target) + view_dir * dist
    camera.rotation_euler = quat.to_euler()


def render(stem, rel_path, kind):
    reset()
    scene = bpy.context.scene
    path = os.path.join(ROOT, rel_path)
    if path.lower().endswith(".fbx"):
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        bpy.ops.wm.open_mainfile(filepath=path)
        scene = bpy.context.scene

    meshes = [o for o in scene.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit("no mesh in " + path)

    apply_materials(meshes, kind, os.path.dirname(path))

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
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Base Contrast"

    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = BACKDROP
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.25
    scene.world = world

    d = radius
    add_area("Key", (target.x - d * 1.9, target.y - d * 2.1, target.z + d * 2.0),
             (math.radians(52), 0, math.radians(-42)), (d * 1.6, d * 1.0), 340, KEY)
    add_area("Fill", (target.x + d * 2.4, target.y - d * 1.7, target.z + d * 0.4),
             (math.radians(82), 0, math.radians(54)), (d * 2.0, d * 1.4), 90, FILL)
    add_area("Rim", (target.x + d * 0.9, target.y + d * 2.0, target.z + d * 1.5),
             (math.radians(118), 0, math.radians(158)), (d * 1.2, d * 0.8), 460, RIM)

    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 85
    cam_data.sensor_fit = "HORIZONTAL"
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    frame(cam, target, (-0.62, -1.0, 0.30), corners)

    os.makedirs(OUT, exist_ok=True)
    scene.render.filepath = os.path.join(OUT, stem + ".png")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)


if __name__ == "__main__":
    for stem, rel in WEAPONS.items():
        render(stem, rel, stem)
    print("done")
